# registrar_incidente_ui.py  (reemplaza el contenido de tu archivo actual)
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QComboBox, QTextEdit, QMessageBox
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt
from datetime import datetime

# lógica: usa solo las funciones que definimos arriba
from modules.incidentes_logic import (
    obtener_equipos_en_uso,
    obtener_estudiante_por_equipo,
    registrar_incidente
)
from modules.sesion import Sesion

class RegistrarIncidente(QWidget):
    def __init__(self):
        super().__init__()
        # Mantengo la verificación de sesión igual que en EditarEstudiantes
        if not Sesion.esta_autenticado():
            QMessageBox.critical(self, "Acceso denegado", "❌ Debes iniciar sesión para acceder a esta ventana.")
            self.close()
            return
        self.setWindowTitle("Registrar Incidente - Institución Educativa del Sur")
        self.showFullScreen()
        self.centrar_ventana()
        self.init_ui()
        # cargar equipos al iniciar
        self.cargar_equipos()

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
            
            QLabel#tituloColegio {
                font-size: 36px;
                font-weight: bold;
                color: #E3F2FD;
            }
            QLabel#subColegio {
                font-size: 18px;
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
            QPushButton#btnMenu     { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton#btnInfo       { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnResumen    { background-color: rgba(255,193,7,0.60); color: black; }
            QPushButton#btnRegistrar  { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton:hover         { opacity: 0.85; }
        """)

        # Header
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo_colegio = QLabel(
            "<div style='text-align:left;'>"
            "<p style='font-size:32px; font-weight:bold; color:#E3F2FD; margin:0;'>Institución Educativa del Sur</p>"
            "<p style='font-size:18px; color:#aaa; margin:0;'>Compromiso y Superación</p>"
            "</div>"
        )
        titulo_colegio.setObjectName("tituloColegio")
        titulo_colegio.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)   

        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(lambda: sys.exit(0))

        header = QHBoxLayout()
        header.addWidget(logo)
        header.addWidget(titulo_colegio)
        header.addStretch()
        header.addWidget(btn_menu)
        header.addWidget(btn_info)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        # Título
        titulo = QLabel("Registrar Incidente")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Sección Incidentes ---
        # combo de equipos (se cargará desde BD)
        self.cmb_equipo = QComboBox()
        self.cmb_equipo.currentIndexChanged.connect(self.on_equipo_changed)

        # etiqueta para mostrar el estudiante asociado al equipo seleccionado
        self.lbl_estudiante = QLabel("Estudiante: —")
        self.lbl_estudiante.setStyleSheet("color: #E3F2FD; font-weight: bold;")

        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Dañado", "Ocupado"])

        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Describe el incidente con detalle...")

        btn_resumen = QPushButton("Generar Resumen")
        btn_resumen.setObjectName("btnResumen")
        btn_resumen.clicked.connect(self.generar_resumen)

        incidente_layout = QVBoxLayout()
        incidente_layout.addWidget(QLabel("Equipo"))
        incidente_layout.addWidget(self.cmb_equipo)
        incidente_layout.addWidget(self.lbl_estudiante)
        incidente_layout.addWidget(QLabel("Estado"))
        incidente_layout.addWidget(self.cmb_estado)
        incidente_layout.addWidget(QLabel("Descripción"))
        incidente_layout.addWidget(self.txt_descripcion)
        incidente_layout.addWidget(btn_resumen, alignment=Qt.AlignmentFlag.AlignRight)

        # --- Sección Resumen ---
        self.txt_resumen = QTextEdit()
        self.txt_resumen.setReadOnly(True)
        self.txt_resumen.setPlaceholderText("Aquí aparecerá el resumen generado...")

        btn_registrar = QPushButton("Registrar Incidente")
        btn_registrar.setObjectName("btnRegistrar")
        btn_registrar.clicked.connect(self.ui_registrar_incidente)

        resumen_layout = QVBoxLayout()
        resumen_layout.addWidget(QLabel("Resumen"))
        resumen_layout.addWidget(self.txt_resumen)
        resumen_layout.addWidget(btn_registrar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Layout principal
        contenido = QHBoxLayout()
        contenido.addLayout(incidente_layout, 1)
        contenido.addLayout(resumen_layout, 1)

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

        # estado: estudiante actual dict (id_matricula, nombres, apellidos) o None
        self.estudiante_actual = None

    # ---------- Integración con lógica ----------
    def cargar_equipos(self):
        """
        Carga el combo con equipos que actualmente están en uso (historial.hora_fin IS NULL)
        """
        equipos = obtener_equipos_en_uso()
        self.cmb_equipo.clear()
        if not equipos:
            self.cmb_equipo.addItem("— No hay equipos en uso —")
            self.cmb_equipo.setEnabled(False)
            self.lbl_estudiante.setText("Estudiante: —")
            self.estudiante_actual = None
            return

        # equipos viene como lista de dicts {'id_equipo': 'E-26'}
        for row in equipos:
            # si row es dict
            if isinstance(row, dict) and "id_equipo" in row:
                self.cmb_equipo.addItem(row["id_equipo"])
            else:
                # si viene como tupla o string, manejarlo
                self.cmb_equipo.addItem(str(row[0]) if isinstance(row, (list, tuple)) else str(row))

        self.cmb_equipo.setEnabled(True)
        # seleccionar primero y forzar mostrar estudiante
        self.on_equipo_changed()

    def on_equipo_changed(self):
        """
        Cuando cambia el equipo seleccionado, consulta quién lo está usando y lo muestra.
        """
        id_equipo = self.cmb_equipo.currentText()
        if not id_equipo or id_equipo.startswith("—"):
            self.lbl_estudiante.setText("Estudiante: —")
            self.estudiante_actual = None
            return

        estudiante = obtener_estudiante_por_equipo(id_equipo)
        if estudiante:
            nombre = f"{estudiante.get('nombres','')} {estudiante.get('apellidos','')}".strip()
            self.lbl_estudiante.setText(f"Estudiante: {nombre}")
            # guardamos id_matricula para registrar luego
            self.estudiante_actual = {
                "id_matricula": estudiante.get("id_matricula"),
                "id_estudiante": estudiante.get("id_estudiante"),
                "nombres": estudiante.get("nombres"),
                "apellidos": estudiante.get("apellidos")
            }
        else:
            self.lbl_estudiante.setText("Estudiante: No hay estudiante activo en este equipo")
            self.estudiante_actual = None

    def generar_resumen(self):
        """
        Genera el resumen con formato narrativo, usando el estudiante actual si está disponible.
        """
        id_equipo = self.cmb_equipo.currentText()
        estado = self.cmb_estado.currentText()
        descripcion = self.txt_descripcion.toPlainText().strip()

        if not descripcion:
            QMessageBox.warning(self, "Descripción vacía", "⚠ Debes escribir una descripción del incidente.")
            return

        if not id_equipo or id_equipo.startswith("—"):
            QMessageBox.warning(self, "Equipo inválido", "⚠ Selecciona un equipo válido.")
            return

        if self.estudiante_actual:
            nombre_est = f"{self.estudiante_actual.get('nombres','')} {self.estudiante_actual.get('apellidos','')}".strip()
        else:
            nombre_est = "—"

        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        hora_actual = datetime.now().strftime("%H:%M:%S")

        resumen = (
            f"El equipo #{id_equipo} tuvo el siguiente incidente:\n"
            f"{descripcion}\n\n"
            f"Lo cual ocurrió a las {hora_actual} del día {fecha_actual}, "
            f"en el momento que el estudiante {nombre_est} se encontraba haciendo uso del mismo."
        )

        self.txt_resumen.setText(resumen)

    def ui_registrar_incidente(self):
        """
        Handler del botón Registrar Incidente: valida y llama a registrar_incidente()
        """
        descripcion = self.txt_descripcion.toPlainText().strip()
        id_equipo = self.cmb_equipo.currentText()

        if not descripcion:
            QMessageBox.warning(self, "Descripción vacía", "⚠ Debes escribir una descripción del incidente.")
            return

        if not id_equipo or id_equipo.startswith("—"):
            QMessageBox.warning(self, "Equipo inválido", "⚠ Selecciona un equipo válido.")
            return

        if not self.estudiante_actual or not self.estudiante_actual.get("id_matricula"):
            QMessageBox.warning(self, "Sin estudiante", "⚠ No hay un estudiante asociado al equipo seleccionado.")
            return

        id_matricula = self.estudiante_actual["id_matricula"]

        nuevo_estado = self.cmb_estado.currentText()
        success, message = registrar_incidente(id_matricula, id_equipo, descripcion, nuevo_estado)

        if success:
            QMessageBox.information(self, "Incidente registrado", f"✅ {message}")
            # limpiar UI y recargar equipos (si acaso el historial cambió)
            self.txt_descripcion.clear()
            self.txt_resumen.clear()
            self.cargar_equipos()
        else:
            QMessageBox.warning(self, "Error al registrar", f"❌ {message}")

    def volver_menu(self):
        if not Sesion.esta_autenticado():
            QMessageBox.warning(self, "Sesión requerida", "⚠ Debe iniciar sesión para acceder al menú.")
            return

        from menu import InterfazAdministrativa
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = RegistrarIncidente()
    ventana.show()
    sys.exit(app.exec())
