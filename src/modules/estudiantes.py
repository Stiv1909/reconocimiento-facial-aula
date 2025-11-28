from modules.conexion import crear_conexion, cerrar_conexion
from datetime import datetime
import pymysql.cursors


# ----------------------------------------------------------
#  Utilidad: Generar id_estudiante
# ----------------------------------------------------------
def generar_id_estudiante(anio, grado):
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        num, grupo = grado.split("-")
        prefijo_grado = f"{int(num):02d}{grupo}"   # "061"

        cursor.execute("SELECT COUNT(*) AS total FROM matriculas WHERE anio = %s AND grado = %s", (anio, grado))
        total = cursor.fetchone()["total"] or 0
        consecutivo = total + 1

        while True:
            id_est = f"{anio}{prefijo_grado}{consecutivo:02d}"
            cursor.execute("SELECT COUNT(*) AS existe FROM estudiantes WHERE id_estudiante = %s", (id_est,))
            existe = cursor.fetchone()["existe"]
            if existe:
                consecutivo += 1
            else:
                break

        return id_est
    finally:
        cursor.close()
        cerrar_conexion(conexion)


# ==========================================================
#   ESTUDIANTES (datos personales)
# ==========================================================
def registrar_estudiante(nombre, apellido, grado, foto_bytes=None, anio=None):
    conexion, cursor = None, None
    try:
        if anio is None:
            anio = datetime.now().year

        id_estudiante = generar_id_estudiante(anio, grado)

        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        sql = """INSERT INTO estudiantes (id_estudiante, nombres, apellidos, foto_rostro)
                 VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql, (id_estudiante, nombre, apellido, foto_bytes))
        conexion.commit()

        registrar_matricula(id_estudiante, grado, anio, estado="Estudiante")

        print(f"✅ Estudiante {nombre} {apellido} registrado con ID {id_estudiante}")
        return True

    except Exception as e:
        print("❌ Error al registrar estudiante:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)


def buscar_estudiantes(nombre="", grado="", estado="", anio=None):
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)

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

    if nombre:
        sql += " AND (e.nombres LIKE %s OR e.apellidos LIKE %s)"
        params.extend([f"%{nombre}%", f"%{nombre}%"])
    if grado:
        sql += " AND (SELECT m.grado FROM matriculas m WHERE m.id_estudiante = e.id_estudiante ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC LIMIT 1) = %s"
        params.append(grado)
    if estado:
        sql += " AND (SELECT m.estado FROM matriculas m WHERE m.id_estudiante = e.id_estudiante ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC LIMIT 1) = %s"
        params.append(estado)
    if anio:
        sql += " AND (SELECT m.anio FROM matriculas m WHERE m.id_estudiante = e.id_estudiante ORDER BY CAST(SUBSTRING_INDEX(m.id_matricula, '-', -1) AS UNSIGNED) DESC LIMIT 1) = %s"
        params.append(anio)

    cursor.execute(sql, tuple(params))
    resultados = cursor.fetchall()

    cursor.close()
    cerrar_conexion(conexion)
    return resultados


def actualizar_datos(id_estudiante, nombre, apellido, grado=None, estado=None):
    conexion, cursor = None, None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        sql_update = """UPDATE estudiantes
                        SET nombres = %s, apellidos = %s
                        WHERE id_estudiante = %s"""
        cursor.execute(sql_update, (nombre, apellido, id_estudiante))
        conexion.commit()

        cursor.execute("""
            SELECT id_matricula, grado, anio, estado
            FROM matriculas
            WHERE id_estudiante = %s
            ORDER BY CAST(SUBSTRING_INDEX(id_matricula, '-', -1) AS UNSIGNED) DESC
            LIMIT 1
        """, (id_estudiante,))
        last = cursor.fetchone()

        last_grado = last["grado"] if last else None
        last_estado = last["estado"] if last else None
        print(f"🔎 Última matrícula encontrada: {last}")

        if (grado is not None and grado != last_grado) or (estado is not None and estado != last_estado):
            anio_actual = datetime.now().year
            nuevo_grado = grado or last_grado
            nuevo_estado = estado if state_is_valid(estado) else (last_estado or "Estudiante")
            print(f"🟢 Cambio detectado → creando nueva matrícula para {id_estudiante}")
            registrar_matricula(id_estudiante, nuevo_grado, anio_actual, nuevo_estado)
        else:
            print("⚠ No se detectaron cambios → no se creó matrícula nueva")

        return True

    except Exception as e:
        print("❌ Error al actualizar estudiante:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)


def state_is_valid(s):
    return s in ("Estudiante", "Ex-Alumno")


def actualizar_rostro(id_estudiante, foto_bytes=None):
    if foto_bytes is None:
        print("⚠ No se recibió foto para actualizar.")
        return False

    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    sql = "UPDATE estudiantes SET foto_rostro = %s WHERE id_estudiante = %s"
    cursor.execute(sql, (foto_bytes, id_estudiante))
    conexion.commit()
    cursor.close()
    cerrar_conexion(conexion)
    print(f"✅ Rostro actualizado para {id_estudiante}")
    return True


# ==========================================================
#   MATRICULAS (historial académico)
# ==========================================================
def registrar_matricula(id_estudiante, grado, anio=None, estado="Estudiante"):
    conexion, cursor = None, None
    try:
        if anio is None:
            anio = datetime.now().year

        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        cursor.execute("SELECT COUNT(*) AS total FROM matriculas WHERE id_estudiante = %s", (id_estudiante,))
        total = cursor.fetchone()["total"] or 0
        consecutivo = total + 1

        id_matricula = f"{id_estudiante}-{consecutivo:02d}"

        sql_insert = """
            INSERT INTO matriculas (id_matricula, id_estudiante, grado, anio, estado)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql_insert, (id_matricula, id_estudiante, grado, anio, estado))
        conexion.commit()

        print(f"✅ Nueva matrícula registrada: {id_matricula} (grado={grado}, anio={anio}, estado={estado})")
        return True
    except Exception as e:
        print("❌ Error al registrar matrícula:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)


def actualizar_matricula(id_matricula, grado=None, estado=None):
    conexion, cursor = None, None
    try:
        conexion = crear_conexion()
        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        sets, params = [], []
        if grado is not None:
            sets.append("grado = %s")
            params.append(grado)
        if estado is not None:
            sets.append("estado = %s")
            params.append(estado)

        if not sets:
            return False

        sql_update = f"UPDATE matriculas SET {', '.join(sets)} WHERE id_matricula = %s"
        params.append(id_matricula)
        cursor.execute(sql_update, tuple(params))
        conexion.commit()
        print(f"✅ Matrícula {id_matricula} actualizada")
        return True
    except Exception as e:
        print("❌ Error al actualizar matrícula:", e)
        if conexion:
            conexion.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conexion:
            cerrar_conexion(conexion)


def obtener_matriculas_por_estudiante(id_estudiante):
    conexion = crear_conexion()
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    sql = """SELECT id_matricula, grado, anio, estado
             FROM matriculas WHERE id_estudiante = %s
             ORDER BY CAST(SUBSTRING_INDEX(id_matricula, '-', -1) AS UNSIGNED) DESC"""
    cursor.execute(sql, (id_estudiante,))
    resultados = cursor.fetchall()
    cursor.close()
    cerrar_conexion(conexion)
    return resultados
