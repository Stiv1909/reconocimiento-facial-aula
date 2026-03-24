# Importa PyMySQL para manejar cursores y excepciones MySQL
import pymysql

# Importa funciones para crear y cerrar la conexión a la base de datos
from modules.conexion import crear_conexion, cerrar_conexion


# ==========================================================
#   FUNCIÓN: agregar_equipo
# ==========================================================
def agregar_equipo(estado="Disponible"):
    # Inicializa variables de conexión y cursor
    conexion, cursor = None, None
    try:
        # Crea conexión con la base de datos
        conexion = crear_conexion()

        # Crea cursor tipo diccionario
        cursor = conexion.cursor(pymysql.cursors.DictCursor)  # <--- DictCursor


        # Buscar último ID registrado
        cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
        row = cursor.fetchone()


        if row:
            # Obtiene el último código registrado
            ultimo_codigo = row['id_equipo']  # <--- usar nombre de columna

            # Extrae la parte numérica del código
            num = int(ultimo_codigo.split("-")[1])

            # Genera el siguiente código secuencial
            nuevo_codigo = f"E-{num+1:02d}"
        else:
            # Si no hay equipos aún, comienza con E-01
            nuevo_codigo = "E-01"


        # Insertar en la tabla
        sql = "INSERT INTO equipos (id_equipo, estado) VALUES (%s, %s)"
        cursor.execute(sql, (nuevo_codigo, estado))
        conexion.commit()


        # Mensaje de confirmación en consola
        print(f"✅ Equipo agregado con código {nuevo_codigo}")
        return True


    except pymysql.MySQLError as e:
        # Captura errores MySQL, revierte cambios y retorna False
        print("❌ Error al agregar equipo:", e)
        if conexion:
            conexion.rollback()
        return False


    finally:
        # Cierra cursor y conexión si existen
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)



# ==========================================================
#   FUNCIÓN: obtener_equipos
# ==========================================================
def obtener_equipos():
    # Crea conexión a la base de datos
    conexion = crear_conexion()

    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)


    # Consulta todos los equipos ordenados por código
    cursor.execute("SELECT id_equipo, estado FROM equipos ORDER BY id_equipo ASC")
    resultados = cursor.fetchall()


    # Cierra cursor y conexión
    cursor.close()
    cerrar_conexion(conexion)


    # Convierte los resultados a lista de tuplas (codigo, estado)
    return [(r['id_equipo'], r['estado']) for r in resultados]



# ==========================================================
#   FUNCIÓN: actualizar_estado
# ==========================================================
def actualizar_estado(codigo, nuevo_estado):
    # Inicializa variables de conexión y cursor
    conexion, cursor = None, None
    try:
        # Crea conexión con la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor()


        # Actualiza el estado del equipo correspondiente
        sql = "UPDATE equipos SET estado = %s WHERE id_equipo = %s"
        cursor.execute(sql, (nuevo_estado, codigo))
        conexion.commit()


        # Mensaje de confirmación en consola
        print(f"✅ Estado actualizado para {codigo} → {nuevo_estado}")
        return True


    except pymysql.MySQLError as e:
        # Captura error, revierte cambios y retorna False
        print("❌ Error al actualizar estado:", e)
        if conexion:
            conexion.rollback()
        return False


    finally:
        # Cierra cursor y conexión si existen
        if cursor: cursor.close()
        if conexion: cerrar_conexion(conexion)



# ==========================================================
#   FUNCIÓN: generar_proximo_codigo
# ==========================================================
def generar_proximo_codigo():
    # Crea conexión a la base de datos
    conexion = crear_conexion()

    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)  # <--- DictCursor


    # Consulta el último código registrado
    cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
    row = cursor.fetchone()


    if row:
        # Obtiene el último código desde la fila
        ultimo_codigo = row['id_equipo']  # <--- usar nombre de columna

        # Extrae la parte numérica y calcula el siguiente
        num = int(ultimo_codigo.split("-")[1])
        nuevo_codigo = f"E-{num+1:02d}"
    else:
        # Si no hay registros, inicia en E-01
        nuevo_codigo = "E-01"


    # Cierra cursor y conexión
    cursor.close()
    cerrar_conexion(conexion)

    # Retorna el siguiente código disponible
    return nuevo_codigo
