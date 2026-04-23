import re

from pydantic import BaseModel, Field, field_validator, model_validator


class AssistantResponse(BaseModel):
    main_response: str = Field(..., description="The main coaching response")
    follow_up_question: str | None = Field(
        None, description="Optional follow-up question"
    )

    model_config = {
        "extra": "ignore",
        "str_strip_whitespace": True,
        "validate_assignment": False,
    }

    @field_validator("main_response")
    def validate_main_response(cls, v):
        if not v or not isinstance(v, str):
            return (
                "I'm sorry, I couldn't generate a proper response. How can I help "
                "you further?"
            )
        return v.strip()

    @field_validator("follow_up_question")
    def validate_follow_up_question(cls, v):
        if not v or not isinstance(v, str):
            return None

        v = v.strip()
        if not v or "?" not in v:
            return None

        if v.count("?") > 1:
            v = v.split("?")[0] + "?"

        return v

    @model_validator(mode="after")
    def ensure_single_question(self) -> "AssistantResponse":
        """
        Enforces the "one question max" rule across the entire response.

        - A question in quotes is not a direct question.
        - If total real questions > 1, keeps only the first question and all
          non-question sentences.
        - Preserves statements that come after questions.
        """

        def count_direct_questions(text: str | None) -> int:
            """Counts questions not inside quotes."""
            if not text or "?" not in text:
                return 0

            # Simple regex to find questions marks not enclosed in quotes.
            # This looks for a '?' followed by an even number of quotes ahead.
            return len(re.findall(r'\?(?=(?:[^"]*"[^"]*")*[^"]*$)', text))

        def remove_excess_questions(text: str) -> str:
            """
            Remove extra questions while keeping the first question and all statements.
            """
            if not text or "?" not in text:
                return text

            sentences = re.split(r"([.!?])", text)
            result = []
            question_count = 0

            i = 0
            while i < len(sentences) - 1:
                sentence = sentences[i]
                punctuation = sentences[i + 1]

                is_question = (
                    punctuation == "?"
                    and len(
                        re.findall(
                            r'\?(?=(?:[^"]*"[^"]*")*[^"]*$)', sentence + punctuation
                        )
                    )
                    > 0
                )

                if is_question:
                    question_count += 1
                    if question_count == 1:
                        result.append(sentence + punctuation)
                else:
                    result.append(sentence + punctuation)

                i += 2

            if i < len(sentences):
                result.append(sentences[i])

            return "".join(result).strip()

        main_qs = count_direct_questions(self.main_response)
        follow_up_qs = count_direct_questions(self.follow_up_question)

        total_qs = main_qs + follow_up_qs

        if total_qs > 1:
            self.main_response = remove_excess_questions(self.main_response)
            if count_direct_questions(self.follow_up_question) > 0:
                self.follow_up_question = None
            return self

        return self

    def get_formatted_response(self) -> str:
        """
        Return formatted response with proper spacing between main response and
        follow-up question.
        """
        coaching_response = self.main_response.strip()

        if self.follow_up_question:
            coaching_response += f"\n{self.follow_up_question.strip()}"

        return coaching_response
