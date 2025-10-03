import sys
import cv2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QGraphicsDropShadowEffect, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage, QColor
from PyQt6.QtCore import Qt, QTimer


class SalidaEstudiantes(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Salida de Estudiantes - Institución Educativa del Sur")
        self.centrar_ventana(1250, 670)

        # Estado cámara
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Guía de silueta
        self.guia_pix = QPixmap("src/guia_silueta.png")\
            .scaled(800, 350, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)

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
            QPushButton#btnMenu     { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnInfo     { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton#btnFinalizar{ background-color: rgba(21, 101, 192, 0.60); }
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
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_info = QPushButton("MÁS INFORMACIÓN")
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

        # --- Mensajes ---
        titulo = QLabel("Salida de Estudiantes")   # 👈 CAMBIO DE TÍTULO
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Tarjetitas de asignamientos simultáneos ---
        self.card_asig1 = self.crear_tarjeta("Asignamiento 1", "Equipo #---")
        self.card_asig2 = self.crear_tarjeta("Asignamiento 2", "Equipo #---")
        self.card_asig3 = self.crear_tarjeta("Asignamiento 3", "Equipo #---")
        self.card_asig4 = self.crear_tarjeta("Asignamiento 4", "Equipo #---")

        cards_layout = QHBoxLayout()
        cards_layout.addStretch()
        cards_layout.addWidget(self.card_asig1)
        cards_layout.addWidget(self.card_asig2)
        cards_layout.addWidget(self.card_asig3)
        cards_layout.addWidget(self.card_asig4)
        cards_layout.addStretch()

        # --- Contador de equipos asignados ---
        self.lbl_contador = QLabel("Equipos asignados: 0")
        self.lbl_contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_contador.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #FFD54F;
        """)

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

        # --- Botón ---
        btn_finalizar = QPushButton("Finalizar salida")   # 👈 CAMBIO DE TEXTO
        btn_finalizar.setObjectName("btnFinalizar")
        btn_finalizar.clicked.connect(self.finalizar_salida)

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
        vbox.addLayout(cards_layout)   # 👈 Tarjetitas aquí
        vbox.addWidget(self.lbl_contador)  # 👈 Contador debajo
        vbox.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(btn_finalizar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(frame)

    def crear_tarjeta(self, titulo, valor):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255,255,255,0.08);
                border: 2px solid #1565C0;
                border-radius: 12px;
            }
            QLabel {
                color: white;
            }
            QLabel#titulo {
                font-size: 14px;
                font-weight: bold;
                color: #E3F2FD;
            }
            QLabel#valor {
                font-size: 14px;
                font-weight: bold;
                color: #FFFFFF;
            }
        """)
        vbox = QVBoxLayout(frame)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("valor")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        vbox.addWidget(lbl_titulo)
        vbox.addWidget(lbl_valor)
        frame.setLayout(vbox)
        frame.setFixedSize(220, 100)

        # Guardamos referencia al valor para actualizar dinámicamente
        frame.lbl_valor = lbl_valor
        return frame

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        rgb = cv2.resize(rgb, (tw, th), interpolation=cv2.INTER_LINEAR)
        img = QImage(rgb.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))
        self.lbl_guia.resize(self.lbl_camara.size())
        self.lbl_guia.move(0, 0)

    def finalizar_salida(self):
        QMessageBox.information(self, "Salida", "✅ Salida registrada correctamente")

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = SalidaEstudiantes()
    ventana.show()
    sys.exit(app.exec())
