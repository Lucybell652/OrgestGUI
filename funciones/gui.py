import customtkinter
from tkinter import filedialog, messagebox
import os
import sys
import threading
import logging

# Importar funciones lógicas
from funciones.duplicados import eliminar_duplicados, verificar_duplicados
from funciones.ordenar import organizar_archivos_carpetas
from funciones.conversiones import convertir_formatos_archivos
from funciones.extraer import extraer_archivos_raiz
from funciones.preprocesador import preprocesar_contenido
from funciones.limpieza_final import limpiar_carpetas_temporales
from funciones.dividir import organizar_archivos_en_subcarpetas 

# ==========================================================================
# SECCIÓN: VENTANAS AUXILIARES / DIÁLOGOS
# ==========================================================================

class InputCentrado(customtkinter.CTkToplevel):
    """Ventana modal personalizada para solicitar datos al usuario (input)."""
    def __init__(self, text="Escribe algo...", title="Entrada"):
        super().__init__()
        
        self.title(title)
        self.user_input = None
        
        # Configuración de geometría (centrado)
        width = 300
        height = 160
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)
        
        # Hacerla modal (siempre encima)
        self.attributes("-topmost", True)
        self.grab_set() 
        
        # Layout Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=0)
        
        # Widgets de la ventana
        self.label = customtkinter.CTkLabel(self, text=text, font=("Arial", 13))
        self.label.grid(row=0, column=0, padx=20, pady=(15, 5))
        
        self.entry = customtkinter.CTkEntry(self, width=200)
        self.entry.grid(row=1, column=0, padx=20, pady=(5, 15))
        self.entry.bind("<Return>", self.on_ok) 
        
        self.btn_ok = customtkinter.CTkButton(self, text="Aceptar", width=100, command=self.on_ok)
        self.btn_ok.grid(row=2, column=0, padx=20, pady=(0, 20))
        
        self.cargar_icono()
        self.after(100, self.entry.focus_force)

    def cargar_icono(self):
        """Intenta cargar el ícono de la aplicación (compatible con .exe y script)."""
        try:
            if getattr(sys, 'frozen', False):
                # Si es un ejecutable (PyInstaller)
                base_dir = os.path.dirname(sys.executable)
            else:
                # Si es un script .py normal
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            icon_path = os.path.join(base_dir, "icono.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

    def on_ok(self, event=None):
        self.user_input = self.entry.get()
        self.destroy()

    def get_input(self):
        """Bloquea la ejecución hasta que se cierra la ventana y retorna el valor ingresado."""
        self.wait_window(self)
        return self.user_input

# ==========================================================================
# SECCIÓN: CLASE PRINCIPAL DE LA APP
# ==========================================================================

class OrgestApp(customtkinter.CTk):
    """Clase principal de la interfaz gráfica (GUI) de Orgest."""
    def __init__(self, log_func):
        super().__init__()
        self.log_func = log_func 
        
        # --- Variables de Estado ---
        self.ruta_actual = "" 
        self.proceso_pendiente = None      
        self.args_pendientes = []          
        self.nombre_proceso_actual = ""    
        self.total_pasos_auto = 6 
        self.paso_auto_actual = 0 
        
        self.cancel_event = threading.Event()
        self.proceso_activo = False
        
        # --- Configuración de Ventana Principal ---
        app_width = 490
        app_height = 760 
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - app_width) // 2
        y = (screen_height - app_height) // 2
        
        self.geometry(f"{app_width}x{app_height}+{x}+{y}")
        self.resizable(False, False)
        self.title("Organizador de Archivos")
        
        self.cargar_icono()
        
        customtkinter.set_appearance_mode("System")
        customtkinter.set_default_color_theme("blue")
        
        # Grid Principal
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 
        self.grid_rowconfigure(2, weight=0) 
        self.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()
        
    def cargar_icono(self):
        try:
            # Lógica para detectar si es .exe o script
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                
            icon_path = os.path.join(base_dir, "icono.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                self.log_func(f"Archivo de ícono no encontrado: {icon_path}", nivel="warning")
        except Exception as e:
            self.log_func(f"Fallo al cargar el ícono: {e}", nivel="error")

    # ==========================================================================
    # SECCIÓN: DISEÑO Y WIDGETS
    # ==========================================================================

    def create_widgets(self):
        """Inicializa y organiza los componentes visuales: Header, Tabs y Footer."""
        # 1. Header
        self.header = customtkinter.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15,5))
        
        title_container = customtkinter.CTkFrame(self.header, fg_color="transparent")
        title_container.pack() 
        
        customtkinter.CTkLabel(title_container, text="ORGEST", font=("Arial", 28, "bold")).pack(side="left")
        customtkinter.CTkLabel(title_container, text="v2.0", text_color="gray").pack(side="left", padx=(10, 0), anchor="s", pady=5)
        
        # 2. Tabs (Pestañas)
        self.main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        self.tabs = customtkinter.CTkTabview(self.main_frame)
        self.tabs.grid(row=0, column=0, sticky="nsew")
        self.tab_auto = self.tabs.add("Modo Automático")
        self.tab_manual = self.tabs.add("Modo Personalizado")
        
        self.setup_auto_tab()
        self.setup_manual_tab()

        # 3. Área Inferior
        self.setup_bottom_area()

    def setup_bottom_area(self):
        """Configura el área inferior con barra de progreso, selección de ruta y botón de acción."""
        self.bottom_area = customtkinter.CTkFrame(self, fg_color="transparent")
        self.bottom_area.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        self.action_frame = customtkinter.CTkFrame(self.bottom_area, fg_color=("gray85", "gray20"), corner_radius=10)
        self.action_frame.pack(fill="x", pady=5)
        
        self.lbl_process_name = customtkinter.CTkLabel(self.action_frame, 
                                                     text="Configuración: Pendiente a elección", 
                                                     font=("Arial", 14, "bold"), 
                                                     text_color="gray")
        self.lbl_process_name.pack(pady=(15, 5))
        
        self.lbl_status = customtkinter.CTkLabel(self.action_frame, 
                                                text="", 
                                                font=("Arial", 11), 
                                                text_color="gray",
                                                anchor="w")
        
        self.progress_bar = customtkinter.CTkProgressBar(self.action_frame, 
                                                         orientation="horizontal", 
                                                         mode="determinate")
        self.progress_bar.set(0)
        
        path_frame = customtkinter.CTkFrame(self.action_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=20, pady=10)
        
        self.btn_select_path = customtkinter.CTkButton(path_frame, 
                                                     text="Seleccionar Carpeta", 
                                                     command=self.select_path_dialog, 
                                                     width=140,
                                                     state="disabled") 
        self.btn_select_path.pack(side="left")
        
        self.path_lbl = customtkinter.CTkLabel(path_frame, 
                                             text="Ninguna ruta seleccionada", 
                                             anchor="w", 
                                             text_color="gray")
        self.path_lbl.pack(side="left", padx=15, fill="x", expand=True)
        
        self.btn_confirm = customtkinter.CTkButton(self.action_frame, 
                                                 text="CONFIRMAR E INICIAR", 
                                                 height=50, 
                                                 font=("Arial", 15, "bold"), 
                                                 fg_color="gray", 
                                                 state="disabled", 
                                                 command=self.handle_action_button) 
        self.btn_confirm.pack(fill="x", padx=20, pady=(5, 20))

    # ==========================================================================
    # SECCIÓN: LÓGICA DE BOTONES Y ESTADO
    # ==========================================================================

    def handle_action_button(self):
        """Gestiona el clic en el botón principal: inicia el proceso o solicita cancelación."""
        if self.proceso_activo:
            self.confirmar_y_cancelar()
        else:
            self.confirmar_e_iniciar()
    
    def confirmar_y_cancelar(self):
        if messagebox.askyesno("Confirmar Cancelación", 
                               "¿Estás seguro de que quieres CANCELAR el proceso?\n\nLa carpeta podría quedar en un estado inconsistente."):
            self.iniciar_cancelacion()

    def iniciar_cancelacion(self):
        """Activa el evento de threading para detener las tareas en ejecución."""
        self.cancel_event.set()
        self.log_func(f"Proceso '{self.nombre_proceso_actual}' cancelado por el usuario.", nivel="warning")
        self.lbl_status.configure(text="CANCELANDO... Esperando finalización del paso actual.", text_color="red")
        self.btn_confirm.configure(state="disabled", fg_color="gray")

    def preparar_ejecucion(self, nombre_proceso, funcion, *args):
        """
        Prepara el estado de la UI para una nueva ejecución:
        limpia flags, resetea barras y habilita el botón de selección de ruta.
        """
        self.nombre_proceso_actual = nombre_proceso
        self.proceso_pendiente = funcion
        self.args_pendientes = args
        self.paso_auto_actual = 0 
        self.cancel_event.clear()
        
        self.lbl_process_name.configure(text=f"Configuración: {self.nombre_proceso_actual}", 
                                      text_color=("black", "white"))
        self.lbl_status.configure(text="")
        self.progress_bar.set(0)
        
        self.btn_select_path.configure(state="normal")
        self.proceso_activo = False
        self.btn_confirm.configure(state="normal", 
                                 text="CONFIRMAR E INICIAR",
                                 fg_color="#2CC985", 
                                 hover_color="#229965")

    def toggle_inputs(self, state):
        """Habilita o deshabilita los controles de la interfaz."""
        st = "normal" if state else "disabled"
        self.btn_auto.configure(state=st)
        for b in self.manual_btns: b.configure(state=st)
        self.btn_select_path.configure(state=st)
        
        if state: 
            self.configure(cursor="")
            self.lbl_status.configure(text="")
            self.proceso_activo = False
            self.progress_bar.pack_forget()
            self.lbl_status.pack_forget()
            self.reset_ui_to_initial_state() 
        else: 
            self.configure(cursor="watch")

    def reset_ui_to_initial_state(self):
        """Restaura los botones y etiquetas a su estado inicial tras un proceso."""
        self.proceso_pendiente = None      
        self.args_pendientes = []
        self.nombre_proceso_actual = ""
        
        self.btn_confirm.configure(state="disabled", 
                                 text="CONFIRMAR E INICIAR",
                                 fg_color="gray", 
                                 hover_color="gray")
        
        self.lbl_process_name.configure(text="Configuración: Pendiente a elección", 
                                       text_color="gray")

    # ==========================================================================
    # SECCIÓN: SELECTOR DE ARCHIVOS
    # ==========================================================================

    def select_path_dialog(self):
        p = filedialog.askdirectory()
        if p:
            self.ruta_actual = p
            self.update_path_label()

    def update_path_label(self):
        """Actualiza la etiqueta de la ruta, truncando el texto si es muy largo."""
        txt = self.ruta_actual
        if not txt:
            self.path_lbl.configure(text="Ninguna ruta seleccionada", text_color="gray")
        else:
            if len(txt) > 30: txt = "..." + txt[-27:]
            self.path_lbl.configure(text=f"Ruta: {txt}", text_color=("black", "white"))

    # ==========================================================================
    # SECCIÓN: FEEDBACK Y PROGRESO
    # ==========================================================================

    def update_progress(self, current, total, file_info=""): 
        """Callback thread-safe para actualizar la barra de progreso desde los hilos de trabajo."""
        if self.cancel_event.is_set():
            return
        if total == 0:
            value = 0
        else:
            value = current / total
        self.after(0, lambda: self._set_progress(value, current, total, file_info))

    def _set_progress(self, value, current, total, file_info=""): 
        """
        Actualiza visualmente la barra y la etiqueta de estado.
        Maneja la visualización de nombres de archivo truncados.
        """
        progreso_actual = f"Archivos: {current}/{total}" if total > 0 else "Calculando..."
        
        file_display = ""
        if file_info:
            MAX_LEN = 30 
            
            if file_info.startswith("Duplicados encontrados:") or file_info.startswith("Limpiando carpetas..."):
                file_display = file_info
            elif file_info:
                if len(file_info) > MAX_LEN:
                    file_display = f"{file_info[:MAX_LEN-3]}..."
                else:
                    file_display = file_info
            
            if file_display:
                progreso_actual = f"{file_display} | {progreso_actual}"

        if self.nombre_proceso_actual == "Modo Automático":
            paso_nombre = self.get_paso_nombre(self.paso_auto_actual)
            base_paso = (self.paso_auto_actual - 1) / self.total_pasos_auto
            progreso_paso = value / self.total_pasos_auto
            progreso_global = base_paso + progreso_paso
            
            self.lbl_process_name.configure(text=f"Configuración: Auto - Paso {self.paso_auto_actual}/6 ({paso_nombre})")
            self.lbl_status.configure(text=f"Progreso global: {int(progreso_global*100)}% | {progreso_actual}") 
            self.progress_bar.set(progreso_global)
        else:
            self.lbl_status.configure(text=progreso_actual) 
            self.progress_bar.set(value)
            
    def get_paso_nombre(self, num_paso):
        """Retorna el nombre descriptivo del paso actual en el modo automático."""
        pasos_nombres = [
            "Eliminar Duplicados",
            "Organizar Archivos",
            "Convertir Formatos",
            "Extraer Archivos a Raíz",
            "Pre-procesar Imágenes",
            "Limpieza Final"
        ]
        if 1 <= num_paso <= len(pasos_nombres):
            return pasos_nombres[num_paso - 1]
        return f"Paso {num_paso}"

    # ==========================================================================
    # SECCIÓN: VALIDACIÓN Y ARRANQUE
    # ==========================================================================

    def confirmar_e_iniciar(self, *args): 
        """
        Valida rutas e inicia el proceso.
        Si la tarea requiere input extra (como 'Dividir'), lanza el diálogo modal antes.
        """
        if not self.ruta_actual:
            messagebox.showwarning("Falta Ruta", "Por favor selecciona una carpeta antes de continuar.")
            return
        
        if not os.path.isdir(self.ruta_actual):
            messagebox.showerror("Error", "La ruta seleccionada no es válida.")
            return

        if self.proceso_pendiente == organizar_archivos_en_subcarpetas:
            dialog = InputCentrado(
                text="Cantidad de archivos por subcarpeta?", 
                title="Configuración"
            )
            entrada = dialog.get_input()
            
            if not entrada:
                return 

            try:
                cantidad = int(entrada)
                if cantidad <= 0:
                    messagebox.showerror("Error", "El número debe ser mayor a 0.")
                    return
                self.args_pendientes = [cantidad]
                self.lbl_process_name.configure(text=f"Configuración: Dividir en lotes de {cantidad}")
                
            except ValueError:
                messagebox.showerror("Error", "Por favor ingresa un número entero válido.")
                return

        mensaje = f"Vas a ejecutar: {self.nombre_proceso_actual}\n\nEn la carpeta:\n{self.ruta_actual}\n\n¿Estás seguro de continuar?"
        
        if self.proceso_pendiente == organizar_archivos_en_subcarpetas:
             mensaje = f"Vas a dividir los archivos en carpetas de {self.args_pendientes[0]} elementos.\n\nEn la ruta:\n{self.ruta_actual}\n\n¿Estás seguro?"

        if messagebox.askyesno("Confirmar Ejecución", mensaje):
            self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
            self.lbl_status.pack(fill="x", padx=20, pady=(5, 0))
            
            self.proceso_activo = True
            self.btn_confirm.configure(text="CANCELAR PROCESO", 
                                     fg_color="red", 
                                     hover_color="#CC0000")
            
            self.iniciar_hilo_proceso()

    # ==========================================================================
    # SECCIÓN: HILOS Y EJECUCIÓN (THREADING)
    # ==========================================================================

    def iniciar_hilo_proceso(self):
        """Bloquea la UI e inicia el proceso en un hilo separado para no congelar la ventana."""
        self.toggle_inputs(False)
        self.lbl_status.configure(text="Iniciando proceso...")
        threading.Thread(target=self.task_wrapper).start()

    def task_wrapper(self):
        """
        Envoltura que se ejecuta en el hilo secundario. 
        Maneja excepciones, inyección de dependencias y resultados finales.
        """
        try:
            func = self.proceso_pendiente
            args = [self.log_func] + list(self.args_pendientes) + [self.update_progress, self.cancel_event] 
            
            if self.nombre_proceso_actual == "Modo Automático":
                self.after(0, lambda: self._set_progress(0, 0, 1, ""))
            
            res = func(self.ruta_actual, *args)
            
            if self.cancel_event.is_set():
                self.after(0, lambda: messagebox.showwarning("Cancelado", "Proceso cancelado por el usuario."))
            elif isinstance(res, dict) and res.get('error'):
                error_msg = res['error']
                self.log_func(f"Error en tarea: {error_msg}", nivel="error")
                self.after(0, lambda: messagebox.showerror("Fallo del Proceso", f"Fallo: {error_msg}"))
            else:
                self.log_func(f"Tarea completada: {self.nombre_proceso_actual}", nivel="debug") 
                self.after(0, lambda: self._set_progress(1, 1, 1, ""))
                self.after(0, lambda: messagebox.showinfo("Éxito", "Proceso finalizado correctamente."))
                
        except Exception as e:
            self.log_func(f"Excepción CRÍTICA: {e}", nivel="critical", exc_info=True)
            if not self.cancel_event.is_set():
                self.after(0, lambda error=e: messagebox.showerror("Error Crítico del Sistema", str(error)))
        finally:
            self.after(0, lambda: self.toggle_inputs(True))

    # ==========================================================================
    # SECCIÓN: MODO AUTOMÁTICO
    # ==========================================================================

    def run_auto_process(self, ruta, log_func, ejecutar_preprocess, update_callback, cancel_event):
        """
        Orquesta la ejecución secuencial de todas las herramientas de limpieza.
        Maneja el checkbox de preprocesamiento y el flujo de pasos.
        """
        pasos = [
            (eliminar_duplicados, [True]),
            (organizar_archivos_carpetas, []),
            (convertir_formatos_archivos, []),
            (extraer_archivos_raiz, [True]),
            (preprocesar_contenido, [True]), 
            (limpiar_carpetas_temporales, [])
        ]
        
        if not ejecutar_preprocess:
            pasos.pop(4) 
            
        self.total_pasos_auto = len(pasos)
        
        for i, (func, args) in enumerate(pasos, 1):
            if cancel_event.is_set():
                return {} 

            self.paso_auto_actual = i
            args_con_callback = [log_func] + args + [update_callback, cancel_event]
            res = func(ruta, *args_con_callback)
            
            if isinstance(res, dict) and res.get('error'):
                paso_nombre = self.get_paso_nombre(i) 
                res['error'] = f"Error en el paso {i}: {res['error']}" 
                return res
                
        self.paso_auto_actual = self.total_pasos_auto
        update_callback(1, 1, "")
        return {}

    def setup_auto_tab(self):
        """Configura la pestaña de 'Modo Automático'."""
        t = self.tab_auto
        t.grid_columnconfigure(0, weight=1)
        t.grid_rowconfigure(1, weight=1)
        t.grid_rowconfigure(2, weight=0) 
        t.grid_rowconfigure(3, weight=0)
        
        customtkinter.CTkLabel(t, text="Secuencia de Limpieza Completa", font=("Arial", 16, "bold")).grid(row=0, pady=(10, 5))
        
        scroll_frame = customtkinter.CTkScrollableFrame(t)
        scroll_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        scroll_frame.grid_columnconfigure(0, weight=1)
        
        pasos_data = [
            ("1. Eliminar Duplicados", "Mueve copias idénticas (MD5) a 'basura'."),
            ("2. Organizar Archivos", "Clasifica en carpetas 'Imagenes', 'Videos', 'Documentos', 'Rars', 'Audio', 'Sin reconocer' y 'Sin procesar'."), 
            ("3. Convertir Formatos", "WebP → PNG, TS/M4S → MP4."),
            ("4. Extraer a Raíz", "Saca archivos de subcarpetas y elimina vacías."),
            ("5. Pre-procesamiento", "Optimiza Imágenes (RGB) y Comprime Videos (H.264)."),
            ("6. Verificación y Limpieza", "Elimina carpetas temporales y residuos ('basura', 'sin_edit', 'fallos').") 
        ]
        
        for i, (titulo, descripcion) in enumerate(pasos_data):
            step_box = customtkinter.CTkFrame(scroll_frame, corner_radius=6, fg_color=("gray85", "gray16"))
            step_box.pack(fill="x", pady=4, padx=5)
            
            customtkinter.CTkLabel(step_box, text=titulo, font=("Arial", 13, "bold"), anchor="w").pack(fill="x", padx=10, pady=(5,0))
            customtkinter.CTkLabel(step_box, text=descripcion, font=("Arial", 11), text_color="gray", anchor="w").pack(fill="x", padx=10, pady=(0,5))

        self.chk_preprocess = customtkinter.CTkCheckBox(t, text="Incluir Pre-procesamiento de Imágenes (Paso 5)")
        self.chk_preprocess.select() 
        self.chk_preprocess.grid(row=2, column=0, pady=(10, 5), padx=20, sticky="w")

        self.btn_auto = customtkinter.CTkButton(t, text="Continuar", height=45, font=("Arial", 14, "bold"), 
                                              command=lambda: self.preparar_ejecucion("Modo Automático", self.run_auto_process, self.chk_preprocess.get()))
        self.btn_auto.grid(row=3, column=0, pady=20, padx=20, sticky="ew")

    # ==========================================================================
    # SECCIÓN: MODO MANUAL / PERSONALIZADO
    # ==========================================================================

    def setup_manual_tab(self):
        """Configura la pestaña de 'Modo Personalizado'."""
        t = self.tab_manual
        t.grid_columnconfigure(0, weight=1)
        t.grid_rowconfigure(1, weight=1)
        
        customtkinter.CTkLabel(t, text="Herramientas Individuales", font=("Arial", 16, "bold")).grid(row=0, pady=(10, 5))
        
        sf = customtkinter.CTkScrollableFrame(t)
        sf.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        sf.grid_columnconfigure(0, weight=1)
        
        tools = [
            ("Eliminar Duplicados", "Busca y borra archivos idénticos.", eliminar_duplicados, True),
            ("Organizar Carpetas", "Separa Imagenes y Videos.", organizar_archivos_carpetas, False),
            ("Convertir Formatos", "WebP/TS/M4S a PNG/MP4.", convertir_formatos_archivos, False),
            ("Extraer Archivos", "Saca todo a la raíz.", extraer_archivos_raiz, True),
            ("Pre-procesar Multimedia", "Optimiza Img y Videos (H.264).", preprocesar_contenido, True),
            ("Limpieza Final", "Borra carpetas temporales.", limpiar_carpetas_temporales, False),
            ("Dividir por Carpetas", "Divide archivos en subcarpetas de N elementos.", organizar_archivos_en_subcarpetas, False) 
        ]
        
        self.manual_btns = []
        for i, (tit, desc, func, has_arg) in enumerate(tools):
            box = customtkinter.CTkFrame(sf, corner_radius=6, fg_color=("gray85", "gray16"))
            box.pack(fill="x", pady=5, padx=5)
            box.grid_columnconfigure(0, weight=1) 
            box.grid_columnconfigure(1, weight=0) 
            
            text_frame = customtkinter.CTkFrame(box, fg_color="transparent")
            text_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
            
            customtkinter.CTkLabel(text_frame, text=tit, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
            customtkinter.CTkLabel(text_frame, text=desc, font=("Arial", 11), text_color="gray", anchor="w").pack(fill="x")
            
            args = [True] if has_arg else []
            cmd = lambda n=tit, f=func, a=args: self.preparar_ejecucion(n, f, *a)
            
            b = customtkinter.CTkButton(box, text="Iniciar", width=100, height=30, command=cmd)
            b.grid(row=0, column=1, padx=15, pady=10) 
            self.manual_btns.append(b)