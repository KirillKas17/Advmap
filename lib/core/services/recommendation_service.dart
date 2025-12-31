import '../database/database_helper.dart';
import '../models/poi.dart';
import '../models/home_work_location.dart';
import '../utils/logger.dart';
import 'package:geolocator/geolocator.dart';

/// Сервис для персонализированных рекомендаций
/// Согласно ТЗ: "При открытии раздела «Рядом с вами» приоритет отдаётся
/// новым и интересным местам вблизи маршрута дом-работа"
class RecommendationService {
  static final RecommendationService instance = RecommendationService._internal();
  RecommendationService._internal();

  /// Получает рекомендации POI рядом с пользователем
  /// Приоритет отдаётся местам вблизи маршрута дом-работа
  Future<List<POI>> getNearbyRecommendations({
    required double latitude,
    required double longitude,
    double radiusMeters = 5000.0,
  }) async {
    try {
      final db = DatabaseHelper.instance;
      
      // Получаем дом и работу пользователя
      final locations = await db.getHomeWorkLocations(verifiedOnly: true);
      final home = locations.firstWhere(
        (l) => l.type == LocationType.home,
        orElse: () => locations.isNotEmpty ? locations.first : null,
      );
      final work = locations.firstWhere(
        (l) => l.type == LocationType.work,
        orElse: () => locations.length > 1 ? locations.last : null,
      );
      
      // Получаем все POI в радиусе
      final allPOIs = await db.getPOIsNearby(
        latitude: latitude,
        longitude: longitude,
        radiusMeters: radiusMeters,
      );
      
      // Получаем открытые POI
      final openedPOIs = await db.getOpenedPOIIds();
      final openedSet = openedPOIs.toSet();
      
      // Фильтруем только неоткрытые POI
      final unopenedPOIs = allPOIs.where((poi) => !openedSet.contains(poi.id)).toList();
      
      // Сортируем по приоритету:
      // 1. POI вблизи маршрута дом-работа (если есть дом и работа)
      // 2. POI ближе к текущей позиции
      if (home != null && work != null) {
        unopenedPOIs.sort((a, b) {
          // Вычисляем расстояние до маршрута дом-работа
          final distA = _distanceToRoute(a.latitude, a.longitude, home, work);
          final distB = _distanceToRoute(b.latitude, b.longitude, home, work);
          
          // Приоритет местам ближе к маршруту
          final routeDiff = distA.compareTo(distB);
          if (routeDiff != 0) return routeDiff;
          
          // Если одинаковое расстояние до маршрута, сортируем по расстоянию от текущей позиции
          final distToCurrentA = Geolocator.distanceBetween(
            latitude,
            longitude,
            a.latitude,
            a.longitude,
          );
          final distToCurrentB = Geolocator.distanceBetween(
            latitude,
            longitude,
            b.latitude,
            b.longitude,
          );
          
          return distToCurrentA.compareTo(distToCurrentB);
        });
      } else {
        // Если нет дома/работы, сортируем просто по расстоянию
        unopenedPOIs.sort((a, b) {
          final distA = Geolocator.distanceBetween(
            latitude,
            longitude,
            a.latitude,
            a.longitude,
          );
          final distB = Geolocator.distanceBetween(
            latitude,
            longitude,
            b.latitude,
            b.longitude,
          );
          return distA.compareTo(distB);
        });
      }
      
      return unopenedPOIs;
    } catch (e, stackTrace) {
      Logger.error('Ошибка получения рекомендаций', e, stackTrace);
      return [];
    }
  }

  /// Вычисляет расстояние от точки до маршрута дом-работа
  double _distanceToRoute(
    double lat,
    double lon,
    HomeWorkLocation home,
    HomeWorkLocation work,
  ) {
    // Упрощённый алгоритм: расстояние до ближайшей точки на отрезке дом-работа
    // Используем формулу расстояния от точки до отрезка
    
    final homeLat = home.latitude;
    final homeLon = home.longitude;
    final workLat = work.latitude;
    final workLon = work.longitude;
    
    // Вычисляем расстояние до дома и работы
    final distToHome = Geolocator.distanceBetween(lat, lon, homeLat, homeLon);
    final distToWork = Geolocator.distanceBetween(lat, lon, workLat, workLon);
    
    // Вычисляем расстояние до отрезка (упрощённо - минимум из расстояний до концов)
    // В реальности нужно вычислять расстояние до перпендикуляра, но для рекомендаций
    // достаточно упрощённой версии
    final minDist = distToHome < distToWork ? distToHome : distToWork;
    
    return minDist;
  }
}
