import os
import json
import platform
import psutil
import cv2
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QCheckBox, QPushButton
from PyQt6.QtCore import Qt

# Ruta del archivo de configuración (se guarda en el mismo directorio)
CONFIG_PATH = "config.json"


# ============================================================
# 🔹 FUNCIÓN: obtener_resolucion_real
# ------------------------------------------------------------
# Detecta automáticamente la resolución real soportada por la cámara.
# Prueba varias resoluciones comunes y devuelve la más alta estable.
# ============================================================
def obtener_resolucion_real(cam_index=0):
    cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)  # Abre la cámara (en Windows usa DirectShow)
    if not cap.isOpened():
        # Si no se logra abrir, se devuelve una resolución por defecto
        return (640, 480)

    # Lista de resoluciones típicas (de mayor a menor calidad)
    resoluciones_comunes = [
        (3840, 2160),  # 4K
        (2560, 1440),  # 2K
        (1920, 1080),  # Full HD
        (1280, 720),   # HD
        (1024, 576),
        (800, 600),
        (640, 480)
    ]

    max_res = (640, 480)  # Resolución mínima garantizada
    for w, h in resoluciones_comunes:
        # Intenta configurar la cámara con esa resolución
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        # Obtiene la resolución real establecida por la cámara
        real_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        real_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Guarda la mayor resolución alcanzada correctamente
        if real_w >= max_res[0] and real_h >= max_res[1]:
            max_res = (real_w, real_h)

    cap.release()  # Libera la cámara
    return max_res



# ============================================================
# 🔹 FUNCIÓN: obtener_info_hardware
# ------------------------------------------------------------
# Obtiene información general del sistema:
# - CPU, núcleos, RAM, cámara y resolución.
# Además, estima la capacidad de detección facial simultánea.
# ============================================================
def obtener_info_hardware():
    """Obtiene la información del hardware y estima la capacidad de detección facial."""

    # --- Obtener resolución de cámara ---
    try:
        width, height = obtener_resolucion_real()
    except Exception:
        # Si falla (no hay cámara o error), se usa una resolución base
        width, height = (640, 480)

    # --- Información de hardware del sistema ---
    ram_gb = psutil.virtual_memory().total / (1024 ** 3)  # Convierte bytes a GB
    cpu_cores = psutil.cpu_count(logical=True)             # Núcleos lógicos
    cpu_name = platform.processor()                        # Nombre del procesador

    # Diccionario con resoluciones de referencia
    resoluciones = {
        (1280, 720): "720p",
        (1920, 1080): "1080p",
        (640, 480): "480p",
        (3840, 2160): "4K"
    }

    # Texto con la resolución actual
    res_text = f"{int(width)}x{int(height)}"
    res_categoria = "Desconocida"

    # --- Determinar la categoría más cercana ---
    min_diff = float("inf")
    for (w, h), nombre in resoluciones.items():
        diff = abs(width - w) + abs(height - h)
        if diff < min_diff:
            min_diff = diff
            res_categoria = nombre

    # --- Estimar capacidad facial según resolución ---
    if res_categoria == "480p":
        max_por_res = 2
    elif res_categoria == "720p":
        max_por_res = 3
    elif res_categoria == "1080p":
        max_por_res = 5
    elif res_categoria == "4K":
        max_por_res = 8
    else:
        max_por_res = 2

    # --- Ajuste según potencia del hardware ---
    if ram_gb >= 16 and cpu_cores >= 8:
        factor_hardware = 1.5
    elif ram_gb >= 8 and cpu_cores >= 4:
        factor_hardware = 1.2
    elif ram_gb >= 4:
        factor_hardware = 1.0
    else:
        factor_hardware = 0.7

    # --- Resultado final ---
    max_faces = int(max_por_res * factor_hardware)
    if max_faces < 1:
        max_faces = 1

    return {
        "cpu": cpu_name or "No detectado",
        "ram": round(ram_gb, 1),
        "cores": cpu_cores,
        "camera_res": res_text,
        "res_categoria": res_categoria,
        "max_faces": max_faces
    }



