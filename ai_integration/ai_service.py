# ai_integration/ai_service.py

import google.generativeai as genai
import os

class AIService:
    _instance = None
    _initialized = False
    _chat_session = None
    _model = None

    SYSTEM_INSTRUCTION = (
        "Eres 'Brainy', el tutor universal de IA de la plataforma de aprendizaje 'BrainCourse'. Tienes dos roles principales:\n"
        "1. Eres un experto académico capaz de explicar cualquier tema, crear ejercicios y guiar en el aprendizaje.\n"
        "2. Eres un guía experto de la propia aplicación BrainCourse y puedes ayudar a los usuarios a encontrar sus funciones.\n\n"
        "--- CONOCIMIENTO SOBRE LA APLICACIÓN BRAINCOURSE ---\n"
        "Cuando un usuario te pregunte cómo hacer algo en la aplicación, usa la siguiente información para guiarlo. Responde de forma amigable y directa, indicando los pasos a seguir.\n\n"
        "- **Para practicar ejercicios:** Deben hacer clic en el botón '🧠 Practicar' en el menú de la izquierda. Allí podrán elegir un tema para generar un quiz.\n"
        "- **Para ver los cursos:** La sección '📚 Mis Cursos' está en el menú de la izquierda. Ahí pueden ver los cursos que tienen asignados o crear uno nuevo.\n"
        "- **Para ver su progreso y estadísticas:** Deben ir a la sección '📊 Mi Progreso' en el menú de la izquierda. Ahí encontrarán un resumen de su nivel, aciertos y un gráfico de rendimiento por tema.\n"
        "- **Para cambiar la apariencia (modo oscuro/claro):** Deben ir a '⚙️ Configuración', luego a la pestaña 'Apariencia'.\n"
        "- **Para cambiar la contraseña:** Esta función no está disponible en el perfil de usuario. (Nota: Esto es para que la IA no invente una solución si no la hemos definido).\n"
        "- **Para vincularse con un profesor (solo alumnos):** Deben ir a '⚙️ Configuración', luego a la pestaña 'Vincular Profesor'. Allí pueden ver invitaciones de profesores o enviar nuevas solicitudes.\n"
        "- **Para cerrar sesión:** Deben hacer clic en el botón rojo 'Cerrar Sesión' en la parte inferior del menú de la izquierda.\n"
        "- **Para eliminar su cuenta:** Esta es una acción delicada. Deben ir a '⚙️ Configuración', a la pestaña 'Perfil', y hacer clic en el botón rojo 'Eliminar mi Cuenta Permanentemente'.\n\n"
        "Tu objetivo es ser el asistente más útil posible, tanto en lo académico como en el uso de la plataforma."
    )

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
        return cls._instance

    def initialize(self, api_key_path: str):
        if not self._initialized:
            try:
                with open(api_key_path, 'r') as f:
                    API_KEY = f.read().strip()
                genai.configure(api_key=API_KEY)
                self._model = genai.GenerativeModel('gemini-2.0-flash')
                self._chat_session = self._model.start_chat(history=[
                    {'role': 'user', 'parts': [self.SYSTEM_INSTRUCTION]},
                    {'role': 'model', 'parts': ["¡Entendido! Soy Brainy."]}
                ])
                self._initialized = True
                print("Gemini API configurada y sesión de chat iniciada.")
            except Exception as e:
                print(f"Error al cargar la API Key o configurar Gemini: {e}")
                self._model = None
                self._chat_session = None
                raise e

    def get_model(self):
        if not self._initialized:
            raise Exception("AIService no ha sido inicializado. Llama a initialize() primero.")
        return self._model

    def get_chat_session(self):
        if not self._initialized:
            raise Exception("AIService no ha sido inicializado. Llama a initialize() primero.")
        if not self._chat_session and self._model:
            self._chat_session = self._model.start_chat(history=[
                {'role': 'user', 'parts': [self.SYSTEM_INSTRUCTION]},
                {'role': 'model', 'parts': ["¡Entendido! Soy Brainy."]}
            ])
        return self._chat_session

    def send_message(self, prompt_text: str, user_level: int = 1, user_profile_data: dict = None, current_topic: str = None, current_question_text: str = None, course_context: dict = None):
        if not self._initialized:
            raise Exception("AIService no ha sido inicializado. Llama a initialize() primero.")
        
        chat_session = self.get_chat_session()

        contexto = "[INICIO DEL CONTEXTO PARA LA IA]\n"
        contexto += f"Eres 'Brainy', el asistente de IA integrado en la plataforma de aprendizaje 'BrainCourse'.\n"
        contexto += f"Estás hablando con un usuario (Nivel de dificultad {user_level}).\n"
        
        if user_profile_data:
            contexto += f"Su objetivo principal es: '{user_profile_data.get('objetivo_principal', 'no especificado')}'\n"
            contexto += f"Su autoevaluacion es: '{user_profile_data.get('autoevaluacion', 'no especificada')}'\n"
        
        if current_topic:
            contexto += f"El usuario está enfocado en el tema '{current_topic}'.\n"
        
        if current_question_text:
            contexto += f"La pregunta actual que el usuario está viendo o acaba de ver es: '{current_question_text}'.\n"

        if course_context:
            contexto += (f"CONTEXTO DE CURSO: El usuario está viendo el curso '{course_context.get('curso_tema')}' "
                         f"y específicamente el módulo '{course_context.get('modulo_titulo')}'.\n")

        contexto += "[FIN DEL CONTEXTO]\n\n"
        
        full_prompt = f"{contexto}PREGUNTA DEL USUARIO: '{prompt_text}'"

        try:
            response = chat_session.send_message(full_prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error al enviar mensaje a Gemini: {e}")
            return f"Lo siento, tuve un problema al procesar tu solicitud: {e}"
    
    def stub_send_message(self, prompt, **kwargs):
        # Método stub para evitar errores de importación y permitir integración real.
        return "Respuesta generada por IA para: " + prompt