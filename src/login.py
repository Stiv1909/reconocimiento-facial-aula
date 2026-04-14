# Mensaje en consola para confirmar que el archivo login.py ha comenzado a ejecutarse
print("Iniciando login.py...")

# Habilita herramientas de depuración para mostrar errores graves del intérprete
import faulthandler
faulthandler.enable()


# Importación de módulos del sistema y manejo de rutas
import sys, os

# Librería para captura y procesamiento de video/imágenes
import cv2

# Librería para operaciones numéricas y manejo de arreglos
import numpy as np

# Librería principal para reconocimiento facial
import face_recognition

# Librería para manejo de tiempos y validaciones temporales
import time

# Librería usada para detección facial y puntos de referencia del rostro
import dlib

# Se importa la distancia euclidiana para calcular el EAR de los ojos
from scipy.spatial import distance as dist

# Importación repetida de sys y os, se mantiene tal como está en el código original
import sys, os

# Componentes gráficos de PyQt6 para construir la interfaz
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QGraphicsDropShadowEffect, QMessageBox
)

# Clases gráficas para imágenes y colores
from PyQt6.QtGui import QPixmap, QImage, QColor

# Clases base para alineación y temporizadores
from PyQt6.QtCore import Qt, QTimer


# Función personalizada para cargar los docentes registrados
from modules.doc_login import cargar_docentes

# Interfaz del menú principal que se abrirá después del login exitoso
from menu import InterfazAdministrativa 

# Clase encargada de almacenar la sesión actual del usuario
from modules.sesion import Sesion

# Ventana para registrar un nuevo docente administrador
from registro_docente import RegistroDocente

# Función que verifica si ya existe al menos un docente administrador
from modules.validaciones import existe_docente_admin




# -------------------------------
# Función para calcular EAR (Eye Aspect Ratio)
# -------------------------------
def calcular_ear(ojo):
    # Distancia vertical entre los puntos 2 y 6 del ojo
    A = dist.euclidean(ojo[1], ojo[5])

    # Distancia vertical entre los puntos 3 y 5 del ojo
    B = dist.euclidean(ojo[2], ojo[4])

    # Distancia horizontal entre los extremos del ojo
    C = dist.euclidean(ojo[0], ojo[3])

    # Fórmula del EAR para determinar si el ojo está abierto o cerrado
    return (A + B) / (2.0 * C)


def normalizar_foto(foto):
        # Si la foto no existe, retorna None
        if foto is None:
            return None

        # Si la foto ya está en bytes o bytearray, la convierte a bytes normales
        if isinstance(foto, (bytes, bytearray)):
            return bytes(foto)

        # Si la foto viene como memoryview, la convierte a bytes
        if isinstance(foto, memoryview):
            return foto.tobytes()

        # Si el tipo no es compatible, retorna None
        return None


