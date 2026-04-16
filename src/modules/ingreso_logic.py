# modules/ingreso_logic.py

# Permite codificar y decodificar datos en base64
import base64

# Librería para operaciones numéricas y manejo de arreglos
import numpy as np

# Librería OpenCV para procesamiento de imágenes
import cv2

# Librería para reconocimiento facial
import face_recognition

# Funciones para abrir y cerrar conexión con la base de datos
from modules.conexion import crear_conexion, cerrar_conexion

# Clase para obtener los datos del usuario en sesión
from modules.sesion import Sesion

# Librería para trabajar con MySQL
import pymysql

# ----------------------------------------------------
# Generar variantes ligeras de la imagen para aumentar precisión
# ----------------------------------------------------
def generar_variantes(img):
    """Devuelve lista de imágenes con ligeras transformaciones"""

    # Lista inicial que contiene la imagen original
    variantes = [img]

    # Brillo ±10%
    # Genera versiones con un poco menos y un poco más de brillo
    for alpha in [0.9, 1.1]:
        variantes.append(cv2.convertScaleAbs(img, alpha=alpha, beta=0))

    # Rotaciones ±10°
    # Obtiene dimensiones de la imagen
    rows, cols, _ = img.shape

    # Genera imágenes rotadas levemente a la izquierda y a la derecha
    for angle in [-10, 10]:
        M = cv2.getRotationMatrix2D((cols/2, rows/2), angle, 1)
        variantes.append(cv2.warpAffine(img, M, (cols, rows)))

    # Retorna la lista de imágenes generadas
    return variantes


# ----------------------------------------------------
# Cargar estudiantes desde la base de datos (filtrado por grado opcional)
# Devuelve list of dicts: { "id", "nombre", "apellido", "encodings" }
# ----------------------------------------------------
# ----------------------------------------------------


def cargar_estudiantes(grado=None):
    # Importación local de pymysql, se mantiene tal como está en el código original
    import pymysql

    # Crea conexión con la base de datos
    conexion = crear_conexion()

    # Si no hay conexión, retorna lista vacía
    if not conexion:
        return []


    # DictCursor para que los campos BLOB vengan como bytes
    cursor = conexion.cursor(pymysql.cursors.DictCursor)


    try:
        # Si se especifica un grado, filtra estudiantes por ese grado
        if grado:
            cursor.execute("""
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
            """, (grado,))
        else:
            # Si no se especifica grado, obtiene todos los estudiantes activos
            cursor.execute("""
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
            """)


        # Lista donde se almacenarán los estudiantes procesados
        estudiantes = []

        for row in cursor.fetchall():
            # Extrae la foto almacenada como BLOB
            foto_blob = row["foto_rostro"]

            # Si no hay foto, se omite el registro
            if foto_blob is None:
                continue


            # Decodificar la imagen desde BLOB
            np_arr = np.frombuffer(foto_blob, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # Si la imagen no pudo reconstruirse correctamente, se omite
            if img is None:
                print(f"No se pudo decodificar la imagen del estudiante {row['id_estudiante']}")
                continue


            # Convierte la imagen de BGR a RGB para face_recognition
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Genera los encodings faciales del estudiante
            encodings = face_recognition.face_encodings(rgb)

            # Si no se pudo generar ningún encoding, se omite
            if not encodings:
                continue


            # Agrega el estudiante procesado a la lista final
            estudiantes.append({
                "id": row["id_estudiante"],
                "nombre": f"{row['nombres']} {row['apellidos']}",
                "apellido": row["apellidos"],
                "encodings": encodings
            })


        # Retorna la lista de estudiantes válidos
        return estudiantes


    finally:
        # Cierra el cursor y la conexión al finalizar
        cursor.close()
        cerrar_conexion(conexion)



# ----------------------------------------------------
# Buscar hasta N estudiantes reconocidos en el frame
# Retorna lista de tuples (id_estudiante, nombre)
# ----------------------------------------------------
def buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=2, tolerance=0.45):
    # Si no hay estudiantes cargados, no se puede hacer comparación
    if not estudiantes_conocidos:
        return []


    # Reduce el tamaño del frame para mejorar el rendimiento
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convierte de BGR a RGB para usar face_recognition
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)


    # Detecta ubicaciones de rostros en el frame reducido usando el modelo HOG
    locations = face_recognition.face_locations(rgb_small, model="hog")

    # Si no se detectan rostros, retorna lista vacía
    if not locations:
        return []


    # Limita la cantidad de rostros a procesar según max_faces
    locations = locations[:max_faces]

    # Genera los encodings de los rostros detectados
    encodings_frame = face_recognition.face_encodings(rgb_small, locations)


    # Lista de estudiantes reconocidos
    encontrados = []

    for enc in encodings_frame:
        # Bandera para saber si ya se encontró coincidencia para este rostro
        match_found = False

        for est in estudiantes_conocidos:
            for est_enc in est["encodings"]:  # ahora iteramos sobre todas las variantes
                # Compara el rostro actual con cada encoding del estudiante
                if face_recognition.compare_faces([est_enc], enc, tolerance=tolerance)[0]:
                    encontrados.append((est["id"], est["nombre"]))
                    match_found = True
                    break

            # Si ya se encontró coincidencia, no sigue buscando en más estudiantes
            if match_found:
                break

        # Si ya se alcanzó el número máximo de rostros a reconocer, detiene el proceso
        if len(encontrados) >= max_faces:
            break


    # Retorna la lista de estudiantes encontrados
    return encontrados


