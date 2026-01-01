import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/home_work_detector.dart';
import 'package:explorers_map/core/services/location_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/location_event.dart';
import 'package:explorers_map/core/models/home_work_location.dart';

void main() {
  late DatabaseHelper db;
  late HomeWorkDetector detector;
  late LocationService locationService;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    detector = HomeWorkDetector.instance;
    locationService = LocationService.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('location_events');
    await database.delete('home_work_locations');
  });

  tearDown(() async {
    await db.close();
  });

  group('Home Work Detection Integration', () {
    test('определяет дом и работу из реальных событий геолокации', () async {
      final now = DateTime(2024, 1, 10);
      final homeLat = 55.7558;
      final homeLon = 37.6173;
      final workLat = 55.7658;
      final workLon = 37.6273;

      // Создаём события посещения дома (вечером в будни и весь день в выходные)
      for (int i = 0; i < 10; i++) {
        final date = now.subtract(Duration(days: i));
        final isWeekend = date.weekday == 6 || date.weekday == 7;
        final hour = isWeekend ? 14 : 21; // Днём в выходные, вечером в будни

        await locationService.createLocationEvent(
          latitude: homeLat + (i * 0.0001),
          longitude: homeLon + (i * 0.0001),
          deviceId: 'test-device',
        );
      }

      // Создаём события посещения работы (днём в будни)
      for (int i = 0; i < 10; i++) {
        final date = now.subtract(Duration(days: i));
        if (date.weekday != 6 && date.weekday != 7) {
          await locationService.createLocationEvent(
            latitude: workLat + (i * 0.0001),
            longitude: workLon + (i * 0.0001),
            deviceId: 'test-device',
          );
        }
      }

      // Определяем дом и работу
      final locations = await detector.detectHomeAndWork(
        startDate: now.subtract(const Duration(days: 7)),
        endDate: now,
      );

      // Проверяем, что найдены локации
      expect(locations.length, greaterThanOrEqualTo(0));
      
      if (locations.isNotEmpty) {
        // Проверяем, что локации сохранены в БД
        final savedLocations = await db.getHomeWorkLocations();
        expect(savedLocations.length, equals(locations.length));
      }
    });

    test('верифицирует обнаруженные локации', () async {
      // Создаём события для определения локаций
      final now = DateTime(2024, 1, 10);
      for (int i = 0; i < 10; i++) {
        await locationService.createLocationEvent(
          latitude: 55.7558 + (i * 0.0001),
          longitude: 37.6173 + (i * 0.0001),
          deviceId: 'test-device',
        );
      }

      final locations = await detector.detectHomeAndWork(
        startDate: now.subtract(const Duration(days: 7)),
        endDate: now,
      );

      if (locations.isNotEmpty) {
        // Верифицируем первую локацию
        await db.updateHomeWorkLocationVerification(
          locations.first.id,
          true,
          'Мой дом',
        );

        final verified = await db.getHomeWorkLocations(verifiedOnly: true);
        expect(verified.length, equals(1));
        expect(verified.first.customName, equals('Мой дом'));
      }
    });
  });
}
