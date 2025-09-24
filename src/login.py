import sys
import cv2
import numpy as np
import face_recognition
import time
import dlib
from scipy.spatial import distance as dist

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QImage, QColor
from PyQt6.QtCore import Qt, QTimer

from modules.doc_login import cargar_docentes
from menu import InterfazAdministrativa   # ✅ Importar tu menú


# -------------------------------
# Función para calcular EAR (Eye Aspect Ratio)
# -------------------------------
def calcular_ear(ojo):
    A = dist.euclidean(ojo[1], ojo[5])
    B = dist.euclidean(ojo[2], ojo[4])
    C = dist.euclidean(ojo[0], ojo[3])
    return (A + B) / (2.0 * C)


class InicioSesionDocente(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicio sesión docente - Institución Educativa del Sur")
        self.centrar_ventana(1250, 670)

        # --- Cargar docentes desde BD ---
        self.docentes = cargar_docentes()
        self.docente_detectado = None
        self.ultimo_encoding = None
        self.ultimo_movimiento = time.time()
        self.ultimo_parpadeo = time.time()
        self.parpadeo_confirmado = False  # 👀 Nuevo estado

        # --- Inicializar cámara en 640x480 ---
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Control de frames
        self.frame_count = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.guia_pix = QPixmap("src/guia_silueta.png")\
            .scaled(800, 350, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)

        # --- Inicializar detector dlib ---
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

        self.init_ui()

    def centrar_ventana(self, ancho, alto):
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
                font-size: 26px;
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
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnInicio     { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnInfo       { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton:hover         { opacity: 0.85; }
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
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btn_inicio = QPushButton("INICIO")
        btn_inicio.setObjectName("btnInicio")
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(self.close)

        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_inicio)
        header.addWidget(btn_info)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        # --- Mensaje de bienvenida ---
        titulo = QLabel("Inicio sesión docente")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mensaje = QLabel("Bienvenido. Por favor mirar la cámara para proceder con el inicio de sesión")
        mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_docente = QLabel("Docente: [ninguno]")
        self.lbl_docente.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Cámara ---
        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setStyleSheet("""
            background-color: rgba(255,255,255,0.08);
            border: 5px solid #1565C0;
            border-radius: 15px;
        """)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_guia = QLabel(self.lbl_camara)
        self.lbl_guia.setPixmap(self.guia_pix)
        self.lbl_guia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # --- Layout principal ---
        frame = QFrame()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addWidget(mensaje)
        vbox.addWidget(self.lbl_docente)
        vbox.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(frame)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Flip horizontal para efecto espejo
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Mostrar SIEMPRE video fluido en PyQt
        h, w, _ = rgb_frame.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        rgb_resized = cv2.resize(rgb_frame, (tw, th), interpolation=cv2.INTER_LINEAR)
        img = QImage(rgb_resized.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))
        self.lbl_guia.resize(self.lbl_camara.size())
        self.lbl_guia.move(0, 0)

        # 🔥 Procesar detección SOLO cada 12 frames
        self.frame_count += 1
        if self.frame_count % 12 != 0:
            return

        # Reducir resolución para procesar más rápido
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)

        # ----------------------------
        # Reconocimiento de rostro
        # ----------------------------
        face_locations = face_recognition.face_locations(small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        self.docente_detectado = None
        if face_encodings:
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    [d["encoding"] for d in self.docentes],
                    face_encoding,
                    tolerance=0.5
                )
                if True in matches:
                    idx = matches.index(True)
                    docente = self.docentes[idx]
                    self.docente_detectado = docente
                    self.lbl_docente.setText(f"Docente: {docente['nombres']} {docente['apellidos']}")
                    self.verificar_movimiento(face_encoding)
                    break
            if not self.docente_detectado:
                self.lbl_docente.setText("Docente: No reconocido")
        else:
            self.lbl_docente.setText("Docente: [ninguno]")

        # ----------------------------
        # Parpadeo (dlib)
        # ----------------------------
        faces = self.detector(rgb_frame, 0)
        for face in faces:
            shape = self.predictor(rgb_frame, face)
            coords = np.array([[p.x, p.y] for p in shape.parts()])

            ojo_izq = coords[42:48]
            ojo_der = coords[36:42]
            ear_izq = calcular_ear(ojo_izq)
            ear_der = calcular_ear(ojo_der)
            ear = (ear_izq + ear_der) / 2.0

            if ear < 0.20:  # ojo cerrado
                self.ultimo_parpadeo = time.time()

        # ----------------------------
        # Validación automática
        # ----------------------------
        if self.docente_detectado:
            if time.time() - self.ultimo_movimiento > 5:
                self.lbl_docente.setText("❌ Rostro estático (posible foto)")
            elif time.time() - self.ultimo_parpadeo > 6:
                self.lbl_docente.setText("❌ Parpadea porfa")
            else:
                if not self.parpadeo_confirmado:
                    self.parpadeo_confirmado = True
                    self.lbl_docente.setText(
                        f"✅ Bienvenido {self.docente_detectado['nombres']} {self.docente_detectado['apellidos']}, redirigiendo..."
                    )
                    QTimer.singleShot(3000, self.abrir_menu)

    def verificar_movimiento(self, encoding_actual):
        if self.ultimo_encoding is not None:
            distancia = np.linalg.norm(self.ultimo_encoding - encoding_actual)
            if distancia > 0.01:
                self.ultimo_movimiento = time.time()
        self.ultimo_encoding = encoding_actual

    def abrir_menu(self):
        self.cap.release()
        self.menu = InterfazAdministrativa()
        self.menu.showMaximized()
        self.close()

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = InicioSesionDocente()
    ventana.show()
    sys.exit(app.exec())
