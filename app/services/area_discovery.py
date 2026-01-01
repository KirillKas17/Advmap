"""Сервис открытия областей (Area POI Discovery)."""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point, Polygon, LineString
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.geozone import Geozone, AreaDiscovery
from app.models.location import LocationPoint, LocationSession

settings = get_settings()
logger = logging.getLogger(__name__)


class DiscoveryStatus(str, Enum):
    """Статус открытия области."""
    DISCOVERED = "discovered"  # 0-30%
    EXPLORED = "explored"  # 30-70%
    COMPLETED = "completed"  # 70%+


class TransitModeThreshold:
    """Пороги для Transit Mode."""
    SPEED_KMH = 25.0  # 25 км/ч
    SPEED_MS = SPEED_KMH / 3.6  # ~6.94 м/с


class AreaDiscoveryService:
    """Сервис для обработки открытия Area POI."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db
        self.min_area_square_meters = 500000  # 0.5 км²
        self.min_time_seconds = 30  # Минимум 30 секунд в зоне
        self.min_area_percent = 10.0  # Минимум 10% площади для открытия

    def process_location_trajectory(
        self,
        user_id: int,
        location_points: List[LocationPoint],
        company_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Обработать траекторию пользователя и открыть пересекающиеся Area POI.
        
        Args:
            user_id: ID пользователя
            location_points: Список точек геолокации
            company_id: ID компании (для мультитенантности)
            
        Returns:
            Список событий открытия областей
        """
        if not location_points:
            return []

        events = []
        
        # Определяем режим движения (Transit Mode)
        is_transit_mode = self._is_transit_mode(location_points)
        
        # Строим LineString из траектории
        trajectory = self._build_trajectory(location_points)
        if not trajectory or trajectory.length == 0:
            return events

        # Находим все Area POI, которые пересекаются с траекторией
        area_geozones = self._find_intersecting_area_poi(trajectory, is_transit_mode, company_id)
        
        for geozone in area_geozones:
            try:
                # Получаем или создаём запись о открытии
                discovery = self._get_or_create_discovery(user_id, geozone.id, company_id)
                
                # Вычисляем пересечение траектории с областью
                intersection_result = self._calculate_intersection(trajectory, geozone, location_points)
                
                if intersection_result:
                    area_covered, time_spent, progress_percent = intersection_result
                    
                    # Обновляем прогресс открытия
                    updated_discovery = self._update_discovery_progress(
                        discovery,
                        area_covered,
                        time_spent,
                        progress_percent,
                    )
                    
                    # Проверяем, было ли это новое открытие или изменение статуса
                    old_status = discovery.discovery_status
                    new_status = updated_discovery.discovery_status
                    
                    if old_status != new_status or discovery.progress_percent == 0:
                        # Генерируем событие открытия
                        event = self._create_discovery_event(
                            user_id,
                            geozone,
                            updated_discovery,
                            old_status,
                            company_id,
                        )
                        if event:
                            events.append(event)
                            
            except Exception as e:
                logger.error(f"Ошибка при обработке Area POI {geozone.id}: {e}", exc_info=True)
                continue

        return events

    def _is_transit_mode(self, location_points: List[LocationPoint]) -> bool:
        """Определить, движется ли пользователь в Transit Mode (> 25 км/ч)."""
        if len(location_points) < 2:
            return False
        
        # Проверяем среднюю скорость последних точек
        speeds = []
        for point in location_points[-10:]:  # Последние 10 точек
            if point.speed_ms and point.speed_ms > 0:
                speeds.append(point.speed_ms)
        
        if not speeds:
            return False
        
        avg_speed_ms = sum(speeds) / len(speeds)
        return avg_speed_ms >= TransitModeThreshold.SPEED_MS

    def _build_trajectory(self, location_points: List[LocationPoint]) -> Optional[LineString]:
        """Построить LineString из точек геолокации."""
        if len(location_points) < 2:
            return None
        
        coords = []
        for point in sorted(location_points, key=lambda p: p.timestamp):
            coords.append((point.longitude, point.latitude))
        
        try:
            return LineString(coords)
        except Exception as e:
            logger.warning(f"Ошибка построения траектории: {e}")
            return None

    def _find_intersecting_area_poi(
        self,
        trajectory: LineString,
        is_transit_mode: bool,
        company_id: Optional[int] = None,
    ) -> List[Geozone]:
        """Найти все Area POI, пересекающиеся с траекторией."""
        trajectory_geom = from_shape(trajectory, srid=4326)
        
        # Типы Area POI
        area_types = [
            "forest_area",
            "river_basin",
            "valley",
            "national_park",
            "farmland",
            "mountain_range",
            "lake_area",
            "coastal_area",
            "rural_settlement_area",
            "infrastructure_area",
        ]
        
        query = (
            self.db.query(Geozone)
            .filter(
                Geozone.is_active.is_(True),
                Geozone.deleted_at.is_(None),
                Geozone.area_type.in_(area_types),
                func.ST_Intersects(Geozone.polygon, trajectory_geom),
            )
        )
        
        if company_id is not None:
            query = query.filter(Geozone.company_id == company_id)
        
        geozones = query.all()
        
        # В Transit Mode фильтруем только крупные области и инфраструктуру
        if is_transit_mode:
            filtered = []
            for geozone in geozones:
                if geozone.area_type in ["infrastructure_area", "valley", "mountain_range", "coastal_area"]:
                    filtered.append(geozone)
                elif geozone.area_square_meters and geozone.area_square_meters > 5000000:  # > 5 км²
                    filtered.append(geozone)
            return filtered
        
        return geozones

    def _get_or_create_discovery(
        self,
        user_id: int,
        geozone_id: int,
        company_id: Optional[int] = None,
    ) -> AreaDiscovery:
        """Получить или создать запись о открытии области."""
        discovery = (
            self.db.query(AreaDiscovery)
            .filter(
                AreaDiscovery.user_id == user_id,
                AreaDiscovery.geozone_id == geozone_id,
            )
            .first()
        )
        
        if not discovery:
            discovery = AreaDiscovery(
                user_id=user_id,
                geozone_id=geozone_id,
                discovery_status=DiscoveryStatus.DISCOVERED.value,
                progress_percent=0.0,
                time_spent_seconds=0,
                area_covered_meters=0.0,
                first_discovered_at=datetime.now(timezone.utc),
                last_updated_at=datetime.now(timezone.utc),
                company_id=company_id,
            )
            self.db.add(discovery)
            self.db.flush()
        
        return discovery

    def _calculate_intersection(
        self,
        trajectory: LineString,
        geozone: Geozone,
        location_points: List[LocationPoint],
    ) -> Optional[Tuple[float, int, float]]:
        """
        Вычислить пересечение траектории с областью.
        
        Returns:
            Tuple[area_covered_meters, time_spent_seconds, progress_percent] или None
        """
        try:
            polygon = to_shape(geozone.polygon)
            
            # Вычисляем пересечение траектории с полигоном
            intersection = trajectory.intersection(polygon)
            
            if intersection.is_empty:
                return None
            
            # Вычисляем покрытую площадь
            # Для LineString вычисляем длину пересечения
            intersection_length = 0.0
            if hasattr(intersection, 'length'):
                intersection_length = intersection.length
            elif hasattr(intersection, 'geoms'):
                # Для MultiLineString суммируем длины
                intersection_length = sum(geom.length for geom in intersection.geoms if hasattr(geom, 'length'))
            
            # Вычисляем время, проведённое в зоне
            time_spent = self._calculate_time_in_zone(location_points, polygon)
            
            # Вычисляем процент открытой площади
            if geozone.area_square_meters and geozone.area_square_meters > 0:
                # Упрощённый расчёт: используем длину пересечения как метрику покрытия
                # В реальности нужно вычислять площадь пересечения траектории с полигоном
                # Используем приблизительную ширину траектории 100м для расчёта покрытой площади
                area_covered = intersection_length * 100  # Примерная ширина траектории 100м
                progress_percent = min(100.0, (area_covered / geozone.area_square_meters) * 100)
            else:
                # Если площадь не задана, используем эвристику на основе времени
                progress_percent = min(100.0, (time_spent / 300) * 10)  # 10% за 5 минут
                area_covered = 0.0
            
            # Проверяем минимальные условия для открытия
            if time_spent < self.min_time_seconds and progress_percent < self.min_area_percent:
                return None
            
            return (area_covered, time_spent, progress_percent)
            
        except Exception as e:
            logger.error(f"Ошибка вычисления пересечения: {e}", exc_info=True)
            return None

    def _calculate_time_in_zone(
        self,
        location_points: List[LocationPoint],
        polygon: Polygon,
    ) -> int:
        """Вычислить время, проведённое в зоне (в секундах)."""
        time_in_zone = 0
        last_timestamp = None
        
        for point in sorted(location_points, key=lambda p: p.timestamp):
            point_geom = Point(point.longitude, point.latitude)
            if polygon.contains(point_geom):
                if last_timestamp:
                    time_diff = (point.timestamp - last_timestamp).total_seconds()
                    time_in_zone += int(time_diff)
                last_timestamp = point.timestamp
            else:
                last_timestamp = None
        
        return time_in_zone

    def _update_discovery_progress(
        self,
        discovery: AreaDiscovery,
        area_covered: float,
        time_spent: int,
        progress_percent: float,
    ) -> AreaDiscovery:
        """Обновить прогресс открытия области."""
        # Обновляем метрики
        discovery.area_covered_meters = max(discovery.area_covered_meters, area_covered)
        discovery.time_spent_seconds += time_spent
        discovery.progress_percent = max(discovery.progress_percent, progress_percent)
        discovery.last_updated_at = datetime.now(timezone.utc)
        
        # Определяем новый статус на основе прогресса
        if discovery.progress_percent >= 70.0:
            discovery.discovery_status = DiscoveryStatus.COMPLETED.value
        elif discovery.progress_percent >= 30.0:
            discovery.discovery_status = DiscoveryStatus.EXPLORED.value
        else:
            discovery.discovery_status = DiscoveryStatus.DISCOVERED.value
        
        self.db.commit()
        self.db.refresh(discovery)
        
        return discovery

    def _create_discovery_event(
        self,
        user_id: int,
        geozone: Geozone,
        discovery: AreaDiscovery,
        old_status: str,
        company_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Создать событие открытия области."""
        # Вычисляем награды
        xp_reward = self._calculate_xp_reward(geozone, discovery)
        
        event = {
            "type": "AREA_DISCOVERED",
            "area_type": geozone.area_type or geozone.geozone_type,
            "name": geozone.name,
            "geozone_id": geozone.id,
            "progress": discovery.progress_percent,
            "status": discovery.discovery_status,
            "old_status": old_status,
            "reward": {
                "xp": xp_reward,
                "artifact": False,  # Артефакты только в meaningful местах
            },
        }
        
        # Выдаём XP пользователю
        try:
            from app.services.achievement import AchievementService
            achievement_service = AchievementService(self.db)
            achievement_service.add_user_xp(user_id, xp_reward, company_id)
        except Exception as e:
            logger.warning(f"Ошибка при выдаче XP: {e}")
        
        return event

    def _calculate_xp_reward(self, geozone: Geozone, discovery: AreaDiscovery) -> int:
        """Вычислить награду XP за открытие области."""
        base_xp = 50
        
        # Бонус за размер области
        if geozone.area_square_meters:
            if geozone.area_square_meters > 10000000:  # > 10 км²
                base_xp += 100
            elif geozone.area_square_meters > 5000000:  # > 5 км²
                base_xp += 50
        
        # Бонус за статус
        if discovery.discovery_status == DiscoveryStatus.COMPLETED.value:
            base_xp += 100
        elif discovery.discovery_status == DiscoveryStatus.EXPLORED.value:
            base_xp += 50
        
        return base_xp

    def get_user_discoveries(
        self,
        user_id: int,
        geozone_id: Optional[int] = None,
        status: Optional[str] = None,
        company_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AreaDiscovery]:
        """Получить открытия областей пользователя."""
        query = self.db.query(AreaDiscovery).filter(AreaDiscovery.user_id == user_id)
        
        if geozone_id:
            query = query.filter(AreaDiscovery.geozone_id == geozone_id)
        
        if status:
            query = query.filter(AreaDiscovery.discovery_status == status)
        
        if company_id is not None:
            query = query.filter(AreaDiscovery.company_id == company_id)
        
        return query.order_by(AreaDiscovery.last_updated_at.desc()).offset(offset).limit(limit).all()

    def get_discovery_by_geozone(
        self,
        user_id: int,
        geozone_id: int,
        company_id: Optional[int] = None,
    ) -> Optional[AreaDiscovery]:
        """Получить открытие области пользователем."""
        query = (
            self.db.query(AreaDiscovery)
            .filter(
                AreaDiscovery.user_id == user_id,
                AreaDiscovery.geozone_id == geozone_id,
            )
        )
        
        if company_id is not None:
            query = query.filter(AreaDiscovery.company_id == company_id)
        
        return query.first()
