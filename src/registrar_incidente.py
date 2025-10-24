import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QComboBox, QTextEdit, QTableWidgetItem,
    QLineEdit, QMessageBox
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt
from datetime import datetime

class RegistrarIncidente(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Registrar Incidente - Institución Educativa del Sur")
        self.resize(1250, 700)
        self.centrar_ventana()
        self.init_ui()

    def centrar_ventana(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

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
            QComboBox, QTextEdit {
                background-color: white;
                color: black;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnManual     { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton#btnInfo       { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnResumen    { background-color: rgba(255,193,7,0.60); color: black; }
            QPushButton#btnRegistrar  { background-color: rgba(21, 101, 192, 0.60); }
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

        btn_manual = QPushButton("MENÚ")
        btn_manual.setObjectName("btnManual")
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")

        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_manual)
        header.addWidget(btn_info)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        # --- Título ---
        titulo = QLabel("Registrar Incidente")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Sección Incidentes ---
        self.cmb_equipo = QComboBox()
        self.cmb_equipo.addItems(["E-01","E-02","E-03","E-04","E-05","E-06","E-26", "E-27", "E-28", "E-29"])

        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Dañado", "Ocupado", "Disponible"])

        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Describe el incidente con detalle...")

        btn_resumen = QPushButton("Generar Resumen")
        btn_resumen.setObjectName("btnResumen")
        btn_resumen.clicked.connect(self.generar_resumen)

        incidente_layout = QVBoxLayout()
        incidente_layout.addWidget(QLabel("Equipo"))
        incidente_layout.addWidget(self.cmb_equipo)
        incidente_layout.addWidget(QLabel("Estado"))
        incidente_layout.addWidget(self.cmb_estado)
        incidente_layout.addWidget(QLabel("Descripción"))
        incidente_layout.addWidget(self.txt_descripcion)
        incidente_layout.addWidget(btn_resumen)

        # --- Sección Resumen ---
        self.txt_resumen = QTextEdit()
        self.txt_resumen.setReadOnly(True)
        self.txt_resumen.setPlaceholderText("Aquí aparecerá el resumen generado...")

        btn_registrar = QPushButton("Registrar Incidente")
        btn_registrar.setObjectName("btnRegistrar")
        btn_registrar.clicked.connect(self.registrar_incidente)

        resumen_layout = QVBoxLayout()
        resumen_layout.addWidget(QLabel("Resumen"))
        resumen_layout.addWidget(self.txt_resumen)
        resumen_layout.addWidget(btn_registrar)

        # --- Layout principal ---
        contenido = QHBoxLayout()
        contenido.addLayout(incidente_layout)
        contenido.addLayout(resumen_layout)

        frame = QFrame()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addLayout(contenido)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(frame)

    def generar_resumen(self):

        equipo = self.cmb_equipo.currentText()
        estado = self.cmb_estado.currentText()
        descripcion = self.txt_descripcion.toPlainText().strip()

        if not descripcion:
            QMessageBox.warning(self, "Descripción vacía", "⚠ Debes escribir una descripción del incidente.")
            return

        # Simular nombre del estudiante (puedes reemplazarlo luego por el nombre obtenido de sesión o base de datos)
        nombre_estudiante = "Juan Pérez"

        # Fecha y hora actuales
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        hora_actual = datetime.now().strftime("%H:%M:%S")

        resumen = (
            f"El equipo #{equipo} tuvo el siguiente incidente:\n"
            f"{descripcion}\n"
            f"Lo cual ocurrió a las {hora_actual} del día {fecha_actual}, "
            f"en el momento que el estudiante {nombre_estudiante} se encontraba haciendo uso del mismo."
        )

        self.txt_resumen.setText(resumen)


    def registrar_incidente(self):
        resumen = self.txt_resumen.toPlainText().strip()
        if not resumen:
            QMessageBox.warning(self, "Resumen vacío", "⚠ Debes generar un resumen antes de registrar.")
            return

        # Aquí iría la lógica para guardar en la base de datos
        QMessageBox.information(self, "Incidente registrado", "✅ El incidente ha sido registrado correctamente.")
        self.txt_descripcion.clear()
        self.txt_resumen.clear()
        self.cmb_estado.setCurrentIndex(0)
        self.cmb_equipo.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistrarIncidente()
    ventana.show()
    sys.exit(app.exec())
