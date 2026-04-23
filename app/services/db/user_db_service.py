from contextlib import contextmanager

import psycopg2
from psycopg2.extras import DictCursor

from app.models.analyzer_model import StageDetail
from app.models.llm_config_model import LLMConfig
from app.models.models import UserInput
from app.models.moderation_model import ModerationRule
from app.models.user_model import AICoachSetup, StageData
from app.util.config import settings
from app.util.errors import DatabaseError
from app.util.helpers import get_logger, handle_exceptions

logger = get_logger(__name__)


class UserDataService:
    def __init__(self):
        self.db_url = settings.DATABASE_URL

    def get_connection(self):
        return psycopg2.connect(self.db_url)

    @contextmanager
    def get_cursor(self, cursor_factory=DictCursor):
        """
        Context manager for database operations that handles connections and cursors

        Args:
            cursor_factory: Cursor factory to use (default: RealDictCursor
                for dict-like rows)

        Yields:
            psycopg2.cursor: Database cursor

        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation error: {e!s}")
            raise DatabaseError(f"Database operation failed: {e!s}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    @handle_exceptions
    def get_assistant_data(self, details: UserInput) -> AICoachSetup | None:
        """
        Fetch all data associated with a specific user ID.
        Returns None if user doesn't exist.
        """
        assistant_id = details.assistant_id
        stage_name = details.current_stage

        with (
            self.get_connection() as conn,
            conn.cursor(cursor_factory=DictCursor) as cur,
        ):
            cur.execute(
                """
                    SELECT ac.id, ac.instructions, ac.onboarding, \
                           ac."onboardingAnalyzer", a."userId"
                    FROM "Assistant" a
                    JOIN "AssistantConfiguration" ac ON a.id = ac."assistantId"
                    WHERE a.id = %s
                """,
                (assistant_id,),
            )
            assistant = cur.fetchone()
            if not assistant:
                logger.warning(f"Assistant not found for assistant_id: {assistant_id}")
                return None

            config_id = assistant["id"]

            cur.execute(
                """
                            SELECT name, instructions, analyzer,
                                (SELECT MIN("order") FROM "Stage" \
                                 WHERE "assistantConfigurationId" = %s) = \
                                "order" AS is_first
                            FROM "Stage"
                            WHERE "assistantConfigurationId" = %s AND name = %s
                            ORDER BY "order" ASC
                            """,
                (
                    config_id,
                    config_id,
                    stage_name,
                ),
            )
            current_stage = cur.fetchone()

            if not current_stage:
                cur.execute(
                    """
                                SELECT name, instructions, analyzer,
                                    (SELECT MIN("order") FROM "Stage" \
                                     WHERE "assistantConfigurationId" = %s) = \
                                    "order" AS is_first
                                FROM "Stage"
                                WHERE "assistantConfigurationId" = %s
                                ORDER BY "order" ASC
                                LIMIT 1
                                """,
                    (
                        config_id,
                        config_id,
                    ),
                )
                current_stage = cur.fetchone()

            cur.execute(
                """
                    SELECT model, temperature, top_p,
                           frequency_penalty, presence_penalty, created_at
                    FROM "ModelConfig"
                    WHERE "assistantConfigurationId" = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                (config_id,),
            )
            model_config = cur.fetchone()

            cur.execute(
                """
                            SELECT guidelines, "toneOfVoice", vector_db
                            FROM "Preference"
                            WHERE "userId" = %s
                        """,
                (assistant["userId"],),
            )
            user_preference = cur.fetchone()

            cur.execute(
                """
                    SELECT id
                    FROM "KnowledgeFile"
                    WHERE "user_id" = %s AND status = 'complete'
                """,
                (assistant["userId"],),
            )
            knowledge_files = cur.fetchall() if assistant["userId"] else []
            knowledge_ids = (
                [row["id"] for row in knowledge_files] if knowledge_files else None
            )

            try:
                if current_stage:
                    if current_stage.get("analyzer") is None:
                        current_stage["analyzer"] = ""
                    stage_data: StageData = StageData(**current_stage)
                else:
                    stage_data = None
            except Exception as e:
                logger.error(f"Error creating StageData: {e!s}")
                stage_data = None

            try:
                llm_config = LLMConfig(**model_config) if model_config else None
            except Exception as e:
                logger.error(f"Error creating LLMConfig: {e!s}")
                llm_config = None

            return AICoachSetup(
                userId=assistant["userId"],
                assistantConfigurationId=config_id,
                instructions=assistant["instructions"],
                onboarding=assistant["onboarding"],
                onboarding_analyzer=assistant["onboardingAnalyzer"],
                stage=stage_data,
                recurring=details.newMessage.recurring,
                llm_config=llm_config,
                knowledge_ids=knowledge_ids,
                guidelines=user_preference["guidelines"] if user_preference else None,
                tone=user_preference["toneOfVoice"] if user_preference else None,
                tone_examples=user_preference["vector_db"] if user_preference else None,
            )

    @handle_exceptions
    def get_assistant_data_by_id(
        self, assistant_id: str, recurring: bool
    ) -> AICoachSetup | None:
        """
        Fetch all data associated with a specific assistant ID.
        Returns None if user doesn't exist.
        """
        with (
            self.get_connection() as conn,
            conn.cursor(cursor_factory=DictCursor) as cur,
        ):
            cur.execute(
                """
                    SELECT ac."id", ac.instructions, ac.onboarding, a."userId"
                    FROM "Assistant" a
                    JOIN "AssistantConfiguration" ac ON a.id = ac."assistantId"
                    WHERE a.id = %s
                """,
                (assistant_id,),
            )
            assistant = cur.fetchone()

            if not assistant:
                return None

            config_id = assistant["id"]

            cur.execute(
                """
                            SELECT instructions, name
                            FROM "Stage"
                            WHERE "assistantConfigurationId" = %s
                            AND "order" = (SELECT MIN("order") FROM "Stage" \
                                             WHERE "assistantConfigurationId" = %s)
                            """,
                (
                    config_id,
                    config_id,
                ),
            )
            current_stage = cur.fetchone()

            cur.execute(
                """
                    SELECT model, temperature, top_p,
                           frequency_penalty, presence_penalty, created_at
                    FROM "ModelConfig"
                    WHERE "assistantConfigurationId" = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """,
                (config_id,),
            )
            model_config = cur.fetchone()

            cur.execute(
                """
                            SELECT guidelines, "toneOfVoice", vector_db
                            FROM "Preference"
                            WHERE "userId" = %s
                        """,
                (assistant["userId"],),
            )
            user_preference = cur.fetchone()

            cur.execute(
                """
                    SELECT id
                    FROM "KnowledgeFile"
                    WHERE "user_id" = %s AND status = 'complete'
                """,
                (assistant["userId"],),
            )
            knowledge_files = cur.fetchall() if assistant["userId"] else []
            knowledge_ids = (
                [row["id"] for row in knowledge_files] if knowledge_files else None
            )

            try:
                stage_data: StageData = StageData(
                    instructions=current_stage["instructions"],
                    name=current_stage["name"],
                    analyzer="",
                    is_first=True,
                )
            except Exception as e:
                logger.error(
                    f"Error creating StageData in get_assistant_data_by_id: {e!s}"
                )
                stage_data = None

            try:
                llm_config = LLMConfig(**model_config) if model_config else None
            except Exception as e:
                logger.error(f"Error creating LLMConfig: {e!s}")
                llm_config = None

            return AICoachSetup(
                userId=assistant["userId"],
                assistantConfigurationId=config_id,
                instructions=assistant["instructions"],
                onboarding=assistant["onboarding"],
                stage=stage_data,
                recurring=recurring,
                llm_config=llm_config,
                knowledge_ids=knowledge_ids,
                guidelines=user_preference["guidelines"] if user_preference else None,
                tone=user_preference["toneOfVoice"] if user_preference else None,
                tone_examples=user_preference["vector_db"] if user_preference else None,
            )

    @handle_exceptions
    def get_stage_with_next(
        self, assistant_id: str, stage_name: str
    ) -> StageDetail | None:
        """
        Fetch stage details including instructions, analyzer, and next stage name.

        Args:
            assistant_id: The ID of the coaching assistant
            stage_name: The name of the current stage

        Returns:
            StageDetail: Pydantic model containing current stage details and
                next stage name.
                        If this is the last stage, next_stage_name will be None.
            None: If no stage is found

        Raises:
            DatabaseError: If there's an error executing the query

        """
        with self.get_cursor() as cursor:
            query = """
                WITH ordered_stages AS (
                    SELECT
                        s.id,
                        s.name,
                        s.instructions,
                        s.analyzer,
                        s."order",
                        LEAD(s.name) OVER (ORDER BY s."order") as next_stage_name,
                        ROW_NUMBER() OVER (ORDER BY s."order" DESC) as reverse_order
                    FROM public."Stage" s
                    JOIN "AssistantConfiguration" ac \
                         ON s."assistantConfigurationId" = ac.id
                    JOIN "Assistant" a ON ac."assistantId" = a.id
                    WHERE a.id = %s
                ),
                stage_with_next AS (
                    SELECT
                        id,
                        name,
                        instructions,
                        analyzer,
                        "order",
                        CASE
                            WHEN reverse_order = 1 THEN NULL  -- Last stage
                            ELSE next_stage_name
                        END as next_stage_name
                    FROM ordered_stages
                )
                SELECT *
                FROM stage_with_next
                WHERE LOWER(name) = LOWER(%s);
            """

            try:
                cursor.execute(query, (assistant_id, stage_name))
                result = cursor.fetchone()

                if not result:
                    logger.warning(
                        f"No stage found for assistant {assistant_id} "
                        f"with name {stage_name}"
                    )
                    return None

                return StageDetail(
                    id=result["id"],
                    name=result["name"],
                    instructions=result["instructions"],
                    analyzer=result["analyzer"],
                    order=result["order"],
                    next_stage_name=result["next_stage_name"],
                )

            except Exception as e:
                logger.error(f"Error fetching stage data: {e!s}")
                raise DatabaseError(f"Failed to fetch stage data: {e!s}")

    def get_user_model_configs(self, assistant_id: str) -> list[dict]:
        """Fetch only the model configurations for a specific user"""
        with (
            self.get_connection() as conn,
            conn.cursor(cursor_factory=DictCursor) as cur,
        ):
            cur.execute(
                """
                    SELECT mc.id, mc.model, mc.temperature, mc.top_p,
                        mc.frequency_penalty, mc.presence_penalty, mc.created_at
                    FROM "ModelConfig" mc
                    JOIN "AssistantConfiguration" ac \
                         ON mc."assistantConfigurationId" = ac.id
                    JOIN "Assistant" a ON ac."assistantId" = a.id
                    WHERE a.id = %s
                    ORDER BY mc.created_at DESC
                """,
                (assistant_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    @handle_exceptions
    def get_stage_sequence(self, assistant_id: str) -> list[str]:
        """
        Return the ordered list of stage names for the assistant.
        """
        sql = """
            SELECT s.name
            FROM "Stage" s
            JOIN "AssistantConfiguration" ac ON s."assistantConfigurationId" = ac.id
            JOIN "Assistant" a ON ac."assistantId" = a.id
            WHERE a.id = %s
            ORDER BY s."order" ASC
        """
        with self.get_cursor() as cur:
            cur.execute(sql, (assistant_id,))
            rows = cur.fetchall()
            return [r["name"] for r in rows]

    def get_latest_model_config(self, assistant_id: str) -> dict | None:
        """Fetch the most recent model configuration for a user"""
        with (
            self.get_connection() as conn,
            conn.cursor(cursor_factory=DictCursor) as cur,
        ):
            cur.execute(
                """
                    SELECT mc.id, mc.model, mc.temperature, mc.top_p,
                        mc.frequency_penalty, mc.presence_penalty, mc.created_at
                    FROM "ModelConfig" mc
                    JOIN "AssistantConfiguration" ac \
                         ON mc."assistantConfigurationId" = ac.id
                    JOIN "Assistant" a ON ac."assistantId" = a.id
                    WHERE a.id = %s
                    ORDER BY mc.created_at DESC
                    LIMIT 1
                """,
                (assistant_id,),
            )
            result = cur.fetchone()
            return dict(result) if result else None

    @handle_exceptions
    def get_user_moderation(self, assistant_id: str) -> list[ModerationRule]:
        """Fetch moderation rules for user"""
        with self.get_cursor() as cursor:
            query = """
                SELECT
                    mr.id,
                    mr.name,
                    mr.allow_category,
                    mr.input_score,
                    mr.output_score,
                    mr.response_examples
                FROM "ModerationRule" mr
                JOIN "AssistantConfiguration" ac \
                     ON mr."assistantConfigurationId" = ac.id
                JOIN "Assistant" a ON ac."assistantId" = a.id
                WHERE a.id = %s
            """
            cursor.execute(query, (assistant_id,))
            return [ModerationRule(**row) for row in cursor.fetchall()]
