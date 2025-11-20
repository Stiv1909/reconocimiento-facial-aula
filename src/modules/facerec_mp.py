# modules/facerec_mp.py
import cv2
import numpy as np
import mediapipe as mp
from typing import List, Tuple

mp_face_mesh = mp.solutions.face_mesh

# Parámetros
EMBED_DIM = 128
RANDOM_SEED = 42
MAX_LANDMARKS = 468  # MediaPipe FaceMesh tiene 468 landmarks
MAX_INPUT_DIM = MAX_LANDMARKS * 3  # x,y,z por landmark

# Proyección aleatoria determinista
_rng = np.random.RandomState(RANDOM_SEED)
_PROJ_MATRIX = _rng.normal(size=(MAX_INPUT_DIM, EMBED_DIM)).astype(np.float32)

# Inicializar FaceMesh compartido (mejor rendimiento si se reutiliza)
_face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=4,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

def _landmarks_to_vector(landmarks) -> np.ndarray:
    pts = np.array([[lm.x, lm.y, lm.z] for lm in landmarks], dtype=np.float32)
    return pts.flatten()

def _normalize_landmark_vector(vec: np.ndarray) -> np.ndarray:
    if vec.size == 0:
        return vec
    pts = vec.reshape(-1, 3)
    # intentamos usar ojos para centrar/escala (índices conocidos)
    try:
        left = pts[33]
        right = pts[263]
        center = (left + right) / 2.0
        scale = np.linalg.norm(left - right)
        if scale < 1e-6:
            scale = 1.0
    except Exception:
        center = pts.mean(axis=0)
        scale = np.std(pts) + 1e-6

    pts = (pts - center) / scale
    return pts.flatten()

def landmarks_to_embedding(landmarks) -> np.ndarray:
    vec = _landmarks_to_vector(landmarks)
    norm_vec = _normalize_landmark_vector(vec)

    # pad / truncate to MAX_INPUT_DIM
    if norm_vec.size < MAX_INPUT_DIM:
        norm_vec = np.concatenate([norm_vec, np.zeros(MAX_INPUT_DIM - norm_vec.size, dtype=np.float32)])
    elif norm_vec.size > MAX_INPUT_DIM:
        norm_vec = norm_vec[:MAX_INPUT_DIM]

    emb = np.dot(norm_vec, _PROJ_MATRIX)  # (EMBED_DIM,)
    n = np.linalg.norm(emb)
    if n > 0:
        emb = emb / n
    return emb.astype(np.float32)

def get_face_embeddings_from_frame(frame_bgr, max_faces=2) -> List[Tuple[np.ndarray, tuple]]:
    """
    Detecta hasta max_faces y devuelve lista de (embedding, bbox)
    bbox = (xmin, ymin, xmax, ymax) en pixeles relativos al frame
    """
    if frame_bgr is None:
        return []

    img_h, img_w = frame_bgr.shape[:2]
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    results = _face_mesh.process(frame_rgb)
    if not results.multi_face_landmarks:
        return []

    out = []
    for face_landmarks in results.multi_face_landmarks[:max_faces]:
        lm = face_landmarks.landmark
        emb = landmarks_to_embedding(lm)

        xs = np.array([p.x for p in lm])
        ys = np.array([p.y for p in lm])
        xmin = int(max(0, xs.min() * img_w))
        xmax = int(min(img_w - 1, xs.max() * img_w))
        ymin = int(max(0, ys.min() * img_h))
        ymax = int(min(img_h - 1, ys.max() * img_h))
        bbox = (xmin, ymin, xmax, ymax)

        out.append((emb, bbox))
    return out

def compare_embeddings(e1: np.ndarray, e2: np.ndarray) -> float:
    """
    Distancia coseno aproximada: 0 = idéntico, mayor = distinto.
    Ambos vectores deben estar L2 normalizados.
    """
    return 1.0 - float(np.dot(e1, e2))
