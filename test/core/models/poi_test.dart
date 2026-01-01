import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/models/poi.dart';

void main() {
  group('POI', () {
    final defaultGeofence = [
      GeoPoint(latitude: 55.0, longitude: 37.0),
      GeoPoint(latitude: 56.0, longitude: 37.0),
      GeoPoint(latitude: 56.0, longitude: 38.0),
      GeoPoint(latitude: 55.0, longitude: 38.0),
    ];

    test('создаёт POI с корректными данными', () {
      final poi = POI(
        id: 'poi-123',
        name: 'Test POI',
        description: 'Test Description',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: defaultGeofence,
        regionId: 'region-123',
      );

      expect(poi.id, equals('poi-123'));
      expect(poi.name, equals('Test POI'));
      expect(poi.latitude, equals(55.7558));
      expect(poi.longitude, equals(37.6173));
      expect(poi.type, equals('landmark'));
      expect(poi.regionId, equals('region-123'));
    });

    group('isPointInGeofence', () {
      test('проверяет попадание точки в геозону с радиусом', () {
        final poi = POI(
          id: 'poi-123',
          name: 'Test POI',
          description: 'Test',
          latitude: 55.7558,
          longitude: 37.6173,
          type: 'landmark',
          geofence: defaultGeofence,
          radius: 100.0,
          regionId: 'region-123',
        );

        // Точка внутри радиуса
        expect(poi.isPointInGeofence(55.7558, 37.6173), isTrue);
        // Точка на границе радиуса
        expect(poi.isPointInGeofence(55.7568, 37.6173), isTrue);
        // Точка вне радиуса
        expect(poi.isPointInGeofence(55.7658, 37.6173), isFalse);
      });

      test('проверяет попадание точки в полигон', () {
        final poi = POI(
          id: 'poi-123',
          name: 'Test POI',
          description: 'Test',
          latitude: 55.5,
          longitude: 37.5,
          type: 'landmark',
          geofence: defaultGeofence,
          regionId: 'region-123',
        );

        // Точка внутри полигона
        expect(poi.isPointInGeofence(55.5, 37.5), isTrue);
        // Точка вне полигона
        expect(poi.isPointInGeofence(54.0, 36.0), isFalse);
      });
    });

    test('toJson и fromJson работают корректно', () {
      final original = POI(
        id: 'poi-123',
        name: 'Test POI',
        description: 'Test Description',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: defaultGeofence,
        radius: 100.0,
        regionId: 'region-123',
        iconUrl: 'https://example.com/icon.png',
        achievementCategory: 'exploration',
      );

      final json = original.toJson();
      final restored = POI.fromJson(json);

      expect(restored.id, equals(original.id));
      expect(restored.name, equals(original.name));
      expect(restored.latitude, equals(original.latitude));
      expect(restored.longitude, equals(original.longitude));
      expect(restored.type, equals(original.type));
      expect(restored.radius, equals(original.radius));
      expect(restored.regionId, equals(original.regionId));
      expect(restored.iconUrl, equals(original.iconUrl));
      expect(restored.achievementCategory, equals(original.achievementCategory));
    });
  });

  group('GeoPoint', () {
    test('создаёт точку с корректными координатами', () {
      final point = GeoPoint(latitude: 55.7558, longitude: 37.6173);
      expect(point.latitude, equals(55.7558));
      expect(point.longitude, equals(37.6173));
    });

    test('toJson и fromJson работают корректно', () {
      final original = GeoPoint(latitude: 55.7558, longitude: 37.6173);
      final json = original.toJson();
      final restored = GeoPoint.fromJson(json);

      expect(restored.latitude, equals(original.latitude));
      expect(restored.longitude, equals(original.longitude));
    });
  });
}
