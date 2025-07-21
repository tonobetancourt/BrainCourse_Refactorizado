# views/settings_view.py

import customtkinter as ctk
from tkinter import messagebox, simpledialog
import os

from models.user_model import User
from services.auth_service import AuthService
from data import gestion_usuarios as user_dao # Usado para la lógica de vinculación profesor/alumno por ahora (podría ir en un servicio)

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user: User, auth_service_instance: AuthService, update_name_callback, logout_callback):
        super().__init__(master)
        self.app = master # Referencia a la ventana principal (root)
        self.current_user = current_user
        self.auth_service = auth_service_instance
        self.update_name_callback = update_name_callback # Callback para actualizar el nombre en la barra lateral de la app principal
        self.logout_callback = logout_callback # Callback para cerrar sesión desde la app principal

        self.title("Configuración")
        self.geometry("600x550")
        self.transient(master) # Mantener encima de la ventana principal
        self.grab_set()        # Bloquear interacciones con la ventana principal

        self.tab_view = ctk.CTkTabview(self, width=580)
        self.tab_view.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_view.add("Perfil")
        if self.current_user.rol == 'alumno':
            self.tab_view.add("Vincular Profesor")
        self.tab_view.add("Apariencia")
        self.tab_view.add("Acerca de")

        self.setup_profile_tab()
        self.setup_appearance_tab()
        self.setup_about_tab()
        if self.current_user.rol == 'alumno':
            self.setup_link_teacher_tab()

    def setup_profile_tab(self):
        profile_frame = self.tab_view.tab("Perfil")
        profile_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(profile_frame, text="Nombre:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_entry = ctk.CTkEntry(profile_frame)
        self.name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.name_entry.insert(0, self.current_user.nombre)

        ctk.CTkLabel(profile_frame, text="Nivel de Estudios:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.study_level_var = ctk.StringVar(value=self.current_user.datos_perfil.get('nivel_estudios', 'Primaria'))
        self.study_level_menu = ctk.CTkOptionMenu(profile_frame, variable=self.study_level_var, values=["Primaria", "Secundaria/Preparatoria", "Universidad"])
        self.study_level_menu.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkButton(profile_frame, text="Guardar Cambios de Perfil", command=self.save_profile_changes).grid(row=2, column=0, columnspan=2, padx=10, pady=(20,5), sticky="ew")

        ctk.CTkLabel(profile_frame, text="--- Zona de Peligro ---", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, columnspan=2, pady=(20, 5))
        ctk.CTkButton(profile_frame, text="Eliminar mi Cuenta Permanentemente", fg_color="red", hover_color="#B71C1C", command=self.delete_account).grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    def save_profile_changes(self):
        new_name = self.name_entry.get().strip()
        new_level = self.study_level_var.get()

        if not new_name:
            messagebox.showerror("Error", "El nombre no puede estar vacío.", parent=self)
            return

        # Crear un diccionario con los datos a actualizar para el AuthService
        datos_para_actualizar = {
            'nombre': new_name,
            'datos_perfil': {'nivel_estudios': new_level} # Solo actualizar esta parte específica de datos_perfil
        }
        
        # Usar AuthService para actualizar y persistir los datos del User
        self.auth_service.actualizar_datos_generales_usuario(self.current_user, datos_para_actualizar)

        self.update_name_callback(new_name) # Callback para actualizar el nombre en la barra lateral de la app principal
        messagebox.showinfo("Éxito", "Tus datos han sido actualizados.", parent=self)

    def delete_account(self):
        if not messagebox.askyesno("Confirmación Crítica", "Esta acción es irreversible. ¿Estás absolutamente seguro de que quieres eliminar tu cuenta y todos tus datos?", icon="warning", parent=self):
            return
        
        password = simpledialog.askstring("Verificación Final", "Para confirmar, por favor, introduce tu contraseña:", show='*', parent=self)
        if not password: # Usuario canceló o no ingresó contraseña
            return

        success, message = self.auth_service.eliminar_cuenta(self.current_user.email, password)

        if success:
            messagebox.showinfo("Cuenta Eliminada", message, parent=self.app)
            self.destroy() # Cerrar ventana de configuración
            self.logout_callback(force=True) # Cerrar sesión de la aplicación principal
        else:
            messagebox.showerror("Error", message, parent=self)

    def setup_link_teacher_tab(self):
        link_frame = self.tab_view.tab("Vincular Profesor")
        link_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(link_frame, text="Conecta con tus profesores para compartir tu progreso.", wraplength=500).pack(pady=10)

        # --- Invitaciones Pendientes ---
        invitaciones = self.current_user.invitaciones_profesor
        if invitaciones:
            inv_frame = ctk.CTkFrame(link_frame); inv_frame.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(inv_frame, text="Invitaciones de Profesores Pendientes", font=ctk.CTkFont(weight="bold")).pack()
            for email_prof in invitaciones:
                req_frame = ctk.CTkFrame(inv_frame); req_frame.pack(fill="x", pady=5)
                ctk.CTkLabel(req_frame, text=email_prof).pack(side="left", padx=10)
                ctk.CTkButton(req_frame, text="Rechazar", command=lambda e=email_prof: self.handle_invitation(e, False)).pack(side="right", padx=5)
                ctk.CTkButton(req_frame, text="Aceptar", command=lambda e=email_prof: self.handle_invitation(e, True)).pack(side="right", padx=5)

        # --- Profesores Vinculados ---
        profesores_actuales = self.current_user.profesores_vinculados
        ctk.CTkLabel(link_frame, text="Profesores Vinculados", font=ctk.CTkFont(weight="bold")).pack(pady=(10,0))
        if not profesores_actuales:
            ctk.CTkLabel(link_frame, text="Aún no estás vinculado a ningún profesor.").pack()
        else:
            for email_prof in profesores_actuales: 
                prof_frame = ctk.CTkFrame(link_frame, fg_color="transparent")
                prof_frame.pack(fill="x", padx=20)
                ctk.CTkLabel(prof_frame, text=f"- {email_prof}", text_color="green").pack(side="left", pady=2)
        
        # --- Enviar Nueva Solicitud ---
        ctk.CTkLabel(link_frame, text="Enviar Nueva Solicitud a un Profesor", font=ctk.CTkFont(weight="bold")).pack(pady=(20,0))
        self.teacher_email_entry = ctk.CTkEntry(link_frame, placeholder_text="profesor@ejemplo.com")
        self.teacher_email_entry.pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(link_frame, text="Enviar Solicitud de Vinculación", command=self.send_link_request).pack(pady=10)

    def handle_invitation(self, profesor_email: str, aceptar: bool):
        """Gestiona la respuesta de un alumno a la invitación de un profesor."""
        # Cargar todos los usuarios para actualizar los datos del profesor
        all_users_data = user_dao.cargar_usuarios()
        profesor_data_dict = all_users_data.get(profesor_email)
        
        if not profesor_data_dict:
            messagebox.showerror("Error", "Profesor no encontrado en el sistema.", parent=self); return
        
        # Convertir el diccionario de datos del profesor a un objeto User
        profesor_user_obj = User.from_dict(profesor_email, profesor_data_dict)

        if aceptar:
            # Actualizar el lado del alumno (usa el método del User model)
            self.current_user.aceptar_invitacion(profesor_email)
            # Actualizar el lado del profesor (agrega al alumno a vinculados)
            # No usamos .recibir_solicitud_alumno porque esto es una invitación directa aceptada
            if self.current_user.email not in profesor_user_obj.alumnos_vinculados:
                profesor_user_obj.alumnos_vinculados.append(self.current_user.email)
            profesor_user_obj.agregar_notificacion(f"El alumno {self.current_user.nombre} ha aceptado tu invitación.")
        else:
            self.current_user.rechazar_invitacion(profesor_email)
            profesor_user_obj.agregar_notificacion(f"El alumno {self.current_user.nombre} ha rechazado tu invitación.")

        # Persistir los cambios en ambos usuarios
        user_dao.actualizar_datos_usuario(self.current_user.email, self.current_user.to_dict())
        user_dao.actualizar_datos_usuario(profesor_email, profesor_user_obj.to_dict())

        messagebox.showinfo("Gestión de Invitación", f"Has {'aceptado' if aceptar else 'rechazado'} la invitación de {profesor_email}.", parent=self)
        self.refresh_link_teacher_tab() # Refrescar la UI de la pestaña

    def send_link_request(self):
        profesor_email = self.teacher_email_entry.get().strip().lower()
        if not profesor_email:
            messagebox.showerror("Error", "El email del profesor no puede estar vacío.", parent=self); return
        
        # Cargar todos los usuarios para verificar y actualizar al profesor
        all_users_data = user_dao.cargar_usuarios()
        profesor_data_dict = all_users_data.get(profesor_email)

        if not profesor_data_dict or profesor_data_dict.get('rol') != 'profesor':
            messagebox.showerror("Error", "No se encontró un profesor con ese correo o el usuario no es un profesor.", parent=self); return
        
        # Convertir el diccionario de datos del profesor a un objeto User
        profesor_user_obj = User.from_dict(profesor_email, profesor_data_dict)

        # Verificar si la solicitud ya fue enviada o si ya están vinculados
        if profesor_email in self.current_user.solicitudes_enviadas or profesor_email in self.current_user.profesores_vinculados:
            messagebox.showinfo("Información", "Ya has enviado una solicitud a este profesor o ya están vinculados.", parent=self); return

        # Actualizar el lado del alumno (usa el método del User model)
        self.current_user.enviar_solicitud_vinculacion(profesor_email)
        
        # Actualizar el lado del profesor (recibir solicitud del alumno)
        profesor_user_obj.recibir_solicitud_alumno(self.current_user.email)
        profesor_user_obj.agregar_notificacion(f"El alumno {self.current_user.nombre} te ha enviado una solicitud de vinculación.")

        # Persistir los cambios en ambos usuarios
        user_dao.actualizar_datos_usuario(self.current_user.email, self.current_user.to_dict())
        user_dao.actualizar_datos_usuario(profesor_email, profesor_user_obj.to_dict())

        messagebox.showinfo("Éxito", "Solicitud enviada. Tu profesor debe aceptarla.", parent=self)
        self.refresh_link_teacher_tab() # Refrescar la UI de la pestaña

    def refresh_link_teacher_tab(self):
        # Limpiar y volver a dibujar el contenido de la pestaña para reflejar los datos actualizados
        for widget in self.tab_view.tab("Vincular Profesor").winfo_children():
            widget.destroy()
        
        # Recargar el objeto current_user para asegurar los datos más recientes desde el disco
        # Se usa el verificar_usuario del auth_service para recargar el objeto User
        # NOTA: Esto es un poco hacky porque verificar_usuario espera la contraseña en texto plano,
        # pero el objeto User solo tiene el hash. Una mejor solución sería un método en AuthService
        # como `get_user_by_email_and_reload(email)` que solo cargue y convierta.
        # Por simplicidad ahora, haremos una carga directa y recrearemos el objeto User.
        print("Recargando datos del usuario para SettingsWindow...")
        all_users = user_dao.cargar_usuarios()
        user_data_reloaded = all_users.get(self.current_user.email)
        if user_data_reloaded:
            self.current_user = User.from_dict(self.current_user.email, user_data_reloaded)
        else:
            print(f"Error: No se pudo recargar el usuario {self.current_user.email}")


        self.setup_link_teacher_tab() # Volver a dibujar la pestaña

    def setup_appearance_tab(self):
        appearance_frame = self.tab_view.tab("Apariencia")
        appearance_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(appearance_frame, text="Modo de Apariencia:", anchor="w").grid(row=0, column=0, padx=20, pady=(10, 0), sticky="w")
        self.appearance_mode_menu = ctk.CTkOptionMenu(appearance_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_menu.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkLabel(appearance_frame, text="Tema de Color:", anchor="w").grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        self.color_theme_menu = ctk.CTkOptionMenu(appearance_frame, values=["blue", "dark-blue", "green"], command=self.change_color_theme_event)
        self.color_theme_menu.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        self.appearance_mode_menu.set(ctk.get_appearance_mode()) # Establecer modo actual
        # No hay una forma fácil de obtener el tema de color actual de CustomTkinter, por defecto es "blue"

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def change_color_theme_event(self, new_color_theme: str):
        ctk.set_default_color_theme(new_color_theme)
        messagebox.showinfo("Reinicio requerido", "El cambio se aplicará la próxima vez que inicies la aplicación.", parent=self)

    def setup_about_tab(self):
        about_frame = self.tab_view.tab("Acerca de")
        info_text = ("BrainCourse v4.0 (Refactorizado)\n\nUna plataforma de aprendizaje adaptativo por IA.\n\nRealizada por: Jesús Olvera y Asistente IA\nTecnologías: Python, CustomTkinter, Gemini, Matplotlib")
        ctk.CTkLabel(about_frame, text=info_text, justify="left", font=ctk.CTkFont(size=14)).pack(padx=20, pady=20, anchor="w")