import cv2
import numpy as np
import face_recognition
from modules.conexion import crear_conexion, cerrar_conexion

def cargar_docentes():
    """
    Carga los docentes desde la BD y genera sus encodings faciales.
    Retorna una lista de diccionarios con:
    { 'cedula', 'nombres', 'apellidos', 'encoding' }
    """
    conexion = crear_conexion()
    if conexion is None:
        print("❌ No se pudo conectar a la BD")
        return []

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT cedula, nombres, apellidos, foto_rostro FROM docentes")
        resultados = cursor.fetchall()

        docentes = []
        for row in resultados:
            if row["foto_rostro"] is None:
                continue

            # Convertir BLOB -> numpy array -> imagen
            np_img = np.frombuffer(row["foto_rostro"], np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

            # Obtener encoding
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb)
            if len(encodings) > 0:
                docentes.append({
                    "cedula": row["cedula"],
                    "nombres": row["nombres"],
                    "apellidos": row["apellidos"],
                    "encoding": encodings[0]
                })
        return docentes
    except Exception as e:
        print("❌ Error al cargar docentes:", e)
        return []
    finally:
        cursor.close()
        cerrar_conexion(conexion)
