import mysql.connector
from mysql.connector import Error


# ==========================================================
#   FUNCIÓN: crear_conexion
#   Descripción:
#       - Establece conexión con la base de datos MySQL
#       - Usa parámetros de host, usuario, contraseña y BD
#       - Devuelve el objeto de conexión si es exitosa
#       - Devuelve None si falla
# ==========================================================
def crear_conexion():
    try:
        conexion = mysql.connector.connect(
            host="localhost",   # Dirección del servidor MySQL (puede ser IP o localhost)
            user="root",        # Usuario de MySQL
            password="1234",    # Contraseña del usuario
            database="control_acceso"  # Nombre de la base de datos
        )
        if conexion.is_connected():
            print("✅ Conexión exitosa a la base de datos")
            return conexion
    except Error as e:
        print(f"❌ Error al conectar: {e}")
        return None


# ==========================================================
#   FUNCIÓN: cerrar_conexion
#   Descripción:
#       - Cierra la conexión a MySQL si está abierta
#       - Recibe el objeto de conexión como parámetro
# ==========================================================
def cerrar_conexion(conexion):
    if conexion and conexion.is_connected():
        conexion.close()
        print("🔒 Conexión cerrada")
