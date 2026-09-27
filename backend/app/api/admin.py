from fastapi import APIRouter, Depends
from app.models.user import User, UserRole
from app.api.deps import require_role

router = APIRouter()


@router.get("/test")
async def admin_test(
    admin_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Protected admin endpoint test."""
    return {
        "message": "Admin authorization verified successfully",
        "username": admin_user.username,
        "email": admin_user.email,
        "role": admin_user.role.value,
    }
