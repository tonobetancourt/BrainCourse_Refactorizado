# services/ejercicios.py

import json
import random
# Ya no importamos 'datetime' aquí, se maneja en user_model o en el servicio que registra la actividad.
# No importamos 'google.generativeai' directamente aquí.

# Importamos el AIService que será el encargado de la comunicación con Gemini
from ai_integration.ai_service import AIService

def _construir_modificador_contextual(datos_perfil_usuario):
    """
    Función de ayuda para crear un texto adicional para el prompt
    basado en el contexto del perfil del usuario.
    """
    if not datos_perfil_usuario:
        return ""

    modificadores = []

    # Extraer datos del perfil del usuario
    año_cursado = datos_perfil_usuario.get('año_cursado')
    objetivo = datos_perfil_usuario.get('objetivo_principal')
    autoevaluacion = datos_perfil_usuario.get('autoevaluacion')

    # Construir el texto basado en los datos
    if año_cursado:
        modificadores.append(f"El usuario está cursando {año_cursado}.")

    if objetivo == "Pasar un examen":
        modificadores.append("El problema debe tener un formato y tono similar a una pregunta de examen: claro, conciso y enfocado en la evaluación.")
    elif objetivo == "Aprender por curiosidad":
        modificadores.append("El problema puede ser más creativo o aplicado a un caso práctico interesante.")
    
    if autoevaluacion == "Necesito mucha ayuda":
        modificadores.append("El problema debe ser de un nivel fundamental, ideal para un principiante en el tema. Si es posible, la pregunta puede incluir un pequeño recordatorio de una fórmula clave.")
    elif autoevaluacion == "Soy bueno/a pero quiero mejorar":
        modificadores.append("El problema puede incluir un pequeño giro o un detalle que requiera más atención para resolverlo, buscando desafiar al usuario.")

    if not modificadores:
        return ""
    
    # Unir todos los modificadores en una sola instrucción para la IA
    return "Considera el siguiente contexto sobre el estudiante al crear el problema: " + " ".join(modificadores)


def generar_quiz_nivelacion_con_ia(nivel_estudios: str, ai_service: AIService):
    """
    Genera un quiz de nivelación completo utilizando la IA de Gemini.
    Recibe una instancia de AIService para la comunicación con la IA.
    """
    if nivel_estudios == "Primaria":
        tema_general = "aritmética básica (sumas, restas, multiplicaciones simples)"
    elif nivel_estudios == "Secundaria/Preparatoria":
        tema_general = "álgebra fundamental (ecuaciones de primer grado, despejar variables)"
    else: # Universidad o cualquier otro
        tema_general = "conceptos pre-cálculo (vectores 2D, funciones simples)"

    prompt_para_ia = (
        f"Crea un quiz de 5 preguntas de opción múltiple sobre el siguiente tema general: '{tema_general}'. "
        "Las preguntas deben tener una dificultad progresiva. Cada pregunta debe tener 4 opciones. Una opción debe ser la respuesta correcta. "
        "Las otras 3 opciones deben ser distractores plausibles. "
        "Devuelve tu respuesta ÚNICA Y EXCLUSIVAMENTE en formato JSON, sin ninguna otra palabra o explicación. "
        "El JSON debe ser una lista de 5 objetos, donde cada objeto tiene esta estructura exacta: "
        '{"pregunta": "texto", "opciones": ["a", "b", "c", "d"], "respuesta": "texto de la respuesta correcta"}'
    )

    try:
        # Usamos el método send_message del AIService para interactuar con la IA
        response_text = ai_service.send_message(prompt_para_ia)
        
        json_text = response_text.strip().replace("```json", "").replace("```", "")
        quiz_data = json.loads(json_text)
        
        # Asegurarse de que la respuesta sea una lista
        if not isinstance(quiz_data, list):
            print(f"La respuesta de la IA no es una lista: {quiz_data}")
            return []
            
        for problema in quiz_data:
            if "opciones" in problema and isinstance(problema["opciones"], list):
                random.shuffle(problema["opciones"])
        
        return quiz_data
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error generando quiz de nivelación con IA: {e}")
        return []

def generar_quiz_tematico_con_ia(tema: str, nivel: int, num_preguntas: int, ai_service: AIService, datos_perfil_usuario: dict = None):
    """
    Genera un quiz temático adaptado al perfil del usuario.
    Recibe una instancia de AIService para la comunicación con la IA.
    """
    modificador_contextual = _construir_modificador_contextual(datos_perfil_usuario)

    prompt_para_ia = (
        f"Crea un quiz de {num_preguntas} preguntas de opción múltiple sobre el siguiente tema: '{tema}'. "
        f"La dificultad de los problemas debe ser apropiada para un nivel {nivel} en una escala del 1 al 10. "
        f"{modificador_contextual} "
        "Cada pregunta debe tener 4 opciones. Una opción debe ser la respuesta correcta. "
        "Las otras opciones deben ser distractores plausibles. "
        "Devuelve tu respuesta ÚNICA Y EXCLUSIVAMENTE en formato JSON, sin ninguna otra palabra o explicación. "
        "El JSON debe ser una lista de objetos, donde cada objeto tiene esta estructura exacta: "
        '{"pregunta": "texto de la pregunta", "opciones": ["a", "b", "c", "d"], "respuesta": "texto de la respuesta correcta"}'
    )

    try:
        response_text = ai_service.send_message(prompt_para_ia, user_level=nivel, user_profile_data=datos_perfil_usuario, current_topic=tema)
        json_text = response_text.strip().replace("```json", "").replace("```", "")
        quiz_data = json.loads(json_text)
        if isinstance(quiz_data, list):
            for problema in quiz_data:
                if "opciones" in problema: random.shuffle(problema["opciones"])
            return quiz_data
        else: return []
    except (json.JSONDecodeError, KeyError, Exception) as e:
        print(f"Error generando quiz temático con IA: {e}"); return []


def generar_examen_modulo(subtemas: list, nivel: int, num_preguntas: int, ai_service: AIService, datos_perfil_usuario: dict = None):
    """
    Genera un examen de módulo adaptado al perfil del usuario.
    Recibe una instancia de AIService para la comunicación con la IA.
    """
    modificador_contextual = _construir_modificador_contextual(datos_perfil_usuario)
    temas_str = ", ".join(subtemas)
    
    prompt = (
        f"Crea un examen de {num_preguntas} preguntas de opción múltiple. Las preguntas deben cubrir de manera "
        f"equilibrada los siguientes temas: '{temas_str}'. La dificultad debe ser apropiada para un nivel {nivel} "
        f"en una escala de 1 a 10. {modificador_contextual} "
        "Cada pregunta debe tener 4 opciones y una respuesta correcta. "
        "Devuelve tu respuesta ÚNICA Y EXCLUSIVAMENTE en formato JSON, como una lista de objetos."
    )
    
    try:
        response_text = ai_service.send_message(prompt, user_level=nivel, user_profile_data=datos_perfil_usuario, current_topic=temas_str)
        json_text = response_text.strip().replace("```json", "").replace("```", "")
        quiz_data = json.loads(json_text)
        if isinstance(quiz_data, list):
            for problema in quiz_data:
                if "opciones" in problema: random.shuffle(problema["opciones"])
            return quiz_data
        else: return []
    except Exception as e:
        print(f"Error generando examen de módulo: {e}"); return []