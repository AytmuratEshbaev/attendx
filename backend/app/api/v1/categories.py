"""Category management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user, get_db, require_role
from app.core.exceptions import DuplicateException, NotFoundException
from app.models.category import Category
from app.models.student import Student
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=SuccessResponse[list[CategoryResponse]])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
    parent_id: int | None = Query(None, description="Filter by parent category. Use 0 for top-level only."),
):
    """List categories. Optionally filter by parent_id (0 = top-level, None = all)."""
    stmt = select(Category)
    if parent_id == 0:
        stmt = stmt.where(Category.parent_id.is_(None))
    elif parent_id is not None:
        stmt = stmt.where(Category.parent_id == parent_id)
    stmt = stmt.order_by(Category.name)
    result = await db.execute(stmt)
    categories = result.scalars().all()
    return SuccessResponse(data=[CategoryResponse.model_validate(c) for c in categories])


@router.post("", response_model=SuccessResponse[CategoryResponse], status_code=201)
async def create_category(
    body: CategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Create a new category."""
    stmt = select(Category).where(
        Category.name == body.name,
        Category.parent_id == body.parent_id,
    )
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise DuplicateException(f"Category '{body.name}' already exists in this group.")
    category = Category(**body.model_dump())
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return SuccessResponse(data=CategoryResponse.model_validate(category))


@router.put("/{category_id}", response_model=SuccessResponse[CategoryResponse])
async def update_category(
    category_id: int,
    body: CategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Update a category."""
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundException(f"Category {category_id} not found.")

    update_data = body.model_dump(exclude_unset=True)

    new_name = update_data.get("name")
    new_parent = update_data.get("parent_id", category.parent_id)
    if new_name and (new_name != category.name or new_parent != category.parent_id):
        existing = await db.execute(
            select(Category).where(
                Category.name == new_name,
                Category.parent_id == new_parent,
                Category.id != category_id,
            )
        )
        if existing.scalar_one_or_none():
            raise DuplicateException(f"Category '{new_name}' already exists in this group.")
        # Sync class_name on students in this category
        await db.execute(
            Student.__table__.update()
            .where(Student.category_id == category_id)
            .values(class_name=new_name)
        )

    for key, value in update_data.items():
        setattr(category, key, value)

    await db.flush()
    await db.refresh(category)
    return SuccessResponse(data=CategoryResponse.model_validate(category))


@router.delete("/{category_id}", response_model=SuccessResponse[dict])
async def delete_category(
    category_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(require_role("admin"))],
):
    """Delete a category (students will have category unset)."""
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundException(f"Category {category_id} not found.")
    await db.delete(category)
    await db.flush()
    return SuccessResponse(data={"message": "Category deleted"})


@router.get("/{category_id}/stats", response_model=SuccessResponse[dict])
async def category_stats(
    category_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user: Annotated[User, Depends(get_current_active_user)],
):
    """Get student count for a category."""
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundException(f"Category {category_id} not found.")
    total = (await db.execute(
        select(func.count()).select_from(Student).where(Student.category_id == category_id)
    )).scalar() or 0
    active = (await db.execute(
        select(func.count()).select_from(Student).where(
            Student.category_id == category_id,
            Student.is_active.is_(True),
        )
    )).scalar() or 0
    children_count = (await db.execute(
        select(func.count()).select_from(Category).where(Category.parent_id == category_id)
    )).scalar() or 0
    return SuccessResponse(data={"total": total, "active": active, "children": children_count})
