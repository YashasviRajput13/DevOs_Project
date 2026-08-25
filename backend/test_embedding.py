from app.services.embedding import EmbeddingService


service = EmbeddingService()

text = """
def hello_world():
    print("Hello DevOS")
"""

embedding = service.embed_text(text)

print("Embedding generated")
print("Dimensions:", len(embedding))
print("First 5 values:", embedding[:5])