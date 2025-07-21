# services/quality_control_service.py

import json
import os
from datetime import datetime
import uuid

RUTA_CORRECCIONES = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'correcciones.json')

class QualityControlService:
    def __init__(self):
        # Asegurarse de que el archivo existe al inicializar
        if not os.path.exists(RUTA_CORRECCIONES):
            try:
                with open(RUTA_CORRECCIONES, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=4, ensure_ascii=False)
            except IOError as e:
                print(f"Error al crear correcciones.json: {e}")

    def guardar_reporte(self, email_profesor, pregunta_original_data, correccion_data):
        """
        Guarda un reporte de error enviado por un profesor en el archivo central.
        pregunta_original_data debe contener 'pregunta', 'respuesta_correcta_ia'
        correccion_data debe contener 'respuesta_profesor', 'justificacion'
        """
        try:
            if not os.path.exists(RUTA_CORRECCIONES):
                lista_reportes = []
            else:
                with open(RUTA_CORRECCIONES, 'r', encoding='utf-8') as f:
                    lista_reportes = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            lista_reportes = []

        nuevo_reporte = {
            "id_reporte": f"rep_{uuid.uuid4().hex[:8]}",
            "fecha": datetime.now().isoformat(),
            "email_profesor": email_profesor,
            "pregunta_original_data": pregunta_original_data, # Ahora guardamos el diccionario completo de la pregunta
            "correccion_profesor": correccion_data,
            "estado": "pendiente" # Puede ser 'pendiente', 'revisado', 'aplicado'
        }

        lista_reportes.insert(0, nuevo_reporte) # Añadir al principio

        try:
            with open(RUTA_CORRECCIONES, 'w', encoding='utf-8') as f:
                json.dump(lista_reportes, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error al guardar reporte en correcciones.json: {e}")
            return False

    def obtener_reportes(self):
        """Carga y retorna todos los reportes de correcciones."""
        try:
            with open(RUTA_CORRECCIONES, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def actualizar_estado_reporte(self, reporte_id, nuevo_estado):
        """Actualiza el estado de un reporte específico."""
        reportes = self.obtener_reportes()
        for reporte in reportes:
            if reporte.get('id_reporte') == reporte_id:
                reporte['estado'] = nuevo_estado
                self.guardar_reportes_raw(reportes) # Usar una función interna para guardar la lista completa
                return True
        return False

    def guardar_reportes_raw(self, reportes_list):
        """Función interna para guardar la lista de reportes directamente."""
        try:
            with open(RUTA_CORRECCIONES, 'w', encoding='utf-8') as f:
                json.dump(reportes_list, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error al guardar correcciones.json: {e}")
            return False