# Importa las funciones para abrir y cerrar la conexión con la base de datos
from modules.conexion import crear_conexion, cerrar_conexion

# Importa la excepción específica para errores de MySQL
from pymysql import MySQLError


def existe_docente_admin():
    # Intenta crear una conexión con la base de datos
    conexion = crear_conexion()

    # Si no se pudo establecer la conexión, retorna False
    if not conexion:
        return False


    try:
        # Crea un cursor para ejecutar consultas SQL
        cursor = conexion.cursor()


        # Ejecuta una consulta para contar cuántos docentes tienen rol de administrador
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM docentes 
            WHERE es_admin = 1
        """)


        # Obtiene la primera fila del resultado de la consulta
        row = cursor.fetchone()


        # Si no se obtuvo ninguna fila, retorna False
        if not row:
            return False


        # PyMySQL devuelve:  {"total": X}
        # Retorna True si existe al menos un docente administrador registrado
        return row["total"] > 0


    except MySQLError as e:
        # Si ocurre un error de MySQL, lo muestra en consola y retorna False
        print(f"⚠ Error verificando admin: {e}")
        return False


    finally:
        try:
            # Intenta cerrar el cursor para liberar recursos
            cursor.close()
        except:
            # Ignora cualquier error si el cursor no existe o ya fue cerrado
            pass

        # Cierra la conexión con la base de datos
        cerrar_conexion(conexion)
