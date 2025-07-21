# debug_gestion.py

import os
import sys

print("--- INFORMACIÓN DE LA RUTA DE PYTHON ---")
print(f"Versión de Python: {sys.version}")
print(f"Ruta del ejecutable Python: {sys.executable}")
print(f"Rutas de búsqueda de módulos de Python (sys.path):")
for p in sys.path:
    print(f"  - {p}")
print("-" * 40)

gestion_usuarios_path = os.path.join(os.path.dirname(__file__), 'data', 'gestion_usuarios.py')

print(f"--- VERIFICANDO ARCHIVO EN DISCO: {gestion_usuarios_path} ---")
if os.path.exists(gestion_usuarios_path):
    print(f"El archivo existe en disco. Tamaño: {os.path.getsize(gestion_usuarios_path)} bytes.")
    try:
        with open(gestion_usuarios_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\nContenido del archivo (primeras 2000 caracteres):")
            print(content[:2000])
            if "def actualizar_datos_usuario(" in content:
                print("\n¡La función 'actualizar_datos_usuario' FUE ENCONTRADA en el contenido del archivo!")
            else:
                print("\nADVERTENCIA: La función 'actualizar_datos_usuario' NO FUE ENCONTRADA en el contenido del archivo.")
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
else:
    print("ERROR: ¡El archivo NO existe en la ruta esperada en disco!")
print("-" * 40)

print("--- INTENTANDO IMPORTAR Y VERIFICAR EL MÓDULO ---")
try:
    # Asegurarse de que la ruta del proyecto esté en sys.path para importaciones relativas
    # Es crucial para que 'from data import gestion_usuarios' funcione correctamente
    project_root_path = os.path.abspath(os.path.dirname(__file__))
    if project_root_path not in sys.path:
        sys.path.insert(0, project_root_path)
    
    from data import gestion_usuarios as debug_user_dao

    print(f"Módulo 'gestion_usuarios' importado exitosamente.")
    print(f"Ruta del módulo cargado: {debug_user_dao.__file__}")

    if hasattr(debug_user_dao, 'actualizar_datos_usuario'):
        print("¡El módulo cargado TIENE el atributo 'actualizar_datos_usuario'!")
        print(f"Tipo del atributo: {type(debug_user_dao.actualizar_datos_usuario)}")
    else:
        print("ERROR: ¡El módulo cargado NO TIENE el atributo 'actualizar_datos_usuario'!")

except ImportError as e:
    print(f"Error de importación al cargar 'data.gestion_usuarios': {e}")
except Exception as e:
    print(f"Otro error inesperado al verificar el módulo: {e}")
print("-" * 40)