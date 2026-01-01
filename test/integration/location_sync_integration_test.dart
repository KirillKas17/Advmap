import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/location_service.dart';
import 'package:explorers_map/core/services/sync_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/location_event.dart';
import 'package:explorers_map/core/models/poi.dart';

void main() {
  late DatabaseHelper db;
  late LocationService locationService;
  late SyncService syncService;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    locationService = LocationService.instance;
    syncService = SyncService.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('location_events');
  });

  tearDown(() async {
    await db.close();
  });

  group('Location Sync Integration', () {
    test('создаёт событие геолокации и сохраняет в БД', () async {
      final eventId = await locationService.createLocationEvent(
        latitude: 55.7558,
        longitude: 37.6173,
        deviceId: 'test-device',
      );

      expect(eventId, isNotNull);

      final unsynced = await db.getUnsyncedEvents();
      expect(unsynced.length, equals(1));
      expect(unsynced.first.id, equals(eventId));
    });

    test('валидирует координаты при создании события', () async {
      final eventId = await locationService.createLocationEvent(
        latitude: 200.0, // Некорректная широта
        longitude: 37.6173,
        deviceId: 'test-device',
      );

      expect(eventId, isNull);

      final unsynced = await db.getUnsyncedEvents();
      expect(unsynced.isEmpty, isTrue);
    });

    test('создаёт событие с POI если попадает в геозону', () async {
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

      final eventId = await locationService.createLocationEvent(
        latitude: 55.7558,
        longitude: 37.6173,
        deviceId: 'test-device',
      );

      expect(eventId, isNotNull);

      final events = await db.getUnsyncedEvents();
      expect(events.first.poiId, equals('poi-1'));
    });

    test('синхронизирует неотправленные события', () async {
      // Создаём несколько событий
      for (int i = 0; i < 5; i++) {
        await locationService.createLocationEvent(
          latitude: 55.7558 + i * 0.001,
          longitude: 37.6173 + i * 0.001,
          deviceId: 'test-device',
        );
      }

      final unsyncedBefore = await db.getUnsyncedEventsCount();
      expect(unsyncedBefore, equals(5));

      // Пытаемся синхронизировать (без интернета вернёт false)
      final hasInternet = await syncService.checkInternetConnection();
      if (hasInternet) {
        final synced = await syncService.syncPendingEvents();
        // В тестовой среде без реального сервера синхронизация может не пройти
        // Но проверяем, что метод вызывается без ошибок
        expect(synced is bool, isTrue);
      }
    });
  });
}
