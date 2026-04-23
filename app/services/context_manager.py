import json
from contextlib import contextmanager
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

from app.util.constants import DB_PARAMS
from app.util.errors import DatabaseError
from app.util.helpers import get_logger, handle_exceptions

logger = get_logger(__name__)


class CoachingContextManager:
    @staticmethod
    def get_connection():
        """Get database connection using configuration parameters"""
        try:
            return psycopg2.connect(**DB_PARAMS)
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e!s}")
            raise DatabaseError(f"Failed to connect to database: {e!s}")

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """
        Context manager for database operations that handles connections and cursors

        Args:
            cursor_factory: Cursor factory to use (default: RealDictCursor for
                dict-like rows)

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
    def update_life_areas(self, chat_id: str, areas: list[dict]):
        """
        Updates the life areas discussed in a coaching session.

        This method specifically handles tracking which life areas are being discussed
        and when they were last updated. Think of it like updating the topics or themes
        of an ongoing conversation.

        Args:
            chat_id: The unique identifier for the chat session
            areas: A list of dictionaries containing information about life areas
                  Each area typically includes the area name, relevance score, and
                  context

        """
        areas_data = {"updated_at": datetime.now().isoformat(), "areas": areas}
        with self.get_cursor() as cursor:
            query = """
            UPDATE public."Chat"
            SET "lifeAreas" = %s
            WHERE "id" = %s
            """
            cursor.execute(query, (json.dumps(areas_data), chat_id))

    @handle_exceptions
    def save_session_summary(self, chat_id: str, summary: dict):
        """
        Saves or updates the comprehensive summary for a coaching session.

        This method handles storing the complete session summary, which includes
        insights, progress, action items, and other key takeaways from the conversation.
        Think of it like writing a detailed wrap-up note after an important meeting.

        Args:
            chat_id: The unique identifier for the chat session
            summary: A dictionary containing the structured session summary
                    This typically includes elements like key insights, action items,
                    progress indicators, and recommendations

        """
        if not summary:
            return

        with self.get_cursor() as cursor:
            query = """
            UPDATE public."Chat"
            SET "sessionSummary" = %s
            WHERE "id" = %s
            """
            cursor.execute(query, (json.dumps(summary), chat_id))

    @handle_exceptions
    def find_relevant_context(self, chat_id: str, assistant_id: str) -> dict:
        """
        Finds relevant previous sessions based on life areas and basic keyword matching.
        """
        with self.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT "lifeAreas"
                FROM public."Chat"
                WHERE "id" = %s
            """,
                (chat_id,),
            )

            current_session = cursor.fetchone()
            if not current_session or not current_session["lifeAreas"]:
                return {
                    "related_insights": [],
                    "relevant_actions": [],
                    "previous_progress": [],
                }

            current_areas = self._extract_areas(current_session["lifeAreas"])

            if not current_areas:
                return {
                    "related_insights": [],
                    "relevant_actions": [],
                    "previous_progress": [],
                }

            query = """
            SELECT
                c."id",
                c."created_at",
                c."sessionSummary",
                c."lifeAreas"
            FROM public."Chat" c
            WHERE c."assistantId" = %s
                AND c."id" != %s
                AND c."sessionSummary" IS NOT NULL
                AND c."lifeAreas" IS NOT NULL
            ORDER BY c."created_at" DESC
            LIMIT 5;
            """

            cursor.execute(query, (assistant_id, chat_id))
            sessions = cursor.fetchall()

            relevant_sessions = []
            for session in sessions:
                session_areas = self._extract_areas(session["lifeAreas"])
                if any(area in current_areas for area in session_areas):
                    relevant_sessions.append(session)

            return self._build_context_from_sessions(relevant_sessions[:3])

    def _build_context_from_sessions(self, sessions) -> dict:
        """Creates a structured context summary from related sessions."""
        context = {
            "related_insights": [],
            "relevant_actions": [],
            "previous_progress": [],
        }

        for session in sessions:
            try:
                summary = session["sessionSummary"]
                if isinstance(summary, str):
                    summary = json.loads(summary)

                if "overall_progress" in summary and "key_milestones" in summary:
                    context["related_insights"].append(
                        {
                            "date": session["created_at"].strftime("%Y-%m-%d %h:%m"),
                            "progress": summary.get("overall_progress", ""),
                            "key_milestones": summary.get("key_milestones", []),
                        }
                    )

                if "action_items" in summary:
                    context["relevant_actions"].extend(
                        [
                            {
                                "action": action,
                                "date": session["created_at"].strftime(
                                    "%Y-%m-%d %h:%m"
                                ),
                            }
                            for action in summary.get("action_items", [])
                        ]
                    )

                if "client_evolution" in summary:
                    evolution = summary.get("client_evolution", {})
                    context["previous_progress"].append(
                        {
                            "date": session["created_at"].strftime("%Y-%m-%d %h:%m"),
                            "emotional": evolution.get("emotional", ""),
                            "behavioral": evolution.get("behavioral", ""),
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing session summary: {e}")
                continue

        return context

    @handle_exceptions
    def _extract_areas(self, life_areas_data: dict) -> list[str]:
        """
        Extracts life area names from the stored life areas data structure.

        This method processes the life areas JSON data stored in the database and
        extracts a list of area names for comparison and matching purposes. It handles
        both the current data structure format and provides fallback handling for
        potential format variations.

        Args:
            life_areas_data: A dictionary containing the life areas data structure.

        Returns:
            List[str]: A list of unique area names extracted from the data structure.
                    Returns an empty list if no valid areas are found or if the
                    data structure is invalid.

        """
        if not life_areas_data:
            logger.debug("No life areas data provided")
            return []

        if isinstance(life_areas_data, str):
            try:
                life_areas_data = json.loads(life_areas_data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse life areas JSON: {e!s}")
                return []

        areas_list = life_areas_data.get("areas", [])

        if not isinstance(areas_list, list):
            logger.warning("Life areas data is not in expected list format")
            return []

        area_names = []
        for area_data in areas_list:
            if isinstance(area_data, dict) and "area" in area_data:
                area_name = area_data["area"]
                if isinstance(area_name, str) and area_name.strip():
                    area_names.append(area_name.lower().strip())
            else:
                logger.warning(f"Invalid area data format: {area_data}")

        return list(dict.fromkeys(area_names))

    def _extract_themes(self, summary: dict) -> list[str]:
        """
        Extracts key themes and phrases from the session summary.
        This helps find thematically related previous sessions.
        """
        themes = []
        if not summary:
            return themes

        for item in summary.get("action_items", []):
            themes.extend(self._extract_key_phrases(item))

        for rec in summary.get("recommendations", []):
            themes.extend(self._extract_key_phrases(rec))

        themes.extend(
            [milestone.lower() for milestone in summary.get("key_milestones", [])]
        )

        return list(set(themes))

    def _extract_key_phrases(self, text: str) -> list[str]:
        """
        Extracts key phrases from text for matching.
        """
        words = text.lower().split()
        return [
            " ".join(words[i : i + n])
            for n in [2, 3]
            for i in range(len(words) - n + 1)
        ]
