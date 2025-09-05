import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QGraphicsDropShadowEffect, QFrame
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt

# Importa funciones del backend (módulo equipos)
from modules.equipos import agregar_equipo, actualizar_estado, obtener_equipos, generar_proximo_codigo


# ==========================================================
#   CLASE: GestionEquipos
#   Función: Gestionar equipos del aula de informática
#   - Agregar nuevos equipos con código automático
#   - Editar estado de equipos ya registrados
#   - Mostrar tabla con todos los equipos
# ==========================================================
class GestionEquipos(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Equipos - Institución Educativa del Sur")
        self.resize(1000, 600)
        self.init_ui()

    # ------------------------------------------------------
    # Construcción de la interfaz gráfica
    # ------------------------------------------------------
    def init_ui(self):
        # Estilos globales (CSS)
        self.setStyleSheet("""
    QWidget { background-color: white; font-family: Arial; font-size: 14px; }
    QLabel { font-weight: bold; color: black; }
    QFrame#frameAgregar QLabel { color: #333333; background-color: transparent; font-weight: bold; }

    QPushButton { border-radius: 6px; padding: 6px 12px; font-weight: bold; color: white; }
    QPushButton#btnMenu { background-color: #C62828; }
    QPushButton#btnInfo { background-color: #1565C0; }
    QPushButton#btnAgregar {
        background-color: white; color: black; font-size: 28px; font-weight: bold; border: 2px solid #1565C0;
    }
    QPushButton#btnAgregar:hover {
        background-color: #E3F2FD; border-color: #0D47A1; color: #0D47A1;
    }
    QPushButton#btnActualizar { background-color: #1565C0; }
    QPushButton:hover { opacity: 0.85; }

    QLineEdit { border: 1px solid #1565C0; border-radius: 5px; padding: 4px; background-color: white; color: black; }

    /* ComboBox */
    QComboBox {
        border: 1px solid #1565C0;
        border-radius: 5px;
        padding: 4px;
        background-color: white;
        color: black;
        min-height: 28px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 1px solid #1565C0;
        background-color: #f0f0f0;
    }
    /* Flechita ▼ */
    QComboBox::down-arrow {
        width: 0;
        height: 0;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 8px solid black;
        margin-right: 6px;
    }
    /* Lista desplegable */
    QComboBox QAbstractItemView {
        border: 1px solid #1565C0;
        background-color: white;
        color: black;   /* ✅ ahora las letras siempre negras */
        selection-background-color: #1565C0;
        selection-color: white;
        font-size: 14px;
    }

    QTableWidget { border: 1px solid #ccc; gridline-color: #ccc; background-color: white; }
    QHeaderView::section { background-color: #1565C0; color: white; font-weight: bold; padding: 4px; }
    QFrame#frameAgregar { background-color: #f5f5f5; border-radius: 10px; padding: 15px; }
""")

        # --- Encabezado superior ---
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)  # Acción para volver al menú principal

        btn_info = QPushButton("MÁS INFORMACIÓN")
        btn_info.setObjectName("btnInfo")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        # --- Sección agregar equipos ---
        lbl_agregar = QLabel("AGREGAR EQUIPOS")
        lbl_agregar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_agregar.setStyleSheet("color: #C62828; font-size: 20px; font-weight: bold; margin-bottom: 10px;")

        lbl_codigo = QLabel("Código:")
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(generar_proximo_codigo())  # Código autogenerado
        self.txt_codigo.setReadOnly(True)

        lbl_estado = QLabel("Estado:")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["disponible", "dañado"])  # Opciones de estado

        # Botón para agregar equipo
        btn_agregar = QPushButton("+")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.setFixedSize(50, 50)

        sombra_btn = QGraphicsDropShadowEffect()
        sombra_btn.setBlurRadius(15)
        sombra_btn.setYOffset(2)
        sombra_btn.setColor(QColor(0, 0, 0, 120))
        btn_agregar.setGraphicsEffect(sombra_btn)

        btn_agregar.clicked.connect(self.agregar_equipo_ui)

        # Layout agregar
        agregar_layout = QHBoxLayout()
        agregar_layout.addStretch()
        agregar_layout.addWidget(lbl_codigo)
        agregar_layout.addWidget(self.txt_codigo)
        agregar_layout.addSpacing(10)
        agregar_layout.addWidget(lbl_estado)
        agregar_layout.addWidget(self.cmb_estado)
        agregar_layout.addSpacing(20)
        agregar_layout.addWidget(btn_agregar)
        agregar_layout.addStretch()

        frame_agregar = QFrame()
        frame_agregar.setObjectName("frameAgregar")
        frame_agregar.setLayout(agregar_layout)

        sombra_frame = QGraphicsDropShadowEffect()
        sombra_frame.setBlurRadius(20)
        sombra_frame.setYOffset(3)
        sombra_frame.setColor(QColor(0, 0, 0, 100))
        frame_agregar.setGraphicsEffect(sombra_frame)

        # --- Barra edición ---
        barra_editar = QLabel("EDITAR ESTADO EQUIPOS")
        barra_editar.setStyleSheet("background-color: #1565C0; color: white; font-weight: bold; padding: 6px;")
        barra_editar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Tabla ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Código", "Estado", "Acciones"])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # no editable
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        # Layout principal
        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(lbl_agregar)
        layout.addWidget(frame_agregar)
        layout.addWidget(barra_editar)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        # Cargar equipos BD
        self.cargar_equipos_ui()

    def agregar_equipo_ui(self):
        estado = self.cmb_estado.currentText()
        if agregar_equipo(estado):
            self.cargar_equipos_ui()
            self.txt_codigo.setText(generar_proximo_codigo())

    def cargar_equipos_ui(self):
        equipos = obtener_equipos()
        self.tabla.setRowCount(len(equipos))

        for fila, (codigo, estado_actual) in enumerate(equipos):
            # Columna 1: Código
            item_codigo = QTableWidgetItem(codigo)
            item_codigo.setForeground(QColor("black"))
            self.tabla.setItem(fila, 0, item_codigo)

            # Columna 2: Estado
            combo_estado = QComboBox()
            opciones = ["disponible", "dañado"]
            combo_estado.addItems(opciones)
            combo_estado.setCurrentText(estado_actual)
            self.tabla.setCellWidget(fila, 1, combo_estado)

            # Columna 3: Botón
            btn_actualizar = QPushButton("Actualizar Estado")
            btn_actualizar.setObjectName("btnActualizar")
            btn_actualizar.clicked.connect(lambda _, f=fila: self.actualizar_estado_ui(f))
            self.tabla.setCellWidget(fila, 2, btn_actualizar)

    def actualizar_estado_ui(self, fila):
        codigo = self.tabla.item(fila, 0).text()
        combo = self.tabla.cellWidget(fila, 1)
        nuevo_estado = combo.currentText()
        actualizar_estado(codigo, nuevo_estado)
        self.cargar_equipos_ui()

    def volver_menu(self):
        from menu import InterfazAdministrativa
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.show()
        self.close()


# ==========================================================
#   EJECUCIÓN DIRECTA
# ==========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = GestionEquipos()
    ventana.show()
    sys.exit(app.exec())
