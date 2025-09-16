import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QFrame, QStackedLayout, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from modules.equipos import agregar_equipo, actualizar_estado, obtener_equipos, generar_proximo_codigo

class GestionEquipos(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Equipos - Institución Educativa del Sur")
        self.resize(1250, 670)
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
            QPushButton#btnMenu { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnInfo { background-color: rgba(21,101,192,0.60); }
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

        btn_info = QPushButton("MÁS INFORMACIÓN")
        btn_info.setObjectName("btnInfo")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addWidget(titulo_colegio)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        # Línea separadora fina
        linea_header = QFrame()
        linea_header.setFrameShape(QFrame.Shape.HLine)
        linea_header.setStyleSheet("color: #444;")

        # ---------------------- SECCIÓN AGREGAR ----------------------
        lbl_agregar = QLabel("AGREGAR EQUIPO")
        lbl_agregar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_agregar.setStyleSheet("font-size: 24px; font-weight: bold; color: #E3F2FD; margin: 10px;")

        lbl_codigo = QLabel("Código:")
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(generar_proximo_codigo())
        self.txt_codigo.setReadOnly(True)
        self.txt_codigo.setStyleSheet("""
    QLineEdit {
        background-color: #2A2A2A;  /* Gris oscuro */
        color: white;
    }
""")

        lbl_estado = QLabel("Estado:")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["disponible", "dañado"])
        self.cmb_estado.setStyleSheet("""
    QComboBox {
        background-color: #2A2A2A;  /* Gris oscuro */
        color: white;
    }
    QComboBox QAbstractItemView {
        background-color: #2A2A2A;  /* Gris oscuro */
        selection-background-color: #1976D2;
        color: white;
    }
""")

        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.setStyleSheet("""
            QPushButton#btnAgregar {
                background-color: rgba(21,101,192,0.60);
                border-radius: 6px;
                font-weight: bold;
                color: white;
                padding: 6px 12px;
            }
            QPushButton#btnAgregar:hover {
                background-color: rgba(21,101,192,0.75);
            }
        """)
        btn_agregar.clicked.connect(self.agregar_equipo_ui)

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
        frame_agregar.setLayout(agregar_layout)
        frame_agregar.setStyleSheet("background-color: #1E293B; border-radius: 10px; padding: 15px;")

        # ---------------------- TABLA EQUIPOS ----------------------
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Código", "Estado", "Acciones"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(50)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(2, 180)

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

        # ---------------------- LAYOUT PRINCIPAL ----------------------
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(linea_header)
        main_layout.addWidget(lbl_agregar)
        main_layout.addWidget(frame_agregar)
        main_layout.addLayout(self.stack_resultados)
        self.setLayout(main_layout)

        # Cargar equipos de la BD
        self.cargar_equipos_ui()

    # ---------------------- FUNCIONES ----------------------
    def agregar_equipo_ui(self):
        codigo = self.txt_codigo.text().strip()
        estado = self.cmb_estado.currentText()
        if not codigo:
            QMessageBox.warning(self, "Error", "⚠ Código vacío")
            return
        if agregar_equipo(codigo, estado):
            self.cargar_equipos_ui()
            self.txt_codigo.setText(generar_proximo_codigo())
            QMessageBox.information(self, "Éxito", f"Equipo {codigo} agregado correctamente")
        else:
            QMessageBox.critical(self, "Error", "No se pudo agregar el equipo")

    def cargar_equipos_ui(self):
        equipos = obtener_equipos()
        self.tabla.setRowCount(len(equipos))

        if equipos:
            self.stack_resultados.setCurrentIndex(1)
        else:
            self.stack_resultados.setCurrentIndex(2)

        for fila, (codigo, estado_actual) in enumerate(equipos):
            # Código centrado
            item_codigo = QTableWidgetItem(codigo)
            item_codigo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(fila, 0, item_codigo)

            # Estado
            combo_estado = QComboBox()
            combo_estado.addItems(["disponible", "dañado"])
            combo_estado.setCurrentText(estado_actual)
            self.tabla.setCellWidget(fila, 1, combo_estado)

            # Botón actualizar
            btn_actualizar = QPushButton("Actualizar")
            btn_actualizar.setObjectName("btnActualizar")
            btn_actualizar.setStyleSheet("""
                QPushButton#btnActualizar {
                    background-color: rgba(21,101,192,0.60);
                    border-radius: 6px;
                    font-weight: bold;
                    color: white;
                    padding: 4px 10px;
                }
                QPushButton#btnActualizar:hover {
                    background-color: rgba(21,101,192,0.75);
                }
            """)
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = GestionEquipos()
    ventana.show()
    sys.exit(app.exec())
