from modules.conexion import crear_conexion, cerrar_conexion

# ==========================================================
#   FUNCIÓN: registrar_docente
#   Descripción:
#       - Inserta un nuevo docente en la tabla "docentes"
#       - Guarda cédula, nombres, apellidos, celular, si es admin y la foto
# ==========================================================
def registrar_docente(cedula, nombre, apellido, celular, es_admin, foto_bytes):
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        sql = """
            INSERT INTO docentes (cedula, nombres, apellidos, celular, es_admin, foto_rostro)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (cedula, nombre, apellido, celular, es_admin, foto_bytes))
        conexion.commit()

        cursor.close()
        cerrar_conexion(conexion)
        print(f"✅ Docente {nombre} {apellido} registrado con cédula {cedula}")
        return True

    except Exception as e:
        print("❌ Error al registrar docente:", e)
        return False
