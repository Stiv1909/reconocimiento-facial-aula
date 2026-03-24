# Importa PyMySQL para manejo de errores y cursores tipo diccionario
import pymysql

# Importa funciones de conexión y cierre de conexión a la base de datos
from modules.conexion import crear_conexion, cerrar_conexion


def buscar_historial(nombre_estudiante="", grado="", fecha="", equipo="", estado=""):
    """
    Retorna una lista de filas con los campos:
    [Estudiante, Grado, Equipo, Fecha, Hora-Inicio, Hora-Fin, Incidente]
    aplicando filtros dinámicos según los valores de los filtros.
    """


    # Inicializa conexión y cursor en None para poder cerrarlos en finally
    conexion = None
    cursor = None


    try:
        # Intenta crear la conexión con la base de datos
        conexion = crear_conexion()
        if not conexion:
            print("❌ No se pudo establecer la conexión con la base de datos.")
            return []


        # Usar DictCursor para acceder a los campos por nombre
        cursor = conexion.cursor(pymysql.cursors.DictCursor)


        # Consulta base
        query = """
            SELECT 
                CONCAT(e.nombres, ' ', e.apellidos) AS estudiante,
                m.grado,
                h.id_equipo,
                DATE_FORMAT(h.fecha, '%%d/%%m/%%Y') AS fecha,
                TIME_FORMAT(h.hora_inicio, '%%H:%%i') AS hora_inicio,
                TIME_FORMAT(h.hora_fin, '%%H:%%i') AS hora_fin,
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


        # Lista para almacenar filtros SQL dinámicos y sus valores
        filtros = []
        valores = []


        # Filtros dinámicos
        if nombre_estudiante.strip():
            # Filtra por coincidencia parcial en nombres o apellidos
            filtros.append("(e.nombres LIKE %s OR e.apellidos LIKE %s)")
            valores.extend([f"%{nombre_estudiante}%", f"%{nombre_estudiante}%"])


        if grado.strip():
            # Filtra por grado exacto
            filtros.append("m.grado = %s")
            valores.append(grado)


        if fecha.strip():
            # Convierte la fecha recibida en formato texto dd/mm/YYYY a tipo fecha SQL
            filtros.append("h.fecha = STR_TO_DATE(%s, '%%d/%%m/%%Y')")
            valores.append(fecha)


        if equipo.strip():
            # Filtra por identificador de equipo
            filtros.append("h.id_equipo = %s")
            valores.append(equipo)


        if estado.strip():
            # Filtra por estado de la matrícula
            filtros.append("m.estado = %s")
            valores.append(estado)


        # Unir filtros al query
        if filtros:
            query += " AND " + " AND ".join(filtros)


        # Agrega orden descendente por fecha y ascendente por hora de inicio
        query += " ORDER BY h.fecha DESC, h.hora_inicio ASC;"


        # Ejecutar consulta
        cursor.execute(query, valores)
        resultados = cursor.fetchall()  # Devuelve lista de diccionarios


        # Convierte cada diccionario en una lista ordenada con las columnas requeridas
        return [
    [
        row["estudiante"],
        row["grado"],
        row["id_equipo"],
        row["fecha"],
        row["hora_inicio"],
        row["hora_fin"],
        row["incidente"]
    ]
    for row in resultados
]


    except pymysql.Error as e:
        # Captura errores específicos de PyMySQL y retorna una lista vacía
        print(f"⚠ Error al consultar el historial: {e}")
        return []


    finally:
        # Cierra el cursor si fue creado
        if cursor:
            cursor.close()

        # Cierra la conexión a la base de datos
        cerrar_conexion(conexion)