class InicioSesionDocente(QWidget):
    def __init__(self):
        # Inicializa la clase base QWidget
        super().__init__()

         # 🔥 1. Primero verificar si hay un docente admin
        if not existe_docente_admin():
            # Muestra un mensaje informando que primero debe registrarse un administrador
            QMessageBox.information(
                self,
                "Registrar administrador",
                "No existe un docente administrador registrado.\nDebes crear uno antes de iniciar el sistema."
            )

            # Abre la ventana de registro del administrador
            self.registrar_admin()

            # Sale del proceso de inicialización del login
            return  # salir del login


        # Título de la ventana principal de inicio de sesión
        self.setWindowTitle("Inicio sesión docente - Institución Educativa del Sur")

        # Centra la ventana en la pantalla con el tamaño indicado
        self.centrar_ventana(1250, 670)


        # --- Cargar docentes desde BD ---
        # Carga la lista de docentes desde la base de datos
        self.docentes = cargar_docentes()

        # Almacena el docente detectado actualmente
        self.docente_detectado = None

        # Guarda el último encoding facial detectado para comparar movimiento
        self.ultimo_encoding = None

        # Registra el instante del último movimiento facial detectado
        self.ultimo_movimiento = time.time()

        # Registra el instante del último parpadeo detectado
        self.ultimo_parpadeo = time.time()

        # Estado para evitar iniciar sesión varias veces
        self.parpadeo_confirmado = False  # Nuevo estado


        # --- Inicializar cámara en 640x480 ---
        # Abre la cámara principal del dispositivo
        self.cap = cv2.VideoCapture(0)

        # Configura el ancho de captura
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)

        # Configura el alto de captura
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)


        # Control de frames
        # Contador usado para procesar reconocimiento solo cada cierto número de frames
        self.frame_count = 0


        # Temporizador que actualiza continuamente la imagen de la cámara
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Ruta de la imagen guía para ubicar el rostro dentro de la cámara
        ruta_guia = os.path.join(os.path.dirname(__file__), "guia_silueta.png")

        # Carga y escala la imagen guía manteniendo la proporción
        self.guia_pix = QPixmap(ruta_guia)\
            .scaled(800, 350, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)


        # --- Inicializar detector dlib ---
        # Detector frontal de rostros de dlib
        self.detector = dlib.get_frontal_face_detector()

        def resource_path(rel_path):
            # Si el programa está empaquetado como ejecutable, usa la ruta temporal de PyInstaller
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, rel_path)

            # ruta cuando corres normal (sin .exe)
            return os.path.join(os.path.dirname(__file__), "..", rel_path)


        # Ruta al modelo de puntos faciales de dlib
        model_path = resource_path("models/shape_predictor_68_face_landmarks.dat")

        # Carga el predictor de landmarks faciales
        self.predictor = dlib.shape_predictor(model_path)

        # Construye la interfaz gráfica
        self.init_ui()


    def centrar_ventana(self, ancho, alto):
        # Obtiene la geometría de la pantalla principal
        screen = QApplication.primaryScreen().geometry()

        # Calcula la posición horizontal para centrar la ventana
        x = (screen.width() - ancho) // 2

        # Calcula la posición vertical para centrar la ventana
        y = (screen.height() - alto) // 2

        # Aplica tamaño y posición a la ventana
        self.setGeometry(x, y, ancho, alto)


    def registrar_admin(self):
        # Crea la ventana de registro de docente administrador
        self.reg = RegistroDocente()

        # Muestra la ventana de registro
        self.reg.show()

        # cerrar ventana de login
        self.close()  # cerrar ventana de login


    def init_ui(self):
        # Aplica estilos generales a la interfaz
        self.setStyleSheet("""
            QWidget {
                background-color: #0D1B2A;
                color: white;
                font-family: Arial;
                font-size: 14px;
            }
            QLabel#titulo {
                font-size: 26px;
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
            QPushButton {
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnInfo       { background-color: rgba(198,40,40,0.60); }
            QPushButton:hover         { opacity: 0.85; }
        """)


        # --- Header ---
        # Etiqueta para mostrar el logo de la institución
        logo = QLabel()

        # Carga la imagen del logo
        pix = QPixmap("src/logo_institucion.jpeg")

        # Si la imagen existe correctamente, la ajusta y la coloca en el label
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))

        # Centra el contenido del logo
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiqueta con el nombre de la institución
        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")

        # Etiqueta con el lema institucional
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")

        # Layout vertical para agrupar nombre y lema
        text_layout = QVBoxLayout()
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)


        
        # Botón para cerrar completamente el programa
        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")
        btn_info.clicked.connect(self.close)


        # Layout horizontal del encabezado
        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(btn_info)


        # Línea separadora entre encabezado y contenido principal
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # --- Mensaje de bienvenida ---
        # Título principal de la ventana
        titulo = QLabel("Inicio sesión docente")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Mensaje de instrucción para el usuario
        mensaje = QLabel("Bienvenido. Por favor mirar la cámara para proceder con el inicio de sesión")
        mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiqueta que mostrará el nombre del docente reconocido
        self.lbl_docente = QLabel("Docente: [ninguno]")
        self.lbl_docente.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --- Cámara ---
        # Label donde se visualizará el video de la cámara
        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setStyleSheet("""
            background-color: rgba(255,255,255,0.08);
            border: 5px solid #1565C0;
            border-radius: 15px;
        """)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Label superpuesto dentro del área de la cámara para mostrar la guía visual
        self.lbl_guia = QLabel(self.lbl_camara)
        self.lbl_guia.setPixmap(self.guia_pix)
        self.lbl_guia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


        # --- Layout principal ---
        # Frame contenedor principal de la interfaz
        frame = QFrame()

        # Sombra para mejorar la apariencia visual del contenedor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)


        # Layout vertical principal con todos los elementos de la ventana
        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addWidget(mensaje)
        vbox.addWidget(self.lbl_docente)
        vbox.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)


        # Layout raíz de la ventana
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(frame)
    
    def confirmar_e_iniciar_sesion(self):
        # asegurarse de tener un docente detectado
        if not self.docente_detectado:
            QMessageBox.critical(self, "Error", "No se encontró la información del docente para iniciar sesión.")
            return


        # Mapear keys robustamente (dependen de cómo cargues docentes)
        d = self.docente_detectado
        usuario_data = {
            # Intenta obtener la cédula con distintos nombres posibles de clave
            "cedula": d.get("id_docente") or d.get("id") or d.get("cedula"),

            # Obtiene nombres del docente
            "nombres": d.get("nombres") or d.get("nombre"),

            # Obtiene apellidos del docente
            "apellidos": d.get("apellidos") or d.get("apellido"),

            # Obtiene el rol o usa "docente" por defecto
            "rol": d.get("rol") or "docente",

            # Normaliza la foto antes de guardarla en sesión
            "foto": normalizar_foto(d.get("foto_rostro") or d.get("foto"))
        }


        # iniciar sesión en memoria
        Sesion.iniciar_sesion(usuario_data)


        # abrir menú
        self.abrir_menu()


    def login(self):
        # Obtiene el texto del campo usuario eliminando espacios laterales
        usuario = self.txt_usuario.text().strip()

        # Obtiene el texto del campo contraseña eliminando espacios laterales
        contrasena = self.txt_contrasena.text().strip()


        # Crea la conexión a la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # Consulta si existe un usuario con esas credenciales
        cursor.execute("SELECT * FROM usuarios WHERE usuario=%s AND contrasena=%s", (usuario, contrasena))
        datos = cursor.fetchone()


        if datos:
            # Guardar sesión
            Sesion.iniciar_sesion({
                "id": self.docente_detectado["id"],
                "nombres": self.docente_detectado["nombres"],
                "apellidos": self.docente_detectado["apellidos"],
                "rol": "docente"
            })


            # Muestra mensaje de bienvenida con el rol del usuario autenticado
            QMessageBox.information(self, "Bienvenido", f"Has iniciado sesión como {datos['rol']}")

            # Abre el menú principal
            self.abrir_menu_principal()
        else:
            # Muestra advertencia si las credenciales no coinciden
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos")


        # Cierra el cursor de la consulta
        cursor.close()

        # Cierra la conexión a la base de datos
        cerrar_conexion(conexion)


    def update_frame(self):
        # Captura un frame de la cámara
        ret, frame = self.cap.read()

        # Si no se pudo capturar el frame, sale del método
        if not ret:
            return


        # Flip horizontal para efecto espejo
        frame = cv2.flip(frame, 1)

        # Convierte el frame de BGR a RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


        # Mostrar SIEMPRE video fluido en PyQt
        h, w, _ = rgb_frame.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        rgb_resized = cv2.resize(rgb_frame, (tw, th), interpolation=cv2.INTER_LINEAR)
        img = QImage(rgb_resized.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))
        self.lbl_guia.resize(self.lbl_camara.size())
        self.lbl_guia.move(0, 0)


        # Procesar detección SOLO cada 12 frames
        self.frame_count += 1
        if self.frame_count % 12 != 0:
            return


        # Reducir resolución para procesar más rápido
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)


        # ----------------------------
        # Reconocimiento de rostro
        # ----------------------------
        # Detecta la ubicación de los rostros en el frame reducido
        face_locations = face_recognition.face_locations(small_frame, model="hog")

        # Genera los encodings faciales de los rostros detectados
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)


        # Reinicia el docente detectado en cada ciclo de análisis
        self.docente_detectado = None

        if face_encodings:
            for face_encoding in face_encodings:
                # Compara el rostro actual con los encodings registrados de los docentes
                matches = face_recognition.compare_faces(
                    [d["encoding"] for d in self.docentes],
                    face_encoding,
                    tolerance=0.5
                )

                # Si hay coincidencia con algún docente registrado
                if True in matches:
                    idx = matches.index(True)
                    docente = self.docentes[idx]
                    self.docente_detectado = docente
                    self.lbl_docente.setText(f"Docente: {docente['nombres']} {docente['apellidos']}")
                    self.verificar_movimiento(face_encoding)
                    break

            # Si se detectó rostro, pero no coincide con ningún docente
            if not self.docente_detectado:
                self.lbl_docente.setText("Docente: No reconocido")
        else:
            # Si no se detecta ningún rostro en pantalla
            self.lbl_docente.setText("Docente: [ninguno]")


        # ----------------------------
        # Parpadeo (dlib)
        # ----------------------------
        # Detecta rostros en el frame completo usando dlib
        faces = self.detector(rgb_frame, 0)

        for face in faces:
            # Obtiene los puntos clave del rostro
            shape = self.predictor(rgb_frame, face)
            coords = np.array([[p.x, p.y] for p in shape.parts()])


            # Extrae los puntos correspondientes a cada ojo
            ojo_izq = coords[42:48]
            ojo_der = coords[36:42]

            # Calcula el EAR de cada ojo
            ear_izq = calcular_ear(ojo_izq)
            ear_der = calcular_ear(ojo_der)

            # Calcula el promedio entre ambos ojos
            ear = (ear_izq + ear_der) / 2.0


            if ear < 0.20:  # ojo cerrado
                # Guarda el instante en que se detectó un parpadeo
                self.ultimo_parpadeo = time.time()


        # ----------------------------
        # Validación automática
        # ----------------------------
        if self.docente_detectado:
            # Si el rostro no se ha movido en más de 5 segundos, lo considera sospechoso
            if time.time() - self.ultimo_movimiento > 5:
                self.lbl_docente.setText("❌ Rostro estático (posible foto)")

            # Si no ha parpadeado en más de 6 segundos, solicita al usuario parpadear
            elif time.time() - self.ultimo_parpadeo > 6:
                self.lbl_docente.setText("❌ Parpadea porfa")
            else:
                if not self.parpadeo_confirmado:
                    # Marca la validación como exitosa para no repetir el inicio de sesión
                    self.parpadeo_confirmado = True
                    self.lbl_docente.setText(
                        f"✅ Bienvenido {self.docente_detectado['nombres']} {self.docente_detectado['apellidos']}, redirigiendo..."
                    )

                    # esperar 3s y luego iniciar sesión y abrir menú
                    QTimer.singleShot(3000, self.confirmar_e_iniciar_sesion)


    def verificar_movimiento(self, encoding_actual):
        # Si ya existe un encoding previo, compara el actual con el anterior
        if self.ultimo_encoding is not None:
            distancia = np.linalg.norm(self.ultimo_encoding - encoding_actual)

            # Si la diferencia supera el umbral, se considera que hubo movimiento
            if distancia > 0.01:
                self.ultimo_movimiento = time.time()

        # Guarda el encoding actual para compararlo en el siguiente ciclo
        self.ultimo_encoding = encoding_actual


    def abrir_menu(self):
        # Libera la cámara antes de cambiar de ventana
        self.cap.release()


        # --- Chequeo de hardware antes del login ---
        from modules.hardware_checker import mostrar_chequeo_hardware
        hardware_info = mostrar_chequeo_hardware()
        
        # Guarda la info del hardware en la sesión para pasarla a las ventanas de ingreso
        from modules.sesion import Sesion
        Sesion.set_hardware_info(hardware_info)


        # Crea la interfaz administrativa
        self.menu = InterfazAdministrativa()

        # Muestra el menú maximizado
        self.menu.showMaximized()

        # Cierra la ventana actual de login
        self.close()


    def closeEvent(self, event):
        # Verifica que el atributo cap exista y no sea nulo
        if hasattr(self, "cap") and self.cap is not None:
            try:
                # Libera la cámara al cerrar la ventana
                self.cap.release()
            except:
                # Ignora cualquier error durante la liberación de la cámara
                pass

        # Ejecuta el comportamiento normal de cierre heredado de QWidget
        super().closeEvent(event)



if __name__ == "__main__":
    # Crea la aplicación principal de PyQt
    app = QApplication(sys.argv)

    # Crea la ventana de inicio de sesión
    ventana = InicioSesionDocente()

    # Muestra la ventana
    ventana.show()

    # Inicia el bucle principal de la aplicación
    sys.exit(app.exec())
