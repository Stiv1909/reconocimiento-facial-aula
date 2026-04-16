# Importación de módulos del sistema para argumentos y manejo de rutas
import sys, os

# Importación de componentes de interfaz gráfica de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QToolButton, QFrame, QGraphicsDropShadowEffect, QInputDialog, QDialog
)

# Importación de clases para íconos, imágenes, dibujo y efectos visuales
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter, QBrush, QLinearGradient, QPainterPath, QImage

# Importación de clases base para alineación, tamaños y animaciones
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, pyqtProperty, QParallelAnimationGroup


# Importa la sesión del usuario autenticado
from modules.sesion import Sesion

# Importa ventanas
from ingreso_estudiantes import IngresoEstudiantes
from salida_estudiantes import SalidaEstudiantes, SeleccionarGradoDialog
from editar_estudiante import EditarEstudiantes
from gestion_equipos import GestionEquipos
from registro_docente import RegistroDocente
from registro_estudiante import RegistroEstudiantes
from historial_accesos import HistorialAccesos
from historial_danos import HistorialDanños
from historial_equipos import HistorialEquipos
from registrar_incidente import RegistrarIncidente
from reporte import ReporteAsistencias


# --- Función utilitaria: crear avatar circular ---
def crear_avatar_circular(ruta_imagen, tamaño=80, borde=3, color_borde=QColor("white")):
    # Carga la imagen desde la ruta indicada
    pixmap = QPixmap(ruta_imagen)

    # Si la imagen no existe o no puede cargarse, retorna un QPixmap vacío
    if pixmap.isNull():
        return QPixmap()


    # Escala la imagen al tamaño requerido, expandiendo si es necesario para llenar el área
    pixmap = pixmap.scaled(
        tamaño, tamaño,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )


    # Crea una imagen transparente que servirá como lienzo para el avatar circular
    avatar = QPixmap(tamaño, tamaño)
    avatar.fill(Qt.GlobalColor.transparent)


    # Inicializa el objeto painter para dibujar sobre el avatar
    painter = QPainter(avatar)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)


    # Dibuja el borde circular si el grosor es mayor que cero
    if borde > 0:
        painter.setPen(QColor(color_borde))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(0, 0, tamaño - 1, tamaño - 1)


    # Crea una trayectoria circular para recortar visualmente la imagen
    path = QPainterPath()
    path.addEllipse(borde, borde, tamaño - 2 * borde, tamaño - 2 * borde)
    painter.setClipPath(path)

    # Dibuja la imagen dentro del área circular
    painter.drawPixmap(0, 0, pixmap)
    painter.end()


    # Retorna el avatar circular generado
    return avatar



# --- Función utilitaria: crear icono en blanco ---
def _crear_icono_blanco(ruta_icono, tamaño=180):
    """Crea una versión blanca del ícono especificado."""
    # Cargar el pixmap original
    pixmap = QPixmap(ruta_icono)
    if pixmap.isNull():
        return QIcon()

    # Escalar al tamaño requerido
    size = QSize(tamaño, tamaño)
    pixmap = pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)

    # Convertir a escala de grises y luego a blanco
    img = pixmap.toImage()
    width = img.width()
    height = img.height()

    # Crear nueva imagen en blanco
    result_img = QImage(width, height, QImage.Format.Format_ARGB32)
    result_img.fill(Qt.GlobalColor.transparent)

    # Procesar cada pixel
    for y in range(height):
        for x in range(width):
            pixel = img.pixel(x, y)
            if pixel != 0:  # No completamente transparente
                color = QColor(pixel)
                if color.alpha() > 0:
                    result_img.setPixelColor(x, y, QColor(255, 255, 255, color.alpha()))

    return QIcon(QPixmap.fromImage(result_img))


