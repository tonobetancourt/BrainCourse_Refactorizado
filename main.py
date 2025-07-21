# main.py (VERSIÓN FINAL Y COMPLETA)

import customtkinter as ctk
from tkinter import messagebox
import os

# Importar las nuevas capas
from ai_integration.ai_service import AIService
from services.auth_service import AuthService
from models.user_model import User 
from data import gestion_usuarios as user_dao 

# Importar las vistas de alumno
from views.student_onboarding_view import OnboardingWindow
from views.student_dashboard_view import StudentDashboardView
from views.settings_view import SettingsWindow 

# Importar las vistas de profesor
from views.teacher_onboarding_view import TeacherOnboardingWindow
from views.teacher_dashboard_view import TeacherDashboardView

# Importar los servicios principales
from services.learning_service import LearningService
from services.course_service import CourseService
from services.quality_control_service import QualityControlService 
from services.teacher_service import TeacherService 


# --- Inicialización Global de Servicios ---
api_key_path = os.path.join(os.path.dirname(__file__), 'api_key.txt')
try:
    ai_service = AIService()
    ai_service.initialize(api_key_path=api_key_path)
except Exception as e:
    messagebox.showerror("Error de Inicialización de IA", f"No se pudo cargar la API Key o iniciar el servicio de IA. Error: {e}\nPor favor, verifica 'api_key.txt'.")
    exit()

# Instancias de servicios principales
auth_service = AuthService(user_dao_module=user_dao) 
learning_service = LearningService(user_dao_module=auth_service.user_dao, ai_service_instance=ai_service)
course_service = CourseService(user_dao_module=auth_service.user_dao, ai_service_instance=ai_service)
quality_control_service = QualityControlService() 
teacher_service = TeacherService(auth_service_instance=auth_service, course_service_instance=course_service, qc_service_instance=quality_control_service)


# --- Ventanas de Autenticación (Login, Registro) ---
class RegisterWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Registro")
        self.geometry("400x450")
        self.transient(master) 
        self.grab_set()        
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Crear una cuenta nueva", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 10))

        ctk.CTkLabel(self, text="Soy un:").grid(row=1, column=0, padx=20, pady=(10,0), sticky="w")
        self.role_var = ctk.StringVar(value="Alumno")
        self.role_selector = ctk.CTkSegmentedButton(self, values=["Alumno", "Profesor"], variable=self.role_var)
        self.role_selector.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.name_entry = ctk.CTkEntry(self, placeholder_text="Nombre")
        self.name_entry.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Correo electrónico")
        self.email_entry.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*")
        self.password_entry.grid(row=5, column=0, padx=20, pady=10, sticky="ew")

        ctk.CTkButton(self, text="Registrarse", command=self.register_user).grid(row=6, column=0, padx=20, pady=20, sticky="ew")

    def register_user(self):
        nombre = self.name_entry.get().strip()
        correo = self.email_entry.get().strip()
        contrasena = self.password_entry.get().strip()
        rol = self.role_var.get().lower()

        if not all([nombre, correo, contrasena]):
            messagebox.showerror("Error", "Todos los campos son obligatorios.", parent=self)
            return

        if "@" not in correo or "." not in correo.split('@')[-1] or len(correo.split('@')[-1].split('.')) < 2:
            messagebox.showerror("Error de Formato", "Por favor, introduce un correo electrónico válido.", parent=self)
            return

        success, message_or_user = auth_service.registrar_usuario(nombre, correo, contrasena, rol)

        if success:
            messagebox.showinfo("Éxito", "¡Registro exitoso! Ahora puedes iniciar sesión.", parent=self)
            self.destroy()
        else:
            messagebox.showerror("Error de Registro", message_or_user, parent=self)


class LoginWindow(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master=master)
        self.master = master 

        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1) 

        ctk.CTkLabel(self, text="Iniciar Sesión en BrainCourse", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=50, pady=(50, 20))

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Correo electrónico", width=300)
        self.email_entry.grid(row=1, column=0, padx=50, pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=300)
        self.password_entry.grid(row=2, column=0, padx=50, pady=10)
        self.password_entry.bind("<Return>", self.login_user_event) 

        ctk.CTkButton(self, text="Iniciar Sesión", command=self.login_user, width=300).grid(row=3, column=0, padx=50, pady=20)

        register_frame = ctk.CTkFrame(self, fg_color="transparent")
        register_frame.grid(row=5, column=0, pady=(0, 50))
        ctk.CTkLabel(register_frame, text="¿No tienes una cuenta?").pack(side="left")
        ctk.CTkButton(register_frame, text="Regístrate aquí", fg_color="transparent", text_color=("blue", "lightblue"), command=self.open_register_window).pack(side="left")

    def login_user_event(self, event=None):
        self.login_user()

    def login_user(self):
        correo = self.email_entry.get().strip().lower()
        contrasena = self.password_entry.get().strip()

        if not correo or not contrasena:
            messagebox.showerror("Error", "Por favor, ingresa correo y contraseña.")
            return

        success, message_or_user_obj = auth_service.verificar_usuario(correo, contrasena)

        if success:
            current_user_obj: User = message_or_user_obj
            self.launch_app_based_on_role(current_user_obj)
        else:
            messagebox.showerror("Error de Inicio de Sesión", message_or_user_obj)

    def launch_app_based_on_role(self, user: User):
        self.destroy() 

        if not user.perfil_completo:
            if user.rol == 'profesor':
                TeacherOnboardingWindow(self.master, user, auth_service, ai_service, self.launch_final_app) 
            else: # Alumno
                OnboardingWindow(self.master, user, auth_service, ai_service, self.launch_final_app)
        else:
            self.launch_final_app(user)


    def launch_final_app(self, user: User):
        if user.rol == 'profesor':
            TeacherDashboardView(self.master, user, auth_service, ai_service, learning_service, course_service, quality_control_service, teacher_service)
        else: # Alumno
            StudentDashboardView(self.master, user, auth_service, ai_service, learning_service, course_service)

    def open_register_window(self):
        RegisterWindow(self.master)


# --- Punto de Entrada de la Aplicación ---
if __name__ == "__main__":
    ctk.set_appearance_mode("System") 
    ctk.set_default_color_theme("blue") 

    root = ctk.CTk()
    root.title("BrainCourse")
    root.geometry("1000x700")

    login_view = LoginWindow(root)

    root.mainloop()