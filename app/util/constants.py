import os

from dotenv import load_dotenv

load_dotenv(override=True)

DB_PARAMS = {
    "host": os.getenv("POSTGRES_HOST", ""),
    "database": os.getenv("POSTGRES_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

KNOWLEDGE_DB_PARAMS = {
    "host": os.getenv("POSTGRES_HOST", ""),
    "database": os.getenv("KNOWLEDGE_DATABASE"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
}

AUTH0_CONFIG = {
    "domain": os.getenv("AUTH_AUTH0_DOMAIN"),
    "client_id": os.getenv("AUTH0_CLIENT_ID"),
    "client_secret": os.getenv("AUTH0_CLIENT_SECRET"),
}

AZURE_CONFIG = {
    "api_key": os.getenv("AZURE_API_KEY"),
    "azure_endpoint": os.getenv("AZURE_API_ENDPOINT"),
    "api_version": os.getenv("AZURE_API_VERSION"),
}

KNOWLEDGE_BASE_API_ENDPOINT = os.environ.get("KNOWLEDGE_BASE_API_ENDPOINT", "")
DOCUMENT_PROCESSING_TIMEOUT_SECONDS = int(
    os.environ.get("DOCUMENT_PROCESSING_TIMEOUT_SECONDS", "1800")
)
CHAT_STAGE_ENDPOINT = os.environ.get("CHAT_STAGE_ENDPOINT", "")
STUDIO_STAGE_ENDPOINT = os.environ.get("STUDIO_STAGE_ENDPOINT", "")
WHATSAPP_STAGE_ENDPOINT = os.environ.get("WHATSAPP_STAGE_ENDPOINT", "")

KNOWLEDGE_KEYWORDS = [
    "learning objectives",
    "learning outcomes",
    "learning methods",
    "learning strategies",
    "session agenda",
    "session content",
    "session topics",
    "session plan",
    "discussion topics",
    "discussion points",
    "what topics",
    "what will be discussed",
    "find out about",
    "tell me about",
    "explain how",
    "describe the",
    "coaching framework",
    "coaching methodology",
    "coaching approach",
    "coaching technique",
    "leadership development",
    "team development",
    "performance improvement",
    "feedback session",
    "assessment criteria",
    "evaluation process",
    "goal setting",
    "objective setting",
    "action plan",
    "development plan",
    # Speech/Communication improvement (coaching context)
    "improve articulation",
    "improve speech",
    "improve communication",
    "improve presentation",
    "develop voice",
    "voice training",
    "speech coaching",
    "presentation skills",
    "communication skills",
    "public speaking",
    "speaking skills",
    "vocal techniques",
    "pitch training",
    "speech improvement",
    "articulation exercises",
    "voice coaching",
    # Content/Topics
    "topics",
    "agenda",
    "discussion",
    "content",
    "subject",
    "theme",
    "material",
    # Learning/Methods (more specific)
    "framework",
    "methodology",
    "process",
    "approach",
    "technique",
    "strategy",
    "model",
    "method",
    "tool",
    "system",
    "practice",
    # Questions (knowledge-seeking)
    "what is",
    "what are",
    "what will",
    "how to",
    "how do",
    "how can",
    "why is",
    "when should",
    "where can",
    "who is",
    "which approach",
    # Information seeking
    "information about",
    "details on",
    "explain",
    "describe",
    "define",
    "understand",
    "know about",
    "find out",
    # Session types
    "workshop",
    "training session",
    "coaching session",
    "exercise",
    "activity",
    "program",
    "course",
    "curriculum",
    # Planning/Structure
    "plan for",
    "prepare for",
    "structure",
    "organize",
    "design",
    "develop",
    # Skills/Development
    "skill development",
    "growth plan",
    "improvement",
    "progress tracking",
    "competency",
    "capability",
    "mastery",
    # Goals/Outcomes
    "goal",
    "objective",
    "outcome",
    "result",
    "achievement",
    "target",
    "aim",
    # Challenges/Issues
    "challenge",
    "problem",
    "issue",
    "difficulty",
    "obstacle",
    "barrier",
    "struggle",
    "concern",
    # Feedback/Assessment
    "feedback",
    "assessment",
    "evaluation",
    "review",
    "reflection",
    "analysis",
    # Coaching specific
    "coaching",
    "mentoring",
    "leadership",
    "management",
    "team",
    "performance",
]

TONE_KEYWORDS = [
    # Voice/Style reference (not improvement)
    "tone of voice",
    "speaking style",
    "voice style",
    "manner of speaking",
    "way of speaking",
    "communication style",
    # Style reference queries
    "how do you speak",
    "how should I speak",
    "what tone should I use",
    "style examples",
    "tone examples",
    "voice examples",
    # Audio/Sound reference
    "how does it sound",
    "how should it sound",
    "audio examples",
    # Expression style reference
    "expression style",
    "phrasing style",
    "wording style",
    "delivery style",
]

DISPLAY_DATE_FORMAT = "%A, %B %d, %Y"
MESSAGE_DATE_FORMAT = "[Sent on %A, %B %d, %Y] "

API_KEY_NAME = "X-API-Key"
API_KEY = os.environ.get("API_KEY")

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
ALLOWED_HEADERS = ["Content-Type", "Authorization", "X-API-Key"]
