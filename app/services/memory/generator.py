from app.models.models import UserInput
from app.services.prompt_loader import PromptLoader


class MemoryGenerator:
    def __init__(self):
        self.prompts = PromptLoader()

    def generate_memory_items(
        self, user_input: UserInput, coach_response: str
    ) -> list[dict[str, str]]:
        memories = []

        if len(user_input.history) > 0:
            coach_message = user_input.history[-1].content
            user_message = user_input.newMessage.content

            coach_memory = self.prompts.get_prompt(
                "memory", "extract-coach-message-memory"
            ).render(coach_response=coach_response)
            if coach_memory and coach_memory.strip():
                memories.append({"text": coach_memory, "category": "coach_questions"})

            memory_bundle = self.prompts.get_prompt(
                "memory", "extract-user-memory"
            ).render(
                coach_message=coach_message,
                user_message=user_message,
                coach_response=coach_response,
            )
            if memory_bundle and memory_bundle.strip():
                memories.append({"text": memory_bundle, "category": "user_memory"})
        else:
            initial_memory = (
                f"Initial coaching session - User message: "
                f"{user_input.newMessage.content}, Coach response: {coach_response}"
            )
            if initial_memory and initial_memory.strip():
                memories.append({"text": initial_memory, "category": "user_memory"})

        return memories
