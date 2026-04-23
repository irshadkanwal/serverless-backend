from app.agents.analyzer.base_analyzer import BaseAnalyzer
from app.models.analyzer_model import AnalysisRequest, EmotionalAnalysisResult
from app.services.llm.llm_service import LLMService
from app.services.prompt_loader import PromptLoader
from app.services.prompt_manager import PromptManager


class EmotionalAnalyzer(BaseAnalyzer[EmotionalAnalysisResult]):
    """Analyzer for emotional aspects of conversation"""

    def __init__(self, llm_service: LLMService, prompt_manager: PromptManager):
        self.llm_service = llm_service
        self.prompt_manager = prompt_manager
        self.prompts = PromptLoader()

    async def analyze(self, request: AnalysisRequest) -> EmotionalAnalysisResult:
        previous_emotions = self._get_previous_emotions(request)

        system_message = {
            "role": "system",
            "content": self.prompts.get_prompt(
                "analysis", "emotional-analysis-system-message"
            ).render(
                previous_emotions=self._format_previous_emotions(previous_emotions),
                conversation_history=request.stage_history,
            ),
        }

        result = await self.llm_service.generate_json_response([system_message])

        return self._process_llm_response(result)

    def _get_previous_emotions(self, request: AnalysisRequest) -> list[dict]:
        """Extract previous emotional analyses from metadata"""
        return request.metadata.get("previous_emotions", []) if request.metadata else []

    def _format_previous_emotions(self, previous_emotions: list[dict]) -> str:
        """Format previous emotions for the prompt"""
        if not previous_emotions:
            return "No previous emotional analysis available."

        formatted = "Recent emotional states:\n"
        for emotion in previous_emotions[-3:]:
            formatted += (
                f"- {emotion['primary_emotion']} "
                f"(intensity: {emotion['emotion_intensity']:.2f})\n"
            )
            if emotion.get("emotional_shifts"):
                formatted += (
                    "  Shifts: "
                    + ", ".join(
                        f"{shift['from_emotion']} → {shift['to_emotion']}"
                        for shift in emotion["emotional_shifts"]
                    )
                    + "\n"
                )
        return formatted

    def _detect_patterns(
        self, current: dict, previous_emotions: list[dict]
    ) -> dict[str, list[str]]:
        """Detect recurring emotional patterns"""
        patterns = {}

        pattern_checks = {
            "intensity_spikes": self._check_intensity_spikes,
            "emotional_cycles": self._check_emotional_cycles,
        }

        for pattern_type, check_func in pattern_checks.items():
            if found_patterns := check_func(current, previous_emotions):
                patterns[pattern_type] = found_patterns

        return patterns

    def _check_intensity_spikes(self, current: dict, previous: list[dict]) -> list[str]:
        """Check for significant changes in emotional intensity"""
        spikes = []
        intensities = [e["emotion_intensity"] for e in previous] + [
            current["emotion_intensity"]
        ]

        for i in range(1, len(intensities)):
            change = intensities[i] - intensities[i - 1]
            if abs(change) >= 0.3:
                spikes.append(
                    f"{'Increase' if change > 0 else 'Decrease'} in emotional "
                    f"intensity: {abs(change):.2f}"
                )

        return spikes

    def _check_emotional_cycles(self, current: dict, previous: list[dict]) -> list[str]:
        """Detect recurring emotional patterns"""
        emotions = [e["primary_emotion"] for e in previous] + [
            current["primary_emotion"]
        ]
        cycles = []

        for length in range(2, min(4, len(emotions))):
            for i in range(len(emotions) - length * 2 + 1):
                sequence = emotions[i : i + length]
                if sequence == emotions[i + length : i + length * 2]:
                    cycles.append(f"Recurring pattern: {' → '.join(sequence)}")

        return cycles
