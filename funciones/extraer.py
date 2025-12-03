import os
import shutil

def encontrar_archivos_a_extraer(ruta):
    """Obtiene lista de archivos anidados que no están en la raíz ni en carpetas ignoradas."""
    archivos_a_mover = []
    ignorar = ["funciones", "logs", "basura", "sin_edit", "fallos"]
    
    for root, _, files in os.walk(ruta, topdown=False):
        if root == ruta or os.path.basename(root) in ignorar: continue
        for f in files:
            archivos_a_mover.append(os.path.join(root, f))
    return archivos_a_mover

def extraer_archivos_raiz(ruta, log_func, modo_automatico=True, update_callback=None, cancel_event=None):
    """
    Mueve todos los archivos de subcarpetas a la raíz principal 
    y elimina las carpetas vacías resultantes.
    """
    extraidos = 0
    ignorar = ["funciones", "logs", "basura", "sin_edit", "fallos"]
    
    archivos_a_mover = encontrar_archivos_a_extraer(ruta)
    total_archivos = len(archivos_a_mover)
    archivos_procesados = 0
    
    for src in archivos_a_mover:
        if cancel_event and cancel_event.is_set():
            return {}
            
        root, f = os.path.split(src)
        dst = os.path.join(ruta, f)
        
        try:
            c = 1
            while os.path.exists(dst):
                n, e = os.path.splitext(f)
                dst = os.path.join(ruta, f"{n}_{c}{e}")
                c += 1
            
            shutil.move(src, dst)
            extraidos += 1
        except Exception as e:
            log_func(f"Error extrayendo {f}: {e}", nivel="error")

        archivos_procesados += 1
        if update_callback: update_callback(archivos_procesados, total_archivos, f)

    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(archivos_procesados, total_archivos, "Limpiando carpetas...")

    for root, dirs, _ in os.walk(ruta, topdown=False):
        if root == ruta or os.path.basename(root) in ignorar: continue
        try:
            if not os.listdir(root):
                os.rmdir(root)
        except Exception: pass
        
    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(1, 1, "")
        
    return {'archivos_extraidos': extraidos}