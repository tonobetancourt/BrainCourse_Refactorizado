# services/auth_service.py (CORREGIDO COMPLETO)

from data import gestion_usuarios as user_dao
from models.user_model import User

class AuthService:
    def __init__(self, user_dao_module=user_dao): # Acepta user_dao como un argumento por defecto
        self.user_dao = user_dao_module # ¡Ahora user_dao es un atributo de la instancia!

    def registrar_usuario(self, nombre, correo, contrasena, rol):
        """
        Registra un nuevo usuario en el sistema.
        Retorna True y el objeto User si el registro es exitoso, False y un mensaje de error si no.
        """
        correo = correo.lower()
        usuarios_data = self.user_dao.cargar_usuarios() # Usa self.user_dao

        if correo in usuarios_data:
            return False, "El correo electrónico ya está registrado."
        
        contrasena_hash = self.user_dao.hashear_contrasena(contrasena) # Usa self.user_dao

        # Crear un diccionario con los datos iniciales para el nuevo usuario
        user_initial_data = {
            'nombre': nombre,
            'contrasena_hash': contrasena_hash,
            'rol': rol,
            'perfil_completo': False,
            'datos_perfil': {},
            'progreso': {'nivel': 1, 'racha_correctas': 0},
            'historial_temas': [],
            'logros': {"primer_quiz": None, "mente_brillante": None, "racha_5": None, "polimata_5": None},
            'estadisticas': {"preguntas_totales": 0, "aciertos_totales": 0, "rendimiento_por_tema": {}},
            'cursos': [],
            'historial_actividad': [],
        }

        if rol == 'profesor':
            user_initial_data['alumnos_vinculados'] = []
            user_initial_data['solicitudes_pendientes'] = []
        else: # rol == 'alumno'
            user_initial_data['profesores_vinculados'] = []
            user_initial_data['solicitudes_enviadas'] = []
            user_initial_data['invitaciones_profesor'] = []
            user_initial_data['notificaciones'] = []

        # Guardar el diccionario de datos del nuevo usuario usando el DAO
        usuarios_data[correo] = user_initial_data
        self.user_dao.guardar_usuarios(usuarios_data) # Usa self.user_dao

        # Retornar el objeto User creado
        nuevo_user_obj = User.from_dict(correo, user_initial_data)
        return True, nuevo_user_obj

    def verificar_usuario(self, correo, contrasena):
        """
        Verifica las credenciales del usuario.
        Retorna True y el objeto User si las credenciales son correctas,
        False y un mensaje de error si no.
        """
        correo = correo.lower()
        usuarios_data = self.user_dao.cargar_usuarios() # Usa self.user_dao

        if correo not in usuarios_data:
            return False, "El correo electrónico no está registrado."
        
        usuario_data = usuarios_data[correo]
        
        contrasena_hasheada = self.user_dao.hashear_contrasena(contrasena) # Usa self.user_dao

        if usuario_data['contrasena_hash'] == contrasena_hasheada:
            # Cargar el diccionario de datos a un objeto User
            user_obj = User.from_dict(correo, usuario_data)
            return True, user_obj
        else:
            return False, "La contraseña es incorrecta."

    def actualizar_perfil_inicial(self, user: User, perfil_data: dict):
        """Actualiza los datos iniciales del perfil del usuario (onboarding)."""
        user.perfil_completo = True
        user.datos_perfil.update(perfil_data)
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict()) # Usa self.user_dao
        return True

    def eliminar_cuenta(self, email: str, contrasena: str):
        """
        Elimina una cuenta de usuario de forma segura y sus referencias en otros usuarios.
        """
        usuarios = self.user_dao.cargar_usuarios() # Usa self.user_dao
        email = email.lower()

        if email not in usuarios:
            return False, "Usuario no encontrado."

        # 1. Verificar contraseña
        hash_ingresado = self.user_dao.hashear_contrasena(contrasena) # Usa self.user_dao
        if usuarios[email]['contrasena_hash'] != hash_ingresado:
            return False, "La contraseña es incorrecta. La cuenta no ha sido eliminada."

        # 2. Determinar rol y obtener datos
        rol_eliminado = usuarios[email].get('rol')
        
        # 3. Eliminar la cuenta
        del usuarios[email]

        # 4. Limpiar referencias en otros perfiles
        for other_email, other_user_data in usuarios.items():
            other_user_obj = User.from_dict(other_email, other_user_data)

            if rol_eliminado == 'profesor':
                if other_user_obj.rol == 'alumno':
                    if email in other_user_obj.profesores_vinculados:
                        other_user_obj.profesores_vinculados.remove(email)
                    if email in other_user_obj.solicitudes_enviadas:
                        other_user_obj.solicitudes_enviadas.remove(email)
                    if email in other_user_obj.invitaciones_profesor:
                        other_user_obj.invitaciones_profesor.remove(email)
                    self.user_dao.actualizar_datos_usuario(other_user_obj.email, other_user_obj.to_dict()) # Usa self.user_dao
            elif rol_eliminado == 'alumno':
                if other_user_obj.rol == 'profesor':
                    if email in other_user_obj.alumnos_vinculados:
                        other_user_obj.alumnos_vinculados.remove(email)
                    if email in other_user_obj.solicitudes_pendientes:
                        other_user_obj.solicitudes_pendientes.remove(email)
                    self.user_dao.actualizar_datos_usuario(other_user_obj.email, other_user_obj.to_dict()) # Usa self.user_dao

        self.user_dao.guardar_usuarios(usuarios) # Usa self.user_dao # Guardar los cambios finales después de la limpieza
        return True, "Cuenta eliminada permanentemente con éxito."

    def actualizar_datos_generales_usuario(self, user: User, datos_a_actualizar: dict):
        """Actualiza datos generales del perfil del usuario (nombre, nivel de estudios, etc.)."""
        if 'nombre' in datos_a_actualizar:
            user.nombre = datos_a_actualizar['nombre']
        if 'datos_perfil' in datos_a_actualizar:
            user.datos_perfil.update(datos_a_actualizar['datos_perfil'])
        
        self.user_dao.actualizar_datos_usuario(user.email, user.to_dict()) # Usa self.user_dao
        return True

    def cambiar_contrasena(self, user_email: str, old_password: str, new_password: str):
        """Cambia la contraseña de un usuario."""
        usuarios = self.user_dao.cargar_usuarios() # Usa self.user_dao
        user_email = user_email.lower()
        
        if user_email not in usuarios:
            return False, "Usuario no encontrado."
        
        user_data = usuarios[user_email]
        if self.user_dao.hashear_contrasena(old_password) != user_data['contrasena_hash']: # Usa self.user_dao
            return False, "La contraseña actual es incorrecta."
        
        user_data['contrasena_hash'] = self.user_dao.hashear_contrasena(new_password) # Usa self.user_dao
        self.user_dao.guardar_usuarios(usuarios) # Usa self.user_dao
        return True, "Contraseña actualizada con éxito."