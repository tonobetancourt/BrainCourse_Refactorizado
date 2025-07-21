from datetime import datetime

class Course:
    def __init__(self, id_curso, tema_general, creador_email, miembros=None, modulos=None, progreso_general=0.0, calificacion_promedio=None):
        self.id_curso = id_curso
        self.tema_general = tema_general
        self.creador_email = creador_email
        self.miembros = miembros if miembros is not None else []  # [{'email': ..., 'rol': 'profesor'/'alumno'/'co-profesor'}]
        self.modulos = modulos if modulos is not None else []
        self.progreso_general = progreso_general
        self.calificacion_promedio = calificacion_promedio

    # Métodos para manejar miembros
    def agregar_miembro(self, email, rol):
        if not any(m['email'] == email for m in self.miembros):
            self.miembros.append({'email': email, 'rol': rol})

    def quitar_miembro(self, email):
        self.miembros = [m for m in self.miembros if m['email'] != email]

    def cambiar_rol_miembro(self, email, nuevo_rol):
        for m in self.miembros:
            if m['email'] == email:
                m['rol'] = nuevo_rol

    # Métodos de serialización
    def to_dict(self):
        return {
            'id_curso': self.id_curso,
            'tema_general': self.tema_general,
            'creador_email': self.creador_email,
            'miembros': self.miembros,
            'modulos': self.modulos,
            'progreso_general': self.progreso_general,
            'calificacion_promedio': self.calificacion_promedio
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id_curso=data['id_curso'],
            tema_general=data['tema_general'],
            creador_email=data['creador_email'],
            miembros=data.get('miembros', []),
            modulos=data.get('modulos', []),
            progreso_general=data.get('progreso_general', 0.0),
            calificacion_promedio=data.get('calificacion_promedio')
        )
