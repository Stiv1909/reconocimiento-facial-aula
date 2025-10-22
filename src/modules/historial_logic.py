from mysql.connector import Error
from modules.conexion import crear_conexion, cerrar_conexion


def buscar_historial(nombre_estudiante="", grado="", fecha="", equipo="", estado=""):
    """
    Retorna una lista de filas con los campos:
    [Estudiante, Grado, Equipo, Fecha, Hora-Inicio, Hora-Fin, Incidente]
    aplicando filtros dinámicos según los valores de los filtros.
    """

    conexion = None
    cursor = None

    try:
        conexion = crear_conexion()
        if not conexion:
            print("❌ No se pudo establecer la conexión con la base de datos.")
            return []

        cursor = conexion.cursor()

        # 🔹 Consulta base con los JOIN necesarios
        query = """
            SELECT 
                CONCAT(e.nombres, ' ', e.apellidos) AS estudiante,
                m.grado,
                h.id_equipo,
                DATE_FORMAT(h.fecha, '%d/%m/%Y') AS fecha,
                TIME_FORMAT(h.hora_inicio, '%H:%i') AS hora_inicio,
                TIME_FORMAT(h.hora_fin, '%H:%i') AS hora_fin,
                COALESCE(i.descripcion, 'Sin novedad') AS incidente
            FROM historial h
            JOIN matriculas m ON h.id_matricula = m.id_matricula
            JOIN estudiantes e ON m.id_estudiante = e.id_estudiante
            LEFT JOIN incidentes i 
                ON i.id_matricula = h.id_matricula 
                AND i.id_equipo = h.id_equipo 
                AND i.fecha = h.fecha
            WHERE 1=1
        """

        filtros = []
        valores = []

        # 🔹 Filtros dinámicos según los valores recibidos
        if nombre_estudiante.strip():
            filtros.append("(e.nombres LIKE %s OR e.apellidos LIKE %s)")
            valores.extend([f"%{nombre_estudiante}%", f"%{nombre_estudiante}%"])

        if grado.strip():
            filtros.append("m.grado = %s")
            valores.append(grado)

        if fecha.strip():
            filtros.append("h.fecha = STR_TO_DATE(%s, '%%d/%%m/%%Y')")
            valores.append(fecha)

        if equipo.strip():
            filtros.append("h.id_equipo = %s")
            valores.append(equipo)

        if estado.strip():
            filtros.append("m.estado = %s")
            valores.append(estado)

        # 🔹 Unir los filtros al query si existen
        if filtros:
            query += " AND " + " AND ".join(filtros)

        query += " ORDER BY h.fecha DESC, h.hora_inicio ASC;"

        # 🔹 Ejecutar consulta
        cursor.execute(query, valores)
        resultados = cursor.fetchall()

        return resultados

    except Error as e:
        print(f"⚠ Error al consultar el historial: {e}")
        return []

    finally:
        if cursor:
            cursor.close()
        cerrar_conexion(conexion)
