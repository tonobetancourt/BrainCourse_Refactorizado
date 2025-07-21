# data/gestion_usuarios.py

import json
import os
import hashlib

RUTA_USUARIOS = os.path.join(os.path.dirname(__file__), 'usuarios.json')

def cargar_usuarios():
    """Carga todos los datos de usuarios desde el archivo JSON."""
    if not os.path.exists(RUTA_USUARIOS):
        with open(RUTA_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
        return {}
    try:
        with open(RUTA_USUARIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error al cargar usuarios.json: {e}")
        try:
            with open(RUTA_USUARIOS, 'w', encoding='utf-8') as f:
                json.dump({}, f, indent=4, ensure_ascii=False)
            return {}
        except IOError as e_write:
            print(f"Error al intentar crear un nuevo usuarios.json: {e_write}")
            return {}


def guardar_usuarios(usuarios):
    """Guarda todos los datos de usuarios en el archivo JSON."""
    try:
        with open(RUTA_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error al guardar usuarios.json: {e}")

def hashear_contrasena(contrasena):
    """Genera un hash SHA256 para la contraseña."""
    return hashlib.sha256(contrasena.encode('utf-8')).hexdigest()

def actualizar_datos_usuario(correo: str, datos_a_actualizar: dict):
    """
    Actualiza los datos de un usuario específico en el archivo JSON.
    Esta función es parte del DAO, ya que es una operación de persistencia para un solo usuario.
    """
    usuarios = cargar_usuarios()
    correo = correo.lower()

    if correo in usuarios:
        usuarios[correo].update(datos_a_actualizar)
        guardar_usuarios(usuarios)
        return True
    return False