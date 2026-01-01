/// Конфигурация приложения
class AppConfig {
  // Интервалы фонового отслеживания (в минутах)
  static const int defaultLocationUpdateInterval = 15;
  static const int batterySavingLocationUpdateInterval = 30;
  
  // Радиус геозон по умолчанию (в метрах)
  static const double defaultGeofenceRadius = 100.0;
  
  // Минимальное время для определения дома/работы (в минутах)
  static const int minStayDurationForHomeWork = 30;
  
  // Пороги для кластеризации
  static const double dbscanEpsilon = 0.001; // ~111 метров
  static const int dbscanMinPoints = 5;
  
  // Временные окна для определения дома/работы
  static const int homeStartHour = 20; // 20:00
  static const int homeEndHour = 8; // 08:00
  static const int workStartHour = 10; // 10:00
  static const int workEndHour = 18; // 18:00
  
  // URL сервера
  static const String apiBaseUrl = 'https://api.explorersmap.com';
  
  // Таймауты
  static const Duration syncTimeout = Duration(seconds: 30);
  static const Duration locationTimeout = Duration(seconds: 10);
}
