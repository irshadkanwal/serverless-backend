from typing import Any

from mem0.memory.utils import sanitize_relationship_for_cypher


class MemoryFormatter:
    def format_memories(self, mems: list[dict[str, Any]]) -> list[str]:
        if not mems:
            return ["No memories found."]
        return [f"- {item['memory']}" for item in mems]

    def format_relations(self, rels: list[dict[str, Any]]) -> list[str]:
        if not rels:
            return ["No related memories found."]
        return [
            (
                f"- {r['source']} {self.sanitize_memory_text(r['relationship'])} "
                f"{r['destination']}"
            )
            for r in rels
        ]

    def sanitize_memory_text(self, text: str) -> str:
        return sanitize_relationship_for_cypher(text)
