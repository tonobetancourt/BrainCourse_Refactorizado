# --- Archivo: voice_assistant.py (Nuevo) ---

import threading

try:
    import speech_recognition as sr
except ImportError:
    sr = None

def start_listening(root, callback_success, callback_error, callback_status):
    if sr is None:
        callback_error("El módulo speech_recognition no está instalado.")
        callback_status("idle")
        return

    def listen():
        callback_status("listening")
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        with mic as source:
            try:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5)
                callback_status("processing")
                text = recognizer.recognize_google(audio, language="es-ES")
                callback_success(text)
            except sr.WaitTimeoutError:
                callback_error("No se detectó voz. Intenta de nuevo.")
            except sr.UnknownValueError:
                callback_error("No se entendió el audio.")
            except sr.RequestError:
                callback_error("Error de conexión con el servicio de reconocimiento.")
            except Exception as e:
                callback_error(f"Error inesperado: {e}")
            finally:
                callback_status("idle")

    threading.Thread(target=listen, daemon=True).start()