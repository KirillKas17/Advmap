import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/models/region.dart';

void main() {
  group('Region', () {
    final defaultBounds = RegionBounds(
      north: 56.0,
      south: 55.0,
      east: 38.0,
      west: 37.0,
    );

    test('создаёт регион с корректными данными', () {
      final region = Region(
        id: 'region-123',
        name: 'Test Region',
        bounds: defaultBounds,
      );

      expect(region.id, equals('region-123'));
      expect(region.name, equals('Test Region'));
      expect(region.bounds.north, equals(56.0));
      expect(region.bounds.south, equals(55.0));
    });

    test('создаёт регион с датами загрузки', () {
      final downloadedAt = DateTime(2024, 1, 1);
      final lastUpdated = DateTime(2024, 1, 2);
      final region = Region(
        id: 'region-123',
        name: 'Test Region',
        bounds: defaultBounds,
        downloadedAt: downloadedAt,
        lastUpdated: lastUpdated,
      );

      expect(region.downloadedAt, equals(downloadedAt));
      expect(region.lastUpdated, equals(lastUpdated));
    });

    test('toJson и fromJson работают корректно', () {
      final original = Region(
        id: 'region-123',
        name: 'Test Region',
        bounds: defaultBounds,
        downloadedAt: DateTime(2024, 1, 1),
        lastUpdated: DateTime(2024, 1, 2),
      );

      final json = original.toJson();
      final restored = Region.fromJson(json);

      expect(restored.id, equals(original.id));
      expect(restored.name, equals(original.name));
      expect(restored.bounds.north, equals(original.bounds.north));
      expect(restored.bounds.south, equals(original.bounds.south));
      expect(restored.bounds.east, equals(original.bounds.east));
      expect(restored.bounds.west, equals(original.bounds.west));
    });
  });

  group('RegionBounds', () {
    test('создаёт границы с корректными данными', () {
      final bounds = RegionBounds(
        north: 56.0,
        south: 55.0,
        east: 38.0,
        west: 37.0,
      );

      expect(bounds.north, equals(56.0));
      expect(bounds.south, equals(55.0));
      expect(bounds.east, equals(38.0));
      expect(bounds.west, equals(37.0));
    });

    test('toJson и fromJson работают корректно', () {
      final original = RegionBounds(
        north: 56.0,
        south: 55.0,
        east: 38.0,
        west: 37.0,
      );

      final json = original.toJson();
      final restored = RegionBounds.fromJson(json);

      expect(restored.north, equals(original.north));
      expect(restored.south, equals(original.south));
      expect(restored.east, equals(original.east));
      expect(restored.west, equals(original.west));
    });
  });
}
