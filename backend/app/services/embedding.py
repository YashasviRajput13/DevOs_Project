"""
embedding.py
============
Lazy-loading EmbeddingService.

The SentenceTransformer model (~90 MB resident RAM for all-MiniLM-L6-v2)
is loaded ONLY on the first encode call, not at import or class
instantiation time.  A module-level singleton ensures the model is loaded
at most once per process lifetime.
"""
from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None  # type: ignore[var-annotated]  # loaded lazily


def _get_model():  # type: ignore[return]
    """Return the cached SentenceTransformer, loading it lazily on first call."""
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model '%s' (first use) …", _MODEL_NAME)
        # Deferred import: torch + sentence_transformers are NOT imported at
        # module load time, saving ~200-400 MB of startup RSS on Render.
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]  # noqa: PLC0415
        _model = SentenceTransformer(_MODEL_NAME)
        logger.info("SentenceTransformer model loaded.")
    return _model


class EmbeddingService:
    """
    Thin wrapper around the shared lazy-loaded SentenceTransformer singleton.
    Instantiating this class is cheap — the model is not touched until
    embed_text / embed_many is called.
    """

    def embed_text(self, text: str) -> list[float]:
        embedding = _get_model().encode(
            text,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def embed_many(self, texts: list[str]) -> np.ndarray:
        embeddings = _get_model().encode(
            texts,
            normalize_embeddings=True,
        )
        return np.asarray(embeddings, dtype=np.float32)