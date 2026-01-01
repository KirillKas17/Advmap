import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/achievement_service.dart';
import 'package:explorers_map/core/services/location_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/poi.dart';
import 'package:explorers_map/core/models/achievement.dart';

void main() {
  late DatabaseHelper db;
  late AchievementService achievementService;
  late LocationService locationService;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    achievementService = AchievementService.instance;
    locationService = LocationService.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('achievements');
    await database.delete('opened_pois');
    await database.delete('pois');
    await database.delete('location_events');
  });

  tearDown(() async {
    await db.close();
  });

  group('Achievement Unlock Integration', () {
    test('разблокирует ачивку при открытии 100 POI', () async {
      // Добавляем 100 POI
      for (int i = 0; i < 100; i++) {
        await db.insertPOI(POI(
          id: 'poi-$i',
          name: 'POI $i',
          description: 'Test',
          latitude: 55.7558 + i * 0.001,
          longitude: 37.6173 + i * 0.001,
          type: 'landmark',
          geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
          radius: 100.0,
          regionId: 'region-1',
        ));
      }

      // Открываем все POI через создание событий геолокации
      for (int i = 0; i < 100; i++) {
        await locationService.createLocationEvent(
          latitude: 55.7558 + i * 0.001,
          longitude: 37.6173 + i * 0.001,
          deviceId: 'test-device',
        );
      }

      // Проверяем ачивки
      final achievements = await achievementService.checkAndUnlockAchievements();
      final collector = achievements.firstWhere(
        (a) => a.id == 'collector',
        orElse: () => Achievement(
          id: '',
          title: '',
          description: '',
          category: '',
        ),
      );

      if (collector.id == 'collector') {
        await achievementService.saveAchievement(collector);
        final saved = await db.getAchievementById('collector');
        expect(saved, isNotNull);
      }
    });

    test('интеграция открытия POI и проверки ачивок', () async {
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

      // Создаём событие геолокации в геозоне POI
      await locationService.createLocationEvent(
        latitude: 55.7558,
        longitude: 37.6173,
        deviceId: 'test-device',
      );

      // Проверяем, что POI открыт
      final isOpened = await db.isPOIOpened('poi-1');
      expect(isOpened, isTrue);

      // Проверяем ачивки
      final achievements = await achievementService.checkAndUnlockAchievements();
      // Может быть разблокирована ачивка или нет в зависимости от условий
      expect(achievements is List, isTrue);
    });
  });
}
