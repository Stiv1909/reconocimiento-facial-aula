import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QDialog, QMessageBox, QStackedLayout, QGraphicsOpacityEffect
)
from PyQt6.QtGui import QPixmap, QImage, QPainter
from PyQt6.QtCore import Qt, QTimer
import cv2
# Importación de funciones desde la lógica de negocio
from modules.estudiantes import (
    buscar_estudiantes,
    actualizar_datos,
    actualizar_rostro,
)
from modules.sesion import Sesion   # 👈 Importamos la sesión


# ==========================================================
#   FUNCIÓN: clave de ordenamiento grado + apellido
# ==========================================================
def clave_grado_apellido(est):
    try:
        grado_txt = est.get("grado", "") or ""
        # espera formato "NN-G" (ej. "10-2", "6-1")
        parts = grado_txt.split("-")
        if len(parts) >= 2:
            num = int(parts[0])
            grupo = int(parts[1])
            return (num, grupo, (est.get("apellidos") or "").lower())
        else:
            # fallback si no tiene guion
            return (999, 999, (est.get("apellidos") or "").lower())
    except Exception:
        return (999, 999, (est.get("apellidos") or "").lower())


# ==========================================================
#   CLASE: VentanaCapturaRostro
# ==========================================================
class VentanaCapturaRostro(QDialog):
    def __init__(self, id_estudiante, parent=None):
        super().__init__(parent)

        # 👇 Verificamos sesión
        if not Sesion.esta_autenticado():
            QMessageBox.critical(self, "Acceso denegado", "❌ Debes iniciar sesión para acceder a esta función.")
            self.close()
            return


        self.id_estudiante = id_estudiante
        self.setWindowTitle("📷 Actualizar Rostro - Institución Educativa del Sur")
        self.resize(950, 650)  # más espacio
        self.centrar_ventana()

        self.guia_pix = QPixmap("src/guia_silueta.png")
        self.init_ui()

        # detector de rostros
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

        # cámara
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.mostrar_frame)
        self.timer.start(30)

        self.foto_bytes = None
        self.ultimo_frame = None
        self.btn_tomar.clicked.connect(self.tomar_foto)
        self.btn_cancelar.clicked.connect(self.cancelar)

    def centrar_ventana(self):
        screen = QApplication.primaryScreen().availableGeometry()
        tamaño = self.frameGeometry()
        tamaño.moveCenter(screen.center())
        self.move(tamaño.topLeft())

    def init_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #0D1B2A; color: white; font-family: Arial; font-size: 14px;}
            QLabel#titulo { font-size: 22px; font-weight: bold; color: #E3F2FD; margin: 10px; }
            QLabel#mensaje { font-size: 18px; font-weight: bold; color: #4CAF50; margin: 6px; }
            QPushButton { border-radius: 6px; padding: 8px 16px; font-weight: bold; color: white; }
            QPushButton#btnTomar { background-color: rgba(21,101,192,0.8); }
            QPushButton#btnCancelar { background-color: rgba(198,40,40,0.8); }
            QPushButton:hover { opacity: 0.9; }
        """)

        main = QVBoxLayout(self)

        # Título
        titulo = QLabel("Actualizar Rostro del Estudiante")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(titulo)

        # Mensaje fijo (oculto visualmente pero ocupa espacio)
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setObjectName("mensaje")
        self.lbl_mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mensaje.setFixedHeight(30)  # asegura espacio fijo
        main.addWidget(self.lbl_mensaje)

        # Video
        self.lbl_video = QLabel()
        self.lbl_video.setFixedSize(800, 460)
        self.lbl_video.setStyleSheet("background-color: black; border-radius: 15px;")
        self.lbl_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.lbl_video, alignment=Qt.AlignmentFlag.AlignCenter)

        # overlay guía (silueta) → SIEMPRE visible
        self.lbl_guia = QLabel(self.lbl_video)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_guia.setStyleSheet("background: transparent; border: none;")
        self.guia_opacity = QGraphicsOpacityEffect(self.lbl_guia)
        self.guia_opacity.setOpacity(0.55)
        self.lbl_guia.setGraphicsEffect(self.guia_opacity)

        if not self.guia_pix.isNull():
            pix_guia = self.guia_pix.scaled(
                self.lbl_video.width(), self.lbl_video.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_guia.setPixmap(pix_guia)
            self.lbl_guia.resize(pix_guia.size())
            self.lbl_guia.move(
                (self.lbl_video.width() - pix_guia.width()) // 2,
                (self.lbl_video.height() - pix_guia.height()) // 2
            )
        self.lbl_guia.show()  # 👈 siempre visible

        # Botones
        botones = QHBoxLayout()
        self.btn_tomar = QPushButton("📸 Tomar Foto")
        self.btn_tomar.setObjectName("btnTomar")
        self.btn_tomar.setEnabled(False)
        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.setObjectName("btnCancelar")
        botones.addStretch()
        botones.addWidget(self.btn_tomar)
        botones.addWidget(self.btn_cancelar)
        botones.addStretch()
        main.addLayout(botones)

    def mostrar_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame = cv2.flip(frame, 1)
        self.ultimo_frame = frame.copy()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostros = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)

        if len(rostros) > 0:
            self.lbl_mensaje.setText("✅ Rostro detectado, capture la imagen")
            self.btn_tomar.setEnabled(True)
        else:
            self.lbl_mensaje.setText("")
            self.btn_tomar.setEnabled(False)

        # convertir frame para mostrar en QLabel
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix_video = QPixmap.fromImage(img).scaled(
            self.lbl_video.width(), self.lbl_video.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_video.setPixmap(pix_video)

    def tomar_foto(self):
        if self.ultimo_frame is None:
            QMessageBox.warning(self, "Error", "No se pudo capturar la imagen.")
            return

        rgb = cv2.cvtColor(self.ultimo_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(500, 350, Qt.AspectRatioMode.KeepAspectRatio)

        dlg = QDialog(self)
        dlg.setWindowTitle("Confirmar Foto")
        dlg.resize(550, 500)
        layout = QVBoxLayout(dlg)

        lbl_text = QLabel("¿Quieres usar esta foto?")
        lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_text.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(lbl_text)

        lbl_img = QLabel()
        lbl_img.setPixmap(pix)
        lbl_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_img)

        botones = QHBoxLayout()
        btn_yes = QPushButton("✅ Sí")
        btn_yes.setStyleSheet("background-color: #1565C0; color: white; padding: 8px 20px; border-radius: 8px; font-weight: bold;")
        btn_no = QPushButton("❌ No")
        btn_no.setStyleSheet("background-color: #C62828; color: white; padding: 8px 20px; border-radius: 8px; font-weight: bold;")
        botones.addStretch()
        botones.addWidget(btn_yes)
        botones.addWidget(btn_no)
        botones.addStretch()
        layout.addLayout(botones)

        btn_yes.clicked.connect(lambda: dlg.done(1))
        btn_no.clicked.connect(lambda: dlg.done(0))

        if dlg.exec() == 1:
            _, buffer = cv2.imencode(".jpg", self.ultimo_frame)
            self.foto_bytes = buffer.tobytes()
            if actualizar_rostro(self.id_estudiante, self.foto_bytes):
                QMessageBox.information(self, "Éxito", "✅ Rostro actualizado correctamente.")
            else:
                QMessageBox.critical(self, "Error", "❌ Ocurrió un error al guardar el rostro.")
            self.close()

    def cancelar(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("")

        # Ajustamos tamaño tipo tarjeta
        dlg.setFixedSize(420, 200)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #0D1B2A;
                border-radius: 15px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton {
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
                color: white;
                background-color: #C62828;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título tipo tarjeta
        lbl_titulo = QLabel("⚠ Acción Cancelada")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setStyleSheet("font-size: 18px; color: white;")
        layout.addWidget(lbl_titulo)

        # Mensaje
        lbl_msg = QLabel("La captura de rostro fue cancelada por el usuario.")
        lbl_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_msg)

        # Botón aceptar centrado
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(dlg.accept)
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignCenter)

        dlg.exec()
        self.close()


    def closeEvent(self, event):
        try:
            self.timer.stop()
        except Exception:
            pass
        if hasattr(self, "cap") and self.cap.isOpened():
            self.cap.release()
        super().closeEvent(event)


# ==========================================================
#   CLASE: EditarEstudiantes
# ==========================================================
class EditarEstudiantes(QWidget):
    def __init__(self):
        super().__init__()

        # 👇 Verificamos sesión
        if not Sesion.esta_autenticado():
            QMessageBox.critical(self, "Acceso denegado", "❌ Debes iniciar sesión para acceder a esta ventana.")
            self.close()
            return
        
        self.setWindowTitle("Editar Estudiantes - Institución Educativa del Sur")
        self.resize(1250, 670)
        self.centrar_ventana()
        self.init_ui()

    def centrar_ventana(self):
        screen = QApplication.primaryScreen().availableGeometry()
        tamaño = self.frameGeometry()
        tamaño.moveCenter(screen.center())
        self.move(tamaño.topLeft())

    def init_ui(self):
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
    QPushButton {
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: bold;
        color: white;
    }
    QPushButton#btnMenu { background-color: rgba(21, 101, 192, 0.60); }
    QPushButton#btnInfo { background-color: rgba(198,40,40,0.60); }
    QPushButton#btnBuscar { background-color: rgba(21, 101, 192, 0.60); font-size: 18px; }
    QPushButton#btnActualizar { background-color: rgba(21, 101, 192, 0.60); }
    QPushButton#btnRostro { background-color: rgba(198,40,40,0.60); }
    QPushButton:hover { opacity: 0.85; }
    QLineEdit, QComboBox {
        border: 1px solid #1565C0;
        border-radius: 5px;
        padding: 4px;
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

        # --- Header con logo ---
        logo = QLabel()
        pixmap_logo = QPixmap("src/logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo_colegio = QLabel(
            "<div style='text-align:left;'>"
            "<p style='font-size:32px; font-weight:bold; color:#E3F2FD; margin:0;'>Institución Educativa del Sur</p>"
            "<p style='font-size:18px; color:#aaa; margin:0;'>Compromiso y Superación</p>"
            "</div>"
        )
        titulo_colegio.setObjectName("tituloColegio")
        titulo_colegio.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_menu.clicked.connect(self.volver_menu)

        btn_info = QPushButton("CERRAR PROGRAMA")
        btn_info.setObjectName("btnInfo")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo)
        top_layout.addWidget(titulo_colegio)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("color: #444;")

        titulo = QLabel("EDITAR ESTUDIANTES")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: #E3F2FD; margin: 10px;")

        # --- Filtros ---
        lbl_nombre = QLabel("Estudiante:")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre completo")

        lbl_grado = QLabel("Grado:")
        self.cmb_grado = QComboBox()
        self.cmb_grado.setFixedWidth(100)
        # mantener el mismo orden lógico en el combo filtro (vacío + grados)
        self.cmb_grado.addItems([
            "", "6-1", "6-2", "6-3", "6-4",
            "7-1", "7-2", "7-3", "7-4",
            "8-1", "8-2", "8-3",
            "9-1", "9-2", "9-3",
            "10-1", "10-2", "10-3",
            "11-1", "11-2", "11-3"
        ])

        lbl_estado = QLabel("Estado:")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["", "Estudiante", "Ex-Alumno"])

        btn_buscar = QPushButton("🔍")
        btn_buscar.setObjectName("btnBuscar")
        btn_buscar.clicked.connect(self.buscar_estudiantes_ui)

        filtros_layout = QHBoxLayout()
        filtros_layout.addWidget(lbl_nombre)
        filtros_layout.addWidget(self.txt_nombre)
        filtros_layout.addWidget(lbl_grado)
        filtros_layout.addWidget(self.cmb_grado)
        filtros_layout.addWidget(lbl_estado)
        filtros_layout.addWidget(self.cmb_estado)
        filtros_layout.addWidget(btn_buscar)

        # --- Tabla ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Nombres", "Apellidos", "Grado", "Estado", "Actualizar Datos", "Actualizar Rostro"
        ])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setRowCount(0)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Ajuste altura de filas
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setShowGrid(False)
        self.tabla.verticalHeader().setDefaultSectionSize(50)

        self.lbl_inicial = QLabel("Realiza una búsqueda para mostrar resultados")
        self.lbl_inicial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_inicial.setStyleSheet("font-size: 16px; color: #aaa;")

        self.lbl_no_resultados = QLabel("No se encontraron estudiantes")
        self.lbl_no_resultados.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_no_resultados.setStyleSheet("font-size: 16px; color: #aaa;")

        self.stack_resultados = QStackedLayout()
        self.stack_resultados.addWidget(self.lbl_inicial)
        self.stack_resultados.addWidget(self.tabla)
        self.stack_resultados.addWidget(self.lbl_no_resultados)
        self.stack_resultados.setCurrentIndex(0)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(separador)
        main_layout.addWidget(titulo)
        main_layout.addLayout(filtros_layout)
        main_layout.addLayout(self.stack_resultados)

        self.setLayout(main_layout)   # 👈 ya no hay crecimiento infinito


    # ==========================================================
    #   FUNCIONES DE LÓGICA
    # ==========================================================
    def buscar_estudiantes_ui(self):
        nombre = self.txt_nombre.text().strip()
        grado = self.cmb_grado.currentText()
        estado = self.cmb_estado.currentText()

        resultados = buscar_estudiantes(nombre, grado, estado)
        # --- Ordenar: primero por grado (numérico), luego por apellido ---
        resultados = sorted(resultados, key=clave_grado_apellido)

        self.tabla.setRowCount(len(resultados))

        if resultados:
            self.stack_resultados.setCurrentIndex(1)
        else:
            self.stack_resultados.setCurrentIndex(2)

        for fila, est in enumerate(resultados):
            id_est = est.get("id_estudiante")
            nombre = est.get("nombres", "")
            apellido = est.get("apellidos", "")
            grado = est.get("grado", "")
            estado = est.get("estado", "")

            self.tabla.setItem(fila, 0, QTableWidgetItem(nombre))
            self.tabla.setItem(fila, 1, QTableWidgetItem(apellido))

            combo_grado = QComboBox()
            combo_grado.addItems([
                "6-1", "6-2", "6-3", "6-4",
                "7-1", "7-2", "7-3", "7-4",
                "8-1", "8-2", "8-3",
                "9-1", "9-2", "9-3",
                "10-1", "10-2", "10-3",
                "11-1", "11-2", "11-3"
            ])
            combo_grado.setCurrentText(grado or "")
            self.tabla.setCellWidget(fila, 2, combo_grado)

            combo_estado = QComboBox()
            combo_estado.addItems(["Estudiante", "Ex-Alumno"])
            combo_estado.setCurrentText(estado or "")
            self.tabla.setCellWidget(fila, 3, combo_estado)

            btn_actualizar = QPushButton("Actualizar")
            btn_actualizar.setObjectName("btnActualizar")
            # capturamos fila e id_est en defaults para evitar late-binding
            btn_actualizar.clicked.connect(lambda _, f=fila, i_est=id_est: self.actualizar_datos_ui(f, i_est))

            btn_rostro = QPushButton("Rostro")
            btn_rostro.setObjectName("btnRostro")
            btn_rostro.clicked.connect(lambda _, i=id_est: self.actualizar_rostro_ui(i))

            self.tabla.setCellWidget(fila, 4, btn_actualizar)
            self.tabla.setCellWidget(fila, 5, btn_rostro)

    def actualizar_datos_ui(self, fila, id_estudiante):
        # obtener datos de la fila (índices corregidos)
        nombre = self.tabla.item(fila, 0).text().strip() if self.tabla.item(fila, 0) else ""
        apellido = self.tabla.item(fila, 1).text().strip() if self.tabla.item(fila, 1) else ""
        nuevo_grado = self.tabla.cellWidget(fila, 2).currentText() if self.tabla.cellWidget(fila, 2) else ""
        nuevo_estado = self.tabla.cellWidget(fila, 3).currentText() if self.tabla.cellWidget(fila, 3) else ""

        if not nombre or not apellido:
            QMessageBox.warning(self, "Campos obligatorios", "⚠ Nombres y Apellidos no pueden estar vacíos.")
            return

        ok = actualizar_datos(id_estudiante, nombre, apellido, grado=nuevo_grado, estado=nuevo_estado)

        if ok:
            QMessageBox.information(self, "Actualización", f"✅ Datos de {nombre} {apellido} actualizados.")
            self.buscar_estudiantes_ui()
        else:
            QMessageBox.critical(self, "Error", "❌ Ocurrió un error al actualizar los datos.")

    def actualizar_rostro_ui(self, id_estudiante):
        ventana = VentanaCapturaRostro(id_estudiante, self)
        ventana.exec()

    def volver_menu(self):
        from menu import InterfazAdministrativa
        self.ventana_menu = InterfazAdministrativa()
        self.ventana_menu.showMaximized()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 👇 Antes de abrir la ventana, validamos si hay sesión
    if Sesion.esta_autenticado():
        ventana = EditarEstudiantes()
        ventana.showMaximized()
    else:
        QMessageBox.warning(None, "Sesión requerida", "⚠ Debes iniciar sesión para acceder al sistema.")

    sys.exit(app.exec())
