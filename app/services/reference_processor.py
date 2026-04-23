import re

from app.models.knowledge_model import EnhancedReference, KnowledgeReference
from app.services.db.file_db_service import FileDatabaseService
from app.util.helpers import get_logger

logger = get_logger(__name__)


class ReferenceProcessor:
    """Service class for processing document references in prompts."""

    def __init__(self, db_service: FileDatabaseService):
        """
        Initialize the ReferenceProcessor.

        Args:
            db_service: Database service for fetching reference content

        """
        self.db_service = db_service

        self._reference_pattern = re.compile(
            r'<reference\s+type="([^"]+)"\s+document="([^"]+)"'
            r'(?:\s+section="([^"]+)")?(?:\s+pages="([^"]+)")?\s*/>'
        )
        self._reference_block_pattern = re.compile(r"\n\n# REFERENCES.*$", re.DOTALL)

    def extract_references(self, text: str) -> list[EnhancedReference]:
        """
        Extract references from text, capturing original tags and assigning numbers.

        Args:
            text: Text containing reference tags

        Returns:
            List of enhanced references with original tags and reference numbers

        """
        if not text:
            return []

        references = []
        for match in self._reference_pattern.finditer(text):
            original_tag = match.group(0)

            ref = KnowledgeReference(
                type=match.group(1),
                document=match.group(2),
                section=match.group(3) if match.group(3) else None,
                pages=match.group(4) if match.group(4) else None,
            )

            enhanced_ref = EnhancedReference(reference=ref, original_tag=original_tag)

            references.append(enhanced_ref)

        ref_map = {}
        for enhanced_ref in references:
            key = (
                enhanced_ref.reference.document,
                enhanced_ref.reference.type,
                enhanced_ref.reference.section,
                enhanced_ref.reference.pages,
            )
            if key not in ref_map:
                ref_map[key] = len(ref_map) + 1
            enhanced_ref.ref_number = ref_map[key]

        return references

    def replace_with_markers(
        self, text: str, references: list[EnhancedReference]
    ) -> str:
        """
        Replace reference tags with numbered markers using simple string replacement.

        Args:
            text: Text containing reference tags
            references: List of enhanced references with original tags

        Returns:
            Text with references replaced by numbered markers

        """
        if not text or not references:
            return text

        result = text

        for ref in references:
            result = result.replace(ref.original_tag, f"---ref {ref.ref_number}---")

        return result

    def clean_remaining_references(self, text: str) -> str:
        """
        Clean any remaining reference tags by doing one final regex replacement.
        This acts as a safety net for any tags that weren't processed earlier.

        Args:
            text: Text that might contain reference tags

        Returns:
            Cleaned text with any remaining references replaced

        """
        doc_maps = {}

        def replace_missed_tags(match):
            doc_name = match.group(2)
            if doc_name not in doc_maps:
                doc_maps[doc_name] = len(doc_maps) + 1
            return f"---ref {doc_maps[doc_name]}---"

        return self._reference_pattern.sub(replace_missed_tags, text)

    async def fetch_reference_content(
        self, user_id: str, reference: EnhancedReference
    ) -> str | None:
        """
        Fetch content for a specific reference using appropriate retrieval method.

        Args:
            user_id: The user's ID (used as workspace)
            reference: The enhanced reference to fetch content for
            rag_service: Optional LightRAG instance for section retrieval

        Returns:
            The reference content or a placeholder if not found

        """
        try:
            file_id = await self.db_service.get_file_id_by_name(
                workspace=user_id, file_name=reference.reference.document
            )

            if not file_id:
                logger.warning(
                    f"File ID not found for document: {reference.reference.document}"
                )
                return None

            if reference.reference.type == "pages" and reference.reference.pages:
                page_spec = reference.reference.pages

                content = await self.db_service.fetch_page_content(
                    workspace=user_id, file_id=file_id, page_spec=page_spec
                )
            elif reference.reference.type == "section" and reference.reference.section:
                # TODO: Implement section retrieval
                content = ""
            else:
                content = await self.db_service.fetch_full_file_content(
                    workspace=user_id, file_id=file_id
                )

            if not content:
                logger.warning(f"No content found for reference: {reference.reference}")
                return None

            reference.content = content
            return content
        except Exception as e:
            logger.error(f"Error fetching reference content: {e!s}")
            return None

    async def create_references_block(
        self, user_id: str, references: list[EnhancedReference]
    ) -> str | None:
        """
        Create a complete references block with content in a single step.

        Args:
            user_id: The user's ID
            references: List of enhanced references

        Returns:
            Complete references block with content or None if no valid references

        """
        if not references:
            return None

        refs_content = ""
        for ref in references:
            content = await self.fetch_reference_content(user_id, ref)
            if content:
                refs_content += f"\n---ref {ref.ref_number}---"
                refs_content += f"\n{content}"

        if refs_content:
            refs_section = "\n\n# REFERENCES"
            refs_section += (
                "\n// The following content is retrieved from knowledge documents "
                "to provide context:"
            )
            refs_section += refs_content
            return refs_section
        return None

    async def populate_references(
        self, user_id: str, references: list[EnhancedReference], prompt: str = ""
    ) -> str:
        """
        Replace reference placeholders with actual content.

        Args:
            user_id: The user's ID
            references: List of enhanced references
            prompt: The prompt with reference placeholders

        Returns:
            Prompt with references populated with actual content

        """
        populated_prompt = prompt

        refs_block = await self.create_references_block(user_id, references)

        if refs_block is None:
            return populated_prompt

        for ref in references:
            placeholder = f"{{reference_{ref.ref_number}}}"
            populated_prompt = populated_prompt.replace(
                placeholder, f"---ref {ref.ref_number}---"
            )

        if "# REFERENCES" in populated_prompt:
            populated_prompt = self._reference_block_pattern.sub(
                refs_block, populated_prompt
            )
        else:
            populated_prompt += refs_block

        return self.clean_remaining_references(populated_prompt)

    def process_references(self, text: str) -> tuple[str, list[EnhancedReference]]:
        """
        Complete reference processing pipeline: extract and replace.

        Args:
            text: The text containing reference tags

        Returns:
            Tuple of (processed text, list of enhanced references)

        """
        if not text:
            return text, []

        references = self.extract_references(text)
        processed_text = self.replace_with_markers(text, references)

        return processed_text, references
