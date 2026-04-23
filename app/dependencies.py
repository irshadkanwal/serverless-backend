from slowapi import Limiter
from slowapi.util import get_remote_address

from app.agents.analyzer.stage_transition_analyzer import StageTransitionAnalyzer
from app.agents.summary.session_summary_agent import SessionSummaryAgent
from app.agents.summary.stage_summary_agent import StageSummaryAgent
from app.services.coaching_service import CoachingService
from app.services.context_manager import CoachingContextManager
from app.services.db.file_db_service import FileDatabaseService
from app.services.db.knowledge_db_service import KnowledgeDatabaseService
from app.services.db.user_db_service import UserDataService
from app.services.knowledge_service import KnowledgeService
from app.services.llm.llm_service import LLMService
from app.services.notification_service import NotificationService
from app.services.prompt_manager import PromptManager
from app.services.summary_service import SummaryService


def get_llm_service():
    return LLMService()


def get_prompt_manager():
    return PromptManager()


def get_context_manager():
    return CoachingContextManager()


def get_coaching_service():
    llm_service = get_llm_service()
    prompt_manager = get_prompt_manager()
    return CoachingService(llm_service, prompt_manager)


def get_user_service():
    return UserDataService()


def get_summary_service():
    llm_service = get_llm_service()
    return SummaryService(llm_service)


def get_summary_agent():
    llm_service = get_llm_service()
    return SessionSummaryAgent(llm_service)


def get_stage_summary_agent():
    llm_service = get_llm_service()
    return StageSummaryAgent(llm_service)


def get_knowledge_service():
    return KnowledgeService()


def get_notification_service():
    return NotificationService()


def get_db_service():
    return FileDatabaseService()


def get_knowledge_db_service():
    return KnowledgeDatabaseService()


def get_stage_transition_analyzer():
    llm_service = get_llm_service()
    prompt_manager = get_prompt_manager()
    return StageTransitionAnalyzer(llm_service, prompt_manager)


def get_limiter():
    return Limiter(key_func=get_remote_address)
