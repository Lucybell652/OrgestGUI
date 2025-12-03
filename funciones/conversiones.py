import os
import shutil
import subprocess
from funciones.dependencias import verificar_ffmpeg 

def encontrar_archivos_a_convertir(ruta, log_func):
    """
    Busca archivos .webp, .ts, .m4s. Prioriza la carpeta 'Sin procesar' 
    si existe; de lo contrario, busca en la ruta raíz.
    """
    targets = ['.webp', '.ts', '.m4s']
    archivos_targets = []
    
    ruta_a_procesar = os.path.join(ruta, "Sin procesar")
    
    if os.path.isdir(ruta_a_procesar):
        log_func("Buscando archivos a convertir en la subcarpeta 'Sin procesar'.", nivel="debug")
        ruta_busqueda = ruta_a_procesar
    else:
        log_func("Buscando archivos a convertir en la ruta principal seleccionada.", nivel="debug")
        ruta_busqueda = ruta
    
    for root, _, files in os.walk(ruta_busqueda):
        if "basura" in root: continue
            
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in targets:
                archivos_targets.append(os.path.join(root, f))
    return archivos_targets

def convertir_formatos_archivos(ruta, log_func, update_callback=None, cancel_event=None):
    """
    Convierte WebP a PNG y TS/M4S a MP4 usando FFmpeg.
    Verifica espacio en disco (>100MB) antes de iniciar.
    """
    try:
        libre = shutil.disk_usage(ruta).free / (1024**2)
        if libre < 100: return {'error': 'Espacio en disco insuficiente (<100MB)'}
    except Exception: 
        pass

    if not verificar_ffmpeg(log_func):
        return {'error': 'FFmpeg no encontrado. Instálalo para convertir videos/webp.'}

    basura = os.path.join(ruta, "basura")
    os.makedirs(basura, exist_ok=True)
    
    conv_count = 0
    
    archivos_targets = encontrar_archivos_a_convertir(ruta, log_func)
    total_archivos = len(archivos_targets)
    archivos_procesados = 0
    
    # --- CONFIGURACIÓN PARA OCULTAR CONSOLA EN WINDOWS ---
    startup_args = {}
    if os.name == 'nt':
        startup_args['creationflags'] = subprocess.CREATE_NO_WINDOW
    # -----------------------------------------------------
    
    for src in archivos_targets:
        # 1. Verificar si el usuario pulsó "Cancelar" en la GUI
        if cancel_event and cancel_event.is_set():
            return {}
            
        # 2. Desglosar la ruta del archivo
        root, f = os.path.split(src)             
        ext = os.path.splitext(f)[1].lower()     
        dst = None
        cmd = []
        
        # 3. Preparar el comando según el tipo de archivo
        if ext == '.webp':
            dst = src.rsplit('.', 1)[0] + '.png'
            cmd = ['ffmpeg', '-i', src, dst, '-y', '-loglevel', 'error']
            
        elif ext in ['.ts', '.m4s']:
            dst = src.rsplit('.', 1)[0] + '.mp4'
            cmd = ['ffmpeg', '-i', src, '-c', 'copy', dst, '-y', '-loglevel', 'error']
        
        # 4. Ejecutar la conversión si se generó un comando válido
        if cmd:
            try:
                # Ejecutamos el comando pasando los argumentos para ocultar la ventana
                res = subprocess.run(cmd, capture_output=True, **startup_args)
                
                if res.returncode == 0:
                    try:
                        shutil.move(src, os.path.join(basura, os.path.basename(src)))
                    except: pass
                    conv_count += 1
                else:
                    log_func(f"Error FFmpeg {f}: {res.stderr.decode()}", nivel="error")
            except Exception as e:
                log_func(f"Excepción convirtiendo {f}: {e}", nivel="error")

        # 5. Actualizar barra de progreso en la interfaz
        archivos_procesados += 1
        if update_callback: update_callback(archivos_procesados, total_archivos, f)

    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(1, 1, "")
        
    return {'convertidos': conv_count}