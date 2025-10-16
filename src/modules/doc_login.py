import cv2
import numpy as np
import face_recognition
from modules.conexion import crear_conexion, cerrar_conexion


def centrar_rostro_en_imagen(foto_bytes, output_size=200, margen=0.5):
    """
    Centra la imagen alrededor del rostro detectado.

    Parámetros:
    - foto_bytes: imagen en formato binario (por ejemplo, un BLOB de la base de datos).
    - output_size: tamaño final (en píxeles) de la imagen recortada y redimensionada.
    - margen: porcentaje adicional alrededor del rostro para no recortar demasiado cerca.

    Retorna:
    - bytes de la imagen recortada y centrada (formato JPG).
    Si no se detecta ningún rostro, devuelve la imagen original sin modificar.
    """

    # Convertir los bytes (BLOB) a un array numpy interpretable por OpenCV
    np_img = np.frombuffer(foto_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)  # Decodificar bytes en imagen BGR

    # Convertir de BGR (OpenCV) a RGB (formato que usa face_recognition)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Detectar rostros en la imagen (devuelve una lista de coordenadas)
    face_locations = face_recognition.face_locations(rgb)

    # Si detecta al menos un rostro
    if len(face_locations) > 0:
        top, right, bottom, left = face_locations[0]  # Tomamos el primer rostro

        # Calcular alto y ancho del área del rostro detectado
        h, w = bottom - top, right - left

        # Ampliar el recorte aplicando un margen adicional
        top = max(0, int(top - h * margen))
        bottom = min(img.shape[0], int(bottom + h * margen))
        left = max(0, int(left - w * margen))
        right = min(img.shape[1], int(right + w * margen))

        # Recortar la imagen manteniendo algo de contexto (no solo el rostro)
        recorte = img[top:bottom, left:right]

        # Redimensionar el recorte a un tamaño estándar (ej: 200x200 píxeles)
        recorte = cv2.resize(recorte, (output_size, output_size))

        # Codificar de nuevo a bytes (formato JPG)
        _, buffer = cv2.imencode(".jpg", recorte)
        return buffer.tobytes()
    else:
        # Si no se detecta rostro, se devuelve la imagen original sin recorte
        return foto_bytes



def cargar_docentes():
    """
    Carga los docentes desde la base de datos y genera sus representaciones faciales (encodings).

    Proceso:
    1. Conecta a la BD y obtiene los docentes con su información y la foto del rostro.
    2. Convierte el campo BLOB de la foto en imagen.
    3. Calcula el encoding facial (vector de 128 valores generado por face_recognition).
    4. Centra la imagen del rostro para una presentación uniforme.
    5. Devuelve una lista de diccionarios con toda la información del docente.

    Estructura del resultado:
    [
        {
            'cedula': str,
            'nombres': str,
            'apellidos': str,
            'rol': 'admin' o 'docente',
            'encoding': numpy.ndarray,
            'foto_rostro': bytes (imagen centrada)
        },
        ...
    ]
    """

    # Crear conexión con la base de datos
    conexion = crear_conexion()
    if conexion is None:
        print("❌ No se pudo conectar a la BD")
        return []

    cursor = conexion.cursor(dictionary=True)
    try:
        # Obtener los campos relevantes de la tabla docentes
        cursor.execute("SELECT cedula, nombres, apellidos, es_admin, foto_rostro FROM docentes")
        resultados = cursor.fetchall()

        docentes = []
        for row in resultados:
            # Si no tiene foto registrada, se omite
            if row["foto_rostro"] is None:
                continue

            # Convertir el campo BLOB a imagen
            np_img = np.frombuffer(row["foto_rostro"], np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

            # Convertir a RGB para el procesamiento facial
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Generar encoding facial (devuelve lista, normalmente con un solo elemento)
            encodings = face_recognition.face_encodings(rgb)

            if len(encodings) > 0:
                # Centrar y recortar la foto del rostro para mostrarla en la interfaz
                foto_centrada = centrar_rostro_en_imagen(row["foto_rostro"])

                # Agregar docente al listado
                docentes.append({
                    "cedula": row["cedula"],
                    "nombres": row["nombres"],
                    "apellidos": row["apellidos"],
                    # Mapeo de flag 'es_admin' a un rol legible
                    "rol": "admin" if row["es_admin"] == 1 else "docente",
                    "encoding": encodings[0],  # Vector de características del rostro
                    "foto_rostro": foto_centrada
                })

        return docentes

    except Exception as e:
        # Captura errores (por ejemplo, fallos de decodificación o SQL)
        print("❌ Error al cargar docentes:", e)
        return []

    finally:
        # Asegura el cierre correcto del cursor y la conexión
        cursor.close()
        cerrar_conexion(conexion)
