import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QToolButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QLinearGradient, QPainterPath
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, pyqtProperty

# Importa tus ventanas
from editar_estudiante import EditarEstudiantes
from gestion_equipos import GestionEquipos
from registro_docente import RegistroDocente
from registro_estudiante import RegistroEstudiantes


# --- Función utilitaria: crear avatar circular ---
def crear_avatar_circular(ruta_imagen, tamaño=80, borde=3, color_borde=QColor("white")):
    """Devuelve un QPixmap circular con borde opcional desde una imagen."""
    pixmap = QPixmap(ruta_imagen)
    if pixmap.isNull():
        return QPixmap()

    # Escalar imagen cuadrada
    pixmap = pixmap.scaled(
        tamaño, tamaño,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )

    # Crear un QPixmap transparente donde dibujar el círculo
    avatar = QPixmap(tamaño, tamaño)
    avatar.fill(Qt.GlobalColor.transparent)

    painter = QPainter(avatar)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Dibujar borde
    if borde > 0:
        painter.setPen(QColor(color_borde))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(0, 0, tamaño - 1, tamaño - 1)

    # Recortar en círculo
    path = QPainterPath()
    path.addEllipse(borde, borde, tamaño - 2 * borde, tamaño - 2 * borde)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()

    return avatar


# --- Botón avanzado ---
class BotonTarjetaAvanzado(QToolButton):
    """Botón tipo tarjeta con efecto hover: icono grande que se reduce, texto aparece suavemente y brillo animado."""
    def __init__(self, icono, texto="", color_borde="#2E7D32", parent=None):
        super().__init__(parent)
        self.texto = texto
        self.color_borde = color_borde

        # Brillo
        self._brillo_pos = -1.0
        self.anim_brillo = QPropertyAnimation(self, b"brillo")
        self.anim_brillo.setDuration(800)
        self.anim_brillo.setStartValue(-1.0)
        self.anim_brillo.setEndValue(1.0)

        # Icono
        self.setIcon(QIcon(icono))
        self.icon_size_default = 180
        self.icon_size_hover = 130
        self.setIconSize(QSize(self.icon_size_default, self.icon_size_default))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)
        self.setStyleSheet("""
            QToolButton {
                background-color: rgba(255,255,255,0.08);
                border-radius: 15px;
                border: none;
            }
        """)

        # Sombra
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(25)
        sombra.setXOffset(0)
        sombra.setYOffset(6)
        sombra.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(sombra)

        # Animación icono
        self.anim_icono = QPropertyAnimation(self, b"iconoSize")
        self.anim_icono.setDuration(300)

        # Animación texto (opacidad)
        self.text_opacity = 0.0
        self.anim_texto = QPropertyAnimation(self, b"textOpacity")
        self.anim_texto.setDuration(300)

    # --- Propiedades ---
    @pyqtProperty(float)
    def brillo(self):
        return self._brillo_pos

    @brillo.setter
    def brillo(self, value):
        self._brillo_pos = value
        self.update()

    def getIconoSize(self):
        return self.iconSize().width()
    def setIconoSize(self, size):
        self.setIconSize(QSize(size, size))
    iconoSize = pyqtProperty(int, fget=getIconoSize, fset=setIconoSize)

    def getTextOpacity(self):
        return self.text_opacity
    def setTextOpacity(self, value):
        self.text_opacity = value
        self.update()
    textOpacity = pyqtProperty(float, fget=getTextOpacity, fset=setTextOpacity)

    # --- Eventos hover ---
    def enterEvent(self, event):
        self.anim_icono.stop()
        self.anim_icono.setStartValue(self.icon_size_default)
        self.anim_icono.setEndValue(self.icon_size_hover)
        self.anim_icono.start()
        self.anim_texto.stop()
        self.anim_texto.setStartValue(0.0)
        self.anim_texto.setEndValue(1.0)
        self.anim_texto.start()
        self.anim_brillo.stop()
        self.anim_brillo.setDirection(QPropertyAnimation.Direction.Forward)
        self.anim_brillo.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.anim_icono.stop()
        self.anim_icono.setStartValue(self.icon_size_hover)
        self.anim_icono.setEndValue(self.icon_size_default)
        self.anim_icono.start()
        self.anim_texto.stop()
        self.anim_texto.setStartValue(1.0)
        self.anim_texto.setEndValue(0.0)
        self.anim_texto.start()
        self.anim_brillo.stop()
        self._brillo_pos = -1.0
        self.update()
        super().leaveEvent(event)

    # --- Pintado custom ---
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._brillo_pos >= 0:
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(max(0.0, self._brillo_pos - 0.2), QColor(255, 255, 255, 0))
            grad.setColorAt(self._brillo_pos, QColor(255, 255, 255, 80))
            grad.setColorAt(min(1.0, self._brillo_pos + 0.2), QColor(255, 255, 255, 0))
            painter.fillRect(self.rect(), QBrush(grad))
        if self.text_opacity > 0:
            painter.setOpacity(self.text_opacity)
            painter.setPen(QColor(255, 255, 255))
            rect = self.rect()
            rect.setTop(rect.top() + self.height() - 30)
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.texto)
            painter.setOpacity(1.0)


