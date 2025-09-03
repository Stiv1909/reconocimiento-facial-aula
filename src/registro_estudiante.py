import sys
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QMessageBox, QComboBox
)
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer

from modules.estudiantes import registrar_estudiante


class RegistroEstudiantes(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Estudiantes - Institución Educativa del Sur")
        self.setGeometry(200, 200, 900, 600)

        # Estado de cámara
        self.camara_activa = True
        self.foto_capturada = None

        # Clasificador de rostros
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        # Cámara
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.init_ui()

    def init_ui(self):
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
        background-color: #C62828;
    }
    QPushButton#btnInfo {
        background-color: #1565C0;
    }
    QPushButton#btnCapturar {
        background-color: #C62828;
    }
    QPushButton#btnAgregar {
        background-color: #1565C0;
    }
    QPushButton:hover {
        opacity: 0.85;
    }
    QLineEdit {
        border: 1px solid #1565C0;
        border-radius: 5px;
        padding: 6px;
        font-size: 16px;
        background-color: white;
        color: black;
    }
    /* ComboBox principal */
    QComboBox {
        border: 1px solid #1565C0;
        border-radius: 5px;
        padding: 6px 35px 6px 10px;
        font-size: 16px;
        min-height: 38px;
        background-color: white;
        color: black;
    }
    QComboBox:hover {
        border: 1px solid #0D47A1;
    }
    QComboBox:focus {
        border: 2px solid #0D47A1;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 30px;
        border-left: 1px solid #1565C0;
        background-color: #f0f0f0;
        border-top-right-radius: 5px;
        border-bottom-right-radius: 5px;
    }
    QComboBox::down-arrow {
        image: none;
        border: none;
        width: 0;
        height: 0;
        margin-right: 8px;
        margin-top: 6px;
        border-left: 7px solid transparent;
        border-right: 7px solid transparent;
        border-top: 7px solid #1565C0;
    }
    /* Lista desplegable */
    QComboBox QAbstractItemView {
        border: 1px solid #1565C0;
        border-radius: 5px;
        background-color: white;
        selection-background-color: #1565C0;
        selection-color: white;
        font-size: 15px;
        outline: 0;
    }
    QComboBox QAbstractItemView::item {
        padding: 6px 10px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: #E3F2FD;
        color: black;
    }
    QLabel {
        font-weight: bold;
    }
""")


        frame = QFrame()
        shadow_frame = QGraphicsDropShadowEffect()
        shadow_frame.setBlurRadius(15)
        shadow_frame.setColor(QColor(0, 0, 0, 80))
        frame.setGraphicsEffect(shadow_frame)

        # Fila superior
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

        # Título
        titulo = QLabel("Registro de Estudiantes")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #C62828; margin-top: 5px; margin-bottom: 10px;")

        # Campos
        lbl_nombre = QLabel("Nombre:")
        self.txt_nombre = QLineEdit()
        lbl_apellido = QLabel("Apellido:")
        self.txt_apellido = QLineEdit()
        lbl_grado = QLabel("Grado:")
        self.cmb_grado = QComboBox()
        self.cmb_grado.addItems([
            "6-1", "6-2", "6-3", "6-4",
            "7-1", "7-2", "7-3", "7-4",
            "8-1", "8-2", "8-3",
            "9-1", "9-2", "9-3",
            "10-1", "10-2", "10-3",
            "11-1", "11-2", "11-3"
        ])

        form_layout = QHBoxLayout()
        form_layout.addStretch()
        form_layout.addWidget(lbl_nombre)
        form_layout.addWidget(self.txt_nombre)
        form_layout.addSpacing(10)
        form_layout.addWidget(lbl_apellido)
        form_layout.addWidget(self.txt_apellido)
        form_layout.addSpacing(10)
        form_layout.addWidget(lbl_grado)
        form_layout.addWidget(self.cmb_grado)
        form_layout.addStretch()

        # Área de cámara
        self.lbl_camara = QLabel("Visualización de lo que observa la cámara")
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camara.setStyleSheet("""
            border: 2px dashed #1565C0;
            background-color: #fafafa;
            font-size: 14px;
        """)
        self.lbl_camara.setFixedHeight(320)

        # Botones
        btn_capturar = QPushButton("📸 Capturar Registro")
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

        # Layouts
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

    def update_frame(self):
        if self.camara_activa:
            ret, frame = self.cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.lbl_camara.setPixmap(QPixmap.fromImage(qt_image))

    def toggle_captura(self):
        if self.camara_activa:
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
            self.camara_activa = True

    def agregar_registro(self):
        nombre = self.txt_nombre.text().strip()
        apellido = self.txt_apellido.text().strip()
        grado = self.cmb_grado.currentText()

        if not nombre or not apellido or not grado:
            QMessageBox.warning(self, "Campos vacíos", "⚠ Debes ingresar todos los campos.")
            return

        if self.foto_capturada is None:
            QMessageBox.warning(self, "Sin foto", "⚠ Debes capturar una foto antes de registrar.")
            return

        # Convertir foto a binario
        ok, buffer = cv2.imencode(".jpg", self.foto_capturada)
        foto_bytes = buffer.tobytes() if ok else None

        exito = registrar_estudiante(nombre, apellido, grado, foto_bytes)

        if exito:
            QMessageBox.information(self, "Éxito", f"✅ Estudiante {nombre} {apellido} registrado correctamente")
            self.txt_nombre.clear()
            self.txt_apellido.clear()
            self.cmb_grado.setCurrentIndex(0)
            self.foto_capturada = None
            self.camara_activa = True
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar el estudiante en la base de datos")

    def closeEvent(self, event):
        self.cap.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistroEstudiantes()
    ventana.show()
    sys.exit(app.exec())
