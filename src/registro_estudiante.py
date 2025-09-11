import sys
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QMessageBox, QComboBox
)
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer

# Importar función del backend (ya genera ID y matrícula)
from modules.estudiantes import registrar_estudiante  


# ==========================================================
#   CLASE: RegistroEstudiantes
# ==========================================================
class RegistroEstudiantes(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registro de Estudiantes - Institución Educativa del Sur")
        self.resize(900, 600)
        self.centrar_ventana()

        # Estado de cámara
        self.camara_activa = True
        self.foto_capturada = None

        # Cámara
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.init_ui()

    # Centrar ventana
    def centrar_ventana(self):
        pantalla = QApplication.primaryScreen().availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(pantalla.center())
        self.move(geo.topLeft())

    # Construcción interfaz
    def init_ui(self):
        self.setStyleSheet("""
    QWidget { background-color: white; color: black; font-family: Arial; font-size: 14px; }
    QFrame { border: 2px solid #ddd; border-radius: 12px; background-color: white; }
    QPushButton { border-radius: 8px; padding: 8px 16px; font-weight: bold; color: white; }
    QPushButton#btnMenu { background-color: #C62828; }
    QPushButton#btnInfo { background-color: #1565C0; }
    QPushButton#btnCapturar { background-color: #C62828; }
    QPushButton#btnAgregar { background-color: #1565C0; }
    QPushButton:hover { opacity: 0.85; }
    QLineEdit { border: 1px solid #1565C0; border-radius: 5px; padding: 6px; font-size: 16px; }
    QComboBox { border: 1px solid #1565C0; border-radius: 5px; padding: 6px 35px 6px 10px; font-size: 16px; min-height: 38px; }
    QLabel { font-weight: bold; }
""")

        # Frame
        frame = QFrame()
        shadow_frame = QGraphicsDropShadowEffect()
        shadow_frame.setBlurRadius(15)
        shadow_frame.setColor(QColor(0, 0, 0, 80))
        frame.setGraphicsEffect(shadow_frame)

        # Logo y botones
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
        titulo = QLabel("Registro de Estudiantes")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #C62828; margin: 10px;")

        # Campos formulario
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

        # Cámara
        self.lbl_camara = QLabel("Visualización de la cámara")
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camara.setStyleSheet("border: 2px dashed #1565C0; background-color: #fafafa; font-size: 14px;")
        self.lbl_camara.setFixedHeight(320)

        # Botones inferiores
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

    # Actualizar cámara
    def update_frame(self):
        if self.camara_activa:
            ret, frame = self.cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.lbl_camara.setPixmap(QPixmap.fromImage(qt_image))

    # Capturar foto
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

    # Guardar estudiante
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

    # Volver al menú
    def volver_menu(self):
        from menu import InterfazAdministrativa
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.show()
        self.close()

    # Liberar cámara
    def closeEvent(self, event):
        self.cap.release()


# Ejecución directa
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistroEstudiantes()
    ventana.show()
    sys.exit(app.exec())
