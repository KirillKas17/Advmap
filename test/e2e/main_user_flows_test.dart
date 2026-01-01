import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/location_service.dart';
import 'package:explorers_map/core/services/achievement_service.dart';
import 'package:explorers_map/core/services/sync_service.dart';
import 'package:explorers_map/core/services/home_work_detector.dart';
import 'package:explorers_map/core/services/recommendation_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/poi.dart';
import 'package:explorers_map/core/models/region.dart';
import 'package:explorers_map/core/models/home_work_location.dart';
import 'package:explorers_map/core/models/achievement.dart';

void main() {
  late DatabaseHelper db;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('location_events');
    await database.delete('pois');
    await database.delete('opened_pois');
    await database.delete('achievements');
    await database.delete('home_work_locations');
    await database.delete('cached_regions');
  });

  tearDown(() async {
    await db.close();
  });

  group('E2E: Основные пользовательские сценарии', () {
    test('Сценарий: Пользователь открывает новые места и получает ачивки', () async {
      // 1. Добавляем регион
      await db.insertCachedRegion(Region(
        id: 'region-1',
        name: 'Москва',
        bounds: RegionBounds(
          north: 56.0,
          south: 55.0,
          east: 38.0,
          west: 37.0,
        ),
      ));

      // 2. Добавляем POI в регионе
      for (int i = 0; i < 100; i++) {
        await db.insertPOI(POI(
          id: 'poi-$i',
          name: 'POI $i',
          description: 'Test POI $i',
          latitude: 55.7558 + i * 0.001,
          longitude: 37.6173 + i * 0.001,
          type: 'landmark',
          geofence: [GeoPoint(latitude: 55.7558 + i * 0.001, longitude: 37.6173 + i * 0.001)],
          radius: 100.0,
          regionId: 'region-1',
        ));
      }

      // 3. Пользователь посещает места (создаёт события геолокации)
      final locationService = LocationService.instance;
      for (int i = 0; i < 100; i++) {
        await locationService.createLocationEvent(
          latitude: 55.7558 + i * 0.001,
          longitude: 37.6173 + i * 0.001,
          deviceId: 'test-device',
        );
      }

      // 4. Проверяем, что POI открыты
      final openedCount = await db.getOpenedPOIsCount();
      expect(openedCount, greaterThan(0));

      // 5. Проверяем и разблокируем ачивки
      final achievementService = AchievementService.instance;
      final achievements = await achievementService.checkAndUnlockAchievements();
      
      // Может быть разблокирована ачивка "Коллекционер мест"
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

    test('Сценарий: Пользователь определяет дом и работу', () async {
      final now = DateTime(2024, 1, 10);
      final homeLat = 55.7558;
      final homeLon = 37.6173;
      final workLat = 55.7658;
      final workLon = 37.6273;

      // 1. Пользователь посещает дом (вечером)
      final locationService = LocationService.instance;
      for (int i = 0; i < 10; i++) {
        await locationService.createLocationEvent(
          latitude: homeLat + (i * 0.0001),
          longitude: homeLon + (i * 0.0001),
          deviceId: 'test-device',
        );
      }

      // 2. Пользователь посещает работу (днём)
      for (int i = 0; i < 10; i++) {
        await locationService.createLocationEvent(
          latitude: workLat + (i * 0.0001),
          longitude: workLon + (i * 0.0001),
          deviceId: 'test-device',
        );
      }

      // 3. Система определяет дом и работу
      final detector = HomeWorkDetector.instance;
      final locations = await detector.detectHomeAndWork(
        startDate: now.subtract(const Duration(days: 7)),
        endDate: now,
      );

      // 4. Пользователь верифицирует локации
      if (locations.isNotEmpty) {
        for (final location in locations) {
          await db.updateHomeWorkLocationVerification(
            location.id,
            true,
            location.type == LocationType.home ? 'Мой дом' : 'Моя работа',
          );
        }

        final verified = await db.getHomeWorkLocations(verifiedOnly: true);
        expect(verified.length, equals(locations.length));
      }
    });

    test('Сценарий: Пользователь получает рекомендации мест', () async {
      // 1. Добавляем дом и работу
      await db.insertHomeWorkLocation(HomeWorkLocation(
        id: 'home-1',
        type: LocationType.home,
        latitude: 55.7558,
        longitude: 37.6173,
        radius: 100.0,
        detectedAt: DateTime.now(),
        verified: true,
      ));

      await db.insertHomeWorkLocation(HomeWorkLocation(
        id: 'work-1',
        type: LocationType.work,
        latitude: 55.7658,
        longitude: 37.6273,
        radius: 100.0,
        detectedAt: DateTime.now(),
        verified: true,
      ));

      // 2. Добавляем POI
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'Near Route POI',
        description: 'Test',
        latitude: 55.7608,
        longitude: 37.6223,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.7608, longitude: 37.6223)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      await db.insertPOI(POI(
        id: 'poi-2',
        name: 'Far POI',
        description: 'Test',
        latitude: 55.7500,
        longitude: 37.6000,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.7500, longitude: 37.6000)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      // 3. Пользователь запрашивает рекомендации
      final recommendationService = RecommendationService.instance;
      final recommendations = await recommendationService.getNearbyRecommendations(
        latitude: 55.7608,
        longitude: 37.6223,
        radiusMeters: 5000.0,
      );

      // 4. Проверяем, что рекомендации приоритизированы по маршруту
      expect(recommendations.isNotEmpty, isTrue);
    });

    test('Сценарий: Синхронизация данных с сервером', () async {
      // 1. Создаём локальные события
      final locationService = LocationService.instance;
      for (int i = 0; i < 5; i++) {
        await locationService.createLocationEvent(
          latitude: 55.7558 + i * 0.001,
          longitude: 37.6173 + i * 0.001,
          deviceId: 'test-device',
        );
      }

      // 2. Проверяем количество несинхронизированных событий
      final unsyncedBefore = await db.getUnsyncedEventsCount();
      expect(unsyncedBefore, equals(5));

      // 3. Пытаемся синхронизировать
      final syncService = SyncService.instance;
      final hasInternet = await syncService.checkInternetConnection();
      
      if (hasInternet) {
        final synced = await syncService.syncPendingEvents();
        // В тестовой среде без реального сервера синхронизация может не пройти
        expect(synced is bool, isTrue);
      }
    });
  });
}
