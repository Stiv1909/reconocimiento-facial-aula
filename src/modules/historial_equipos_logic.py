# historial_equipos_logic.py
# Lógica para buscar el historial de equipos (altas, bajas, cambios de estado)

import pymysql
from modules.conexion import crear_conexion, cerrar_conexion


def buscar_historial_equipos(codigo="", tipo_accion="", fecha=""):
    """
    Retorna una lista de filas con los campos:
    [Equipo, Tipo Acción, Estado Anterior, Estado Nuevo, Descripción, Fecha, Hora, Docente]
    aplicando filtros dinámicos.
    """
    conexion = None
    cursor = None

    try:
        conexion = crear_conexion()
        if not conexion:
            print("❌ No se pudo establecer la conexión con la base de datos.")
            return []

        cursor = conexion.cursor(pymysql.cursors.DictCursor)

        query = """
            SELECT 
                he.id_equipo AS equipo,
                he.tipo_accion,
                COALESCE(he.estado_anterior, '—') AS estado_anterior,
                COALESCE(he.estado_nuevo, '—') AS estado_nuevo,
                COALESCE(he.descripcion, '—') AS descripcion,
                DATE_FORMAT(he.fecha, '%%d/%%m/%%Y') AS fecha,
                TIME_FORMAT(he.hora, '%%H:%%i') AS hora,
                CONCAT(d.nombres, ' ', d.apellidos) AS docente
            FROM historial_equipos he
            JOIN docentes d ON he.cedula = d.cedula
            WHERE 1=1
        """

        filtros = []
        valores = []

        if codigo.strip():
            filtros.append("he.id_equipo = %s")
            valores.append(codigo)

        if tipo_accion.strip():
            filtros.append("he.tipo_accion = %s")
            valores.append(tipo_accion)

        if fecha.strip():
            filtros.append("he.fecha = STR_TO_DATE(%s, '%%d/%%m/%%Y')")
            valores.append(fecha)

        if filtros:
            query += " AND " + " AND ".join(filtros)

        query += " ORDER BY he.fecha DESC, he.hora DESC;"

        cursor.execute(query, valores)
        resultados = cursor.fetchall()

        return [
            [
                row["equipo"],
                row["tipo_accion"],
                row["estado_anterior"],
                row["estado_nuevo"],
                row["descripcion"],
                row["fecha"],
                row["hora"],
                row["docente"]
            ]
            for row in resultados
        ]

    except pymysql.Error as e:
        print(f"⚠ Error al consultar historial de equipos: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        cerrar_conexion(conexion)


def registrar_historial_equipo(id_equipo, tipo_accion, estado_anterior, estado_nuevo, descripcion, cedula):
    """
    Registra una acción en el historial de equipos.
    Retorna (True, mensaje) si éxito, (False, mensaje) si error.
    """
    conexion = None
    cursor = None

    try:
        conexion = crear_conexion()
        cursor = conexion.cursor()

        from datetime import datetime
        now = datetime.now()

        sql = """
            INSERT INTO historial_equipos 
            (id_equipo, tipo_accion, estado_anterior, estado_nuevo, descripcion, fecha, hora, id_docente)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(sql, (
            id_equipo, tipo_accion, estado_anterior, estado_nuevo, descripcion,
            now.date(), now.time(), id_docente
        ))
        conexion.commit()

        return (True, f"Historial registrado para {id_equipo}")

    except pymysql.Error as e:
        print(f"⚠ Error al registrar historial: {e}")
        if conexion:
            conexion.rollback()
        return (False, str(e))

    finally:
        if cursor:
            cursor.close()
        cerrar_conexion(conexion)