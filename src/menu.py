import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QToolButton, QSizePolicy, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QPixmap, QColor
from PyQt6.QtCore import Qt, QSize

# Importa tus ventanas
from editar_estudiante import EditarEstudiantes
from gestion_equipos import GestionEquipos
from registro_docente import RegistroDocente
from registro_estudiante import RegistroEstudiantes


# ==========================================================
#   CLASE: InterfazAdministrativa
#   Función: Ventana principal (menú administrativo)
#   - Muestra opciones del sistema con iconos
#   - Acceso a ventanas de gestión (docentes, estudiantes, equipos, etc.)
# ==========================================================
class InterfazAdministrativa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interfaz Administrativa - Institución Educativa del Sur")
        self.resize(1000, 650)
        self.centrar_ventana()  # Centrar ventana al iniciar
        self.init_ui()

    # ------------------------------------------------------
    # Método: centrar_ventana
    # Descripción: Posiciona la ventana en el centro de la pantalla
    # ------------------------------------------------------
    def centrar_ventana(self):
        screen = QApplication.primaryScreen().availableGeometry()
        tamaño = self.frameGeometry()
        tamaño.moveCenter(screen.center())
        self.move(tamaño.topLeft())

    # ------------------------------------------------------
    # Método: init_ui
    # Descripción: Construye toda la interfaz gráfica
    # ------------------------------------------------------
    def init_ui(self):
        # Estilos globales (CSS)
        self.setStyleSheet("""
            QWidget { background-color: white; color: black; font-family: Arial; font-size: 14px; }
            QPushButton {
                border-radius: 6px; padding: 6px 12px; font-weight: bold; color: white;
            }
            QPushButton#btnSesion { background-color: #C62828; }
            QPushButton#btnInfo { background-color: #1565C0; }
            QPushButton:hover { opacity: 0.85; }
            QLabel#titulo { font-size: 22px; font-weight: bold; color: #C62828; }
            QLabel#subtitulo { font-size: 14px; color: black; }
            QToolButton {
                background-color: white; border: 2px solid #ddd; border-radius: 12px;
                padding: 12px; color: black; font-size: 13px;
            }
            QToolButton:hover { border-color: #1565C0; background-color: #E3F2FD; }
            QToolTip { background-color: #333; color: white; border-radius: 5px;
                       padding: 5px; font-size: 12px; }
        """)

        # ------------------------------------------------------
        # Encabezado superior (logo + botones de sesión/info)
        # ------------------------------------------------------
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(
                70, 70, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_sesion = QPushButton("CREAR SESIÓN")
        btn_sesion.setObjectName("btnSesion")

        btn_info = QPushButton("MÁS INFORMACIÓN")
        btn_info.setObjectName("btnInfo")

        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addStretch()
        header_layout.addWidget(btn_sesion)
        header_layout.addWidget(btn_info)

        # Línea separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #ccc;")

        # ------------------------------------------------------
        # Títulos principales
        # ------------------------------------------------------
        titulo = QLabel("Sistema de gestión de equipos")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitulo = QLabel("Por favor seleccione la acción que desea realizar")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ------------------------------------------------------
        # Botones de acciones (menú central con iconos)
        # ------------------------------------------------------
        acciones = [
            ("Registrar Docente", "src/icons/docente.png", "Registrar Docentes nuevos en el sistema"),
            ("Dar Ingreso a Estudiantes", "src/icons/ingreso.png", "Asignar equipos e ingresar estudiantes"),
            ("Dar Salida a Estudiantes", "src/icons/salida.png", "Liberar equipos y dar salida a estudiantes"),
            ("Editar Estudiantes", "src/icons/editar_est.png", "Modificar la información de estudiantes"),
            ("Registrar Estudiantes", "src/icons/estudiante.png", "Registrar Estudiantes nuevos en el sistema"),
            ("Gestionar Equipos", "src/icons/equipos.png", "Registrar equipos o cambiar estado"),
            ("Registrar Incidente", "src/icons/incidente.png", "Registrar novedades sobre equipos"),
            ("Consultar Historial de Accesos", "src/icons/listar.png", "Consultar histórico de ingresos"),
            ("Generación de Asistencia", "src/icons/asis.png", "Descargar asistencia en PDF")
        ]

        grid = QGridLayout()
        grid.setSpacing(25)

        for i, (texto, icono, tooltip) in enumerate(acciones):
            # Crear botón de acción con ícono + texto
            btn = QToolButton()
            btn.setIcon(QIcon(icono))
            btn.setIconSize(QSize(64, 64))
            btn.setText(texto)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setToolTip(tooltip)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # Conectar botones a sus ventanas
            if texto == "Gestionar Equipos":
                btn.clicked.connect(self.abrir_gestion_equipos)
            elif texto == "Editar Estudiantes":
                btn.clicked.connect(self.abrir_editar_estudiantes)
            elif texto == "Registrar Docente":
                btn.clicked.connect(self.abrir_registrar_docente)
            elif texto == "Registrar Estudiantes":
                btn.clicked.connect(self.abrir_registrar_estudiantes)

            # Efecto de sombra (para resaltar)
            sombra = QGraphicsDropShadowEffect()
            sombra.setBlurRadius(15)
            sombra.setXOffset(0)
            sombra.setYOffset(3)
            sombra.setColor(QColor(0, 0, 0, 80))
            btn.setGraphicsEffect(sombra)

            # Agregar botón a la cuadrícula
            grid.addWidget(btn, i // 5, i % 5)

        # ------------------------------------------------------
        # Layout principal
        # ------------------------------------------------------
        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(separador)
        main_layout.addSpacing(10)
        main_layout.addWidget(titulo)
        main_layout.addWidget(subtitulo)
        main_layout.addSpacing(20)
        main_layout.addLayout(grid)

        self.setLayout(main_layout)

    # ------------------------------------------------------
    # Métodos: abrir interfaces secundarias
    # ------------------------------------------------------
    def abrir_gestion_equipos(self):
        self.ventana_equipos = GestionEquipos()
        self.ventana_equipos.show()
        self.close()

    def abrir_editar_estudiantes(self):
        self.ventana_editar = EditarEstudiantes()
        self.ventana_editar.show()
        self.close()

    def abrir_registrar_docente(self):
        self.ventana_docente = RegistroDocente()
        self.ventana_docente.show()
        self.close()

    def abrir_registrar_estudiantes(self):
        self.ventana_estudiante = RegistroEstudiantes()
        self.ventana_estudiante.show()
        self.close()


# ==========================================================
#   EJECUCIÓN DIRECTA
# ==========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = InterfazAdministrativa()
    ventana.show()
    sys.exit(app.exec())
