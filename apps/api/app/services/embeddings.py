import hashlib
import math
import re

from app.core.config import get_settings


class EmbeddingService:
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9\u0900-\u097F\s]+", " ", text.lower())
        return [token for token in cleaned.split() if token]

    @staticmethod
    def _normalize(vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    @staticmethod
    def embed_text(text: str) -> list[float]:
        settings = get_settings()
        dimensions = settings.embedding_dimensions
        vector = [0.0] * dimensions

        tokens = EmbeddingService._tokenize(text)
        if not tokens:
            return vector

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()

            bucket = int.from_bytes(digest[:4], "big") % dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            magnitude = 1.0 + ((digest[5] % 7) / 10.0)

            vector[bucket] += sign * magnitude

        return EmbeddingService._normalize(vector)

    @staticmethod
    def embed_query(query: str) -> list[float]:
        return EmbeddingService.embed_text(query)

    @staticmethod
    def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
        if not vector_a or not vector_b or len(vector_a) != len(vector_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = math.sqrt(sum(a * a for a in vector_a))
        norm_b = math.sqrt(sum(b * b for b in vector_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)