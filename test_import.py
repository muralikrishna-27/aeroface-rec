import traceback
try:
    print("Importing deepface...")
    from deepface import DeepFace
    print("DeepFace OK")

    print("Importing face.embedding...")
    from face.embedding import generate_embedding
    print("All imports OK!")
except Exception as e:
    traceback.print_exc()
