import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/recommendation_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/poi.dart';
import 'package:explorers_map/core/models/home_work_location.dart';

void main() {
  late DatabaseHelper db;
  late RecommendationService service;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    service = RecommendationService.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('pois');
    await database.delete('opened_pois');
    await database.delete('home_work_locations');
  });

  tearDown(() async {
    await db.close();
  });

  group('RecommendationService', () {
    test('получает рекомендации POI рядом с пользователем', () async {
      // Добавляем POI
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

      final recommendations = await service.getNearbyRecommendations(
        latitude: 55.7558,
        longitude: 37.6173,
        radiusMeters: 1000.0,
      );

      expect(recommendations.length, equals(1));
      expect(recommendations.first.id, equals('poi-1'));
    });

    test('исключает уже открытые POI из рекомендаций', () async {
      await db.insertPOI(POI(
        id: 'poi-1',
        name: 'POI 1',
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
        name: 'POI 2',
        description: 'Test',
        latitude: 55.7560,
        longitude: 37.6175,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.7560, longitude: 37.6175)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      // Открываем один POI
      await db.markPOIOpenedSafe('poi-1');

      final recommendations = await service.getNearbyRecommendations(
        latitude: 55.7558,
        longitude: 37.6173,
        radiusMeters: 1000.0,
      );

      expect(recommendations.length, equals(1));
      expect(recommendations.first.id, equals('poi-2'));
    });

    test('приоритизирует POI вблизи маршрута дом-работа', () async {
      // Добавляем дом и работу
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

      // Добавляем POI на маршруте и вне маршрута
      await db.insertPOI(POI(
        id: 'poi-on-route',
        name: 'On Route',
        description: 'Test',
        latitude: 55.7608, // Между домом и работой
        longitude: 37.6223,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.7608, longitude: 37.6223)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      await db.insertPOI(POI(
        id: 'poi-off-route',
        name: 'Off Route',
        description: 'Test',
        latitude: 55.7500, // В стороне от маршрута
        longitude: 37.6000,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.7500, longitude: 37.6000)],
        radius: 100.0,
        regionId: 'region-1',
      ));

      final recommendations = await service.getNearbyRecommendations(
        latitude: 55.7608,
        longitude: 37.6223,
        radiusMeters: 5000.0,
      );

      // Первая рекомендация должна быть на маршруте
      expect(recommendations.isNotEmpty, isTrue);
      if (recommendations.length >= 2) {
        expect(recommendations.first.id, equals('poi-on-route'));
      }
    });
  });
}
