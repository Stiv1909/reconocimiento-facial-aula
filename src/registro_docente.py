# Importa el módulo sys para controlar la salida del programa
import sys

# Importa OpenCV para cámara, imágenes y detección facial
import cv2

# Importa widgets y layouts de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsDropShadowEffect,
    QMessageBox, QComboBox
)

# Importa clases para imágenes, pixmaps y colores
from PyQt6.QtGui import QImage, QPixmap, QColor

# Importa utilidades base de Qt y temporizador
from PyQt6.QtCore import Qt, QTimer


# Importa la función que registra docentes en la lógica del sistema
from modules.docentes import registrar_docente


# Importa el control de sesión
from modules.sesion import Sesion

# Importa validación para comprobar si ya existe un docente administrador
from modules.validaciones import existe_docente_admin




class RegistroDocente(QWidget):
    def __init__(self):
        # Inicializa la ventana base
        super().__init__()


        # ✅ Verificar sesión
        # 🔥 Permitir entrar sin sesión SOLO si no existe un admin registrado
        if not Sesion.esta_autenticado():
            if not existe_docente_admin():
                # No hay admin → permitir registro inicial
                QMessageBox.information(
                    self,
                    "Registro inicial",
                    "No existe un docente administrador. Registre un administrador para iniciar el sistema."
                )
            else:
                # Ya hay admin → bloquear acceso sin sesión
                QMessageBox.critical(
                    self,
                    "Acceso denegado",
                    "⚠ Debe iniciar sesión para registrar más docentes."
                )
                sys.exit(0)


        # Configura título y posición inicial de la ventana
        self.setWindowTitle("Registro de Docentes - Institución Educativa del Sur")
        self.centrar_ventana(1250, 670)


        # Estado de cámara
        # Indica si la cámara está activa o congelada
        self.camara_activa = True

        # Almacena la foto capturada del docente
        self.foto_capturada = None

        # Inicializa la cámara principal
        self.cap = cv2.VideoCapture(0)


        # --- Detector de rostro ---
        # Carga el clasificador Haar Cascade para detección frontal de rostros
        self.detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


        # Timer para refrescar cámara
        # Temporizador que actualiza continuamente el frame mostrado
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)


        # Guía de silueta
        # Carga imagen guía para superponerla en el área de cámara
        self.guia_pix = QPixmap("src/guia_silueta.png")\
            .scaled(800, 350, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)


        # Construye la interfaz gráfica
        self.init_ui()


    def centrar_ventana(self, ancho=1250, alto=670):
        # Obtiene la geometría de la pantalla principal
        screen = QApplication.primaryScreen().geometry()

        # Calcula posición para centrar la ventana
        x = (screen.width() - ancho) // 2
        y = (screen.height() - alto) // 2
        self.setGeometry(x, y, ancho, alto)


    def init_ui(self):
        # Aplica estilos visuales generales
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
            QPushButton:hover       { opacity: 0.85; }
        """)


        # --- Header ---
        # Label para mostrar el logo institucional
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
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


        # Botón etiquetado como cerrar sesión, pero redirige al login
        btn_menu = QPushButton("CERRAR SESIÓN")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)


        # Botón para cerrar la ventana o programa
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(self.close)


        # Layout horizontal del encabezado
        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_menu)
        header.addWidget(btn_info)


        # Separador horizontal
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # --- Título ---
        # Título principal del módulo
        titulo = QLabel("Registro de Docentes")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --- Formulario ---
        # Campo de cédula
        lbl_cedula = QLabel("Cédula:")
        self.txt_cedula = QLineEdit()

        # Campo de nombres
        lbl_nombre = QLabel("Nombres:")
        self.txt_nombre = QLineEdit()

        # Campo de apellidos
        lbl_apellido = QLabel("Apellidos:")
        self.txt_apellido = QLineEdit()

        # Campo de celular
        lbl_celular = QLabel("Celular:")
        self.txt_celular = QLineEdit()

        # Selector para indicar si el docente será administrador
        lbl_admin = QLabel("¿Es administrador?")
        self.cmb_admin = QComboBox()
        self.cmb_admin.addItems(["No", "Sí"])


        # Layout horizontal del formulario
        form = QHBoxLayout()
        form.addStretch()
        form.addWidget(lbl_cedula)
        form.addWidget(self.txt_cedula)
        form.addSpacing(15)
        form.addWidget(lbl_nombre)
        form.addWidget(self.txt_nombre)
        form.addSpacing(15)
        form.addWidget(lbl_apellido)
        form.addWidget(self.txt_apellido)
        form.addSpacing(15)
        form.addWidget(lbl_celular)
        form.addWidget(self.txt_celular)
        form.addSpacing(15)
        form.addWidget(lbl_admin)
        form.addWidget(self.cmb_admin)
        form.addStretch()


        # --- Área de cámara ---
        # Label donde se mostrará el video de la cámara
        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setStyleSheet("""
            background-color: none;
            border: 5px solid #1c2c3c;
            border-radius: 15px;
        """)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Label superpuesto con la guía visual
        self.lbl_guia = QLabel(self.lbl_camara)
        self.lbl_guia.setPixmap(self.guia_pix)
        self.lbl_guia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


        # --- Mensaje de estado ---
        # Etiqueta que informa si hay un rostro detectado
        self.lbl_estado = QLabel("")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")


        # --- Botones ---
        # Botón para capturar la imagen del docente
        self.btn_capturar = QPushButton("Capturar")
        self.btn_capturar.setObjectName("btnCapturar")
        self.btn_capturar.clicked.connect(self.toggle_captura)
        self.btn_capturar.setEnabled(False)  # 🔹 empieza deshabilitado


        # Botón para registrar el docente en la base de datos
        btn_agregar = QPushButton("Agregar")
        btn_agregar.setObjectName("btnAgregar")
        btn_agregar.clicked.connect(self.agregar_registro)


        # Layout horizontal inferior con botones
        bottom = QHBoxLayout()
        bottom.addStretch()
        bottom.addWidget(self.btn_capturar)
        bottom.addSpacing(20)
        bottom.addWidget(btn_agregar)
        bottom.addStretch()


        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addLayout(header)
        main_layout.addWidget(separador)
        main_layout.addWidget(titulo)
        main_layout.addLayout(form)
        main_layout.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_estado)   # 🔹 mensaje debajo de la cámara
        main_layout.addLayout(bottom)


        self.setLayout(main_layout)


    def update_frame(self):
        # Si la cámara está pausada, no actualiza el video
        if not self.camara_activa:
            return

        # Captura un frame de la cámara
        ret, frame = self.cap.read()
        if not ret:
            return

        # Invierte horizontalmente la imagen para efecto espejo
        frame = cv2.flip(frame, 1)

        # Convierte a escala de grises para detección facial
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostros = self.detector.detectMultiScale(gray, 1.3, 5)


        if len(rostros) > 0:
            # Si hay rostro detectado, habilita captura
            self.lbl_estado.setText("✅ Rostro detectado, capture la imagen")
            self.btn_capturar.setEnabled(True)
        else:
            # Si no hay rostro, deshabilita captura
            self.lbl_estado.setText("")
            self.btn_capturar.setEnabled(False)


        # Convierte a RGB para mostrar en PyQt
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        rgb = cv2.resize(rgb, (tw, th), interpolation=cv2.INTER_LINEAR)
        img = QImage(rgb.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))
        self.lbl_guia.resize(self.lbl_camara.size())
        self.lbl_guia.move(0, 0)


    def toggle_captura(self):
        # Si la cámara está activa, captura la foto y congela el video
        if self.camara_activa:
            ret, frame = self.cap.read()
            if not ret:
                return
            frame = cv2.flip(frame, 1)
            self.foto_capturada = frame.copy()
            self.camara_activa = False
            self.update_frame()
        else:
            # Si estaba congelada, reactiva la cámara
            self.camara_activa = True


    def agregar_registro(self):
        # Obtiene y limpia los datos ingresados en el formulario
        cedula = self.txt_cedula.text().strip()
        nombre = self.txt_nombre.text().strip()
        apellido = self.txt_apellido.text().strip()
        celular = self.txt_celular.text().strip()
        es_admin = 1 if self.cmb_admin.currentText() == "Sí" else 0


        # Verifica que todos los campos estén completos
        if not cedula or not nombre or not apellido or not celular:
            QMessageBox.warning(self, "Campos vacíos", "⚠ Debes completar todos los campos")
            return

        # Verifica que ya se haya capturado una foto
        if self.foto_capturada is None:
            QMessageBox.warning(self, "Sin foto", "⚠ Debes capturar una foto primero")
            return


        # Codifica la foto en formato JPG y la convierte a bytes
        ok, buf = cv2.imencode(".jpg", self.foto_capturada)
        foto_bytes = buf.tobytes() if ok else None


        # Intenta registrar el docente en la lógica de negocio
        if registrar_docente(cedula, nombre, apellido, celular, es_admin, foto_bytes):
            QMessageBox.information(self, "Éxito", f"Docente {nombre} {apellido} registrado")
            self.txt_cedula.clear()
            self.txt_nombre.clear()
            self.txt_apellido.clear()
            self.txt_celular.clear()
            self.cmb_admin.setCurrentIndex(0)
            self.foto_capturada = None
            self.camara_activa = True
        else:
            QMessageBox.critical(self, "Error", "No se pudo registrar el docente")


    def volver_menu(self):
        # Abre la ventana de inicio de sesión
        from login import InicioSesionDocente
        self.cap.release()
        self.ventana_menu = InicioSesionDocente()
        self.ventana_menu.showMaximized()
        self.close()


    def closeEvent(self, event):
        # Libera la cámara al cerrar la ventana
        self.cap.release()
        super().closeEvent(event)



if __name__ == "__main__":
    # Crea la aplicación principal
    app = QApplication(sys.argv)

    # Crea y muestra la ventana de registro docente
    ventana = RegistroDocente()
    ventana.show()

    # Ejecuta el bucle principal de la aplicación
    sys.exit(app.exec())