# --- Interfaz principal ---
class InterfazAdministrativa(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interfaz Administrativa - Institución Educativa del Sur")
        self.default_width = 1000
        self.default_height = 600
        self.resize(self.default_width, self.default_height)
        self.init_ui()

    def centrar_ventana(self, ancho=1000, alto=600):
        self.resize(ancho, alto)
        screen = QApplication.primaryScreen().availableGeometry()
        frame = self.frameGeometry()
        frame.moveCenter(screen.center())
        self.move(frame.topLeft())
    
    def changeEvent(self, event):
        """Detecta cambios de estado (maximizar/restaurar)."""
        if event.type() == event.Type.WindowStateChange:
            if not self.isMaximized():  # Si el usuario restaura
                self.centrar_ventana(self.default_width, self.default_height)
        super().changeEvent(event)

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #0D1B2A; /* azul oscuro */
                color: white;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel#titulo { font-size: 28px; font-weight: bold; color: #E3F2FD; }
            QLabel#subtitulo { font-size: 16px; color: #ccc; }
            QLabel#nombreColegio { font-size: 36px; font-weight: bold; color: #E3F2FD; }
            QLabel#lemaColegio { font-size: 22px; color: #aaa; }
            QPushButton {
                border-radius: 6px; padding: 6px 12px; font-weight: bold; color: white;
            }
            QPushButton#btnSesion { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnInfo { background-color: rgba(21, 101, 192,0.60); }
        """)

        # --- Encabezado ---
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")
        texto_layout = QVBoxLayout()
        texto_layout.addWidget(nombre)
        texto_layout.addWidget(lema)
        texto_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Foto docente circular
        foto_docente = QLabel()
        foto_docente.setObjectName("fotoDocente")
        pixmap_docente = crear_avatar_circular("src/icons/user.png", 80, borde=3, color_borde=QColor("white"))
        if not pixmap_docente.isNull():
            foto_docente.setPixmap(pixmap_docente)
        foto_docente.setFixedSize(80, 80)
        foto_docente.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_sesion = QPushButton("CERRAR SESIÓN")
        btn_sesion.setObjectName("btnSesion")
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")

        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addLayout(texto_layout)
        header_layout.addStretch()
        header_layout.addWidget(btn_sesion)
        header_layout.addWidget(btn_info)
        header_layout.addWidget(foto_docente)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        titulo = QLabel("Sistema de gestión de equipos")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitulo = QLabel("Por favor seleccione la acción que desea realizar")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Botones con distribución original ---
        acciones = [
            ("src/icons/ingreso.png", "Ingreso Estudiantes", "#2E7D32"),
            ("src/icons/salida.png", "Salida Estudiantes", "#2E7D32"),
            ("src/icons/editar_est.png", "Editar Estudiantes", "#2E7D32"),
            ("src/icons/estudiante.png", "Registrar Estudiantes", "#2E7D32"),
            ("src/icons/asis.png", "Generación de Asistencia", "#2E7D32"),
            ("src/icons/docente.png", "Registrar Docente", "#1565C0"),
            ("src/icons/equipos.png", "Gestionar Equipos", "#EF6C00"),
            ("src/icons/listar.png", "Historial de Accesos", "#EF6C00"),
            ("src/icons/incidente.png", "Registrar Incidente", "#C62828")
        ]

        grid = QGridLayout()
        grid.setSpacing(25)

        for i, (icono, texto, color) in enumerate(acciones):
            btn = BotonTarjetaAvanzado(icono, texto, color)
            if texto == "Gestionar Equipos":
                btn.clicked.connect(self.abrir_gestion_equipos)
            elif texto == "Editar Estudiantes":
                btn.clicked.connect(self.abrir_editar_estudiantes)
            elif texto == "Registrar Docente":
                btn.clicked.connect(self.abrir_registrar_docente)
            elif texto == "Registrar Estudiantes":
                btn.clicked.connect(self.abrir_registrar_estudiantes)
            # Distribución: primera fila 5, segunda fila 4
            grid.addWidget(btn, i // 5, i % 5)

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(separador)
        main_layout.addSpacing(10)
        main_layout.addWidget(titulo)
        main_layout.addWidget(subtitulo)
        main_layout.addSpacing(20)
        main_layout.addLayout(grid)
        main_layout.addStretch()

        self.setLayout(main_layout)

    # --- Métodos abrir ventanas ---
    def abrir_gestion_equipos(self):
        self.ventana_equipos = GestionEquipos()
        self.ventana_equipos.showMaximized()
        self.close()

    def abrir_editar_estudiantes(self):
        self.ventana_editar = EditarEstudiantes()
        self.ventana_editar.showMaximized()
        self.close()

    def abrir_registrar_docente(self):
        self.ventana_docente = RegistroDocente()
        self.ventana_docente.showMaximized()
        self.close()

    def abrir_registrar_estudiantes(self):
        self.ventana_estudiante = RegistroEstudiantes()
        self.ventana_estudiante.showMaximized()
        self.close()


# ==========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = InterfazAdministrativa()
    ventana.showMaximized()  # 👈 Arranca maximizada
    sys.exit(app.exec())
