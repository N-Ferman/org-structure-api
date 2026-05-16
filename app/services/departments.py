from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.department import Department
from app.models.employee import Employee
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.employee import EmployeeCreate


def get_department_or_404(
    db: Session,
    department_id: int,
) -> Department:
    department = db.get(Department, department_id)

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    return department


def find_department_by_parent_and_name(
    db: Session,
    *,
    parent_id: int | None,
    name: str,
    exclude_department_id: int | None = None,
) -> Department | None:
    query = select(Department).where(Department.name == name)

    if parent_id is None:
        query = query.where(Department.parent_id.is_(None))
    else:
        query = query.where(Department.parent_id == parent_id)

    if exclude_department_id is not None:
        query = query.where(Department.id != exclude_department_id)

    return db.scalar(query)


def ensure_parent_exists(
    db: Session,
    parent_id: int | None,
) -> None:
    if parent_id is None:
        return

    parent = db.get(Department, parent_id)

    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent department not found",
        )


def ensure_department_name_is_unique(
    db: Session,
    *,
    name: str,
    parent_id: int | None,
    exclude_department_id: int | None = None,
) -> None:
    existing_department = find_department_by_parent_and_name(
        db,
        parent_id=parent_id,
        name=name,
        exclude_department_id=exclude_department_id,
    )

    if existing_department is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name must be unique within the same parent",
        )


def ensure_no_cycle(
    db: Session,
    *,
    department_id: int,
    new_parent_id: int | None,
) -> None:
    if new_parent_id is None:
        return

    if department_id == new_parent_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department cannot be parent of itself",
        )

    current_parent_id = new_parent_id
    visited_ids: set[int] = set()

    while current_parent_id is not None:
        if current_parent_id in visited_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cycle detected in department tree",
            )

        visited_ids.add(current_parent_id)

        if current_parent_id == department_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot move department inside its own subtree",
            )

        current_parent_id = db.scalar(
            select(Department.parent_id).where(
                Department.id == current_parent_id
            )
        )


def commit_or_raise_conflict(
    db: Session,
    conflict_message: str,
) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_message,
        ) from exc


def create_department(
    db: Session,
    payload: DepartmentCreate,
) -> Department:
    ensure_parent_exists(db, payload.parent_id)

    ensure_department_name_is_unique(
        db,
        name=payload.name,
        parent_id=payload.parent_id,
    )

    department = Department(
        name=payload.name,
        parent_id=payload.parent_id,
    )

    db.add(department)

    commit_or_raise_conflict(
        db,
        "Department name must be unique within the same parent",
    )

    db.refresh(department)

    return department


def create_employee_in_department(
    db: Session,
    *,
    department_id: int,
    payload: EmployeeCreate,
) -> Employee:
    get_department_or_404(db, department_id)

    employee = Employee(
        department_id=department_id,
        full_name=payload.full_name,
        position=payload.position,
        hired_at=payload.hired_at,
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return employee


def build_department_tree(
    db: Session,
    *,
    department: Department,
    depth: int,
    include_employees: bool,
) -> dict:
    employees: list[Employee] = []

    if include_employees:
        employees = list(
            db.scalars(
                select(Employee)
                .where(Employee.department_id == department.id)
                .order_by(Employee.created_at.asc(), Employee.id.asc())
            )
        )

    children_nodes: list[dict] = []

    if depth > 0:
        children = list(
            db.scalars(
                select(Department)
                .where(Department.parent_id == department.id)
                .order_by(Department.name.asc(), Department.id.asc())
            )
        )

        children_nodes = [
            build_department_tree(
                db,
                department=child,
                depth=depth - 1,
                include_employees=include_employees,
            )
            for child in children
        ]

    return {
        "department": department,
        "employees": employees,
        "children": children_nodes,
    }


def get_department_tree(
    db: Session,
    *,
    department_id: int,
    depth: int,
    include_employees: bool,
) -> dict:
    department = get_department_or_404(db, department_id)

    return build_department_tree(
        db,
        department=department,
        depth=depth,
        include_employees=include_employees,
    )


def update_department(
    db: Session,
    *,
    department_id: int,
    payload: DepartmentUpdate,
) -> Department:
    department = get_department_or_404(db, department_id)

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        return department

    new_name = update_data.get("name", department.name)

    if "parent_id" in update_data:
        new_parent_id = update_data["parent_id"]

        ensure_parent_exists(db, new_parent_id)

        ensure_no_cycle(
            db,
            department_id=department.id,
            new_parent_id=new_parent_id,
        )
    else:
        new_parent_id = department.parent_id

    ensure_department_name_is_unique(
        db,
        name=new_name,
        parent_id=new_parent_id,
        exclude_department_id=department.id,
    )

    if "name" in update_data:
        department.name = update_data["name"]

    if "parent_id" in update_data:
        department.parent_id = update_data["parent_id"]

    db.add(department)

    commit_or_raise_conflict(
        db,
        "Department name must be unique within the same parent",
    )

    db.refresh(department)

    return department


def collect_subtree_department_ids(
    db: Session,
    *,
    root_department_id: int,
) -> list[int]:
    result: list[int] = []
    stack: list[int] = [root_department_id]
    visited_ids: set[int] = set()

    while stack:
        current_id = stack.pop()

        if current_id in visited_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cycle detected in department tree",
            )

        visited_ids.add(current_id)
        result.append(current_id)

        child_ids = list(
            db.scalars(
                select(Department.id).where(
                    Department.parent_id == current_id
                )
            )
        )

        stack.extend(child_ids)

    return result


def delete_department(
    db: Session,
    *,
    department_id: int,
    mode: str,
    reassign_to_department_id: int | None,
) -> None:
    department = get_department_or_404(db, department_id)

    if mode == "cascade":
        db.delete(department)
        db.commit()
        return

    if mode == "reassign":
        if reassign_to_department_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reassign_to_department_id is required when mode=reassign",
            )

        get_department_or_404(db, reassign_to_department_id)

        subtree_department_ids = collect_subtree_department_ids(
            db,
            root_department_id=department_id,
        )

        if reassign_to_department_id in subtree_department_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot reassign employees to department that will be deleted",
            )

        db.execute(
            update(Employee)
            .where(Employee.department_id.in_(subtree_department_ids))
            .values(department_id=reassign_to_department_id)
        )

        db.delete(department)
        db.commit()
        return

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="mode must be cascade or reassign",
    )