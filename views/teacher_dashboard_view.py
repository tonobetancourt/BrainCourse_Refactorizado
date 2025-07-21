# views/teacher_dashboard_view.py (VERSIÓN FINAL Y COMPLETA)

import customtkinter as ctk
from tkinter import messagebox, simpledialog
import threading
import os
from PIL import Image, ImageTk 
from datetime import datetime

# Importar las capas de servicios y modelos
from models.user_model import User
from services.auth_service import AuthService
from services.teacher_service import TeacherService
from services.course_service import CourseService 
from services.quality_control_service import QualityControlService 
from services.learning_service import LearningService 
from ai_integration.ai_service import AIService 

# Importar las ventanas de soporte
from views.correction_window import CorrectionWindow
from views.quiz_review_window import QuizReviewWindow
from views.settings_view import SettingsWindow

class TeacherDashboardView(ctk.CTkFrame):
    def __init__(self, master, current_user: User, auth_service_instance: AuthService, ai_service_instance: AIService, learning_service_instance: LearningService, course_service_instance: CourseService, qc_service_instance: QualityControlService, teacher_service_instance: TeacherService):
        super().__init__(master=master) 
        
        self.master = master 
        self.current_user = current_user
        self.auth_service = auth_service_instance
        self.ai_service = ai_service_instance 
        self.learning_service = learning_service_instance
        self.course_service = course_service_instance
        self.qc_service = qc_service_instance
        self.teacher_service = teacher_service_instance
        
        self.user_dao = self.auth_service.user_dao 
        self.settings_window = None 
        self.gear_image_photo = None # Inicializar para evitar AttributeError si la imagen no carga

        self.grid(row=0, column=0, sticky="nsew") 
        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)
        
        self.master.title(f"Panel de Profesor - BrainCourse") 

        # Inicializar content_frame antes de cualquier llamada a métodos que lo usen
        self.setup_main_content_area()
        self.setup_sidebar()
        self.show_students_view() 

    def setup_sidebar(self):
        sidebar_frame = ctk.CTkFrame(self, width=250, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(5, weight=1) # Fila expandible para empujar botones inferiores

        ctk.CTkLabel(sidebar_frame, text=f"  Hola, Prof. {self.current_user.nombre}", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, padx=20, pady=20, sticky="w")

        ctk.CTkButton(sidebar_frame, text="👥 Mis Alumnos", command=self.show_students_view).grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(sidebar_frame, text="🚨 Reportes de IA", command=self.show_ai_reports_view).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(sidebar_frame, text="📚 Mis Cursos", command=self.show_teacher_courses_view).grid(row=3, column=0, padx=20, pady=10, sticky="ew") # ¡Botón de Mis Cursos!
        
        try:
            gear_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "gear_icon.png")
            self.gear_image_photo = ImageTk.PhotoImage(Image.open(gear_icon_path).resize((20, 20), Image.LANCZOS)) 
            self.settings_button = ctk.CTkButton(sidebar_frame, text=" Configuración", image=self.gear_image_photo, compound="left", command=self.open_settings_window)
        except Exception as e: 
            print(f"Advertencia: 'gear_icon.png' no encontrado o error al cargar: {e}")
            self.settings_button = ctk.CTkButton(sidebar_frame, text="⚙️ Configuración", command=self.open_settings_window)
        self.settings_button.grid(row=7, column=0, padx=20, pady=10, sticky="s")


        ctk.CTkButton(sidebar_frame, text="Cerrar Sesión", command=self.logout, fg_color="#D32F2F", hover_color="#B71C1C").grid(row=8, column=0, padx=20, pady=20, sticky="s")

    def logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Estás seguro de que quieres cerrar sesión?", parent=self.master):
            self.destroy()
            from main import LoginWindow 
            LoginWindow(self.master)

    def setup_main_content_area(self):
        self.content_frame = ctk.CTkScrollableFrame(self, label_text="Contenido Principal")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)


    def update_sidebar_name(self, new_name: str):
        """Callback para actualizar el nombre en la barra lateral después de un cambio en la configuración."""
        self.current_user.nombre = new_name 
        self.setup_sidebar()

    def open_settings_window(self):
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self.master, self.current_user, self.auth_service, self.update_sidebar_name, self.logout)
        else:
            self.settings_window.focus()

    def refresh_teacher_user_data(self):
        """Recarga los datos del profesor para asegurar que estén actualizados (ej. después de aceptar/rechazar solicitudes)."""
        all_users_data = self.user_dao.cargar_usuarios()
        updated_data = all_users_data.get(self.current_user.email, self.current_user.to_dict())
        self.current_user = User.from_dict(self.current_user.email, updated_data)
        self.setup_sidebar()

    def show_students_view(self):
        self.refresh_teacher_user_data() 
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(label_text="Gestión de Alumnos")
        
        invite_frame = ctk.CTkFrame(self.content_frame); invite_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(invite_frame, text="Invitar Alumno por Correo:", font=ctk.CTkFont(size=16)).pack(side="left", padx=10)
        self.invite_email_entry = ctk.CTkEntry(invite_frame, placeholder_text="alumno@ejemplo.com"); self.invite_email_entry.pack(side="left", padx=5, expand=True, fill="x")
        ctk.CTkButton(invite_frame, text="Invitar", command=self.invite_student).pack(side="left", padx=10)

        solicitudes_frame = ctk.CTkFrame(self.content_frame); solicitudes_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(solicitudes_frame, text="Solicitudes Pendientes", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        solicitudes = self.current_user.solicitudes_pendientes
        if not solicitudes:
            ctk.CTkLabel(solicitudes_frame, text="No tienes solicitudes pendientes.").pack(pady=5, padx=10)
        else:
            for email_alumno in solicitudes:
                req_frame = ctk.CTkFrame(solicitudes_frame); req_frame.pack(fill="x", pady=5, padx=10)
                ctk.CTkLabel(req_frame, text=email_alumno).pack(side="left", padx=10)
                ctk.CTkButton(req_frame, text="Rechazar", command=lambda e=email_alumno: self.handle_student_request(e, False)).pack(side="right", padx=5)
                ctk.CTkButton(req_frame, text="Aceptar", command=lambda e=email_alumno: self.handle_student_request(e, True)).pack(side="right", padx=5)
        
        alumnos_frame = ctk.CTkFrame(self.content_frame); alumnos_frame.pack(fill="x")
        ctk.CTkLabel(alumnos_frame, text="Mis Alumnos Vinculados", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        alumnos_vinculados_data = self.teacher_service.obtener_alumnos_vinculados_con_data(self.current_user)
        
        if not alumnos_vinculados_data:
            ctk.CTkLabel(alumnos_frame, text="Aún no tienes alumnos vinculados.").pack(pady=5, padx=10)
        else:
            for alumno_data in alumnos_vinculados_data:
                student_frame = ctk.CTkFrame(alumnos_frame); student_frame.pack(fill="x", pady=5, padx=10)
                ctk.CTkLabel(student_frame, text=f"{alumno_data['nombre']} ({alumno_data['email']})").pack(side="left", padx=10)
                ctk.CTkButton(student_frame, text="Desvincular", fg_color="red", command=lambda e=alumno_data['email']: self.unlink_student(e)).pack(side="right", padx=5)
                ctk.CTkButton(student_frame, text="Ver Progreso", command=lambda e=alumno_data['email']: self.show_student_details(e)).pack(side="right", padx=5)

    def invite_student(self):
        email_alumno = self.invite_email_entry.get().strip().lower()
        if not email_alumno: return

        success, message = self.teacher_service.invitar_alumno(self.current_user, email_alumno)
        if success:
            messagebox.showinfo("Éxito", message, parent=self.master)
            self.invite_email_entry.delete(0, 'end')
        else:
            messagebox.showerror("Error", message, parent=self.master)
        self.show_students_view()

    def handle_student_request(self, email_alumno: str, aceptar: bool):
        success, message = self.teacher_service.manejar_solicitud_alumno(self.current_user, email_alumno, aceptar)
        if success:
            messagebox.showinfo("Éxito", message, parent=self.master)
        else:
            messagebox.showerror("Error", message, parent=self.master)
        self.show_students_view()

    def unlink_student(self, email_alumno: str):
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres desvincular a {email_alumno}?", parent=self.master):
            success, message = self.teacher_service.desvincular_alumno(self.current_user, email_alumno)
            if success:
                messagebox.showinfo("Éxito", message, parent=self.master)
            else:
                messagebox.showerror("Error", message, parent=self.master)
            self.show_students_view()
    
    def show_student_details(self, email_alumno: str):
        all_alumnos_data = self.teacher_service.obtener_alumnos_vinculados_con_data(self.current_user)
        student_data = next((a for a in all_alumnos_data if a['email'] == email_alumno), None)
        
        if not student_data:
            messagebox.showerror("Error", "No se encontraron los datos del alumno."); return
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(label_text=f"Detalles de {student_data['nombre']}")

        ctk.CTkButton(self.content_frame, text="< Volver a Mis Alumnos", command=self.show_students_view).pack(anchor="w", pady=10)

        stats_frame = ctk.CTkFrame(self.content_frame); stats_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(stats_frame, text="Estadísticas Generales", font=ctk.CTkFont(size=16, weight="bold")).pack()
        
        preg_totales = student_data.get('preguntas_totales', 0)
        aciertos_totales = student_data.get('aciertos_totales', 0)
        porcentaje = (aciertos_totales / preg_totales * 100) if preg_totales > 0 else 0
        
        ctk.CTkLabel(stats_frame, text=f"Nivel: {student_data.get('nivel', 1)} | Preguntas: {preg_totales} | Aciertos: {porcentaje:.1f}%").pack(pady=5)

        courses_frame = ctk.CTkFrame(self.content_frame); courses_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(courses_frame, text="Cursos Asignados", font=ctk.CTkFont(size=16, weight="bold")).pack()
        
        cursos_alumno = student_data.get('cursos_asignados', [])
        if not cursos_alumno:
            ctk.CTkLabel(courses_frame, text="No tiene cursos asignados.").pack(pady=5)
        else:
            for curso in cursos_alumno:
                curso_row_frame = ctk.CTkFrame(courses_frame, fg_color="transparent")
                curso_row_frame.pack(fill="x", padx=10)
                progreso_curso = curso.get('progreso_general', 0)
                calificacion_promedio = curso.get('calificacion_promedio')
                
                curso_info_text = f"Curso: {curso.get('tema_general', 'N/A')} ({progreso_curso*100:.0f}%)"
                if calificacion_promedio is not None:
                    curso_info_text += f" | Nota: {calificacion_promedio:.1f}"

                ctk.CTkLabel(curso_row_frame, text=curso_info_text, wraplength=400, justify="left").pack(side="left", pady=5)
                
                ctk.CTkButton(curso_row_frame, text="🗑️", fg_color="red", width=40, command=lambda c_id=curso.get('id_curso'), a_email=student_data['email']: self.delete_course_from_student(a_email, c_id)).pack(side="right", padx=5)
                
                ctk.CTkButton(curso_row_frame, text="Revisar Contenido", command=lambda c=curso, a_email=student_data['email']: self.review_student_course_content(a_email, c.get('id_curso'))).pack(side="right", padx=5)

        ctk.CTkButton(courses_frame, text="Asignar Nuevo Curso", command=lambda e=email_alumno: self.assign_new_course_to_student(e)).pack(pady=10)

        history_frame = ctk.CTkFrame(self.content_frame); history_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(history_frame, text="Historial de Actividad Reciente", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10,5))
        
        historial = student_data.get('historial_actividad_reciente', [])
        if not historial:
            ctk.CTkLabel(history_frame, text="Sin actividad reciente registrada.").pack(pady=5)
        else:
            for actividad in historial:
                act_frame = ctk.CTkFrame(history_frame); act_frame.pack(fill="x", pady=4)
                fecha = datetime.fromisoformat(actividad['fecha']).strftime('%d/%m/%Y %H:%M')
                
                act_text = f"{fecha} - {actividad.get('tipo', 'Actividad')}: {actividad.get('tema', 'N/A')} ({actividad.get('resultado', 'N/A')})"
                if actividad.get('pregunta') and actividad.get('fue_correcta') is not None:
                    act_text += f"\nPregunta: {actividad.get('pregunta', 'N/A')} - Respuesta: {'Correcta' if actividad.get('fue_correcta', False) else 'Incorrecta'}"

                ctk.CTkLabel(act_frame, text=act_text, wraplength=600, justify="left").pack(side="left", padx=10)
                
                if actividad.get('preguntas') is not None and isinstance(actividad.get('preguntas'), list):
                    ctk.CTkButton(act_frame, text="Revisar Detalle", width=80, command=lambda a=actividad: QuizReviewWindow(self.master, self.current_user, self.teacher_service, a)).pack(side="right", padx=10, pady=5)


    def delete_course_from_student(self, email_alumno: str, id_curso: str):
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres eliminar este curso del perfil de {email_alumno}?", parent=self.master):
            alumno_full_data = self.user_dao.cargar_usuarios().get(email_alumno)
            if not alumno_full_data:
                messagebox.showerror("Error", "Datos del alumno no encontrados.", parent=self.master); return
            alumno_user_obj = User.from_dict(email_alumno, alumno_full_data)

            success = self.course_service.eliminar_curso_de_usuario(alumno_user_obj, id_curso) 
            
            if success:
                messagebox.showinfo("Éxito", "Curso eliminado del alumno.", parent=self.master)
            else:
                messagebox.showerror("Error", "No se pudo eliminar el curso del alumno.", parent=self.master)
            
            self.show_student_details(email_alumno)

    def assign_new_course_to_student(self, email_alumno: str):
        tema = simpledialog.askstring("Asignar Curso", "Escribe el tema para el nuevo curso:", parent=self.master)
        if not tema or not tema.strip(): return

        messagebox.showinfo("Asignando Curso", "Generando y asignando curso. Esto puede tardar un momento.", parent=self.master)
        
        def _assign_in_thread():
            success, message = self.teacher_service.asignar_curso_a_alumno(self.current_user, email_alumno, tema)
            self.master.after(0, lambda: self._process_assign_course_result(success, message, email_alumno))
        
        threading.Thread(target=_assign_in_thread).start()

    def _process_assign_course_result(self, success: bool, message: str, email_alumno: str):
        if success:
            messagebox.showinfo("Éxito", message, parent=self.master)
        else:
            messagebox.showerror("Error", message, parent=self.master)
        self.show_student_details(email_alumno)

    def review_student_course_content(self, email_alumno: str, id_curso: str):
        alumno_full_data = self.user_dao.cargar_usuarios().get(email_alumno)
        if not alumno_full_data:
            messagebox.showerror("Error", "Datos del alumno no encontrados para revisar el curso.", parent=self.master); return

        alumno_user_obj = User.from_dict(email_alumno, alumno_full_data)
        curso_activo_alumno = alumno_user_obj.encontrar_curso(id_curso)
        if not curso_activo_alumno:
            messagebox.showerror("Error", "Curso no encontrado en el perfil del alumno."); return
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(label_text=f"Revisando Curso: {curso_activo_alumno.get('tema_general', 'N/A')} de {alumno_user_obj.nombre}")

        ctk.CTkButton(self.content_frame, text=f"< Volver a los detalles de {alumno_user_obj.nombre}", command=lambda e=alumno_user_obj.email: self.show_student_details(e)).pack(anchor="w", pady=10)
        
        for modulo in curso_activo_alumno['modulos']:
            modulo_frame = ctk.CTkFrame(self.content_frame)
            modulo_frame.pack(fill="x", pady=5)
            
            estado = "✅" if modulo.get('completado') else "📖"
            calificacion = f"Nota: {modulo.get('calificacion_examen')}" if modulo.get('completado') and modulo.get('calificacion_examen') is not None else ""
            label_texto = f"{estado} {modulo.get('titulo', 'Módulo')} {calificacion}"
            
            ctk.CTkLabel(modulo_frame, text=label_texto, anchor="w").pack(side="left", padx=10, pady=10)
            
            ctk.CTkButton(modulo_frame, text="Ver Contenido Teórico", command=lambda m=modulo: self.review_student_module_content(m)).pack(side="right", padx=10)

    def review_student_module_content(self, modulo: dict):
        review_window = ctk.CTkToplevel(self.master)
        review_window.title(f"Teoría: {modulo.get('titulo', 'Módulo')}")
        review_window.geometry("700x500")
        review_window.transient(self.master)
        review_window.grab_set()

        textbox = ctk.CTkTextbox(review_window, wrap="word")
        textbox.pack(fill="both", expand=True, padx=10, pady=10)

        contenido_completo = ""
        teoria_generada = modulo.get('teoria_generada', {})
        if teoria_generada:
            for subtema, teoria in teoria_generada.items():
                contenido_completo += f"--- {subtema} ---\n\n{teoria}\n\n"
        else:
            contenido_completo = "El alumno aún no ha generado el contenido teórico para este módulo."
        
        textbox.insert("1.0", contenido_completo)
        textbox.configure(state="disabled")

    def show_ai_reports_view(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(label_text="Reportes de Errores de IA")

        ctk.CTkLabel(self.content_frame, text="Lista de Reportes de Errores", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        
        reportes = self.qc_service.obtener_reportes()

        if not reportes:
            ctk.CTkLabel(self.content_frame, text="No hay reportes de errores de IA.").pack(pady=5)
        else:
            for reporte in reportes:
                report_frame = ctk.CTkFrame(self.content_frame); report_frame.pack(fill="x", pady=5, padx=10)
                report_frame.grid_columnconfigure(0, weight=1)
                report_frame.grid_columnconfigure(1, weight=0)

                fecha = datetime.fromisoformat(reporte['fecha']).strftime('%d/%m/%Y %H:%M')
                profesor_email = reporte.get('email_profesor', 'Desconocido')
                pregunta_original = reporte.get('pregunta_original_data', {}).get('pregunta', 'N/A')
                respuesta_ia = reporte.get('pregunta_original_data', {}).get('respuesta_correcta_ia', 'N/A')
                respuesta_profesor = reporte.get('correccion_profesor', {}).get('respuesta_profesor', 'N/A')
                justificacion = reporte.get('correccion_profesor', {}).get('justificacion', 'Sin justificación')
                estado = reporte.get('estado', 'pendiente').capitalize()

                report_text = (
                    f"ID: {reporte['id_reporte']} | Fecha: {fecha} | Profesor: {profesor_email}\n"
                    f"Estado: {estado}\n"
                    f"Pregunta (IA): {pregunta_original}\n"
                    f"Respuesta IA: {respuesta_ia}\n"
                    f"Respuesta Profesor: {respuesta_profesor}\n"
                    f"Justificación: {justificacion}"
                )
                ctk.CTkLabel(report_frame, text=report_text, wraplength=700, justify="left").grid(row=0, column=0, sticky="w", padx=10, pady=5)
                
                if estado == "Pendiente":
                    ctk.CTkButton(report_frame, text="Marcar como Revisado", command=lambda r_id=reporte['id_reporte']: self.mark_report_reviewed(r_id)).grid(row=0, column=1, sticky="e", padx=10)
                else:
                    ctk.CTkLabel(report_frame, text=f"Estado: {estado}", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="e", padx=10)


        def mark_report_reviewed(self, reporte_id: str):
            if messagebox.askyesno("Marcar como Revisado", f"¿Marcar reporte {reporte_id} como 'Revisado'?", parent=self.master):
                success = self.qc_service.actualizar_estado_reporte(reporte_id, "revisado")
                if success:
                    messagebox.showinfo("Éxito", f"Reporte {reporte_id} marcado como 'Revisado'.", parent=self.master)
                else:
                    messagebox.showerror("Error", f"No se pudo actualizar el reporte {reporte_id}.", parent=self.master)
                self.show_ai_reports_view()


    def show_teacher_courses_view(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(label_text="Mis Cursos")

        ctk.CTkButton(self.content_frame, text="➕ Crear Nuevo Curso", command=self.create_new_course).pack(pady=10)

        cursos = self.course_service.obtener_cursos_de_usuario(self.current_user)
        if not cursos:
            ctk.CTkLabel(self.content_frame, text="Aún no has creado cursos.").pack(pady=10)
        else:
            for course in cursos:
                curso_frame = ctk.CTkFrame(self.content_frame)
                curso_frame.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(curso_frame, text=course.tema_general, font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
                ctk.CTkButton(curso_frame, text="Editar Título", command=lambda c=course: self.edit_course_title(c)).pack(side="right", padx=10)
                ctk.CTkButton(curso_frame, text="Ver Contenido", command=lambda c=course: self.view_course_content(c)).pack(side="right", padx=10)
                miembros_str = ", ".join([f"{m['email']} ({m['rol']})" for m in course.miembros])
                ctk.CTkLabel(curso_frame, text=f"Miembros: {miembros_str}").pack(side="left", padx=10)

    def view_course_content(self, course):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.content_frame.configure(label_text=f"Contenido del Curso: {course.tema_general}")

        ctk.CTkButton(self.content_frame, text="< Volver a Mis Cursos", command=self.show_teacher_courses_view).pack(anchor="w", pady=10)
        ctk.CTkLabel(self.content_frame, text=f"Tema: {course.tema_general}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=5)
        ctk.CTkLabel(self.content_frame, text=f"ID: {course.id_curso}").pack(pady=2)

        # --- Gestión de miembros del curso ---
        miembros_frame = ctk.CTkFrame(self.content_frame)
        miembros_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(miembros_frame, text="Miembros del Curso:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=5)
        for miembro in course.miembros:
            if miembro['rol'] == 'profesor':
                ctk.CTkLabel(miembros_frame, text=f"👨‍🏫 {miembro['email']} (profesor)", text_color="blue").pack(anchor="w", padx=15)
            else:
                alumno_row = ctk.CTkFrame(miembros_frame, fg_color="transparent")
                alumno_row.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(alumno_row, text=f"👤 {miembro['email']} (alumno)").pack(side="left")
                ctk.CTkButton(alumno_row, text="Quitar", fg_color="red", width=60, command=lambda e=miembro['email'], c=course: self.remove_student_from_course(c, e)).pack(side="right", padx=5)

        # --- Agregar alumno al curso ---
        add_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        add_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(add_frame, text="Agregar alumno por correo:", font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        self.add_student_entry = ctk.CTkEntry(add_frame, placeholder_text="alumno@ejemplo.com")
        self.add_student_entry.pack(side="left", padx=5)
        ctk.CTkButton(add_frame, text="Agregar", command=lambda c=course: self.add_student_to_course(c)).pack(side="left", padx=5)

        # --- Estructura del curso ---
        ctk.CTkLabel(self.content_frame, text="Módulos:", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        for modulo in course.modulos:
            modulo_frame = ctk.CTkFrame(self.content_frame)
            modulo_frame.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(modulo_frame, text=modulo.get('titulo', 'Módulo'), font=ctk.CTkFont(size=14)).pack(anchor="w", padx=10)
            ctk.CTkButton(modulo_frame, text="Editar Título", width=80, command=lambda m=modulo, c=course: self.edit_module_title(c, m)).pack(anchor="e", padx=5)
            for subtema in modulo.get('subtemas', []):
                subtema_frame = ctk.CTkFrame(modulo_frame, fg_color="transparent")
                subtema_frame.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(subtema_frame, text=f"• {subtema}", wraplength=500, justify="left").pack(side="left", padx=5)
                ctk.CTkButton(subtema_frame, text="Editar Teoría", width=100, command=lambda s=subtema, m=modulo, c=course: self.edit_subtema_theory(c, m, s)).pack(side="right", padx=5)
                teoria_actual = modulo.get('teoria_generada', {}).get(subtema)
                if teoria_actual:
                    ctk.CTkLabel(subtema_frame, text="(Teoría personalizada)", text_color="green").pack(side="left", padx=5)
                else:
                    ctk.CTkLabel(subtema_frame, text="(Sin teoría)", text_color="red").pack(side="left", padx=5)

    def add_student_to_course(self, course):
        email = self.add_student_entry.get().strip().lower()
        if not email:
            messagebox.showerror("Error", "Debes ingresar un correo.", parent=self.master)
            return
        # Verifica si ya es miembro
        if any(m['email'] == email for m in course.miembros):
            messagebox.showinfo("Ya es miembro", f"{email} ya es miembro de este curso.", parent=self.master)
            return
        # Verifica que el usuario exista y sea alumno
        from data import gestion_usuarios as user_dao
        usuarios = user_dao.cargar_usuarios()
        if email not in usuarios or usuarios[email].get('rol') != 'alumno':
            messagebox.showerror("Error", "No se encontró un alumno con ese correo.", parent=self.master)
            return
        # Agrega al curso y al usuario
        from models.user_model import User
        alumno = User.from_dict(email, usuarios[email])
        from models.course_model import Course
        # Actualiza el curso (agrega miembro)
        course.miembros.append({'email': email, 'rol': 'alumno'})
        # Actualiza el usuario (agrega curso)
        if not any(c['id_curso'] == course.id_curso for c in alumno.cursos):
            alumno.cursos.append(course.to_dict())
        # Persistencia
        from data import gestion_cursos as course_dao
        course_dao.actualizar_curso(course.to_dict())
        user_dao.actualizar_datos_usuario(email, alumno.to_dict())
        messagebox.showinfo("Éxito", f"{email} ha sido agregado al curso.", parent=self.master)
        self.view_course_content(course)

    def remove_student_from_course(self, course, email):
        # Quita al alumno del curso y el curso del alumno
        course.miembros = [m for m in course.miembros if m['email'] != email]
        from data import gestion_usuarios as user_dao
        usuarios = user_dao.cargar_usuarios()
        if email in usuarios:
            alumno = User.from_dict(email, usuarios[email])
            alumno.cursos = [c for c in alumno.cursos if c['id_curso'] != course.id_curso]
            user_dao.actualizar_datos_usuario(email, alumno.to_dict())
        from data import gestion_cursos as course_dao
        course_dao.actualizar_curso(course.to_dict())
        messagebox.showinfo("Eliminado", f"{email} ha sido eliminado del curso.", parent=self.master)
        self.view_course_content(course)

    def edit_module_title(self, course, modulo):
        new_title = simpledialog.askstring("Editar Módulo", "Nuevo título del módulo:", initialvalue=modulo.get('titulo', ''), parent=self.master)
        if new_title and new_title.strip():
            modulo['titulo'] = new_title.strip()
            from data import gestion_cursos as course_dao
            course_dao.actualizar_curso(course.to_dict())
            messagebox.showinfo("Éxito", "Título del módulo actualizado.", parent=self.master)
            self.view_course_content(course)

    def edit_subtema_theory(self, course, modulo, subtema):
        edit_win = ctk.CTkToplevel(self.master)
        edit_win.title(f"Editar Teoría: {subtema}")
        edit_win.geometry("700x500")
        edit_win.transient(self.master)
        edit_win.grab_set()

        ctk.CTkLabel(edit_win, text=f"Editar teoría para: {subtema}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        textbox = ctk.CTkTextbox(edit_win, wrap="word")
        textbox.pack(fill="both", expand=True, padx=10, pady=10)

        teoria_actual = modulo.get('teoria_generada', {}).get(subtema, "")
        textbox.insert("1.0", teoria_actual)

        def generar_con_ia():
            from services import curso_generator
            teoria_ia = curso_generator.generar_teoria_subtema(subtema, self.ai_service)
            textbox.delete("1.0", "end")
            textbox.insert("1.0", teoria_ia)

        def guardar_teoria():
            nueva_teoria = textbox.get("1.0", "end-1c").strip()
            if not nueva_teoria:
                messagebox.showerror("Error", "La teoría no puede estar vacía.", parent=edit_win)
                return
            if 'teoria_generada' not in modulo:
                modulo['teoria_generada'] = {}
            modulo['teoria_generada'][subtema] = nueva_teoria
            from data import gestion_cursos as course_dao
            course_dao.actualizar_curso(course.to_dict())
            messagebox.showinfo("Éxito", "Teoría actualizada correctamente. Todos los alumnos verán esta versión.", parent=edit_win)
            edit_win.destroy()
            self.view_course_content(course)

        ctk.CTkButton(edit_win, text="Generar con IA", command=generar_con_ia).pack(pady=5)
        ctk.CTkButton(edit_win, text="Guardar Teoría", command=guardar_teoria).pack(pady=10)

    def create_new_course(self):
        tema = simpledialog.askstring("Nuevo Curso", "Escribe el tema general para tu nuevo curso:", parent=self.master)
        if not tema or not tema.strip():
            return
        messagebox.showinfo("Generando Curso", "La IA está diseñando tu curso. Esto puede tardar un momento.", parent=self.master)
        def _generar_en_hilo():
            course = self.course_service.crear_curso(self.current_user, tema)
            self.master.after(0, lambda: self._procesar_resultado_curso_generado(course, tema))
        threading.Thread(target=_generar_en_hilo).start()

    def _procesar_resultado_curso_generado(self, course, tema):
        if course:
            messagebox.showinfo("¡Curso Creado!", f"Tu curso sobre '{tema}' ha sido creado.", parent=self.master)
            self.show_teacher_courses_view()
        else:
            messagebox.showerror("Error", "No se pudo generar el sílabo para el curso.", parent=self.master)

    def edit_course_title(self, course):
        new_title = simpledialog.askstring("Editar Curso", "Nuevo título del curso:", initialvalue=course.tema_general, parent=self.master)
        if new_title and new_title.strip():
            course.tema_general = new_title.strip()
            from data import gestion_cursos as course_dao
            course_dao.actualizar_curso(course.to_dict())
            messagebox.showinfo("Éxito", "Título del curso actualizado.", parent=self.master)
            self.show_teacher_courses_view()