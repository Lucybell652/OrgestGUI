import os
import shutil
import subprocess
from pathlib import Path
from funciones.dependencias import verificar_ffmpeg 

# Extensiones soportadas
EXT_IMAGENES = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
EXT_VIDEOS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}

def encontrar_archivos_media(ruta):
    """Encuentra recursivamente archivos de imagen y video válidos."""
    archivos_procesar = []
    
    for root, _, files in os.walk(ruta):
        # Ignoramos carpetas propias del programa para evitar bucles o errores
        if any(x in root for x in ["sin_edit", "fallos", "basura", "funciones", "logs"]): continue
            
        for f in files:
            ext = Path(f).suffix.lower()
            if ext in EXT_IMAGENES or ext in EXT_VIDEOS:
                archivos_procesar.append(os.path.join(root, f))
                
    return archivos_procesar

def procesar_video_ffmpeg(ruta_origen, log_func):
    """
    Re-codifica video a MP4 H.264.
    Usa parámetros específicos para balancear calidad y peso.
    """
    directorio, nombre_archivo = os.path.split(ruta_origen)
    nombre_base = os.path.splitext(nombre_archivo)[0]
    # Creamos un archivo temporal para no sobrescribir el original mientras se procesa
    ruta_temp = os.path.join(directorio, f"temp_{nombre_base}.mp4")
    
    cmd = [
        'ffmpeg', '-i', ruta_origen,
        '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        ruta_temp, '-y', '-loglevel', 'error'
    ]
    
    # --- CONFIGURACIÓN PARA OCULTAR CONSOLA EN WINDOWS ---
    startup_args = {}
    if os.name == 'nt':
        startup_args['creationflags'] = subprocess.CREATE_NO_WINDOW
    # -----------------------------------------------------

    # Pasamos startup_args a subprocess.run
    res = subprocess.run(cmd, capture_output=True, text=True, **startup_args)
    
    if res.returncode == 0:
        # Si la conversión fue exitosa:
        ruta_final = os.path.join(directorio, f"{nombre_base}.mp4")
        
        # Si el archivo original no era .mp4, lo borramos (ya tenemos la versión nueva)
        if ruta_origen != ruta_final:
            os.remove(ruta_origen)
            
        # Renombramos el temporal al nombre final
        shutil.move(ruta_temp, ruta_final)
        return True
    else:
        # Si falló, registramos el error y borramos el archivo temporal corrupto
        log_func(f"Error FFmpeg en {nombre_archivo}: {res.stderr}", nivel="error")
        if os.path.exists(ruta_temp):
            os.remove(ruta_temp)
        return False

def preprocesar_contenido(ruta, log_func, modo_automatico=True, update_callback=None, cancel_event=None):
    """
    Optimiza imágenes (usando Pillow) y videos (usando FFmpeg).
    Crea backups en 'sin_edit' antes de modificar cualquier archivo para seguridad.
    """
    # 1. Verificación de herramientas disponibles
    pillow_ok = True
    try:
        from PIL import Image, ImageOps
    except ImportError:
        pillow_ok = False
        log_func("Pillow no instalado. Se saltará el procesamiento de imágenes.", nivel="warning")

    ffmpeg_ok = verificar_ffmpeg(log_func)
    if not ffmpeg_ok:
        log_func("FFmpeg no encontrado. Se saltará el procesamiento de videos.", nivel="warning")

    if not pillow_ok and not ffmpeg_ok:
        return {'error': 'No hay herramientas disponibles (Faltan Pillow y FFmpeg)'}

    # 2. Preparar carpetas de seguridad
    sin_edit = os.path.join(ruta, "sin_edit")
    fallos = os.path.join(ruta, "fallos")
    os.makedirs(sin_edit, exist_ok=True)
    
    archivos = encontrar_archivos_media(ruta)
    total_archivos = len(archivos)
    procesados = 0
    archivos_procesados_count = 0
    
    for full_path in archivos:
        # Cancelación desde la GUI
        if cancel_event and cancel_event.is_set():
            return {}
            
        root, f = os.path.split(full_path)
        ext = Path(f).suffix.lower()
        es_video = ext in EXT_VIDEOS
        es_imagen = ext in EXT_IMAGENES
        
        # Saltamos si falta la herramienta específica para ese archivo
        if es_video and not ffmpeg_ok:
            archivos_procesados_count += 1
            continue
        if es_imagen and not pillow_ok:
            archivos_procesados_count += 1
            continue
            
        try:
            # 3. BACKUP DE SEGURIDAD (Crítico)
            # Antes de modificar, guardamos una copia idéntica en 'sin_edit'
            backup = os.path.join(sin_edit, f)
            c = 1
            # Evitamos sobrescribir backups existentes
            while os.path.exists(backup):
                n, e = os.path.splitext(f)
                backup = os.path.join(sin_edit, f"{n}_{c}{e}")
                c += 1
            shutil.copy2(full_path, backup)
            
            exito = False
            
            # 4. Procesamiento según tipo
            if es_imagen:
                with Image.open(full_path) as img:
                    # Convertir a RGB:
                    if img.mode in ('RGBA', 'P', 'LA', 'CMYK'):
                        img = img.convert('RGB')
                    
                    # Redimensionar solo si es excesivamente grande (>5000px)
                    if max(img.size) > 5000:
                        img.thumbnail((5000, 5000), Image.LANCZOS)
                        
                    # Guardar con optimización activada (elimina metadatos innecesarios)
                    img.save(full_path, quality=85, optimize=True)
                    exito = True
                    
            elif es_video:
                # Delegamos la tarea compleja a la función de FFmpeg
                exito = procesar_video_ffmpeg(full_path, log_func)

            if exito:
                procesados += 1
                
        except Exception as e:
            # Si algo falla, registramos el error y movemos el archivo problemático a 'fallos'
            log_func(f"Error procesando {f}: {e}", nivel="error")
            os.makedirs(fallos, exist_ok=True)
            try: shutil.move(full_path, os.path.join(fallos, f))
            except: pass

        # 5. Actualizar GUI
        archivos_procesados_count += 1
        if update_callback: update_callback(archivos_procesados_count, total_archivos, f)

    if update_callback and not (cancel_event and cancel_event.is_set()):
        update_callback(1, 1, "")
        
    return {'archivos_optimizados': procesados}