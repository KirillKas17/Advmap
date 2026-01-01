import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/models/home_work_location.dart';

void main() {
  group('HomeWorkLocation', () {
    test('создаёт локацию с корректными данными', () {
      final location = HomeWorkLocation(
        id: 'location-123',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
      );

      expect(location.id, equals('location-123'));
      expect(location.type, equals(LocationType.home));
      expect(location.latitude, equals(55.7558));
      expect(location.longitude, equals(37.6173));
      expect(location.radius, equals(100.0));
      expect(location.verified, isFalse);
    });

    test('создаёт верифицированную локацию', () {
      final verifiedAt = DateTime(2024, 1, 2);
      final location = HomeWorkLocation(
        id: 'location-123',
        type: LocationType.work,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
        verified: true,
        verifiedAt: verifiedAt,
        customName: 'Офис',
      );

      expect(location.type, equals(LocationType.work));
      expect(location.verified, isTrue);
      expect(location.verifiedAt, equals(verifiedAt));
      expect(location.customName, equals('Офис'));
    });

    test('displayName возвращает кастомное имя или дефолтное', () {
      final withCustomName = HomeWorkLocation(
        id: 'location-123',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
        customName: 'Мой дом',
      );
      expect(withCustomName.displayName, equals('Мой дом'));

      final withoutCustomName = HomeWorkLocation(
        id: 'location-123',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
      );
      expect(withoutCustomName.displayName, equals('Дом'));

      final workLocation = HomeWorkLocation(
        id: 'location-123',
        type: LocationType.work,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
      );
      expect(workLocation.displayName, equals('Работа'));
    });

    test('toJson и fromJson работают корректно', () {
      final original = HomeWorkLocation(
        id: 'location-123',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
        verified: true,
        verifiedAt: DateTime(2024, 1, 2),
        customName: 'Мой дом',
      );

      final json = original.toJson();
      final restored = HomeWorkLocation.fromJson(json);

      expect(restored.id, equals(original.id));
      expect(restored.type, equals(original.type));
      expect(restored.latitude, equals(original.latitude));
      expect(restored.longitude, equals(original.longitude));
      expect(restored.radius, equals(original.radius));
      expect(restored.verified, equals(original.verified));
      expect(restored.customName, equals(original.customName));
    });
  });
}
