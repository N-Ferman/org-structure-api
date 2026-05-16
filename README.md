# Organization Structure API

API для управления организационной структурой компании: подразделения, сотрудники и дерево подразделений.

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL 16
- Alembic
- Docker Compose
- pytest

---

# Запуск проекта

## 1. Клонировать репозиторий

```bash
git clone <repository_url>
cd org-structure-api
```

## 2. Создать `.env`

```bash
cp .env.example .env
```

## 3. Запустить проект

```bash
docker compose up --build
```

API будет доступно:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

Healthcheck:

```bash
curl http://localhost:8000/health
```

---

# Миграции

## Создать миграцию

```bash
docker compose run --rm api alembic revision --autogenerate -m "migration name"
```

## Применить миграции

```bash
docker compose run --rm api alembic upgrade head
```

---

# Тесты

```bash
docker compose exec api pytest -q
```

---

# Структура проекта

```text
app/
├── api/        # FastAPI endpoints
├── core/       # settings
├── db/         # database/session
├── models/     # SQLAlchemy models
├── schemas/    # Pydantic schemas
├── services/   # business logic
└── main.py
```

---

# Модели

## Department

- id
- name
- parent_id
- created_at

Связи:

- Department 1—N Employee
- Department 1—N Department

## Employee

- id
- department_id
- full_name
- position
- hired_at
- created_at

---

# API

## Создать подразделение

```http
POST /departments/
```

## Создать сотрудника

```http
POST /departments/{department_id}/employees/
```

## Получить подразделение с деревом

```http
GET /departments/{department_id}?depth=1&include_employees=true
```

## Обновить подразделение

```http
PATCH /departments/{department_id}
```

## Удалить подразделение

```http
DELETE /departments/{department_id}?mode=cascade
```

или

```http
DELETE /departments/{department_id}?mode=reassign&reassign_to_department_id=1
```

---

# Бизнес-правила

- Нельзя создать сотрудника в несуществующем подразделении
- Название подразделения уникально внутри одного parent
- Пробелы по краям строк обрезаются
- Нельзя сделать подразделение родителем самого себя
- Нельзя создать цикл в дереве
- `depth` ограничен значениями 0..5
- Поддерживаются режимы удаления:
  - `cascade`
  - `reassign`

---

# Тесты

Реализованы тесты для:

- создания подразделений
- создания сотрудников
- получения дерева
- проверки duplicate name
- проверки циклов
- удаления подразделений

