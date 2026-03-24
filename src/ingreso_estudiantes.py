# Importa módulos base del sistema y manejo de tiempo
import sys
import time

# Librería OpenCV para captura y procesamiento de video
import cv2

# Componentes gráficos de PyQt6
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QGraphicsDropShadowEffect, QComboBox, QDialog, QMessageBox
)

# Clases para manejo de imágenes y colores en PyQt
from PyQt6.QtGui import QPixmap, QImage, QColor

# Clases base de Qt para alineación y temporización
from PyQt6.QtCore import Qt, QTimer

# Librería de reconocimiento facial
import face_recognition


# Importamos la lógica
from modules.ingreso_logic import cargar_estudiantes, asignar_equipo, contar_equipos_ocupados
from modules.sesion import Sesion
from modules.hardware_checker import mostrar_chequeo_hardware



# ---------------------------------------------------
# Ventana principal - Ingreso estudiantes
# ---------------------------------------------------
class IngresoEstudiantes(QWidget):
    def __init__(self, grado):
        # Inicializa la clase base QWidget
        super().__init__()

        # Define el título de la ventana incluyendo el grado seleccionado
        self.setWindowTitle(f"Ingreso de Estudiantes - {grado}")

        # Centra la ventana en pantalla con el tamaño especificado
        self.centrar_ventana(1250, 670)


        # Estado cámara
        # Inicializa la cámara principal del sistema
        self.cap = cv2.VideoCapture(0)

        # Crea un temporizador para actualizar continuamente los frames de video
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)


        # Contador de frames para optimizar reconocimiento
        # Permite ejecutar el reconocimiento facial cada cierto número de frames
        self.frame_count = 0


        # Guía de silueta
        # Carga la guía visual superpuesta sobre el área de cámara
        self.guia_pix = QPixmap("") \
            .scaled(800, 350, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)


        # Cargamos estudiantes de ese grado desde la BD (ahora con variantes)
        self.estudiantes_conocidos = cargar_estudiantes(grado)


        if not self.estudiantes_conocidos:
            # Si no hay estudiantes en ese grado, regresa al menú principal
            from menu import InterfazAdministrativa
            QMessageBox.warning(self, "Sin datos", f"No se encontraron estudiantes en {grado}")
            self.ventana_menu = InterfazAdministrativa()
            self.ventana_menu.showMaximized()
            self.close()


            return


        # Estado persistente
        # Diccionario reservado para almacenar información persistente por estudiante
        self.last_seen = {}


        # --- Chequeo de hardware y capacidad de rostros ---
        # Obtiene información del hardware para adaptar la cantidad máxima de rostros a procesar
        self.hardware_info = mostrar_chequeo_hardware()
        self.max_faces = self.hardware_info["max_faces"]


        # Construye la interfaz gráfica
        self.init_ui()

        # Inicia el temporizador de actualización de cámara
        self.timer.start(30)


    def centrar_ventana(self, ancho, alto):
        # Obtiene la geometría de la pantalla principal
        screen = QApplication.primaryScreen().geometry()

        # Calcula la posición horizontal para centrar la ventana
        x = (screen.width() - ancho) // 2

        # Calcula la posición vertical para centrar la ventana
        y = (screen.height() - alto) // 2

        # Aplica posición y tamaño a la ventana
        self.setGeometry(x, y, ancho, alto)


    def init_ui(self):
        # Aplica estilos visuales generales a toda la ventana
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
            QPushButton#btnMenu     { background-color: rgba(21,101,192,0.6); }
            QPushButton#btnInfo     { background-color: rgba(198,40,40,0.60); }
            QPushButton#btnFinalizar{ background-color: rgba(21, 101, 192, 0.60); }
            QPushButton:hover       { opacity: 0.85; }
        """)


        # --- Header ---
        # Etiqueta para mostrar el logo institucional
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")

        # Si el logo existe, lo escala y lo coloca en la interfaz
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiquetas con el nombre y lema institucional
        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")


        # Layout vertical para agrupar nombre y lema
        text_layout = QVBoxLayout()
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)


        # Botón para regresar al menú principal
        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)

        # Botón para cerrar la ventana actual
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


        # Línea horizontal separadora
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")


        # --- Mensajes ---
        # Título principal del módulo
        titulo = QLabel("Ingreso de Estudiantes")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Mensaje de instrucción para el usuario
        mensaje = QLabel("Por favor mirar la cámara para el registro")
        mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # --- Tarjetas Dinamicas---
        # Lista que almacenará visualmente las tarjetas de asignación
        self.cards = []

        # Lista que almacena los nombres actualmente visibles en cada tarjeta
        self.nombres_actuales = [None] * self.max_faces  # se adapta dinámicamente


        # Layout horizontal para organizar las tarjetas
        cards_layout = QHBoxLayout()
        cards_layout.addStretch()


        for i in range(self.max_faces):
            # Crea una tarjeta por cada rostro máximo soportado por el hardware
            card = self.crear_tarjeta(f"Asignamiento {i + 1}", "Equipo #---")
            self.cards.append(card)
            cards_layout.addWidget(card)


        cards_layout.addStretch()


        # --- Contador ---
        # Muestra cuántos equipos están actualmente asignados
        self.lbl_contador = QLabel("Equipos asignados: 0")
        self.lbl_contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_contador.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #FFD54F;
        """)


        # --- Cámara ---
        # Label donde se mostrará el video de la cámara
        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setStyleSheet("""
            background-color: rgba(255,255,255,0.08);
            border: 5px solid #1565C0;
            border-radius: 15px;
        """)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Label hijo para superponer la guía visual sobre la cámara
        self.lbl_guia = QLabel(self.lbl_camara)
        self.lbl_guia.setPixmap(self.guia_pix)
        self.lbl_guia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)


        # --- Botón ---
        # Botón para finalizar el proceso y volver al menú
        btn_finalizar = QPushButton("Finalizar ingreso")
        btn_finalizar.setObjectName("btnFinalizar")
        btn_finalizar.clicked.connect(self.volver_menu)


        # --- Layout principal ---
        # Frame contenedor principal de la ventana
        frame = QFrame()

        # Efecto de sombra para mejorar la apariencia visual
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)


        # Layout vertical principal
        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addWidget(mensaje)
        vbox.addLayout(cards_layout)
        vbox.addWidget(self.lbl_contador)
        vbox.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(btn_finalizar, alignment=Qt.AlignmentFlag.AlignCenter)


        # Layout raíz de la ventana
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(frame)


    def volver_menu(self):
        # Importa el menú principal en el momento de volver
        from menu import InterfazAdministrativa

        # Libera la cámara antes de cambiar de ventana
        self.cap.release()

        # Abre la ventana del menú principal
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()


    def crear_tarjeta(self, titulo, valor):
        # Crea un frame que representará una tarjeta visual
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0,0,255,0.01);
                border: 2px solid #1565C0;
                border-radius: 12px;
            }
            QLabel {
                color: white;
            }
            QLabel#titulo {
                font-size: 16px;
                font-weight: bold;
                color: #E3F2FD;
            }
            QLabel#valor {
                font-size: 18px;
                font-weight: bold;
                color: #FFFFFF;
            }
        """)

        # Layout vertical interno de la tarjeta
        vbox = QVBoxLayout(frame)

        # Etiqueta para el título de la tarjeta
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Etiqueta para mostrar el valor principal de la tarjeta
        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("valor")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)


        # Agrega los labels al layout
        vbox.addWidget(lbl_titulo)
        vbox.addWidget(lbl_valor)
        frame.setLayout(vbox)
        frame.setFixedSize(250, 120)


        # Guarda referencias directas a las etiquetas para poder actualizarlas luego
        frame.lbl_valor = lbl_valor
        frame.lbl_titulo = lbl_titulo
        return frame


    # ---------------------------------------------------
    # Actualización de cámara y reconocimiento facial
    # ---------------------------------------------------
    def update_frame(self):
        # Captura un frame de la cámara
        ret, frame = self.cap.read()
        if not ret:
            return

        # Voltea el frame horizontalmente para efecto espejo
        frame = cv2.flip(frame, 1)


        # --- Mostrar cámara ---
        # Convierte el frame de BGR a RGB para mostrarlo en PyQt
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        rgb_resized = cv2.resize(rgb, (tw, th), interpolation=cv2.INTER_LINEAR)
        img = QImage(rgb_resized.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))
        self.lbl_guia.resize(self.lbl_camara.size())
        self.lbl_guia.move(0, 0)


        # --- Reconocimiento facial cada 5 frames ---
        self.frame_count += 1
        if self.frame_count % 5 == 0:
            # Lista temporal de nombres reconocidos en el frame actual
            nombres_en_frame = []

            # Reduce el tamaño del frame para acelerar el reconocimiento
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)


            # Detecta rostros y limita el número al máximo soportado por el hardware
            locations = face_recognition.face_locations(rgb_small, model="hog")[:self.max_faces]

            # Genera los encodings de los rostros detectados
            encodings_frame = face_recognition.face_encodings(rgb_small, locations)


            for encoding in encodings_frame:
                match_found = False
                for est in self.estudiantes_conocidos:
                    for est_enc in est["encodings"]:  # usamos todas las variantes
                        # Compara el rostro actual con los encodings del estudiante
                        if face_recognition.compare_faces([est_enc], encoding, tolerance=0.40)[0]:
                            nombre = est["nombre"]
                            id_est = est["id"]

                            # Evita agregar nombres duplicados en el mismo frame
                            if nombre not in [n for n, _ in nombres_en_frame]:
                                nombres_en_frame.append((nombre, id_est))
                            match_found = True
                            break
                    if match_found:
                        break


            # Conjunto de nombres actualmente presentes en cámara
            present = set(n for n, _ in nombres_en_frame)


            # --- Liberar tarjetas cuyos nombres ya no están en cámara ---
            for i, nombre_tarjeta in enumerate(self.nombres_actuales):
                if nombre_tarjeta is not None and nombre_tarjeta not in present:
                    self.nombres_actuales[i] = None  # liberar tarjeta
                    self.cards[i].lbl_titulo.setText(f"Asignamiento {i + 1}")
                    self.cards[i].lbl_valor.setText("Equipo #---")


            # --- Asignar nuevos rostros ---
            for nombre, id_est in nombres_en_frame:
                if nombre in self.nombres_actuales:
                    continue  # ya está asignado


                if None in self.nombres_actuales:
                    idx = self.nombres_actuales.index(None)
                    self.nombres_actuales[idx] = nombre


                    # Asignar equipo en BD
                    equipo = asignar_equipo(id_est)


                    self.cards[idx].lbl_titulo.setText(nombre)
                    self.cards[idx].lbl_valor.setText(f"Equipo: {equipo}")


            # --- Actualizar contador ---
            ocupados = contar_equipos_ocupados()
            self.lbl_contador.setText(f"Equipos asignados: {ocupados}")


    def closeEvent(self, event):
        # Detiene el temporizador de actualización
        self.timer.stop()

        # Libera la cámara
        self.cap.release()

        # Ejecuta el cierre normal de la ventana
        super().closeEvent(event)



# ---------------------------------------------------
# Main
# ---------------------------------------------------
if __name__ == "__main__":
    # Crea la aplicación principal de PyQt
    app = QApplication(sys.argv)

    # Informa que este módulo debe abrirse desde el menú principal
    QMessageBox.information(None, "Info", "Este módulo se abre desde el menú principal.")

    # Ejecuta el ciclo principal de la aplicación
    sys.exit(app.exec())
