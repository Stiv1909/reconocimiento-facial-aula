from modules.conexion import crear_conexion, cerrar_conexion


# ==========================================================
#   FUNCIÓN: agregar_equipo
#   Descripción:
#       - Inserta un nuevo equipo en la tabla "equipos".
#       - Genera automáticamente un ID con formato E-01, E-02, ...
#   Parámetros:
#       - estado (str): estado inicial del equipo (por defecto "Disponible").
#   Retorna:
#       - True  -> si el registro fue exitoso
#       - False -> si ocurrió un error
# ==========================================================
def agregar_equipo(estado="Disponible"):
    conexion = None
    cursor = None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # Buscar último ID registrado
        cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            # Ejemplo último: "E-07" → genera "E-08"
            ultimo_codigo = row[0]
            num = int(ultimo_codigo.split("-")[1])
            nuevo_codigo = f"E-{num+1:02d}"
        else:
            # Si no hay registros, empieza en E-01
            nuevo_codigo = "E-01"

        # Insertar en la tabla
        sql = "INSERT INTO equipos (id_equipo, estado) VALUES (%s, %s)"
        cursor.execute(sql, (nuevo_codigo, estado))
        conexion.commit()

        print(f"✅ Equipo agregado con código {nuevo_codigo}")
        return True

    except Exception as e:
        print("❌ Error al agregar equipo:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)


# ==========================================================
#   FUNCIÓN: obtener_equipos
#   Descripción:
#       - Devuelve todos los equipos registrados en la tabla.
#       - Ordenados por ID de forma ascendente.
#   Retorna:
#       - Lista de tuplas: [(id_equipo, estado), ...]
# ==========================================================
def obtener_equipos():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT id_equipo, estado FROM equipos ORDER BY id_equipo ASC")
    resultados = cursor.fetchall()

    cursor.close()
    cerrar_conexion(conexion)

    # Convertir todo a string por seguridad
    return [(str(codigo), str(estado)) for codigo, estado in resultados]


# ==========================================================
#   FUNCIÓN: actualizar_estado
#   Descripción:
#       - Cambia el estado de un equipo específico.
#   Parámetros:
#       - codigo (str): ID del equipo (ejemplo "E-03")
#       - nuevo_estado (str): nuevo estado ("disponible", "ocupado", "dañado")
#   Retorna:
#       - True  -> si se actualizó correctamente
#       - False -> si ocurrió un error
# ==========================================================
def actualizar_estado(codigo, nuevo_estado):
    conexion = None
    cursor = None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        sql = "UPDATE equipos SET estado = %s WHERE id_equipo = %s"
        cursor.execute(sql, (nuevo_estado, codigo))
        conexion.commit()

        print(f"✅ Estado actualizado para {codigo} → {nuevo_estado}")
        return True

    except Exception as e:
        print("❌ Error al actualizar estado:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)


# ==========================================================
#   FUNCIÓN: generar_proximo_codigo
#   Descripción:
#       - Calcula cuál sería el próximo código secuencial.
#       - Ejemplo: último "E-07" → devuelve "E-08".
#   Retorna:
#       - String con el próximo ID de equipo.
# ==========================================================
def generar_proximo_codigo():
    conexion = crear_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
    row = cursor.fetchone()

    if row:
        ultimo_codigo = row[0]  # Ejemplo: "E-07"
        num = int(ultimo_codigo.split("-")[1])
        nuevo_codigo = f"E-{num+1:02d}"
    else:
        nuevo_codigo = "E-01"

    cursor.close()
    cerrar_conexion(conexion)
    return nuevo_codigo
