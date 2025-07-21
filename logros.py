# logros.py (Refactorizado)

from datetime import datetime
# Ya no importamos tkinter.messagebox aquí, porque esta capa no debe conocer la UI.
# Ya no importamos gestion_usuarios directamente.

# Importamos el User model
from models.user_model import User

LOGROS_DEFINICIONES = {
    "primer_quiz": "Completaste tu primer quiz.",
    "mente_brillante": "Obtuviste una puntuación perfecta en un quiz.",
    "racha_5": "Lograste 5 respuestas correctas seguidas.",
    "polimata_5": "Completaste quizzes en 5 temas diferentes."
}

def verificar_y_actualizar_logros(user: User, tipo_evento: str, **kwargs) -> list[str]:
    """
    Verifica y actualiza los logros para un usuario dado.
    Esta función solo modifica el objeto User y retorna los logros desbloqueados.
    La persistencia (guardar el usuario) y la notificación a la UI se manejan en otro lugar.

    Args:
        user (User): La instancia del usuario.
        tipo_evento (str): El tipo de evento que ha ocurrido (ej. 'post_quiz', 'respuesta_correcta').
        **kwargs: Datos adicionales relevantes para el evento.

    Returns:
        list[str]: Una lista de los IDs de los logros recién desbloqueados.
    """
    nuevos_logros_desbloqueados = []

    # Logro: Primer Quiz
    if tipo_evento == 'post_quiz':
        # La lógica de User.desbloquear_logro() ya comprueba si el logro es None
        if user.desbloquear_logro("primer_quiz"):
            nuevos_logros_desbloqueados.append("primer_quiz")

    # Logro: Mente Brillante
    if tipo_evento == 'post_quiz':
        quiz_data = kwargs.get('quiz_data', {})
        if quiz_data.get('total', 0) >= 5 and quiz_data.get('aciertos', 0) == quiz_data.get('total', 0):
            if user.desbloquear_logro("mente_brillante"):
                nuevos_logros_desbloqueados.append("mente_brillante")
            
    # Logro: Racha de 5
    if tipo_evento == 'respuesta_correcta':
        # Asumimos que la racha ya fue incrementada en el servicio antes de llamar a esto
        if user.progreso.get('racha_correctas', 0) >= 5:
            if user.desbloquear_logro("racha_5"):
                nuevos_logros_desbloqueados.append("racha_5")

    # Logro: Polímata (5 temas)
    if tipo_evento == 'post_quiz':
        # Asumimos que el tema ya fue añadido al historial_temas en el servicio
        if len(user.estadisticas.get('rendimiento_por_tema', {})) >= 5: # Usa rendimiento_por_tema para contar temas distintos
            if user.desbloquear_logro("polimata_5"):
                nuevos_logros_desbloqueados.append("polimata_5")
    
    # Esta función ya no guarda el usuario directamente, lo hará el servicio que la llama.
    return nuevos_logros_desbloqueados