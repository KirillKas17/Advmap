import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/region_detector.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/region.dart';

void main() {
  late DatabaseHelper db;
  late RegionDetector detector;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    detector = RegionDetector.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('cached_regions');
  });

  tearDown(() async {
    await db.close();
  });

  group('RegionDetector', () {
    test('определяет регион по координатам', () async {
      // Добавляем регион в БД
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

      // Точка внутри региона
      final regionId = await detector.detectRegion(55.5, 37.5);
      expect(regionId, equals('region-1'));
    });

    test('возвращает null если регион не найден', () async {
      final regionId = await detector.detectRegion(55.5, 37.5);
      expect(regionId, isNull);
    });

    test('возвращает null если точка слишком далеко от регионов', () async {
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

      // Точка очень далеко (более 50 км)
      final regionId = await detector.detectRegion(60.0, 50.0);
      expect(regionId, isNull);
    });

    test('находит ближайший регион если точка не в границах', () async {
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

      // Точка близко к региону (в пределах 50 км)
      final regionId = await detector.detectRegion(55.1, 37.1);
      expect(regionId, equals('region-1'));
    });
  });
}
