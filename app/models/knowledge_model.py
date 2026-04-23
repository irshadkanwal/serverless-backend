from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BuildKnowledgeResponse(BaseModel):
    status: str
    message: str


class DocumentData(BaseModel):
    """
    Document data model for storage operations.
    """

    id: str = Field(default="cbsk_doc_id", description="Document identifier")
    content: list[str] = Field(
        default_factory=list, description="Document content chunks"
    )
    pages_content: list[str] = Field(
        default_factory=list, description="Document pages content"
    )
    workspace: str = Field(default="cbs-knowledge", description="Workspace identifier")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )


class KnowledgeReference(BaseModel):
    type: Literal["full", "section", "pages"]
    document: str = Field(default="cbsk_doc_id", description="Document identifier")
    section: str | None = Field(default=None, description="Section in the document")
    pages: str | None = Field(default=None, description="Pages in the document")


class EnhancedReference(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    reference: KnowledgeReference = Field(
        description=(
            "The core reference information containing document, type, section, "
            "and pages"
        )
    )
    original_tag: str = Field(
        description="The complete original reference tag captured from the text"
    )
    ref_number: int = Field(
        default=0,
        description="The assigned reference number used for replacing tags in the text",
    )
    content: str | None = Field(
        default=None,
        description="The fetched document content associated with this reference",
    )


class KnowledgeSearchRequest(BaseModel):
    query: str
    workspace: str
    knowledge_ids: list[str] | None = None


class KnowledgeResponse(BaseModel):
    context: str | None
