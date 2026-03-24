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
from modules.equipos import agregar_equipo, actualizar_estado, obtener_equipos, generar_proximo_codigo

# Importa el control de sesión
from modules.sesion import Sesion



class GestionEquipos(QWidget):
    def __init__(self):
        # Inicializa la clase base QWidget
        super().__init__()


        # 🔒 Verificar sesión iniciada
        if not Sesion.esta_autenticado():
            QMessageBox.critical(self, "Acceso denegado", "⚠ Debe iniciar sesión para acceder a Gestión de Equipos.")
            sys.exit(0)


        # Configura ventana principal
        self.setWindowTitle("Gestión de Equipos - Institución Educativa del Sur")
        self.resize(1250, 670)
        self.centrar_ventana()
        self.init_ui()


    def centrar_ventana(self):
        # Obtiene el área disponible de la pantalla
        screen = QApplication.primaryScreen().availableGeometry()

        # Obtiene geometría de la ventana y la centra
        tamaño = self.frameGeometry()
        tamaño.moveCenter(screen.center())
        self.move(tamaño.topLeft())


    def init_ui(self):
        # ---------------------- ESTILOS ----------------------
        # Aplica estilos visuales globales de la interfaz
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
        # Crea label para el logo
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Crea etiqueta HTML con nombre y lema de la institución
        titulo_colegio = QLabel(
            "<div style='text-align:left;'>"
            "<p style='font-size:32px; font-weight:bold; color:#E3F2FD; margin:0;'>Institución Educativa del Sur</p>"
            "<p style='font-size:18px; color:#aaa; margin:0;'>Compromiso y Superación</p>"
            "</div>"
        )
        titulo_colegio.setObjectName("tituloColegio")
        titulo_colegio.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)


        # Botón para volver al menú
        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)


        # Botón para cerrar todo el programa
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(lambda: sys.exit(0))


        # Layout horizontal del encabezado
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
        # Título de la sección de agregar equipo
        lbl_agregar = QLabel("AGREGAR EQUIPO")
        lbl_agregar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_agregar.setStyleSheet("font-size: 24px; font-weight: bold; color: #E3F2FD; margin: 10px;")


        # Campo de código autogenerado
        lbl_codigo = QLabel("Código:")
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(generar_proximo_codigo())
        self.txt_codigo.setReadOnly(True)
        self.txt_codigo.setStyleSheet("background-color: #2A2A2A; color: white;")


        # Combo para seleccionar estado inicial del equipo
        lbl_estado = QLabel("Estado:")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["disponible", "dañado"])
        self.cmb_estado.setStyleSheet("""
            QComboBox {
                background-color: #2A2A2A;
                color: white;
            }
            QComboBox QAbstractItemView {
                background-color: #2A2A2A;
                selection-background-color: #1976D2;
                color: white;
            }
        """)


        # Botón para agregar un nuevo equipo
        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.clicked.connect(self.agregar_equipo_ui)


        # Layout horizontal del formulario de agregado
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


        # Frame contenedor para el formulario de agregar
        frame_agregar = QFrame()
        frame_agregar.setLayout(agregar_layout)
        frame_agregar.setStyleSheet("background-color: #1E293B; border-radius: 10px; padding: 15px;")


        # ---------------------- TABLA EQUIPOS ----------------------
        # Tabla principal de equipos
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Código", "Estado", "Acciones"])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(50)


        # Configura cómo se ajustan las columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(2, 180)


        # Mensaje inicial antes de cargar equipos
        lbl_inicial = QLabel("Agrega un equipo para mostrar resultados")
        lbl_inicial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_inicial.setStyleSheet("font-size: 16px; color: #aaa;")


        # Mensaje cuando no existen equipos
        lbl_no_resultados = QLabel("No hay equipos")
        lbl_no_resultados.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_no_resultados.setStyleSheet("font-size: 16px; color: #aaa;")


        # Stack para alternar entre mensaje inicial, tabla y mensaje sin resultados
        self.stack_resultados = QStackedLayout()
        self.stack_resultados.addWidget(lbl_inicial)
        self.stack_resultados.addWidget(self.tabla)
        self.stack_resultados.addWidget(lbl_no_resultados)
        self.stack_resultados.setCurrentIndex(0)


        # ---------------------- LAYOUT PRINCIPAL ----------------------
        # Layout principal de la ventana
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
        # Obtiene el estado seleccionado para el nuevo equipo
        estado = self.cmb_estado.currentText()
        if agregar_equipo(estado):
            # Si se agrega correctamente, recarga la tabla y actualiza el próximo código
            self.cargar_equipos_ui()
            self.txt_codigo.setText(generar_proximo_codigo())
            QMessageBox.information(self, "Éxito", "Equipo agregado correctamente")
        else:
            QMessageBox.critical(self, "Error", "No se pudo agregar el equipo")


    def cargar_equipos_ui(self):
        # Consulta todos los equipos desde la lógica
        equipos = obtener_equipos()
        self.tabla.setRowCount(len(equipos))


        if equipos:
            # Si hay equipos, muestra la tabla
            self.stack_resultados.setCurrentIndex(1)
        else:
            # Si no hay equipos, muestra mensaje correspondiente
            self.stack_resultados.setCurrentIndex(2)


        for fila, (codigo, estado_actual) in enumerate(equipos):
            # Inserta el código del equipo en la columna 0
            item_codigo = QTableWidgetItem(codigo)
            item_codigo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(fila, 0, item_codigo)


            # Inserta un combo para cambiar el estado del equipo
            combo_estado = QComboBox()
            combo_estado.addItems(["disponible", "dañado"])
            combo_estado.setCurrentText(estado_actual)
            self.tabla.setCellWidget(fila, 1, combo_estado)


            # Botón para actualizar el estado del equipo
            btn_actualizar = QPushButton("Actualizar")
            btn_actualizar.setObjectName("btnActualizar")
            btn_actualizar.clicked.connect(lambda _, f=fila: self.actualizar_estado_ui(f))
            self.tabla.setCellWidget(fila, 2, btn_actualizar)


    def actualizar_estado_ui(self, fila):
        # Obtiene el código del equipo desde la fila
        codigo = self.tabla.item(fila, 0).text()

        # Obtiene el combo de estado en esa fila
        combo = self.tabla.cellWidget(fila, 1)
        nuevo_estado = combo.currentText()

        # Actualiza el estado y recarga la tabla
        actualizar_estado(codigo, nuevo_estado)
        self.cargar_equipos_ui()


    def volver_menu(self):
        # Verifica sesión antes de regresar al menú
        if not Sesion.esta_autenticado():
            QMessageBox.warning(self, "Sesión requerida", "⚠ Debe iniciar sesión para acceder al menú.")
            return


        # Abre el menú principal y cierra la ventana actual
        from menu import InterfazAdministrativa
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()



if __name__ == "__main__":
    # Crea la aplicación principal
    app = QApplication(sys.argv)


    if not Sesion.esta_autenticado():
        QMessageBox.critical(None, "Acceso denegado", "⚠ Debe iniciar sesión para usar esta ventana.")
        sys.exit(0)


    # Crea y muestra la ventana de gestión de equipos
    ventana = GestionEquipos()
    ventana.show()
    sys.exit(app.exec())
