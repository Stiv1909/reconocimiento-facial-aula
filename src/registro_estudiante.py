# Importa el módulo sys para controlar la salida de la aplicación
import sys

# Importa OpenCV para manejo de cámara, imágenes y detección de rostros
import cv2

# Importa los componentes gráficos necesarios de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QMessageBox, QComboBox
)

# Importa clases para mostrar imágenes dentro de PyQt
from PyQt6.QtGui import QImage, QPixmap

# Importa utilidades de Qt para alineación y temporizador
from PyQt6.QtCore import Qt, QTimer


# Importa la función que registra estudiantes en la base de datos
from modules.estudiantes import registrar_estudiante  

# Importa la clase de sesión para validar autenticación
from modules.sesion import Sesion


class RegistroEstudiantes(QWidget):
    def __init__(self):
        # Inicializa la ventana base
        super().__init__()

        # ✅ Verificar sesión
        if not Sesion.esta_autenticado():
            # Si no hay sesión activa, se bloquea el acceso a la ventana
            QMessageBox.critical(self, "Acceso denegado", "⚠ Debe iniciar sesión para usar esta ventana.")
            sys.exit(0)  # Cierra la app si no hay sesión activa


        # Título de la ventana
        self.setWindowTitle("Registro de Estudiantes - Institución Educativa del Sur")


        # Estado de cámara
        # Indica si la cámara está activa y transmitiendo en tiempo real
        self.camara_activa = True

        # Almacena la última foto capturada del estudiante
        self.foto_capturada = None

        # Inicializa la cámara principal del dispositivo
        self.cap = cv2.VideoCapture(0)


        # --- Clasificador de rostros ---
        # Carga el clasificador Haar Cascade para detección frontal de rostros
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


        # Timer para refrescar cámara
        # Crea un temporizador para actualizar continuamente el frame de la cámara
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)


        # Carga silueta de guía (PNG transparente)
        # Carga la guía visual para orientar el rostro dentro del área de la cámara
        self.guia_pix = QPixmap("src/guia_silueta.png")\
            .scaled(800, 350,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)


        # Construye la interfaz gráfica
        self.init_ui()


    def init_ui(self):
        # Aplica el estilo visual general de la ventana
        self.setStyleSheet("""
            QWidget {
                background-color: #0D1B2A;
                color: white;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel#titulo {
                font-size: 28px;
                font-weight: bold;
                color: #E3F2FD;
            }
            QLabel#nombreColegio {
                font-size: 36px;
                font-weight: bold;
                color: #E3F2FD;
            }
            QLabel#lemaColegio {
                font-size: 22px;
                color: #aaa;
            }
            QLineEdit, QComboBox {
                border: 1px solid #1565C0;
                border-radius: 5px;
                padding: 6px;
                font-size: 16px;
                background: white;
                color: black;
            }
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnMenu     { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton#btnInfo     { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnCapturar { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnAgregar  { background-color: rgba(21, 101, 192, 0.60); }
            QPushButton:disabled    { background-color: #555; color: #ccc; }
            QPushButton:hover:enabled { opacity: 0.85; }
        """)


        # --- Header ---
        # Label para mostrar el logo institucional
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")

        # Si la imagen del logo existe, la escala y la muestra
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiquetas con nombre y lema institucional
        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")


        # Layout vertical para agrupar nombre y lema
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)


        # Botón para volver al menú principal
        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)


        # Botón para cerrar el programa
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")


        # Layout horizontal del encabezado
        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_menu)
        header.addWidget(btn_info)


        # Línea horizontal separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # Título de la ventana
        titulo = QLabel("Registro de Estudiantes")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --- Formulario ---
        # Campo para nombre del estudiante
        lbl_nombre = QLabel("Nombre:")
        self.txt_nombre = QLineEdit()

        # Campo para apellido del estudiante
        lbl_apellido = QLabel("Apellido:")
        self.txt_apellido = QLineEdit()

        # Selector de grado del estudiante
        lbl_grado = QLabel("Grado:")
        self.cmb_grado = QComboBox()
        self.cmb_grado.addItems([
            "6-1","6-2","6-3","6-4",
            "7-1","7-2","7-3","7-4",
            "8-1","8-2","8-3",
            "9-1","9-2","9-3",
            "10-1","10-2","10-3",
            "11-1","11-2","11-3"
        ])


        # Layout horizontal del formulario
        form = QHBoxLayout()
        form.addStretch()
        form.addWidget(lbl_nombre)
        form.addWidget(self.txt_nombre)
        form.addSpacing(15)
        form.addWidget(lbl_apellido)
        form.addWidget(self.txt_apellido)
        form.addSpacing(15)
        form.addWidget(lbl_grado)
        form.addWidget(self.cmb_grado)
        form.addStretch()


        # --- Área de cámara ---
        # Label que mostrará el video en tiempo real de la cámara
        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setStyleSheet("""
            background-color: none;
            border: 5px solid #1c2c3c;
            border-radius: 15px;
        """)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Label superpuesto para mostrar la guía de silueta facial
        self.lbl_guia = QLabel(self.lbl_camara)
        self.lbl_guia.setPixmap(self.guia_pix)
        self.lbl_guia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


        # 🔹 Etiqueta de estado rostro
        # Muestra mensajes visuales según se detecte o no un rostro
        self.lbl_estado = QLabel("")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")


        # --- Botones inferiores ---
        # Botón para capturar la imagen del estudiante
        self.btn_capturar = QPushButton("Capturar")
        self.btn_capturar.setObjectName("btnCapturar")
        self.btn_capturar.setEnabled(False)  # 🔹 Deshabilitado al inicio
        self.btn_capturar.clicked.connect(self.toggle_captura)


        # Botón para guardar el nuevo estudiante
        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.clicked.connect(self.agregar_registro)


        # Layout horizontal inferior con botones de acción
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(self.btn_capturar)
        bottom.addSpacing(20)
        bottom.addWidget(btn_agregar)
        bottom.addStretch()


        # Layout principal de la ventana
        main_layout = QVBoxLayout()
        main_layout.addLayout(header)
        main_layout.addWidget(separador)
        main_layout.addWidget(titulo)
        main_layout.addSpacing(15)
        main_layout.addLayout(form)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.lbl_estado)   # 🔹 mensaje de rostro detectado
        main_layout.addSpacing(10)
        main_layout.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addSpacing(15)
        main_layout.addLayout(bottom)
        main_layout.addStretch()
        self.setLayout(main_layout)


    def update_frame(self):
        # Si la cámara está pausada, no actualiza el video
        if not self.camara_activa:
            return

        # Captura un frame desde la cámara
        ret, frame = self.cap.read()
        if not ret:
            return


        # Voltea horizontalmente la imagen para efecto espejo
        frame = cv2.flip(frame, 1)

        # Convierte el frame a escala de grises para la detección de rostros
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


        # 🔹 Detectar rostros
        # Busca rostros en el frame actual
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)


        if len(faces) > 0:
            # Si hay al menos un rostro, habilita la captura y muestra mensaje
            self.btn_capturar.setEnabled(True)
            self.lbl_estado.setText("✅ Rostro detectado, capture la imagen")
        else:
            # Si no hay rostro, deshabilita captura y limpia mensaje
            self.btn_capturar.setEnabled(False)
            self.lbl_estado.setText("")


        # Convierte el frame a RGB para mostrarlo en PyQt
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        rgb = cv2.resize(rgb, (tw, th), interpolation=cv2.INTER_LINEAR)
        img = QImage(rgb.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))

        # Ajusta la guía superpuesta al tamaño del área de cámara
        self.lbl_guia.resize(self.lbl_camara.size())
        self.lbl_guia.move(0, 0)


    def toggle_captura(self):
        # Si la cámara está activa, captura la imagen actual y la congela
        if self.camara_activa:
            ret, frame = self.cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            self.foto_capturada = frame.copy()
            self.camara_activa = False
            self.update_frame()
        else:
            # Si la cámara estaba pausada, la reactiva
            self.camara_activa = True


    def agregar_registro(self):
        # Obtiene nombre, apellido y grado ingresados en el formulario
        nombre = self.txt_nombre.text().strip()
        apellido = self.txt_apellido.text().strip()
        grado = self.cmb_grado.currentText()

        # Valida que los campos de texto no estén vacíos
        if not nombre or not apellido:
            QMessageBox.warning(self, "Campos vacíos", "⚠ Debes completar todos los campos")
            return

        # Valida que se haya capturado una foto antes de registrar
        if self.foto_capturada is None:
            QMessageBox.warning(self, "Sin foto", "⚠ Debes capturar una foto primero")
            return

        # Codifica la imagen capturada en formato JPG
        ok, buf = cv2.imencode(".jpg", self.foto_capturada)
        foto_bytes = buf.tobytes() if ok else None

        # Llama a la función de registro en base de datos
        if registrar_estudiante(nombre, apellido, grado, foto_bytes):
            QMessageBox.information(self, "Éxito", f"Estudiante {nombre} {apellido} registrado")
            self.txt_nombre.clear()
            self.txt_apellido.clear()
            self.cmb_grado.setCurrentIndex(0)
            self.foto_capturada = None
            self.camara_activa = True
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el estudiante")


    def volver_menu(self):
        # Importa la interfaz administrativa en el momento de volver
        from menu import InterfazAdministrativa

        # Libera la cámara antes de cambiar de ventana
        self.cap.release()

        # Crea y muestra la ventana del menú principal
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()  # 🔹 Abrir menú maximizado
        self.close()


    def closeEvent(self, event):
        # Libera la cámara al cerrar la ventana
        self.cap.release()
        super().closeEvent(event)



if __name__ == "__main__":
    # Crea la aplicación principal de PyQt
    app = QApplication(sys.argv)

    # Crea la ventana de registro de estudiantes
    ventana = RegistroEstudiantes()

    # Muestra la ventana maximizada por defecto
    ventana.showMaximized()  # 🔹 Abrir maximizada por defecto

    # Inicia el ciclo principal de la aplicación
    sys.exit(app.exec())
