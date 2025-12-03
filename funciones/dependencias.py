import sys
import subprocess
import os
import shutil
import urllib.request
import zipfile
import io

# --- Dependencias de Python ---
PYTHON_PACKAGES = {
    "customtkinter": "customtkinter",
    "Pillow": "PIL" 
}

def instalar_python_dependencies(log_func):
    """Verifica e instala dependencias de Python faltantes usando pip."""
    log_func("Verificando e instalando dependencias de Python...", nivel="debug")
    
    for package_name, import_name in PYTHON_PACKAGES.items():
        try:
            __import__(import_name)
        except ImportError:
            log_func(f"Dependencia de Python faltante: {package_name}. Intentando instalar...", nivel="warning")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package_name],
                    capture_output=True, 
                    check=True,
                    text=True
                )
                log_func(f"Instalación de {package_name} exitosa.", nivel="debug")
            except subprocess.CalledProcessError as e:
                log_func(f"Fallo al instalar {package_name}: {e.stderr}", nivel="error")
                print(f"ERROR CRÍTICO: No se pudo instalar {package_name}. Revisa el log para detalles.")
                return False
            except Exception as e:
                log_func(f"Excepción inesperada al instalar {package_name}: {e}", nivel="error")
                print(f"ERROR CRÍTICO: No se pudo instalar {package_name}.")
                return False
    return True

def obtener_ruta_base_real():
    """Retorna la carpeta donde está el ejecutable (o el script main.py)."""
    if getattr(sys, 'frozen', False):
        # Si estamos ejecutando como .exe (PyInstaller)
        return os.path.dirname(sys.executable)
    else:
        # Si estamos ejecutando como script .py normal
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def obtener_ruta_local_ffmpeg():
    """Usa la ruta base real para localizar la carpeta ffmpeg."""
    base_dir = obtener_ruta_base_real()
    return os.path.join(base_dir, 'ffmpeg')

def verificar_ffmpeg(log_func):
    """
    Verifica si ffmpeg está instalado.
    Prioridad: 
    1. Ruta local del proyecto (portable).
    2. PATH del sistema.
    """
    local_ffmpeg_dir = obtener_ruta_local_ffmpeg()
    local_exe = os.path.join(local_ffmpeg_dir, 'bin', 'ffmpeg.exe')
    
    # 1. Verificar Localmente
    if os.path.exists(local_exe):
        try:
            subprocess.run([local_exe, '-version'], 
                           capture_output=True, 
                           check=True, 
                           text=True)
            log_func(f"FFmpeg verificado en ruta local: {local_exe}", nivel="debug")
            return True 
        except Exception as e:
            log_func(f"Fallo al ejecutar FFmpeg local: {e}", nivel="warning")
            
    # 2. Verificar en el Sistema (PATH)
    try:
        subprocess.run(['ffmpeg', '-version'], 
                       capture_output=True, 
                       check=True, 
                       text=True)
        log_func("FFmpeg verificado en el PATH del sistema.", nivel="debug")
        return True 
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass 
            
    log_func("FFmpeg no encontrado ni localmente ni en el sistema.", nivel="warning")
    return False

def descargar_e_instalar_ffmpeg_portable(log_func):
    """
    Descarga el build oficial de Gyan.dev, lo descomprime y lo organiza
    en la carpeta 'ffmpeg' de la raíz del proyecto.
    """
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    destino_dir = obtener_ruta_local_ffmpeg()
    
    log_func(f"Iniciando descarga de FFmpeg portable desde: {url}", nivel="info")
    print("\n⬇️ Descargando FFmpeg (esto puede tardar unos minutos)...")
    
    try:
        # 1. Descargar el ZIP en memoria
        with urllib.request.urlopen(url) as response:
            zip_content = response.read()
            
        log_func("Descarga completada. Descomprimiendo...", nivel="debug")
        print("📦 Descomprimiendo archivos...")

        # 2. Procesar el ZIP
        with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
            # Encontrar la carpeta interna que contiene el 'bin'
            # (El zip suele tener una carpeta tipo 'ffmpeg-6.0-essentials_build/bin')
            carpeta_raiz_zip = None
            for name in z.namelist():
                if name.endswith('bin/ffmpeg.exe'):
                    # Obtenemos la ruta raíz dentro del zip (ej: "ffmpeg-x.x/bin/ffmpeg.exe" -> "ffmpeg-x.x")
                    carpeta_raiz_zip = name.split('/bin/')[0]
                    break
            
            if not carpeta_raiz_zip:
                raise Exception("No se encontró la estructura 'bin/ffmpeg.exe' en el ZIP descargado.")

            # 3. Extraer y organizar
            temp_extract_path = os.path.join(destino_dir, "temp_extract")
            z.extractall(temp_extract_path)
            
            # Ruta donde se extrajo realmente
            extracted_root = os.path.join(temp_extract_path, carpeta_raiz_zip)
            
            # Mover el contenido de esa carpeta a nuestro destino final 'ffmpeg/'
            # Si la carpeta destino ya existe, hay que tener cuidado, shutil.move espera que no exista o manejarlo
            if os.path.exists(destino_dir):
                # Limpiamos si ya existía para evitar mezclas corruptas (excepto la temp)
                for item in os.listdir(destino_dir):
                    if item != "temp_extract":
                        path = os.path.join(destino_dir, item)
                        if os.path.isdir(path): shutil.rmtree(path)
                        else: os.remove(path)
            
            # Mover todo el contenido de la carpeta extraída a la raíz de 'ffmpeg'
            for item in os.listdir(extracted_root):
                shutil.move(os.path.join(extracted_root, item), destino_dir)
            
            # 4. Limpieza final
            shutil.rmtree(temp_extract_path)
            
        print("✅ FFmpeg instalado correctamente en la carpeta del programa.")
        log_func("Instalación portable de FFmpeg completada con éxito.", nivel="info")
        return True

    except Exception as e:
        log_func(f"Error crítico instalando FFmpeg: {e}", nivel="error")
        print(f"\n❌ Error al descargar/instalar FFmpeg: {e}")
        # Limpieza en caso de error
        if os.path.exists(destino_dir):
            shutil.rmtree(destino_dir, ignore_errors=True)
        return False

def chequear_e_instalar_todo(log_func):
    """Ejecuta todas las verificaciones necesarias para que el programa corra."""
    
    # 1. Instalar dependencias Python
    if not instalar_python_dependencies(log_func):
        print("\nEl programa no puede continuar sin las librerías de Python requeridas.")
        return False
        
    # 2. Verificar FFmpeg
    if not verificar_ffmpeg(log_func):
        # Si falla, intentamos descargarlo automáticamente
        if not descargar_e_instalar_ffmpeg_portable(log_func):
            print("\n⚠️ No se pudo instalar FFmpeg automáticamente.")
            print("Por favor, descarga FFmpeg manualmente y pon la carpeta 'bin' dentro de una carpeta 'ffmpeg' en la raíz.")
            # Permitimos continuar, aunque las funciones de video fallarán
    
    log_func("Todas las dependencias y herramientas han sido chequeadas.", nivel="debug")
    return True