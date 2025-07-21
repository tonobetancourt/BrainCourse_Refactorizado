# views/student_onboarding_view.py

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import threading

from models.user_model import User
from services.auth_service import AuthService
from services.learning_service import LearningService # Para la generación del quiz de nivelación
from ai_integration.ai_service import AIService # Usado por LearningService

class OnboardingWindow(ctk.CTkToplevel):
    def __init__(self, master, current_user: User, auth_service_instance: AuthService, ai_service_instance: AIService, callback_final):
        super().__init__(master)
        self.title("Configuración de Perfil")
        self.geometry("600x650")
        self.transient(master) # Hace que la ventana de registro esté siempre encima de la principal
        self.grab_set()        # Bloquea interacciones con la ventana principal

        self.current_user = current_user # El objeto User que se está configurando
        self.auth_service = auth_service_instance
        self.ai_service = ai_service_instance # Se lo pasamos a LearningService
        self.learning_service = LearningService(user_dao_module=self.auth_service.user_dao, ai_service_instance=self.ai_service) # Instancia de LearningService
        self.callback_final = callback_final # Callback para lanzar el dashboard principal

        self.quiz_respuestas_correctas = 0
        self.quiz_completo = []
        self.quiz_pregunta_actual_idx = 0
        self.respuesta_correcta_str = ""

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(padx=20, pady=20, fill="both", expand=True)
        self.form_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.form_frame, text="¡Bienvenido/a! Personalicemos tu aprendizaje", font=ctk.CTkFont(size=24, weight="bold")).grid(row=0, column=0, padx=20, pady=(10, 20))

        # --- Fecha de Nacimiento ---
        ctk.CTkLabel(self.form_frame, text="Tu fecha de nacimiento:", anchor="w").grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")
        dob_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        dob_frame.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        dob_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.day_var = ctk.StringVar(value="Día")
        self.day_menu = ctk.CTkOptionMenu(dob_frame, variable=self.day_var, values=[str(i) for i in range(1, 32)])
        self.day_menu.grid(row=0, column=0, padx=5, sticky="ew")

        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.month_var = ctk.StringVar(value="Mes")
        self.month_menu = ctk.CTkOptionMenu(dob_frame, variable=self.month_var, values=meses)
        self.month_menu.grid(row=0, column=1, padx=5, sticky="ew")

        current_year = datetime.now().year
        years = [str(i) for i in range(current_year - 7, current_year - 100, -1)] # Rango de años lógicos
        self.year_var = ctk.StringVar(value="Año")
        self.year_menu = ctk.CTkOptionMenu(dob_frame, variable=self.year_var, values=years)
        self.year_menu.grid(row=0, column=2, padx=5, sticky="ew")

        # --- Nivel de Estudios ---
        ctk.CTkLabel(self.form_frame, text="Nivel de estudios actual:", anchor="w").grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")
        self.study_level_var = ctk.StringVar(value="Primaria")
        self.study_level_menu = ctk.CTkOptionMenu(self.form_frame, variable=self.study_level_var, values=["Primaria", "Secundaria/Preparatoria", "Universidad"], command=self.update_year_options)
        self.study_level_menu.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # --- Año/Grado Cursado ---
        ctk.CTkLabel(self.form_frame, text="Año/Grado que cursas:", anchor="w").grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")
        self.year_grade_var = ctk.StringVar(value="Selecciona un nivel...")
        self.year_grade_menu = ctk.CTkOptionMenu(self.form_frame, variable=self.year_grade_var, values=["-"])
        self.year_grade_menu.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # --- Objetivo Principal ---
        ctk.CTkLabel(self.form_frame, text="¿Cuál es tu objetivo principal?", anchor="w").grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        self.goal_var = ctk.StringVar(value="Pasar un examen")
        self.goal_menu = ctk.CTkOptionMenu(self.form_frame, variable=self.goal_var, values=["Pasar un examen", "Reforzar mis conocimientos", "Aprender por curiosidad"])
        self.goal_menu.grid(row=8, column=0, padx=20, pady=10, sticky="ew")

        # --- Autoevaluación ---
        ctk.CTkLabel(self.form_frame, text="¿Cómo te sientes con esta área de estudio?", anchor="w").grid(row=9, column=0, padx=20, pady=(10, 0), sticky="w")
        self.confidence_var = ctk.StringVar(value="Me defiendo")
        self.confidence_menu = ctk.CTkOptionMenu(self.form_frame, variable=self.confidence_var, values=["Necesito mucha ayuda", "Me defiendo", "Soy bueno/a pero quiero mejorar"])
        self.confidence_menu.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        self.next_button = ctk.CTkButton(self.form_frame, text="Siguiente: Cuestionario de Nivelación", command=self.iniciar_cuestionario)
        self.next_button.grid(row=11, column=0, padx=20, pady=20, sticky="ew")

        # --- Quiz Frame (oculto inicialmente) ---
        self.quiz_frame = ctk.CTkFrame(self)
        self.quiz_label_pregunta = ctk.CTkLabel(self.quiz_frame, text="Pregunta aquí", font=ctk.CTkFont(size=18), wraplength=550)
        self.quiz_label_pregunta.pack(padx=20, pady=20)
        self.quiz_opciones_frame = ctk.CTkFrame(self.quiz_frame, fg_color="transparent")
        self.quiz_opciones_frame.pack(fill="x", padx=20, pady=20)
        self.loading_label = ctk.CTkLabel(self.quiz_frame, text="Generando cuestionario con IA...", font=ctk.CTkFont(size=16))
        
        # Initialize year options
        self.update_year_options()

    def update_year_options(self, *args):
        level = self.study_level_var.get()
        options = ["-"]
        if level == "Primaria":
            options = [f"{i}º de Primaria" for i in range(1, 7)]
        elif level == "Secundaria/Preparatoria":
            options = [f"{i}º de Secundaria" for i in range(1, 4)] + [f"{i}º de Preparatoria" for i in range(1, 4)]
        elif level == "Universidad":
            options = [f"{i}er Semestre" for i in range(1, 11)]
        
        self.year_grade_menu.configure(values=options)
        self.year_grade_var.set(options[0])

    def iniciar_cuestionario(self):
        try:
            dia_str, mes_str, anio_str = self.day_var.get(), self.month_var.get(), self.year_var.get()
            if "Día" in dia_str or "Mes" in mes_str or "Año" in anio_str:
                raise ValueError("Fecha no seleccionada")
            
            meses_dict = {
                "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
                "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
            }
            fecha_nacimiento = datetime(int(anio_str), meses_dict[mes_str], int(dia_str)).date()
        except (ValueError, KeyError):
            messagebox.showerror("Fecha Inválida", "Por favor, selecciona una fecha de nacimiento válida.", parent=self)
            return

        if self.year_grade_var.get() == "Selecciona un nivel..." or self.year_grade_var.get() == "-":
            messagebox.showerror("Campo Requerido", "Por favor, selecciona el año/grado que cursas.", parent=self)
            return

        hoy = datetime.now().date()
        edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

        self.datos_perfil = {
            'fecha_nacimiento': fecha_nacimiento.isoformat(),
            'edad_calculada': edad,
            'nivel_estudios': self.study_level_var.get(),
            'año_cursado': self.year_grade_var.get(),
            'objetivo_principal': self.goal_var.get(),
            'autoevaluacion': self.confidence_var.get()
        }

        self.next_button.configure(state="disabled", text="Generando...")
        
        # Mostrar frame del quiz y el mensaje de carga
        self.form_frame.pack_forget()
        self.quiz_frame.pack(fill="both", expand=True)
        self.loading_label.pack(pady=20)

        # Iniciar la generación del quiz en un hilo, usando el LearningService
        thread = threading.Thread(target=self.generar_quiz_en_hilo, args=(self.datos_perfil['nivel_estudios'],))
        thread.start()

    def generar_quiz_en_hilo(self, nivel_estudios):
        # Usamos el LearningService para generar el quiz, que a su vez usa el AIService
        quiz_data = self.learning_service.generar_quiz_nivelacion(self.current_user) # Pasar el user object para contexto
        self.after(0, self.procesar_resultado_del_hilo, quiz_data)

    def procesar_resultado_del_hilo(self, quiz_data):
        self.loading_label.pack_forget()
        if not quiz_data:
            messagebox.showerror("Error", "No se pudo generar el cuestionario. Intenta de nuevo.", parent=self)
            # Volver a mostrar el formulario de onboarding para que el usuario pueda reintentar
            self.quiz_frame.pack_forget()
            self.form_frame.pack(fill="both", expand=True)
            self.next_button.configure(state="normal", text="Siguiente: Cuestionario de Nivelación")
            return

        self.quiz_completo = quiz_data
        self.quiz_pregunta_actual_idx = 0
        self.siguiente_pregunta_quiz()

    def siguiente_pregunta_quiz(self):
        if self.quiz_pregunta_actual_idx >= len(self.quiz_completo):
            self.finalizar_cuestionario()
            return

        # Limpiar opciones anteriores
        for widget in self.quiz_opciones_frame.winfo_children():
            widget.destroy()

        self.title(f"Pregunta {self.quiz_pregunta_actual_idx + 1}/{len(self.quiz_completo)}")
        pregunta_actual = self.quiz_completo[self.quiz_pregunta_actual_idx]
        self.respuesta_correcta_str = str(pregunta_actual["respuesta"])

        self.quiz_label_pregunta.configure(text=pregunta_actual["pregunta"])

        self.quiz_opciones_frame.grid_columnconfigure((0, 1), weight=1) # Ajustar columnas para botones de opciones

        # Crear botones para las opciones
        for i, opcion in enumerate(pregunta_actual["opciones"]):
            ctk.CTkButton(self.quiz_opciones_frame, text=str(opcion), 
                            command=lambda opc=opcion: self.verificar_respuesta_quiz(str(opc))
                        ).grid(row=i // 2, column=i % 2, padx=5, pady=5, sticky="ew")
        
        self.quiz_pregunta_actual_idx += 1

    def verificar_respuesta_quiz(self, opcion_elegida_str):
        # No actualizamos el User model aquí con racha/estadísticas, porque es un quiz de nivelación inicial.
        # Solo contamos las respuestas correctas para determinar el nivel inicial.
        if opcion_elegida_str == self.respuesta_correcta_str:
            self.quiz_respuestas_correctas += 1
        
        # Pasar a la siguiente pregunta
        self.siguiente_pregunta_quiz()

    def finalizar_cuestionario(self):
        aciertos = self.quiz_respuestas_correctas
        num_preguntas = len(self.quiz_completo)
        
        # Lógica para determinar el nivel inicial basado en el rendimiento del quiz
        nivel_inicial = 1
        if num_preguntas > 0:
            porcentaje_aciertos = (aciertos / num_preguntas) * 100
            if porcentaje_aciertos >= 80:
                nivel_inicial = 5
            elif porcentaje_aciertos >= 50:
                nivel_inicial = 3
            else:
                nivel_inicial = 1
        
        # Actualizar el objeto User con los datos del perfil y el nivel inicial
        # Esto NO persiste directamente, solo actualiza el objeto en memoria.
        # La persistencia la hará auth_service.actualizar_perfil_inicial.
        self.current_user.datos_perfil.update(self.datos_perfil)
        self.current_user.progreso['nivel'] = nivel_inicial
        self.current_user.progreso['racha_correctas'] = 0 # Reiniciar racha

        # Persistir los cambios del usuario usando AuthService
        self.auth_service.actualizar_perfil_inicial(self.current_user, self.datos_perfil)

        messagebox.showinfo(
            "¡Listo!",
            f"¡Configuración completa!\nHas acertado {aciertos} de {num_preguntas} preguntas.\nTu nivel de partida será el {nivel_inicial}.",
            parent=self
        )
        self.destroy()
        # Llamar al callback para lanzar el dashboard principal, pasando el user actualizado
        self.callback_final(self.current_user)
        