# ============================================================
# 🔹 FUNCIONES: guardar_config / cargar_config
# ------------------------------------------------------------
# Guardan y cargan el archivo config.json con la información
# de hardware o configuración del usuario.
# ============================================================
def guardar_config(data):
    """Guarda la configuración actual en config.json."""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def cargar_config():
    """Carga la configuración guardada si existe."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)



# ============================================================
# 🔹 FUNCIÓN: hardware_cambiado
# ------------------------------------------------------------
# Compara los campos principales del hardware actual con los
# previamente guardados para detectar cambios significativos.
# ============================================================
def hardware_cambiado(previo, actual):
    """Compara campos clave del hardware para detectar cambios reales."""
    claves = ["cpu", "cores", "ram", "camera_res"]
    for clave in claves:
        if previo.get(clave) != actual.get(clave):
            return True
    return False



# ============================================================
# 🔹 CLASE: HardwareDialog
# ------------------------------------------------------------
# Ventana QDialog (PyQt6) que muestra la información detectada
# del hardware y la capacidad estimada de reconocimiento facial.
# ============================================================
class HardwareDialog(QDialog):
    """Ventana informativa sobre hardware y capacidad facial."""

    def __init__(self, hardware_info):
        super().__init__()
        self.setWindowTitle("Chequeo de hardware")

        # Estilo visual (fondo oscuro y acentos azules)
        self.setStyleSheet("""
            QDialog {
                background-color: #0D1B2A;
                color: white;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel {
                color: #E3F2FD;
            }
            QPushButton {
                background-color: #1565C0;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                color: white;
            }
            QPushButton:hover {
                opacity: 0.8;
            }
            QCheckBox {
                color: #E3F2FD;
            }
        """)

        # Crear el diseño vertical principal
        layout = QVBoxLayout()

        # Mostrar la información obtenida del hardware
        layout.addWidget(QLabel("🔍 Análisis del sistema detectado:"))
        layout.addWidget(QLabel(f"Procesador: {hardware_info['cpu']}"))
        layout.addWidget(QLabel(f"Núcleos: {hardware_info['cores']}"))
        layout.addWidget(QLabel(f"Memoria RAM: {hardware_info['ram']} GB"))
        layout.addWidget(QLabel(f"Cámara: {hardware_info['camera_res']} ({hardware_info['res_categoria']})"))
        layout.addSpacing(10)
        layout.addWidget(QLabel("Capacidad estimada de detección simultánea:"))
        layout.addWidget(QLabel(f"➡ {hardware_info['max_faces']} rostros"))
        layout.addSpacing(15)

        # Checkbox para no volver a mostrar este diálogo
        self.chk_no_mostrar = QCheckBox("No volver a mostrar este mensaje")
        layout.addWidget(self.chk_no_mostrar)

        # Botón de aceptar
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(self.accept)  # Cierra el diálogo
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignCenter)

        # Asignar layout al diálogo
        self.setLayout(layout)

        # Tamaño fijo de la ventana
        self.setFixedSize(420, 340)



# ============================================================
# 🔹 FUNCIÓN: mostrar_chequeo_hardware
# ------------------------------------------------------------
# Controla cuándo se debe mostrar la ventana de chequeo:
# - Si es la primera vez.
# - Si hubo un cambio en el hardware.
# - Si el usuario no marcó "no volver a mostrar".
# ============================================================
def mostrar_chequeo_hardware():
    """Muestra el diálogo si es necesario o si cambió el hardware."""

    actual = obtener_info_hardware()  # Detectar hardware actual
    config = cargar_config()          # Cargar config.json

    # Primera vez o si cambió el hardware desde el último chequeo
    if "hardware" not in config or hardware_cambiado(config.get("hardware", {}), actual):
        dlg = HardwareDialog(actual)
        dlg.exec()  # Mostrar ventana de información
        config["hardware"] = actual
        config["mostrar_dialogo"] = not dlg.chk_no_mostrar.isChecked()
        guardar_config(config)
        return actual

    # Si el usuario no desactivó la visualización, mostrar nuevamente
    if config.get("mostrar_dialogo", True):
        dlg = HardwareDialog(actual)
        dlg.exec()
        config["mostrar_dialogo"] = not dlg.chk_no_mostrar.isChecked()
        guardar_config(config)

    return actual
