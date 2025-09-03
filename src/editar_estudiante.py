import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QComboBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QDialog
)
from PyQt6.QtGui import QPixmap, QColor, QImage
from PyQt6.QtCore import Qt,QTimer
import cv2
import numpy as np
# Importa tu lógica desde otro archivo
from modules.estudiantes import buscar_estudiantes, actualizar_datos, actualizar_rostro


class VentanaCapturaRostro(QDialog):
    def __init__(self, id_estudiante, parent=None):
        super().__init__(parent)
        self.id_estudiante = id_estudiante
        self.setWindowTitle("Capturar Rostro")
        self.setGeometry(300, 200, 640, 520)

        # Layout
        layout = QVBoxLayout()

        # Label para mostrar la cámara
        self.lbl_video = QLabel()
        self.lbl_video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_video)

        # Botones
        botones_layout = QHBoxLayout()
        self.btn_tomar = QPushButton("📸 Tomar Foto")
        self.btn_cancelar = QPushButton("❌ Cancelar")
        botones_layout.addWidget(self.btn_tomar)
        botones_layout.addWidget(self.btn_cancelar)
        layout.addLayout(botones_layout)

        self.setLayout(layout)

        # Inicializar cámara
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.mostrar_frame)
        self.timer.start(30)

        # Conectar botones
        self.btn_tomar.clicked.connect(self.tomar_foto)
        self.btn_cancelar.clicked.connect(self.cancelar)

        self.foto_bytes = None

    def mostrar_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
            self.lbl_video.setPixmap(QPixmap.fromImage(img))

    def tomar_foto(self):
        ret, frame = self.cap.read()
        if ret:
            _, buffer = cv2.imencode(".jpg", frame)
            self.foto_bytes = buffer.tobytes()

            # Guardar en la DB
            from modules.estudiantes import actualizar_rostro
            if actualizar_rostro(self.id_estudiante, self.foto_bytes):
                print("✅ Rostro actualizado correctamente")
            else:
                print("❌ Error al guardar el rostro")

            self.close()

    def cancelar(self):
        print("⚠ Captura cancelada por el usuario")
        self.close()

    def closeEvent(self, event):
        self.timer.stop()
        if self.cap.isOpened():
            self.cap.release()
        super().closeEvent(event)