# --- Botón avanzado ---
class BotonTarjetaAvanzado(QToolButton):
    def __init__(self, icono, texto="", color_borde="#2E7D32", parent=None):
        # Inicializa la clase base QToolButton
        super().__init__(parent)

        # Guarda el texto y color asociado al botón
        self.texto = texto
        self.color_borde = color_borde
        self.ruta_icono = icono  # Guarda la ruta del ícono original

        # Posición inicial del brillo animado
        self._brillo_pos = -1.0


        # Animaciones
        # Animación de brillo para el efecto visual al pasar el mouse
        self.anim_brillo = QPropertyAnimation(self, b"brillo")
        self.anim_brillo.setDuration(800)
        self.anim_brillo.setStartValue(-1.0)
        self.anim_brillo.setEndValue(1.0)


        # Asigna ícono original al botón
        self.setIcon(QIcon(icono))

        # Tamaños del ícono en estado normal y hover
        self.icon_size_default = 180
        self.icon_size_hover = 130

        # Establece el tamaño inicial del ícono
        self.setIconSize(QSize(self.icon_size_default, self.icon_size_default))

        # Hace que el botón muestre solo el ícono
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        # Define el tamaño mínimo y máximo del botón
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)

        # Aplica estilo visual al botón
        self.setStyleSheet("""
            QToolButton {
                background-color: rgba(255,255,255,0.08);
                border-radius: 15px;
                border: none;
            }
        """)


        # Agrega sombra al botón para darle profundidad visual
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(25)
        sombra.setXOffset(0)
        sombra.setYOffset(6)
        sombra.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(sombra)


        # Animación para cambiar el tamaño del ícono
        self.anim_icono = QPropertyAnimation(self, b"iconoSize")
        self.anim_icono.setDuration(300)


        # Opacidad inicial del texto sobre el botón
        self.text_opacity = 0.0

        # Animación para mostrar y ocultar el texto
        self.anim_texto = QPropertyAnimation(self, b"textOpacity")
        self.anim_texto.setDuration(300)


    # --- Propiedades ---
    @pyqtProperty(float)
    def brillo(self):
        # Retorna la posición actual del brillo
        return self._brillo_pos

    @brillo.setter
    def brillo(self, value):
        # Actualiza la posición del brillo y redibuja el botón
        self._brillo_pos = value
        self.update()


    def getIconoSize(self):
        # Retorna el ancho actual del ícono
        return self.iconSize().width()

    def setIconoSize(self, size):
        # Actualiza el tamaño del ícono
        self.setIconSize(QSize(size, size))

    # Declara una propiedad animable para el tamaño del ícono
    iconoSize = pyqtProperty(int, fget=getIconoSize, fset=setIconoSize)


    def getTextOpacity(self):
        # Retorna el nivel actual de opacidad del texto
        return self.text_opacity

    def setTextOpacity(self, value):
        # Actualiza la opacidad del texto y redibuja el botón
        self.text_opacity = value
        self.update()

    # Declara una propiedad animable para la opacidad del texto
    textOpacity = pyqtProperty(float, fget=getTextOpacity, fset=setTextOpacity)


    # --- Eventos hover ---
    def enterEvent(self, event):
        # Detiene cualquier animación previa del ícono
        self.anim_icono.stop()

        # Configura la animación para reducir el tamaño del ícono al pasar el mouse
        self.anim_icono.setStartValue(self.icon_size_default)
        self.anim_icono.setEndValue(self.icon_size_hover)
        self.anim_icono.start()

        # Configura la animación para mostrar el texto
        self.anim_texto.stop()
        self.anim_texto.setStartValue(0.0)
        self.anim_texto.setEndValue(1.0)
        self.anim_texto.start()

        # Inicia la animación del brillo
        self.anim_brillo.stop()
        self.anim_brillo.setDirection(QPropertyAnimation.Direction.Forward)
        self.anim_brillo.start()

        # Cambia el ícono a blanco en hover
        self.setIcon(_crear_icono_blanco(self.ruta_icono, self.icon_size_default))

        # Llama al comportamiento original del evento
        super().enterEvent(event)


    def leaveEvent(self, event):
        # Detiene la animación actual del ícono
        self.anim_icono.stop()

        # Configura la animación para restaurar el tamaño original del ícono
        self.anim_icono.setStartValue(self.icon_size_hover)
        self.anim_icono.setEndValue(self.icon_size_default)
        self.anim_icono.start()

        # Configura la animación para ocultar el texto
        self.anim_texto.stop()
        self.anim_texto.setStartValue(1.0)
        self.anim_texto.setEndValue(0.0)
        self.anim_texto.start()

        # Restaura el ícono original al salir del hover
        self.setIcon(QIcon(self.ruta_icono))

        # Reinicia el efecto de brillo
        self.anim_brillo.stop()
        self._brillo_pos = -1.0
        self.update()

        # Llama al comportamiento original del evento
        super().leaveEvent(event)


    def paintEvent(self, event):
        # Ejecuta primero el dibujo base del botón
        super().paintEvent(event)

        # Crea el painter para dibujar efectos encima del botón
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibuja el brillo animado si está activo
        if self._brillo_pos >= 0:
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(max(0.0, self._brillo_pos - 0.2), QColor(255, 255, 255, 0))
            grad.setColorAt(self._brillo_pos, QColor(255, 255, 255, 80))
            grad.setColorAt(min(1.0, self._brillo_pos + 0.2), QColor(255, 255, 255, 0))
            painter.fillRect(self.rect(), QBrush(grad))

        # Dibuja el texto si tiene opacidad visible
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
        # Inicializa la ventana principal
        super().__init__()

        # Configura título y dimensiones iniciales de la ventana
        self.setWindowTitle("Interfaz Administrativa - Institución Educativa del Sur")
        self.default_width = 1000
        self.default_height = 600
        self.resize(self.default_width, self.default_height)


        # Obtiene los datos del usuario autenticado en sesión
        self.usuario = Sesion.obtener_usuario()


        if not self.usuario:
            # No hay sesión: cerramos la ventana (redirigir al login)
            self.close()
            return



        # Construye la interfaz gráfica
        self.init_ui()


    def centrar_ventana(self, ancho=1000, alto=600):
        # Ajusta el tamaño de la ventana
        self.resize(ancho, alto)

        # Obtiene el área disponible de la pantalla
        screen = QApplication.primaryScreen().availableGeometry()

        # Obtiene la geometría actual de la ventana
        frame = self.frameGeometry()

        # Centra la ventana respecto a la pantalla
        frame.moveCenter(screen.center())
        self.move(frame.topLeft())


    def changeEvent(self, event):
        # Detecta cambios de estado de la ventana
        if event.type() == event.Type.WindowStateChange:
            # Si deja de estar maximizada, la vuelve a centrar
            if not self.isMaximized():
                self.centrar_ventana(self.default_width, self.default_height)

        # Ejecuta el comportamiento original del evento
        super().changeEvent(event)


    def init_ui(self):
        # Limpiar layout existente si lo hay para evitar duplicates
        if self.layout() is not None:
            while self.layout().count():
                item = self.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        
        # Aplica estilos visuales generales a la ventana
        self.setStyleSheet("""
            QWidget { background-color: #0D1B2A; color: white; font-family: Arial; font-size: 14px; }
            QLabel#titulo { font-size: 28px; font-weight: bold; color: #E3F2FD; }
            QLabel#subtitulo { font-size: 16px; color: #ccc; }
            QLabel#nombreColegio { font-size: 36px; font-weight: bold; color: #E3F2FD; }
            QLabel#lemaColegio { font-size: 22px; color: #aaa; }
            QPushButton { border-radius: 6px; padding: 6px 12px; font-weight: bold; color: white; }
            QPushButton#btnSesion { background-color: rgba(21, 101, 192,0.60); }
            QPushButton#btnInfo { background-color: rgba(198,40,40,0.60); }
        """)


        # --- Encabezado ---
        # Label donde se mostrará el logo institucional
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")

        # Si el logo existe, lo escala y lo asigna al label
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            # Si no existe, muestra texto alternativo
            logo.setText("Logo no encontrado")

        # Centra el contenido del logo
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiqueta con el nombre de la institución
        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")

        # Etiqueta con el lema institucional
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")

        # Layout vertical para nombre y lema
        texto_layout = QVBoxLayout()
        texto_layout.addWidget(nombre)
        texto_layout.addWidget(lema)
        texto_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        # Foto docente
        foto_docente = QLabel()
        pixmap_docente = None

        # Si el usuario en sesión tiene foto, la convierte desde bytes a QImage
        if self.usuario and self.usuario.get("foto"):
            image = QImage.fromData(self.usuario["foto"])
            pixmap = QPixmap.fromImage(image)
            pixmap_docente = self._crear_avatar_desde_pixmap(pixmap, 80, 3, QColor("white"))
        else:
            # Si no hay foto, usa un avatar por defecto
            pixmap_docente = crear_avatar_circular("src/icons/user.png", 80, borde=3, color_borde=QColor("white"))

        # Si el avatar fue generado correctamente, lo asigna al label
        if pixmap_docente and not pixmap_docente.isNull():
            foto_docente.setPixmap(pixmap_docente)

        # Configura tamaño fijo y alineación de la foto del docente
        foto_docente.setFixedSize(80, 80)
        foto_docente.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Botón para cerrar sesión y volver al login
        btn_sesion = QPushButton("CERRAR SESIÓN")
        btn_sesion.setObjectName("btnSesion")
        btn_sesion.clicked.connect(self._cerrar_sesion_wrapper)

        # Botón para cerrar completamente la aplicación
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(QApplication.quit)

        # --- Detección robusto de administrador (ANTES de usar es_admin) ---
        es_admin = False
        u = self.usuario or {}
        if "es_admin" in u and u["es_admin"] is not None:
            try:
                es_admin = bool(int(u["es_admin"]))
            except Exception:
                es_admin = bool(u["es_admin"])
        elif "rol" in u and u["rol"] is not None:
            try:
                es_admin = str(u["rol"]).lower() == "admin"
            except Exception:
                es_admin = False
        else:
            es_admin = False

        # Botón simple para cambiar menú
        self.btn_menu = QPushButton("🔄 Cambiar Menú")
        self.btn_menu.setObjectName("btnMenu")
        self.btn_menu.setFixedHeight(40)
        
        # Estilo simple
        self.btn_menu.setStyleSheet("""
            QPushButton#btnMenu {
                background-color: #7B1FA2;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 14px;
                color: white;
            }
            QPushButton#btnMenu:hover {
                background-color: #9C27B0;
            }
        """)
        self.btn_menu.clicked.connect(self.cambiar_menu)
        
        # Pestañas ya configuradas arriba

        # Layout horizontal del encabezado
        header_layout = QHBoxLayout()
        header_layout.addWidget(logo)
        header_layout.addLayout(texto_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_menu)
        header_layout.addWidget(btn_sesion)
        header_layout.addWidget(btn_info)

        # Layout adicional para ubicar la foto del docente
        docente_layout = QVBoxLayout()
        docente_layout.addWidget(foto_docente)
        header_layout.addLayout(docente_layout)


        # Línea horizontal separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # Título principal del módulo
        titulo = QLabel("Sistema de gestión de equipos")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Subtítulo con instrucción al usuario
        subtitulo = QLabel("Por favor seleccione la acción que desea realizar")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --- Botones ---
        # Menú DOCENTE: funciones de consulta y registro de uso (sin modificar datos)
        acciones_docente = [
            ("src/icons/ingreso.png", "Ingreso Estudiantes", "#2E7D32"),
            ("src/icons/salida.png", "Salida Estudiantes", "#2E7D32"),
            ("src/icons/listar.png", "Historial de Accesos", "#EF6C00"),
            ("src/icons/incidente.png", "Historial de Daños", "#C62828"),
            ("src/icons/equipos.png", "Historial de Equipos", "#1565C0"),
            ("src/icons/incidente.png", "Registrar Incidente", "#C62828"),
            ("src/icons/asis.png", "Generación de Asistencia", "#2E7D32"),
        ]
        
        # Menú ADMINISTRATIVO: solo funciones exclusivas de admin (sin repetidos del docente)
        acciones_admin = [
            ("src/icons/editar_est.png", "Editar Estudiantes", "#2E7D32"),
            ("src/icons/estudiante.png", "Registrar Estudiantes", "#2E7D32"),
            ("src/icons/docente.png", "Registrar Docente", "#1565C0"),
            ("src/icons/equipos.png", "Gestionar Equipos", "#EF6C00"),
        ]
        
        # Determinar qué acciones mostrar según el tipo de menú
        menu_tipo = Sesion.get_menu_tipo()
        if menu_tipo == "administrativo" and es_admin:
            acciones = acciones_admin
        else:
            acciones = acciones_docente

        # Guardar listas para cambio de menú
        self.acciones_docente = acciones_docente
        self.acciones_admin = acciones_admin
        self.es_admin = es_admin

        # Crear grid para botones
        grid = QGridLayout()
        grid.setSpacing(25)
        
        # Llenar el grid con botones
        row, col = 0, 0
        max_cols = 5
        for icono, texto, color in acciones:
            # Botones protegidos
            if texto in ["Editar Estudiantes", "Registrar Estudiantes", "Registrar Docente", "Gestionar Equipos", "Historial de Daños", "Historial de Equipos"]:
                if not es_admin:
                    continue
            
            btn = BotonTarjetaAvanzado(icono, texto, color)
            
            # Conecta cada botón con su método
            if texto == "Ingreso Estudiantes":
                btn.clicked.connect(self.abrir_ingreso_estudiantes)
            elif texto == "Salida Estudiantes":
                btn.clicked.connect(self.abrir_salida_estudiantes)
            elif texto == "Gestionar Equipos":
                btn.clicked.connect(self.abrir_gestion_equipos)
            elif texto == "Editar Estudiantes":
                btn.clicked.connect(self.abrir_editar_estudiantes)
            elif texto == "Registrar Docente":
                btn.clicked.connect(self.abrir_registrar_docente)
            elif texto == "Registrar Estudiantes":
                btn.clicked.connect(self.abrir_registrar_estudiantes)
            elif texto == "Historial de Accesos":
                btn.clicked.connect(self.abrir_historial_accesos)
            elif texto == "Historial de Daños":
                btn.clicked.connect(self.abrir_historial_danos)
            elif texto == "Historial de Equipos":
                btn.clicked.connect(self.abrir_historial_equipos)
            elif texto == "Registrar Incidente":
                btn.clicked.connect(self.abrir_registrar_incidente)
            elif texto == "Generación de Asistencia":
                btn.clicked.connect(self.abrir_reporte_asistencias)
            
            grid.addWidget(btn, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

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


    def _crear_avatar_desde_pixmap(self, pixmap, tamaño=80, borde=3, color_borde=QColor("white")):
        # Si el pixmap es inválido, retorna uno vacío
        if pixmap.isNull():
            return QPixmap()

        # Ajusta el pixmap al tamaño indicado
        pixmap = pixmap.scaled(
            tamaño, tamaño,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # Crea un lienzo transparente para el avatar circular
        avatar = QPixmap(tamaño, tamaño)
        avatar.fill(Qt.GlobalColor.transparent)

        # Inicializa el pintor
        painter = QPainter(avatar)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Dibuja el borde circular si corresponde
        if borde > 0:
            painter.setPen(QColor(color_borde))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(0, 0, tamaño - 1, tamaño - 1)

        # Crea una máscara circular para recortar la imagen
        path = QPainterPath()
        path.addEllipse(borde, borde, tamaño - 2 * borde, tamaño - 2 * borde)
        painter.setClipPath(path)

        # Dibuja la imagen dentro de la máscara
        painter.drawPixmap(0, 0, pixmap)
        painter.end()

        # Retorna el avatar generado
        return avatar


    # --- Métodos abrir ventanas ---
    def abrir_ingreso_estudiantes(self):
        # Lista de grados disponibles para el ingreso de estudiantes
        grados = ["6-1","6-3","7-1", "7-3", "8-1", "9-1", "9-2", "9-3","10-1", "11-1"]

        # Muestra un diálogo para seleccionar el grado
        grado, ok = QInputDialog.getItem(self, "Seleccionar grado", "Seleccione el grado:", grados, 0, False)

        # Si el usuario confirma y selecciona un grado válido, abre la ventana correspondiente
        if ok and grado:
            self.ventana_equipos = IngresoEstudiantes(grado)
            self.ventana_equipos.showMaximized()
            self.close()


    def abrir_salida_estudiantes(self):
        # Lista de grados disponibles para la salida de estudiantes
        grados = ["6-1","6-3","7-1","7-3","8-1", "9-1", "9-2", "9-3","10-1", "11-1"]

        # Solicita al usuario seleccionar un grado
        grado, ok = QInputDialog.getItem(self, "Seleccionar grado", "Seleccione el grado:", grados, 0, False)

        # Si el usuario confirma, abre la ventana de salida y carga el grado seleccionado
        if ok and grado:
            self.ventana_salida = SalidaEstudiantes()
            self.ventana_salida.selected_grade = grado  # Asignar el grado directamente
            self.ventana_salida.on_cargar_grado()       # Cargar los datos del grado
            self.ventana_salida.showMaximized()
            self.close()


    def abrir_gestion_equipos(self):
        # Abre la ventana de gestión de equipos
        self.ventana_equipos = GestionEquipos()
        self.ventana_equipos.showMaximized()
        self.close()


    def abrir_editar_estudiantes(self):
        # Abre la ventana para editar estudiantes
        self.ventana_editar = EditarEstudiantes()
        self.ventana_editar.showMaximized()
        self.close()


    def abrir_registrar_docente(self):
        # Abre la ventana para registrar docentes
        self.ventana_docente = RegistroDocente()
        self.ventana_docente.showMaximized()
        self.close()


    def abrir_registrar_estudiantes(self):
        # Abre la ventana para registrar estudiantes
        self.ventana_estudiante = RegistroEstudiantes()
        self.ventana_estudiante.showMaximized()
        self.close()
    
    def abrir_historial_accesos(self):
        # Abre la ventana de historial de accesos
        self.ventana_historial = HistorialAccesos()
        self.ventana_historial.showMaximized()
        self.close()

    def abrir_historial_danos(self):
        # Abre la ventana de historial de daños
        self.ventana_danos = HistorialDanños()
        self.ventana_danos.showMaximized()
        self.close()

    def abrir_historial_equipos(self):
        # Abre la ventana de historial de equipos
        self.ventana_equipos = HistorialEquipos()
        self.ventana_equipos.showMaximized()
        self.close()

    def abrir_registrar_incidente(self):
        # Abre la ventana para registrar incidentes
        self.ventana_incidente = RegistrarIncidente()
        self.ventana_incidente.showMaximized()
        self.close()
    
    def abrir_reporte_asistencias(self):
        # Abre la ventana de generación de reportes de asistencia
        self.ventana_reporte = ReporteAsistencias()
        self.ventana_reporte.showMaximized()
        self.close()


    # --- Wrapper para cerrar sesión ---
    def _cerrar_sesion_wrapper(self):
        self.cerrar_sesion()


    # --- Cambiar tipo de menú ---
    def cambiar_menu(self):
        # Cambiar el tipo de menú
        menu_actual = Sesion.get_menu_tipo()
        if menu_actual == "docente":
            Sesion.set_menu_tipo("administrativo")
        else:
            Sesion.set_menu_tipo("docente")
        
        # Abrir nueva ventana y cerrar esta
        from menu import InterfazAdministrativa
        self.nueva_menu = InterfazAdministrativa()
        self.nueva_menu.showMaximized()
        self.close()


    # --- Cerrar sesión ---
    def cerrar_sesion(self):
        # Importa la ventana de login en el momento de cerrar sesión
        from login import InicioSesionDocente

        # Limpia la sesión actual y resetear tipo de menú
        Sesion.cerrar_sesion()
        Sesion.set_menu_tipo("docente")

        # Crea nuevamente la ventana de inicio de sesión
        self.login = InicioSesionDocente()
        self.login.show()

        # Cierra la ventana actual del menú
        self.close()


if __name__ == "__main__":
    # Crea la aplicación principal de PyQt
    app = QApplication(sys.argv)

    # Instancia la interfaz administrativa
    ventana = InterfazAdministrativa()

    # Muestra la ventana maximizada
    ventana.showMaximized()

    # Ejecuta el ciclo principal de la aplicación
    sys.exit(app.exec())
