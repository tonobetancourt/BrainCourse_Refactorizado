# views/teacher_onboarding_view.py (Implementación REAL)

import customtkinter as ctk
from tkinter import messagebox
from models.user_model import User
from services.auth_service import AuthService
from ai_integration.ai_service import AIService # Aunque no la use directamente, se pasa por consistencia
from services.teacher_service import TeacherService # Necesario para interactuar con TeacherService

class TeacherOnboardingWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user: User, auth_service_instance: AuthService, ai_service_instance: AIService, callback_final):
        super().__init__(master)
        self.master = master
        self.current_user = current_user
        self.auth_service = auth_service_instance
        self.ai_service = ai_service_instance # Se pasa pero no se usa directamente en el onboarding
        # Aunque TeacherService no se usa en el onboarding, lo inicializamos aquí
        # para que el callback_final pueda pasar todos los servicios al TeacherDashboardView.
        # No hay problema con que se cree una instancia temprana aquí.
        self.teacher_service = TeacherService(auth_service_instance, None, None) # Course y QC Services se pasan después

        self.callback_final = callback_final

        self.title("Perfil de Profesor")
        self.geometry("600x500")
        self.transient(master)
        self.grab_set()

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        self.form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.form_frame, text=f"¡Bienvenido, Prof. {self.current_user.nombre}! Completa tu Perfil", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, columnspan=2, padx=20, pady=(10, 20))

        ctk.CTkLabel(self.form_frame, text="Carrera:", anchor="w").grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.career_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: Licenciatura en Matemáticas Aplicadas")
        self.career_entry.grid(row=1, column=1, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(self.form_frame, text="Nivel Académico Máximo:", anchor="w").grid(row=2, column=0, padx=20, pady=10, sticky="w")
        self.academic_level_var = ctk.StringVar(value="Licenciatura/Ingeniería")
        self.academic_level_menu = ctk.CTkOptionMenu(self.form_frame, variable=self.academic_level_var, values=["Licenciatura/Ingeniería", "Maestría", "Doctorado", "Postdoctorado"])
        self.academic_level_menu.grid(row=2, column=1, padx=20, pady=10, sticky="ew")

        ctk.CTkLabel(self.form_frame, text="Institución donde labora:", anchor="w").grid(row=3, column=0, padx=20, pady=10, sticky="w")
        self.institution_entry = ctk.CTkEntry(self.form_frame, placeholder_text="Ej: Universidad Autónoma")
        self.institution_entry.grid(row=3, column=1, padx=20, pady=10, sticky="ew")

        ctk.CTkButton(self.form_frame, text="Guardar Perfil y Continuar", command=self.save_teacher_profile).grid(row=4, column=0, columnspan=2, padx=20, pady=30, sticky="ew")

    def save_teacher_profile(self):
        carrera = self.career_entry.get().strip()
        nivel_academico = self.academic_level_var.get()
        institucion = self.institution_entry.get().strip()

        if not all([carrera, nivel_academico, institucion]):
            messagebox.showerror("Campos Incompletos", "Por favor, completa todos los campos.", parent=self)
            return
        
        datos_perfil_profesor = {
            "carrera": carrera,
            "nivel_academico": nivel_academico,
            "institucion": institucion
        }

        # Actualizar el objeto User con los nuevos datos del perfil y marcarlo como completo
        self.current_user.perfil_completo = True
        self.current_user.datos_perfil.update(datos_perfil_profesor)

        # Persistir los cambios usando el AuthService
        self.auth_service.actualizar_perfil_inicial(self.current_user, datos_perfil_profesor)

        messagebox.showinfo("Perfil Completo", "Tu perfil de profesor ha sido guardado.", parent=self)
        self.destroy()
        self.callback_final(self.current_user) # Llamar al callback final para lanzar el dashboard principal

        # Stub para evitar errores si no está implementado
        ctk.CTkLabel(self, text="Onboarding de Profesor (en desarrollo)").pack(pady=50)
        ctk.CTkButton(self, text="Continuar", command=lambda: self.finalizar(self.callback_final, self.current_user)).pack(pady=20)

    def finalizar(self, callback, user):
        self.destroy()
        callback(user)