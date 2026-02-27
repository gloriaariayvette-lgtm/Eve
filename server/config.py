from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM — OpenAI-compatible endpoint (LM Studio, ollama, vLLM, etc.)
    llm_base_url: str = "http://localhost:1234/v1"
    llm_api_key: str = "lm-studio"
    llm_model: str = "gemma-3-12b-it"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7

    # Server
    host: str = "0.0.0.0"
    port: int = 8765

    # TTS (Piper)
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

    # Phase 4: Personality — preset name: "eve", "spark", "sage", "whisper"
    personality: str = "eve"

    # Phase 4: Memory
    memory_max_recent_turns: int = 30

    # Phase 5: Telemetry
    telemetry_enabled: bool = True
    telemetry_export_path: str = ""  # empty = no file export, just in-memory

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
