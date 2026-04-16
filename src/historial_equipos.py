# historial_equipos.py
# Ventana para consultar el historial de equipos (altas, bajas, cambios de estado)

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QStackedLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt

from modules.historial_equipos_logic import buscar_historial_equipos
from modules.equipos import obtener_todos_equipos, obtener_estados
from modules.sesion import Sesion


class HistorialEquipos(QWidget):
    def __init__(self):
        super().__init__()

        if not Sesion.esta_autenticado():
            QMessageBox.critical(self, "Acceso denegado", "❌ Debes iniciar sesión para acceder a esta ventana.")
            self.close()
            return

        self.setWindowTitle("Historial de Equipos - Institución Educativa del Sur")
        self.showFullScreen()
        self.centrar_ventana()
        self.init_ui()

    def centrar_ventana(self):
        screen = QApplication.primaryScreen().availableGeometry()
        geom = self.frameGeometry()
        geom.moveCenter(screen.center())
        self.move(geom.topLeft())

    def init_ui(self):
        self.setStyleSheet("""
    QWidget {
        background-color: #0D1B2A;
        color: white;
        font-family: Arial;
        font-size: 14px;
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
    QLabel#seccionTitulo {
        font-size: 22px;
        font-weight: bold;
        color: #E3F2FD;
        margin: 10px 0;
    }
    QPushButton {
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: bold;
        color: white;
    }
    QPushButton#btnMenu { background-color: rgba(21, 101, 192, 0.60); }
    QPushButton#btnInfo { background-color: rgba(198,40,40,0.60); }
    QPushButton#btnBuscar { background-color: rgba(21, 101, 192, 0.60); font-size: 18px; min-width:44px; min-height:44px; border-radius:22px; }
    QPushButton:hover { opacity: 0.85; }
    QLineEdit, QComboBox {
        border: 1px solid #1565C0;
        border-radius: 5px;
        padding: 6px;
        background-color: #2A2A2A;
        color: white;
    }
    QTableWidget {
        border: none;
        border-radius: 10px;
        background-color: #1E293B;
        alternate-background-color: #243447;
        gridline-color: transparent;
        selection-background-color: #1976D2;
        selection-color: white;
        font-size: 14px;
    }
    QHeaderView::section {
        background-color: rgba(13, 71, 161, 0.8);
        color: white;
        font-size: 15px;
        font-weight: bold;
        border: none;
        padding: 10px;
        border-radius: 6px;
    }
    QTableWidget::item {
        padding: 8px;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    QTableWidget::item:hover {
        background-color: rgba(25,118,210,0.3);
        color: #E3F2FD;
    }
""")

        # Logo
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título colegio
        titulo_colegio = QLabel(
            "<div style='text-align:left;'>"
            "<p style='font-size:32px; font-weight:bold; color:#E3F2FD; margin:0;'>Institución Educativa del Sur</p>"
            "<p style='font-size:18px; color:#aaa; margin:0;'>Compromiso y Superación</p>"
            "</div>"
        )
        titulo_colegio.setObjectName("tituloColegio")
        titulo_colegio.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # Botones
        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)

        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(lambda: sys.exit(0))

        # Header layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addWidget(titulo_colegio)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        # Sección título
        seccion_titulo = QLabel("Historial de Equipos")
        seccion_titulo.setObjectName("seccionTitulo")
        seccion_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tarjeta
        tarjeta = QFrame()
        tarjeta.setStyleSheet("background-color: #111827; border-radius: 12px;")

        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(26)
        sombra.setColor(QColor(0, 0, 0, 180))
        sombra.setOffset(0, 6)
        tarjeta.setGraphicsEffect(sombra)

        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(18, 18, 18, 18)
        tarjeta_layout.setSpacing(12)

        # Filtros
        filtros_container = QFrame()
        filtros_container.setStyleSheet("background-color: #0F172A; border-radius: 10px;")

        filtros_layout = QVBoxLayout(filtros_container)
        filtros_layout.setContentsMargins(20, 15, 20, 15)
        filtros_layout.setSpacing(12)

        # Fila 1
        fila1 = QHBoxLayout()
        fila1.setSpacing(15)

        lbl_equipo = QLabel("💻 Equipo:")
        lbl_equipo.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.cmb_equipo = QComboBox()
        equipos = obtener_todos_equipos()
        equipos_list = [""] + [eq['id_equipo'] for eq in equipos]
        self.cmb_equipo.addItems(equipos_list)
        self.cmb_equipo.setFixedWidth(120)

        lbl_tipo = QLabel("📋 Tipo:")
        lbl_tipo.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["", "alta", "baja", "cambio_estado", "otro"])
        self.cmb_tipo.setFixedWidth(150)

        lbl_fecha = QLabel("📅 Fecha:")
        lbl_fecha.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.txt_fecha = QLineEdit()
        self.txt_fecha.setPlaceholderText("DD/MM/AAAA")
        self.txt_fecha.setFixedWidth(160)

        self.btn_buscar = QPushButton("🔍 Buscar")
        self.btn_buscar.setObjectName("btnBuscar")
        self.btn_buscar.setFixedHeight(48)
        self.btn_buscar.setStyleSheet("""
            QPushButton#btnBuscar {
                background-color: rgba(21, 101, 192, 0.8);
                border-radius: 8px;
                font-size: 18px;
                padding: 10px 20px;
            }
        """)
        self.btn_buscar.clicked.connect(self.buscar_historial_ui)

        fila1.addWidget(lbl_equipo)
        fila1.addWidget(self.cmb_equipo)
        fila1.addStretch()
        fila1.addWidget(lbl_tipo)
        fila1.addWidget(self.cmb_tipo)
        fila1.addStretch()
        fila1.addWidget(lbl_fecha)
        fila1.addWidget(self.txt_fecha)
        fila1.addStretch()
        fila1.addWidget(self.btn_buscar)
        fila1.addStretch()

        filtros_layout.addLayout(fila1)

        tarjeta_layout.addWidget(filtros_container)

        # Tabla
        titulo_tabla = QLabel("Historial de Equipos")
        titulo_tabla.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_tabla.setStyleSheet("font-size:16px; font-weight:bold; color:#E3F2FD; margin-top:6px;")

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "Equipo", "Tipo Acción", "Estado Anterior", "Estado Nuevo", "Descripción", "Fecha", "Hora", "Docente"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setShowGrid(False)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setStyleSheet("QTableWidget { background-color: #1E293B; }")

        # Mensajes
        lbl_inicial = QLabel("Realiza una búsqueda para mostrar resultados")
        lbl_inicial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_inicial.setStyleSheet("font-size:16px; color:#aaa;")

        lbl_no = QLabel("No se encontró historial para este equipo")
        lbl_no.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_no.setStyleSheet("font-size:16px; color:#aaa;")

        # Stack
        self.stack = QStackedLayout()
        self.stack.addWidget(lbl_inicial)
        self.stack.addWidget(self.tabla)
        self.stack.addWidget(lbl_no)
        self.stack.setCurrentIndex(0)

        tarjeta_layout.addWidget(titulo_tabla)
        tarjeta_layout.addLayout(self.stack)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(separador)
        main_layout.addWidget(seccion_titulo)
        main_layout.addWidget(tarjeta)

    def buscar_historial_ui(self):
        equipo = self.cmb_equipo.currentText().strip()
        tipo = self.cmb_tipo.currentText().strip()
        fecha = self.txt_fecha.text().strip()

        resultados = buscar_historial_equipos(equipo, tipo, fecha)

        if not resultados:
            self.stack.setCurrentIndex(2)
            self.tabla.setRowCount(0)
            return

        self.stack.setCurrentIndex(1)
        self.tabla.setRowCount(0)

        for fila in resultados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for col, valor in enumerate(fila):
                self.tabla.setItem(row, col, QTableWidgetItem(str(valor)))

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

    if Sesion.esta_autenticado():
        w = HistorialEquipos()
        w.showMaximized()
    else:
        QMessageBox.warning(None, "Sesión requerida", "⚠ Debes iniciar sesión para acceder al sistema.")

    sys.exit(app.exec())