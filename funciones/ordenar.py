import os
import shutil

def organizar_archivos_carpetas(ruta, log_func, update_callback=None, cancel_event=None):
    """
    Clasifica los archivos en carpetas según su extensión (Imagenes, Videos, Docs, etc).
    Crea las carpetas de destino dinámicamente si son necesarias.
    """
    dirs = {
        'Imagenes': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', ".avif"],
        'Videos': ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.mpeg', '.mpg'],
        'Documentos': ['.doc', '.docx', '.pdf', '.odt', '.txt', '.md', '.rtf', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
        'Rars': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso'],
        'Audio': ['.mp3', '.wav', '.flac', '.ogg', '.aac', '.wma', '.m4a'],
        'Sin reconocer': [],
        'Sin procesar': ['.webp', '.ts', '.m4s'] 
    }
    
    protegidos = ['funciones', 'logs', 'basura', 'fallos', 'sin_edit', 'Imagenes', 'Videos', 'Documentos', 'Rars', 'Audio', 'Sin reconocer', 'Sin procesar']
    
    archivos_a_recorrer = []
    categorias_necesarias = set()
    
    for root, _, files in os.walk(ruta):
        if os.path.basename(root) in protegidos: continue
        for f in files: 
            full_path = os.path.join(root, f)
            ext = os.path.splitext(f)[1].lower()
            
            tipo = 'Sin reconocer'
            if ext in dirs['Imagenes']: tipo = 'Imagenes'
            elif ext in dirs['Videos']: tipo = 'Videos'
            elif ext in dirs['Documentos']: tipo = 'Documentos'
            elif ext in dirs['Rars']: tipo = 'Rars'
            elif ext in dirs['Audio']: tipo = 'Audio'
            elif ext in dirs['Sin procesar']: tipo = 'Sin procesar' 
            
            if os.path.join(ruta, tipo) != root:
                archivos_a_recorrer.append(full_path)
                categorias_necesarias.add(tipo)
            
    total_archivos = len(archivos_a_recorrer)
    
    if total_archivos == 0:
        if update_callback and not (cancel_event and cancel_event.is_set()):
            update_callback(1, 1, "")
        return {
            'imagenes_movidas': 0, 'videos_movidos': 0, 'documentos_movidos': 0, 
            'rars_movidos': 0, 'audio_movidos': 0, 'no_reconocidos_movidos': 0,
            'sin_procesar_movidos': 0
        }

    paths_dest = {}
    for k in categorias_necesarias:
        paths_dest[k] = os.path.join(ruta, k)
        os.makedirs(paths_dest[k], exist_ok=True)
        
    counts = {
        'imagenes': 0, 'videos': 0, 'documentos': 0, 'rars': 0, 'audio': 0,
        'sin_reconocer': 0, 'sin_procesar': 0
    }
    
    archivos_procesados = 0
    
    for origen in archivos_a_recorrer:
        if cancel_event and cancel_event.is_set():
            return {}
            
        root, f = os.path.split(origen)
        ext = os.path.splitext(f)[1].lower()
        
        tipo = 'Sin reconocer' 
        if ext in dirs['Imagenes']: tipo = 'Imagenes'
        elif ext in dirs['Videos']: tipo = 'Videos'
        elif ext in dirs['Documentos']: tipo = 'Documentos'
        elif ext in dirs['Rars']: tipo = 'Rars'
        elif ext in dirs['Audio']: tipo = 'Audio'
        elif ext in dirs['Sin procesar']: tipo = 'Sin procesar' 
        
        if tipo in paths_dest: 
            destino_dir = paths_dest[tipo]
        else:
            archivos_procesados += 1
            if update_callback: update_callback(archivos_procesados, total_archivos, f)
            continue
            
        try:
            dest_final = os.path.join(destino_dir, f)
            c = 1
            while os.path.exists(dest_final):
                n, e = os.path.splitext(f)
                dest_final = os.path.join(destino_dir, f"{n}_{c}{e}")
                c += 1
            
            shutil.move(origen, dest_final)
            key_count = tipo.lower().replace(' ', '_')
            counts[key_count] += 1
        except Exception as e:
            log_func(f"Error moviendo {f}: {e}", nivel="error")
            
        archivos_procesados += 1
        if update_callback: update_callback(archivos_procesados, total_archivos, f)

    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(1, 1, "")
        
    return {
        'imagenes_movidas': counts['imagenes'], 
        'videos_movidos': counts['videos'],
        'documentos_movidos': counts['documentos'],
        'rars_movidos': counts['rars'],
        'audio_movidos': counts['audio'],
        'no_reconocidos_movidos': counts['sin_reconocer'],
        'sin_procesar_movidos': counts['sin_procesar']
    }