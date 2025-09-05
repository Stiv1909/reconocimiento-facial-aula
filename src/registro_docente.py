import sys
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QMessageBox
)
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer

# Importar función del backend para guardar en la BD
from modules.docentes import registrar_docente  


# ==========================================================
#   CLASE: RegistroDocente
#   Función: Permite registrar un docente en la BD
#            - Captura foto desde cámara
#            - Detecta rostro y lo guarda
#            - Almacena nombre, apellido y foto en BD
# ==========================================================
class RegistroDocente(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro Docente - Institución Educativa del Sur")
        self.resize(900, 600)
        self.centrar_ventana()   # 🔹 Centramos ventana al iniciar

        # --- Estado de cámara ---
        self.camara_activa = True      # Controla si la cámara está activa
        self.foto_capturada = None     # Guardará la foto tomada

        # --- Clasificador de rostros ---
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # --- Variables de cámara ---
        self.cap = cv2.VideoCapture(0)     # Abrir cámara
        self.timer = QTimer()              # Timer para refrescar la cámara
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)               # Cada 30ms refresca la vista

        self.init_ui()

    # ------------------------------------------------------
    # Método: centrar_ventana
    # Descripción: Posiciona la ventana en el centro de pantalla
    # ------------------------------------------------------
    def centrar_ventana(self):
        pantalla = QApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(pantalla.center())
        self.move(geo.topLeft())

    # ------------------------------------------------------
    # Método: init_ui
    # Descripción: Construye toda la interfaz gráfica
    # ------------------------------------------------------
    def init_ui(self):
        # --- Estilos globales (CSS) ---
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
                font-family: Arial;
                font-size: 14px;
            }
            QFrame {
                border: 2px solid #ddd;
                border-radius: 12px;
                background-color: white;
            }
            QPushButton {
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnMenu { background-color: #C62828; }
            QPushButton#btnInfo { background-color: #1565C0; }
            QPushButton#btnCapturar { background-color: #C62828; }
            QPushButton#btnAgregar { background-color: #1565C0; }
            QPushButton:hover { opacity: 0.85; }
            QLineEdit {
                border: 1px solid #1565C0;
                border-radius: 5px;
                padding: 4px;
                background-color: white;
                color: black;
            }
            QLabel { font-weight: bold; }
        """)

        # --- Contenedor principal con sombra ---
        frame = QFrame()
        shadow_frame = QGraphicsDropShadowEffect()
        shadow_frame.setBlurRadius(15)
        shadow_frame.setColor(QColor(0, 0, 0, 80))
        frame.setGraphicsEffect(shadow_frame)

        # --- Encabezado superior (logo + botones) ---
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(
                70, 70,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)  # 🔹 Volver al menú principal

        btn_info = QPushButton("MÁS INFORMACIÓN")
        btn_info.setObjectName("btnInfo")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        # --- Título principal ---
        titulo = QLabel("Registro Docente")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #C62828; margin: 10px;")

        # --- Formulario de datos ---
        lbl_nombre = QLabel("Nombre:")
        self.txt_nombre = QLineEdit()

        lbl_apellido = QLabel("Apellido:")
        self.txt_apellido = QLineEdit()

        form_layout = QHBoxLayout()
        form_layout.addStretch()
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.txt_nombre)
        form_layout.addSpacing(20)
        form_layout.addWidget(lbl_apellido)
        form_layout.addWidget(self.txt_apellido)
        form_layout.addStretch()

        # --- Cámara (vista previa) ---
        self.lbl_camara = QLabel("Visualización de la cámara")
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camara.setStyleSheet("""
            border: 2px dashed #1565C0;
            background-color: #fafafa;
            font-size: 14px;
        """)
        self.lbl_camara.setFixedHeight(320)

        # --- Botones inferiores ---
        btn_capturar = QPushButton("📸 Capturar Rostro")
        btn_capturar.setObjectName("btnCapturar")
        btn_capturar.clicked.connect(self.toggle_captura)

        btn_agregar = QPushButton("✅ Agregar Registro")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.clicked.connect(self.agregar_registro)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_capturar)
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(btn_agregar)
        bottom_layout.addStretch()

        # --- Layout final ---
        frame_layout = QVBoxLayout()
        frame_layout.addLayout(top_layout)
        frame_layout.addWidget(titulo)
        frame_layout.addLayout(form_layout)
        frame_layout.addWidget(self.lbl_camara)
        frame_layout.addLayout(bottom_layout)
        frame.setLayout(frame_layout)

        main_layout = QVBoxLayout()
        main_layout.addWidget(frame)
        self.setLayout(main_layout)

    # ------------------------------------------------------
    # Método: update_frame
    # Descripción: Actualiza la cámara en vivo en el QLabel
    # ------------------------------------------------------
    def update_frame(self):
        if self.camara_activa:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # Convertir imagen OpenCV → QImage
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.lbl_camara.setPixmap(QPixmap.fromImage(qt_image))

    # ------------------------------------------------------
    # Método: toggle_captura
    # Descripción: Captura una foto o reactiva la cámara
    # ------------------------------------------------------
    def toggle_captura(self):
        if self.camara_activa:
            ret, frame = self.cap.read()
            if ret:
                # Guardamos la foto
                self.foto_capturada = frame.copy()

                # Mostramos foto en el QLabel
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.lbl_camara.setPixmap(QPixmap.fromImage(qt_image))

                # Pausamos cámara
                self.camara_activa = False
        else:
            # Reactivar cámara
            self.camara_activa = True

    # ------------------------------------------------------
    # Método: agregar_registro
    # Descripción: Guarda datos + foto en la base de datos
    # ------------------------------------------------------
    def agregar_registro(self):
        nombre = self.txt_nombre.text().strip()
        apellido = self.txt_apellido.text().strip()

        # Validaciones
        if not nombre or not apellido:
            QMessageBox.warning(self, "Campos vacíos", "⚠ Debes ingresar nombre y apellido.")
            return

        if self.foto_capturada is None:
            QMessageBox.warning(self, "Sin foto", "⚠ Debes capturar una foto antes de registrar.")
            return

        # Convertir foto a bytes para BD
        ok, buffer = cv2.imencode(".jpg", self.foto_capturada)
        foto_bytes = buffer.tobytes() if ok else None

        # Guardar en la base de datos
        exito = registrar_docente(nombre, apellido, foto_bytes)

        if exito:
            QMessageBox.information(self, "Éxito", f"✅ Docente {nombre} {apellido} registrado correctamente")
            # Resetear formulario
            self.txt_nombre.clear()
            self.txt_apellido.clear()
            self.foto_capturada = None
            self.camara_activa = True
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar el docente en la base de datos")

    # ------------------------------------------------------
    # Método: volver_menu
    # Descripción: Regresa a la ventana principal (menú)
    # ------------------------------------------------------
    def volver_menu(self):
        from menu import InterfazAdministrativa  # Lazy import para evitar circular import
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.show()
        self.close()

    # ------------------------------------------------------
    # Método: closeEvent
    # Descripción: Libera la cámara al cerrar la ventana
    # ------------------------------------------------------
    def closeEvent(self, event):
        self.cap.release()


# ==========================================================
#   EJECUCIÓN DIRECTA
# ==========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistroDocente()
    ventana.show()
    sys.exit(app.exec())
