import json
import os
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

DEMO_SUBJECTS = frozenset({"learner-red-1", "learner-red-2", "learner-blue-1"})


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    environment: Literal["local"] = "local"
    version: str = Field(default="0.1.0", pattern=r"^\d+\.\d+\.\d+$")
    demo_credentials: dict[str, str] = Field(
        default_factory=lambda: {
            "demo-learner-red": "learner-red-1",
            "demo-learner-red-second": "learner-red-2",
            "demo-learner-blue": "learner-blue-1",
        },
        repr=False,
        exclude=True,
    )

    @field_validator("demo_credentials")
    @classmethod
    def validate_credentials(cls, credentials: dict[str, str]) -> dict[str, str]:
        if not 1 <= len(credentials) <= 16:
            raise ValueError("Configure between one and sixteen local demo credentials")
        for credential, subject in credentials.items():
            if (
                not 8 <= len(credential) <= 128
                or not credential.isascii()
                or any(character.isspace() for character in credential)
                or subject not in DEMO_SUBJECTS
            ):
                raise ValueError("Invalid local demo credential configuration")
        return credentials

    @classmethod
    def from_environment(cls) -> "Settings":
        values: dict[str, object] = {
            "environment": os.getenv("LEARNING_ENVIRONMENT", "local"),
            "version": os.getenv("LEARNING_VERSION", "0.1.0"),
        }
        encoded = os.getenv("LEARNING_DEMO_CREDENTIALS_JSON", "")
        try:
            if encoded:
                values["demo_credentials"] = json.loads(encoded)
            return cls.model_validate(values)
        except (ValueError, ValidationError):
            raise ValueError("Invalid learning API configuration") from None
