# models/user_model.py

from datetime import datetime

class User:
    def __init__(self, email, nombre, contrasena_hash, rol, perfil_completo=False, datos_perfil=None,
                 progreso=None, historial_temas=None, logros=None, estadisticas=None, cursos=None,
                 historial_actividad=None, profesores_vinculados=None, solicitudes_enviadas=None,
                 invitaciones_profesor=None, notificaciones=None, alumnos_vinculados=None,
                 solicitudes_pendientes=None):
        
        self.email = email
        self.nombre = nombre
        self.contrasena_hash = contrasena_hash
        self.rol = rol
        self.perfil_completo = perfil_completo
        self.datos_perfil = datos_perfil if datos_perfil is not None else {}
        
        self.progreso = progreso if progreso is not None else {'nivel': 1, 'racha_correctas': 0}
        self.historial_temas = historial_temas if historial_temas is not None else []
        self.logros = logros if logros is not None else {"primer_quiz": None, "mente_brillante": None, "racha_5": None, "polimata_5": None}
        self.estadisticas = estadisticas if estadisticas is not None else {"preguntas_totales": 0, "aciertos_totales": 0, "rendimiento_por_tema": {}}
        self.cursos = cursos if cursos is not None else []
        self.historial_actividad = historial_actividad if historial_actividad is not None else []
        
        # Campos específicos de Alumno
        self.profesores_vinculados = profesores_vinculados if profesores_vinculados is not None else []
        self.solicitudes_enviadas = solicitudes_enviadas if solicitudes_enviadas is not None else []
        self.invitaciones_profesor = invitaciones_profesor if invitaciones_profesor is not None else []
        self.notificaciones = notificaciones if notificaciones is not None else []

        # Campos específicos de Profesor
        self.alumnos_vinculados = alumnos_vinculados if alumnos_vinculados is not None else []
        self.solicitudes_pendientes = solicitudes_pendientes if solicitudes_pendientes is not None else []

    @classmethod
    def from_dict(cls, email, data):
        """Crea una instancia de User desde un diccionario de datos."""
        return cls(
            email=email,
            nombre=data.get('nombre'),
            contrasena_hash=data.get('contrasena_hash'),
            rol=data.get('rol'),
            perfil_completo=data.get('perfil_completo', False),
            datos_perfil=data.get('datos_perfil'),
            progreso=data.get('progreso'),
            historial_temas=data.get('historial_temas'),
            logros=data.get('logros'),
            estadisticas=data.get('estadisticas'),
            cursos=data.get('cursos'),
            historial_actividad=data.get('historial_actividad'),
            profesores_vinculados=data.get('profesores_vinculados'),
            solicitudes_enviadas=data.get('solicitudes_enviadas'),
            invitaciones_profesor=data.get('invitaciones_profesor'),
            notificaciones=data.get('notificaciones'),
            alumnos_vinculados=data.get('alumnos_vinculados'),
            solicitudes_pendientes=data.get('solicitudes_pendientes')
        )

    def to_dict(self):
        """Convierte la instancia de User a un diccionario para guardar en JSON."""
        data = {
            'nombre': self.nombre,
            'contrasena_hash': self.contrasena_hash,
            'rol': self.rol,
            'perfil_completo': self.perfil_completo,
            'datos_perfil': self.datos_perfil,
            'progreso': self.progreso,
            'historial_temas': self.historial_temas,
            'logros': self.logros,
            'estadisticas': self.estadisticas,
            'cursos': self.cursos,
            'historial_actividad': self.historial_actividad,
        }
        if self.rol == 'alumno':
            data['profesores_vinculados'] = self.profesores_vinculados
            data['solicitudes_enviadas'] = self.solicitudes_enviadas
            data['invitaciones_profesor'] = self.invitaciones_profesor
            data['notificaciones'] = self.notificaciones
        elif self.rol == 'profesor':
            data['alumnos_vinculados'] = self.alumnos_vinculados
            data['solicitudes_pendientes'] = self.solicitudes_pendientes
        return data

    def registrar_respuesta_quiz(self, tema, es_correcta, pregunta_texto, respuesta_usuario, respuesta_correcta_ia):
        """Actualiza estadísticas y historial de actividad por una respuesta de quiz."""
        self.estadisticas['preguntas_totales'] = self.estadisticas.get('preguntas_totales', 0) + 1
        if tema not in self.estadisticas.get('rendimiento_por_tema', {}):
            self.estadisticas['rendimiento_por_tema'][tema] = {"aciertos": 0, "total": 0}
        self.estadisticas['rendimiento_por_tema'][tema]['total'] += 1

        if es_correcta:
            self.estadisticas['aciertos_totales'] = self.estadisticas.get('aciertos_totales', 0) + 1
            self.estadisticas['rendimiento_por_tema'][tema]['aciertos'] += 1
        
        actividad = {
            "fecha": datetime.now().isoformat(),
            "tipo": "Quiz de Práctica" if self.rol == 'alumno' else "Revisión de Quiz (Profesor)", # Ajustar según contexto
            "tema": tema,
            "resultado": "Correcta" if es_correcta else "Incorrecta",
            "pregunta": pregunta_texto,
            "respuesta_usuario": str(respuesta_usuario),
            "respuesta_correcta_ia": str(respuesta_correcta_ia),
            "fue_correcta": es_correcta
        }
        if self.rol == 'alumno':
            self.historial_actividad.insert(0, actividad)

    def incrementar_racha(self):
        """Incrementa la racha de respuestas correctas."""
        self.progreso['racha_correctas'] = self.progreso.get('racha_correctas', 0) + 1

    def resetear_racha(self):
        """Reinicia la racha de respuestas correctas."""
        self.progreso['racha_correctas'] = 0

    def subir_nivel(self):
        """Incrementa el nivel del usuario."""
        self.progreso['nivel'] = self.progreso.get('nivel', 1) + 1

    def agregar_historial_tema(self, tema):
        """Añade un tema al historial de temas practicados."""
        if tema in self.historial_temas:
            self.historial_temas.remove(tema)
        self.historial_temas.insert(0, tema)
        self.historial_temas = self.historial_temas[:5]

    def desbloquear_logro(self, logro_id):
        """Marca un logro como desbloqueado."""
        if self.logros.get(logro_id) is None:
            self.logros[logro_id] = datetime.now().isoformat()
            return True
        return False

    def agregar_notificacion(self, texto):
        """Añade una notificación al usuario."""
        notificacion = {
            "id": f"notif_{datetime.now().timestamp()}",
            "fecha": datetime.now().isoformat(),
            "texto": texto,
            "leida": False
        }
        self.notificaciones.insert(0, notificacion)

    def marcar_notificaciones_leidas(self):
        """Marca todas las notificaciones como leídas."""
        for notif in self.notificaciones:
            notif['leida'] = True

    def agregar_curso(self, curso_id, rol_en_curso):
        """Agrega un curso al usuario con un rol específico (alumno/profesor/co-profesor)."""
        if not hasattr(self, 'cursos_membresia'):
            self.cursos_membresia = []
        if not any(m['id_curso'] == curso_id for m in self.cursos_membresia):
            self.cursos_membresia.append({'id_curso': curso_id, 'rol_en_curso': rol_en_curso})

    def quitar_curso(self, curso_id):
        """Quita un curso de la membresía del usuario."""
        if hasattr(self, 'cursos_membresia'):
            self.cursos_membresia = [m for m in self.cursos_membresia if m['id_curso'] != curso_id]

    def encontrar_curso(self, id_curso):
        """Busca y retorna un curso por su ID."""
        return next((c for c in self.cursos if c['id_curso'] == id_curso), None)

    def actualizar_progreso_modulo(self, id_curso, id_modulo, completado, calificacion_examen=None):
        """Actualiza el estado de un módulo dentro de un curso."""
        curso = self.encontrar_curso(id_curso)
        if curso:
            modulo = next((m for m in curso['modulos'] if m['id_modulo'] == id_modulo), None)
            if modulo:
                modulo['completado'] = completado
                if calificacion_examen is not None:
                    modulo['calificacion_examen'] = round(calificacion_examen, 2)
                
                modulos_completados = sum(1 for m in curso['modulos'] if m.get('completado'))
                curso['progreso_general'] = modulos_completados / len(curso['modulos'])
                
                calificaciones = [m['calificacion_examen'] for m in curso['modulos'] if m.get('completado') and m.get('calificacion_examen') is not None]
                if calificaciones:
                    curso['calificacion_promedio'] = round(sum(calificaciones) / len(calificaciones), 2)
                else:
                    curso['calificacion_promedio'] = None

    def guardar_teoria_generada(self, id_curso, id_modulo, subtema, teoria):
        """Guarda la teoría generada para un subtema específico."""
        curso = self.encontrar_curso(id_curso)
        if curso:
            modulo = next((m for m in curso['modulos'] if m['id_modulo'] == id_modulo), None)
            if modulo:
                if 'teoria_generada' not in modulo:
                    modulo["teoria_generada"] = {}
                modulo["teoria_generada"][subtema] = teoria

    def enviar_solicitud_vinculacion(self, email_profesor):
        """Envía una solicitud de vinculación a un profesor."""
        if self.rol == 'alumno' and email_profesor not in self.solicitudes_enviadas:
            self.solicitudes_enviadas.append(email_profesor)
            return True
        return False

    def recibir_invitacion_profesor(self, email_profesor):
        """Recibe una invitación de un profesor."""
        if self.rol == 'alumno' and email_profesor not in self.invitaciones_profesor:
            self.invitaciones_profesor.append(email_profesor)
            return True
        return False

    def aceptar_invitacion(self, email_profesor):
        """Acepta una invitación de vinculación de profesor."""
        if self.rol == 'alumno' and email_profesor in self.invitaciones_profesor:
            self.invitaciones_profesor.remove(email_profesor)
            if email_profesor not in self.profesores_vinculados:
                self.profesores_vinculados.append(email_profesor)
            return True
        return False

    def rechazar_invitacion(self, email_profesor):
        """Rechaza una invitación de vinculación de profesor."""
        if self.rol == 'alumno' and email_profesor in self.invitaciones_profesor:
            self.invitaciones_profesor.remove(email_profesor)
            return True
        return False

    def recibir_solicitud_alumno(self, email_alumno):
        """Recibe una solicitud de vinculación de un alumno."""
        if self.rol == 'profesor' and email_alumno not in self.solicitudes_pendientes:
            self.solicitudes_pendientes.append(email_alumno)
            return True
        return False
    
    def aceptar_solicitud_alumno(self, email_alumno):
        """Acepta una solicitud de vinculación de un alumno."""
        if self.rol == 'profesor' and email_alumno in self.solicitudes_pendientes:
            self.solicitudes_pendientes.remove(email_alumno)
            if email_alumno not in self.alumnos_vinculados:
                self.alumnos_vinculados.append(email_alumno)
            return True
        return False

    def rechazar_solicitud_alumno(self, email_alumno):
        """Rechaza una solicitud de vinculación de un alumno."""
        if self.rol == 'profesor' and email_alumno in self.solicitudes_pendientes:
            self.solicitudes_pendientes.remove(email_alumno)
            return True
        return False
        
    def desvincular_alumno(self, email_alumno):
        """Desvincula un alumno del profesor."""
        if self.rol == 'profesor' and email_alumno in self.alumnos_vinculados:
            self.alumnos_vinculados.remove(email_alumno)
            return True
        return False

    def asignar_curso(self, curso_dict):
        """Agrega un curso completo (dict) a la lista de cursos del usuario."""
        if not any(c['id_curso'] == curso_dict['id_curso'] for c in self.cursos):
            self.cursos.append(curso_dict)