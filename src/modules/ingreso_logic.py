# modules/ingreso_logic.py
import numpy as np
import cv2
import face_recognition
from modules.conexion import crear_conexion, cerrar_conexion
from modules.sesion import Sesion


# ----------------------------------------------------
# Cargar estudiantes desde la base de datos (filtrado por grado opcional)
# Devuelve list of dicts: { "id", "nombre", "apellido", "encoding" }
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
            encodings = face_recognition.face_encodings(rgb)
            if len(encodings) > 0:
                estudiantes.append({
                    "id": id_est,
                    "nombre": f"{nombres} {apellidos}",
                    "apellido": apellidos,
                    "encoding": encodings[0]
                })
    finally:
        cursor.close()
        cerrar_conexion(conexion)

    return estudiantes


# ----------------------------------------------------
# Buscar hasta N estudiantes reconocidos en el frame
# Retorna lista de tuples (id_estudiante, nombre)
# ----------------------------------------------------
def buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=2, tolerance=0.5):
    if not estudiantes_conocidos:
        return []

    # Reducimos la imagen (más rápido)
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Detectamos ubicaciones y encodings (modelo HOG por ser más rápido en CPU)
    locations = face_recognition.face_locations(rgb_small, model="hog")
    if not locations:
        return []

    locations = locations[:max_faces]
    encodings = face_recognition.face_encodings(rgb_small, locations)

    conocidos_enc = [est["encoding"] for est in estudiantes_conocidos]

    encontrados = []
    for enc in encodings:
        matches = face_recognition.compare_faces(conocidos_enc, enc, tolerance=tolerance)
        if True in matches:
            idx = matches.index(True)
            encontrados.append((estudiantes_conocidos[idx]["id"], estudiantes_conocidos[idx]["nombre"]))
            if len(encontrados) >= max_faces:
                break

    return encontrados


# ----------------------------------------------------
# Compatibilidad: función simple que devuelve primer match (id, nombre) o None
# ----------------------------------------------------
def buscar_estudiante_por_rostro(frame, estudiantes_conocidos, tolerance=0.5):
    encontrados = buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=1, tolerance=tolerance)
    return encontrados[0] if encontrados else None


# ----------------------------------------------------
# Asignar equipo a estudiante
# Reglas:
#  - Si ya tiene asignación activa (historial.hora_fin IS NULL) devuelve esa misma.
#  - Si no, calcula posición por apellido dentro del grado -> E-01, E-02, ...
#  - Inserta registro en historial (hora_fin NULL) y marca equipo ocupado.
#  - Guarda la cédula del docente desde Sesion (key: "cedula").
#  - NO registra salidas (NO actualización de hora_fin aquí).
# ----------------------------------------------------
def asignar_equipo(id_estudiante):
    conexion = crear_conexion()
    if not conexion:
        return None

    cursor = conexion.cursor()

    try:
        # 0) docente en sesión (cedula)
        usuario = Sesion.obtener_usuario()
        cedula_docente = usuario["cedula"] if usuario and "cedula" in usuario else None

        # 1) Determinar matrícula activa (la última) del estudiante
        cursor.execute(
            "SELECT MAX(id_matricula) FROM matriculas WHERE id_estudiante = %s AND estado = 'Estudiante'",
            (id_estudiante,)
        )
        row = cursor.fetchone()
        matricula = row[0] if row else None
        if not matricula:
            return None

        # 2) Si ya tiene asignación activa (para esa matrícula), devolverla
        cursor.execute(
            "SELECT id_equipo FROM historial WHERE id_matricula = %s AND hora_fin IS NULL",
            (matricula,)
        )
        row = cursor.fetchone()
        if row:
            return row[0]

        # 3) Obtener grado de la matrícula
        cursor.execute("SELECT grado FROM matriculas WHERE id_matricula = %s", (matricula,))
        row = cursor.fetchone()
        if not row:
            return None
        grado = row[0]

        # 4) Obtener lista de estudiantes del mismo grado (usando la última matrícula por estudiante)
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

        # 5) Ordenar por apellido (case-insensitive), construir lista ordenada de ids
        estudiantes_ordenados = sorted(filas, key=lambda x: (x[1].lower() if x[1] else ""))
        ids_ordenados = [f[0] for f in estudiantes_ordenados]

        # 6) Encontrar posición del estudiante
        try:
            pos = ids_ordenados.index(id_estudiante)
        except ValueError:
            return None

        # 7) Código de equipo según posición (E-01, E-02, ...)
        codigo_equipo = f"E-{str(pos+1).zfill(2)}"

        # 8) Verificar si ese equipo existe
        cursor.execute("SELECT estado FROM equipos WHERE id_equipo = %s", (codigo_equipo,))
        equipo_row = cursor.fetchone()
        if not equipo_row:
            # Si no existe el equipo con ese código, fallback a primer equipo disponible
            cursor.execute("SELECT id_equipo FROM equipos WHERE estado = 'disponible' ORDER BY id_equipo ASC LIMIT 1")
            r = cursor.fetchone()
            if not r:
                return None
            codigo_equipo = r[0]
        else:
            # Si existe y está ocupado por otra matrícula activa, fallback también
            estado = equipo_row[0]
            if estado == "ocupado":
                # comprobar a quién pertenece esa ocupación (historial activo)
                cursor.execute("SELECT id_matricula FROM historial WHERE id_equipo = %s AND hora_fin IS NULL", (codigo_equipo,))
                occ = cursor.fetchone()
                if occ and occ[0] != matricula:
                    # ocupado por otro -> elegir primer disponible como fallback
                    cursor.execute("SELECT id_equipo FROM equipos WHERE estado = 'disponible' ORDER BY id_equipo ASC LIMIT 1")
                    r = cursor.fetchone()
                    if not r:
                        return None
                    codigo_equipo = r[0]

        # 9) Marcar equipo como ocupado (si no lo está)
        cursor.execute("SELECT estado FROM equipos WHERE id_equipo = %s", (codigo_equipo,))
        estado_row = cursor.fetchone()
        if estado_row and estado_row[0] != "ocupado":
            cursor.execute("UPDATE equipos SET estado = 'ocupado' WHERE id_equipo = %s", (codigo_equipo,))

        # 10) Insertar registro en historial (id_matricula, cedula_docente, id_equipo, fecha, hora_inicio, hora_fin NULL)
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
# Retorna un entero con la cantidad de equipos ocupados
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
