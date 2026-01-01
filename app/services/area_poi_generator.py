"""Сервис генерации Area POI из геоданных OpenStreetMap."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import make_valid
from shapely.ops import transform
from sqlalchemy import text, func
from sqlalchemy.orm import Session
import pyproj

from app.core.config import get_settings
from app.models.geozone import Geozone
from app.services.geozone import GeozoneService

settings = get_settings()
logger = logging.getLogger(__name__)


class AreaPOIGenerator:
    """Сервис для генерации Area POI из геоданных."""

    def __init__(self, db: Session):
        """Инициализация сервиса."""
        self.db = db
        self.geozone_service = GeozoneService(db)
        self.min_area_square_meters = 500000  # 0.5 км²

    def generate_area_poi_from_osm(
        self,
        bbox: Optional[Dict[str, float]] = None,
        area_types: Optional[List[str]] = None,
        company_id: Optional[int] = None,
    ) -> List[Geozone]:
        """
        Генерировать Area POI из данных OpenStreetMap через PostGIS.
        
        Args:
            bbox: Границы для поиска {'min_lon': float, 'min_lat': float, 'max_lon': float, 'max_lat': float}
            area_types: Типы областей для генерации (если None - все типы)
            company_id: ID компании
            
        Returns:
            Список созданных геозон
        """
        if area_types is None:
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
        
        created_geozones = []
        
        # Маппинг OSM тегов на типы Area POI
        osm_tag_mapping = {
            "forest_area": [
                ("landuse", "forest"),
                ("natural", "wood"),
            ],
            "river_basin": [
                ("waterway", "river"),
                ("waterway", "stream"),
                ("natural", "water"),
            ],
            "valley": [
                ("natural", "valley"),
            ],
            "national_park": [
                ("leisure", "nature_reserve"),
                ("boundary", "national_park"),
                ("leisure", "park"),
            ],
            "farmland": [
                ("landuse", "farmland"),
                ("landuse", "agricultural"),
            ],
            "mountain_range": [
                ("natural", "mountain_range"),
                ("natural", "peak"),
            ],
            "lake_area": [
                ("natural", "water"),
                ("waterway", "riverbank"),
            ],
            "coastal_area": [
                ("natural", "coastline"),
                ("place", "bay"),
            ],
            "rural_settlement_area": [
                ("place", "village"),
                ("place", "hamlet"),
            ],
            "infrastructure_area": [
                ("highway", "motorway"),
                ("highway", "trunk"),
                ("railway", "rail"),
            ],
        }
        
        for area_type in area_types:
            if area_type not in osm_tag_mapping:
                continue
            
            tags = osm_tag_mapping[area_type]
            geozones = self._query_osm_features(tags, bbox, area_type, company_id)
            created_geozones.extend(geozones)
        
        return created_geozones

    def _query_osm_features(
        self,
        tags: List[tuple],
        bbox: Optional[Dict[str, float]],
        area_type: str,
        company_id: Optional[int],
    ) -> List[Geozone]:
        """
        Запросить объекты OSM из PostGIS по тегам.
        
        Предполагается, что в БД есть таблица osm_features с колонками:
        - geometry (geometry)
        - tags (jsonb)
        - name (text)
        - osm_id (bigint)
        """
        created_geozones = []
        
        try:
            # Формируем SQL запрос для поиска объектов OSM
            # Это примерный запрос - в реальности структура таблицы может отличаться
            query_parts = []
            params = {}
            
            # Условие по тегам
            tag_conditions = []
            for i, (key, value) in enumerate(tags):
                tag_conditions.append(f"tags->>'{key}' = :tag_value_{i}")
                params[f"tag_value_{i}"] = value
            
            tag_where = " OR ".join(tag_conditions)
            
            # Условие по bbox
            bbox_where = ""
            if bbox:
                bbox_where = f"""
                    AND ST_Intersects(
                        geometry,
                        ST_MakeEnvelope(
                            :min_lon, :min_lat, :max_lon, :max_lat, 4326
                        )
                    )
                """
                params.update({
                    "min_lon": bbox["min_lon"],
                    "min_lat": bbox["min_lat"],
                    "max_lon": bbox["max_lon"],
                    "max_lat": bbox["max_lat"],
                })
            
            # Проверяем существование таблицы osm_features
            # Если таблицы нет, возвращаем пустой список (данные можно загрузить отдельно)
            check_table_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'osm_features'
                )
            """)
            table_exists = self.db.execute(check_table_query).scalar()
            
            if not table_exists:
                logger.warning("Таблица osm_features не найдена. Используйте импорт данных OSM.")
                return []
            
            # Запрос объектов OSM
            sql_query = text(f"""
                SELECT 
                    osm_id,
                    name,
                    tags,
                    ST_AsText(geometry) as geometry_wkt,
                    ST_Area(ST_Transform(geometry, 3857)) as area_m2
                FROM osm_features
                WHERE ({tag_where})
                    AND geometry IS NOT NULL
                    AND ST_Area(ST_Transform(geometry, 3857)) > :min_area
                    {bbox_where}
                LIMIT 1000
            """)
            
            params["min_area"] = self.min_area_square_meters
            
            result = self.db.execute(sql_query, params)
            
            for row in result:
                try:
                    geozone = self._create_geozone_from_osm_row(
                        row, area_type, company_id
                    )
                    if geozone:
                        created_geozones.append(geozone)
                except Exception as e:
                    logger.error(f"Ошибка создания геозоны из OSM объекта {row.osm_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Ошибка запроса OSM объектов: {e}", exc_info=True)
        
        return created_geozones

    def _create_geozone_from_osm_row(
        self,
        row: Any,
        area_type: str,
        company_id: Optional[int],
    ) -> Optional[Geozone]:
        """Создать геозону из строки результата OSM запроса."""
        try:
            # Проверяем, не существует ли уже такая геозона
            existing = (
                self.db.query(Geozone)
                .filter(
                    Geozone.osm_id == str(row.osm_id),
                    Geozone.area_type == area_type,
                    Geozone.deleted_at.is_(None),
                )
                .first()
            )
            
            if existing:
                return existing
            
            # Парсим WKT геометрию
            from shapely import wkt as shapely_wkt
            geometry = shapely_wkt.loads(row.geometry_wkt)
            
            # Преобразуем MultiPolygon в Polygon если нужно
            if isinstance(geometry, MultiPolygon):
                # Берём самый большой полигон
                geometry = max(geometry.geoms, key=lambda p: p.area)
            
            if not isinstance(geometry, Polygon):
                logger.warning(f"Неожиданный тип геометрии для OSM объекта {row.osm_id}")
                return None
            
            # Валидация и исправление полигона
            if not geometry.is_valid:
                geometry = make_valid(geometry)
            
            # Вычисляем центр
            center = geometry.centroid
            center_lat = center.y
            center_lon = center.x
            
            # Получаем название
            name = row.name
            if not name and row.tags:
                # Пытаемся извлечь название из тегов
                if isinstance(row.tags, dict):
                    name = row.tags.get("name") or row.tags.get("name:en") or f"{area_type.replace('_', ' ').title()} {row.osm_id}"
                else:
                    name = f"{area_type.replace('_', ' ').title()} {row.osm_id}"
            elif not name:
                name = f"{area_type.replace('_', ' ').title()} {row.osm_id}"
            
            # Вычисляем площадь в м²
            area_m2 = row.area_m2 if hasattr(row, 'area_m2') else None
            if not area_m2:
                # Вычисляем площадь через преобразование в проекцию для точного расчёта
                try:
                    wgs84 = pyproj.CRS('EPSG:4326')
                    utm = pyproj.CRS('EPSG:3857')
                    project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
                    projected_geom = transform(project, geometry)
                    area_m2 = projected_geom.area
                except Exception:
                    # Fallback: приблизительный расчёт
                    area_m2 = geometry.area * 111000 * 111000  # Примерно
            
            # Создаём геозону
            polygon_coords = [[lon, lat] for lon, lat in geometry.exterior.coords]
            
            geozone = self.geozone_service.create_geozone(
                name=name,
                polygon_coordinates=polygon_coords,
                geozone_type="area_poi",
                description=f"Area POI generated from OpenStreetMap (OSM ID: {row.osm_id})",
                company_id=company_id,
            )
            
            # Обновляем дополнительные поля
            geozone.area_type = area_type
            geozone.area_square_meters = area_m2
            geozone.osm_id = str(row.osm_id)
            if row.tags:
                geozone.osm_tags = row.tags if isinstance(row.tags, dict) else {}
            
            self.db.commit()
            self.db.refresh(geozone)
            
            logger.info(f"Создана Area POI: {geozone.name} (ID: {geozone.id}, тип: {area_type})")
            
            return geozone
            
        except Exception as e:
            logger.error(f"Ошибка создания геозоны: {e}", exc_info=True)
            self.db.rollback()
            return None

    def generate_area_poi_for_region(
        self,
        center_lat: float,
        center_lon: float,
        radius_km: float = 50.0,
        company_id: Optional[int] = None,
    ) -> List[Geozone]:
        """
        Генерировать Area POI для региона вокруг точки.
        
        Args:
            center_lat: Широта центра региона
            center_lon: Долгота центра региона
            radius_km: Радиус региона в километрах
            company_id: ID компании
            
        Returns:
            Список созданных геозон
        """
        # Вычисляем bbox
        # Приблизительный расчёт (для точного нужна проекция)
        lat_offset = radius_km / 111.0
        lon_offset = radius_km / (111.0 * abs(center_lat / 90.0) if center_lat != 0 else 1)
        
        bbox = {
            "min_lon": center_lon - lon_offset,
            "min_lat": center_lat - lat_offset,
            "max_lon": center_lon + lon_offset,
            "max_lat": center_lat + lat_offset,
        }
        
        return self.generate_area_poi_from_osm(bbox=bbox, company_id=company_id)
