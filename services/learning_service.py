# services/learning_service.py

from models.user_model import User
from data import gestion_usuarios as user_dao
from ai_integration.ai_service import AIService
from services import ejercicios # Ahora `ejercicios` se trata como un módulo auxiliar para este servicio
import logros # El refactorizado logros.py
from datetime import datetime

class LearningService:
    def __init__(self, user_dao_module, ai_service_instance: AIService):
        self.user_dao = user_dao_module # Pasamos el módulo gestion_usuarios
        self.ai_service = ai_service_instance

    def generar_quiz_nivelacion(self, user: User):
        """Genera un quiz de nivelación para el usuario."""
        return ejercicios.generar_quiz_nivelacion_con_ia(user.datos_perfil.get('nivel_estudios'), self.ai_service)

    def generar_quiz_tematico(self, user: User, topic: str, num_questions: int):
        """Genera un quiz temático para el usuario."""
        user.agregar_historial_tema(topic) # Actualiza el historial de temas del usuario
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict()) # Persiste el historial
        return ejercicios.generar_quiz_tematico_con_ia(topic, user.progreso.get('nivel'), num_questions, self.ai_service, user.datos_perfil)
    
    def generar_examen_modulo(self, user: User, subtemas: list, num_questions: int):
        """Genera un examen para un módulo específico."""
        return ejercicios.generar_examen_modulo(subtemas, user.progreso.get('nivel'), num_questions, self.ai_service, user.datos_perfil)

    def procesar_respuesta_quiz(self, user: User, tema: str, pregunta_data: dict, opcion_elegida: str):
        """
        Procesa la respuesta del usuario a una pregunta del quiz/examen.
        Actualiza el progreso, estadísticas y verifica logros.
        
        Args:
            user (User): La instancia del usuario.
            tema (str): El tema del quiz/examen.
            pregunta_data (dict): Datos de la pregunta (pregunta, opciones, respuesta).
            opcion_elegida (str): La opción seleccionada por el usuario.
        
        Returns:
            tuple[bool, list[str]]: (es_correcta, logros_desbloqueados_ids)
        """
        # Usar 'respuesta' si existe, si no, 'respuesta_correcta_ia'
        respuesta_correcta = pregunta_data.get("respuesta", pregunta_data.get("respuesta_correcta_ia"))
        es_correcta = (str(opcion_elegida) == str(respuesta_correcta))

        # Actualizar estadísticas en el modelo User
        user.registrar_respuesta_quiz(tema, es_correcta, pregunta_data['pregunta'], opcion_elegida, respuesta_correcta)
        
        # Actualizar racha y nivel en el modelo User
        if es_correcta:
            user.incrementar_racha()
            if user.progreso.get('racha_correctas', 0) >= 3 and user.progreso.get('racha_correctas', 0) % 3 == 0:
                user.subir_nivel()
        else:
            user.resetear_racha()
            # La lógica para 'preguntas_falladas' se manejará en la UI si es para repaso inmediato

        # Verificar y actualizar logros (la función de logros modifica el objeto User)
        unlocked_achievements = logros.verificar_y_actualizar_logros(user, 'respuesta_correcta')

        # Persistir los cambios en la base de datos
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict())
        
        return es_correcta, unlocked_achievements

    def finalizar_quiz(self, user: User, quiz_results: dict, is_exam: bool = False):
        """
        Finaliza un quiz (práctica o examen).
        Actualiza el historial de actividad y verifica logros post-quiz.
        
        Args:
            user (User): La instancia del usuario.
            quiz_results (dict): Diccionario con 'topic', 'total_questions', 'correct_answers', 'questions_details'.
            is_exam (bool): True si es un examen de módulo, False para un quiz de práctica.
        
        Returns:
            list[str]: IDs de logros desbloqueados.
        """
        # Aquí se registra la actividad en el historial del usuario
        actividad = {
            "fecha": datetime.now().isoformat(),
            "tipo": "Examen de Módulo" if is_exam else "Quiz de Práctica",
            "tema": quiz_results['topic'],
            "resultado": f"{quiz_results['correct_answers']}/{quiz_results['total_questions']}",
            "preguntas": quiz_results['questions_details'] # Lista de dicts con pregunta, respuesta_usuario, fue_correcta, etc.
        }
        user.historial_actividad.insert(0, actividad)

        # Verificar y actualizar logros post-quiz
        unlocked_achievements = logros.verificar_y_actualizar_logros(user, 'post_quiz', quiz_data={
            'aciertos': quiz_results['correct_answers'],
            'total': quiz_results['total_questions']
        })
        
        # También para el logro Polímata (Polímata 5), si aplica al final del quiz
        # Se llama de nuevo con 'post_quiz' para que la lógica de logros verifique los temas distintos
        unlocked_achievements.extend(logros.verificar_y_actualizar_logros(user, 'polimata_5'))

        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict()) # Persistir los cambios del usuario

        return unlocked_achievements