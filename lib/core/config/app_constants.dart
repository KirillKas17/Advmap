import 'package:latlong2/latlong.dart';

/// Константы приложения
class AppConstants {
  // Координаты по умолчанию (Москва)
  static const LatLng defaultLocation = LatLng(55.7558, 37.6173);
  
  // Максимальные значения
  static const int maxPOIsInMemory = 1000;
  static const int maxEventsInQueue = 10000;
  static const int maxDatabaseSizeMB = 500;
  
  // Интервалы очистки
  static const int cleanupIntervalDays = 7;
  static const int keepSyncedEventsDays = 30;
  
  // Радиусы поиска
  static const double defaultSearchRadiusMeters = 5000.0; // 5 км
  static const double homeWorkSearchRadiusMeters = 1000.0; // 1 км
}
