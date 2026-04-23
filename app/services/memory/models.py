from pydantic import BaseModel


class MemoryAddRequest(BaseModel):
    text: str
    user_id: str
    category: str | None = "user_memory"


class MemorySearchRequest(BaseModel):
    query: str
    user_id: str
    category: str | None = "user_memory"


class MemoryResponse(BaseModel):
    results: list[str]
    relations: list[str] | None = []


class DeleteRequest(BaseModel):
    user_id: str


class AllMemoriesRequest(BaseModel):
    user_id: str