# ----------------------------------------------------
# Compatibilidad: función simple que devuelve primer match (id, nombre) o None
# ----------------------------------------------------
def buscar_estudiante_por_rostro(frame, estudiantes_conocidos, tolerance=0.45):
    # Reutiliza la función general, pero limita la búsqueda a un solo rostro
    encontrados = buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=1, tolerance=tolerance)

    # Retorna el primer encontrado o None si no hay coincidencias
    return encontrados[0] if encontrados else None


# ----------------------------------------------------
# Asignar equipo a estudiante
# (igual que tu código original)
# ----------------------------------------------------
def asignar_equipo(id_estudiante):
    # Crea conexión con la base de datos
    conexion = crear_conexion()

    # Si no hay conexión, retorna None
    if not conexion:
        return None


    # Cursor tipo diccionario para acceder a los campos por nombre
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Obtiene el usuario que ha iniciado sesión actualmente
        usuario = Sesion.obtener_usuario()

        # Extrae la cédula del docente si existe en la sesión
        cedula_docente = usuario["cedula"] if usuario and "cedula" in usuario else None


        # Obtener la matrícula más reciente del estudiante
        cursor.execute(
            "SELECT MAX(id_matricula) AS max_matricula FROM matriculas WHERE id_estudiante = %s AND estado = 'Estudiante'",
            (id_estudiante,)
        )
        row = cursor.fetchone()
        matricula = row["max_matricula"] if row else None

        # Si no existe matrícula activa, retorna None
        if not matricula:
            return None


        # Verificar si ya tiene equipo asignado
        cursor.execute(
            "SELECT id_equipo FROM historial WHERE id_matricula = %s AND hora_fin IS NULL",
            (matricula,)
        )
        row = cursor.fetchone()

        # Si ya tiene un equipo asignado actualmente, retorna ese equipo
        if row:
            return row["id_equipo"]


        # Obtener grado del estudiante
        cursor.execute("SELECT grado FROM matriculas WHERE id_matricula = %s", (matricula,))
        row = cursor.fetchone()

        # Si no se encuentra el grado, retorna None
        if not row:
            return None
        grado = row["grado"]


        # Obtener todos los estudiantes del mismo grado
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

        # Si no hay estudiantes en ese grado, retorna None
        if not filas:
            return None


        # Ordenar por apellido
        estudiantes_ordenados = sorted(filas, key=lambda x: (x["apellidos"].lower() if x["apellidos"] else ""))
        ids_ordenados = [f["id_estudiante"] for f in estudiantes_ordenados]


        try:
            # Busca la posición del estudiante dentro de la lista ordenada
            pos = ids_ordenados.index(id_estudiante)
        except ValueError:
            # Si no aparece en la lista, retorna None
            return None


        # Genera el código del equipo según la posición del estudiante
        codigo_equipo = f"E-{str(pos+1).zfill(2)}"


        # Verificar estado del equipo
        cursor.execute("SELECT estado FROM equipos WHERE id_equipo = %s", (codigo_equipo,))
        equipo_row = cursor.fetchone()

        # Función para obtener siguiente equipo disponible (no dañado, no ocupado)
        def obtener_siguiente_disponible(posicion):
            cursor.execute(
                "SELECT id_equipo FROM equipos WHERE id_equipo != %s ORDER BY id_equipo ASC",
                (codigo_equipo,)
            )
            for eq in cursor.fetchall():
                eq_id = eq["id_equipo"]
                # Verificar que no esté dañado ni ocupado por otro
                cursor.execute(
                    "SELECT estado FROM equipos WHERE id_equipo = %s",
                    (eq_id,)
                )
                est = cursor.fetchone()
                if est and est["estado"] == "disponible":
                    # Verificar que no esté en uso
                    cursor.execute(
                        "SELECT id_matricula FROM historial WHERE id_equipo = %s AND hora_fin IS NULL",
                        (eq_id,)
                    )
                    if not cursor.fetchone():
                        return eq_id
            return None

        if not equipo_row:
            # Tomar primer equipo disponible
            cursor.execute("SELECT id_equipo FROM equipos WHERE estado = 'disponible' ORDER BY id_equipo ASC LIMIT 1")
            r = cursor.fetchone()
            if not r:
                return None
            codigo_equipo = r["id_equipo"]
        else:
            estado = equipo_row["estado"]
            if estado in ("ocupado", "dañado", "otro"):
                # Busca siguiente equipo disponible (no dañado, no ocupado)
                nuevo = obtener_siguiente_disponible(pos)
                if nuevo:
                    codigo_equipo = nuevo
                else:
                    # Si está ocupado por otro estudiante, buscar disponible
                    cursor.execute(
                        "SELECT id_equipo FROM equipos WHERE estado = 'disponible' ORDER BY id_equipo ASC LIMIT 1"
                    )
                    r = cursor.fetchone()
                    if not r:
                        return None
                    codigo_equipo = r["id_equipo"]


        # Marcar equipo como ocupado si no lo está
        cursor.execute("SELECT estado FROM equipos WHERE id_equipo = %s", (codigo_equipo,))
        estado_row = cursor.fetchone()
        if estado_row and estado_row["estado"] != "ocupado":
            cursor.execute("UPDATE equipos SET estado = 'ocupado' WHERE id_equipo = %s", (codigo_equipo,))


        # Insertar historial
        cursor.execute(
            """
            INSERT INTO historial (id_matricula, cedula, id_equipo, fecha, hora_inicio, hora_fin)
            VALUES (%s, %s, %s, CURDATE(), CURTIME(), NULL)
            """,
            (matricula, cedula_docente, codigo_equipo)
        )


        # Guarda definitivamente los cambios realizados en la base de datos
        conexion.commit()

        # Retorna el código del equipo asignado
        return codigo_equipo


    finally:
        # Cierra el cursor y la conexión al finalizar
        cursor.close()
        cerrar_conexion(conexion)



