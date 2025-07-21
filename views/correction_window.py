# views/correction_window.py

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime

from models.user_model import User
from services.teacher_service import TeacherService # Para guardar la corrección


class CorrectionWindow(ctk.CTkToplevel):
    def __init__(self, master, profesor_user: User, teacher_service_instance: TeacherService, pregunta_data: dict):
        super().__init__(master)
        self.master = master
        self.profesor_user = profesor_user
        self.teacher_service = teacher_service_instance
        self.pregunta_data = pregunta_data # Datos originales de la pregunta de la IA

        self.title("Reportar Error de IA")
        self.geometry("600x450")
        self.transient(master) # Mantener encima de la ventana principal
        self.grab_set()        # Bloquear interacciones con la ventana principal

        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Corregir Respuesta de la IA", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=10)

        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(info_frame, text=f"Pregunta: {pregunta_data.get('pregunta', 'N/A')}", wraplength=550, justify="left").pack(anchor="w", padx=10, pady=5)
        ctk.CTkLabel(info_frame, text=f"Respuesta (IA): {pregunta_data.get('respuesta_correcta_ia', 'N/A')}", wraplength=550, justify="left").pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(self, text="Tu Respuesta Correcta:", anchor="w").grid(row=2, column=0, padx=20, pady=(10,0), sticky="w")
        self.correct_answer_entry = ctk.CTkEntry(self)
        self.correct_answer_entry.grid(row=3, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self, text="Justificación (opcional):", anchor="w").grid(row=4, column=0, padx=20, pady=(10,0), sticky="w")
        self.justification_textbox = ctk.CTkTextbox(self, height=100)
        self.justification_textbox.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkButton(self, text="Enviar Corrección", command=self.submit_correction).grid(row=6, column=0, padx=20, pady=20)

    def submit_correction(self):
        respuesta_profesor = self.correct_answer_entry.get().strip()
        justificacion = self.justification_textbox.get("1.0", "end-1c").strip()

        if not respuesta_profesor:
            messagebox.showerror("Error", "Debes proporcionar la respuesta correcta.", parent=self)
            return
        
        # Datos de la corrección a enviar al TeacherService
        correccion_data = {
            "respuesta_profesor": respuesta_profesor,
            "justificacion": justificacion
        }

        # Llamar al TeacherService para guardar la corrección
        success = self.teacher_service.guardar_correccion_ia(
            self.profesor_user.email,
            self.pregunta_data, # Pasa la pregunta original completa
            correccion_data
        )

        if success:
            messagebox.showinfo("Éxito", "Tu corrección ha sido enviada. ¡Gracias!", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo enviar la corrección. Intenta de nuevo.", parent=self)