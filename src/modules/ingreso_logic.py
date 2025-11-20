# modules/ingreso_logic.py
import numpy as np
import cv2
import face_recognition
from modules.conexion import crear_conexion, cerrar_conexion
from modules.sesion import Sesion

# ----------------------------------------------------
# Generar variantes ligeras de la imagen para aumentar precisión
# ----------------------------------------------------
def generar_variantes(img):
    """Devuelve lista de imágenes con ligeras transformaciones"""
    variantes = [img]
    # Brillo ±10%
    for alpha in [0.9, 1.1]:
        variantes.append(cv2.convertScaleAbs(img, alpha=alpha, beta=0))
    # Rotaciones ±10°
    rows, cols, _ = img.shape
    for angle in [-10, 10]:
        M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
        variantes.append(cv2.warpAffine(img, M, (cols, rows)))
    return variantes

# ----------------------------------------------------
# Cargar estudiantes desde la base de datos (filtrado por grado opcional)
# Devuelve list of dicts: { "id", "nombre", "apellido", "encodings" }
# ----------------------------------------------------
def cargar_estudiantes(grado=None):
    conexion = crear_conexion()
    if not conexion:
        return []

    cursor = conexion.cursor()

    if grado:
        cursor.execute(
            """
            SELECT e.id_estudiante, e.nombres, e.apellidos, e.foto_rostro
            FROM estudiantes e
            INNER JOIN matriculas m 
                ON e.id_estudiante = m.id_estudiante
            INNER JOIN (
                SELECT id_estudiante, MAX(id_matricula) AS ultima_matricula
                FROM matriculas
                WHERE estado = 'Estudiante'
                GROUP BY id_estudiante
            ) ult 
                ON m.id_estudiante = ult.id_estudiante 
                AND m.id_matricula = ult.ultima_matricula
            WHERE m.grado = %s AND m.estado = 'Estudiante'
            """,
            (grado,)
        )
    else:
        cursor.execute(
            """
            SELECT e.id_estudiante, e.nombres, e.apellidos, e.foto_rostro
            FROM estudiantes e
            INNER JOIN matriculas m 
                ON e.id_estudiante = m.id_estudiante
            INNER JOIN (
                SELECT id_estudiante, MAX(id_matricula) AS ultima_matricula
                FROM matriculas
                WHERE estado = 'Estudiante'
                GROUP BY id_estudiante
            ) ult 
                ON m.id_estudiante = ult.id_estudiante 
                AND m.id_matricula = ult.ultima_matricula
            WHERE m.estado = 'Estudiante'
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
            encodings = []

            for var in generar_variantes(rgb):
                enc = face_recognition.face_encodings(var)
                if enc:
                    encodings.append(enc[0])

            if encodings:
                estudiantes.append({
                    "id": id_est,
                    "nombre": f"{nombres} {apellidos}",
                    "apellido": apellidos,
                    "encodings": encodings  # lista de encodings
                })
    finally:
        cursor.close()
        cerrar_conexion(conexion)

    return estudiantes

# ----------------------------------------------------
# Buscar hasta N estudiantes reconocidos en el frame
# Retorna lista de tuples (id_estudiante, nombre)
# ----------------------------------------------------
def buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=2, tolerance=0.45):
    if not estudiantes_conocidos:
        return []

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb_small, model="hog")
    if not locations:
        return []

    locations = locations[:max_faces]
    encodings_frame = face_recognition.face_encodings(rgb_small, locations)

    encontrados = []
    for enc in encodings_frame:
        match_found = False
        for est in estudiantes_conocidos:
            for est_enc in est["encodings"]:  # ahora iteramos sobre todas las variantes
                if face_recognition.compare_faces([est_enc], enc, tolerance=tolerance)[0]:
                    encontrados.append((est["id"], est["nombre"]))
                    match_found = True
                    break
            if match_found:
                break
        if len(encontrados) >= max_faces:
            break

    return encontrados

# ----------------------------------------------------
# Compatibilidad: función simple que devuelve primer match (id, nombre) o None
# ----------------------------------------------------
def buscar_estudiante_por_rostro(frame, estudiantes_conocidos, tolerance=0.45):
    encontrados = buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=1, tolerance=tolerance)
    return encontrados[0] if encontrados else None

# ----------------------------------------------------
# Asignar equipo a estudiante
# (igual que tu código original)
# ----------------------------------------------------
def asignar_equipo(id_estudiante):
    conexion = crear_conexion()
    if not conexion:
        return None

    cursor = conexion.cursor()
    try:
        usuario = Sesion.obtener_usuario()
        cedula_docente = usuario["cedula"] if usuario and "cedula" in usuario else None

        cursor.execute(
            "SELECT MAX(id_matricula) FROM matriculas WHERE id_estudiante = %s AND estado = 'Estudiante'",
            (id_estudiante,)
        )
        row = cursor.fetchone()
        matricula = row[0] if row else None
        if not matricula:
            return None

        cursor.execute(
            "SELECT id_equipo FROM historial WHERE id_matricula = %s AND hora_fin IS NULL",
            (matricula,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        cursor.execute("SELECT grado FROM matriculas WHERE id_matricula = %s", (matricula,))
        row = cursor.fetchone()
        if not row:
            return None
        grado = row[0]

        cursor.execute(
            """
            SELECT m.id_estudiante, e.apellidos
            FROM matriculas m
            INNER JOIN estudiantes e ON m.id_estudiante = e.id_estudiante
            INNER JOIN (
                SELECT id_estudiante, MAX(id_matricula) AS ultima_matricula
                FROM matriculas
                WHERE estado = 'Estudiante'
                GROUP BY id_estudiante
            ) ult ON m.id_estudiante = ult.id_estudiante AND m.id_matricula = ult.ultima_matricula
            WHERE m.grado = %s AND m.estado = 'Estudiante'
            """,
            (grado,)
        )
        filas = cursor.fetchall()
        if not filas:
            return None

        estudiantes_ordenados = sorted(filas, key=lambda x: (x[1].lower() if x[1] else ""))
        ids_ordenados = [f[0] for f in estudiantes_ordenados]

        try:
            pos = ids_ordenados.index(id_estudiante)
        except ValueError:
            return None

        codigo_equipo = f"E-{str(pos+1).zfill(2)}"

        cursor.execute("SELECT estado FROM equipos WHERE id_equipo = %s", (codigo_equipo,))
        equipo_row = cursor.fetchone()
        if not equipo_row:
            cursor.execute("SELECT id_equipo FROM equipos WHERE estado = 'disponible' ORDER BY id_equipo ASC LIMIT 1")
            r = cursor.fetchone()
            if not r:
                return None
            codigo_equipo = r[0]
        else:
            estado = equipo_row[0]
            if estado == "ocupado":
                cursor.execute("SELECT id_matricula FROM historial WHERE id_equipo = %s AND hora_fin IS NULL", (codigo_equipo,))
                occ = cursor.fetchone()
                if occ and occ[0] != matricula:
                    cursor.execute("SELECT id_equipo FROM equipos WHERE estado = 'disponible' ORDER BY id_equipo ASC LIMIT 1")
                    r = cursor.fetchone()
                    if not r:
                        return None
                    codigo_equipo = r[0]

        cursor.execute("SELECT estado FROM equipos WHERE id_equipo = %s", (codigo_equipo,))
        estado_row = cursor.fetchone()
        if estado_row and estado_row[0] != "ocupado":
            cursor.execute("UPDATE equipos SET estado = 'ocupado' WHERE id_equipo = %s", (codigo_equipo,))

        cursor.execute(
            """
            INSERT INTO historial (id_matricula, cedula, id_equipo, fecha, hora_inicio, hora_fin)
            VALUES (%s, %s, %s, CURDATE(), CURTIME(), NULL)
            """,
            (matricula, cedula_docente, codigo_equipo)
        )

        conexion.commit()
        return codigo_equipo

    finally:
        cursor.close()
        cerrar_conexion(conexion)

# ----------------------------------------------------
# Contar equipos con estado 'ocupado'
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
