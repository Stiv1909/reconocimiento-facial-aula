from modules.conexion import crear_conexion, cerrar_conexion

def registrar_docente(nombre, apellido, foto_bytes):
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        sql = "INSERT INTO docentes (nombres, apellidos, foto_rostro) VALUES (%s, %s, %s)"
        cursor.execute(sql, (nombre, apellido, foto_bytes))

        conexion.commit()
        cursor.close()
        cerrar_conexion(conexion)   # ✅ usar tu función, no conexion.close()
        return True
    except Exception as e:
        print("❌ Error al registrar docente:", e)
        return False