# ----------------------------------------------------
# Contar equipos con estado 'ocupado'
# ----------------------------------------------------
def contar_equipos_ocupados():
    # Crea conexión con la base de datos
    conexion = crear_conexion()

    # Si no hay conexión, retorna 0
    if not conexion:
        return 0


    # Cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Cuenta cuántos equipos están marcados como ocupados
        cursor.execute("SELECT COUNT(*) AS total FROM equipos WHERE estado = 'ocupado'")
        row = cursor.fetchone()

        # Retorna la cantidad total o 0 si no hay resultado
        return row["total"] if row else 0
    finally:
        # Cierra el cursor y la conexión
        cursor.close()
        cerrar_conexion(conexion)


# ----------------------------------------------------
# Obtener estudiantes que ya ingresaron hoy (para mostrar en lista)
# ----------------------------------------------------
def get_estudiantes_ingresados_hoy(grado=None):
    """Retorna lista de ids de estudiantes que ya ingresaron hoy"""
    conexion = crear_conexion()
    if not conexion:
        return []

    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        sql = """
            SELECT DISTINCT h.id_matricula, e.id_estudiante, e.nombres, e.apellidos
            FROM historial h
            INNER JOIN matriculas m ON h.id_matricula = m.id_matricula
            INNER JOIN estudiantes e ON m.id_estudiante = e.id_estudiante
            WHERE DATE(h.hora_inicio) = CURDATE()
        """
        if grado:
            sql += " AND m.grado = %s"
            cursor.execute(sql, (grado,))
        else:
            cursor.execute(sql)

        rows = cursor.fetchall()
        # Retorna lista de dicts con info del estudiante
        return [{"id": r["id_estudiante"], "nombre": r["nombres"], "apellido": r["apellidos"]} for r in rows]
    finally:
        cursor.close()
        cerrar_conexion(conexion)
