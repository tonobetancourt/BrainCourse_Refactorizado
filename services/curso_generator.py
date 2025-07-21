# services/curso_generator.py

import json
import uuid
# No importamos 'google.generativeai' directamente aquí.

from ai_integration.ai_service import AIService # Importamos el AIService

def generar_silabo_curso(tema_general: str, ai_service: AIService):
    """
    Genera un sílabo de curso utilizando la IA de Gemini.
    Recibe una instancia de AIService para la comunicación con la IA.
    """
    prompt = (
        f"Actúa como un diseñador de cursos experto. Para el tema '{tema_general}', crea un sílabo detallado "
        "en formato JSON. El JSON debe tener una clave 'modulos', que es una lista de 3 a 5 módulos. "
        "Cada módulo debe tener un 'titulo' (string) y una lista de 'subtemas' (lista de strings). "
        "No incluyas introducciones, solo el JSON puro. Ejemplo de la estructura deseada: "
        '{"modulos": [{"titulo": "Módulo 1: ...", "subtemas": ["Subtema 1.1", "Subtema 1.2"]}]}'
    )
    try:
        # Usamos el método send_message del AIService
        response_text = ai_service.send_message(prompt, current_topic=tema_general)
        json_text = response_text.strip().replace("```json", "").replace("```", "")
        silabo = json.loads(json_text)

        curso_completo = {
            "id_curso": f"curso_{uuid.uuid4().hex[:8]}",
            "tema_general": tema_general,
            "progreso_general": 0.0,
            "calificacion_promedio": None,
            "modulos": []
        }
        for modulo_data in silabo.get("modulos", []):
            curso_completo["modulos"].append({
                "id_modulo": f"mod_{uuid.uuid4().hex[:6]}",
                "titulo": modulo_data.get("titulo", "Sin título"),
                "subtemas": modulo_data.get("subtemas", []),
                "completado": False,
                "calificacion_examen": None,
                "teoria_generada": {}
            })
        return curso_completo
    except Exception as e:
        print(f"Error generando sílabo del curso: {e}")
        return None

def generar_teoria_subtema(subtema: str, ai_service: AIService):
    """
    Genera teoría para un subtema utilizando la IA de Gemini.
    Recibe una instancia de AIService para la comunicación con la IA.
    """
    prompt = (
        "Actúa como un profesor de matemáticas claro y conciso. Explica el siguiente concepto: "
        f"'{subtema}'. Proporciona la teoría fundamental, cualquier fórmula clave y un ejemplo simple resuelto. "
        "Usa un lenguaje fácil de entender."
    )
    try:
        # Usamos el método send_message del AIService
        response_text = ai_service.send_message(prompt, current_topic=subtema)
        return response_text.strip()
    except Exception as e:
        print(f"Error generando teoría del subtema: {e}")
        return "No se pudo generar la teoría para este subtema."