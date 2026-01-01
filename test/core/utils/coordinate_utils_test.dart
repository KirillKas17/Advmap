import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/utils/coordinate_utils.dart';

void main() {
  group('CoordinateUtils', () {
    group('normalizeLongitude', () {
      test('нормализует долготу в диапазон [-180, 180]', () {
        expect(CoordinateUtils.normalizeLongitude(0.0), equals(0.0));
        expect(CoordinateUtils.normalizeLongitude(180.0), equals(180.0));
        expect(CoordinateUtils.normalizeLongitude(-180.0), equals(-180.0));
        expect(CoordinateUtils.normalizeLongitude(181.0), equals(-179.0));
        expect(CoordinateUtils.normalizeLongitude(-181.0), equals(179.0));
        expect(CoordinateUtils.normalizeLongitude(360.0), equals(0.0));
        expect(CoordinateUtils.normalizeLongitude(-360.0), equals(0.0));
        expect(CoordinateUtils.normalizeLongitude(540.0), equals(-180.0));
      });
    });

    group('distanceBetween', () {
      test('вычисляет расстояние между двумя точками', () {
        // Расстояние между Москвой и Санкт-Петербургом ~635 км
        final distance = CoordinateUtils.distanceBetween(
          55.7558, // Москва
          37.6173,
          59.9343, // Санкт-Петербург
          30.3351,
        );
        expect(distance, greaterThan(600000)); // Больше 600 км
        expect(distance, lessThan(700000)); // Меньше 700 км
      });

      test('возвращает 0 для одинаковых точек', () {
        final distance = CoordinateUtils.distanceBetween(
          55.7558,
          37.6173,
          55.7558,
          37.6173,
        );
        expect(distance, equals(0.0));
      });
    });

    group('isPointInBoundingBox', () {
      test('проверяет попадание точки в bounding box', () {
        expect(
          CoordinateUtils.isPointInBoundingBox(
            55.0,
            37.0,
            54.0, // minLat
            56.0, // maxLat
            36.0, // minLon
            38.0, // maxLon
          ),
          isTrue,
        );
      });

      test('отклоняет точки вне bounding box', () {
        expect(
          CoordinateUtils.isPointInBoundingBox(
            53.0, // Вне диапазона
            37.0,
            54.0,
            56.0,
            36.0,
            38.0,
          ),
          isFalse,
        );

        expect(
          CoordinateUtils.isPointInBoundingBox(
            55.0,
            35.0, // Вне диапазона
            54.0,
            56.0,
            36.0,
            38.0,
          ),
          isFalse,
        );
      });

      test('обрабатывает граничные случаи', () {
        expect(
          CoordinateUtils.isPointInBoundingBox(
            54.0, // Граница
            36.0, // Граница
            54.0,
            56.0,
            36.0,
            38.0,
          ),
          isTrue,
        );
      });
    });

    group('approximateDistance', () {
      test('вычисляет приближённое расстояние', () {
        final distance = CoordinateUtils.approximateDistance(
          55.7558,
          37.6173,
          55.7658, // ~1 км севернее
          37.6173,
        );
        expect(distance, greaterThan(500)); // Больше 500 м
        expect(distance, lessThan(2000)); // Меньше 2 км
      });

      test('возвращает 0 для одинаковых точек', () {
        final distance = CoordinateUtils.approximateDistance(
          55.7558,
          37.6173,
          55.7558,
          37.6173,
        );
        expect(distance, equals(0.0));
      });
    });
  });
}
