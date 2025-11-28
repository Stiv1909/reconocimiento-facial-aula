import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QLineEdit, QComboBox, QTextEdit, QMessageBox
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt
from modules.sesion import Sesion
from modules.reporte_logic import generar_reporte_pdf
import os
class ReporteAsistencias(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reporte de Asistencias - Institución Educativa del Sur")
        self.resize(1250, 700)
        self.centrar_ventana()
        self.usuario = Sesion.obtener_usuario()
        if not self.usuario:
            # No hay sesión: cerramos la ventana (redirigir al login)
            self.close()
            return

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
            QLineEdit, QComboBox {
                background-color: white;
                color: black;
                border-radius: 6px;
                padding: 6px;
                font-size: 14px;
            }
            QTextEdit {
                background-color: white;
                color: black;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnMenu     { background-color: rgba(21, 101, 192,0.60); }
            QPushButton#btnInfo     { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnGenerar  { background-color: rgba(255,193,7,0.60); color: black; }
            QPushButton#btnDescargar{ background-color: rgba(21, 101, 192, 0.60); }
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
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.abrir_menu)
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(QApplication.quit)

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
        titulo = QLabel("Asistencias")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Filtros ---
        self.txt_desde = QLineEdit()
        self.txt_desde.setPlaceholderText("Desde: DD/MM/AAAA")

        self.txt_hasta = QLineEdit()
        self.txt_hasta.setPlaceholderText("Hasta: DD/MM/AAAA")

        self.cmb_grado = QComboBox()
        self.cmb_grado.addItems(["6-1", "7-1", "7-3", "8-1", "9-1", "10-1", "11-1"])

        btn_generar = QPushButton("Generar")
        btn_generar.setObjectName("btnGenerar")
        btn_generar.clicked.connect(self.generar_reporte)

        filtros = QHBoxLayout()
        filtros.addWidget(self.txt_desde)
        filtros.addWidget(self.txt_hasta)
        filtros.addWidget(self.cmb_grado)
        filtros.addWidget(btn_generar)

        # --- Previsualización ---
        previsual = QLabel("Previsualización")
        previsual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        previsual.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFD54F;")

        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setPlaceholderText("Visualización del documento de asistencias")

        btn_descargar = QPushButton("Descargar PDF")
        btn_descargar.setObjectName("btnDescargar")
        btn_descargar.clicked.connect(self.descargar_pdf)

        # --- Layout principal ---
        frame = QFrame()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addLayout(filtros)
        vbox.addWidget(previsual)
        vbox.addWidget(self.txt_preview)
        vbox.addWidget(btn_descargar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(frame)

    def generar_reporte(self):
        desde = self.txt_desde.text().strip()
        hasta = self.txt_hasta.text().strip()
        grado = self.cmb_grado.currentText()

        if not desde or not hasta:
            QMessageBox.warning(self, "Fechas incompletas", "⚠ Debes ingresar ambas fechas.")
            return

        # Previsualización simple, NO el PDF real
        texto = (
            f"REPORTE DE ASISTENCIAS\n"
            f"Grado: {grado}\n"
            f"Desde: {desde}\n"
            f"Hasta: {hasta}\n"
            f"\n✔ Presiona 'Descargar PDF' para generar el documento oficial."
        )
        self.txt_preview.setText(texto)

    def descargar_pdf(self):
        contenido = self.txt_preview.toPlainText().strip()
        if not contenido:
            QMessageBox.warning(self, "Sin contenido", "⚠ Debes generar el reporte antes de descargar.")
            return

        # DATOS DEL DOCENTE LOGUEADO
        usuario = Sesion.obtener_usuario()
        docente_payload = {
            "nombres": usuario.get("nombres", ""),
            "apellidos": usuario.get("apellidos", "")
        }
        codigo_doc = usuario.get("cedula", "")

        # LLAMADA A LA LÓGICA
        from modules.reporte_logic import generar_reporte_pdf
        result = generar_reporte_pdf(
            self.txt_desde.text().strip(),
            self.txt_hasta.text().strip(),
            self.cmb_grado.currentText(),
            docente=docente_payload,
            codigo_doc=codigo_doc
        )

        if result["ok"]:
            QMessageBox.information(self, "Éxito", "📄 Reporte generado correctamente en Descargas.")
        else:
            QMessageBox.critical(self, "Error", result["msg"])


    def abrir_menu(self):
        from menu import InterfazAdministrativa
        self.menu = InterfazAdministrativa()
        self.menu.showMaximized()
        self.close()

    # --- Cerrar sesión ---
    def cerrar_sesion(self):
        from login import InicioSesionDocente
        Sesion.cerrar_sesion()
        self.login = InicioSesionDocente()
        self.login.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = ReporteAsistencias()
    ventana.show()
    sys.exit(app.exec())
