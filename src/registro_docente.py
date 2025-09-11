import sys
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QMessageBox, QComboBox
)
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer

# Importar función del backend para guardar en la BD
from modules.docentes import registrar_docente  


# ==========================================================
#   CLASE: RegistroDocente
# ==========================================================
class RegistroDocente(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro Docente - Institución Educativa del Sur")
        self.resize(900, 600)
        self.centrar_ventana()

        # Estado cámara
        self.camara_activa = True
        self.foto_capturada = None

        # Clasificador de rostros
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        # Cámara
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.init_ui()

    def centrar_ventana(self):
        pantalla = QApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(pantalla.center())
        self.move(geo.topLeft())

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

        frame = QFrame()
        shadow_frame = QGraphicsDropShadowEffect()
        shadow_frame.setBlurRadius(15)
        shadow_frame.setColor(QColor(0, 0, 0, 80))
        frame.setGraphicsEffect(shadow_frame)

        # Encabezado
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)

        btn_info = QPushButton("MÁS INFORMACIÓN")
        btn_info.setObjectName("btnInfo")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        # Título
        titulo = QLabel("Registro Docente")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #C62828; margin: 10px;")

        # Formulario
        self.txt_cedula = QLineEdit()
        self.txt_cedula.setPlaceholderText("Cédula")

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombres")

        self.txt_apellido = QLineEdit()
        self.txt_apellido.setPlaceholderText("Apellidos")

        self.txt_celular = QLineEdit()
        self.txt_celular.setPlaceholderText("Celular")

        self.cmb_admin = QComboBox()
        self.cmb_admin.addItems(["No", "Sí"])  # 0 = No admin, 1 = Admin

        form_layout = QVBoxLayout()
        form_layout.addWidget(QLabel("Cédula:"))
        form_layout.addWidget(self.txt_cedula)
        form_layout.addWidget(QLabel("Nombres:"))
        form_layout.addWidget(self.txt_nombre)
        form_layout.addWidget(QLabel("Apellidos:"))
        form_layout.addWidget(self.txt_apellido)
        form_layout.addWidget(QLabel("Celular:"))
        form_layout.addWidget(self.txt_celular)
        form_layout.addWidget(QLabel("¿Es administrador?"))
        form_layout.addWidget(self.cmb_admin)

        # Cámara
        self.lbl_camara = QLabel("Visualización de la cámara")
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camara.setStyleSheet("""
            border: 2px dashed #1565C0;
            background-color: #fafafa;
            font-size: 14px;
        """)
        self.lbl_camara.setFixedHeight(320)

        # Botones
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
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

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
        cedula = self.txt_cedula.text().strip()
        nombre = self.txt_nombre.text().strip()
        apellido = self.txt_apellido.text().strip()
        celular = self.txt_celular.text().strip()
        es_admin = 1 if self.cmb_admin.currentText() == "Sí" else 0

        if not cedula or not nombre or not apellido or not celular:
            QMessageBox.warning(self, "Campos vacíos", "⚠ Todos los campos son obligatorios.")
            return

        if self.foto_capturada is None:
            QMessageBox.warning(self, "Sin foto", "⚠ Debes capturar una foto antes de registrar.")
            return

        ok, buffer = cv2.imencode(".jpg", self.foto_capturada)
        foto_bytes = buffer.tobytes() if ok else None

        exito = registrar_docente(cedula, nombre, apellido, celular, es_admin, foto_bytes)

        if exito:
            QMessageBox.information(self, "Éxito", f"✅ Docente {nombre} {apellido} registrado correctamente")
            self.txt_cedula.clear()
            self.txt_nombre.clear()
            self.txt_apellido.clear()
            self.txt_celular.clear()
            self.cmb_admin.setCurrentIndex(0)
            self.foto_capturada = None
            self.camara_activa = True
        else:
            QMessageBox.critical(self, "Error", "❌ No se pudo registrar el docente en la base de datos")

    def volver_menu(self):
        from menu import InterfazAdministrativa
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.show()
        self.close()

    def closeEvent(self, event):
        self.cap.release()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistroDocente()
    ventana.show()
    sys.exit(app.exec())
