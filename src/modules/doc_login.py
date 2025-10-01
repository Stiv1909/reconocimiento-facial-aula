import cv2
import numpy as np
import face_recognition
from modules.conexion import crear_conexion, cerrar_conexion


def centrar_rostro_en_imagen(foto_bytes, output_size=200, margen=0.5):
    """
    Centra la imagen alrededor del rostro detectado.
    - No recorta solo la cara, sino que toma un marco más grande.
    - margen: porcentaje adicional alrededor del rostro.
    """
    np_img = np.frombuffer(foto_bytes, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb)

    if len(face_locations) > 0:
        top, right, bottom, left = face_locations[0]

        # Calcular ancho y alto del rostro
        h, w = bottom - top, right - left

        # Expandir con un margen alrededor
        top = max(0, int(top - h * margen))
        bottom = min(img.shape[0], int(bottom + h * margen))
        left = max(0, int(left - w * margen))
        right = min(img.shape[1], int(right + w * margen))

        # Recorte manteniendo contexto
        recorte = img[top:bottom, left:right]

        # Redimensionar al tamaño de salida
        recorte = cv2.resize(recorte, (output_size, output_size))

        # Convertir de nuevo a bytes
        _, buffer = cv2.imencode(".jpg", recorte)
        return buffer.tobytes()
    else:
        # Si no detecta rostro, devuelve original
        return foto_bytes


def cargar_docentes():
    """
    Carga los docentes desde la BD y genera sus encodings faciales.
    Retorna una lista de diccionarios con:
    { 'cedula', 'nombres', 'apellidos', 'encoding', 'foto_rostro' }
    """
    conexion = crear_conexion()
    if conexion is None:
        print("❌ No se pudo conectar a la BD")
        return []

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT cedula, nombres, apellidos, es_admin, foto_rostro FROM docentes")
        resultados = cursor.fetchall()

        docentes = []
        for row in resultados:
            if row["foto_rostro"] is None:
                continue

            # BLOB -> numpy -> imagen
            np_img = np.frombuffer(row["foto_rostro"], np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

            # Obtener encoding (en original, no recortada)
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)

            if len(encodings) > 0:
                # Foto centrada según el rostro
                foto_centrada = centrar_rostro_en_imagen(row["foto_rostro"])

                docentes.append({
                    "cedula": row["cedula"],
                    "nombres": row["nombres"],
                    "apellidos": row["apellidos"],
                    "rol": "admin" if row["es_admin"] == 1 else "docente",  # 👈 aquí hacemos el mapeo
                    "encoding": encodings[0],
                    "foto_rostro": foto_centrada
                })
        return docentes
    except Exception as e:
        print("❌ Error al cargar docentes:", e)
        return []
    finally:
        cursor.close()
        cerrar_conexion(conexion)
