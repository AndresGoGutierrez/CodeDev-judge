from typing import List, Dict
from pydantic import BaseModel, Field, validator
import os


class Settings(BaseModel):
    # Información del proyecto
    PROJECT_NAME: str = "Judge Microservice"
    API_V1_STR: str = "/api"

    # CORS
    CORS_ORIGINS: List[str] = Field(default=["*"])

    # Base de datos
    DATABASE_URL: str = "sqlite:///./judge.db"

    # Judge0
    JUDGE0_URL: str = "http://192.168.56.101:2358"
    JUDGE0_AUTH_TOKEN: str = ""

    AUTH_SERVICE_URL: str = "http://localhost:4000"


    # RabbitMQ o similar para comunicación entre microservicios
    MESSAGE_BROKER_URL: str = "amqp://guest:guest@rabbitmq:5672//"

    # Configuración del juez
    MAX_CODE_SIZE: int = 65536  # bytes

    # Mapeo de lenguajes a IDs de Judge0
    # Cambiado para usar IDs numéricos como claves
    LANGUAGE_MAP: Dict[int, int] = {
        1: 71,  # Python 3.8
        2: 54,  # C++ (GCC 9.2.0)
        3: 62,  # Java (OpenJDK 13.0.1)
        4: 63,  # JavaScript (Node.js 12.14.0)
        5: 50,  # C (GCC 9.2.0)
        6: 51,  # C# (Mono 6.6.0.161)
        7: 60,  # Go (1.13.5)
        8: 72,  # Ruby (2.7.0)
        9: 73,  # Rust (1.40.0)

        
        71: 71,  # Python 3.8
        54: 54,  # C++ (GCC 9.2.0)
        62: 62,  # Java (OpenJDK 13.0.1)
        63: 63,  # JavaScript (Node.js 12.14.0)
        50: 50,  # C (GCC 9.2.0)
        51: 51,  # C# (Mono 6.6.0.161)
        60: 60,  # Go (1.13.5)
        72: 72,  # Ruby (2.7.0)
        73: 73,  # Rust (1.40.0)
    }

    # Mapeo inverso para referencia (nombre del lenguaje a ID interno)
    LANGUAGE_NAME_TO_ID: Dict[str, int] = {
        "python": 1,
        "cpp": 2,
        "java": 3,
        "javascript": 4,
        "c": 5,
        "csharp": 6,
        "go": 7,
        "ruby": 8,
        "rust": 9,
    }

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    class Config:
        case_sensitive = True
        env_file = ".env"


# Instanciar las configuraciones
settings = Settings()
