# Importa utilidades del sistema
import sys

# Importa widgets y layouts necesarios de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QFrame, QStackedLayout, QMessageBox
)

# Importa QPixmap para manejo del logo institucional
from PyQt6.QtGui import QPixmap

# Importa utilidades base de Qt
from PyQt6.QtCore import Qt


# Importa funciones de lógica relacionadas con equipos
from modules.equipos import (
    agregar_equipo, actualizar_estado, obtener_equipos, generar_proximo_codigo,
    obtener_marcas, obtener_procesadores, obtener_rams, obtener_discos
)

# Importa el control de sesión
from modules.sesion import Sesion


class GestionEquipos(QWidget):
    def __init__(self):
        super().__init__()

        if not Sesion.esta_autenticado():
            QMessageBox.critical(self, "Acceso denegado", "⚠ Debe iniciar sesión para acceder a Gestión de Equipos.")
            sys.exit(0)

        self.setWindowTitle("Gestión de Equipos - Institución Educativa del Sur")
        self.resize(1400, 750)
        self.centrar_ventana()
        self.init_ui()

    def centrar_ventana(self):
        screen = QApplication.primaryScreen().availableGeometry()
        tamaño = self.frameGeometry()
        tamaño.moveCenter(screen.center())
        self.move(tamaño.topLeft())

    def init_ui(self):
        # ---------------------- ESTILOS ----------------------
        self.setStyleSheet("""
            QWidget { background-color: #0D1B2A; color: white; font-family: Arial; font-size: 14px; }
            QLabel#tituloColegio { font-size: 36px; font-weight: bold; color: #E3F2FD; }
            QLabel#lemaColegio { font-size: 18px; color: #aaa; }
            QPushButton { border-radius: 6px; padding: 6px 12px; font-weight: bold; color: white; }
            QPushButton#btnMenu { background-color: rgba(21,101,192,0.6); }
            QPushButton#btnInfo { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnAgregar { background-color: rgba(21,101,192,0.60); }
            QPushButton#btnActualizar { background-color: rgba(21,101,192,0.60); }
            QPushButton:hover { opacity: 0.85; }
            QLineEdit, QComboBox { 
                border: 1px solid #1565C0; border-radius: 5px; padding: 4px; background-color: #2A2A2A; color: white;
            }
            QTableWidget {
                border: none; border-radius: 10px; background-color: #1E293B; 
                alternate-background-color: #243447; gridline-color: transparent; 
                selection-background-color: #1976D2; selection-color: white; font-size: 14px;
            }
            QHeaderView::section {
                background-color: rgba(13,71,161,0.8); color: white; font-size: 15px; font-weight: bold; border: none; padding: 10px; border-radius: 6px;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.05); }
            QTableWidget::item:hover { background-color: rgba(25,118,210,0.3); color: #E3F2FD; }
            QPushButton#btnActualizar { background-color: rgba(21,101,192,0.60); border-radius: 6px; font-weight: bold; color: white; padding: 4px 10px; }
            QPushButton#btnActualizar:hover { background-color: rgba(21,101,192,0.75); }
            QPushButton#btnAgregar:hover { background-color: rgba(21,101,192,0.75); }
        """)

        # ---------------------- HEADER ----------------------
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
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

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addWidget(titulo_colegio)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        linea_header = QFrame()
        linea_header.setFrameShape(QFrame.Shape.HLine)
        linea_header.setStyleSheet("color: #444;")

        # ---------------------- SECCIÓN AGREGAR ----------------------
        lbl_agregar = QLabel("AGREGAR EQUIPO")
        lbl_agregar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_agregar.setStyleSheet("font-size: 24px; font-weight: bold; color: #E3F2FD; margin: 10px;")

        # Código (autogenerado)
        lbl_codigo = QLabel("Código:")
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(generar_proximo_codigo())
        self.txt_codigo.setReadOnly(True)
        self.txt_codigo.setStyleSheet("background-color: #2A2A2A; color: white;")

        # Estado
        lbl_estado = QLabel("Estado:")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["disponible", "dañado", "otro"])

        # Marca (escrito en mayúsculas)
        lbl_marca = QLabel("Marca:")
        self.txt_marca = QLineEdit()
        self.txt_marca.setPlaceholderText("DELL")
        self.txt_marca.textChanged.connect(lambda: self.txt_marca.setText(self.txt_marca.text().upper()))

        # Modelo (escrito)
        lbl_modelo = QLabel("Modelo:")
        self.txt_modelo = QLineEdit()

        # Procesador (escrito en mayúsculas)
        lbl_procesador = QLabel("Procesador:")
        self.txt_procesador = QLineEdit()
        self.txt_procesador.setPlaceholderText("INTEL CORE I5")
        self.txt_procesador.textChanged.connect(lambda: self.txt_procesador.setText(self.txt_procesador.text().upper()))

        # RAM (solo números + GB)
        lbl_ram = QLabel("RAM:")
        self.txt_ram = QLineEdit()
        self.txt_ram.setPlaceholderText("8")

        # Disco (escrito en mayúsculas)
        lbl_disco = QLabel("Disco:")
        self.txt_disco = QLineEdit()
        self.txt_disco.setPlaceholderText("SSD 512 GB")
        self.txt_disco.textChanged.connect(lambda: self.txt_disco.setText(self.txt_disco.text().upper()))

        # Serial
        lbl_serial = QLabel("Serial:")
        self.txt_serial = QLineEdit()

        # Año
        lbl_anio = QLabel("Año:")
        self.txt_anio = QLineEdit()
        self.txt_anio.setPlaceholderText("2024")

        # Observaciones
        lbl_obs = QLabel("Obs:")
        self.txt_obs = QLineEdit()

        # Botón agregar
        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.clicked.connect(self.agregar_equipo_ui)

        # Layout formulario (dos filas)
        fila1 = QHBoxLayout()
        fila1.addWidget(lbl_codigo)
        fila1.addWidget(self.txt_codigo)
        fila1.addSpacing(10)
        fila1.addWidget(lbl_estado)
        fila1.addWidget(self.cmb_estado)
        fila1.addSpacing(10)
        fila1.addWidget(lbl_marca)
        fila1.addWidget(self.txt_marca)
        fila1.addSpacing(10)
        fila1.addWidget(lbl_modelo)
        fila1.addWidget(self.txt_modelo)
        fila1.addSpacing(10)
        fila1.addWidget(lbl_procesador)
        fila1.addWidget(self.txt_procesador)

        fila2 = QHBoxLayout()
        fila2.addWidget(lbl_ram)
        fila2.addWidget(self.txt_ram)
        fila2.addSpacing(10)
        fila2.addWidget(lbl_disco)
        fila2.addWidget(self.txt_disco)
        fila2.addSpacing(10)
        fila2.addWidget(lbl_serial)
        fila2.addWidget(self.txt_serial)
        fila2.addSpacing(10)
        fila2.addWidget(lbl_anio)
        fila2.addWidget(self.txt_anio)
        fila2.addSpacing(10)
        fila2.addWidget(lbl_obs)
        fila2.addWidget(self.txt_obs)
        fila2.addSpacing(20)
        fila2.addWidget(btn_agregar)

        agregar_layout = QVBoxLayout()
        agregar_layout.addLayout(fila1)
        agregar_layout.addLayout(fila2)

        frame_agregar = QFrame()
        frame_agregar.setLayout(agregar_layout)
        frame_agregar.setStyleSheet("background-color: #1E293B; border-radius: 10px; padding: 15px;")

        # ---------------------- TABLA EQUIPOS ----------------------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Estado", "Marca", "Modelo", "Procesador", "RAM", "Disco", "Serial", "Acciones"
        ])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(50)

        header = self.tabla.horizontalHeader()
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(8, 150)

        lbl_inicial = QLabel("Agrega un equipo para mostrar resultados")
        lbl_inicial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_inicial.setStyleSheet("font-size: 16px; color: #aaa;")

        lbl_no_resultados = QLabel("No hay equipos")
        lbl_no_resultados.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_no_resultados.setStyleSheet("font-size: 16px; color: #aaa;")

        self.stack_resultados = QStackedLayout()
        self.stack_resultados.addWidget(lbl_inicial)
        self.stack_resultados.addWidget(self.tabla)
        self.stack_resultados.addWidget(lbl_no_resultados)
        self.stack_resultados.setCurrentIndex(0)

        # ---------------------- MAIN LAYOUT ----------------------
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(linea_header)
        main_layout.addWidget(lbl_agregar)
        main_layout.addWidget(frame_agregar)
        main_layout.addLayout(self.stack_resultados)
        self.setLayout(main_layout)

        self.cargar_equipos_ui()

    # ---------------------- FUNCIONES ----------------------
    def agregar_equipo_ui(self):
        estado = self.cmb_estado.currentText()
        marca = self.txt_marca.text().strip().upper()
        modelo = self.txt_modelo.text().strip()
        procesador = self.txt_procesador.text().strip().upper()
        ram = self.txt_ram.text().strip() + " GB" if self.txt_ram.text().strip() else ""
        disco = self.txt_disco.text().strip().upper()
        serial = self.txt_serial.text().strip()
        anio = self.txt_anio.text().strip()
        obs = self.txt_obs.text().strip()

        try:
            anio = int(anio) if anio else None
        except:
            anio = None

        if agregar_equipo(estado, marca, modelo, procesador, ram, disco, serial, anio, obs):
            self.cargar_equipos_ui()
            self.limpiar_campos()
            self.txt_codigo.setText(generar_proximo_codigo())
            QMessageBox.information(self, "Éxito", "Equipo agregado correctamente")
        else:
            QMessageBox.critical(self, "Error", "No se pudo agregar el equipo")

    def cargar_equipos_ui(self):
        equipos = obtener_equipos()
        self.tabla.setRowCount(len(equipos))

        if equipos:
            self.stack_resultados.setCurrentIndex(1)
        else:
            self.stack_resultados.setCurrentIndex(2)

        for fila, eq in enumerate(equipos):
            codigo, estado, marca, modelo, procesador, ram, disco, serial = eq
            
            item_codigo = QTableWidgetItem(codigo)
            item_codigo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(fila, 0, item_codigo)

            combo_estado = QComboBox()
            combo_estado.addItems(["disponible", "dañado", "otro"])
            combo_estado.setCurrentText(estado)
            self.tabla.setCellWidget(fila, 1, combo_estado)

            items = [marca, modelo, procesador, ram, disco, serial]
            for col, texto in enumerate(items, start=2):
                item = QTableWidgetItem(texto if texto else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, col, item)

            btn_actualizar = QPushButton("Actualizar")
            btn_actualizar.setObjectName("btnActualizar")
            btn_actualizar.clicked.connect(lambda _, f=fila: self.actualizar_estado_ui(f))
            self.tabla.setCellWidget(fila, 8, btn_actualizar)

    def actualizar_estado_ui(self, fila):
        from PyQt6.QtWidgets import QInputDialog, QLineEdit
        codigo = self.tabla.item(fila, 0).text()
        combo = self.tabla.cellWidget(fila, 1)
        nuevo_estado = combo.currentText()
        
        # Siempre pedir descripción al cambiar estado
        descripcion, ok = QInputDialog.getText(
            self, f"Cambiar estado a {nuevo_estado}",
            "Descripción del cambio:",
            QLineEdit.EchoMode.Normal
        )
        if not ok:
            return  # Cancelar si el usuario presiona Cancel
        if not descripcion:
            descripcion = ""

        actualizar_estado(codigo, nuevo_estado, descripcion)
        self.cargar_equipos_ui()

    def limpiar_campos(self):
        self.txt_modelo.clear()
        self.txt_marca.clear()
        self.txt_procesador.clear()
        self.txt_ram.clear()
        self.txt_disco.clear()
        self.txt_serial.clear()
        self.txt_anio.clear()
        self.txt_obs.clear()

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

    if not Sesion.esta_autenticado():
        QMessageBox.critical(None, "Acceso denegado", "⚠ Debe iniciar sesión para usar esta ventana.")
        sys.exit(0)

    ventana = GestionEquipos()
    ventana.show()
    sys.exit(app.exec())