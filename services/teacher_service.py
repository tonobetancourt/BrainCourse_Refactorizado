# services/teacher_service.py (VERSIÓN FINAL Y COMPLETA)

from models.user_model import User
from data import gestion_usuarios as user_dao
from services.auth_service import AuthService
from services.course_service import CourseService
from services.quality_control_service import QualityControlService
from ai_integration.ai_service import AIService


class TeacherService:
    def __init__(self, auth_service_instance: AuthService, course_service_instance: CourseService, qc_service_instance: QualityControlService):
        self.auth_service = auth_service_instance
        self.user_dao = self.auth_service.user_dao
        self.course_service = course_service_instance
        self.qc_service = qc_service_instance

    def invitar_alumno(self, profesor_user: User, alumno_email: str) -> tuple[bool, str]:
        """
        Envía una invitación de vinculación a un alumno.
        Retorna (True, mensaje_exito) o (False, mensaje_error).
        """
        alumno_email = alumno_email.lower()
        all_users_data = self.user_dao.cargar_usuarios()
        
        if alumno_email not in all_users_data or all_users_data[alumno_email].get('rol') != 'alumno':
            return False, "No se encontró un alumno con ese correo electrónico."
        
        alumno_user_obj = User.from_dict(alumno_email, all_users_data[alumno_email])

        if alumno_user_obj.email in profesor_user.alumnos_vinculados:
            return False, "Este alumno ya está vinculado contigo."
        
        if profesor_user.email in alumno_user_obj.invitaciones_profesor:
            return False, "Ya le has enviado una invitación a este alumno y está pendiente."

        if alumno_user_obj.recibir_invitacion_profesor(profesor_user.email):
            alumno_user_obj.agregar_notificacion(f"El profesor {profesor_user.nombre} te ha invitado a vincularte.")
            self.user_dao.actualizar_datos_usuario(alumno_user_obj.email, alumno_user_obj.to_dict())
            return True, f"Invitación enviada a {alumno_email}."
        
        return False, "No se pudo enviar la invitación (posiblemente ya existe)."

    def manejar_solicitud_alumno(self, profesor_user: User, alumno_email: str, aceptar: bool) -> tuple[bool, str]:
        """
        Gestiona una solicitud de vinculación de un alumno (aceptar o rechazar).
        Retorna (True, mensaje_exito) o (False, mensaje_error).
        """
        alumno_email = alumno_email.lower()
        all_users_data = self.user_dao.cargar_usuarios()
        
        if alumno_email not in all_users_data or all_users_data[alumno_email].get('rol') != 'alumno':
            return False, "No se encontraron los datos del alumno."

        alumno_user_obj = User.from_dict(alumno_email, all_users_data[alumno_email])

        if profesor_user.email in alumno_user_obj.solicitudes_enviadas:
            alumno_user_obj.solicitudes_enviadas.remove(profesor_user.email)
        
        if aceptar:
            success_prof_side = profesor_user.aceptar_solicitud_alumno(alumno_email)

            if success_prof_side:
                alumno_user_obj.agregar_notificacion(f"El profesor {profesor_user.nombre} ha aceptado tu solicitud de vinculación.")
                self.user_dao.actualizar_datos_usuario(alumno_user_obj.email, alumno_user_obj.to_dict())
                self.user_dao.actualizar_datos_usuario(profesor_user.email, profesor_user.to_dict()) 
                return True, f"Solicitud de {alumno_email} aceptada y vinculación establecida."
            else:
                return False, f"No se pudo aceptar la solicitud de {alumno_email} (posiblemente ya vinculado o no pendiente)."
        else:
            success_prof_side = profesor_user.rechazar_solicitud_alumno(alumno_email)
            
            if success_prof_side:
                alumno_user_obj.agregar_notificacion(f"El profesor {profesor_user.nombre} ha rechazado tu solicitud de vinculación.")
                self.user_dao.actualizar_datos_usuario(alumno_user_obj.email, alumno_user_obj.to_dict())
                self.user_dao.actualizar_datos_usuario(profesor_user.email, profesor_user.to_dict()) 
                return True, f"Solicitud de {alumno_email} rechazada."
            else:
                return False, f"No se pudo rechazar la solicitud de {alumno_email} (posiblemente no pendiente)."
        
    def desvincular_alumno(self, profesor_user: User, alumno_email: str) -> tuple[bool, str]:
        """
        Desvincula a un alumno del profesor.
        Retorna (True, mensaje_exito) o (False, mensaje_error).
        """
        alumno_email = alumno_email.lower()
        all_users_data = self.user_dao.cargar_usuarios()

        if alumno_email not in all_users_data or all_users_data[alumno_email].get('rol') != 'alumno':
            return False, "No se encontraron los datos del alumno a desvincular."
        
        alumno_user_obj = User.from_dict(alumno_email, all_users_data[alumno_email])

        if profesor_user.desvincular_alumno(alumno_email):
            if profesor_user.email in alumno_user_obj.profesores_vinculados:
                alumno_user_obj.profesores_vinculados.remove(profesor_user.email)
                alumno_user_obj.agregar_notificacion(f"El profesor {profesor_user.nombre} te ha desvinculado.")
                self.user_dao.actualizar_datos_usuario(profesor_user.email, profesor_user.to_dict())
                self.user_dao.actualizar_datos_usuario(alumno_user_obj.email, alumno_user_obj.to_dict())
                return True, f"{alumno_email} ha sido desvinculado exitosamente."
        
        return False, "El alumno no estaba vinculado."

    def obtener_alumnos_vinculados_con_data(self, profesor_user: User) -> list[dict]:
        """
        Retorna una lista de diccionarios con datos relevantes de los alumnos vinculados.
        Incluye nombre, email y un resumen de estadísticas/progreso.
        """
        alumnos_data = []
        all_users_data = self.user_dao.cargar_usuarios()

        for email_alumno in profesor_user.alumnos_vinculados:
            alumno_full_data = all_users_data.get(email_alumno)
            if alumno_full_data:
                alumno_obj = User.from_dict(email_alumno, alumno_full_data)
                alumnos_data.append({
                    "email": alumno_obj.email,
                    "nombre": alumno_obj.nombre,
                    "nivel": alumno_obj.progreso.get('nivel', 1),
                    "preguntas_totales": alumno_obj.estadisticas.get('preguntas_totales', 0),
                    "aciertos_totales": alumno_obj.estadisticas.get('aciertos_totales', 0),
                    "rendimiento_por_tema": alumno_obj.estadisticas.get('rendimiento_por_tema', {}),
                    "historial_actividad_reciente": alumno_obj.historial_actividad[:10],
                    "cursos_asignados": alumno_obj.cursos
                })
        return alumnos_data
    
    def asignar_curso_a_alumno(self, profesor_user: User, alumno_email: str, tema: str) -> tuple[bool, str]:
        """
        Asigna un nuevo curso a un alumno vinculado.
        Retorna (True, mensaje_exito) o (False, mensaje_error).
        """
        alumno_email = alumno_email.lower()
        all_users_data = self.user_dao.cargar_usuarios()

        if alumno_email not in all_users_data or all_users_data[alumno_email].get('rol') != 'alumno':
            return False, "No se encontró el alumno o no es un alumno válido."
        
        if alumno_email not in profesor_user.alumnos_vinculados:
            return False, "El alumno no está vinculado con este profesor."

        alumno_user_obj = User.from_dict(alumno_email, all_users_data[alumno_email])
        
        nuevo_curso = self.course_service.crear_curso_para_usuario(alumno_user_obj, tema)
        
        if nuevo_curso:
            alumno_user_obj.agregar_notificacion(f"Tu profesor, {profesor_user.nombre}, te ha asignado un nuevo curso sobre '{tema}'.")
            self.user_dao.actualizar_datos_usuario(alumno_user_obj.email, alumno_user_obj.to_dict()) 
            return True, f"Curso sobre '{tema}' asignado a {alumno_email}."
        
        return False, "No se pudo generar y asignar el curso."

    def guardar_correccion_ia(self, profesor_email: str, pregunta_original_data: dict, correccion_data: dict) -> bool:
        """
        Registra una corrección de la IA enviada por un profesor.
        Delega al QualityControlService.
        """
        return self.qc_service.guardar_reporte(profesor_email, pregunta_original_data, correccion_data)
    
    def obtener_reportes_correccion(self):
        """Obtiene todos los reportes de corrección de la IA."""
        return self.qc_service.obtener_reportes()

    def actualizar_estado_reporte_correccion(self, reporte_id: str, nuevo_estado: str) -> bool:
        """Actualiza el estado de un reporte de corrección de la IA."""
        return self.qc_service.actualizar_estado_reporte(reporte_id, nuevo_estado)