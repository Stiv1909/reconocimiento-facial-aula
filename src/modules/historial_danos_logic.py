# historial_danos_logic.py
# Lógica para buscar daños registrados en equipos

import pymysql
from modules.conexion import crear_conexion, cerrar_conexion


def buscar_danos(nombre_estudiante="", grado="", equipo="", fecha=""):
    """
    Retorna una lista de filas con los campos:
    [Equipo, Estudiante, Grado, Fecha, Descripción, Estado]
    aplicando filtros dinámicos según los valores de los filtros.
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
                i.id_equipo AS equipo,
                CONCAT(e.nombres, ' ', e.apellidos) AS estudiante,
                m.grado,
                DATE_FORMAT(i.fecha, '%%d/%%m/%%Y') AS fecha,
                i.descripcion,
                CASE 
                    WHEN e.id_estudiante IS NOT NULL THEN 'Reportado'
                    ELSE 'Sin estudiante asignado'
                END AS estado
            FROM incidentes i
            LEFT JOIN estudiantes e ON i.id_estudiante = e.id_estudiante
            LEFT JOIN matriculas m ON m.id_estudiante = e.id_estudiante AND m.estado = 'Estudiante'
            WHERE i.descripcion LIKE %s
        """

        filtros = []
        valores = ["%daño%"]

        if nombre_estudiante.strip():
            filtros.append("(e.nombres LIKE %s OR e.apellidos LIKE %s)")
            valores.extend([f"%{nombre_estudiante}%", f"%{nombre_estudiante}%"])

        if grado.strip():
            filtros.append("m.grado = %s")
            valores.append(grado)

        if equipo.strip():
            filtros.append("i.id_equipo = %s")
            valores.append(equipo)

        if fecha.strip():
            filtros.append("i.fecha = STR_TO_DATE(%s, '%%d/%%m/%%Y')")
            valores.append(fecha)

        if filtros:
            query += " AND " + " AND ".join(filtros)

        query += " ORDER BY i.fecha DESC, i.id_incidente DESC;"

        cursor.execute(query, valores)
        resultados = cursor.fetchall()

        return [
            [
                row["equipo"],
                row["estudiante"],
                row["grado"] if row["grado"] else "—",
                row["fecha"],
                row["descripcion"],
                row["estado"]
            ]
            for row in resultados
        ]

    except pymysql.Error as e:
        print(f"⚠ Error al consultar daños: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        cerrar_conexion(conexion)