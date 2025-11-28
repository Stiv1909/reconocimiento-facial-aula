import pymysql
from pymysql import MySQLError

# ==========================================================
#   FUNCIÓN: crear_conexion
# ==========================================================
def crear_conexion():
    try:
        conexion = pymysql.connect(
            host="localhost",
            user="root",
            password="1234",
            database="control_acceso",
            charset=None,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ Conexión exitosa a la base de datos")
        return conexion
    except MySQLError as e:
        print(f"❌ Error al conectar: {e}")
        return None


# ==========================================================
#   FUNCIÓN: cerrar_conexion
# ==========================================================
def cerrar_conexion(conexion):
    if conexion:
        try:
            conexion.close()
            print("🔒 Conexión cerrada")
        except:
            pass
