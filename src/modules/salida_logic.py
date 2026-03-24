# Importa NumPy para manipular bytes de imagen como arreglos
import numpy as np

# Importa OpenCV para decodificar y transformar imágenes
import cv2

# Importa la librería de reconocimiento facial
import face_recognition

# Importa datetime para registrar la fecha de asistencia
from datetime import datetime

# Importa funciones de conexión a base de datos
from modules.conexion import crear_conexion, cerrar_conexion

# Importa PyMySQL para cursores tipo diccionario
import pymysql


# ----------------------------------------------------
# Cargar estudiantes con equipos ocupados (última matrícula activa)
# ----------------------------------------------------
def cargar_estudiantes():
    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return []


    # Crea un cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Consulta estudiantes con matrícula activa y equipo actualmente ocupado
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


    # Lista donde se almacenarán los estudiantes listos para reconocimiento facial
    estudiantes = []
    try:
        for row in cursor.fetchall():
            # Obtiene la foto del rostro almacenada como blob
            foto_blob = row["foto_rostro"]
            if foto_blob is None:
                continue


            # Convierte los bytes de imagen en un arreglo NumPy
            np_arr = np.frombuffer(foto_blob, np.uint8)

            # Decodifica la imagen desde el blob
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if img is None:
                continue


            # Convierte la imagen a RGB para face_recognition
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Extrae los encodings faciales de la imagen
            encodings = face_recognition.face_encodings(rgb)
            if len(encodings) > 0:
                # Si se detectó al menos un rostro, guarda el primer encoding
                estudiantes.append({
                    "id": row["id_estudiante"],
                    "nombre": f"{row['nombres']} {row['apellidos']}",
                    "encoding": encodings[0]
                })
    finally:
        # Cierra cursor y conexión al finalizar
        cursor.close()
        cerrar_conexion(conexion)


    # Retorna la lista de estudiantes reconocibles
    return estudiantes



# ----------------------------------------------------
# Buscar estudiantes reconocidos en el frame
# ----------------------------------------------------
def buscar_estudiantes_en_frame(frame, estudiantes_conocidos, max_faces=2, tolerance=0.40):
    # Si no hay estudiantes conocidos cargados, no procesa nada
    if not estudiantes_conocidos:
        return []


    # Reduce el tamaño del frame para acelerar el reconocimiento facial
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convierte el frame reducido a RGB
    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)


    # Detecta ubicaciones de rostros en el frame
    locations = face_recognition.face_locations(rgb_small, model="hog")
    if not locations:
        return []


    # Limita la cantidad de rostros procesados al máximo permitido
    locations = locations[:max_faces]

    # Genera encodings de los rostros detectados
    encodings = face_recognition.face_encodings(rgb_small, locations)

    # Lista de encodings conocidos de estudiantes
    conocidos_enc = [e["encoding"] for e in estudiantes_conocidos]


    # Lista de estudiantes encontrados en el frame actual
    encontrados = []
    for enc in encodings:
        # Compara el encoding detectado con todos los conocidos
        matches = face_recognition.compare_faces(conocidos_enc, enc, tolerance=tolerance)
        if True in matches:
            # Toma el primer estudiante que coincida
            idx = matches.index(True)
            encontrados.append(estudiantes_conocidos[idx])
            if len(encontrados) >= max_faces:
                break


    # Retorna los estudiantes reconocidos en el frame
    return encontrados



# ----------------------------------------------------
# Registrar salida del estudiante (actualiza historial y libera equipo)
# ----------------------------------------------------
def registrar_salida(id_estudiante):
    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return None


    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # 1) Última matrícula activa
        cursor.execute(
            "SELECT MAX(id_matricula) AS max_matricula FROM matriculas WHERE id_estudiante = %s AND estado = 'Estudiante'",
            (id_estudiante,)
        )
        row = cursor.fetchone()
        matricula = row["max_matricula"] if row else None
        if not matricula:
            return None


        # 2) Buscar equipo activo
        cursor.execute(
            "SELECT id_equipo FROM historial WHERE id_matricula = %s AND hora_fin IS NULL",
            (matricula,)
        )
        row = cursor.fetchone()
        if not row:
            return None


        # Guarda el equipo actualmente asignado a ese estudiante
        id_equipo = row["id_equipo"]


        # 3) Registrar hora de salida
        cursor.execute(
            "UPDATE historial SET hora_fin = CURTIME() WHERE id_matricula = %s AND id_equipo = %s AND hora_fin IS NULL",
            (matricula, id_equipo)
        )


        # 4) Liberar equipo
        cursor.execute(
            "UPDATE equipos SET estado = 'disponible' WHERE id_equipo = %s",
            (id_equipo,)
        )


        # Confirma los cambios en base de datos
        conexion.commit()

        # Retorna el identificador del equipo liberado
        return id_equipo


    finally:
        # Cierra cursor y conexión
        cursor.close()
        cerrar_conexion(conexion)



# ----------------------------------------------------
# Contar equipos aún ocupados
# ----------------------------------------------------
def contar_equipos_ocupados():
    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return 0


    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Cuenta cuántos equipos están marcados como ocupados
        cursor.execute("SELECT COUNT(*) AS total FROM equipos WHERE estado = 'ocupado'")
        row = cursor.fetchone()
        return row["total"] if row else 0
    finally:
        # Cierra recursos
        cursor.close()
        cerrar_conexion(conexion)



# ----------------------------------------------------
# Obtener estudiantes pendientes por salida
# ----------------------------------------------------
def estudiantes_pendientes():
    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return []


    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Consulta los estudiantes que aún tienen equipos ocupados
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
        return [row["nombre"] for row in cursor.fetchall()]
    finally:
        # Cierra recursos
        cursor.close()
        cerrar_conexion(conexion)



# ----------------------------------------------------
# Registrar asistencias cuando todos hayan salido
# ----------------------------------------------------
def registrar_asistencia(grado=None):
    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return


    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # 1️⃣ Tomar grado si no se pasa
        if not grado:
            # Si no llega un grado, toma uno activo desde la tabla matrículas
            cursor.execute("SELECT grado FROM matriculas WHERE estado = 'Estudiante' LIMIT 1")
            row = cursor.fetchone()
            if not row:
                return
            grado = row["grado"]


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


        # 3️⃣ Obtener matrículas que usaron equipo hoy
        cursor.execute("""
            SELECT DISTINCT m.id_matricula
            FROM historial h
            INNER JOIN matriculas m ON m.id_matricula = h.id_matricula
            WHERE DATE(h.hora_inicio) = CURDATE()
        """)
        presentes = [row["id_matricula"] for row in cursor.fetchall()]


        # 4️⃣ Registrar asistencias
        fecha_hoy = datetime.now().date()
        for est in estudiantes:
            id_matricula = est["id_matricula"]

            # Marca presente si usó equipo hoy; en caso contrario, ausente
            estado = 'presente' if id_matricula in presentes else 'ausente'
            cursor.execute("""
                INSERT INTO asistencias (id_matricula, fecha, estado)
                VALUES (%s, %s, %s)
            """, (id_matricula, fecha_hoy, estado))


        # Guarda todos los registros de asistencia
        conexion.commit()
        print(f"Asistencia registrada correctamente para el grado {grado}")


    finally:
        # Cierra recursos de base de datos
        cursor.close()
        cerrar_conexion(conexion)
