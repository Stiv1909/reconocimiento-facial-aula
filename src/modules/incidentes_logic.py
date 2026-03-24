# modules/incidentes_logic.py

# Importa date y datetime para manejar fecha actual y hora actual
from datetime import date, datetime

# Importa funciones de conexión a base de datos
from modules.conexion import crear_conexion, cerrar_conexion

# Importa la sesión del sistema para identificar al docente autenticado
from modules.sesion import Sesion

# Importa PyMySQL para cursores y operaciones con MySQL
import pymysql


def _obtener_cedula_sesion():
    """
    Intenta obtener la cédula del docente desde la sesión con varias claves posibles.
    Devuelve la cédula como string o None si no encuentra.
    """
    # Inicializa usuario en None
    usuario = None
    try:
        # Intenta obtener el usuario actual desde la sesión
        usuario = Sesion.obtener_usuario()
    except Exception:
        usuario = None


    # Si no hay usuario en sesión, retorna None
    if not usuario:
        return None


    # posibles claves donde la cédula podría estar
    for key in ("cedula", "id", "usuario", "username", "dni"):
        if isinstance(usuario, dict) and key in usuario and usuario[key]:
            return str(usuario[key])


    # si usuario es objeto con atributos
    for attr in ("cedula", "id", "username", "dni"):
        if hasattr(usuario, attr):
            val = getattr(usuario, attr)
            if val:
                return str(val)


    return None



def obtener_equipos_en_uso():
    """
    Retorna lista de equipos que actualmente están en uso (historial.hora_fin IS NULL).
    Cada elemento es dict {'id_equipo': 'E-01'}.
    """
    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return []


    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Consulta los equipos con historial activo
        cursor.execute("""
            SELECT DISTINCT h.id_equipo
            FROM historial h
            WHERE h.hora_fin IS NULL
            ORDER BY h.id_equipo
        """)
        rows = cursor.fetchall()
        return rows or []
    finally:
        # Cierra recursos de base de datos
        cursor.close()
        cerrar_conexion(conexion)



def obtener_estudiante_por_equipo(id_equipo):
    """
    Dado id_equipo devuelve el estudiante que actualmente lo está usando
    (historial.hora_fin IS NULL). Retorna dict con keys:
    id_matricula, id_estudiante, nombres, apellidos
    o None si no hay nadie.
    """
    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return None


    # Crea cursor tipo diccionario
    cursor = conexion.cursor(pymysql.cursors.DictCursor)
    try:
        # Consulta el estudiante más reciente que está usando ese equipo
        cursor.execute("""
            SELECT m.id_matricula,
                   e.id_estudiante,
                   e.nombres,
                   e.apellidos
            FROM historial h
            JOIN matriculas m ON h.id_matricula = m.id_matricula
            JOIN estudiantes e ON m.id_estudiante = e.id_estudiante
            WHERE h.id_equipo = %s AND h.hora_fin IS NULL
            ORDER BY h.fecha DESC, h.hora_inicio DESC
            LIMIT 1
        """, (id_equipo,))
        row = cursor.fetchone()
        return row
    finally:
        # Cierra recursos
        cursor.close()
        cerrar_conexion(conexion)



def registrar_incidente(id_matricula, id_equipo, descripcion, nuevo_estado=None):
    """
    Inserta un incidente usando:
      - cedula: tomada desde la sesión
      - id_equipo
      - id_matricula
      - descripcion
      - fecha: date.today()
    Además actualiza el estado del equipo si se indica nuevo_estado.
    Si el nuevo estado es "dañado", cierra el historial (asigna hora_fin actual).
    """
    # Obtiene la cédula del docente autenticado desde la sesión
    cedula = _obtener_cedula_sesion()
    if not cedula:
        return False, "No hay una sesión de docente activa (no se encontró cédula)."


    # Crea conexión con la base de datos
    conexion = crear_conexion()
    if not conexion:
        return False, "No se pudo conectar con la base de datos."


    # Crea cursor estándar para ejecutar consultas
    cursor = conexion.cursor()
    try:
        # Verificar que el estudiante esté usando el equipo actualmente
        cursor.execute("""
            SELECT 1 FROM historial
            WHERE id_matricula = %s AND id_equipo = %s AND hora_fin IS NULL
            LIMIT 1
        """, (id_matricula, id_equipo))
        if cursor.fetchone() is None:
            return False, "El estudiante no está actualmente en clase usando ese equipo."


        # Insertar el incidente
        insert_sql = """
            INSERT INTO incidentes (cedula, id_equipo, id_matricula, descripcion, fecha)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_sql, (cedula, id_equipo, id_matricula, descripcion, date.today()))


        # Actualizar el estado del equipo si se proporcionó
        if nuevo_estado:
            cursor.execute("""
                UPDATE equipos SET estado = %s WHERE id_equipo = %s
            """, (nuevo_estado.lower(), id_equipo))


            # si el estado es "dañado", cerrar el historial activo
            if nuevo_estado.lower() == "dañado":
                hora_fin = datetime.now().strftime("%H:%M:%S")
                cursor.execute("""
                    UPDATE historial
                    SET hora_fin = %s
                    WHERE id_equipo = %s AND hora_fin IS NULL
                """, (hora_fin, id_equipo))


        # Confirma la transacción
        conexion.commit()
        return True, "Incidente registrado correctamente. Estado del equipo actualizado."
    except Exception as e:
        # Revierte la transacción si ocurre cualquier error
        conexion.rollback()
        return False, f"Error al registrar incidente: {e}"
    finally:
        # Cierra recursos de base de datos
        cursor.close()
        cerrar_conexion(conexion)
