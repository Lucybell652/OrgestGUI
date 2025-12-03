import os
import shutil

def limpiar_carpetas_temporales(ruta, log_func, update_callback=None, cancel_event=None):
    """Elimina las carpetas temporales generadas ('basura', 'sin_edit', 'fallos')."""
    targets = ['basura', 'sin_edit', 'fallos']
    eliminadas = 0
    
    total_targets = len(targets)
    targets_procesados = 0
    
    for t in targets:
        if cancel_event and cancel_event.is_set():
            return {}
            
        p = os.path.join(ruta, t)
        if os.path.exists(p):
            try:
                shutil.rmtree(p)
                eliminadas += 1
            except Exception as e:
                log_func(f"No se pudo borrar {t}: {e}", nivel="error")
        
        targets_procesados += 1
        if update_callback: update_callback(targets_procesados, total_targets)

    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(1, 1)
        
    return {'carpetas_eliminadas': eliminadas}