# 📂 ORGEST v2.0 - Organizador Inteligente de Archivos

¡Bienvenido a Orgest! Una aplicación de escritorio moderna construida en Python para automatizar la limpieza, organización y optimización de tus archivos multimedia.

![Estado](https://img.shields.io/badge/Estado-En%20Mejoras-orange)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)

## 🚀 Características Principales

* **Organización Automática:** Clasifica archivos en carpetas (Imágenes, Videos, Documentos, Audio, Rars) con un solo clic.
* **Gestión de Duplicados:** Detecta archivos idénticos (por hash MD5) y los mueve a la papelera.
* **Conversión Multimedia (FFmpeg):**
    * Convierte videos `.ts` y `.m4s` a `.mp4` sin pérdida de calidad.
    * Convierte imágenes `.webp` a `.png`.
* **Optimización de Medios:** Comprime imágenes grandes y recodifica videos a H.264 para ahorrar espacio.
* **Limpieza Profunda:** Extrae archivos de subcarpetas vacías y elimina residuos temporales.
* **100% Portable:** Si no tienes FFmpeg instalado, el programa lo descarga y configura automáticamente en la primera ejecución.

## 📥 Descarga (Para Usuarios)

Puedes descargar la última versión lista para usar (no requiere instalar Python):

👉 **Descargar [Orgest](https://github.com/Lucybell652/OrgestGUI/releases)**

## 🛠️ Instalación (Para Desarrolladores)

Si deseas modificar el código fuente:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/Lucybell652/OrgestGUI.git](https://github.com/Lucybell652/OrgestGUI.git)
    cd Orgest
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Ejecutar:**
    ```bash
    python main.py
    ```

## 📝 Licencia

Este proyecto es de uso libre. Sería un honor que lo uses y mejor aún que puedas mejorarlo.
