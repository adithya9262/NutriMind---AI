import math
import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_coach import AIUserMemory


class MemoryRetriever(ABC):
    @abstractmethod
    async def retrieve_top_k(self, session: AsyncSession, user_id: uuid.UUID, query_embedding: list[float], k: int = 5) -> Sequence[AIUserMemory]:
        """Retrieve the top k most relevant memories for the given user."""
        pass


class PythonRetriever(MemoryRetriever):
    """Fallback retriever that uses pure Python cosine similarity on JSONB arrays."""

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        return dot_product / (magnitude1 * magnitude2)

    async def retrieve_top_k(self, session: AsyncSession, user_id: uuid.UUID, query_embedding: list[float], k: int = 5) -> Sequence[AIUserMemory]:
        stmt = select(AIUserMemory).where(AIUserMemory.user_id == user_id)
        result = await session.execute(stmt)
        memories = result.scalars().all()

        # Calculate similarity and sort
        scored_memories = []
        for mem in memories:
            score = 0.0
            if mem.embedding:
                score = self._cosine_similarity(query_embedding, mem.embedding)
            # Factor in importance score slightly
            adjusted_score = score * 0.9 + (mem.importance_score / 10.0) * 0.1
            scored_memories.append((adjusted_score, mem))

        # Sort descending by score
        scored_memories.sort(key=lambda x: x[0], reverse=True)

        return [m[1] for m in scored_memories[:k]]


class PgVectorRetriever(MemoryRetriever):
    """Retriever that uses pgvector extension via SQLAlchemy."""

    async def retrieve_top_k(self, session: AsyncSession, user_id: uuid.UUID, query_embedding: list[float], k: int = 5) -> Sequence[AIUserMemory]:
        from sqlalchemy import text

        emb_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"

        stmt = text("""
            SELECT id, user_id, memory_type, content, importance_score, confidence, created_at, updated_at, last_used_at, usage_count, embedding
            FROM ai_user_memories
            WHERE user_id = :user_id AND embedding IS NOT NULL
            ORDER BY embedding <=> :embedding_str::vector
            LIMIT :k
        """)
        try:
            result = await session.execute(stmt, {"user_id": user_id, "embedding_str": emb_str, "k": k})
            rows = result.fetchall()

            memories = []
            for row in rows:
                mem = AIUserMemory(
                    id=row.id,
                    user_id=row.user_id,
                    memory_type=row.memory_type,
                    content=row.content,
                    importance_score=row.importance_score,
                    confidence=row.confidence,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    last_used_at=row.last_used_at,
                    usage_count=row.usage_count,
                    embedding=row.embedding
                )
                memories.append(mem)
            return memories
        except Exception:
            # Fallback to PythonRetriever if pgvector fails or is not installed
            return await PythonRetriever().retrieve_top_k(session, user_id, query_embedding, k)


def get_memory_retriever(use_pgvector: bool = False) -> MemoryRetriever:
    """Factory to get the configured memory retriever."""
    if use_pgvector:
        return PgVectorRetriever()
    return PythonRetriever()
