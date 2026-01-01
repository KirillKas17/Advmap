import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/home_work_detector.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/home_work_location.dart';
import 'package:explorers_map/core/models/location_event.dart';

void main() {
  late DatabaseHelper db;
  late HomeWorkDetector detector;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    detector = HomeWorkDetector.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('location_events');
    await database.delete('home_work_locations');
  });

  tearDown(() async {
    await db.close();
  });

  group('HomeWorkDetector', () {
    test('определяет дом и работу из истории посещений', () async {
      final now = DateTime(2024, 1, 10);
      final homeLat = 55.7558;
      final homeLon = 37.6173;
      final workLat = 55.7658;
      final workLon = 37.6273;

      // Создаём события посещения дома (вечером)
      for (int i = 0; i < 10; i++) {
        final arrivalTime = DateTime(now.year, now.month, now.day - i, 21, 0);
        await db.insertLocationEvent(LocationEvent(
          id: 'home-event-$i',
          latitude: homeLat + (i * 0.0001),
          longitude: homeLon + (i * 0.0001),
          timestamp: arrivalTime,
          deviceId: 'device-123',
        ));
      }

      // Создаём события посещения работы (днём в будни)
      for (int i = 0; i < 10; i++) {
        final arrivalTime = DateTime(now.year, now.month, now.day - i, 11, 0);
        await db.insertLocationEvent(LocationEvent(
          id: 'work-event-$i',
          latitude: workLat + (i * 0.0001),
          longitude: workLon + (i * 0.0001),
          timestamp: arrivalTime,
          deviceId: 'device-123',
        ));
      }

      final locations = await detector.detectHomeAndWork(
        startDate: now.subtract(const Duration(days: 7)),
        endDate: now,
      );

      expect(locations.length, greaterThan(0));
    });

    test('возвращает пустой список при недостаточном количестве данных', () async {
      final now = DateTime(2024, 1, 10);
      
      // Добавляем только 2 события (недостаточно для кластеризации)
      await db.insertLocationEvent(LocationEvent(
        id: 'event-1',
        latitude: 55.7558,
        longitude: 37.6173,
        timestamp: now,
        deviceId: 'device-123',
      ));

      final locations = await detector.detectHomeAndWork(
        startDate: now.subtract(const Duration(days: 7)),
        endDate: now,
      );

      expect(locations.isEmpty, isTrue);
    });

    test('isReadyForDetection возвращает false при недостаточных данных', () async {
      final isReady = await detector.isReadyForDetection();
      expect(isReady, isFalse);
    });

    test('isTraveling возвращает false при недостаточных данных', () async {
      final isTraveling = await detector.isTraveling();
      expect(isTraveling, isFalse);
    });
  });
}
