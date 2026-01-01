"""Тесты для обнаружения спуфинга GPS."""
from datetime import datetime

import pytest

from app.services.gps_spoofing import GPSSpoofingDetectionService


def test_detect_spoofing_high_speed(db_session):
    """Тест обнаружения спуфинга по высокой скорости."""
    service = GPSSpoofingDetectionService(db_session)

    is_spoofed, score, reason = service.detect_spoofing(
        latitude=55.7558,
        longitude=37.6173,
        accuracy_meters=10.0,
        speed_ms=200.0,  # Нереалистично высокая скорость
        timestamp=datetime.utcnow(),
        user_id=1,
    )

    assert is_spoofed is True
    assert score > 0.5
    assert reason is not None


def test_detect_spoofing_low_accuracy(db_session):
    """Тест обнаружения спуфинга по низкой точности."""
    service = GPSSpoofingDetectionService(db_session)

    is_spoofed, score, reason = service.detect_spoofing(
        latitude=55.7558,
        longitude=37.6173,
        accuracy_meters=2000.0,  # Очень низкая точность
        speed_ms=10.0,
        timestamp=datetime.utcnow(),
        user_id=1,
    )

    assert is_spoofed is True
    assert score > 0.5
    assert reason is not None
