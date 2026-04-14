# Importa módulos base del sistema y manejo de tiempo
import sys
import cv2
import time

# Importa componentes gráficos principales de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QGraphicsDropShadowEffect, QMessageBox, QDialog, QComboBox, QListWidget, QListWidgetItem
)

# Importa clases para imágenes y colores
from PyQt6.QtGui import QPixmap, QImage, QColor

# Importa utilidades base de Qt
from PyQt6.QtCore import Qt, QTimer

# Librería de reconocimiento facial
import face_recognition




# Funciones de lógica
from modules.salida_logic import (
    cargar_estudiantes,
    buscar_estudiantes_en_frame,
    registrar_salida,
    contar_equipos_ocupados,
    estudiantes_pendientes,
    registrar_asistencia
)
from modules.hardware_checker import obtener_info_hardware
from modules.conexion import crear_conexion, cerrar_conexion


# ---------------------------
# Diálogo para seleccionar grado
# ---------------------------
class SeleccionarGradoDialog(QDialog):
    def __init__(self, parent=None):
        # Inicializa la clase base QDialog
        super().__init__(parent)

        # Configura el título y tamaño fijo del diálogo
        self.setWindowTitle("Seleccionar grado")
        self.setFixedSize(300, 150)

        # Aplica estilos visuales al cuadro de diálogo
        self.setStyleSheet("""
            QDialog { background-color: #0D1B2A; color: white; font-family: Arial; }
            QLabel { font-size: 14px; }
            QComboBox { font-size: 14px; padding: 5px; border-radius: 4px; }
            QPushButton { background-color: #1565C0; color: white; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background-color: #1976D2; }
        """)


        # Crea el layout principal del diálogo
        layout = QVBoxLayout()

        # Etiqueta de instrucción para seleccionar el grado
        label = QLabel("Seleccione el grado:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


        # ComboBox donde se mostrarán los grados disponibles
        self.combo_grado = QComboBox()
        layout.addWidget(self.combo_grado)


        # Botón para aceptar la selección realizada
        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.clicked.connect(self.accept)
        layout.addWidget(btn_aceptar, alignment=Qt.AlignmentFlag.AlignCenter)


        # Asigna el layout al diálogo
        self.setLayout(layout)

        # Carga automáticamente los grados desde la base de datos
        self.cargar_grados()


    def cargar_grados(self):
        """Carga los grados desde la base de datos."""
        # Crea conexión con la base de datos
        conn = crear_conexion()
        if not conn:
            return

        # Crea cursor para ejecutar la consulta
        cur = conn.cursor()

        # Consulta los grados distintos con estado activo como estudiante
        cur.execute("SELECT DISTINCT grado FROM matriculas WHERE estado='Estudiante' ORDER BY grado")

        # Agrega cada grado obtenido al ComboBox
        for row in cur.fetchall():
            self.combo_grado.addItem(row[0])

        # Cierra cursor y conexión
        cur.close()
        cerrar_conexion(conn)


    def obtener_grado(self):
        # Retorna el grado actualmente seleccionado en el ComboBox
        return self.combo_grado.currentText()



# ---------------------------
# Ventana principal: SalidaEstudiantes
# ---------------------------
class SalidaEstudiantes(QWidget):
    def __init__(self, grado=None):
        # Inicializa la clase base QWidget
        super().__init__()

        # Configura título y posición inicial de la ventana
        self.setWindowTitle("Salida de Estudiantes")
        self.centrar_ventana(1250, 670)


        # Cámara y timer
        # Inicializa la cámara principal
        self.cap = cv2.VideoCapture(0)

        # Crea temporizador para refrescar la cámara en tiempo real
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)


        # Estado
        # Lista de estudiantes reconocibles cargados desde la base de datos
        self.estudiantes_conocidos = []

        # Lista con los nombres actualmente visibles en las tarjetas
        self.nombres_actuales = []

        # Diccionario reservado para control de última detección
        self.last_seen = {}

        # Conjunto para evitar registrar repetidamente al mismo estudiante
        self.detectados_recientes = set()

        # Indica si ya se registraron las asistencias del grado
        self.asistencias_registradas = False

        # Guarda el grado seleccionado recibido desde el diálogo
        self.selected_grade = grado  # recibido del diálogo


        # Hardware info
        # Obtiene información del hardware y la capacidad máxima de rostros simultáneos
        # Obtiene info del hardware desde la sesión (configurada en login)
        from modules.sesion import Sesion
        self.hardware_info = Sesion.get_hardware_info()
        if self.hardware_info is None:
            # Fallback: obtener directamente si no hay sesión
            self.hardware_info = obtener_info_hardware()
        self.max_faces = self.hardware_info["max_faces"]


        # UI
        # Construye la interfaz gráfica
        self.init_ui()


        # Cargar los estudiantes del grado seleccionado
        if self.selected_grade:
            self.on_cargar_grado()


        # Inicia el temporizador de actualización de cámara
        self.timer.start(30)


    def centrar_ventana(self, ancho, alto):
        # Obtiene la geometría de la pantalla principal
        screen = QApplication.primaryScreen().geometry()

        # Calcula la posición horizontal para centrar la ventana
        x = (screen.width() - ancho) // 2

        # Calcula la posición vertical para centrar la ventana
        y = (screen.height() - alto) // 2

        # Aplica la geometría final a la ventana
        self.setGeometry(x, y, ancho, alto)


    # ---------------------------
    # INTERFAZ GRÁFICA
    # ---------------------------
    def init_ui(self):
        # Aplica estilos visuales generales a la ventana
        self.setStyleSheet("""
            QWidget { background-color: #0D1B2A; color: white; font-family: Arial; font-size: 14px; }
            QLabel#titulo { font-size: 26px; font-weight: bold; color: #E3F2FD; }
            QLabel#nombreColegio { font-size: 36px; font-weight: bold; color: #E3F2FD; }
            QLabel#lemaColegio { font-size: 22px; color: #aaa; }
            QPushButton { border-radius: 6px; padding: 8px 16px; font-weight: bold; color: white; }
            QPushButton#btnMenu { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnInfo { background-color: rgba(21,101,192,0.60); }
            QPushButton#btnFinalizar { background-color: rgba(21,101,192,0.60); }
            QPushButton:hover { opacity: 0.85; }
        """)


        # Header
        # Etiqueta para mostrar el logo institucional
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiquetas con nombre y lema de la institución
        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")


        # Layout vertical para nombre y lema
        text_layout = QVBoxLayout()
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)


        # Botón para volver al menú principal
        self.btn_menu = QPushButton("MENÚ")
        self.btn_menu.setObjectName("btnMenu")
        self.btn_menu.clicked.connect(self.volver_menu)


        # Botón para cerrar el programa
        self.btn_info = QPushButton("CERRAR PROGRAMA")
        self.btn_info.setObjectName("btnInfo")
        self.btn_info.clicked.connect(self.close)


        # Layout horizontal del encabezado
        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(self.btn_menu)
        header.addWidget(self.btn_info)


        # Línea horizontal separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # Título principal y mensaje de instrucción
        titulo = QLabel(f"Salida de Estudiantes")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensaje = QLabel("Mire hacia la cámara para registrar su salida.")
        mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Lista de estudiantes que han salido
        self.lista_salidas = QListWidget()
        self.lista_salidas.setStyleSheet("""
            QListWidget {
                background-color: rgba(255,255,255,0.05);
                border: 2px solid #4CAF50;
                border-radius: 10px;
                color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }
        """)
        self.nombres_salidos = set()

        # Etiqueta que muestra cuántos equipos siguen ocupados
        self.lbl_contador = QLabel("Salidos: 0")
        self.lbl_contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_contador.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFD54F;")


        # Label donde se mostrará el video en vivo de la cámara
        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camara.setStyleSheet("""
            background-color: rgba(0,0,139,0.5);
            border: 5px solid #1565C0;
            border-radius: 15px;
        """)


        # Botón para finalizar la salida del grado
        self.btn_finalizar = QPushButton("Finalizar salida")
        self.btn_finalizar.setObjectName("btnFinalizar")
        self.btn_finalizar.clicked.connect(self.on_finalizar_salida)


        # Contenedor principal con sombra
        frame = QFrame()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)


        # Layout principal del contenido
        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addWidget(mensaje)
        
        vbox.addWidget(self.lbl_contador)
        vbox.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self.btn_finalizar, alignment=Qt.AlignmentFlag.AlignCenter)


        # Layout raíz de la ventana
        layout = QVBoxLayout()
        layout.addWidget(frame)
        self.setLayout(layout)
        self.update_buttons_state()


    def crear_tarjeta(self, titulo, valor):
        # Crea una tarjeta visual con título y valor
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: rgba(0,0,255,0.01);
                     border: 2px solid #1565C0; border-radius: 12px; padding: 6px; }
            QLabel { color: white; }
            QLabel#titulo { font-size: 16px; font-weight: bold; color: #E3F2FD; }
            QLabel#valor { font-size: 14px; color: #FFFFFF; }
        """)
        vbox = QVBoxLayout(frame)

        # Etiqueta superior de la tarjeta
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Etiqueta inferior con el estado o valor asociado
        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("valor")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Agrega ambas etiquetas al layout de la tarjeta
        vbox.addWidget(lbl_titulo)
        vbox.addWidget(lbl_valor)

        # Guarda referencias directas para poder actualizarlas luego
        frame.lbl_titulo = lbl_titulo
        frame.lbl_valor = lbl_valor
        frame.setFixedSize(250, 120)
        return frame


    # ---------------------------
    # Cargar grado
    # ---------------------------
    def on_cargar_grado(self):
        # Obtiene el grado previamente seleccionado
        grado = self.selected_grade
        if not grado:
            QMessageBox.warning(self, "Grado inválido", "No se seleccionó un grado.")
            return


        try:
            # Intenta cargar los estudiantes filtrados por grado
            estudiantes = cargar_estudiantes(grado)
        except TypeError:
            # Compatibilidad si la función no recibe parámetro grado
            estudiantes = cargar_estudiantes()


        if not estudiantes:
            QMessageBox.information(self, "Sin datos", f"No hay estudiantes ocupando equipos en {grado}.")
            return


        # Reinicia el estado interno para comenzar un nuevo proceso de salida
        self.estudiantes_conocidos = estudiantes
        self.detectados_recientes.clear()
        self.asistencias_registradas = False

        # Limpiar lista y mostrar estudiantes pendientes
        self.lista_salidas.clear()
        
        # Mostrar cada estudiante con equipo ocupado
        for est in estudiantes:
            self.lista_salidas.addItem(f"{est['nombre']} - Pendiente")

        # Contador
        pendientes = len(estudiantes)
        self.lbl_contador.setText(f"Pendientes: {pendientes}")
        self.update_buttons_state()
        QMessageBox.information(self, "Listo", f"Grado {grado} cargado. Hay {pendientes} estudiantes. Escanee para registrar salida.")


    def update_buttons_state(self):
        # Consulta cuántos equipos siguen ocupados
        ocupados = contar_equipos_ocupados()

        # Solo permite volver al menú o cerrar si ya no quedan equipos ocupados
        enabled = (ocupados == 0)
        self.btn_menu.setEnabled(enabled)
        self.btn_info.setEnabled(enabled)


    # ---------------------------
    # Detección facial y registro
    # ---------------------------
    def update_frame(self):
        # Captura un frame desde la cámara
        ret, frame = self.cap.read()
        if not ret:
            return

        # Invierte la imagen horizontalmente para efecto espejo
        frame = cv2.flip(frame, 1)


        # Convierte el frame a RGB y lo muestra en la interfaz
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        resized = cv2.resize(rgb, (tw, th))
        img = QImage(resized.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))


        # Si no se ha seleccionado grado o no hay estudiantes cargados, no procesa reconocimiento
        if not self.selected_grade or not self.estudiantes_conocidos:
            return


        # Busca estudiantes reconocidos en el frame actual
        encontrados = buscar_estudiantes_en_frame(frame, self.estudiantes_conocidos, max_faces=self.max_faces)
        present = set(e["nombre"] for e in encontrados)


        # Procesa cada estudiante reconocido
        for estudiante in encontrados:
            nombre = estudiante["nombre"]
            id_est = estudiante["id"]

            # Evita registrar dos veces el mismo estudiante
            if nombre in self.detectados_recientes:
                continue

            equipo = registrar_salida(id_est)
            if equipo:
                self.detectados_recientes.add(nombre)
                
                # Buscar y actualizar el item en la lista
                for i in range(self.lista_salidas.count()):
                    item = self.lista_salidas.item(i)
                    if item and nombre in item.text():
                        item.setText(f"{nombre} - Equipo: {equipo}")
                        break
                
                pendientes = self.lista_salidas.count() - len(self.detectados_recientes)
                self.lbl_contador.setText(f"Pendientes: {pendientes}")
                self.update_buttons_state()


        # Si ya no y aún no se registra la asistencia, la registra
        if contar_equipos_ocupados() == 0 and not self.asistencias_registradas:
            try:
                registrar_asistencia(self.selected_grade)
            except TypeError:
                registrar_asistencia()
            self.asistencias_registradas = True
            QMessageBox.information(self, "Asistencias registradas", "Se registraron las asistencias para el grado.")
            self.update_buttons_state()


    # ---------------------------
    # Finalizar salida
    # ---------------------------
    def on_finalizar_salida(self):
        # Consulta el número actual de equipos ocupados
        ocupados = contar_equipos_ocupados()

        if ocupados == 0:
            # Si ya no hay equipos ocupados, registra asistencia si aún falta y vuelve al menú
            if not self.asistencias_registradas:
                try:
                    registrar_asistencia(self.selected_grade)
                except TypeError:
                    registrar_asistencia()
                self.asistencias_registradas = True
            self.volver_menu()
            return


        try:
            # Intenta obtener la lista de estudiantes pendientes de salida
            pendientes = estudiantes_pendientes(self.selected_grade)
        except TypeError:
            # Compatibilidad si la función no recibe grado
            pendientes = estudiantes_pendientes()


        if pendientes:
            # Muestra advertencia si todavía hay estudiantes pendientes
            texto = "No se puede finalizar. Estudiantes pendientes:\n\n" + "\n".join(pendientes)
            QMessageBox.warning(self, "Pendientes", texto)


    # ---------------------------
    # Volver al menú
    # ---------------------------
    def volver_menu(self):
        # Importa el menú principal al momento de regresar
        from menu import InterfazAdministrativa
        try:
            # Detiene el temporizador y libera la cámara
            self.timer.stop()
            self.cap.release()
        except Exception:
            pass

        # Abre la ventana del menú principal
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()


    def closeEvent(self, event):
        try:
            # Detiene el temporizador y libera la cámara al cerrar la ventana
            self.timer.stop()
            self.cap.release()
        except Exception:
            pass
        super().closeEvent(event)



# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    # Crea la aplicación principal
    app = QApplication(sys.argv)

    # Muestra primero el diálogo para seleccionar grado
    dialog = SeleccionarGradoDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        grado = dialog.obtener_grado()
        if grado:
            # Si se selecciona un grado válido, abre la ventana principal de salida
            ventana = SalidaEstudiantes(grado)
            ventana.showMaximized()
            sys.exit(app.exec())

    # Si no se selecciona grado, termina la aplicación
    sys.exit(0)
