import 'package:geolocator/geolocator.dart';

/// Утилиты для работы с координатами
class CoordinateUtils {
  /// Нормализует долготу в диапазон [-180, 180]
  static double normalizeLongitude(double lon) {
    while (lon > 180) lon -= 360;
    while (lon < -180) lon += 360;
    return lon;
  }

  /// Вычисляет расстояние между двумя точками (в метрах)
  static double distanceBetween(
    double lat1,
    double lon1,
    double lat2,
    double lon2,
  ) {
    return Geolocator.distanceBetween(lat1, lon1, lat2, lon2);
  }

  /// Проверяет, находится ли точка в bounding box
  static bool isPointInBoundingBox(
    double lat,
    double lon,
    double minLat,
    double maxLat,
    double minLon,
    double maxLon,
  ) {
    return lat >= minLat &&
        lat <= maxLat &&
        lon >= minLon &&
        lon <= maxLon;
  }

  /// Вычисляет приближённое расстояние в метрах для быстрой фильтрации
  /// Использует упрощённую формулу для предварительной фильтрации
  static double approximateDistance(
    double lat1,
    double lon1,
    double lat2,
    double lon2,
  ) {
    const double metersPerDegreeLat = 111000.0;
    final double metersPerDegreeLon = 111000.0 * (lat1.abs() / 90.0 + 0.1);
    
    final latDiff = (lat2 - lat1).abs() * metersPerDegreeLat;
    final lonDiff = (lon2 - lon1).abs() * metersPerDegreeLon;
    
    return (latDiff * latDiff + lonDiff * lonDiff).sqrt();
  }
}
