import os
import shutil
from typing import List, Dict, Union

def organizar_archivos_en_subcarpetas(ruta_carpeta: str, log_func, cantidad_archivos: int, update_callback=None, cancel_event=None):
    """
    Agrupa los archivos de una carpeta en subcarpetas numeradas (0001, 0002...)
    con un límite de 'cantidad_archivos' por carpeta.
    """
    
    if not os.path.isdir(ruta_carpeta):
        return {'error': 'La ruta proporcionada no es válida.'}
    
    try:
        cantidad = int(cantidad_archivos)
        if cantidad <= 0: raise ValueError
    except ValueError:
        return {'error': 'La cantidad debe ser un número entero mayor a 0.'}

    ignorar = ["funciones", "logs", "basura", "sin_edit", "fallos"]
    archivos = []
    
    try:
        for f in os.listdir(ruta_carpeta):
            full_path = os.path.join(ruta_carpeta, f)
            if os.path.isfile(full_path) and f not in ignorar:
                archivos.append(f)
    except Exception as e:
        return {'error': f'Error leyendo directorio: {e}'}

    if not archivos:
        if update_callback: update_callback(1, 1, "")
        return {'movidos': 0, 'creadas': 0}

    total_archivos = len(archivos)
    contador_archivos_carpeta = 0
    numero_carpeta = 1
    total_movidos = 0
    carpetas_creadas = 0
    
    nombre_carpeta = f"{numero_carpeta:04d}"
    ruta_subcarpeta = os.path.join(ruta_carpeta, nombre_carpeta)
    os.makedirs(ruta_subcarpeta, exist_ok=True)
    carpetas_creadas += 1
    
    for i, archivo in enumerate(archivos, 1):
        if cancel_event and cancel_event.is_set():
            return {}

        if contador_archivos_carpeta == cantidad:
            numero_carpeta += 1
            nombre_carpeta = f"{numero_carpeta:04d}"
            ruta_subcarpeta = os.path.join(ruta_carpeta, nombre_carpeta)
            os.makedirs(ruta_subcarpeta, exist_ok=True)
            carpetas_creadas += 1
            contador_archivos_carpeta = 0  

        ruta_origen = os.path.join(ruta_carpeta, archivo)
        ruta_destino = os.path.join(ruta_subcarpeta, archivo)
        
        try:
            if os.path.exists(ruta_destino):
                base, ext = os.path.splitext(archivo)
                ruta_destino = os.path.join(ruta_subcarpeta, f"{base}_dup{ext}")

            shutil.move(ruta_origen, ruta_destino)
            total_movidos += 1
            contador_archivos_carpeta += 1
        except Exception as e:
            log_func(f"Error moviendo {archivo} a {nombre_carpeta}: {e}", nivel="error")
            
        if update_callback: update_callback(i, total_archivos, archivo)

    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(1, 1, "")

    return {
        'archivos_movidos': total_movidos,
        'carpetas_creadas': carpetas_creadas,
        'ultimo_lote': nombre_carpeta
    }