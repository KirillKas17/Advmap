"""API endpoints для геозон."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.geozone import GeozoneCreate, GeozoneResponse, GeozoneVisitResponse
from app.services.geozone import GeozoneService

router = APIRouter(prefix="/geozone", tags=["geozone"])


@router.post("/", response_model=GeozoneResponse, status_code=status.HTTP_201_CREATED)
def create_geozone(
    geozone_data: GeozoneCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Создать новую геозону."""
    service = GeozoneService(db)
    try:
        geozone = service.create_geozone(
            name=geozone_data.name,
            polygon_coordinates=geozone_data.polygon_coordinates,
            geozone_type=geozone_data.geozone_type,
            description=geozone_data.description,
            company_id=current_user.company_id,
        )
        return geozone
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=List[GeozoneResponse])
def get_geozones(
    geozone_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить все активные геозоны."""
    service = GeozoneService(db)
    geozones = service.get_all_active_geozones(
        geozone_type=geozone_type,
        company_id=current_user.company_id,
    )
    return geozones


@router.get("/{geozone_id}", response_model=GeozoneResponse)
def get_geozone(
    geozone_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить геозону по ID."""
    service = GeozoneService(db)
    geozone = service.get_geozone_by_id(geozone_id)
    if not geozone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Геозона не найдена",
        )
    return geozone


@router.post("/{geozone_id}/check", response_model=dict)
def check_point_in_geozone(
    geozone_id: int,
    latitude: float,
    longitude: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Проверить, находится ли точка внутри геозоны."""
    service = GeozoneService(db)
    is_inside = service.check_point_in_geozone(latitude, longitude, geozone_id)

    if is_inside:
        # Создать запись о посещении
        visit = service.create_geozone_visit(
            user_id=current_user.id,
            geozone_id=geozone_id,
            company_id=current_user.company_id,
        )
        return {
            "is_inside": True,
            "visit_id": visit.id,
            "message": "Вы находитесь в геозоне!",
        }

    return {"is_inside": False, "message": "Вы не находитесь в геозоне"}


@router.post("/check-nearby", response_model=List[GeozoneResponse])
def check_nearby_geozones(
    latitude: float,
    longitude: float,
    geozone_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Найти все геозоны, содержащие данную точку."""
    service = GeozoneService(db)
    geozones = service.find_geozones_by_point(
        latitude=latitude,
        longitude=longitude,
        geozone_type=geozone_type,
        company_id=current_user.company_id,
    )

    # Создать записи о посещениях
    for geozone in geozones:
        service.create_geozone_visit(
            user_id=current_user.id,
            geozone_id=geozone.id,
            company_id=current_user.company_id,
        )

    return geozones


@router.get("/visits/my", response_model=List[GeozoneVisitResponse])
def get_my_visits(
    geozone_id: Optional[int] = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Получить мои посещения геозон."""
    service = GeozoneService(db)
    visits = service.get_user_geozone_visits(
        user_id=current_user.id,
        geozone_id=geozone_id,
        company_id=current_user.company_id,
        limit=limit,
    )
    return visits
