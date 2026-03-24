# Importa las funciones para abrir y cerrar conexión con la base de datos
from modules.conexion import crear_conexion, cerrar_conexion

# Importa datetime para obtener el año actual del sistema
from datetime import datetime

# Importa cursores tipo diccionario de PyMySQL
import pymysql.cursors



# ----------------------------------------------------------
#  Utilidad: Generar id_estudiante
# ----------------------------------------------------------
def generar_id_estudiante(anio, grado):
    # Crea conexión con la base de datos
    conexion = crear_conexion()

    # Crea cursor tipo diccionario para acceder a los campos por nombre
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Separa el grado en número y grupo, por ejemplo "6-1" -> "6" y "1"
        num, grupo = grado.split("-")

        # Genera el prefijo del grado con dos dígitos para el número
        prefijo_grado = f"{int(num):02d}{grupo}"   # "061"


        # Cuenta cuántas matrículas existen en ese año y grado
        cursor.execute("SELECT COUNT(*) AS total FROM matriculas WHERE anio = %s AND grado = %s", (anio, grado))
        total = cursor.fetchone()["total"] or 0

        # Calcula el siguiente consecutivo disponible
        consecutivo = total + 1


        while True:
            # Construye el ID del estudiante usando año + grado + consecutivo
            id_est = f"{anio}{prefijo_grado}{consecutivo:02d}"

            # Verifica si ese ID ya existe en la tabla estudiantes
            cursor.execute("SELECT COUNT(*) AS existe FROM estudiantes WHERE id_estudiante = %s", (id_est,))
            existe = cursor.fetchone()["existe"]

            if existe:
                # Si el ID ya existe, incrementa el consecutivo y vuelve a intentar
                consecutivo += 1
            else:
                # Si el ID no existe, sale del ciclo
                break


        # Retorna el ID generado
        return id_est
    finally:
        # Cierra cursor y conexión al finalizar
        cursor.close()
        cerrar_conexion(conexion)



