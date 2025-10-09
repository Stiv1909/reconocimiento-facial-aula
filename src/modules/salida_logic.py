import numpy as np
import cv2
import face_recognition
from datetime import datetime
from modules.conexion import crear_conexion, cerrar_conexion


# ----------------------------------------------------
# Cargar estudiantes con equipos ocupados (última matrícula activa)
# ----------------------------------------------------
def cargar_estudiantes():
    conexion = crear_conexion()
    if not conexion:
        return []

    cursor = conexion.cursor()
    cursor.execute(
        """
        SELECT e.id_estudiante, e.nombres, e.apellidos, e.foto_rostro
        FROM estudiantes e
        INNER JOIN matriculas m ON e.id_estudiante = m.id_estudiante
        INNER JOIN historial h ON h.id_matricula = m.id_matricula
        INNER JOIN equipos eq ON eq.id_equipo = h.id_equipo
        WHERE m.estado = 'Estudiante' AND eq.estado = 'ocupado'
        GROUP BY e.id_estudiante
        """
    )

    estudiantes = []
    try:
        for id_est, nombres, apellidos, foto_blob in cursor.fetchall():
            if foto_blob is None:
                continue

            np_arr = np.frombuffer(foto_blob, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                continue

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)
            if len(encodings) > 0:
                estudiantes.append({
                    "id": id_est,
                    "nombre": f"{nombres} {apellidos}",
                    "encoding": encodings[0]
                })
    finally:
        cursor.close()
        cerrar_conexion(conexion)

    return estudiantes


# ----------------------------------------------------
# Buscar estudiantes reconocidos en el frame
# ----------------------------------------------------
def buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=2, tolerance=0.5):
    if not estudiantes_conocidos:
        return []

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb_small, model="hog")
    if not locations:
        return []

    locations = locations[:max_faces]
    encodings = face_recognition.face_encodings(rgb_small, locations)
    conocidos_enc = [e["encoding"] for e in estudiantes_conocidos]

    encontrados = []
    for enc in encodings:
        matches = face_recognition.compare_faces(conocidos_enc, enc, tolerance=tolerance)
        if True in matches:
            idx = matches.index(True)
            encontrados.append(estudiantes_conocidos[idx])
            if len(encontrados) >= max_faces:
                break

    return encontrados


# ----------------------------------------------------
# Registrar salida del estudiante (actualiza historial y libera equipo)
# ----------------------------------------------------
def registrar_salida(id_estudiante):
    conexion = crear_conexion()
    if not conexion:
        return None

    cursor = conexion.cursor()
    try:
        # 1) Obtener la última matrícula activa
        cursor.execute(
            "SELECT MAX(id_matricula) FROM matriculas WHERE id_estudiante = %s AND estado = 'Estudiante'",
            (id_estudiante,)
        )
        row = cursor.fetchone()
        matricula = row[0] if row else None
        if not matricula:
            return None

        # 2) Buscar si tiene sesión activa
        cursor.execute(
            "SELECT h.id_equipo FROM historial h WHERE h.id_matricula = %s AND h.hora_fin IS NULL",
            (matricula,)
        )
        row = cursor.fetchone()
        if not row:
            return None

        id_equipo = row[0]

        # 3) Registrar hora de salida
        cursor.execute(
            "UPDATE historial SET hora_fin = CURTIME() WHERE id_matricula = %s AND id_equipo = %s AND hora_fin IS NULL",
            (matricula, id_equipo)
        )

        # 4) Liberar equipo
        cursor.execute("UPDATE equipos SET estado = 'disponible' WHERE id_equipo = %s", (id_equipo,))

        conexion.commit()
        return id_equipo

    finally:
        cursor.close()
        cerrar_conexion(conexion)


# ----------------------------------------------------
# Contar equipos aún ocupados
# ----------------------------------------------------
def contar_equipos_ocupados():
    conexion = crear_conexion()
    if not conexion:
        return 0

    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM equipos WHERE estado = 'ocupado'")
        row = cursor.fetchone()
        return row[0] if row else 0
    finally:
        cursor.close()
        cerrar_conexion(conexion)


# ----------------------------------------------------
# Obtener estudiantes pendientes por salida
# ----------------------------------------------------
def estudiantes_pendientes():
    conexion = crear_conexion()
    if not conexion:
        return []

    cursor = conexion.cursor()
    try:
        cursor.execute(
            """
            SELECT CONCAT(e.nombres, ' ', e.apellidos) AS nombre
            FROM estudiantes e
            INNER JOIN matriculas m ON e.id_estudiante = m.id_estudiante
            INNER JOIN historial h ON h.id_matricula = m.id_matricula
            INNER JOIN equipos eq ON eq.id_equipo = h.id_equipo
            WHERE eq.estado = 'ocupado'
            GROUP BY e.id_estudiante
            """
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        cerrar_conexion(conexion)


# ----------------------------------------------------
# Registrar asistencias cuando todos hayan salido
# ----------------------------------------------------
def registrar_asistencia(grado=None):
    conexion = crear_conexion()
    if not conexion:
        return

    cursor = conexion.cursor()
    try:
        # 1️⃣ Si se pasa un grado, usarlo directamente; si no, tomar el primero activo
        if not grado:
            cursor.execute("SELECT grado FROM matriculas WHERE estado = 'Estudiante' LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return
            grado = row[0]

        # 2️⃣ Obtener estudiantes de ese grado
        cursor.execute("""
            SELECT e.id_estudiante, m.id_matricula
            FROM estudiantes e
            INNER JOIN matriculas m ON e.id_estudiante = m.id_estudiante
            WHERE m.grado = %s AND m.estado = 'Estudiante'
        """, (grado,))
        estudiantes = cursor.fetchall()

        if not estudiantes:
            print(f"No hay estudiantes registrados en el grado {grado}")
            return

        # 3️⃣ Obtener los que usaron equipo hoy
        cursor.execute("""
            SELECT DISTINCT m.id_matricula
            FROM historial h
            INNER JOIN matriculas m ON m.id_matricula = h.id_matricula
            WHERE DATE(h.hora_inicio) = CURDATE()
        """)
        presentes = [row[0] for row in cursor.fetchall()]

        # 4️⃣ Registrar asistencias
        fecha_hoy = datetime.now().date()
        for id_est, id_matricula in estudiantes:
            estado = 'presente' if id_matricula in presentes else 'ausente'
            cursor.execute("""
                INSERT INTO asistencias (id_matricula, fecha, estado)
                VALUES (%s, %s, %s)
            """, (id_matricula, fecha_hoy, estado))

        conexion.commit()
        print(f"Asistencia registrada correctamente para el grado {grado}")

    finally:
        cursor.close()
        cerrar_conexion(conexion)

