# services/course_service.py

from models.user_model import User
from models.course_model import Course
from data import gestion_usuarios as user_dao
from data import gestion_cursos as course_dao
from ai_integration.ai_service import AIService
from services import curso_generator

class CourseService:
    def __init__(self, user_dao_module, ai_service_instance: AIService):
        self.user_dao = user_dao_module
        self.ai_service = ai_service_instance

    def crear_curso(self, creador: User, tema: str):
        new_course_data = curso_generator.generar_silabo_curso(tema, self.ai_service)
        if new_course_data:
            course = Course(
                id_curso=new_course_data['id_curso'],
                tema_general=tema,
                creador_email=creador.email,
                miembros=[{'email': creador.email, 'rol': 'profesor'}],
                modulos=new_course_data['modulos']
            )
            creador.agregar_curso(course.id_curso, 'profesor')
            self.user_dao.actualizar_datos_usuario(creador.email, creador.to_dict())
            course_dao.actualizar_curso(course.to_dict())
            return course
        return None

    def agregar_miembro_a_curso(self, course: Course, user: User, rol: str):
        course.agregar_miembro(user.email, rol)
        user.agregar_curso(course.id_curso, rol)
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict())
        course_dao.actualizar_curso(course.to_dict())

    def quitar_miembro_de_curso(self, course: Course, user: User):
        course.quitar_miembro(user.email)
        user.quitar_curso(course.id_curso)
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict())
        course_dao.actualizar_curso(course.to_dict())

    def obtener_cursos_de_usuario(self, user: User):
        return [Course.from_dict(c) for c in course_dao.obtener_cursos_de_usuario(user.email)]

    def obtener_curso_por_id(self, id_curso):
        c = course_dao.obtener_curso_por_id(id_curso)
        return Course.from_dict(c) if c else None

    def crear_curso_para_usuario(self, user: User, topic: str):
        """
        Genera un nuevo curso usando la IA y lo asigna al usuario.
        Retorna el objeto curso generado si tiene éxito, None en caso contrario.
        """
        new_course_data = curso_generator.generar_silabo_curso(topic, self.ai_service)
        if new_course_data:
            user.asignar_curso(new_course_data)
            self.user_dao.actualizar_datos_usuario(user.email, user.to_dict())
            return new_course_data
        return None

    def eliminar_curso_de_usuario(self, user: User, course_id: str):
        """Elimina un curso del perfil del usuario."""
        user.eliminar_curso(course_id)
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict())
        return True

    def obtener_teoria_subtema(self, user: User, course_id: str, module_id: str, subtema: str):
        """
        Obtiene la teoría de un subtema. Si no está cacheada, la genera con IA y la guarda.
        Retorna el texto de la teoría.
        """
        # Buscar el curso oficial (no solo el del usuario)
        from data import gestion_cursos as course_dao
        curso_oficial = course_dao.obtener_curso_por_id(course_id)
        if not curso_oficial:
            return "Error: Curso no encontrado."
        modulo = next((m for m in curso_oficial['modulos'] if m['id_modulo'] == module_id), None)
        if not modulo:
            return "Error: Módulo no encontrado."
        teoria_cache = modulo.get("teoria_generada", {}).get(subtema)
        if teoria_cache:
            return teoria_cache
        else:
            from services import curso_generator
            teoria = curso_generator.generar_teoria_subtema(subtema, self.ai_service)
            if "No se pudo generar" not in teoria:
                if 'teoria_generada' not in modulo:
                    modulo['teoria_generada'] = {}
                modulo['teoria_generada'][subtema] = teoria
                course_dao.actualizar_curso(curso_oficial)
            return teoria

    def marcar_modulo_completado(self, user: User, course_id: str, module_id: str, quiz_score: float):
        """
        Marca un módulo como completado y actualiza la calificación del examen.
        """
        user.actualizar_progreso_modulo(course_id, module_id, completado=True, calificacion_examen=quiz_score)
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict())
        return True