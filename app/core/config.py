from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/org_structure"
    )

    test_database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5433/org_structure_test"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()