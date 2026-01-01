"""API endpoints для верификации."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.verification import VerificationService
from app.schemas.verification import (
    VerificationRequestResponse,
    VerificationRequestCreate,
    UserStatusResponse,
)

router = APIRouter(prefix="/verification", tags=["verification"])
logger = logging.getLogger(__name__)


@router.post("/request", response_model=VerificationRequestResponse, status_code=status.HTTP_201_CREATED)
def request_verification(
    request_data: VerificationRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Запросить верификацию."""
    service = VerificationService(db)
    try:
        request = service.request_verification(
            user_id=current_user.id,
            requested_status=request_data.requested_status,
            evidence_data=request_data.evidence_data,
            company_id=current_user.company_id,
        )
        return request
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/status", response_model=UserStatusResponse)
def get_user_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить статус пользователя."""
    service = VerificationService(db)
    status_obj = service._get_user_status(current_user.id)
    return {"status": status_obj.value if status_obj else "newbie"}


@router.get("/requests/my", response_model=List[VerificationRequestResponse])
def get_my_verification_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мои заявки на верификацию."""
    from app.models.verification import VerificationRequest
    
    requests = (
        db.query(VerificationRequest)
        .filter(VerificationRequest.user_id == current_user.id)
    )
    if current_user.company_id is not None:
        requests = requests.filter(VerificationRequest.company_id == current_user.company_id)
    
    return requests.order_by(VerificationRequest.created_at.desc()).all()
