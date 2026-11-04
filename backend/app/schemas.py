"""Request validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .catalog import CROPS, DISTRICTS, IRRIGATION_METHODS, LANGUAGES, SEASONS

MAX_CHAT_MESSAGE_CHARS = 1000
MAX_CHAT_MESSAGES = 11

CropId = Literal[tuple(CROPS)]
DistrictId = Literal[tuple(DISTRICTS)]
SeasonId = Literal[tuple(SEASONS)]
IrrigationId = Literal[tuple(IRRIGATION_METHODS)]
LanguageId = Literal[tuple(LANGUAGES)]


class FarmInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    crop: CropId
    district: DistrictId
    season: SeasonId
    field_acres: float = Field(gt=0, le=10_000)
    nitrogen: float = Field(ge=0, le=2_000)
    phosphorus: float = Field(ge=0, le=500)
    potassium: float = Field(ge=0, le=2_000)
    soil_ph: float | None = Field(default=None, ge=0, le=14)
    irrigation: IrrigationId = "rainfed"
    previous_crop: CropId | None = None
    avg_temp_c: float | None = Field(default=None, ge=-5, le=55)
    rainfall_mm: float | None = Field(default=None, ge=0, le=6_000)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_CHAT_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1, max_length=MAX_CHAT_MESSAGES)
    language: LanguageId = "en"
    farm: FarmInput | None = None

    @field_validator("messages")
    @classmethod
    def _alternates_from_user_to_user(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        expected = ["user" if index % 2 == 0 else "assistant" for index in range(len(value))]
        if [message.role for message in value] != expected or expected[-1] != "user":
            raise ValueError("messages must alternate, starting and ending with the user")
        return value
