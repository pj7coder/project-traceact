from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "TraceACT Forensic Intelligence Platform"
    API_V1_STR: str = "/api"
    
    # Blockchain APIs
    # Blockchain APIs & Explorers
    ETHERSCAN_API_KEY: str = ""
    ETHERSCAN_BASE_URL: str = "https://api.etherscan.io/v2/api"
    BLOCKSCOUT_BASE_URL: str = "https://eth.blockscout.com/api/v2"
    ETHEREUM_RPC_URL: str = "https://ethereum-rpc.publicnode.com"
    BLOCKSTREAM_API_URL: str = "https://blockstream.info/api"
    TRONGRID_API_KEY: str = ""
    TRONGRID_BASE_URL: str = "https://api.trongrid.io"
    TRONSCAN_API_KEY: str = ""
    TRONSCAN_BASE_URL: str = "https://apilist.tronscanapi.com/api"
    SOLANA_RPC_URL: str = "https://api.mainnet-beta.solana.com"
    
    # Request configuration
    API_TIMEOUT_SECONDS: float = 20.0
    MAX_TRANSACTIONS_FETCH: int = 50

    # Database Configuration (MongoDB)
    MONGODB_URI: str = "mongodb://localhost:27017/sih_forensics"
    MONGODB_DB_NAME: str = "sih_forensics"

    # Local LLM Configuration (Ollama)
    OLLAMA_HOST: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # Live Tracking & Email Notification Configuration
    LIVE_TRACKING_INTERVAL_MINUTES: int = 60
    EMAIL_NOTIFICATIONS_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "alerts@sahyog-lea.gov.in"
    ALERT_EMAIL_RECIPIENT: str = "investigator@cybercell.gov.in"

    # Law Enforcement Investigator Profile
    INVESTIGATOR_ID: str = "LEA-I4C-4092"
    INVESTIGATOR_NAME: str = "Cyber Forensics Officer"
    INVESTIGATOR_AGENCY: str = "Indian Cyber Crime Coordination Centre (I4C)"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

