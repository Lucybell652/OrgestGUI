import os
import sys
import logging
import time
from datetime import datetime, timedelta
import tkinter.messagebox as messagebox 

sys.path.append(os.path.join(os.path.dirname(__file__), 'funciones'))

from funciones.dependencias import chequear_e_instalar_todo 
from funciones.dependencias import verificar_ffmpeg 
from funciones.gui import OrgestApp 

DEPS_OK = False
FFMPEG_ENCONTRADO = False
CONTEO_INICIAL = 3 
SPLASH_TIMER_ID = None 

LOG_FILE = None
logger_instance = None

def limpiar_logs_antiguos():
    """Elimina los archivos de log que tengan más de 24 horas de antigüedad."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir): return
    
    fecha_limite = datetime.now() - timedelta(days=1)
    try:
        for archivo in os.listdir(log_dir):
            if archivo.startswith('orgest_') and archivo.endswith('.log'):
                ruta = os.path.join(log_dir, archivo)
                if datetime.fromtimestamp(os.path.getctime(ruta)) < fecha_limite:
                    os.remove(ruta)
    except Exception:
        pass

def configurar_logger(log_file):
    """
    Configura el manejador de logs para escribir en archivo.
    Establece el nivel base en WARNING para evitar saturación.
    """
    global logger_instance
    
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logger_instance = logging.getLogger('orgest')
    logger_instance.setLevel(logging.WARNING) 
    
    if not logger_instance.handlers:
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setLevel(logging.WARNING) 
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger_instance.addHandler(handler)
        
    return logger_instance

def manejar_log(mensaje, nivel="error", exc_info=False):
    """
    Wrapper central para logging. Inicializa el archivo de log solo si
    se recibe un mensaje de nivel WARNING o superior (Lazy Initialization).
    """
    global LOG_FILE, logger_instance
    
    if logger_instance is None and nivel in ["error", "critical", "warning"]:
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        LOG_FILE = os.path.join(log_dir, f'orgest_{timestamp}.log')
        limpiar_logs_antiguos()
        configurar_logger(LOG_FILE)

    if logger_instance:
        if nivel == "error":
            logger_instance.error(mensaje, exc_info=exc_info)
        elif nivel == "warning":
            logger_instance.warning(mensaje, exc_info=exc_info)
        elif nivel == "critical":
            logger_instance.critical(mensaje, exc_info=exc_info)
        elif nivel == "info":
            logger_instance.info(mensaje, exc_info=exc_info)
        elif nivel == "debug":
            logger_instance.debug(mensaje, exc_info=exc_info)

def contar_archivos_totales(ruta):
    """Cuenta recursivamente los archivos en una ruta, ignorando carpetas de sistema."""
    total = 0
    ignoradas = ["basura", "fallos", "sin_edit", "funciones", "logs"]
    try:
        for root, _, files in os.walk(ruta):
            if os.path.basename(root) not in ignoradas:
                total += len(files)
        return total
    except Exception:
        return 0

def iniciar_conteo_regresivo(label_contador, log_func, root_splash, tiempo_restante):
    """Actualiza la etiqueta del splash screen cada segundo hasta llegar a cero."""
    global SPLASH_TIMER_ID
    
    if not root_splash.winfo_exists():
        return
        
    if tiempo_restante > 0:
        label_contador.configure(text=f"Iniciando la aplicación en {tiempo_restante} segundos...")
        SPLASH_TIMER_ID = root_splash.after(1000, lambda: iniciar_conteo_regresivo(label_contador, log_func, root_splash, tiempo_restante - 1))
    else:
        label_contador.configure(text="Iniciando...", text_color="green")
        iniciar_gui(log_func, root_splash)

def iniciar_gui(log_func, root_splash):
    """Cierra el splash screen e instancia la aplicación principal."""
    global SPLASH_TIMER_ID
    
    try:
        if root_splash.winfo_exists():
            root_splash.destroy() 
        
        app = OrgestApp(log_func) 
        app.mainloop()
    except Exception as e:
        log_func(f"Error crítico iniciando la aplicación: {e}", nivel="critical", exc_info=True)
        messagebox.showerror("Error de Arranque", f"Fallo al iniciar la aplicación principal: {e}")
        sys.exit(1)

def mostrar_bienvenida_y_esperar(log_func):
    """
    Muestra una ventana de carga (Splash Screen) con el estado de las dependencias.
    Si faltan dependencias críticas, muestra error y sale.
    """
    global DEPS_OK, FFMPEG_ENCONTRADO

    try:
        import customtkinter
    except ImportError:
        log_func("Fallo al importar customtkinter. Saliendo.", nivel="critical") 
        print("ERROR CRÍTICO: La librería customtkinter no está disponible.")
        sys.exit(1)

    if DEPS_OK:
        python_status = "✅ Librerías OK."
    else:
        python_status = "❌ FALTAN librerías CRÍTICAS."

    if FFMPEG_ENCONTRADO:
        ffmpeg_status = "✅ FFmpeg disponible."
    else:
        ffmpeg_status = "⚠️ FFmpeg NO ENCONTRADO. Conversiones no funcionarán."
        
    if not DEPS_OK:
        error_msg = (
            f"ERROR CRÍTICO: Las dependencias de Python esenciales (customtkinter/Pillow) no pudieron ser instaladas.\n\n"
            f"Por favor, revisa el archivo de log para más detalles y asegúrate de que tienes conexión a internet y permisos de instalación.\n\n"
            f"{ffmpeg_status}"
        )
        messagebox.showerror("Fallo de Dependencias", error_msg)
        log_func("El usuario debe cerrar la ventana. Saliendo del programa.", nivel="critical")
        sys.exit(1)
        
    root_splash = customtkinter.CTk()
    root_splash.title("ORGEST: Inicializando")
    root_splash.geometry("450x220")
    root_splash.resizable(False, False)
    root_splash.attributes('-topmost', True) 
    
    screen_width = root_splash.winfo_screenwidth()
    screen_height = root_splash.winfo_screenheight()
    x = (screen_width - 450) // 2
    y = (screen_height - 220) // 2
    root_splash.geometry(f"450x220+{x}+{y}")
    
    customtkinter.CTkLabel(root_splash, 
                           text="ORGEST: Organizador de Archivos", 
                           font=("Arial", 20, "bold")).pack(pady=(30, 10))
    
    customtkinter.CTkLabel(root_splash, 
                           text=f"{python_status}", 
                           text_color="green", 
                           font=("Arial", 14)).pack()

    customtkinter.CTkLabel(root_splash, 
                           text=f"{ffmpeg_status}", 
                           text_color="green" if FFMPEG_ENCONTRADO else "orange", 
                           font=("Arial", 14)).pack(pady=(5, 20))
                           
    lbl_contador = customtkinter.CTkLabel(root_splash, 
                           text=f"Iniciando la aplicación en {CONTEO_INICIAL} segundos...", 
                           font=("Arial", 12, "italic"))
    lbl_contador.pack()
                           
    root_splash.after(100, lambda: iniciar_conteo_regresivo(lbl_contador, log_func, root_splash, CONTEO_INICIAL))
    root_splash.mainloop()

def main():
    """Punto de entrada: configura log, chequea dependencias y lanza la interfaz."""
    global DEPS_OK, FFMPEG_ENCONTRADO
    
    log_func = manejar_log 
    DEPS_OK = chequear_e_instalar_todo(log_func) 
    FFMPEG_ENCONTRADO = verificar_ffmpeg(log_func) 
    mostrar_bienvenida_y_esperar(log_func)

if __name__ == "__main__":
    main()