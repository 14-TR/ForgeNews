from dataclasses import dataclass

@dataclass(frozen=True)
class AWSConfig:
    REGION_NAME: str = "us-east-2"
    DB_SECRET_NAME: str = "dbConfig-2"
    OPENAI_SECRET_NAME: str = "open-ai"
    VIIRS_SECRET_NAME: str = "ViirsSecrets" 