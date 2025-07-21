# views/student_dashboard_view.py

import customtkinter as ctk
import os
from tkinter import messagebox, simpledialog
import threading
from PIL import Image, ImageTk 
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importar las capas de servicios y modelos
from models.user_model import User
from data import gestion_usuarios as user_dao # Usado para guardar cambios del usuario (persistir)
from services.auth_service import AuthService
from services.learning_service import LearningService
from services.course_service import CourseService
from ai_integration.ai_service import AIService # Para interacción directa con la IA en el chat

# Importar módulos auxiliares
import voice_assistant
import logros # El módulo refactorizado de logros

class StudentDashboardView:
    def __init__(self, root, current_user: User, auth_service_instance: AuthService, ai_service_instance: AIService, learning_service_instance: LearningService, course_service_instance: CourseService):
        self.root = root
        self.current_user = current_user
        self.auth_service = auth_service_instance
        self.ai_service = ai_service_instance
        self.learning_service = learning_service_instance
        self.course_service = course_service_instance

        self.root.title(f"BrainCourse - {self.current_user.nombre}")
        
        # Cargar y configurar el icono de la aplicación
        try:
            # Ajustar la ruta para acceder a la carpeta assets
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icon.png")
            self.app_icon_photo = ImageTk.PhotoImage(Image.open(icon_path)) 
            self.root.iconphoto(True, self.app_icon_photo) 
        except Exception as e:
            print(f"Advertencia: 'icon.png' no encontrado o error al cargar: {e}")
            
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.root.geometry("1000x700")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(root, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # --- CORRECCIÓN: Inicializar widgets principales antes de usarlos ---
        self.setup_main_content_area()
        self.setup_sidebar()
        self.configure_chat_tags()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Inicializar variables de estado de la UI (no persistentes en el modelo User)
        self.mode = 'chat' # 'chat', 'practica', 'cursos', 'stats'
        self.practice_state = 'waiting_for_topic' # 'waiting_for_topic', 'choosing_length', 'answering_quiz', 'answering_exam'
        self.current_practice_topic = None
        self.practice_quiz = [] # Lista de preguntas del quiz actual
        self.practice_quiz_idx = 0 # Índice de la pregunta actual
        self.practice_quiz_correctas = 0 # Conteo de aciertos en el quiz actual
        self.pregunta_actual_texto = None # Texto de la pregunta actual para pedir pistas
        self.pista_usada = False
        self.preguntas_falladas = [] # Lista de preguntas falladas en el quiz actual para el repaso
        self.respuestas_dadas_quiz_actual = [] # Historial de respuestas para el quiz actual (para guardar en user.historial_actividad)

        self.curso_activo = None # Objeto de curso activo (dict del user.cursos)
        self.modulo_activo = None # Objeto de módulo activo (dict de curso_activo['modulos'])

        # Carga inicial (siempre empieza en modo chat)
        self.check_notifications()
        self.iniciar_modo_chat(es_inicio=True)

    def setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self.main_frame, width=250, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1) # Espacio para los botones de abajo

        self.sidebar_label_name = ctk.CTkLabel(self.sidebar_frame, text=f"  Hola, {self.current_user.nombre}", font=ctk.CTkFont(size=20, weight="bold"))
        self.sidebar_label_name.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        ctk.CTkButton(self.sidebar_frame, text="🤖 Asistente IA", command=self.iniciar_modo_chat).grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="🧠 Practicar", command=self.iniciar_modo_practica).grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="📚 Mis Cursos", command=self.iniciar_modo_cursos).grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="📊 Mi Progreso", command=self.iniciar_modo_estadisticas).grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # --- Asegurar que los botones de Configuración y Cerrar Sesión siempre estén visibles ---
        self.settings_window = None
        try:
            gear_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "gear_icon.png")
            self.gear_image_photo = ImageTk.PhotoImage(Image.open(gear_icon_path).resize((20, 20), Image.LANCZOS)) 
            self.settings_button = ctk.CTkButton(self.sidebar_frame, text=" Configuración", image=self.gear_image_photo, compound="left", command=self.open_settings_window)
        except Exception as e: 
            print(f"Advertencia: 'gear_icon.png' no encontrado o error al cargar: {e}")
            self.settings_button = ctk.CTkButton(self.sidebar_frame, text="⚙️ Configuración", command=self.open_settings_window)
        self.settings_button.grid(row=7, column=0, padx=20, pady=10, sticky="s")

        self.logout_button = ctk.CTkButton(self.sidebar_frame, text="Cerrar Sesión", command=self.logout, fg_color="#D32F2F", hover_color="#B71C1C")
        self.logout_button.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="s")

    def update_sidebar_name(self, new_name: str):
        """Callback para actualizar el nombre en la barra lateral después de un cambio en la configuración."""
        self.sidebar_label_name.configure(text=f"  Hola, {new_name}")
        self.current_user.nombre = new_name
        # --- Redibujar los botones de configuración y cerrar sesión si se actualiza el nombre ---
        self.settings_button.lift()
        self.logout_button.lift()

    def setup_main_content_area(self):
        self.main_content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.main_content_frame.grid(row=0, column=1, sticky="nsew")
        self.main_content_frame.grid_columnconfigure(0, weight=1)
        # Configurar filas para contenido dinámico
        self.main_content_frame.grid_rowconfigure(0, weight=0) # Para barra de progreso / encabezados dinámicos
        self.main_content_frame.grid_rowconfigure(1, weight=1) # Área de contenido principal (historial de chat, estadísticas, detalles del curso)
        self.main_content_frame.grid_rowconfigure(2, weight=0) # Opciones / elementos interactivos
        self.main_content_frame.grid_rowconfigure(3, weight=0) # Área de entrada (input_area_frame)

        # Elementos de UI comunes que se mostrarán/ocultarán dinámicamente
        self.progress_bar = ctk.CTkProgressBar(self.main_content_frame)

        self.chat_history = ctk.CTkTextbox(self.main_content_frame, wrap="word", state='disabled', font=ctk.CTkFont(family="Arial", size=14))
        
        self.opciones_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.opciones_frame.grid_columnconfigure((0, 1), weight=1) # Para opciones de quiz

        self.historial_temas_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.historial_temas_frame.grid_columnconfigure((0,1,2,3,4), weight=1) # Para temas recientes

        self.quiz_length_selection_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.quiz_length_selection_frame.grid_columnconfigure((0,1,2), weight=1) # Para botones de longitud de quiz

        self.repaso_quiz_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.repaso_quiz_frame.grid_columnconfigure((0,1), weight=1) # Para opciones de repaso

        self.cursos_list_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent") # Para lista de cursos
        self.cursos_list_frame.grid_columnconfigure(0, weight=1)

        self.stats_display_frame = ctk.CTkFrame(self.main_content_frame, fg_color="transparent") # Para mostrar estadísticas
        self.stats_display_frame.grid_columnconfigure(0, weight=1)

        # Área de entrada en la parte inferior para chat/temas de práctica
        self.input_area_frame = ctk.CTkFrame(self.main_content_frame, corner_radius=20)
        self.input_area_frame.grid_columnconfigure(0, weight=1)
        self.input_area_frame.grid_columnconfigure(1, weight=0) # Botón de micrófono
        self.input_area_frame.grid_columnconfigure(2, weight=0) # Botón de enviar

        self.user_input_field = ctk.CTkTextbox(self.input_area_frame, height=40, wrap="word", font=ctk.CTkFont(family="Arial", size=14))
        self.user_input_field.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=10)
        self.user_input_field.bind("<Return>", self.procesar_entrada_on_enter)

        try:
            # Ajustar la ruta para acceder a la carpeta assets
            mic_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mic_icon.png")
            self.mic_image_photo = ImageTk.PhotoImage(Image.open(mic_icon_path).resize((20, 20), Image.LANCZOS))
            self.mic_button = ctk.CTkButton(self.input_area_frame, text="", image=self.mic_image_photo, width=40, height=40, corner_radius=20, command=self.iniciar_dictado_por_voz)
        except Exception as e: 
            print(f"Advertencia: 'mic_icon.png' no encontrado o error al cargar: {e}")
            self.mic_button = ctk.CTkButton(self.input_area_frame, text="🎤", width=40, height=40, corner_radius=20, command=self.iniciar_dictado_por_voz)
        self.mic_button.grid(row=0, column=1, padx=5, pady=10, sticky="se")

        self.send_button = ctk.CTkButton(self.input_area_frame, text="▲", width=40, height=40, corner_radius=20, command=self.procesar_entrada)
        self.send_button.grid(row=0, column=2, padx=(0, 15), pady=10, sticky="se")

    def open_settings_window(self):
        # Importar SettingsWindow aquí para evitar dependencias circulares al inicio
        from views.settings_view import SettingsWindow
        if self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self.root, self.current_user, self.auth_service, self.update_sidebar_name, self.logout)
        else:
            self.settings_window.focus()

    def check_notifications(self):
        """Muestra notificaciones no leídas y las marca como leídas."""
        notificaciones_no_leidas = [n for n in self.current_user.notificaciones if not n.get('leida', False)]
        if notificaciones_no_leidas:
            for notif in notificaciones_no_leidas:
                messagebox.showinfo("Notificación", notif['texto'], parent=self.root)
            self.current_user.marcar_notificaciones_leidas() # Método en User model
            user_dao.actualizar_datos_usuario(self.current_user.email, self.current_user.to_dict()) # Persistir cambios

    def configure_chat_tags(self):
        mode = ctk.get_appearance_mode()
        colors = {
            "Agente": ("#007BFF", "#90CAF9"), # Blue
            "Tú": ("#1f1f1f", "#fafafa"),     # Dark/Light text
            "Sistema": ("#6c757d", "#b0bec5"), # Gray
            "Correcto": ("#28a745", "#66bb6a"), # Green
            "Incorrecto": ("#dc3545", "#ef5350") # Red
        }
        for tag, (light, dark) in colors.items():
            self.chat_history.tag_config(tag, foreground=dark if mode == "Dark" else light)

    def add_message(self, sender: str, message: str, tag: str = None):
        self.chat_history.configure(state='normal')
        self.chat_history.insert("end", f"{sender}: ", (tag if tag else sender, "bold"))
        self.chat_history.insert("end", f"{message}\n\n")
        self.chat_history.configure(state='disabled')
        self.chat_history.see("end") # Auto-scroll to end

    def limpiar_pantalla(self):
        self.chat_history.configure(state='normal')
        self.chat_history.delete("1.0", "end")
        self.chat_history.configure(state='disabled')

    def ocultar_todos_los_widgets(self):
        # Oculta todos los widgets que se gestionan dinámicamente
        for widget_frame in [
            self.progress_bar,
            self.chat_history,
            self.opciones_frame,
            self.historial_temas_frame,
            self.quiz_length_selection_frame,
            self.repaso_quiz_frame,
            self.cursos_list_frame,
            self.stats_display_frame,
            self.input_area_frame
        ]:
            widget_frame.grid_remove()
        
        # Quitar gráficos de matplotlib si existen
        for widget in self.main_content_frame.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()

    def _get_ai_context_data(self):
        """Retorna un diccionario con datos de contexto del usuario para el AIService."""
        return {
            'user_level': self.current_user.progreso.get('nivel', 1),
            'user_profile_data': self.current_user.datos_perfil,
            'current_topic': self.current_practice_topic,
            'current_question_text': self.pregunta_actual_texto,
            'course_context': {
                'curso_tema': self.curso_activo['tema_general'],
                'modulo_titulo': self.modulo_activo['titulo']
            } if self.curso_activo and self.modulo_activo else None
        }

    def iniciar_modo_chat(self, es_inicio=False):
        self.pregunta_actual_texto = None # Reset context for new chat
        self.current_practice_topic = None
        self.modulo_activo = None
        self.mode = 'chat'

        self.ocultar_todos_los_widgets()
        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        self.input_area_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        if es_inicio:
            self.add_message("Agente", f"¡Hola, {self.current_user.nombre}! ¿En qué puedo ayudarte hoy?")
        else:
            self.limpiar_pantalla()
            self.add_message("Agente", "Cambiando a modo Asistente IA.")
        
        self.user_input_field.focus()

    def iniciar_modo_practica(self):
        self.pregunta_actual_texto = None # Reset context for new practice
        self.mode = 'practica'
        self.practice_state = 'waiting_for_topic'
        self.limpiar_pantalla()
        self.ocultar_todos_los_widgets()

        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        self.input_area_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20)) # Input debajo de los temas

        # Mostrar temas recientes del usuario
        for widget in self.historial_temas_frame.winfo_children():
            widget.destroy()
        
        if self.current_user.historial_temas:
            ctk.CTkLabel(self.historial_temas_frame, text="Temas Recientes:").grid(row=0, column=0, columnspan=5, padx=10, pady=(0,5), sticky="w")
            for i, tema in enumerate(self.current_user.historial_temas):
                btn = ctk.CTkButton(self.historial_temas_frame, text=tema, fg_color="gray", command=lambda t=tema: self.elegir_tema(t))
                btn.grid(row=1, column=i, padx=5, pady=5, sticky="ew")
        
        self.historial_temas_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        self.add_message("Sistema", f"¡Modo Práctica! Tu nivel es {self.current_user.progreso.get('nivel', 1)}.\n\nElige un tema reciente o escribe uno nuevo:")
        self.user_input_field.focus()

    def iniciar_modo_cursos(self):
        self.pregunta_actual_texto = None
        self.mode = 'cursos'
        self.curso_activo = None # Reset active course
        self.ocultar_todos_los_widgets()
        
        self.cursos_list_frame.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=10)
        for widget in self.cursos_list_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkLabel(self.cursos_list_frame, text="Mis Cursos", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)

        # --- Mostrar cursos desde el perfil del usuario (para alumnos) ---
        cursos_usuario = self.current_user.cursos if hasattr(self.current_user, "cursos") else []
        if not cursos_usuario:
            ctk.CTkLabel(self.cursos_list_frame, text="Aún no has empezado ningún curso.").pack(pady=10)
        else:
            for course in cursos_usuario:
                row_frame = ctk.CTkFrame(self.cursos_list_frame, fg_color="transparent")
                row_frame.pack(fill="x", padx=20, pady=5)

                progreso = course.get('progreso_general', 0)
                curso_btn = ctk.CTkButton(row_frame, text=f"{course.get('tema_general', 'Sin tema')} ({progreso*100:.0f}%)", command=lambda c=course: self.ver_curso(c['id_curso']))
                curso_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))

                # Mostrar miembros si existen (para compatibilidad con cursos de profesor)
                miembros = course.get('miembros', [])
                if miembros:
                    miembros_str = ", ".join([f"{m['email']} ({m['rol']})" for m in miembros])
                    ctk.CTkLabel(row_frame, text=f"Miembros: {miembros_str}", font=ctk.CTkFont(size=12)).pack(side="left", padx=10)

                # Opción para abandonar el curso (si no es el creador)
                # No aplica para alumnos, pero si quieres permitirlo, descomenta:
                # if course.get('creador_email') and course.get('creador_email') != self.current_user.email:
                #     ctk.CTkButton(row_frame, text="Salir", fg_color="red", command=lambda c=course: self.abandonar_curso(c)).pack(side="right", padx=5)

        ctk.CTkButton(self.cursos_list_frame, text="➕ Crear Nuevo Curso", command=self.crear_nuevo_curso).pack(pady=20)

    def ver_curso_modular(self, course):
        self.curso_activo = course
        self.ocultar_todos_los_widgets()
        self.cursos_list_frame.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=10)
        for widget in self.cursos_list_frame.winfo_children():
            widget.destroy()
        ctk.CTkButton(self.cursos_list_frame, text="< Volver a Mis Cursos", command=self.iniciar_modo_cursos).pack(anchor="w", padx=10, pady=10)
        ctk.CTkLabel(self.cursos_list_frame, text=course.tema_general, font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)

        for modulo in course.modulos:
            modulo_frame = ctk.CTkFrame(self.cursos_list_frame)
            modulo_frame.pack(fill="x", padx=20, pady=5)
            estado = "✅" if modulo.get('completado') else "📖"
            calificacion = f"Nota: {modulo.get('calificacion_examen')}" if modulo.get('completado') and modulo.get('calificacion_examen') is not None else ""
            label_texto = f"{estado} {modulo['titulo']} {calificacion}"
            ctk.CTkLabel(modulo_frame, text=label_texto, anchor="w").pack(side="left", padx=10, pady=10)
            btn_text = "Revisar" if modulo.get('completado') else "Empezar"
            start_button = ctk.CTkButton(modulo_frame, text=btn_text, command=lambda m=modulo: self.ver_modulo_modular(m))
            start_button.pack(side="right", padx=10, pady=5)

    def ver_modulo_modular(self, modulo_data: dict):
        self.modulo_activo = modulo_data
        self.cursos_list_frame.grid_remove()
        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        self.input_area_frame.grid_remove()
        self.limpiar_pantalla()
        self.add_message("Sistema", f"Módulo: {self.modulo_activo['titulo']}\n\nHaz clic en un subtema para ver la teoría. Cuando estés listo, toma el examen.")
        self.opciones_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        for widget in self.opciones_frame.winfo_children():
            widget.destroy()
        for subtema in self.modulo_activo['subtemas']:
            ctk.CTkButton(self.opciones_frame, text=subtema, fg_color="gray", command=lambda s=subtema: self.ver_teoria_subtema_modular(s)).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(self.opciones_frame, text="📝 Tomar Examen del Módulo", command=self.iniciar_examen_modulo).pack(fill="x", padx=10, pady=20)
        ctk.CTkButton(self.opciones_frame, text="< Volver a los Módulos", command=lambda: self.ver_curso_modular(self.curso_activo)).pack(fill="x", padx=10, pady=5)

    def ver_teoria_subtema_modular(self, subtema: str):
        self.add_message("Tú", f"Quiero aprender sobre: {subtema}")
        self.add_message("Sistema", "Obteniendo explicación...", tag="Sistema")
        def _mostrar_teoria():
            teoria = self.course_service.obtener_teoria_subtema(self.current_user, self.curso_activo.id_curso, self.modulo_activo['id_modulo'], subtema)
            self.root.after(0, lambda: self.add_message("Agente", teoria))
        threading.Thread(target=_mostrar_teoria).start()

    def ver_teoria_subtema(self, subtema: str):
        self.add_message("Tú", f"Quiero aprender sobre: {subtema}")
        self.add_message("Sistema", "Obteniendo explicación...", tag="Sistema")
        def _mostrar_teoria():
            teoria = self.course_service.obtener_teoria_subtema(self.current_user, self.curso_activo['id_curso'], self.modulo_activo['id_modulo'], subtema)
            self.root.after(0, lambda: self.add_message("Agente", teoria))
        threading.Thread(target=_mostrar_teoria).start()

    def abandonar_curso(self, course):
        confirm = messagebox.askyesno("Salir del Curso", f"¿Seguro que quieres salir del curso '{course.tema_general}'?", parent=self.root)
        if confirm:
            self.course_service.quitar_miembro_de_curso(course, self.current_user)
            messagebox.showinfo("Curso Abandonado", "Has salido del curso.", parent=self.root)
            self.iniciar_modo_cursos()

    # --- Gestión de Cursos ---
    def crear_nuevo_curso(self):
        tema = simpledialog.askstring("Nuevo Curso", "Escribe el tema general para tu nuevo curso:", parent=self.root)
        if not tema or not tema.strip():
            return
        
        messagebox.showinfo("Generando Curso", "La IA está diseñando tu curso. Esto puede tardar un momento.", parent=self.root)
        
        def _generar_en_hilo():
            # Llamar a CourseService para crear el curso
            nuevo_curso = self.course_service.crear_curso_para_usuario(self.current_user, tema)
            self.root.after(0, self._procesar_resultado_curso_generado, nuevo_curso, tema)

        threading.Thread(target=_generar_en_hilo).start()

    def _procesar_resultado_curso_generado(self, nuevo_curso: dict, tema: str):
        if nuevo_curso:
            messagebox.showinfo("¡Curso Creado!", f"Tu curso sobre '{tema}' ha sido creado.", parent=self.root)
            self.iniciar_modo_cursos() # Refrescar la lista de cursos
        else:
            messagebox.showerror("Error", "No se pudo generar el sílabo para el curso.", parent=self.root)
    
    def eliminar_curso(self, id_curso: str):
        curso_a_eliminar = self.current_user.encontrar_curso(id_curso)
        if not curso_a_eliminar: return

        confirmacion = messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de que quieres eliminar el curso '{curso_a_eliminar['tema_general']}'?", parent=self.root)
        if confirmacion:
            self.course_service.eliminar_curso_de_usuario(self.current_user, id_curso)
            messagebox.showinfo("Curso Eliminado", "El curso ha sido eliminado de tu perfil.", parent=self.root)
            self.iniciar_modo_cursos() # Refrescar la lista de cursos

    def ver_curso(self, id_curso: str):
        self.curso_activo = self.current_user.encontrar_curso(id_curso)
        if not self.curso_activo:
            messagebox.showerror("Error", "No se pudo encontrar el curso."); return
        
        self.ocultar_todos_los_widgets()
        self.chat_history.grid_remove() # Asegurarse de que el historial de chat esté oculto
        self.cursos_list_frame.grid(row=1, column=0, rowspan=3, sticky="nsew", padx=20, pady=10)
        
        for widget in self.cursos_list_frame.winfo_children():
            widget.destroy()
        
        ctk.CTkButton(self.cursos_list_frame, text="< Volver a Mis Cursos", command=self.iniciar_modo_cursos).pack(anchor="w", padx=10, pady=10)
        ctk.CTkLabel(self.cursos_list_frame, text=self.curso_activo['tema_general'], font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)

        for modulo in self.curso_activo['modulos']:
            modulo_frame = ctk.CTkFrame(self.cursos_list_frame)
            modulo_frame.pack(fill="x", padx=20, pady=5)
            
            estado = "✅" if modulo.get('completado') else "📖"
            calificacion = f"Nota: {modulo.get('calificacion_examen')}" if modulo.get('completado') and modulo.get('calificacion_examen') is not None else ""
            label_texto = f"{estado} {modulo['titulo']} {calificacion}"
            
            ctk.CTkLabel(modulo_frame, text=label_texto, anchor="w").pack(side="left", padx=10, pady=10)
            
            btn_text = "Revisar" if modulo.get('completado') else "Empezar"
            start_button = ctk.CTkButton(modulo_frame, text=btn_text, command=lambda m=modulo: self.ver_modulo(m))
            start_button.pack(side="right", padx=10, pady=5)
    
    def ver_modulo(self, modulo_data: dict):
        self.modulo_activo = modulo_data
        self.cursos_list_frame.grid_remove() # Ocultar lista de cursos
        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10)) # Mostrar historial de chat para la teoría
        self.input_area_frame.grid_remove() # Ocultar campo de entrada normal (solo botones)
        self.limpiar_pantalla()

        self.add_message("Sistema", f"Módulo: {self.modulo_activo['titulo']}\n\nHaz clic en un subtema para ver la teoría. Cuando estés listo, toma el examen.")
        
        self.opciones_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20)) # Para botones de subtemas y de examen
        for widget in self.opciones_frame.winfo_children():
            widget.destroy() # Limpiar opciones anteriores
        
        # Botones de subtemas
        for subtema in self.modulo_activo['subtemas']:
            ctk.CTkButton(self.opciones_frame, text=subtema, fg_color="gray", command=lambda s=subtema: self.ver_teoria_subtema(s)).pack(fill="x", padx=10, pady=5)
        
        # Botón de Examen
        ctk.CTkButton(self.opciones_frame, text="📝 Tomar Examen del Módulo", command=self.iniciar_examen_modulo).pack(fill="x", padx=10, pady=20)
        
        # Botón de Volver
        ctk.CTkButton(self.opciones_frame, text="< Volver a los Módulos", command=lambda: self.ver_curso(self.curso_activo['id_curso'])).pack(fill="x", padx=10, pady=5)

    def ver_teoria_subtema(self, subtema: str):
        self.add_message("Tú", f"Quiero aprender sobre: {subtema}")
        self.add_message("Sistema", "Obteniendo explicación...", tag="Sistema")
        def _mostrar_teoria():
            teoria = self.course_service.obtener_teoria_subtema(self.current_user, self.curso_activo['id_curso'], self.modulo_activo['id_modulo'], subtema)
            self.root.after(0, lambda: self.add_message("Agente", teoria))
        threading.Thread(target=_mostrar_teoria).start()

    def iniciar_modo_estadisticas(self):
        messagebox.showinfo("En desarrollo", "La sección de estadísticas estará disponible próximamente.", parent=self.root)

    def iniciar_examen_modulo(self):
        num_preguntas = 5 # Número fijo de preguntas para el examen de módulo
        self.add_message("Sistema", f"Iniciando examen de {num_preguntas} preguntas sobre {self.modulo_activo['titulo']}...", tag="Sistema")
        self.practice_state = 'answering_exam'
        self.current_practice_topic = self.modulo_activo['titulo'] # Tema para los datos del quiz

        # Limpiar estado actual del quiz
        self.practice_quiz = []
        self.practice_quiz_idx = 0
        self.practice_quiz_correctas = 0
        self.respuestas_dadas_quiz_actual = []
        self.preguntas_falladas = [] # Aunque en el examen no se repasan, es bueno resetearlo

        self.ocultar_todos_los_widgets() # Ocultar botones de módulo
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(10,0))
        self.chat_history.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 10))
        self.opciones_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))


        def _generar_examen():
            # Llamar a LearningService para generar el examen
            quiz_data = self.learning_service.generar_examen_modulo(self.current_user, self.modulo_activo['subtemas'], num_preguntas)
            self.root.after(0, self._procesar_resultado_quiz_generado, quiz_data)

        threading.Thread(target=_generar_examen).start()

    # --- Gestión de Quizzes de Práctica (reutilizado por el quiz de Onboarding y Examen de Módulo) ---
    def elegir_tema(self, topic: str):
        self.current_practice_topic = topic.strip().capitalize()
        self.practice_state = 'choosing_length'
        self.add_message("Tú", f"Quiero practicar sobre: {self.current_practice_topic}")
        self.add_message("Sistema", "¿Cuántas preguntas quieres para tu quiz?")
        
        self.historial_temas_frame.grid_remove() # Ocultar temas recientes
        self.input_area_frame.grid_remove() # Ocultar campo de entrada de usuario
        
        for widget in self.quiz_length_selection_frame.winfo_children():
            widget.destroy() # Limpiar botones anteriores

        ctk.CTkButton(self.quiz_length_selection_frame, text="3 (Rápido)", command=lambda: self.iniciar_quiz_tematico(3)).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.quiz_length_selection_frame, text="5 (Normal)", command=lambda: self.iniciar_quiz_tematico(5)).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.quiz_length_selection_frame, text="10 (Intenso)", command=lambda: self.iniciar_quiz_tematico(10)).grid(row=0, column=2, padx=10, pady=10, sticky="ew")
        
        self.quiz_length_selection_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

    def iniciar_quiz_tematico(self, num_preguntas: int):
        self.add_message("Sistema", f"Creando un quiz de {num_preguntas} preguntas sobre '{self.current_practice_topic}'.\nPor favor, espera...", tag="Sistema")
        for widget in self.quiz_length_selection_frame.winfo_children():
            widget.configure(state="disabled") # Deshabilitar botones mientras se genera
        self.root.update_idletasks() # Forzar actualización de la UI

        # Resetear estado del quiz para uno nuevo
        self.practice_quiz = []
        self.practice_quiz_idx = 0
        self.practice_quiz_correctas = 0
        self.respuestas_dadas_quiz_actual = []
        self.preguntas_falladas = []
        
        def _generar_quiz():
            # Llamar a LearningService para generar el quiz
            quiz_data = self.learning_service.generar_quiz_tematico(self.current_user, self.current_practice_topic, num_preguntas)
            self.root.after(0, self._procesar_resultado_quiz_generado, quiz_data)

        threading.Thread(target=_generar_quiz).start()

    def _procesar_resultado_quiz_generado(self, quiz_data: list):
        self.quiz_length_selection_frame.grid_remove() # Ocultar selección de longitud del quiz
        
        if not quiz_data:
            self.add_message("Sistema", "No pude generar un quiz para ese tema. Volviendo al menú.", tag="Incorrecto")
            self.root.after(3000, self.iniciar_modo_practica) # Volver al menú de práctica
            return
        
        self.practice_quiz = quiz_data
        self.practice_quiz_idx = 0
        self.practice_quiz_correctas = 0
        self.preguntas_falladas = []
        self.respuestas_dadas_quiz_actual = []

        self.limpiar_pantalla()
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(10,0))
        self.progress_bar.set(0) # Resetear barra de progreso

        self.siguiente_pregunta_practica()

    def siguiente_pregunta_practica(self):
        progreso_actual = self.practice_quiz_idx / len(self.practice_quiz)
        self.progress_bar.set(progreso_actual)

        if self.practice_quiz_idx >= len(self.practice_quiz):
            self.finalizar_quiz_practica()
            return
        
        self.pista_usada = False # Resetear para nueva pregunta
        pregunta_actual = self.practice_quiz[self.practice_quiz_idx]
        self.pregunta_actual_texto = pregunta_actual["pregunta"]
        # La respuesta correcta es necesaria para la verificación, pero no se muestra aún

        self.add_message("Sistema", f"Pregunta {self.practice_quiz_idx + 1}/{len(self.practice_quiz)}:\n\n{self.pregunta_actual_texto}")
        
        self.opciones_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        for widget in self.opciones_frame.winfo_children():
            widget.destroy() # Limpiar opciones antiguas

        # Crear botones para las opciones
        for i, opcion_txt in enumerate(pregunta_actual["opciones"]):
            btn = ctk.CTkButton(self.opciones_frame, text=str(opcion_txt), 
                                command=lambda opc=opcion_txt, p_data=pregunta_actual: self.verificar_respuesta_practica(opc, p_data))
            btn.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky="ew")
        
        # Añadir botón de ayuda
        ayuda_btn = ctk.CTkButton(self.opciones_frame, text="❓ Pedir Pista", fg_color="transparent", border_width=1, command=self.pedir_ayuda_ia)
        ayuda_btn.grid(row=(len(pregunta_actual["opciones"]) + 1) // 2, column=0, columnspan=2, padx=10, pady=10, sticky="ew") # Fila ajustada

    def verificar_respuesta_practica(self, opcion_elegida: str, pregunta_data: dict):
        """
        Verifica la respuesta del usuario para una pregunta de práctica o examen.
        Delega la lógica de negocio al LearningService.
        """
        # Obtener la respuesta correcta de forma segura
        respuesta_correcta = pregunta_data.get('respuesta', pregunta_data.get('respuesta_correcta_ia'))

        # Añadir la respuesta actual al historial temporal del quiz
        self.respuestas_dadas_quiz_actual.append({
            "pregunta": pregunta_data['pregunta'],
            "respuesta_usuario": str(opcion_elegida),
            "respuesta_correcta_ia": str(respuesta_correcta),
            "fue_correcta": (str(opcion_elegida) == str(respuesta_correcta))
        })

        self.add_message("Tú", f"Mi respuesta es: {opcion_elegida}")

        # Llamar a LearningService para procesar la respuesta
        es_correcta, unlocked_achievements = self.learning_service.procesar_respuesta_quiz(
            self.current_user,
            self.current_practice_topic,
            {**pregunta_data, "respuesta": respuesta_correcta},  # Asegura que la clave 'respuesta' exista
            opcion_elegida
        )

        # Actualización de la UI
        if es_correcta:
            self.add_message("Sistema", "¡Correcto! ✅", tag="Correcto")
            self.practice_quiz_correctas += 1
        else:
            self.add_message("Sistema", f"Incorrecto. ❌ La respuesta era {respuesta_correcta}.", tag="Incorrecto")
            self.preguntas_falladas.append(pregunta_data) # Añadir a la lista de fallidas para repaso

        # UI: Deshabilitar botones y resaltar
        for widget in self.opciones_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                widget.configure(state="disabled")
                opcion_texto = widget.cget("text")
                if "Pista" not in opcion_texto and "Solución" not in opcion_texto and "¿Por qué" not in opcion_texto:
                    if opcion_texto == str(opcion_elegida):
                        widget.configure(fg_color="green" if es_correcta else "red", hover=False)
                    elif not es_correcta and opcion_texto == str(respuesta_correcta):
                        widget.configure(fg_color="green", hover=False)
                elif es_correcta and ("Pista" in opcion_texto or "Solución" in opcion_texto):
                    widget.configure(text="💡 ¿Por qué es correcto?", command=self.pedir_explicacion_acierto, state="normal", fg_color="transparent")
        
        # Mostrar notificación de subida de nivel si aplica
        if es_correcta and self.current_user.progreso.get('racha_correctas', 0) > 0 and self.current_user.progreso.get('racha_correctas', 0) % 3 == 0:
            messagebox.showinfo("¡Felicidades!", f"¡Subiste al Nivel {self.current_user.progreso.get('nivel')}!", parent=self.root)

        # Notificar sobre nuevos logros desbloqueados
        for achievement_id in unlocked_achievements:
            mensaje = f"🏆 ¡Logro Desbloqueado! 🏆\n\n{logros.LOGROS_DEFINICIONES[achievement_id]}"
            messagebox.showinfo("¡Felicidades!", mensaje, parent=self.root)

        self.practice_quiz_idx += 1
        self.root.after(2500, self.siguiente_pregunta_practica) # Pequeño retraso antes de la siguiente pregunta

    def finalizar_quiz_practica(self):
        self.limpiar_pantalla()
        self.progress_bar.grid_remove()
        self.opciones_frame.grid_remove() # Ocultar frame de opciones

        quiz_results_for_service = {
            'topic': self.current_practice_topic,
            'total_questions': len(self.practice_quiz),
            'correct_answers': self.practice_quiz_correctas,
            'questions_details': self.respuestas_dadas_quiz_actual # Historial detallado para el servicio
        }

        unlocked_achievements = self.learning_service.finalizar_quiz(self.current_user, quiz_results_for_service, self.practice_state == 'answering_exam')

        # Notificar sobre cualquier logro final (ej. Mente Brillante, Polímata)
        for achievement_id in unlocked_achievements:
            mensaje = f"🏆 ¡Logro Desbloqueado! 🏆\n\n{logros.LOGROS_DEFINICIONES[achievement_id]}"
            messagebox.showinfo("¡Felicidades!", mensaje, parent=self.root)

        if self.practice_state == 'answering_exam':
            self.add_message("Sistema", f"¡Examen del módulo completado!\n\nObtuviste {self.practice_quiz_correctas} de {len(self.practice_quiz)} respuestas correctas.", tag="Sistema")
            # Actualizar progreso y calificación del curso a través de CourseService
            self.course_service.marcar_modulo_completado(
                self.current_user,
                self.curso_activo['id_curso'],
                self.modulo_activo['id_modulo'],
                (self.practice_quiz_correctas / len(self.practice_quiz)) * 10 # Calificación sobre 10
            )
            self.root.after(4000, lambda: self.ver_curso(self.curso_activo['id_curso'])) # Volver a la vista del módulo
        else: # Quiz de práctica regular
            self.add_message("Sistema", f"¡Quiz completado!\n\nObtuviste {self.practice_quiz_correctas} de {len(self.practice_quiz)} respuestas correctas.", tag="Sistema")
            
            if self.preguntas_falladas:
                self.add_message("Sistema", "¿Quieres repasar las preguntas que fallaste?", "Sistema")
                for widget in self.repaso_quiz_frame.winfo_children(): widget.destroy()
                ctk.CTkButton(self.repaso_quiz_frame, text="✅ Sí, repasar errores", command=self.iniciar_repaso_errores).grid(row=0, column=0, padx=10, pady=10, sticky="ew")
                ctk.CTkButton(self.repaso_quiz_frame, text="❌ No, volver al menú", command=self.iniciar_modo_practica).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
                self.repaso_quiz_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
            else:
                self.add_message("Sistema", "¡Felicidades, no tuviste errores! Volviendo al menú...", tag="Correcto")
                self.root.after(4000, self.iniciar_modo_practica)

    def iniciar_repaso_errores(self):
        self.repaso_quiz_frame.grid_remove() # Ocultar opciones de repaso
        self.add_message("Sistema", "¡Perfecto! Vamos a repasar tus errores.", "Sistema")
        # Iniciar un nuevo quiz con las preguntas falladas
        self.root.after(1500, lambda: self._procesar_resultado_quiz_generado(self.preguntas_falladas))
        self.practice_state = 'answering_quiz' # El repaso sigue siendo un quiz, no un examen de módulo

    def pedir_ayuda_ia(self):
        if not self.pregunta_actual_texto: return
        
        # Encontrar el botón de ayuda para cambiar su texto/estado
        ayuda_btn = next((w for w in self.opciones_frame.winfo_children() if isinstance(w, ctk.CTkButton) and ("Pista" in w.cget("text") or "Solución" in w.cget("text"))), None)
        if not ayuda_btn: return

        ai_context = self._get_ai_context_data()

        if not self.pista_usada:
            self.add_message("Sistema", "Claro, aquí tienes una pista...", tag="Sistema")
            # Llamar a AIService directamente para respuesta de chat
            threading.Thread(target=lambda: self.add_message("Agente", self.ai_service.send_message(
                f"Dame una pista corta para resolver: '{self.pregunta_actual_texto}'",
                **ai_context
            ))).start()
            self.pista_usada = True
            ayuda_btn.configure(text="❓ Pedir Solución Completa")
        else:
            self.add_message("Sistema", "Aquí tienes la solución completa...", tag="Sistema")
            # Llamar a AIService directamente para respuesta de chat
            threading.Thread(target=lambda: self.add_message("Agente", self.ai_service.send_message(
                f"Explícame paso a paso cómo resolver: '{self.pregunta_actual_texto}'",
                **ai_context
            ))).start()
            ayuda_btn.configure(state="disabled") # Deshabilitar después de dar la solución completa

    def pedir_explicacion_acierto(self):
        self.add_message("Sistema", "¡Buena pregunta! Aquí te explico por qué la respuesta correcta...", tag="Sistema")
        ai_context = self._get_ai_context_data()
        threading.Thread(target=lambda: self.add_message("Agente", self.ai_service.send_message(
            f"Mi respuesta fue correcta. Explícame brevemente por qué la solución a este problema es la correcta: '{self.pregunta_actual_texto}'",
            **ai_context
        ))).start()
        for widget in self.opciones_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton) and "¿Por qué es correcto?" in widget.cget("text"):
                widget.configure(state="disabled") # Deshabilitar botón después de pedir la explicación

    # --- Procesamiento de Entrada de Usuario ---
    def procesar_entrada_on_enter(self, event=None):
        # Solo procesar si se presiona Enter sin Shift (para entrada multilínea)
        if event and event.state & 0x1: # Comprueba si la tecla Shift está presionada
            return # No hacer nada si es Shift+Enter, permite una nueva línea
        self.procesar_entrada()
        return "break" # Evita el comportamiento predeterminado de Tkinter de nueva línea

    def procesar_entrada(self):
        user_input = self.user_input_field.get("1.0", "end-1c").strip()
        if not user_input: return
        self.user_input_field.delete("1.0", "end") # Limpiar campo de entrada

        if self.mode == 'practica' and self.practice_state == 'waiting_for_topic':
            self.elegir_tema(user_input)
        elif self.mode == 'chat':
            self.add_message("Tú", user_input)
            # Interacción directa con la IA en el chat, pasando el contexto
            ai_context = self._get_ai_context_data()
            threading.Thread(target=lambda: self.add_message("Agente", self.ai_service.send_message(
                user_input,
                **ai_context
            ))).start()
    
    def iniciar_dictado_por_voz(self):
        self.mic_button.configure(state="disabled")
        voice_assistant.start_listening(root=self.root, callback_success=self.on_speech_recognized, callback_error=self.on_speech_error, callback_status=self.update_voice_status)
    
    def on_speech_recognized(self, text: str):
        # Inserta el texto al final del campo de entrada, sin borrar lo anterior
        self.user_input_field.insert("end-1c", text)
        self.user_input_field.focus()

    def on_speech_error(self, error_message: str):
        self.add_message("Sistema", f"Error de voz: {error_message}", tag="Incorrecto")

    def update_voice_status(self, status: str):
        # Re-habilitar botón de micrófono y actualizar su apariencia según el estado
        if status == "listening":
            self.mic_button.configure(fg_color="red", text="...")
        elif status == "processing":
            self.mic_button.configure(fg_color="orange", text="...")
        elif status == "idle":
            self.mic_button.configure(state="normal", fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            try:
                # Ajustar la ruta para acceder a la carpeta assets
                mic_icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mic_icon.png")
                self.mic_image_photo = ImageTk.PhotoImage(Image.open(mic_icon_path).resize((20, 20), Image.LANCZOS))
                self.mic_button.configure(text="", image=self.mic_image_photo)
            except Exception as e:
                print(f"Advertencia: 'mic_icon.png' no encontrado o error al cargar: {e}")
                self.mic_button.configure(text="🎤")

    def _save_user_data(self):
        """Guarda manualmente los datos del usuario. Los servicios ya lo hacen automáticamente."""
        # Esto es una salvaguarda. Los servicios ya deben persistir los cambios al User object.
        # Puedes remover esta llamada si confías plenamente en que los servicios persisten todo.
        user_dao.actualizar_datos_usuario(self.current_user.email, self.current_user.to_dict())

    def logout(self, force: bool = False):
        """Cierra la sesión del usuario."""
        if force or messagebox.askyesno("Cerrar Sesión", "¿Estás seguro de que quieres cerrar sesión?"):
            self._save_user_data() # Asegurarse de que los datos se guarden antes de cerrar sesión
            self.main_frame.destroy()
            # Importar LoginWindow localmente para evitar dependencias circulares al inicio
            from main import LoginWindow # Asumiendo que LoginWindow sigue en main.py por ahora
            LoginWindow(self.root)

    def on_closing(self):
        """Maneja el evento de cierre de la ventana."""
        if messagebox.askyesno("Salir", "¿Estás seguro de que quieres salir?"):
            self._save_user_data() # Asegurarse de que los datos se guarden al cerrar la aplicación
            self.root.destroy()