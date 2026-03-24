# Importa la librería PyMySQL para conectarse a una base de datos MySQL
import pymysql

# Importa la clase de excepción específica para capturar errores de MySQL
from pymysql import MySQLError


# ==========================================================
#   FUNCIÓN: crear_conexion
# ==========================================================
def crear_conexion():
    try:
        # Intenta establecer una conexión con la base de datos MySQL local
        conexion = pymysql.connect(
            host="localhost",  # Servidor donde está alojada la base de datos
            user="root",  # Usuario de acceso a MySQL
            password="1234",  # Contraseña del usuario de MySQL
            database="control_acceso",  # Nombre de la base de datos a utilizar
            charset=None,  # Configuración de caracteres, se deja tal como está en el código original
            cursorclass=pymysql.cursors.DictCursor  # Hace que los resultados se devuelvan como diccionarios
        )

        # Muestra en consola un mensaje indicando que la conexión fue exitosa
        print("✅ Conexión exitosa a la base de datos")

        # Retorna el objeto conexión para ser usado en otras operaciones
        return conexion

    except MySQLError as e:
        # Si ocurre un error al conectar, lo muestra en consola
        print(f"❌ Error al conectar: {e}")

        # Retorna None para indicar que no se pudo establecer la conexión
        return None



# ==========================================================
#   FUNCIÓN: cerrar_conexion
# ==========================================================
def cerrar_conexion(conexion):
    # Verifica que el objeto conexión exista antes de intentar cerrarlo
    if conexion:
        try:
            # Cierra la conexión activa con la base de datos
            conexion.close()

            # Muestra en consola que la conexión fue cerrada correctamente
            print("🔒 Conexión cerrada")
        except:
            # Si ocurre algún error al cerrar, simplemente lo ignora
            pass
