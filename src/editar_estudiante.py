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


# ==========================================================
#   CLASE: VentanaCapturaRostro
# ==========================================================
class VentanaCapturaRostro(QDialog):
    def __init__(self, id_estudiante, parent=None):
        super().__init__(parent)
        self.id_estudiante = id_estudiante
        self.setWindowTitle("📷 Actualizar Rostro - Institución Educativa del Sur")
        self.resize(900, 600)
        self.centrar_ventana()

        self.guia_pix = QPixmap("src/guia_silueta.png")
        self.init_ui()

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
            QPushButton { border-radius: 6px; padding: 8px 16px; font-weight: bold; color: white; }
            QPushButton#btnTomar { background-color: rgba(21,101,192,0.8); }
            QPushButton#btnCancelar { background-color: rgba(198,40,40,0.8); }
            QPushButton:hover { opacity: 0.9; }
        """)

        main = QVBoxLayout(self)

        titulo = QLabel("Actualizar Rostro del Estudiante")
        titulo.setObjectName("titulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(titulo)

        self.lbl_video = QLabel()
        self.lbl_video.setFixedSize(800, 450)  # proporción 16:9
        self.lbl_video.setStyleSheet("""
            background-color: black;
            border-radius: 15px;
        """)
        self.lbl_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main.addWidget(self.lbl_video, alignment=Qt.AlignmentFlag.AlignCenter)

        # overlay guía (sin marco)
        self.lbl_guia = QLabel(self.lbl_video)
        self.lbl_guia.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.lbl_guia.setStyleSheet("background: transparent; border: none;")
        self.guia_opacity = QGraphicsOpacityEffect(self.lbl_guia)
        self.guia_opacity.setOpacity(0.55)
        self.lbl_guia.setGraphicsEffect(self.guia_opacity)
        self.lbl_guia.hide()

        botones = QHBoxLayout()
        self.btn_tomar = QPushButton("📸 Tomar Foto")
        self.btn_tomar.setObjectName("btnTomar")
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

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix_video = QPixmap.fromImage(img)

        target_w = self.lbl_video.width()
        target_h = self.lbl_video.height()

        scaled_pix = pix_video.scaled(
            target_w, target_h,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        crop_x = (scaled_pix.width() - target_w) // 2
        crop_y = (scaled_pix.height() - target_h) // 2
        cropped = scaled_pix.copy(crop_x, crop_y, target_w, target_h)

        self.lbl_video.setPixmap(cropped)

        if not self.guia_pix.isNull():
            pix_guia = self.guia_pix.scaled(
                target_w, target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_guia.setPixmap(pix_guia)
            self.lbl_guia.resize(pix_guia.size())
            self.lbl_guia.move((target_w - pix_guia.width()) // 2,
                               (target_h - pix_guia.height()) // 2)
            self.lbl_guia.show()
        else:
            self.lbl_guia.hide()

    def tomar_foto(self):
        if self.ultimo_frame is None:
            QMessageBox.warning(self, "Error", "No se pudo capturar la imagen.")
            return

        # convertir a QPixmap para mostrar en preview
        rgb = cv2.cvtColor(self.ultimo_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(img).scaled(500, 350, Qt.AspectRatioMode.KeepAspectRatio)

        # diálogo personalizado
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
        # si elige No, regresa a la cámara

    def cancelar(self):
        QMessageBox.warning(self, "Cancelado", "⚠ Captura cancelada por el usuario.")
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
    QPushButton#btnMenu { background-color: rgba(198,40,40,0.60); }
    QPushButton#btnInfo { background-color: rgba(21, 101, 192, 0.60); }
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

        btn_info = QPushButton("MÁS INFORMACIÓN")
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
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID Matrícula", "Nombres", "Apellidos", "Grado", "Estado", "Actualizar Datos", "Actualizar Rostro"
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
        self.tabla.setRowCount(len(resultados))

        if resultados:
            self.stack_resultados.setCurrentIndex(1)
        else:
            self.stack_resultados.setCurrentIndex(2)

        for fila, est in enumerate(resultados):
            id_est = est["id_estudiante"]
            id_mat = est["id_matricula"]
            nombre = est["nombres"]
            apellido = est["apellidos"]
            grado = est["grado"]
            estado = est["estado"]

            self.tabla.setItem(fila, 0, QTableWidgetItem(str(id_mat)))
            self.tabla.setItem(fila, 1, QTableWidgetItem(nombre))
            self.tabla.setItem(fila, 2, QTableWidgetItem(apellido))

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
            self.tabla.setCellWidget(fila, 3, combo_grado)

            combo_estado = QComboBox()
            combo_estado.addItems(["Estudiante", "Ex-Alumno"])
            combo_estado.setCurrentText(estado or "")
            self.tabla.setCellWidget(fila, 4, combo_estado)

            btn_actualizar = QPushButton("Actualizar")
            btn_actualizar.setObjectName("btnActualizar")
            btn_actualizar.clicked.connect(lambda _, f=fila, i_est=id_est, i_mat=id_mat: self.actualizar_datos_ui(f, i_est, i_mat))

            btn_rostro = QPushButton("Rostro")
            btn_rostro.setObjectName("btnRostro")
            btn_rostro.clicked.connect(lambda _, i=id_est: self.actualizar_rostro_ui(i))

            self.tabla.setCellWidget(fila, 5, btn_actualizar)
            self.tabla.setCellWidget(fila, 6, btn_rostro)

    def actualizar_datos_ui(self, fila, id_estudiante, id_matricula):
        nombre = self.tabla.item(fila, 1).text().strip()
        apellido = self.tabla.item(fila, 2).text().strip()
        nuevo_grado = self.tabla.cellWidget(fila, 3).currentText()
        nuevo_estado = self.tabla.cellWidget(fila, 4).currentText()

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
        self.ventana_menu.show()
        self.ventana_menu.centrar_ventana(1000, 600)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = EditarEstudiantes()
    ventana.show()
    sys.exit(app.exec())
