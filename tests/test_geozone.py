"""Тесты для сервиса геозон."""
import pytest
from shapely.geometry import Point

from app.services.geozone import GeozoneService


def test_create_geozone(db_session):
    """Тест создания геозоны."""
    service = GeozoneService(db_session)
    polygon_coords = [
        [37.6173, 55.7558],  # Москва
        [37.6273, 55.7558],
        [37.6273, 55.7658],
        [37.6173, 55.7658],
        [37.6173, 55.7558],  # Замыкаем полигон
    ]

    geozone = service.create_geozone(
        name="Тестовая геозона",
        polygon_coordinates=polygon_coords,
        geozone_type="landmark",
    )

    assert geozone.id is not None
    assert geozone.name == "Тестовая геозона"
    assert geozone.geozone_type == "landmark"


def test_check_point_in_geozone(db_session):
    """Тест проверки точки в геозоне."""
    service = GeozoneService(db_session)
    polygon_coords = [
        [37.6173, 55.7558],
        [37.6273, 55.7558],
        [37.6273, 55.7658],
        [37.6173, 55.7658],
        [37.6173, 55.7558],
    ]

    geozone = service.create_geozone(
        name="Тестовая геозона",
        polygon_coordinates=polygon_coords,
        geozone_type="landmark",
    )

    # Точка внутри
    is_inside = service.check_point_in_geozone(55.7608, 37.6223, geozone.id)
    assert is_inside is True

    # Точка снаружи
    is_outside = service.check_point_in_geozone(55.7000, 37.5000, geozone.id)
    assert is_outside is False
