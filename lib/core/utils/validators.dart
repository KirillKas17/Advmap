/// Валидаторы для проверки данных
class Validators {
  /// Валидирует координаты широты
  static bool isValidLatitude(double latitude) {
    return latitude >= -90.0 && latitude <= 90.0;
  }

  /// Валидирует координаты долготы
  static bool isValidLongitude(double longitude) {
    return longitude >= -180.0 && longitude <= 180.0;
  }

  /// Валидирует координаты
  static bool isValidCoordinates(double latitude, double longitude) {
    return isValidLatitude(latitude) && isValidLongitude(longitude);
  }

  /// Валидирует радиус геозоны
  static bool isValidRadius(double? radius) {
    if (radius == null) return true;
    return radius > 0 && radius <= 100000; // Максимум 100 км
  }

  /// Валидирует ID
  static bool isValidId(String? id) {
    return id != null && id.isNotEmpty && id.length <= 255;
  }

  /// Валидирует название
  static bool isValidName(String? name) {
    return name != null && name.isNotEmpty && name.length <= 500;
  }

  /// Валидирует геозону (полигон)
  static bool isValidGeofence(List<dynamic> geofence) {
    if (geofence.length < 3) return false;
    
    // Проверяем, что все точки валидны
    for (final point in geofence) {
      if (point is! Map<String, dynamic>) return false;
      final lat = point['latitude'] as num?;
      final lon = point['longitude'] as num?;
      if (lat == null || lon == null) return false;
      if (!isValidCoordinates(lat.toDouble(), lon.toDouble())) return false;
    }
    
    return true;
  }
}
