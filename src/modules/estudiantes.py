from modules.conexion import crear_conexion, cerrar_conexion

# =============================
# Registro de estudiante
# =============================
def registrar_estudiante(nombre, apellido, grado, foto_bytes):
    conexion = None
    cursor = None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # --- 1. Obtener estudiantes actuales ---
        sql_select = "SELECT id_estudiante, apellidos, nombres FROM estudiantes WHERE grado = %s"
        cursor.execute(sql_select, (grado,))
        estudiantes = cursor.fetchall()

        # --- 2. Agregar el nuevo estudiante en memoria ---
        estudiantes.append((None, apellido, nombre))

        # --- 3. Ordenar alfabéticamente ---
        estudiantes.sort(key=lambda x: (x[1].lower(), x[2].lower()))

        # --- 4. Generar prefijo ---
        prefijo = grado.replace("-", "")

        # --- 5. Asignar IDs nuevos ---
        nuevos_estudiantes = []
        for i, (id_est, ape, nom) in enumerate(estudiantes, start=1):
            nuevo_id = f"{prefijo}{i:02d}"
            nuevos_estudiantes.append((id_est, nuevo_id, ape, nom))

        # --- 6A. Asignar IDs temporales para evitar conflictos ---
        for id_est, _, ape, nom in nuevos_estudiantes:
            if id_est is not None:
                tmp_id = f"T{id_est}"  # ✅ ID temporal corto
                cursor.execute(
                    "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
                    (tmp_id, id_est)
                )

        # --- 6B. Asignar los IDs definitivos ---
        for id_est, nuevo_id, ape, nom in nuevos_estudiantes:
            if id_est is not None:
                cursor.execute(
                    "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
                    (nuevo_id, f"T{id_est}")  # ✅ corto
                )

        # --- 6C. Insertar el nuevo estudiante ---
        for id_est, nuevo_id, ape, nom in nuevos_estudiantes:
            if id_est is None:
                sql_insert = """INSERT INTO estudiantes (id_estudiante, nombres, apellidos, grado, foto_rostro)
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


# =============================
# Buscar estudiantes
# =============================
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


# =============================
# Actualizar datos (con reordenamiento)
# =============================
def actualizar_datos(id_estudiante, nombre, apellido, grado, estado):
    conexion = None
    cursor = None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # --- 1. Obtener grado actual antes del cambio ---
        cursor.execute("SELECT grado FROM estudiantes WHERE id_estudiante = %s", (id_estudiante,))
        row = cursor.fetchone()
        grado_origen = row[0] if row else None

        # --- 2. Asignar ID temporal para evitar duplicados ---
        tmp_id = f"X{id_estudiante}"
        cursor.execute(
            "UPDATE estudiantes SET id_estudiante = %s WHERE id_estudiante = %s",
            (tmp_id, id_estudiante)
        )

        # --- 3. Actualizar los datos (incluido el grado) ---
        sql_update = """UPDATE estudiantes 
                        SET id_estudiante = %s, nombres = %s, apellidos = %s, grado = %s, estado = %s
                        WHERE id_estudiante = %s"""
        cursor.execute(sql_update, (tmp_id, nombre, apellido, grado, estado, tmp_id))

        # --- 4. Reordenar IDs en el curso de origen ---
        if grado_origen and grado_origen != grado:
            reordenar_ids(cursor, grado_origen)

        # --- 5. Reordenar IDs en el curso destino ---
        reordenar_ids(cursor, grado)

        conexion.commit()
        print(f"✅ Estudiante {id_estudiante} actualizado y IDs reordenados en {grado}.")
        return True

    except Exception as e:
        print("❌ Error al actualizar estudiante:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)

# =============================
# Actualizar rostro
# =============================
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


# =============================
# Función auxiliar: Reordenar IDs por grado
# =============================
def reordenar_ids(cursor, grado):
    # 1. Obtener estudiantes del grado
    cursor.execute("SELECT id_estudiante, apellidos, nombres FROM estudiantes WHERE grado = %s", (grado,))
    estudiantes = cursor.fetchall()

    if not estudiantes:
        return

    # 2. Ordenar por apellido + nombre
    estudiantes.sort(key=lambda x: (x[1].lower(), x[2].lower()))

    # 3. Prefijo del grado
    prefijo = grado.replace("-", "")

    # 4. Generar nuevos IDs
    nuevos = []
    for i, (id_est, ape, nom) in enumerate(estudiantes, start=1):
        nuevo_id = f"{prefijo}{i:02d}"
        nuevos.append((id_est, nuevo_id))

    # 5. Asignar IDs temporales únicos
    for id_est, _ in nuevos:
        tmp_id = f"TMP_{grado}_{id_est}"   # ✅ ahora incluye el grado
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

