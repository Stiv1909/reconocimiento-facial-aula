# Importa PyMySQL para manejar cursores y excepciones MySQL
import pymysql

# Importa funciones para crear y cerrar la conexión a la base de datos
from modules.conexion import crear_conexion, cerrar_conexion


# ==========================================================
#   FUNCIÓN: agregar_equipo
# ==========================================================
def agregar_equipo(estado="disponible", marca="", modelo="", procesador="", 
                 ram="", disco="", serial="", anio= None, observaciones=""):
    """
    Agrega un nuevo equipo con características técnicas.
    """
    conexion, cursor = None, None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # Buscar último ID registrado
        cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
        row = cursor.fetchone()

        if row:
            ultimo_codigo = row['id_equipo']
            num = int(ultimo_codigo.split("-")[1])
            nuevo_codigo = f"E-{num+1:02d}"
        else:
            nuevo_codigo = "E-01"

        # Insertar en la tabla con todas las características
        sql = """INSERT INTO equipos 
            (id_equipo, estado, marca, modelo, procesador, ram, disco, serial, anio_adquisicion, observaciones) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        cursor.execute(sql, (nuevo_codigo, estado, marca, modelo, procesador, 
                          ram, disco, serial, anio, observaciones))
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

    cursor.execute("""SELECT id_equipo, estado, marca, modelo, procesador, ram, disco, serial 
                     FROM equipos ORDER BY id_equipo ASC""")
    resultados = cursor.fetchall()

    cursor.close()
    cerrar_conexion(conexion)

    return [(r['id_equipo'], r['estado'], r.get('marca',''), r.get('modelo',''),
             r.get('procesador',''), r.get('ram',''), r.get('disco',''), r.get('serial','')) for r in resultados]


# ==========================================================
#   FUNCIÓN: obtener_todos_equipos
# ==========================================================
def obtener_todos_equipos():
    """Obtiene todos los equipos con todas sus características."""
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT * FROM equipos ORDER BY id_equipo ASC")
    resultados = cursor.fetchall()

    cursor.close()
    cerrar_conexion(conexion)

    return resultados


# ==========================================================
#   FUNCIÓN: actualizar_estado
# ==========================================================
def actualizar_estado(codigo, nuevo_estado, descripcion=""):
    conexion, cursor = None, None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        # Obtener estado anterior
        cursor.execute("SELECT estado FROM equipos WHERE id_equipo = %s", (codigo,))
        row = cursor.fetchone()
        estado_anterior = row['estado'] if row else ""

        # Actualizar estado
        sql = "UPDATE equipos SET estado = %s WHERE id_equipo = %s"
        cursor.execute(sql, (nuevo_estado, codigo))

        # Registrar en historial solo si hay cambio
        if estado_anterior != nuevo_estado:
            from datetime import datetime
            ahora = datetime.now()
            cedula = ""
            try:
                from modules.sesion import Sesion
                cedula = Sesion.obtener_cedula()
            except:
                pass
            cursor.execute("""INSERT INTO historial_equipos 
                (id_equipo, tipo_accion, estado_anterior, estado_nuevo, descripcion, fecha, hora, cedula)
                VALUES (%s, 'cambio_estado', %s, %s, %s, %s, %s, %s)""",
                (codigo, estado_anterior, nuevo_estado, descripcion, ahora.date(), ahora.time(), cedula))
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
#   FUNCIÓN: actualizar_equipo
# ==========================================================
def actualizar_equipo(codigo, marca, modelo, procesador, ram, disco, serial, anio, observaciones):
    """Actualiza todas las características de un equipo."""
    conexion, cursor = None, None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        sql = """UPDATE equipos SET 
            marca=%s, modelo=%s, procesador=%s, ram=%s, disco=%s, 
            serial=%s, anio_adquisicion=%s, observaciones=%s 
            WHERE id_equipo=%s"""
        
        cursor.execute(sql, (marca, modelo, procesador, ram, disco, 
                          serie, anio, observaciones, codigo))
        conexion.commit()

        print(f"✅ Equipo {codigo} actualizado")
        return True

    except pymysql.MySQLError as e:
        print("❌ Error al actualizar equipo:", e)
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
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT id_equipo FROM equipos ORDER BY id_equipo DESC LIMIT 1")
    row = cursor.fetchone()

    if row:
        ultimo_codigo = row['id_equipo']
        num = int(ultimo_codigo.split("-")[1])
        nuevo_codigo = f"E-{num+1:02d}"
    else:
        nuevo_codigo = "E-01"

    cursor.close()
    cerrar_conexion(conexion)

    return nuevo_codigo


# ==========================================================
#   FUNCIÓN: obtener_marcas
# ==========================================================
def obtener_marcas():
    """Obtiene lista dinámica de marcas."""
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT DISTINCT marca FROM equipos WHERE marca IS NOT NULL AND marca != '' ORDER BY marca")
    resultados = cursor.fetchall()
    
    cursor.close()
    cerrar_conexion(conexion)
    
    return [r['marca'] for r in resultados] if resultados else ["Dell", "HP", "Lenovo", "Acer", "Asus", "Toshiba"]


# ==========================================================
#   FUNCIÓN: obtener_procesadores
# ==========================================================
def obtener_procesadores():
    """Obtiene lista dinámica de procesadores."""
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT DISTINCT procesador FROM equipos WHERE procesador IS NOT NULL AND procesador != '' ORDER BY procesador")
    resultados = cursor.fetchall()
    
    cursor.close()
    cerrar_conexion(conexion)
    
    return [r['procesador'] for r in resultados] if resultados else ["Intel Core i3", "Intel Core i5", "Intel Core i7", "AMD Ryzen 3", "AMD Ryzen 5", "AMD Ryzen 7"]


# ==========================================================
#   FUNCIÓN: obtener_estados
# ==========================================================
def obtener_estados():
    """Obtiene lista dinámica de estados."""
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT DISTINCT estado_nuevo FROM historial_equipos WHERE estado_nuevo IS NOT NULL AND estado_nuevo != '' ORDER BY estado_nuevo")
    resultados = cursor.fetchall()
    
    cursor.close()
    cerrar_conexion(conexion)
    
    return [r['estado_nuevo'] for r in resultados] if resultados else ["disponible", "dañado", "otro"]


# ==========================================================
#   FUNCIÓN: obtener_rams
# ==========================================================
def obtener_rams():
    """Obtiene lista dinámica de opciones de RAM."""
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT DISTINCT ram FROM equipos WHERE ram IS NOT NULL AND ram != '' ORDER BY ram")
    resultados = cursor.fetchall()
    
    cursor.close()
    cerrar_conexion(conexion)
    
    return [r['ram'] for r in resultados] if resultados else ["4 GB", "8 GB", "16 GB", "32 GB"]


# ==========================================================
#   FUNCIÓN: obtener_discos
# ==========================================================
def obtener_discos():
    """Obtiene lista dinámica de opciones de disco."""
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT DISTINCT disco FROM equipos WHERE disco IS NOT NULL AND disco != '' ORDER BY disco")
    resultados = cursor.fetchall()
    
    cursor.close()
    cerrar_conexion(conexion)
    
    return [r['disco'] for r in resultados] if resultados else ["HDD 500 GB", "HDD 1 TB", "SSD 256 GB", "SSD 512 GB", "SSD 1 TB"]


# ==========================================================
#   FUNCIÓN: obtener_grados
# ==========================================================
def obtener_grados():
    """Obtiene lista dinámica de grados desde la tabla matrículas."""
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT DISTINCT grado FROM matriculas WHERE grado IS NOT NULL AND grado != '' ORDER BY grado")
    resultados = cursor.fetchall()
    
    cursor.close()
    cerrar_conexion(conexion)
    
    return [r['grado'] for r in resultados] if resultados else ["6-1", "6-2", "7-1", "7-2", "8-1", "8-2", "9-1", "9-2", "10-1", "10-2", "11-1", "11-2"]