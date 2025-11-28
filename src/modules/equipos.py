import pymysql
from modules.conexion import crear_conexion, cerrar_conexion

# ==========================================================
#   FUNCIÓN: agregar_equipo
# ==========================================================
def agregar_equipo(estado="Disponible"):
    conexion, cursor = None, None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)  # <--- DictCursor

        # Buscar último ID registrado
        cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            ultimo_codigo = row['id_equipo']  # <--- usar nombre de columna
            num = int(ultimo_codigo.split("-")[1])
            nuevo_codigo = f"E-{num+1:02d}"
        else:
            nuevo_codigo = "E-01"

        # Insertar en la tabla
        sql = "INSERT INTO equipos (id_equipo, estado) VALUES (%s, %s)"
        cursor.execute(sql, (nuevo_codigo, estado))
        conexion.commit()

        print(f"✅ Equipo agregado con código {nuevo_codigo}")
        return True

    except pymysql.MySQLError as e:
        print("❌ Error al agregar equipo:", e)
        if conexion:
            conexion.rollback()
        return False

    finally:
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)


# ==========================================================
#   FUNCIÓN: obtener_equipos
# ==========================================================
def obtener_equipos():
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT id_equipo, estado FROM equipos ORDER BY id_equipo ASC")
    resultados = cursor.fetchall()

    cursor.close()
    cerrar_conexion(conexion)

    return [(r['id_equipo'], r['estado']) for r in resultados]


# ==========================================================
#   FUNCIÓN: actualizar_estado
# ==========================================================
def actualizar_estado(codigo, nuevo_estado):
    conexion, cursor = None, None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        sql = "UPDATE equipos SET estado = %s WHERE id_equipo = %s"
        cursor.execute(sql, (nuevo_estado, codigo))
        conexion.commit()

        print(f"✅ Estado actualizado para {codigo} → {nuevo_estado}")
        return True

    except pymysql.MySQLError as e:
        print("❌ Error al actualizar estado:", e)
        if conexion:
            conexion.rollback()
        return False

    finally:
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)


# ==========================================================
#   FUNCIÓN: generar_proximo_codigo
# ==========================================================
def generar_proximo_codigo():
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)  # <--- DictCursor

    cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
    row = cursor.fetchone()

    if row:
        ultimo_codigo = row['id_equipo']  # <--- usar nombre de columna
        num = int(ultimo_codigo.split("-")[1])
        nuevo_codigo = f"E-{num+1:02d}"
    else:
        nuevo_codigo = "E-01"

    cursor.close()
    cerrar_conexion(conexion)
    return nuevo_codigo
