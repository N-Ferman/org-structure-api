from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import normalize_required_text


class EmployeeCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: date | None = None

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: object) -> str:
        return normalize_required_text(value, "full_name")

    @field_validator("position", mode="before")
    @classmethod
    def normalize_position(cls, value: object) -> str:
        return normalize_required_text(value, "position")


class EmployeeRead(BaseModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: date | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)