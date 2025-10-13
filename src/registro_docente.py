import sys
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QMessageBox, QComboBox
)
from PyQt6.QtGui import QImage, QPixmap, QColor
from PyQt6.QtCore import Qt, QTimer

from modules.docentes import registrar_docente

from modules.sesion import Sesion



class RegistroDocente(QWidget):
    def __init__(self):
        super().__init__()

        # ✅ Verificar sesión
        if not Sesion.esta_autenticado():
            QMessageBox.critical(self, "Acceso denegado", "⚠ Debe iniciar sesión para usar esta ventana.")
            sys.exit(0)  # Cierra la app si no hay sesión activa

        self.setWindowTitle("Registro de Docentes - Institución Educativa del Sur")
        self.centrar_ventana(1250, 670)

        # Estado de cámara
        self.camara_activa = True
        self.foto_capturada = None
        self.cap = cv2.VideoCapture(0)

        # --- Detector de rostro ---
        self.detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        # Timer para refrescar cámara
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Guía de silueta
        self.guia_pix = QPixmap("src/guia_silueta.png")\
            .scaled(800, 350, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)

        self.init_ui()

    def centrar_ventana(self, ancho=1250, alto=670):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - ancho) // 2
        y = (screen.height() - alto) // 2
        self.setGeometry(x, y, ancho, alto)

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0D1B2A;
                color: white;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel#titulo {
                font-size: 28px;
                font-weight: bold;
                color: #E3F2FD;
            }
            QLabel#nombreColegio {
                font-size: 36px;
                font-weight: bold;
                color: #E3F2FD;
            }
            QLabel#lemaColegio {
                font-size: 22px;
                color: #aaa;
            }
            QLineEdit, QComboBox {
                border: 1px solid #1565C0;
                border-radius: 5px;
                padding: 6px;
                font-size: 16px;
                background: white;
                color: black;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnMenu     { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton#btnInfo     { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnCapturar { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnAgregar  { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton:hover       { opacity: 0.85; }
        """)

        # --- Header ---
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)

        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")

        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_menu)
        header.addWidget(btn_info)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        # --- Título ---
        titulo = QLabel("Registro de Docentes")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Formulario ---
        lbl_cedula = QLabel("Cédula:")
        self.txt_cedula = QLineEdit()
        lbl_nombre = QLabel("Nombres:")
        self.txt_nombre = QLineEdit()
        lbl_apellido = QLabel("Apellidos:")
        self.txt_apellido = QLineEdit()
        lbl_celular = QLabel("Celular:")
        self.txt_celular = QLineEdit()
        lbl_admin = QLabel("¿Es administrador?")
        self.cmb_admin = QComboBox()
        self.cmb_admin.addItems(["No", "Sí"])

        form = QHBoxLayout()
        form.addStretch()
        form.addWidget(lbl_cedula)
        form.addWidget(self.txt_cedula)
        form.addSpacing(15)
        form.addWidget(lbl_nombre)
        form.addWidget(self.txt_nombre)
        form.addSpacing(15)
        form.addWidget(lbl_apellido)
        form.addWidget(self.txt_apellido)
        form.addSpacing(15)
        form.addWidget(lbl_celular)
        form.addWidget(self.txt_celular)
        form.addSpacing(15)
        form.addWidget(lbl_admin)
        form.addWidget(self.cmb_admin)
        form.addStretch()

        # --- Área de cámara ---
        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setStyleSheet("""
            background-color: none;
            border: 5px solid #1c2c3c;
            border-radius: 15px;
        """)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_guia = QLabel(self.lbl_camara)
        self.lbl_guia.setPixmap(self.guia_pix)
        self.lbl_guia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # --- Mensaje de estado ---
        self.lbl_estado = QLabel("")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")

        # --- Botones ---
        self.btn_capturar = QPushButton("Capturar")
        self.btn_capturar.setObjectName("btnCapturar")
        self.btn_capturar.clicked.connect(self.toggle_captura)
        self.btn_capturar.setEnabled(False)  # 🔹 empieza deshabilitado

        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.clicked.connect(self.agregar_registro)

        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(self.btn_capturar)
        bottom.addSpacing(20)
        bottom.addWidget(btn_agregar)
        bottom.addStretch()

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(header)
        main_layout.addWidget(separador)
        main_layout.addWidget(titulo)
        main_layout.addLayout(form)
        main_layout.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_estado)   # 🔹 mensaje debajo de la cámara
        main_layout.addLayout(bottom)

        self.setLayout(main_layout)

    def update_frame(self):
        if not self.camara_activa:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostros = self.detector.detectMultiScale(gray, 1.3, 5)

        if len(rostros) > 0:
            self.lbl_estado.setText("✅ Rostro detectado, capture la imagen")
            self.btn_capturar.setEnabled(True)
        else:
            self.lbl_estado.setText("")
            self.btn_capturar.setEnabled(False)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        rgb = cv2.resize(rgb, (tw, th), interpolation=cv2.INTER_LINEAR)
        img = QImage(rgb.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))
        self.lbl_guia.resize(self.lbl_camara.size())
        self.lbl_guia.move(0, 0)

    def toggle_captura(self):
        if self.camara_activa:
            ret, frame = self.cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            self.foto_capturada = frame.copy()
            self.camara_activa = False
            self.update_frame()
        else:
            self.camara_activa = True

    def agregar_registro(self):
        cedula = self.txt_cedula.text().strip()
        nombre = self.txt_nombre.text().strip()
        apellido = self.txt_apellido.text().strip()
        celular = self.txt_celular.text().strip()
        es_admin = 1 if self.cmb_admin.currentText() == "Sí" else 0

        if not cedula or not nombre or not apellido or not celular:
            QMessageBox.warning(self, "Campos vacíos", "⚠ Debes completar todos los campos")
            return
        if self.foto_capturada is None:
            QMessageBox.warning(self, "Sin foto", "⚠ Debes capturar una foto primero")
            return

        ok, buf = cv2.imencode(".jpg", self.foto_capturada)
        foto_bytes = buf.tobytes() if ok else None

        if registrar_docente(cedula, nombre, apellido, celular, es_admin, foto_bytes):
            QMessageBox.information(self, "Éxito", f"Docente {nombre} {apellido} registrado")
            self.txt_cedula.clear()
            self.txt_nombre.clear()
            self.txt_apellido.clear()
            self.txt_celular.clear()
            self.cmb_admin.setCurrentIndex(0)
            self.foto_capturada = None
            self.camara_activa = True
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el docente")

    def volver_menu(self):
        from menu import InterfazAdministrativa
        self.cap.release()
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistroDocente()
    ventana.show()
    sys.exit(app.exec())
