import pymysql
from modules.conexion import crear_conexion, cerrar_conexion

# ==========================================================
#   FUNCIÓN: registrar_docente
#   Descripción:
#       - Inserta un nuevo docente en la tabla "docentes"
#       - Guarda cédula, nombres, apellidos, celular, si es admin y la foto
# ==========================================================

def registrar_docente(cedula, nombre, apellido, celular, es_admin, foto_bytes):
    """
    Inserta un nuevo registro en la tabla 'docentes'.

    Parámetros:
    - cedula (str): número de identificación del docente.
    - nombre (str): nombres del docente.
    - apellido (str): apellidos del docente.
    - celular (str): número de contacto del docente.
    - es_admin (int): 1 si es administrador, 0 si es docente regular.
    - foto_bytes (bytes): imagen del rostro del docente en formato binario (BLOB).

    Retorna:
    - True si el registro fue exitoso.
    - False si ocurre un error durante la inserción.
    """

    conexion, cursor = None, None
    try:
        # Crear conexión a la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # Sentencia SQL parametrizada para evitar inyección SQL
        sql = """
            INSERT INTO docentes (cedula, nombres, apellidos, celular, es_admin, foto_rostro)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Ejecutar la consulta pasando los valores en una tupla
        cursor.execute(sql, (cedula, nombre, apellido, celular, es_admin, foto_bytes))

        # Guardar los cambios en la base de datos
        conexion.commit()

        # Cerrar cursor y conexión
        cursor.close()
        cerrar_conexion(conexion)

        # Mensaje de confirmación
        print(f"✅ Docente {nombre} {apellido} registrado con cédula {cedula}")
        return True

    except pymysql.MySQLError as e:
        # Captura errores específicos de pymysql
        print("❌ Error al registrar docente:", e)
        if conexion:
            conexion.rollback()
        return False

    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)
