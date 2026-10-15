"""  
Creating local text embeddings for schema retrieval.
"""


from sentence_transformers import SentenceTransformer


# Creates 384-dimensional vectors.
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

embedding_model = None

def get_embedding_model():
    """ Loading the embedding model only when it is first needed."""

    global embedding_model

    if embedding_model is None:
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    return embedding_model


def create_embedding(text):
    """ Converting text into a 384-dimensional vector using the embedding model."""

    model = get_embedding_model()

    return model.encode(text).tolist()


if __name__ == "__main__":
    # Example usage
    example_text = "Which Products have the highest price?"

    vector = create_embedding(example_text)

    print("Model:", EMBEDDING_MODEL_NAME)
    print("Vector dimensions:", len(vector))
    print("First 5 values:", vector[:5])
