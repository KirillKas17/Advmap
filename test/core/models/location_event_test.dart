import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/models/location_event.dart';

void main() {
  group('LocationEvent', () {
    test('создаёт событие с корректными данными', () {
      final event = LocationEvent(
        id: 'test-id',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
      );

      expect(event.id, equals('test-id'));
      expect(event.latitude, equals(55.7558));
      expect(event.longitude, equals(37.6173));
      expect(event.deviceId, equals('device-123'));
      expect(event.synced, isFalse);
      expect(event.poiId, isNull);
      expect(event.regionId, isNull);
    });

    test('создаёт событие с опциональными полями', () {
      final syncedAt = DateTime(2024, 1, 2);
      final event = LocationEvent(
        id: 'test-id',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
        poiId: 'poi-123',
        regionId: 'region-123',
        synced: true,
        syncedAt: syncedAt,
      );

      expect(event.poiId, equals('poi-123'));
      expect(event.regionId, equals('region-123'));
      expect(event.synced, isTrue);
      expect(event.syncedAt, equals(syncedAt));
    });

    test('copyWith создаёт копию с изменёнными полями', () {
      final original = LocationEvent(
        id: 'test-id',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
      );

      final copy = original.copyWith(
        latitude: 56.0,
        synced: true,
        poiId: 'poi-123',
      );

      expect(copy.id, equals(original.id));
      expect(copy.latitude, equals(56.0));
      expect(copy.longitude, equals(original.longitude));
      expect(copy.synced, isTrue);
      expect(copy.poiId, equals('poi-123'));
    });

    test('toJson и fromJson работают корректно', () {
      final original = LocationEvent(
        id: 'test-id',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1, 12, 0, 0),
        deviceId: 'device-123',
        poiId: 'poi-123',
        regionId: 'region-123',
        synced: true,
        syncedAt: DateTime(2024, 1, 2, 12, 0, 0),
      );

      final json = original.toJson();
      final restored = LocationEvent.fromJson(json);

      expect(restored.id, equals(original.id));
      expect(restored.latitude, equals(original.latitude));
      expect(restored.longitude, equals(original.longitude));
      expect(restored.deviceId, equals(original.deviceId));
      expect(restored.poiId, equals(original.poiId));
      expect(restored.regionId, equals(original.regionId));
      expect(restored.synced, equals(original.synced));
    });
  });
}
