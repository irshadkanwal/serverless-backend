from datetime import datetime
from typing import Any

import aiohttp

from app.models.analyzer_model import StageTransitionResult
from app.models.knowledge_model import DocumentData
from app.models.models import UserInput
from app.util.constants import (
    CHAT_STAGE_ENDPOINT,
    KNOWLEDGE_BASE_API_ENDPOINT,
    STUDIO_STAGE_ENDPOINT,
    WHATSAPP_STAGE_ENDPOINT,
)
from app.util.helpers import get_logger, handle_exceptions


class NotificationService:
    """
    Service for sending notifications to the backend API
    about the status of file processing and chat stage transitions.
    """

    def __init__(self):
        """
        Initialize the notification service.

        Args:
            knowledge_endpoint: Optional override for the knowledge API endpoint URL
            chat_stage_endpoint: Optional override for the chat stage endpoint URL

        """
        self.logger = get_logger("notification_service")

    async def notify_processing_complete(
        self, document: DocumentData, status: str = "complete"
    ) -> bool:
        """
        Notify the backend API that file processing is complete.

        Args:
            document: The document data that was processed

        Returns:
            True if notification was successful, False otherwise

        """
        try:
            payload = {
                "user_id": document.workspace,
                "file_id": document.id,
                "status": status,
            }

            return await self._send_notification(KNOWLEDGE_BASE_API_ENDPOINT, payload)

        except Exception as e:
            self.logger.error(f"Error sending processing notification: {e!s}")
            return False

    @handle_exceptions
    async def notify_stage_transition(
        self,
        stage_transition: StageTransitionResult,
        user_input: UserInput,
        initial_stage: str,
    ):
        """
        Notify the backend API about a chat stage transition.

        Args:
            stage_transition: The stage transition analysis result
            user_input: The user input containing chat and message details
            initial_stage: The initial stage before the transition

        """
        match user_input.app:
            case "studio":
                await self._send_studio_transition(stage_transition, user_input.chat_id)
            case "coachbot":
                await self._send_coachbot_transition(stage_transition, user_input)
            case "whatsapp":
                await self._send_whatsapp_transition(
                    stage_transition, user_input, initial_stage
                )

    async def _send_notification(self, endpoint: str, payload: dict[str, Any]) -> bool:
        """
        Send a notification to the specified endpoint.

        Args:
            endpoint: The API endpoint URL
            payload: The payload to send

        Returns:
            True if notification was successful, False otherwise

        """
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            connector = aiohttp.TCPConnector(ssl=False)
            async with (
                aiohttp.ClientSession(timeout=timeout, connector=connector) as session,
                session.post(
                    endpoint, headers={"Content-Type": "application/json"}, json=payload
                ) as response,
            ):
                if response.status >= 200 and response.status < 300:
                    return True
                response_text = await response.text()
                self.logger.error(
                    f"Failed to send notification. Status: {response.status}, "
                    f"Response: {response_text}, Endpoint: {endpoint}, "
                    f"Payload: {payload}"
                )
                return False
        except aiohttp.ClientConnectionError as e:
            self.logger.error(
                f"Connection error to {endpoint}: {e!s} - {datetime.now().isoformat()}"
            )
            return False
        except Exception as e:
            self.logger.error(
                f"Error sending notification: {e!s} - {datetime.now().isoformat()}"
            )
            return False

    @handle_exceptions
    async def _send_studio_transition(
        self, stage_transition: StageTransitionResult, chat_id: str
    ):
        """
        Notify the backend API about a chat stage transition.

        Args:
            stage_transition: The stage transition result

        Returns:
            True if notification was successful, False otherwise

        """
        endpoint = f"{STUDIO_STAGE_ENDPOINT}{chat_id}/stage-analysis"
        await self._send_notification(endpoint, stage_transition.model_dump())

    @handle_exceptions
    async def _send_coachbot_transition(
        self, stage_transition: StageTransitionResult, user_input: UserInput
    ):
        """
        Notify the backend API about a chat stage transition.

        Args:
            user_id: The ID of the user
            chat_id: The ID of the chat session
            stage: The new stage

        Returns:
            True if notification was successful, False otherwise

        """
        payload = {
            "userId": user_input.user_id,
            "id": user_input.chat_id,
            "stageAnalysis": stage_transition.model_dump(),
        }

        await self._send_notification(CHAT_STAGE_ENDPOINT, payload)

    @handle_exceptions
    async def _send_whatsapp_transition(
        self,
        stage_transition: StageTransitionResult,
        user_input: UserInput,
        initial_stage: str,
    ):
        """
        Notify the backend API about a chat stage transition.

        Args:
            stage_transition: The stage transition result
            user_input: The user input containing chat and message details
            initial_stage: The initial stage before the transition

        Returns:
            True if notification was successful, False otherwise

        """
        payload = {
            "chat_id": user_input.chat_id,
            "initial_stage": initial_stage,
            "result": stage_transition.model_dump(),
        }

        await self._send_notification(WHATSAPP_STAGE_ENDPOINT, payload)
