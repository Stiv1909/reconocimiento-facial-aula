import sys
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QMessageBox
)
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer

from modules.docentes import registrar_docente  # Importar función para BD


class RegistroDocente(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro Docente - Institución Educativa del Sur")
        self.setGeometry(200, 200, 900, 600)

        # --- Estado de cámara ---
        self.camara_activa = True
        self.foto_capturada = None

        # --- Cargar clasificador de rostros ---
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        # --- Variables de cámara ---
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.init_ui()

    def init_ui(self):
        # --- Estilos globales con colores del escudo ---
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
            QPushButton#btnMenu {
                background-color: #C62828; /* Rojo escudo */
            }
            QPushButton#btnInfo {
                background-color: #1565C0; /* Azul escudo */
            }
            QPushButton#btnCapturar {
                background-color: #C62828; /* Rojo escudo */
            }
            QPushButton#btnAgregar {
                background-color: #1565C0; /* Azul escudo */
            }
            QPushButton:hover {
                opacity: 0.85;
            }
            QLineEdit {
                border: 1px solid #1565C0;
                border-radius: 5px;
                padding: 4px;
                background-color: white;
                color: black;
            }
            QLabel {
                font-weight: bold;
            }
        """)

        # --- Contenedor principal ---
        frame = QFrame()
        shadow_frame = QGraphicsDropShadowEffect()
        shadow_frame.setBlurRadius(15)
        shadow_frame.setColor(QColor(0, 0, 0, 80))
        frame.setGraphicsEffect(shadow_frame)

        # --- Fila superior: Logo + Botones ---
        logo = QLabel()
        pixmap_logo = QPixmap(r"C:\Users\steven\Documents\2.GIT-GRADO\reconocimiento-facial-aula\src\logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_info = QPushButton("MÁS INFORMACIÓN")
        btn_info.setObjectName("btnInfo")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        # --- Título ---
        titulo = QLabel("Registro Docente")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #C62828; margin-top: 5px; margin-bottom: 10px;")

        # --- Campos de texto ---
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

        # --- Área de cámara ---
        self.lbl_camara = QLabel("Visualización de lo que observa la cámara")
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

        # --- Layout interno ---
        frame_layout = QVBoxLayout()
        frame_layout.addLayout(top_layout)
        frame_layout.addWidget(titulo)
        frame_layout.addLayout(form_layout)
        frame_layout.addWidget(self.lbl_camara)
        frame_layout.addLayout(bottom_layout)
        frame.setLayout(frame_layout)

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(frame)
        self.setLayout(main_layout)

    def update_frame(self):
        if self.camara_activa:
            ret, frame = self.cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.lbl_camara.setPixmap(QPixmap.fromImage(qt_image))

    def toggle_captura(self):
        if self.camara_activa:
            # Congelar imagen
            ret, frame = self.cap.read()
            if ret:
                self.foto_capturada = frame.copy()
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.lbl_camara.setPixmap(QPixmap.fromImage(qt_image))
                self.camara_activa = False
        else:
            # Volver a cámara en vivo
            self.camara_activa = True

    def agregar_registro(self):
        nombre = self.txt_nombre.text().strip()
        apellido = self.txt_apellido.text().strip()

        if not nombre or not apellido:
            QMessageBox.warning(self, "Campos vacíos", "⚠ Debes ingresar nombre y apellido.")
            return

        if self.foto_capturada is None:
            QMessageBox.warning(self, "Sin foto", "⚠ Debes capturar una foto antes de registrar.")
            return

        # Convertir foto a binario
        ok, buffer = cv2.imencode(".jpg", self.foto_capturada)
        foto_bytes = buffer.tobytes() if ok else None

        exito = registrar_docente(nombre, apellido, foto_bytes)

        if exito:
            QMessageBox.information(self, "Éxito", f"✅ Docente {nombre} {apellido} registrado correctamente")
            self.txt_nombre.clear()
            self.txt_apellido.clear()
            self.foto_capturada = None
            self.camara_activa = True
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar el docente en la base de datos")

    def closeEvent(self, event):
        self.cap.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistroDocente()
    ventana.show()
    sys.exit(app.exec())
