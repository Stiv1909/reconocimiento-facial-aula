import mysql.connector
from mysql.connector import Error

def crear_conexion():
    try:
        conexion = mysql.connector.connect(
            host="localhost",       # o la IP del servidor
            user="root",            # tu usuario de MySQL
            password="1234",            # tu contraseña (si no tienes, déjalo vacío)
            database="control_acceso"
        )
        if conexion.is_connected():
            print("✅ Conexión exitosa a la base de datos")
            return conexion
    except Error as e:
        print(f"❌ Error al conectar: {e}")
        return None

def cerrar_conexion(conexion):
    if conexion and conexion.is_connected():
        conexion.close()
        print("🔒 Conexión cerrada")
