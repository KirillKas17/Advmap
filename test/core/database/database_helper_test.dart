import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/location_event.dart';
import 'package:explorers_map/core/models/poi.dart';
import 'package:explorers_map/core/models/home_work_location.dart';
import 'package:explorers_map/core/models/region.dart';
import 'package:explorers_map/core/models/achievement.dart';

void main() {
  late DatabaseHelper db;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    // Очищаем БД перед каждым тестом
    final database = await db.database;
    await database.delete('location_events');
    await database.delete('pois');
    await database.delete('home_work_locations');
    await database.delete('cached_regions');
    await database.delete('opened_pois');
    await database.delete('achievements');
  });

  tearDown(() async {
    await db.close();
  });

  group('LocationEvents', () {
    test('вставляет событие геолокации', () async {
      final event = LocationEvent(
        id: 'event-1',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
      );

      final id = await db.insertLocationEvent(event);
      expect(id, equals('event-1'));

      final unsynced = await db.getUnsyncedEvents();
      expect(unsynced.length, equals(1));
      expect(unsynced.first.id, equals('event-1'));
    });

    test('получает несинхронизированные события', () async {
      await db.insertLocationEvent(LocationEvent(
        id: 'event-1',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
        synced: false,
      ));

      await db.insertLocationEvent(LocationEvent(
        id: 'event-2',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 2),
        deviceId: 'device-123',
        synced: true,
      ));

      final unsynced = await db.getUnsyncedEvents();
      expect(unsynced.length, equals(1));
      expect(unsynced.first.id, equals('event-1'));
    });

    test('помечает события как синхронизированные', () async {
      await db.insertLocationEvent(LocationEvent(
        id: 'event-1',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
        synced: false,
      ));

      await db.markEventsAsSynced(['event-1']);

      final unsynced = await db.getUnsyncedEvents();
      expect(unsynced.isEmpty, isTrue);
    });

    test('получает синхронизированные события за период', () async {
      await db.insertLocationEvent(LocationEvent(
        id: 'event-1',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
        synced: true,
        syncedAt: DateTime(2024, 1, 1),
      ));

      await db.insertLocationEvent(LocationEvent(
        id: 'event-2',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 15),
        deviceId: 'device-123',
        synced: true,
        syncedAt: DateTime(2024, 1, 15),
      ));

      final synced = await db.getSyncedEvents(
        startDate: DateTime(2024, 1, 1),
        endDate: DateTime(2024, 1, 10),
      );
      expect(synced.length, equals(1));
      expect(synced.first.id, equals('event-1'));
    });

    test('получает количество несинхронизированных событий', () async {
      await db.insertLocationEvent(LocationEvent(
        id: 'event-1',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 1),
        deviceId: 'device-123',
        synced: false,
      ));

      await db.insertLocationEvent(LocationEvent(
        id: 'event-2',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: DateTime(2024, 1, 2),
        deviceId: 'device-123',
        synced: false,
      ));

      final count = await db.getUnsyncedEventsCount();
      expect(count, equals(2));
    });
  });

  group('POIs', () {
    test('вставляет POI', () async {
      final poi = POI(
        id: 'poi-1',
        name: 'Test POI',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [
          GeoPoint(latitude: 55.0, longitude: 37.0),
          GeoPoint(latitude: 56.0, longitude: 37.0),
          GeoPoint(latitude: 56.0, longitude: 38.0),
        ],
        regionId: 'region-1',
      );

      await db.insertPOI(poi);

      final retrieved = await db.getPOIById('poi-1');
      expect(retrieved, isNotNull);
      expect(retrieved!.name, equals('Test POI'));
    });

    test('получает POI по региону', () async {
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'POI 1',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
        regionId: 'region-1',
      ));

      await db.insertPOI(POI(
        id: 'poi-2',
        name: 'POI 2',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
        regionId: 'region-2',
      ));

      final pois = await db.getPOIsByRegion('region-1');
      expect(pois.length, equals(1));
      expect(pois.first.id, equals('poi-1'));
    });

    test('получает POI поблизости', () async {
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'Near POI',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.7558, longitude: 37.6173)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      await db.insertPOI(POI(
        id: 'poi-2',
        name: 'Far POI',
        description: 'Test',
        latitude: 60.0,
        longitude: 40.0,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 60.0, longitude: 40.0)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      final nearby = await db.getPOIsNearby(
        latitude: 55.7558,
        longitude: 37.6173,
        radiusMeters: 1000.0,
      );
      expect(nearby.length, equals(1));
      expect(nearby.first.id, equals('poi-1'));
    });

    test('отмечает POI как открытый', () async {
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'Test POI',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
        regionId: 'region-1',
      ));

      await db.markPOIOpenedSafe('poi-1');

      final isOpened = await db.isPOIOpened('poi-1');
      expect(isOpened, isTrue);
    });

    test('безопасно открывает POI (избегает дубликатов)', () async {
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'Test POI',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
        regionId: 'region-1',
      ));

      await db.markPOIOpenedSafe('poi-1');
      await db.markPOIOpenedSafe('poi-1'); // Повторный вызов

      final openedIds = await db.getOpenedPOIIds();
      expect(openedIds.length, equals(1));
    });

    test('получает количество открытых POI', () async {
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'Test POI',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
        regionId: 'region-1',
      ));

      await db.markPOIOpenedSafe('poi-1');

      final count = await db.getOpenedPOIsCount();
      expect(count, equals(1));
    });
  });

  group('HomeWorkLocations', () {
    test('вставляет локацию дома/работы', () async {
      final location = HomeWorkLocation(
        id: 'location-1',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
      );

      await db.insertHomeWorkLocation(location);

      final locations = await db.getHomeWorkLocations();
      expect(locations.length, equals(1));
      expect(locations.first.type, equals(LocationType.home));
    });

    test('получает только верифицированные локации', () async {
      await db.insertHomeWorkLocation(HomeWorkLocation(
        id: 'location-1',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
        verified: true,
      ));

      await db.insertHomeWorkLocation(HomeWorkLocation(
        id: 'location-2',
        type: LocationType.work,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
        verified: false,
      ));

      final verified = await db.getHomeWorkLocations(verifiedOnly: true);
      expect(verified.length, equals(1));
      expect(verified.first.id, equals('location-1'));
    });

    test('обновляет верификацию локации', () async {
      await db.insertHomeWorkLocation(HomeWorkLocation(
        id: 'location-1',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime(2024, 1, 1),
        verified: false,
      ));

      await db.updateHomeWorkLocationVerification('location-1', true, 'Мой дом');

      final locations = await db.getHomeWorkLocations();
      expect(locations.first.verified, isTrue);
      expect(locations.first.customName, equals('Мой дом'));
    });
  });

  group('Regions', () {
    test('вставляет регион', () async {
      final region = Region(
        id: 'region-1',
        name: 'Test Region',
        bounds: RegionBounds(
          north: 56.0,
          south: 55.0,
          east: 38.0,
          west: 37.0,
        ),
        downloadedAt: DateTime(2024, 1, 1),
      );

      await db.insertCachedRegion(region);

      final regions = await db.getCachedRegions();
      expect(regions.length, equals(1));
      expect(regions.first.name, equals('Test Region'));
    });

    test('получает регион по ID', () async {
      await db.insertCachedRegion(Region(
        id: 'region-1',
        name: 'Test Region',
        bounds: RegionBounds(
          north: 56.0,
          south: 55.0,
          east: 38.0,
          west: 37.0,
        ),
      ));

      final region = await db.getCachedRegion('region-1');
      expect(region, isNotNull);
      expect(region!.name, equals('Test Region'));
    });
  });

  group('Achievements', () {
    test('вставляет достижение', () async {
      final achievement = Achievement(
        id: 'achievement-1',
        title: 'Test Achievement',
        description: 'Test',
        category: 'exploration',
        unlockedAt: DateTime(2024, 1, 1),
      );

      await db.insertAchievement(achievement);

      final retrieved = await db.getAchievementById('achievement-1');
      expect(retrieved, isNotNull);
      expect(retrieved!.title, equals('Test Achievement'));
    });

    test('получает только разблокированные достижения', () async {
      await db.insertAchievement(Achievement(
        id: 'achievement-1',
        title: 'Unlocked',
        description: 'Test',
        category: 'exploration',
        unlockedAt: DateTime(2024, 1, 1),
      ));

      await db.insertAchievement(Achievement(
        id: 'achievement-2',
        title: 'Locked',
        description: 'Test',
        category: 'exploration',
      ));

      final unlocked = await db.getAchievements(unlockedOnly: true);
      expect(unlocked.length, equals(1));
      expect(unlocked.first.id, equals('achievement-1'));
    });
  });

  group('Cleanup', () {
    test('очищает старые синхронизированные события', () async {
      final oldDate = DateTime(2024, 1, 1);
      final newDate = DateTime.now();

      await db.insertLocationEvent(LocationEvent(
        id: 'event-old',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: oldDate,
        deviceId: 'device-123',
        synced: true,
        syncedAt: oldDate,
      ));

      await db.insertLocationEvent(LocationEvent(
        id: 'event-new',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: newDate,
        deviceId: 'device-123',
        synced: true,
        syncedAt: newDate,
      ));

      final deleted = await db.cleanupOldSyncedEvents(daysToKeep: 30);
      expect(deleted, greaterThan(0));
    });
  });
}
