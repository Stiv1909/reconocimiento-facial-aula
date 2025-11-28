from modules.conexion import crear_conexion, cerrar_conexion
from pymysql import MySQLError

def existe_docente_admin():
    conexion = crear_conexion()
    if not conexion:
        return False

    try:
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM docentes 
            WHERE es_admin = 1
        """)

        row = cursor.fetchone()

        if not row:
            return False

        # PyMySQL devuelve:  {"total": X}
        return row["total"] > 0

    except MySQLError as e:
        print(f"⚠ Error verificando admin: {e}")
        return False

    finally:
        try:
            cursor.close()
        except:
            pass
        cerrar_conexion(conexion)
