import 'package:json_annotation/json_annotation.dart';

part 'poi.g.dart';

/// Точка интереса (POI)
@JsonSerializable()
class POI {
  final String id;
  final String name;
  final String description;
  final double latitude;
  final double longitude;
  
  /// Тип POI: landmark, nature, city, district, etc.
  final String type;
  
  /// Геозона POI (полигон координат)
  final List<GeoPoint> geofence;
  
  /// Радиус геозоны в метрах (для окружностей)
  final double? radius;
  
  /// ID региона, к которому относится POI
  final String regionId;
  
  /// Иконка для отображения на карте
  final String? iconUrl;
  
  /// Категория ачивки, связанной с этим POI
  final String? achievementCategory;

  POI({
    required this.id,
    required this.name,
    required this.description,
    required this.latitude,
    required this.longitude,
    required this.type,
    required this.geofence,
    this.radius,
    required this.regionId,
    this.iconUrl,
    this.achievementCategory,
  });

  factory POI.fromJson(Map<String, dynamic> json) => _$POIFromJson(json);
  Map<String, dynamic> toJson() => _$POIToJson(this);
  
  /// Проверяет, попадает ли точка в геозону POI
  bool isPointInGeofence(double lat, double lon) {
    // Если есть радиус, используем окружность
    if (radius != null) {
      final distance = _calculateDistance(latitude, longitude, lat, lon);
      return distance <= radius!;
    }
    
    // Иначе проверяем попадание в полигон
    return _isPointInPolygon(lat, lon, geofence);
  }
  
  /// Вычисляет расстояние между двумя точками (в метрах)
  double _calculateDistance(double lat1, double lon1, double lat2, double lon2) {
    return Geolocator.distanceBetween(lat1, lon1, lat2, lon2);
  }
  
  /// Проверяет, находится ли точка внутри полигона (алгоритм Ray Casting)
  bool _isPointInPolygon(double lat, double lon, List<GeoPoint> polygon) {
    if (polygon.length < 3) return false;
    
    bool inside = false;
    for (int i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
      final xi = polygon[i].latitude;
      final yi = polygon[i].longitude;
      final xj = polygon[j].latitude;
      final yj = polygon[j].longitude;
      
      // Проверяем пересечение луча с ребром полигона
      final intersect = ((yi > lon) != (yj > lon)) &&
          (lat < (xj - xi) * (lon - yi) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }
}

/// Точка геозоны
@JsonSerializable()
class GeoPoint {
  final double latitude;
  final double longitude;

  GeoPoint({
    required this.latitude,
    required this.longitude,
  });

  factory GeoPoint.fromJson(Map<String, dynamic> json) => _$GeoPointFromJson(json);
  Map<String, dynamic> toJson() => _$GeoPointToJson(this);
}
