from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentTree,
    DepartmentUpdate,
)
from app.schemas.employee import EmployeeCreate, EmployeeRead
from app.services.departments import (
    create_department,
    create_employee_in_department,
    delete_department,
    get_department_tree,
    update_department,
)


router = APIRouter(
    prefix="/departments",
    tags=["departments"],
)


@router.post(
    "/",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_department_endpoint(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
) -> DepartmentRead:
    return create_department(db, payload)


@router.post(
    "/{department_id}/employees/",
    response_model=EmployeeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_employee_endpoint(
    payload: EmployeeCreate,
    department_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> EmployeeRead:
    return create_employee_in_department(
        db,
        department_id=department_id,
        payload=payload,
    )


@router.get(
    "/{department_id}",
    response_model=DepartmentTree,
)
def get_department_endpoint(
    department_id: int = Path(..., gt=0),
    depth: int = Query(default=1, ge=0, le=5),
    include_employees: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> DepartmentTree:
    return get_department_tree(
        db,
        department_id=department_id,
        depth=depth,
        include_employees=include_employees,
    )


@router.patch(
    "/{department_id}",
    response_model=DepartmentRead,
)
def update_department_endpoint(
    payload: DepartmentUpdate,
    department_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
) -> DepartmentRead:
    return update_department(
        db,
        department_id=department_id,
        payload=payload,
    )


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_department_endpoint(
    department_id: int = Path(..., gt=0),
    mode: Literal["cascade", "reassign"] = Query(...),
    reassign_to_department_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
) -> Response:
    delete_department(
        db,
        department_id=department_id,
        mode=mode,
        reassign_to_department_id=reassign_to_department_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)