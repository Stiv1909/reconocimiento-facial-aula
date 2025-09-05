from modules.conexion import crear_conexion, cerrar_conexion


# ==========================================================
#   FUNCIÓN: registrar_docente
#   Descripción:
#       - Inserta un nuevo docente en la tabla "docentes"
#       - Guarda nombres, apellidos y la foto en formato binario
#   Parámetros:
#       - nombre (str): nombres del docente
#       - apellido (str): apellidos del docente
#       - foto_bytes (bytes): foto capturada en formato binario
#   Retorna:
#       - True  -> si el registro fue exitoso
#       - False -> si ocurrió un error
# ==========================================================
def registrar_docente(nombre, apellido, foto_bytes):
    try:
        # Conectar a la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # Consulta SQL para insertar datos
        sql = """
            INSERT INTO docentes (nombres, apellidos, foto_rostro)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (nombre, apellido, foto_bytes))

        # Guardar cambios en la BD
        conexion.commit()

        # Cerrar recursos
        cursor.close()
        cerrar_conexion(conexion)   # ✅ Usamos nuestra función de cierre

        return True
    except Exception as e:
        print("❌ Error al registrar docente:", e)
        return False

