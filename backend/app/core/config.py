from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "JARVIS"
    APP_ENV: str = "development"
    DATABASE_URL: str
    JWT_SECRET: str
    LOG_LEVEL: str = "INFO"
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 2000
    AI_TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    RECENT_MESSAGE_LIMIT: int = 20

    EMBEDDING_PROVIDER: str = "mock"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MEMORY_ENABLED: bool = True
    MEMORY_TOP_K: int = 5
    MEMORY_SIMILARITY_THRESHOLD: float = 0.70
    MAX_MEMORY_CONTEXT_TOKENS: int = 1500
    MEMORY_MIN_CONFIDENCE: float = 0.75
    MEMORY_MIN_IMPORTANCE: float = 0.50

    # Phase 5: Tools Configuration
    TOOLS_ENABLED: bool = True
    MAX_TOOL_CALLS_PER_REQUEST: int = 1
    
    HTTP_TOOL_ENABLED: bool = False
    HTTP_ALLOWED_DOMAINS: str = "" # Comma separated list of domains, e.g. "api.github.com,example.com"
    HTTP_TIMEOUT: int = 10
    HTTP_MAX_RESPONSE_SIZE: int = 1048576 # 1 MB

    # Phase 6: Agent Runtime Configuration
    MAX_AGENT_STEPS: int = 6
    MAX_AGENT_TOOL_CALLS: int = 6
    AGENT_TIMEOUT_SECONDS: int = 60
    MAX_AGENT_TOKEN_BUDGET: int = 8000
    
    # Phase 7: Web Research Configuration
    SEARCH_PROVIDER: str = "mock"
    SEARCH_API_KEY: str = ""
    MAX_RESEARCH_QUERIES: int = 3
    MAX_SOURCES_PER_QUERY: int = 5
    MAX_SOURCES_TO_FETCH: int = 8
    MAX_CONTENT_LENGTH_PER_SOURCE: int = 5000
    MAX_TOTAL_RESEARCH_CONTENT: int = 20000
    RESEARCH_TIMEOUT_SECONDS: int = 60
    
    # Phase 8: Document Intelligence Configuration
    FILE_STORAGE_PATH: str = "./data/uploads"
    MAX_FILE_SIZE_MB: int = 25
    MAX_FILES_PER_USER: int = 100
    MAX_DOCUMENT_PAGES: int = 300
    MAX_DOCUMENT_TEXT_LENGTH: int = 1000000
    MAX_SPREADSHEET_ROWS: int = 10000
    MAX_SPREADSHEET_CELLS: int = 100000
    MAX_PPTX_SLIDES: int = 200
    RAG_CHUNK_SIZE: int = 1200
    RAG_CHUNK_OVERLAP: int = 150
    RAG_TOP_K: int = 6
    RAG_SIMILARITY_THRESHOLD: float = 0.70
    
    # Phase 9: Vision & OCR Configuration
    OCR_PROVIDER: str = "mock"
    VISION_PROVIDER: str = "mock"
    MAX_IMAGE_SIZE_MB: int = 10
    MAX_IMAGE_WIDTH: int = 12000
    MAX_IMAGE_HEIGHT: int = 12000
    MAX_IMAGE_PIXELS: int = 40000000
    MAX_PDF_OCR_PAGES: int = 100
    PDF_RENDER_DPI: int = 150
    MAX_OCR_PAGE_PIXELS: int = 20000000
    MAX_OCR_PAGE_PIXELS: int = 20000000
    OCR_TIMEOUT_SECONDS: int = 30
    VISION_TIMEOUT_SECONDS: int = 30
    
    # Phase 10: Voice & Real-Time Configuration
    STT_PROVIDER: str = "mock"
    TTS_PROVIDER: str = "mock"
    STT_LANGUAGE: str = "th"
    TTS_VOICE: str = "alloy"
    TTS_SPEED: float = 1.0
    MAX_AUDIO_SIZE_MB: int = 25
    MAX_AUDIO_DURATION_SECONDS: int = 120
    STORE_VOICE_AUDIO: bool = False

    # Phase 12: External Integrations & Proactive Assistant
    ENCRYPTION_KEY: str = "" # base64 32 bytes
    INTEGRATIONS_ENABLED: bool = True
    GOOGLE_CALENDAR_ENABLED: bool = True
    GMAIL_ENABLED: bool = True
    LINE_ENABLED: bool = True
    TELEGRAM_ENABLED: bool = True
    WEBHOOKS_ENABLED: bool = True
    PROACTIVE_ASSISTANT_ENABLED: bool = True
    DAILY_BRIEFING_ENABLED: bool = True
    DAILY_BRIEFING_TIME: str = "08:00"

    # Phase 13: Agent Manager
    AGENT_MANAGER_ENABLED: bool = True
    MAX_SPECIALIST_AGENTS: int = 4
    MAX_AGENT_DEPTH: int = 2
    MAX_TOTAL_AGENT_STEPS: int = 12
    MAX_PARALLEL_AGENTS: int = 2
    MAX_AGENT_RUNTIME_SECONDS: int = 120
    CODING_AGENT_ENABLED: bool = False
    # Phase 14: Physical JARVIS / IoT & Smart Home
    IOT_MOCK_MODE: bool = True
    MQTT_ENABLED: bool = False
    MQTT_BROKER_HOST: str = ""
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: str = ""
    MQTT_PASSWORD: str = ""
    MQTT_TLS: bool = True
    MQTT_CLIENT_ID: str = "jarvis_backend"
    MQTT_KEEPALIVE: int = 60
    
    HOME_ASSISTANT_ENABLED: bool = False
    HOME_ASSISTANT_URL: str = ""
    HOME_ASSISTANT_TOKEN: str = ""
    
    MAX_IOT_COMMANDS_PER_MINUTE: int = 30
    MAX_IOT_COMMANDS_PER_DEVICE: int = 10
    MAX_SENSOR_EVENTS_PER_SECOND: int = 100
    MAX_AUTOMATION_DEPTH: int = 3
    MAX_AUTOMATION_EXECUTIONS_PER_MINUTE: int = 30
    IOT_REQUIRE_CONFIRMATION_DEFAULT: bool = False

    # Phase 15: Edge Processing & Hardware Deployment
    EDGE_ENABLED: bool = True
    EDGE_STT_ENABLED: bool = True
    EDGE_STT_PROVIDER: str = "mock"
    EDGE_STT_MODEL: str = "local_th"
    EDGE_STT_LANGUAGE: str = "th"
    EDGE_TTS_ENABLED: bool = True
    EDGE_TTS_PROVIDER: str = "mock"
    EDGE_TTS_MODEL: str = "local_th"
    EDGE_TTS_LANGUAGE: str = "th"
    STORE_EDGE_AUDIO: bool = False
    EDGE_MAX_STORAGE_MB: int = 512
    EDGE_EVENT_RETENTION_HOURS: int = 24
    EDGE_MAX_QUEUE_SIZE: int = 1000
    EDGE_AUTO_UPDATE: bool = False
    EDGE_VISION_ENABLED: bool = False
    EDGE_OFFLINE_MODE: bool = True
    EDGE_HEARTBEAT_INTERVAL: int = 30
    
    # Phase 16: JARVIS Intelligence Layer 2.0
    INTELLIGENCE_ENABLED: bool = True
    PROACTIVE_ASSISTANT_ENABLED: bool = True
    PROACTIVE_VOICE_ENABLED: bool = False
    ROUTINE_SUGGESTIONS_ENABLED: bool = True
    SMART_DAILY_BRIEFING_ENABLED: bool = True
    MAX_PROACTIVE_NOTIFICATIONS_PER_DAY: int = 10
    PROACTIVE_DEFAULT_COOLDOWN_MINUTES: int = 360
    WORLD_MODEL_CACHE_TTL_SECONDS: int = 60
    WORLD_MODEL_EVENT_RETENTION_DAYS: int = 14
    AUTO_LOW_RISK_ACTIONS: bool = False
    MAX_RECOMMENDATIONS_PER_REFRESH: int = 5

    # Phase 17: Learning & Personalization Engine
    PERSONALIZATION_ENABLED: bool = True
    BEHAVIOR_LEARNING_ENABLED: bool = True
    LEARNED_PREFERENCE_THRESHOLD: float = 0.75
    MIN_EVIDENCE_FOR_LEARNING: int = 5
    PREFERENCE_DECAY_ENABLED: bool = True
    PREFERENCE_DECAY_DAYS: int = 90
    PERSONALIZATION_SUGGESTIONS_ENABLED: bool = True
    MAX_BEHAVIOR_EVENTS_PER_DAY: int = 1000
    STORE_RAW_BEHAVIOR_CONTENT: bool = False
    EDGE_PERSONALIZATION_SYNC: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
