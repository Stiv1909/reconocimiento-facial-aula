from modules.conexion import crear_conexion, cerrar_conexion


# ==========================================================
#   FUNCIÓN: registrar_estudiante
#   Descripción:
#       - Inserta un nuevo estudiante en la tabla "estudiantes".
#       - Reordena los IDs dentro del grado en orden alfabético
#         (Apellidos + Nombres).
#       - Los IDs siguen el formato: 6-1 → "61XX", 10-2 → "102XX".
#   Parámetros:
#       - nombre (str)
#       - apellido (str)
#       - grado (str) → ejemplo "6-1"
#       - foto_bytes (binario) → foto capturada
#   Retorna:
#       - True  -> si se registró correctamente
#       - False -> si ocurrió un error
# ==========================================================
def registrar_estudiante(nombre, apellido, grado, foto_bytes):
    conexion = None
    cursor = None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # --- 1. Obtener estudiantes actuales del grado ---
        sql_select = "SELECT id_estudiante, apellidos, nombres FROM estudiantes WHERE grado = %s"
        cursor.execute(sql_select, (grado,))
        estudiantes = cursor.fetchall()

        # --- 2. Agregar el nuevo estudiante en memoria ---
        estudiantes.append((None, apellido, nombre))

        # --- 3. Ordenar alfabéticamente ---
        estudiantes.sort(key=lambda x: (x[1].lower(), x[2].lower()))

        # --- 4. Prefijo del grado (ej: "6-1" → "61") ---
        prefijo = grado.replace("-", "")

        # --- 5. Generar IDs nuevos ---
        nuevos_estudiantes = []
        for i, (id_est, ape, nom) in enumerate(estudiantes, start=1):
            nuevo_id = f"{prefijo}{i:02d}"
            nuevos_estudiantes.append((id_est, nuevo_id, ape, nom))

        # --- 6A. IDs temporales para evitar conflictos ---
        for id_est, _, ape, nom in nuevos_estudiantes:
            if id_est is not None:
                tmp_id = f"T{id_est}"  # Ej: T6101
                cursor.execute(
                    "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
                    (tmp_id, id_est)
                )

        # --- 6B. Reasignar IDs definitivos ---
        for id_est, nuevo_id, ape, nom in nuevos_estudiantes:
            if id_est is not None:
                cursor.execute(
                    "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
                    (nuevo_id, f"T{id_est}")
                )

        # --- 6C. Insertar el nuevo estudiante ---
        for id_est, nuevo_id, ape, nom in nuevos_estudiantes:
            if id_est is None:
                sql_insert = """INSERT INTO estudiantes 
                                (id_estudiante, nombres, apellidos, grado, foto_rostro)
                                VALUES (%s, %s, %s, %s, %s)"""
                cursor.execute(sql_insert, (nuevo_id, nom, ape, grado, foto_bytes))

        conexion.commit()
        return True

    except Exception as e:
        print("❌ Error al registrar estudiante:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)


# ==========================================================
#   FUNCIÓN: buscar_estudiantes
#   Descripción:
#       - Consulta estudiantes aplicando filtros dinámicos:
#         por nombre, grado y/o estado.
#   Parámetros:
#       - nombre (str)
#       - grado (str)
#       - estado (str)
#   Retorna:
#       - Lista de diccionarios con los estudiantes encontrados.
# ==========================================================
def buscar_estudiantes(nombre="", grado="", estado=""):
    conexion = crear_conexion()
    cursor = conexion.cursor(dictionary=True)

    sql = """SELECT id_estudiante, nombres, apellidos, grado, estado
             FROM estudiantes WHERE 1=1"""
    params = []

    if nombre:
        sql += " AND (nombres LIKE %s OR apellidos LIKE %s)"
        params.extend([f"%{nombre}%", f"%{nombre}%"])
    if grado:
        sql += " AND grado = %s"
        params.append(grado)
    if estado:
        sql += " AND estado = %s"
        params.append(estado)

    cursor.execute(sql, tuple(params))
    resultados = cursor.fetchall()

    cursor.close()
    cerrar_conexion(conexion)
    return resultados


# ==========================================================
#   FUNCIÓN: actualizar_datos
#   Descripción:
#       - Modifica los datos de un estudiante (nombre, apellido,
#         grado y estado).
#       - Reordena IDs en caso de cambio de grado.
#   Parámetros:
#       - id_estudiante (str)
#       - nombre (str)
#       - apellido (str)
#       - grado (str)
#       - estado (str)
#   Retorna:
#       - True  -> si se actualizó correctamente
#       - False -> si ocurrió un error
# ==========================================================
def actualizar_datos(id_estudiante, nombre, apellido, grado, estado):
    conexion = None
    cursor = None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # --- 1. Obtener grado original ---
        cursor.execute("SELECT grado FROM estudiantes WHERE id_estudiante = %s", (id_estudiante,))
        row = cursor.fetchone()
        grado_origen = row[0] if row else None

        # --- 2. ID temporal para evitar duplicados ---
        tmp_id = f"X{id_estudiante}"
        cursor.execute(
            "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
            (tmp_id, id_estudiante)
        )

        # --- 3. Actualizar datos principales ---
        sql_update = """UPDATE estudiantes 
                        SET id_estudiante = %s, nombres = %s, apellidos = %s, grado = %s, estado = %s
                        WHERE id_estudiante = %s"""
        cursor.execute(sql_update, (tmp_id, nombre, apellido, grado, estado, tmp_id))

        # --- 4. Reordenar IDs en el grado de origen ---
        if grado_origen and grado_origen != grado:
            reordenar_ids(cursor, grado_origen)

        # --- 5. Reordenar IDs en el grado destino ---
        reordenar_ids(cursor, grado)

        conexion.commit()
        print(f"✅ Estudiante {id_estudiante} actualizado y reordenado en {grado}.")
        return True

    except Exception as e:
        print("❌ Error al actualizar estudiante:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)


# ==========================================================
#   FUNCIÓN: actualizar_rostro
#   Descripción:
#       - Cambia la foto de rostro de un estudiante.
#   Parámetros:
#       - id_estudiante (str)
#       - foto_bytes (binario)
#   Retorna:
#       - True  -> si se actualizó correctamente
#       - False -> si no se envió foto o hubo error
# ==========================================================
def actualizar_rostro(id_estudiante, foto_bytes=None):
    if foto_bytes is None:
        print("⚠ No se recibió foto para actualizar.")
        return False

    conexion = crear_conexion()
    cursor = conexion.cursor()

    sql = "UPDATE estudiantes SET foto_rostro = %s WHERE id_estudiante = %s"
    cursor.execute(sql, (foto_bytes, id_estudiante))
    conexion.commit()

    cursor.close()
    cerrar_conexion(conexion)
    return True


# ==========================================================
#   FUNCIÓN AUXILIAR: reordenar_ids
#   Descripción:
#       - Reorganiza los IDs de un grado según apellidos y nombres.
#       - Evita conflictos usando IDs temporales.
#   Parámetros:
#       - cursor: cursor activo de MySQL
#       - grado (str)
# ==========================================================
def reordenar_ids(cursor, grado):
    # 1. Obtener estudiantes del grado
    cursor.execute("SELECT id_estudiante, apellidos, nombres FROM estudiantes WHERE grado = %s", (grado,))
    estudiantes = cursor.fetchall()

    if not estudiantes:
        return

    # 2. Ordenar por apellidos + nombres
    estudiantes.sort(key=lambda x: (x[1].lower(), x[2].lower()))

    # 3. Prefijo según grado
    prefijo = grado.replace("-", "")

    # 4. Generar nuevos IDs
    nuevos = []
    for i, (id_est, ape, nom) in enumerate(estudiantes, start=1):
        nuevo_id = f"{prefijo}{i:02d}"
        nuevos.append((id_est, nuevo_id))

    # 5. IDs temporales únicos
    for id_est, _ in nuevos:
        tmp_id = f"TMP_{grado}_{id_est}"
        cursor.execute(
            "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
            (tmp_id, id_est)
        )

    # 6. Reasignar IDs definitivos
    for id_est, nuevo_id in nuevos:
        cursor.execute(
            "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
            (nuevo_id, f"TMP_{grado}_{id_est}")
        )
