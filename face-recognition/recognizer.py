#CNN BRAIN

import numpy as np
import pickle
from deepface import DeepFace
from scipy.spatial.distance import cosine #Compute similarity/distance between vectors
import cv2
import logging #to keep logs of the process and errors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) #name identifies where logs come from

MODEL_NAME = "FaceNet" #model used for face recognition
DETECTOR = "opencv" #face detection
THRESHOLD = 0.40 #cut-off for cosine distance for two face embeddings to be considered a match

def extract_embedding(image_array: np.ndarray) -> np.ndarray | None: #-> return type hinting
    """
    Takes a BGR image (ndarray from opencv),
    detects the face, and returns a 128-d FaceNet embedding,
    returns None if no face is detected.
    """
    try:
        rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)

        #coverts face into mathematical signature
        result = DeepFace.represent(img_path = rgb, model_name =MODEL_NAME, detector_backend = DETECTOR,enforce_detection = True, align =True)

        embedding = np.array(result[0]["embedding"], dtype = np.float32)
        return embedding
    
    except ValueError as e:
        logger.warning(f"No face detected: {e}")
        return None
    except Exception as e:
        logger.error(f"Emnedding extraction failed: {e}")
        return None

def serialize_embedding(embedding: np.ndarray) -> bytes:
    """serialize numpy array to bytes for database storage"""
    return pickle.dump(embedding)

def deserialize_embedding(blob: bytes) -> np.ndarray:
    """deserialize bytes to numpy array"""
    return pickle.load(blob)

def compare_embedding(query: np.ndarray, stored :np.ndarray) ->float:
    """
    Returns cosine distance between two embeddings:
        0.0 -> Identical
        1.0 -> Different
    """
    return float(cosine(query,stored))

def find_match(query_embeddings: np.ndarray, student_embeddings: list[dict]) -> dict | None:
    """
    compare both of the embeddings and 
    return the best match if within the threshold <=0.40,
    else None
    """
    best_match = None
    best_distance = float("inf") #positive infinity

    for student in student_embeddings:
        stored_emb = deserialize_embedding(student["embedding"])
        distance = compare_embedding(query_embeddings, stored_emb)

        logger.info(f"Student {student["student_id"]} - distance: {distance:.4f}")

        if distance < best_distance:
            best_distance = distance
            best_match = student
    
    if best_distance <= THRESHOLD:
        confidence = round((1 - best_distance) *100, 2)
        return {
            "student_id": best_match["student_id"],
            "name" : best_match["name"],
            "distance" : round(best_distance, 4),
            "confidence" : confidence
            }
    
    logger.info(f"No match found, best distance was {best_distance:.4f}")
    return None
