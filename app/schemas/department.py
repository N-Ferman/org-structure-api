from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.common import normalize_required_text
from app.schemas.employee import EmployeeRead


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: int | None = Field(default=None, gt=0)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        return normalize_required_text(value, "name")


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = Field(default=None, gt=0)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        if value is None:
            raise ValueError("name cannot be null")

        return normalize_required_text(value, "name")


class DepartmentRead(BaseModel):
    id: int
    name: str
    parent_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentTree(BaseModel):
    department: DepartmentRead
    employees: list[EmployeeRead] = Field(default_factory=list)
    children: list["DepartmentTree"] = Field(default_factory=list)