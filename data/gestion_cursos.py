import json
import os

RUTA_CURSOS = os.path.join(os.path.dirname(__file__), 'cursos.json')

def cargar_cursos():
    """Carga todos los cursos desde el archivo JSON."""
    if not os.path.exists(RUTA_CURSOS):
        with open(RUTA_CURSOS, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4, ensure_ascii=False)
        return []
    try:
        with open(RUTA_CURSOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def guardar_cursos(cursos):
    """Guarda la lista completa de cursos en el archivo JSON."""
    with open(RUTA_CURSOS, 'w', encoding='utf-8') as f:
        json.dump(cursos, f, indent=4, ensure_ascii=False)

def actualizar_curso(curso_dict):
    """Actualiza (o agrega) un curso en el archivo JSON."""
    cursos = cargar_cursos()
    idx = next((i for i, c in enumerate(cursos) if c['id_curso'] == curso_dict['id_curso']), None)
    if idx is not None:
        cursos[idx] = curso_dict
    else:
        cursos.append(curso_dict)
    guardar_cursos(cursos)

def obtener_curso_por_id(id_curso):
    """Devuelve el dict del curso por su ID, o None si no existe."""
    cursos = cargar_cursos()
    return next((c for c in cursos if c['id_curso'] == id_curso), None)

def obtener_cursos_de_usuario(email):
    """Devuelve una lista de cursos (dict) donde el usuario es miembro."""
    cursos = cargar_cursos()
    return [c for c in cursos if any(m['email'] == email for m in c.get('miembros', []))]
