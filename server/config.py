from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Velaris Integration (primary mode) ---
    # Set velaris_url to enable Velaris mode; leave empty for standalone LLM mode
    velaris_url: str = ""  # e.g. "http://100.72.225.119:8400"
    velaris_poll_interval: float = 3.0  # seconds between /api/state polls

    # --- LLM — standalone mode (used when velaris_url is empty) ---
    llm_base_url: str = "http://localhost:1234/v1"
    llm_api_key: str = "lm-studio"
    llm_model: str = "gemma-3-12b-it"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7

    # Server
    host: str = "0.0.0.0"
    port: int = 8765

    # TTS — MiniMax Speech-02-HD (Velaris's voice)
    minimax_api_key: str = ""  # set to enable MiniMax TTS
    minimax_url: str = "https://api.minimaxi.chat"
    minimax_voice: str = "Wise_Woman"

    # TTS — Piper (local fallback)
    piper_model: str = "en_US-lessac-medium"
    piper_rate: int = 22050
    piper_enabled: bool = True

    # Avatar
    vrm_model_path: str = "models/default.vrm"

    # Tracking — "webxr" (PSVR2/SteamVR), "webcam" (MediaPipe), "manual"
    tracking_mode: str = "webxr"

    # Spatial
    default_distance: float = 1.5  # meters, conversational distance
    min_distance: float = 0.5
    max_distance: float = 4.0

    # Personality — preset name (standalone mode only; Velaris has SOUL.md)
    personality: str = "eve"

    # Memory (standalone mode only; Velaris has 23+ memory systems)
    memory_max_recent_turns: int = 30

    # Telemetry
    telemetry_enabled: bool = True
    telemetry_export_path: str = ""

    @property
    def velaris_mode(self) -> bool:
        """True if we're bridged to Velaris, False for standalone LLM mode."""
        return bool(self.velaris_url)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
