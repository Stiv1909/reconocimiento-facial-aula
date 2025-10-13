import sys
import cv2
import time
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QFrame, QGraphicsDropShadowEffect, QMessageBox, QDialog, QComboBox
)
from PyQt6.QtGui import QPixmap, QImage, QColor
from PyQt6.QtCore import Qt, QTimer
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
from modules.hardware_checker import mostrar_chequeo_hardware
from modules.conexion import crear_conexion, cerrar_conexion

# ---------------------------
# Diálogo para seleccionar grado
# ---------------------------
class SeleccionarGradoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar grado")
        self.setFixedSize(300, 150)
        self.setStyleSheet("""
            QDialog { background-color: #0D1B2A; color: white; font-family: Arial; }
            QLabel { font-size: 14px; }
            QComboBox { font-size: 14px; padding: 5px; border-radius: 4px; }
            QPushButton { background-color: #1565C0; color: white; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background-color: #1976D2; }
        """)

        layout = QVBoxLayout()
        label = QLabel("Seleccione el grado:")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.combo_grado = QComboBox()
        layout.addWidget(self.combo_grado)

        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.clicked.connect(self.accept)
        layout.addWidget(btn_aceptar, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
        self.cargar_grados()

    def cargar_grados(self):
        """Carga los grados desde la base de datos."""
        conn = crear_conexion()
        if not conn:
            return
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT grado FROM matriculas WHERE estado='Estudiante' ORDER BY grado")
        for row in cur.fetchall():
            self.combo_grado.addItem(row[0])
        cur.close()
        cerrar_conexion(conn)

    def obtener_grado(self):
        return self.combo_grado.currentText()


# ---------------------------
# Ventana principal: SalidaEstudiantes
# ---------------------------
class SalidaEstudiantes(QWidget):
    def __init__(self, grado=None):
        super().__init__()
        self.setWindowTitle("Salida de Estudiantes")
        self.centrar_ventana(1250, 670)

        # Cámara y timer
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # Estado
        self.estudiantes_conocidos = []
        self.nombres_actuales = []
        self.last_seen = {}
        self.detectados_recientes = set()
        self.asistencias_registradas = False
        self.selected_grade = grado  # recibido del diálogo

        # Hardware info
        self.hardware_info = mostrar_chequeo_hardware()
        self.max_faces = self.hardware_info["max_faces"]

        # UI
        self.init_ui()

        # Cargar los estudiantes del grado seleccionado
        if self.selected_grade:
            self.on_cargar_grado()

        self.timer.start(30)

    def centrar_ventana(self, ancho, alto):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - ancho) // 2
        y = (screen.height() - alto) // 2
        self.setGeometry(x, y, ancho, alto)

    # ---------------------------
    # INTERFAZ GRÁFICA
    # ---------------------------
    def init_ui(self):
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
        logo = QLabel()
        pix = QPixmap("src/logo_institucion.jpeg")
        if not pix.isNull():
            logo.setPixmap(pix.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        nombre = QLabel("Institución Educativa del Sur")
        nombre.setObjectName("nombreColegio")
        lema = QLabel("Compromiso y Superación")
        lema.setObjectName("lemaColegio")

        text_layout = QVBoxLayout()
        text_layout.addWidget(nombre)
        text_layout.addWidget(lema)

        self.btn_menu = QPushButton("MENÚ")
        self.btn_menu.setObjectName("btnMenu")
        self.btn_menu.clicked.connect(self.volver_menu)

        self.btn_info = QPushButton("CERRAR PROGRAMA")
        self.btn_info.setObjectName("btnInfo")
        self.btn_info.clicked.connect(self.close)

        header = QHBoxLayout()
        header.addWidget(logo)
        header.addLayout(text_layout)
        header.addStretch()
        header.addWidget(self.btn_menu)
        header.addWidget(self.btn_info)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        titulo = QLabel(f"Salida de Estudiantes")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensaje = QLabel("Mire hacia la cámara para registrar su salida.")
        mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tarjetas
        self.cards = []
        self.nombres_actuales = [None] * self.max_faces
        cards_layout = QHBoxLayout()
        cards_layout.addStretch()
        for i in range(self.max_faces):
            card = self.crear_tarjeta(f"Salida {i + 1}", "Esperando rostro...")
            self.cards.append(card)
            cards_layout.addWidget(card)
        cards_layout.addStretch()

        self.lbl_contador = QLabel(f"Equipos ocupados: {contar_equipos_ocupados()}")
        self.lbl_contador.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_contador.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFD54F;")

        self.lbl_camara = QLabel()
        self.lbl_camara.setFixedSize(800, 350)
        self.lbl_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_camara.setStyleSheet("""
            background-color: rgba(0,0,139,0.5);
            border: 5px solid #1565C0;
            border-radius: 15px;
        """)

        self.btn_finalizar = QPushButton("Finalizar salida")
        self.btn_finalizar.setObjectName("btnFinalizar")
        self.btn_finalizar.clicked.connect(self.on_finalizar_salida)

        frame = QFrame()
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 150))
        frame.setGraphicsEffect(shadow)

        vbox = QVBoxLayout(frame)
        vbox.addLayout(header)
        vbox.addWidget(separador)
        vbox.addWidget(titulo)
        vbox.addWidget(mensaje)
        vbox.addLayout(cards_layout)
        vbox.addWidget(self.lbl_contador)
        vbox.addWidget(self.lbl_camara, alignment=Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(self.btn_finalizar, alignment=Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(frame)
        self.setLayout(layout)
        self.update_buttons_state()

    def crear_tarjeta(self, titulo, valor):
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame { background-color: rgba(0,0,255,0.01);
                     border: 2px solid #1565C0; border-radius: 12px; padding: 6px; }
            QLabel { color: white; }
            QLabel#titulo { font-size: 16px; font-weight: bold; color: #E3F2FD; }
            QLabel#valor { font-size: 14px; color: #FFFFFF; }
        """)
        vbox = QVBoxLayout(frame)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("valor")
        lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(lbl_titulo)
        vbox.addWidget(lbl_valor)
        frame.lbl_titulo = lbl_titulo
        frame.lbl_valor = lbl_valor
        frame.setFixedSize(250, 120)
        return frame

    # ---------------------------
    # Cargar grado
    # ---------------------------
    def on_cargar_grado(self):
        grado = self.selected_grade
        if not grado:
            QMessageBox.warning(self, "Grado inválido", "No se seleccionó un grado.")
            return

        try:
            estudiantes = cargar_estudiantes(grado)
        except TypeError:
            estudiantes = cargar_estudiantes()

        if not estudiantes:
            QMessageBox.information(self, "Sin datos", f"No hay estudiantes ocupando equipos en {grado}.")
            return

        self.estudiantes_conocidos = estudiantes
        self.nombres_actuales = [None] * self.max_faces
        self.detectados_recientes.clear()
        self.asistencias_registradas = False

        for i, card in enumerate(self.cards):
            card.lbl_titulo.setText(f"Salida {i + 1}")
            card.lbl_valor.setText("Esperando rostro...")

        self.lbl_contador.setText(f"Equipos ocupados: {contar_equipos_ocupados()}")
        self.update_buttons_state()
        QMessageBox.information(self, "Listo", f"Grado {grado} cargado. Puede comenzar a escanear.")

    def update_buttons_state(self):
        ocupados = contar_equipos_ocupados()
        enabled = (ocupados == 0)
        self.btn_menu.setEnabled(enabled)
        self.btn_info.setEnabled(enabled)

    # ---------------------------
    # Detección facial y registro
    # ---------------------------
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, _ = rgb.shape
        tw = self.lbl_camara.width()
        th = int(h * tw / w)
        resized = cv2.resize(rgb, (tw, th))
        img = QImage(resized.data, tw, th, 3 * tw, QImage.Format.Format_RGB888)
        self.lbl_camara.setPixmap(QPixmap.fromImage(img))

        if not self.selected_grade or not self.estudiantes_conocidos:
            return

        encontrados = buscar_estudiantes_en_frame(frame, self.estudiantes_conocidos, max_faces=self.max_faces)
        present = set(e["nombre"] for e in encontrados)

        for i, nombre_tarjeta in enumerate(self.nombres_actuales):
            if nombre_tarjeta is not None and nombre_tarjeta not in present:
                self.nombres_actuales[i] = None
                self.cards[i].lbl_titulo.setText(f"Salida {i + 1}")
                self.cards[i].lbl_valor.setText("Esperando rostro...")

        for estudiante in encontrados:
            nombre = estudiante["nombre"]
            id_est = estudiante["id"]

            if nombre in self.detectados_recientes or nombre in self.nombres_actuales:
                continue

            if None in self.nombres_actuales:
                idx = self.nombres_actuales.index(None)
                equipo = registrar_salida(id_est)
                if equipo:
                    self.nombres_actuales[idx] = nombre
                    self.cards[idx].lbl_titulo.setText(nombre)
                    self.cards[idx].lbl_valor.setText(f"Equipo liberado: {equipo}")
                    self.detectados_recientes.add(nombre)
                    self.lbl_contador.setText(f"Equipos ocupados: {contar_equipos_ocupados()}")
                    self.update_buttons_state()
                    self.estudiantes_conocidos = [e for e in self.estudiantes_conocidos if e["id"] != id_est]

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
        ocupados = contar_equipos_ocupados()
        if ocupados == 0:
            if not self.asistencias_registradas:
                try:
                    registrar_asistencia(self.selected_grade)
                except TypeError:
                    registrar_asistencia()
                self.asistencias_registradas = True
            self.volver_menu()
            return

        try:
            pendientes = estudiantes_pendientes(self.selected_grade)
        except TypeError:
            pendientes = estudiantes_pendientes()

        if pendientes:
            texto = "No se puede finalizar. Estudiantes pendientes:\n\n" + "\n".join(pendientes)
            QMessageBox.warning(self, "Pendientes", texto)

    # ---------------------------
    # Volver al menú
    # ---------------------------
    def volver_menu(self):
        from menu import InterfazAdministrativa
        try:
            self.timer.stop()
            self.cap.release()
        except Exception:
            pass
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()

    def closeEvent(self, event):
        try:
            self.timer.stop()
            self.cap.release()
        except Exception:
            pass
        super().closeEvent(event)


# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = SeleccionarGradoDialog()
    if dialog.exec() == QDialog.DialogCode.Accepted:
        grado = dialog.obtener_grado()
        if grado:
            ventana = SalidaEstudiantes(grado)
            ventana.showMaximized()
            sys.exit(app.exec())
    sys.exit(0)
