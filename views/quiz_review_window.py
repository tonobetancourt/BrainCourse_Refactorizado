# views/quiz_review_window.py

import customtkinter as ctk
from datetime import datetime

from models.user_model import User
from services.teacher_service import TeacherService
from views.correction_window import CorrectionWindow # Para abrir la ventana de corrección


class QuizReviewWindow(ctk.CTkToplevel):
    def __init__(self, master, profesor_user: User, teacher_service_instance: TeacherService, actividad_data: dict):
        super().__init__(master)
        self.master = master
        self.profesor_user = profesor_user
        self.teacher_service = teacher_service_instance
        self.actividad_data = actividad_data # Datos de la actividad completa del historial

        self.title(f"Revisión de Quiz: {actividad_data.get('tema', 'N/A')}")
        self.geometry("800x600")
        self.transient(master)
        self.grab_set()

        scrollable_frame = ctk.CTkScrollableFrame(self, label_text=f"Detalle de Actividad del {datetime.fromisoformat(actividad_data['fecha']).strftime('%d/%m/%Y %H:%M')}")
        scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Iterar sobre las preguntas de la actividad
        for i, pregunta in enumerate(actividad_data.get('preguntas', [])):
            p_frame = ctk.CTkFrame(scrollable_frame)
            p_frame.pack(fill="x", pady=5, padx=5)
            p_frame.grid_columnconfigure(0, weight=1) # Pregunta y respuestas
            p_frame.grid_columnconfigure(1, weight=0) # Botón de reporte

            ctk.CTkLabel(p_frame, text=f"Pregunta {i+1}: {pregunta.get('pregunta', 'N/A')}", wraplength=700, justify="left", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
            
            respuesta_alumno = str(pregunta.get('respuesta_usuario', 'No respondió'))
            respuesta_ia = str(pregunta.get('respuesta_correcta_ia', 'N/A'))
            
            color_alumno = "green" if pregunta.get('fue_correcta', False) else "red"
            ctk.CTkLabel(p_frame, text=f"Respuesta del Alumno: {respuesta_alumno}", text_color=color_alumno).grid(row=1, column=0, sticky="w", padx=10, pady=2)
            
            # Si la respuesta del alumno fue incorrecta, mostrar la respuesta de la IA y el botón de reportar
            if not pregunta.get('fue_correcta', False):
                ctk.CTkLabel(p_frame, text=f"Respuesta Correcta (según IA): {respuesta_ia}").grid(row=2, column=0, sticky="w", padx=10, pady=2)
                
                # El botón de Reportar Error solo se muestra si la IA dio una respuesta correcta y el alumno falló
                # Y pasamos los datos originales de la pregunta a la ventana de corrección
                pregunta_original_data = {
                    'pregunta': pregunta.get('pregunta'),
                    'respuesta_correcta_ia': pregunta.get('respuesta_correcta_ia')
                }
                ctk.CTkButton(p_frame, text="Reportar Error de IA", fg_color="transparent", border_width=1, command=lambda p_data=pregunta_original_data: self.open_correction_window(p_data)).grid(row=2, column=1, sticky="e", padx=10)

    def open_correction_window(self, pregunta_original_data: dict):
        CorrectionWindow(self, self.profesor_user, self.teacher_service, pregunta_original_data)