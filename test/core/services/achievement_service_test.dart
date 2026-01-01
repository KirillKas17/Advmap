import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/achievement_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/achievement.dart';
import 'package:explorers_map/core/models/home_work_location.dart';
import 'package:explorers_map/core/models/poi.dart';
import 'package:explorers_map/core/models/region.dart';

void main() {
  late DatabaseHelper db;
  late AchievementService service;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    service = AchievementService.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('achievements');
    await database.delete('opened_pois');
    await database.delete('home_work_locations');
    await database.delete('location_events');
    await database.delete('cached_regions');
  });

  tearDown(() async {
    await db.close();
  });

  group('AchievementService', () {
    test('проверяет ачивку "Коллекционер мест"', () async {
      // Добавляем 100 открытых POI
      for (int i = 0; i < 100; i++) {
        await db.insertPOI(POI(
          id: 'poi-$i',
          name: 'POI $i',
          description: 'Test',
          latitude: 55.7558 + i * 0.001,
          longitude: 37.6173 + i * 0.001,
          type: 'landmark',
          geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
          regionId: 'region-1',
        ));
        await db.markPOIOpenedSafe('poi-$i');
      }

      final achievements = await service.checkAndUnlockAchievements();
      final collector = achievements.firstWhere(
        (a) => a.id == 'collector',
        orElse: () => Achievement(
          id: '',
          title: '',
          description: '',
          category: '',
        ),
      );

      expect(collector.id, equals('collector'));
    });

    test('проверяет ачивку "Путешественник"', () async {
      // Добавляем 10 регионов
      for (int i = 0; i < 10; i++) {
        await db.insertCachedRegion(Region(
          id: 'region-$i',
          name: 'Region $i',
          bounds: RegionBounds(
            north: 56.0 + i,
            south: 55.0 + i,
            east: 38.0 + i,
            west: 37.0 + i,
          ),
        ));
      }

      final achievements = await service.checkAndUnlockAchievements();
      final traveler = achievements.firstWhere(
        (a) => a.id == 'traveler',
        orElse: () => Achievement(
          id: '',
          title: '',
          description: '',
          category: '',
        ),
      );

      expect(traveler.id, equals('traveler'));
    });

    test('сохраняет разблокированную ачивку', () async {
      final achievement = Achievement(
        id: 'test-achievement',
        title: 'Test',
        description: 'Test',
        category: 'test',
        unlockedAt: DateTime.now(),
      );

      await service.saveAchievement(achievement);

      final saved = await db.getAchievementById('test-achievement');
      expect(saved, isNotNull);
      expect(saved!.title, equals('Test'));
    });

    test('не сохраняет дубликаты ачивок', () async {
      final achievement = Achievement(
        id: 'test-achievement',
        title: 'Test',
        description: 'Test',
        category: 'test',
        unlockedAt: DateTime.now(),
      );

      await service.saveAchievement(achievement);
      await service.saveAchievement(achievement);

      final achievements = await service.getUnlockedAchievements();
      expect(achievements.length, equals(1));
    });

    test('получает все разблокированные ачивки', () async {
      await db.insertAchievement(Achievement(
        id: 'achievement-1',
        title: 'Achievement 1',
        description: 'Test',
        category: 'test',
        unlockedAt: DateTime.now(),
      ));

      await db.insertAchievement(Achievement(
        id: 'achievement-2',
        title: 'Achievement 2',
        description: 'Test',
        category: 'test',
      ));

      final unlocked = await service.getUnlockedAchievements();
      expect(unlocked.length, equals(1));
      expect(unlocked.first.id, equals('achievement-1'));
    });
  });
}