class EditarEstudiantes(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editar Estudiantes - Institución Educativa del Sur")
        self.setGeometry(200, 200, 1050, 650)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
                font-family: Arial;
                font-size: 14px;
            }
            QFrame {
                border: 2px solid #ddd;
                border-radius: 12px;
                background-color: white;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: bold;
                color: white;
            }
            QPushButton#btnMenu { background-color: #C62828; }
            QPushButton#btnInfo { background-color: #1565C0; }
            QPushButton#btnBuscar { background-color: #1565C0; font-size: 18px; }
            QPushButton#btnActualizar { background-color: #1565C0; }
            QPushButton#btnRostro { background-color: #C62828; }
            QPushButton:hover { opacity: 0.85; }
            QLineEdit, QComboBox {
                border: 1px solid #1565C0;
                border-radius: 5px;
                padding: 4px;
                background-color: white;
                color: black;
            }
            QTableWidget {
                border: 1px solid #ccc;
                gridline-color: #ccc;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #1565C0;
                color: white;
                font-weight: bold;
                padding: 4px;
            }
        """)

        frame = QFrame()
        shadow_frame = QGraphicsDropShadowEffect()
        shadow_frame.setBlurRadius(15)
        shadow_frame.setColor(QColor(0, 0, 0, 80))
        frame.setGraphicsEffect(shadow_frame)

        # --- Fila superior ---
        logo = QLabel()
        pixmap_logo = QPixmap(r"C:\Users\steven\Documents\2.GIT-GRADO\reconocimiento-facial-aula\src\logo_institucion.jpeg")
        if not pixmap_logo.isNull():
            pixmap_logo = pixmap_logo.scaled(70, 70, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pixmap_logo)
        else:
            logo.setText("Logo no encontrado")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_menu = QPushButton("MENÚ")
        btn_menu.setObjectName("btnMenu")
        btn_info = QPushButton("MÁS INFORMACIÓN")
        btn_info.setObjectName("btnInfo")

        top_layout = QHBoxLayout()
        top_layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignLeft)
        top_layout.addStretch()
        top_layout.addWidget(btn_menu)
        top_layout.addWidget(btn_info)

        # --- Título ---
        titulo = QLabel("EDITAR ESTUDIANTES")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: #C62828; margin: 5px;")

        # --- Filtros ---
        lbl_nombre = QLabel("Estudiante:")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre completo")

        lbl_grado = QLabel("Grado:")
        self.cmb_grado = QComboBox()
        self.cmb_grado.setMinimumWidth(70)
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
        filtros_layout.addSpacing(10)
        filtros_layout.addWidget(lbl_grado)
        filtros_layout.addWidget(self.cmb_grado)
        filtros_layout.addSpacing(10)
        filtros_layout.addWidget(lbl_estado)
        filtros_layout.addWidget(self.cmb_estado)
        filtros_layout.addSpacing(10)
        filtros_layout.addWidget(btn_buscar)

        # --- Barra "Estudiantes" ---
        barra_estudiantes = QLabel("ESTUDIANTES")
        barra_estudiantes.setStyleSheet("background-color: #1565C0; color: white; font-weight: bold; padding: 6px;")
        barra_estudiantes.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Tabla ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(["Nombres", "Apellidos", "Grado", "Estado", "Actualizar Datos", "Actualizar Rostro"])
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setRowCount(0)  # Vacía al inicio

        # Ajuste proporcional de columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Nombres
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Apellidos
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Grado
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Estado
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Botón Actualizar Datos
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Botón Actualizar Rostro

        # --- Layout interno ---
        frame_layout = QVBoxLayout()
        frame_layout.addLayout(top_layout)
        frame_layout.addWidget(titulo)
        frame_layout.addLayout(filtros_layout)
        frame_layout.addWidget(barra_estudiantes)
        frame_layout.addWidget(self.tabla)
        frame.setLayout(frame_layout)

        # --- Layout principal ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(frame)
        self.setLayout(main_layout)

    def buscar_estudiantes_ui(self):
        nombre = self.txt_nombre.text().strip()
        grado = self.cmb_grado.currentText()
        estado = self.cmb_estado.currentText()

        resultados = buscar_estudiantes(nombre, grado, estado)  # Llama a tu backend
        self.tabla.setRowCount(len(resultados))

        for fila, est in enumerate(resultados):
            id_est = est["id_estudiante"]
            nombre = est["nombres"]
            apellido = est["apellidos"]
            grado = est["grado"]
            estado = est["estado"]

            self.tabla.setItem(fila, 0, QTableWidgetItem(nombre))
            self.tabla.setItem(fila, 1, QTableWidgetItem(apellido))

            # 🔥 ComboBox para Grado
            combo_grado = QComboBox()
            combo_grado.addItems(["6-1", "6-2", "6-3", "6-4",
                                "7-1", "7-2", "7-3", "7-4",
                                "8-1", "8-2", "8-3",
                                "9-1", "9-2", "9-3",
                                "10-1", "10-2", "10-3",
                                "11-1", "11-2", "11-3"])
            combo_grado.setMinimumWidth(70)   # 👈 ancho mínimo dentro de la celda
            if grado in [combo_grado.itemText(i) for i in range(combo_grado.count())]:
                combo_grado.setCurrentText(grado)
            self.tabla.setCellWidget(fila, 2, combo_grado)

            # 🔥 ComboBox para Estado
            combo_estado = QComboBox()
            combo_estado.addItems(["Estudiante", "Ex-Alumno"])
            if estado in [combo_estado.itemText(i) for i in range(combo_estado.count())]:
                combo_estado.setCurrentText(estado)
            self.tabla.setCellWidget(fila, 3, combo_estado)

            # Botón Actualizar
            btn_actualizar = QPushButton("Actualizar Datos")
            btn_actualizar.setObjectName("btnActualizar")
            btn_actualizar.clicked.connect(lambda _, f=fila, i=id_est: self.actualizar_datos_ui(f, i))

            btn_rostro = QPushButton("Actualizar Rostro")
            btn_rostro.setObjectName("btnRostro")
            btn_rostro.clicked.connect(lambda _, i=id_est: self.actualizar_rostro_ui(i))

            self.tabla.setCellWidget(fila, 4, btn_actualizar)
            self.tabla.setCellWidget(fila, 5, btn_rostro)


    def actualizar_datos_ui(self, fila, id_estudiante):
        nombre = self.tabla.item(fila, 0).text()
        apellido = self.tabla.item(fila, 1).text()
        grado = self.tabla.cellWidget(fila, 2).currentText()
        estado = self.tabla.cellWidget(fila, 3).currentText()
        ok = actualizar_datos(id_estudiante, nombre, apellido, grado, estado)
        if ok:
            # Refrescar búsqueda con los filtros actuales
            self.buscar_estudiantes_ui()

    def actualizar_rostro_ui(self, id_estudiante):
        ventana = VentanaCapturaRostro(id_estudiante, self)
        ventana.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = EditarEstudiantes()
    ventana.show()
    sys.exit(app.exec())
