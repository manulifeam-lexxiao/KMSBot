from __future__ import annotations

from abc import ABC, abstractmethod

from kms_bot.schemas.documents import ChunkRecord, CleanedDocument
from kms_bot.schemas.common import OperationAcceptedResponse
from kms_bot.schemas.index import IndexStatusResponse
from kms_bot.schemas.query import AnswerGeneratorInput, QueryRequest, QueryResponse, SearchResultHit
from kms_bot.schemas.sync import SyncStatusResponse


class SyncService(ABC):
    @abstractmethod
    async def trigger_full_sync(self) -> OperationAcceptedResponse:
        raise NotImplementedError

    @abstractmethod
    async def trigger_incremental_sync(self) -> OperationAcceptedResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_status(self) -> SyncStatusResponse:
        raise NotImplementedError


class ParseService(ABC):
    @abstractmethod
    async def parse_document(self, *, doc_id: str, title: str, raw_content: str) -> CleanedDocument:
        raise NotImplementedError


class ChunkService(ABC):
    @abstractmethod
    async def chunk_document(self, document: CleanedDocument) -> list[ChunkRecord]:
        raise NotImplementedError


class SearchService(ABC):
    @abstractmethod
    async def search(self, *, query: str, top_k: int) -> list[SearchResultHit]:
        raise NotImplementedError

    @abstractmethod
    async def rebuild_index(self) -> OperationAcceptedResponse:
        raise NotImplementedError

    @abstractmethod
    async def get_index_status(self) -> IndexStatusResponse:
        raise NotImplementedError


class AnswerService(ABC):
    @abstractmethod
    async def generate_answer(self, payload: AnswerGeneratorInput) -> str:
        raise NotImplementedError


class QueryService(ABC):
    @abstractmethod
    async def answer_query(self, request: QueryRequest) -> QueryResponse:
        raise NotImplementedError