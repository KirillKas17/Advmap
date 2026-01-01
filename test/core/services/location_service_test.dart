import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/location_service.dart';
import 'package:explorers_map/core/utils/validators.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/poi.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:geolocator/geolocator.dart';

void main() {
  late DatabaseHelper db;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    SharedPreferences.setMockInitialValues({});
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('location_events');
    await database.delete('pois');
  });

  tearDown(() async {
    await db.close();
  });

  group('LocationService', () {
    test('createLocationEvent валидирует координаты', () async {
      final service = LocationService.instance;
      
      // Некорректные координаты должны вернуть null
      final invalidEvent = await service.createLocationEvent(
        latitude: 200.0, // Некорректная широта
        longitude: 0.0,
        deviceId: 'test-device',
      );
      
      expect(invalidEvent, isNull);
    });

    test('createLocationEvent валидирует deviceId', () async {
      final service = LocationService.instance;
      
      // Некорректный deviceId должен вернуть null
      final invalidEvent = await service.createLocationEvent(
        latitude: 55.7558,
        longitude: 37.6173,
        deviceId: '', // Пустой deviceId
      );
      
      expect(invalidEvent, isNull);
    });

    test('createLocationEvent создаёт событие с корректными данными', () async {
      final service = LocationService.instance;
      
      final eventId = await service.createLocationEvent(
        latitude: 55.7558,
        longitude: 37.6173,
        deviceId: 'test-device',
      );
      
      expect(eventId, isNotNull);
      
      final events = await db.getUnsyncedEvents();
      expect(events.length, equals(1));
      expect(events.first.latitude, equals(55.7558));
      expect(events.first.longitude, equals(37.6173));
    });

    test('checkPOIGeofence использует валидацию', () async {
      final service = LocationService.instance;
      
      // Некорректные координаты должны вернуть null
      final result = await service.checkPOIGeofence(200.0, 0.0);
      
      expect(result, isNull);
    });

    test('checkPOIGeofence находит POI в геозоне', () async {
      final service = LocationService.instance;
      
      // Добавляем POI
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'Test POI',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.7558, longitude: 37.6173)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      final poiId = await service.checkPOIGeofence(55.7558, 37.6173);
      expect(poiId, equals('poi-1'));
    });

    test('setBackgroundTrackingEnabled и isBackgroundTrackingEnabled', () async {
      final service = LocationService.instance;
      
      await service.setBackgroundTrackingEnabled(true);
      final enabled = await service.isBackgroundTrackingEnabled();
      expect(enabled, isTrue);
      
      await service.setBackgroundTrackingEnabled(false);
      final disabled = await service.isBackgroundTrackingEnabled();
      expect(disabled, isFalse);
    });

    test('getLocationAccuracy и setLocationAccuracy', () async {
      final service = LocationService.instance;
      
      await service.setLocationAccuracy(LocationAccuracy.high);
      final accuracy = await service.getLocationAccuracy();
      expect(accuracy, equals(LocationAccuracy.high));
      
      await service.setLocationAccuracy(LocationAccuracy.low);
      final lowAccuracy = await service.getLocationAccuracy();
      expect(lowAccuracy, equals(LocationAccuracy.low));
    });
  });
}
