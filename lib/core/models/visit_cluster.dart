import 'package:geolocator/geolocator.dart';

/// Кластер посещений для определения дома/работы
class VisitCluster {
  final double centerLatitude;
  final double centerLongitude;
  final List<VisitPoint> points;
  final int totalVisits;
  final Duration totalDuration;
  
  /// Среднее время пребывания в кластере
  Duration get averageDuration => Duration(
    milliseconds: totalDuration.inMilliseconds ~/ totalVisits,
  );

  VisitCluster({
    required this.centerLatitude,
    required this.centerLongitude,
    required this.points,
    required this.totalVisits,
    required this.totalDuration,
  });
  
  /// Вычисляет расстояние до кластера в метрах
  double distanceTo(double lat, double lon) {
    return Geolocator.distanceBetween(
      centerLatitude,
      centerLongitude,
      lat,
      lon,
    );
  }
}

/// Точка посещения
class VisitPoint {
  final double latitude;
  final double longitude;
  final DateTime arrivalTime;
  final DateTime? departureTime;
  
  Duration get duration {
    if (departureTime == null) return Duration.zero;
    return departureTime!.difference(arrivalTime);
  }

  VisitPoint({
    required this.latitude,
    required this.longitude,
    required this.arrivalTime,
    this.departureTime,
  });
}
