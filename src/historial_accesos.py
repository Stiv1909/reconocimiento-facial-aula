# Importa utilidades del sistema
import sys

# Importa widgets y layouts necesarios de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QDialog, QMessageBox, QStackedLayout, QGraphicsDropShadowEffect
)

# Importa utilidades gráficas para imágenes y color
from PyQt6.QtGui import QPixmap, QColor

# Importa utilidades base de Qt
from PyQt6.QtCore import Qt

# Importa la función de búsqueda del historial desde la lógica
from modules.historial_logic import buscar_historial

# Si usas Sesion como en EditarEstudiantes, mantenlo
from modules.sesion import Sesion



class HistorialAccesos(QWidget):
    def __init__(self):
        # Inicializa la clase base QWidget
        super().__init__()


        # Mantengo la verificación de sesión igual que en EditarEstudiantes
        if not Sesion.esta_autenticado():
            # Si no hay sesión activa, deniega acceso y cierra la ventana
            QMessageBox.critical(self, "Acceso denegado", "❌ Debes iniciar sesión para acceder a esta ventana.")
            self.close()
            return


        # Configura título, modo de pantalla y construcción de interfaz
        self.setWindowTitle("Historial de Accesos - Institución Educativa del Sur")
        self.showFullScreen()
        self.centrar_ventana()
        self.init_ui()


    def centrar_ventana(self):
        # Obtiene el área disponible de la pantalla principal
        screen = QApplication.primaryScreen().availableGeometry()

        # Obtiene la geometría actual de la ventana
        geom = self.frameGeometry()

        # Centra la ventana respecto a la pantalla
        geom.moveCenter(screen.center())
        self.move(geom.topLeft())


    def init_ui(self):
        # Aplica estilos visuales globales a la ventana
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


        # Crea y carga el logo institucional
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiqueta con el nombre y lema de la institución usando HTML
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
        btn_menu.clicked.connect(self.volver_menu)   # conecta como en tu app si lo necesitas


        # Botón para cerrar el programa completo
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(lambda: sys.exit(0))


        # Layout superior del encabezado
        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addWidget(titulo_colegio)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)


        # Separador horizontal bajo el encabezado
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # -------- Sección: Consultar Historial --------
        # Título de la sección principal
        seccion_titulo = QLabel("Consultar Historial")
        seccion_titulo.setObjectName("seccionTitulo")
        seccion_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Tarjeta contenedora con sombra (misma estética)
        tarjeta = QFrame()
        tarjeta.setStyleSheet("background-color: #111827; border-radius: 12px;")

        # Aplica sombra a la tarjeta contenedora
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(26)
        sombra.setColor(QColor(0, 0, 0, 180))
        sombra.setOffset(0, 6)
        tarjeta.setGraphicsEffect(sombra)


        # Layout principal interno de la tarjeta
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(18, 18, 18, 18)
        tarjeta_layout.setSpacing(12)


        # --- Filtros mejorados visualmente ---
        # Contenedor visual para los filtros
        filtros_container = QFrame()
        filtros_container.setStyleSheet("background-color: #0F172A; border-radius: 10px;")

        # Layout vertical que agrupa las dos filas de filtros
        filtros_layout = QVBoxLayout(filtros_container)
        filtros_layout.setContentsMargins(20, 15, 20, 15)
        filtros_layout.setSpacing(12)


        # --- Fila 1: Estudiante y Grado ---
        fila1 = QHBoxLayout()
        fila1.setSpacing(15)


        # Filtro por estudiante
        lbl_est = QLabel("👤 Estudiante:")
        lbl_est.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.txt_estudiante = QLineEdit()
        self.txt_estudiante.setPlaceholderText("Ingrese nombre o apellido del estudiante...")


        # Filtro por grado
        lbl_grado = QLabel("🏫 Grado:")
        lbl_grado.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.cmb_grado = QComboBox()
        self.cmb_grado.addItems([
            "", "6-1", "6-2", "6-3", "6-4",
            "7-1", "7-2", "7-3", "7-4",
            "8-1", "8-2", "8-3",
            "9-1", "9-2", "9-3",
            "10-1", "10-2", "10-3",
            "11-1", "11-2", "11-3"
        ])
        self.cmb_grado.setFixedWidth(120)


        # Agrega widgets a la primera fila
        fila1.addWidget(lbl_est)
        fila1.addWidget(self.txt_estudiante, 2)
        fila1.addWidget(lbl_grado)
        fila1.addWidget(self.cmb_grado, 1)
        fila1.addStretch()


        # --- Fila 2: Fecha,  Equipo y Estado ---
        fila2 = QHBoxLayout()
        fila2.setSpacing(15)


        # Filtro por fecha
        lbl_fecha = QLabel("📅 Fecha:")
        lbl_fecha.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.txt_fecha = QLineEdit()
        self.txt_fecha.setPlaceholderText("DD/MM/AAAA")
        self.txt_fecha.setFixedWidth(160)


        # Filtro por equipo
        lbl_equipo = QLabel("💻 Equipo:")
        lbl_equipo.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.cmb_equipo = QComboBox()
        self.cmb_equipo.addItems(["", "E-26", "E-27", "E-28", "E-29", "E-30"])
        self.cmb_equipo.setFixedWidth(120)


        # Filtro por estado
        lbl_estado = QLabel("🧍 Estado:")
        lbl_estado.setStyleSheet("color: #E3F2FD; font-weight: bold;")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["", "Estudiante","Ex-alumno"])
        self.cmb_estado.setFixedWidth(180)


        # Botón para ejecutar la búsqueda
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


        # Agrega widgets a la segunda fila
        fila2.addWidget(lbl_fecha)
        fila2.addWidget(self.txt_fecha)
        fila2.addStretch()
        fila2.addWidget(lbl_equipo)
        fila2.addWidget(self.cmb_equipo)
        fila2.addStretch()
        fila2.addWidget(lbl_estado)
        fila2.addWidget(self.cmb_estado)
        fila2.addStretch()
        fila2.addWidget(self.btn_buscar)
        fila2.addStretch()


        # Agregar las filas al layout del contenedor de filtros
        filtros_layout.addLayout(fila1)
        filtros_layout.addLayout(fila2)


        tarjeta_layout.addWidget(filtros_container)


        # --- Área de historial: título + stack (mensaje inicial / tabla / no results) ---
        # Título encima de la tabla
        titulo_tabla = QLabel("Historial")
        titulo_tabla.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_tabla.setStyleSheet("font-size:16px; font-weight:bold; color:#E3F2FD; margin-top:6px;")


        # Tabla con columnas EXACTAS de la maqueta
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Estudiante", "Grado", "Equipo", "Fecha", "Hora-Inicio", "Hora - Fin", "Incidente"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setShowGrid(False)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setStyleSheet("QTableWidget { background-color: #1E293B; }")


        # Mensaje inicial antes de buscar
        lbl_inicial = QLabel("Realiza una búsqueda para mostrar resultados")
        lbl_inicial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_inicial.setStyleSheet("font-size:16px; color:#aaa;")


        # Mensaje cuando no hay registros
        lbl_no = QLabel("No se encontraron registros")
        lbl_no.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_no.setStyleSheet("font-size:16px; color:#aaa;")


        # Stack para alternar entre vista inicial, tabla y sin resultados
        self.stack = QStackedLayout()
        self.stack.addWidget(lbl_inicial)   # 0
        self.stack.addWidget(self.tabla)    # 1
        self.stack.addWidget(lbl_no)        # 2
        self.stack.setCurrentIndex(0)


        # Agrega título y stack a la tarjeta
        tarjeta_layout.addWidget(titulo_tabla)
        tarjeta_layout.addLayout(self.stack)


        # -------- Main layout (encabezado + separador + sección) --------
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(separador)
        main_layout.addWidget(seccion_titulo)
        main_layout.addWidget(tarjeta)


    # Placeholder visual — conecta con tu lógica real
    def buscar_historial_ui(self):
        # Obtiene valores de los filtros de búsqueda
        nombre = self.txt_estudiante.text().strip()
        grado = self.cmb_grado.currentText().strip()
        fecha = self.txt_fecha.text().strip()
        equipo = self.cmb_equipo.currentText().strip()
        estado = self.cmb_estado.currentText().strip()


        # Ejecuta la búsqueda en la capa lógica
        resultados = buscar_historial(nombre, grado, fecha, equipo, estado)


        if not resultados:
            # Si no hay resultados, muestra la vista de "sin resultados"
            self.stack.setCurrentIndex(2)
            self.tabla.setRowCount(0)
            return


        # Si hay resultados, muestra la tabla
        self.stack.setCurrentIndex(1)
        self.tabla.setRowCount(0)


        # Inserta cada fila encontrada en la tabla
        for fila in resultados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for col, valor in enumerate(fila):
                self.tabla.setItem(row, col, QTableWidgetItem(str(valor)))


    def volver_menu(self):
        # Verifica sesión antes de volver al menú
        if not Sesion.esta_autenticado():
            QMessageBox.warning(self, "Sesión requerida", "⚠ Debe iniciar sesión para acceder al menú.")
            return


        # Abre la ventana del menú principal
        from menu import InterfazAdministrativa
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()


# Ejecutar solo en modo standalone (igual patrón de EditarEstudiantes)
if __name__ == "__main__":
    # Crea la aplicación principal
    app = QApplication(sys.argv)

    # controlar sesión exactamente igual que EditarEstudiantes
    if Sesion.esta_autenticado():
        w = HistorialAccesos()
        w.showMaximized()
    else:
        QMessageBox.warning(None, "Sesión requerida", "⚠ Debes iniciar sesión para acceder al sistema.")

    # Inicia el ciclo principal de la aplicación
    sys.exit(app.exec())
