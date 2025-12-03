import os
import shutil
import hashlib

def calcular_hash_archivo(ruta_archivo, log_func):
    """Calcula el hash MD5 de un archivo leyendo por bloques."""
    hasher = hashlib.md5()
    try:
        if not os.path.exists(ruta_archivo) or os.path.getsize(ruta_archivo) == 0:
            return None
        with open(ruta_archivo, 'rb') as archivo:
            for bloque in iter(lambda: archivo.read(4096), b""):
                hasher.update(bloque)
        return hasher.hexdigest()
    except Exception as e:
        log_func(f"Error hash {ruta_archivo}: {e}", nivel="error")
        return None

def encontrar_archivos(ruta):
    """Encuentra recursivamente todos los archivos válidos a procesar."""
    archivos_validos = []
    ignorar = ["funciones", "logs"]
    for root, _, files in os.walk(ruta):
        if os.path.basename(root) in ignorar: continue
        for f in files:
            archivos_validos.append(os.path.join(root, f))
    return archivos_validos, len(archivos_validos)

def encontrar_duplicados(ruta, log_func, update_callback=None, cancel_event=None):
    """Genera una lista de rutas de archivos que tienen contenido idéntico (hash duplicado)."""
    archivos_validos, total_archivos = encontrar_archivos(ruta)
    
    hashes = {}
    duplicados = []
    
    archivos_procesados = 0
    
    for full_path in archivos_validos:
        if cancel_event and cancel_event.is_set():
            return []
            
        h = calcular_hash_archivo(full_path, log_func)
        
        if h:
            if h in hashes:
                duplicados.append(full_path)
            else:
                hashes[h] = full_path
        
        archivos_procesados += 1
        if update_callback:
            update_callback(archivos_procesados, total_archivos, os.path.basename(full_path))
            
    return duplicados

def eliminar_duplicados(ruta, log_func, modo_automatico=False, update_callback=None, cancel_event=None):
    """
    Identifica archivos duplicados y los mueve a una carpeta 'basura'.
    Renombra si hay colisiones de nombres en el destino.
    """
    dups = encontrar_duplicados(ruta, log_func, update_callback, cancel_event)
    
    if cancel_event and cancel_event.is_set():
        return {}
        
    movidos = 0
    
    if dups:
        basura = os.path.join(ruta, "basura")
        os.makedirs(basura, exist_ok=True)
        
        if update_callback:
            update_callback(0, 1, f"Duplicados encontrados: {len(dups)}. Moviendo a 'basura'...")
            
        total_dups = len(dups)
        dups_movidos = 0
        
        for d in dups:
            if cancel_event and cancel_event.is_set():
                return {}
                
            try:
                nombre = os.path.basename(d)
                dest = os.path.join(basura, nombre)
                c = 1
                while os.path.exists(dest):
                    n, e = os.path.splitext(nombre)
                    dest = os.path.join(basura, f"{n}_{c}{e}")
                    c += 1
                shutil.move(d, dest)
                movidos += 1
            except Exception as e:
                log_func(f"Fallo moviendo duplicado {d}: {e}", nivel="error")
            
            dups_movidos += 1
            if total_dups > 0 and update_callback:
                update_callback(dups_movidos, total_dups, nombre) 
                
    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(1, 1, "")
                
    return {'duplicados_eliminados': movidos}

def verificar_duplicados(ruta, log_func, modo_automatico=False, update_callback=None, cancel_event=None):
    """Alias de compatibilidad para eliminar_duplicados."""
    return eliminar_duplicados(ruta, log_func, modo_automatico, update_callback, cancel_event)