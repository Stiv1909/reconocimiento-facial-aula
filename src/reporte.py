# Importa utilidades del sistema
import sys

# Importa widgets y layouts necesarios de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QLineEdit, QComboBox, QTextEdit, QMessageBox
)

# Importa utilidades gráficas para imágenes y color
from PyQt6.QtGui import QPixmap, QColor

# Importa constantes base de Qt
from PyQt6.QtCore import Qt

# Importa el control de sesión
from modules.sesion import Sesion

# Importa la función para generar reportes PDF
from modules.reporte_logic import generar_reporte_pdf

# Importa utilidades de sistema de archivos (no usado en este archivo pero disponible)
import os


class ReporteAsistencias(QWidget):
    def __init__(self):
        # Inicializa la clase base QWidget
        super().__init__()

        # Configura la ventana principal
        self.setWindowTitle("Reporte de Asistencias - Institución Educativa del Sur")
        self.resize(1250, 700)
        self.centrar_ventana()

        # Obtiene el usuario actual de la sesión
        self.usuario = Sesion.obtener_usuario()
        if not self.usuario:
            # No hay sesión: cerramos la ventana (redirigir al login)
            self.close()
            return


        # Inicializa la interfaz de usuario
        self.init_ui()


    def centrar_ventana(self):
        # Obtiene la geometría de la pantalla principal
        screen = QApplication.primaryScreen().geometry()

        # Calcula posición para centrar la ventana
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


    def init_ui(self):
        # Aplica estilos visuales generales de la interfaz
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
            QPushButton#btnMenu      { background-color: rgba(21, 101, 192,0.60); }
            QPushButton#btnInfo      { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnGenerar   { background-color: rgba(255,193,7,0.60); color: black; }
            QPushButton#btnDescargar { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton:hover        { opacity: 0.85; }
        """)


        # --- Header ---
        # Crea label para mostrar el logo institucional
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Crea etiqueta con nombre de la institución
        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")

        # Crea etiqueta con el lema de la institución
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")


        # Layout vertical para agrupar nombre y lema
        text_layout = QVBoxLayout()
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        # Botón para volver al menú
        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.abrir_menu)

        # Botón para cerrar el programa
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(QApplication.quit)


        # Layout horizontal del encabezado
        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_menu)
        header.addWidget(btn_info)


        # Línea separadora bajo el encabezado
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # --- Título ---
        # Título principal de la ventana
        titulo = QLabel("Asistencias")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --- Filtros ---
        # Campo de texto para fecha inicial
        self.txt_desde = QLineEdit()
        self.txt_desde.setPlaceholderText("Desde: DD/MM/AAAA")


        # Campo de texto para fecha final
        self.txt_hasta = QLineEdit()
        self.txt_hasta.setPlaceholderText("Hasta: DD/MM/AAAA")


        # Combo para seleccionar el grado
        self.cmb_grado = QComboBox()
        self.cmb_grado.addItems(["6-1", "7-1", "7-3", "8-1", "9-1","9-2","9-3", "10-1", "11-1"])


        # Botón para generar el reporte
        btn_generar = QPushButton("Generar")
        btn_generar.setObjectName("btnGenerar")
        btn_generar.clicked.connect(self.generar_reporte)


        # Layout horizontal de los filtros
        filtros = QHBoxLayout()
        filtros.addWidget(self.txt_desde)
        filtros.addWidget(self.txt_hasta)
        filtros.addWidget(self.cmb_grado)
        filtros.addWidget(btn_generar)


        # --- Previsualización ---
        # Etiqueta para la sección de previsualización
        previsual = QLabel("Previsualización")
        previsual.setAlignment(Qt.AlignmentFlag.AlignCenter)
        previsual.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFD54F;")


        # Caja de texto de solo lectura para mostrar previsualización
        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setPlaceholderText("Visualización del documento de asistencias")


        # Botón para descargar el PDF
        btn_descargar = QPushButton("Descargar PDF")
        btn_descargar.setObjectName("btnDescargar")
        btn_descargar.clicked.connect(self.descargar_pdf)


        # --- Layout principal ---
        # Frame contenedor con sombra
        frame = QFrame()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)


        # Layout vertical del contenido interno
        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addLayout(filtros)
        vbox.addWidget(previsual)
        vbox.addWidget(self.txt_preview)
        vbox.addWidget(btn_descargar, alignment=Qt.AlignmentFlag.AlignCenter)


        # Asigna layout raíz a la ventana
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(frame)


    def generar_reporte(self):
        # Obtiene fechas desde los campos de entrada
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
        # Obtiene contenido de la previsualización
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
        # Abre la interfaz administrativa y cierra la actual
        from menu import InterfazAdministrativa
        self.menu = InterfazAdministrativa()
        self.menu.showMaximized()
        self.close()


    # --- Cerrar sesión ---
    def cerrar_sesion(self):
        # Cierra la sesión actual y vuelve a la pantalla de login
        from login import InicioSesionDocente
        Sesion.cerrar_sesion()
        self.login = InicioSesionDocente()
        self.login.show()
        self.close()


if __name__ == "__main__":
    # Crea la aplicación principal
    app = QApplication(sys.argv)
    ventana = ReporteAsistencias()
    ventana.show()
    sys.exit(app.exec())