# ==========================================================
#   ESTUDIANTES (datos personales)
# ==========================================================
def registrar_estudiante(nombre, apellido, grado, foto_bytes=None, anio=None):
    # Inicializa las variables de conexión y cursor
    conexion, cursor = None, None
    try:
        # Si no se especifica el año, toma el actual del sistema
        if anio is None:
            anio = datetime.now().year


        # Genera el ID único del estudiante
        id_estudiante = generar_id_estudiante(anio, grado)


        # Crea la conexión con la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)


        # Inserta los datos personales del estudiante en la tabla estudiantes
        sql = """INSERT INTO estudiantes (id_estudiante, nombres, apellidos, foto_rostro)
                 VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql, (id_estudiante, nombre, apellido, foto_bytes))
        conexion.commit()


        # Registra automáticamente la primera matrícula del estudiante
        registrar_matricula(id_estudiante, grado, anio, estado="Estudiante")


        # Muestra mensaje de éxito en consola
        print(f"✅ Estudiante {nombre} {apellido} registrado con ID {id_estudiante}")
        return True


    except Exception as e:
        # Si ocurre un error, lo muestra y revierte la transacción si aplica
        print("❌ Error al registrar estudiante:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        # Cierra cursor y conexión si fueron creados
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)



def buscar_estudiantes(nombre="", grado="", estado="", anio=None):
    # Crea conexión y cursor para consultar estudiantes
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)


    # Consulta base que obtiene datos del estudiante y su última matrícula registrada
    sql = """
        SELECT e.id_estudiante, e.nombres, e.apellidos,
               (SELECT m.id_matricula FROM matriculas m WHERE m.id_estudiante = e.id_estudiante
                    ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC
                    LIMIT 1) AS id_matricula,
               (SELECT m.grado FROM matriculas m WHERE m.id_estudiante = e.id_estudiante
                    ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC
                    LIMIT 1) AS grado,
               (SELECT m.anio FROM matriculas m WHERE m.id_estudiante = e.id_estudiante
                    ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC
                    LIMIT 1) AS anio,
               (SELECT m.estado FROM matriculas m WHERE m.id_estudiante = e.id_estudiante
                    ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC
                    LIMIT 1) AS estado
        FROM estudiantes e
        WHERE 1=1
    """
    params = []


    # Agrega filtro por nombre o apellido si se proporcionó
    if nombre:
        sql += " AND (e.nombres LIKE %s OR e.apellidos LIKE %s)"
        params.extend([f"%{nombre}%", f"%{nombre}%"])

    # Agrega filtro por grado usando la última matrícula del estudiante
    if grado:
        sql += " AND (SELECT m.grado FROM matriculas m WHERE m.id_estudiante = e.id_estudiante ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC LIMIT 1) = %s"
        params.append(grado)

    # Agrega filtro por estado usando la última matrícula del estudiante
    if estado:
        sql += " AND (SELECT m.estado FROM matriculas m WHERE m.id_estudiante = e.id_estudiante ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC LIMIT 1) = %s"
        params.append(estado)

    # Agrega filtro por año usando la última matrícula del estudiante
    if anio:
        sql += " AND (SELECT m.anio FROM matriculas m WHERE m.id_estudiante = e.id_estudiante ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC LIMIT 1) = %s"
        params.append(anio)


    # Ejecuta la consulta con los filtros dinámicos
    cursor.execute(sql, tuple(params))
    resultados = cursor.fetchall()


    # Cierra recursos y retorna resultados
    cursor.close()
    cerrar_conexion(conexion)
    return resultados



def actualizar_datos(id_estudiante, nombre, apellido, grado=None, estado=None):
    # Inicializa conexión y cursor
    conexion, cursor = None, None
    try:
        # Crea conexión a la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)


        # Actualiza los datos personales básicos del estudiante
        sql_update = """UPDATE estudiantes
                        SET nombres = %s, apellidos = %s
                        WHERE id_estudiante = %s"""
        cursor.execute(sql_update, (nombre, apellido, id_estudiante))
        conexion.commit()


        # Consulta la última matrícula registrada del estudiante
        cursor.execute("""
            SELECT id_matricula, grado, anio, estado
            FROM matriculas
            WHERE id_estudiante = %s
            ORDER BY CAST(SUBSTRING_INDEX(id_matricula, '-', -1) AS UNSIGNED) DESC
            LIMIT 1
        """, (id_estudiante,))
        last = cursor.fetchone()


        # Obtiene el último grado y estado registrados
        last_grado = last["grado"] if last else None
        last_estado = last["estado"] if last else None
        print(f"🔎 Última matrícula encontrada: {last}")


        # Si hay cambios en grado o estado, genera una nueva matrícula histórica
        if (grado is not None and grado != last_grado) or (estado is not None and estado != last_estado):
            anio_actual = datetime.now().year
            nuevo_grado = grado or last_grado
            nuevo_estado = estado if state_is_valid(estado) else (last_estado or "Estudiante")
            print(f"🟢 Cambio detectado → creando nueva matrícula para {id_estudiante}")
            registrar_matricula(id_estudiante, nuevo_grado, anio_actual, nuevo_estado)
        else:
            # Si no hubo cambios relevantes, no crea matrícula nueva
            print("⚠ No se detectaron cambios → no se creó matrícula nueva")


        return True


    except Exception as e:
        # Si ocurre un error, lo informa y revierte cambios
        print("❌ Error al actualizar estudiante:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        # Cierra recursos
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)



def state_is_valid(s):
    # Verifica si el estado enviado es uno de los permitidos
    return s in ("Estudiante", "Ex-Alumno")



def actualizar_rostro(id_estudiante, foto_bytes=None):
    # Si no se recibe imagen, se cancela la actualización
    if foto_bytes is None:
        print("⚠ No se recibió foto para actualizar.")
        return False


    # Crea conexión y cursor para actualizar la foto del estudiante
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Actualiza el campo foto_rostro del estudiante
    sql = "UPDATE estudiantes SET foto_rostro = %s WHERE id_estudiante = %s"
    cursor.execute(sql, (foto_bytes, id_estudiante))
    conexion.commit()
    cursor.close()
    cerrar_conexion(conexion)

    # Muestra confirmación en consola
    print(f"✅ Rostro actualizado para {id_estudiante}")
    return True



# ==========================================================
#   MATRICULAS (historial académico)
# ==========================================================
def registrar_matricula(id_estudiante, grado, anio=None, estado="Estudiante"):
    # Inicializa conexión y cursor
    conexion, cursor = None, None
    try:
        # Si no se especifica el año, usa el actual
        if anio is None:
            anio = datetime.now().year


        # Crea conexión con la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)


        # Cuenta cuántas matrículas tiene ya el estudiante
        cursor.execute("SELECT COUNT(*) AS total FROM matriculas WHERE id_estudiante = %s", (id_estudiante,))
        total = cursor.fetchone()["total"] or 0
        consecutivo = total + 1


        # Construye el id de matrícula agregando un consecutivo al id del estudiante
        id_matricula = f"{id_estudiante}-{consecutivo:02d}"


        # Inserta la nueva matrícula en la tabla matriculas
        sql_insert = """
            INSERT INTO matriculas (id_matricula, id_estudiante, grado, anio, estado)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql_insert, (id_matricula, id_estudiante, grado, anio, estado))
        conexion.commit()


        # Muestra confirmación en consola
        print(f"✅ Nueva matrícula registrada: {id_matricula} (grado={grado}, anio={anio}, estado={estado})")
        return True
    except Exception as e:
        # Si ocurre un error, revierte la operación
        print("❌ Error al registrar matrícula:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        # Cierra recursos
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)



def actualizar_matricula(id_matricula, grado=None, estado=None):
    # Inicializa conexión y cursor
    conexion, cursor = None, None
    try:
        # Crea conexión con la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)


        # Lista de campos a actualizar y sus parámetros
        sets, params = [], []
        if grado is not None:
            sets.append("grado = %s")
            params.append(grado)
        if estado is not None:
            sets.append("estado = %s")
            params.append(estado)


        # Si no se recibió ningún campo para actualizar, retorna False
        if not sets:
            return False


        # Construye la consulta dinámica de actualización
        sql_update = f"UPDATE matriculas SET {', '.join(sets)} WHERE id_matricula = %s"
        params.append(id_matricula)
        cursor.execute(sql_update, tuple(params))
        conexion.commit()

        # Muestra mensaje de confirmación
        print(f"✅ Matrícula {id_matricula} actualizada")
        return True
    except Exception as e:
        # Si ocurre un error, revierte cambios
        print("❌ Error al actualizar matrícula:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        # Cierra recursos
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)



def obtener_matriculas_por_estudiante(id_estudiante):
    # Crea conexión y cursor para consultar matrículas del estudiante
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

    # Consulta todas las matrículas del estudiante ordenadas de la más reciente a la más antigua
    sql = """SELECT id_matricula, grado, anio, estado
             FROM matriculas WHERE id_estudiante = %s
             ORDER BY CAST(SUBSTRING_INDEX(id_matricula, '-', -1) AS UNSIGNED) DESC"""
    cursor.execute(sql, (id_estudiante,))
    resultados = cursor.fetchall()

    # Cierra recursos y retorna los resultados
    cursor.close()
    cerrar_conexion(conexion)
    return resultados
