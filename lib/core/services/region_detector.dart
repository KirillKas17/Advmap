import '../database/database_helper.dart';
import '../models/region.dart';
import '../config/app_constants.dart';
import 'dart:math';

/// Сервис для определения региона по координатам
class RegionDetector {
  static final RegionDetector instance = RegionDetector._internal();
  RegionDetector._internal();

  /// Определяет регион по координатам на основе загруженных регионов
  Future<String?> detectRegion(double latitude, double longitude) async {
    final db = DatabaseHelper.instance;
    
    // Получаем все загруженные регионы из БД
    final regions = await db.getCachedRegions();
    
    if (regions.isEmpty) {
      return null;
    }

    // Проверяем, попадает ли точка в границы какого-либо региона
    for (final region in regions) {
      if (_isPointInBounds(latitude, longitude, region.bounds)) {
        return region.id;
      }
    }

    // Если не попали ни в один регион, возвращаем ближайший (если он не слишком далеко)
    final nearestRegionId = _findNearestRegion(latitude, longitude, regions);
    
    // Проверяем, не слишком ли далеко ближайший регион
    if (nearestRegionId != null) {
      final nearestRegion = regions.firstWhere(
        (r) => r.id == nearestRegionId,
      );
      final centerLat = (nearestRegion.bounds.north + nearestRegion.bounds.south) / 2;
      final centerLon = (nearestRegion.bounds.east + nearestRegion.bounds.west) / 2;
      final distance = _calculateDistance(latitude, longitude, centerLat, centerLon);
      
      // Если ближайший регион дальше 50 км, не возвращаем его
      if (distance > 50000) {
        return null;
      }
    }
    
    return nearestRegionId;
  }

  /// Проверяет, попадает ли точка в границы региона
  bool _isPointInBounds(double lat, double lon, RegionBounds bounds) {
    return lat >= bounds.south &&
        lat <= bounds.north &&
        lon >= bounds.west &&
        lon <= bounds.east;
  }

  /// Находит ближайший регион к точке
  String? _findNearestRegion(
    double lat,
    double lon,
    List<Region> regions,
  ) {
    if (regions.isEmpty) return null;

    Region? nearestRegion;
    double minDistance = double.infinity;

    for (final region in regions) {
      // Вычисляем центр региона
      final centerLat = (region.bounds.north + region.bounds.south) / 2;
      final centerLon = (region.bounds.east + region.bounds.west) / 2;

      // Вычисляем расстояние до центра региона
      final distance = _calculateDistance(lat, lon, centerLat, centerLon);

      if (distance < minDistance) {
        minDistance = distance;
        nearestRegion = region;
      }
    }

    return nearestRegion?.id;
  }

  /// Вычисляет расстояние между двумя точками (упрощённая формула Гаверсинуса)
  double _calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    const double earthRadius = 6371000; // Радиус Земли в метрах
    
    final dLat = _toRadians(lat2 - lat1);
    final dLon = _toRadians(lon2 - lon1);
    
    final a = sin(dLat / 2) * sin(dLat / 2) +
        cos(_toRadians(lat1)) *
            cos(_toRadians(lat2)) *
            sin(dLon / 2) *
            sin(dLon / 2);
    
    final c = 2 * atan2(sqrt(a), sqrt(1 - a));
    
    return earthRadius * c;
  }

  double _toRadians(double degrees) {
    return degrees * (pi / 180);
  }
}
