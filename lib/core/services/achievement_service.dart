import '../database/database_helper.dart';
import '../models/achievement.dart';
import '../models/home_work_location.dart';
import '../models/poi.dart';
import '../utils/logger.dart';
import 'package:geolocator/geolocator.dart';

/// Сервис для работы с достижениями
class AchievementService {
  static final AchievementService instance = AchievementService._internal();
  AchievementService._internal();

  /// Проверяет условия ачивок и разблокирует их при выполнении
  Future<List<Achievement>> checkAndUnlockAchievements() async {
    final unlockedAchievements = <Achievement>[];
    
    try {
      // Проверяем различные типы ачивок
      final db = DatabaseHelper.instance;
      
      // Ачивка: Мастер маршрута (дом-работа 100 раз)
      final routeMaster = await _checkRouteMasterAchievement(db);
      if (routeMaster != null) {
        unlockedAchievements.add(routeMaster);
      }
      
      // Ачивка: Ночной исследователь (10 новых мест в радиусе 1 км от дома)
      final nightExplorer = await _checkNightExplorerAchievement(db);
      if (nightExplorer != null) {
        unlockedAchievements.add(nightExplorer);
      }
      
      // Ачивка: Первый исследователь (открыть POI первым)
      final firstExplorer = await _checkFirstExplorerAchievement(db);
      if (firstExplorer != null) {
        unlockedAchievements.add(firstExplorer);
      }
      
      // Ачивка: Путешественник (открыть 10 регионов)
      final traveler = await _checkTravelerAchievement(db);
      if (traveler != null) {
        unlockedAchievements.add(traveler);
      }
      
      // Ачивка: Коллекционер мест (открыть 100 POI)
      final collector = await _checkCollectorAchievement(db);
      if (collector != null) {
        unlockedAchievements.add(collector);
      }
      
    } catch (e, stackTrace) {
      Logger.error('Ошибка проверки ачивок', e, stackTrace);
    }
    
    return unlockedAchievements;
  }

  /// Проверяет ачивку "Мастер маршрута" (дом-работа 100 раз)
  Future<Achievement?> _checkRouteMasterAchievement(DatabaseHelper db) async {
    final locations = await db.getHomeWorkLocations(verifiedOnly: true);
    
    if (locations.length < 2) {
      return null;
    }
    
    final home = locations.firstWhere(
      (l) => l.type == LocationType.home,
      orElse: () => locations.first,
    );
    final work = locations.firstWhere(
      (l) => l.type == LocationType.work,
      orElse: () => locations.last,
    );
    
    // Подсчитываем количество поездок дом-работа за последние 30 дней
    final thirtyDaysAgo = DateTime.now().subtract(const Duration(days: 30));
    final events = await db.getUnsyncedEvents(limit: 10000);
    final syncedEvents = await db.getUnsyncedEvents(limit: 10000); // TODO: Добавить метод для синхронизированных
    
    int routeCount = 0;
    bool wasAtHome = false;
    
    for (final event in events) {
      final distanceToHome = Geolocator.distanceBetween(
        home.latitude,
        home.longitude,
        event.latitude,
        event.longitude,
      );
      final distanceToWork = Geolocator.distanceBetween(
        work.latitude,
        work.longitude,
        event.latitude,
        event.longitude,
      );
      
      if (distanceToHome < home.radius) {
        wasAtHome = true;
      } else if (distanceToWork < work.radius && wasAtHome) {
        routeCount++;
        wasAtHome = false;
      }
    }
    
    if (routeCount >= 100) {
      return Achievement(
        id: 'route_master',
        title: 'Мастер маршрута',
        description: 'Прошёл путь дом-работа 100 раз',
        category: 'daily',
        unlockedAt: DateTime.now(),
      );
    }
    
    return null;
  }

  /// Проверяет ачивку "Ночной исследователь" (10 новых мест в радиусе 1 км от дома)
  Future<Achievement?> _checkNightExplorerAchievement(DatabaseHelper db) async {
    final locations = await db.getHomeWorkLocations(verifiedOnly: true);
    final home = locations.firstWhere(
      (l) => l.type == LocationType.home,
      orElse: () => locations.isNotEmpty ? locations.first : null,
    );
    
    if (home == null) return null;
    
    // Получаем открытые POI в радиусе 1 км от дома
    final nearbyPOIs = await db.getPOIsNearby(
      latitude: home.latitude,
      longitude: home.longitude,
      radiusMeters: 1000,
    );
    
    // Фильтруем только те, что открыты ночью (20:00-08:00)
    int nightOpenedCount = 0;
    final openedPOIs = await db.getOpenedPOIIds();
    
    for (final poi in nearbyPOIs) {
      if (openedPOIs.contains(poi.id)) {
        // TODO: Проверить время открытия POI
        nightOpenedCount++;
      }
    }
    
    if (nightOpenedCount >= 10) {
      return Achievement(
        id: 'night_explorer',
        title: 'Ночной исследователь',
        description: 'Обнаружил 10 новых мест в радиусе 1 км от дома ночью',
        category: 'daily',
        unlockedAt: DateTime.now(),
      );
    }
    
    return null;
  }

  /// Проверяет ачивку "Первый исследователь" (открыть POI первым)
  Future<Achievement?> _checkFirstExplorerAchievement(DatabaseHelper db) async {
    // TODO: Требует интеграции с сервером для проверки, был ли POI открыт кем-то раньше
    return null;
  }

  /// Проверяет ачивку "Путешественник" (открыть 10 регионов)
  Future<Achievement?> _checkTravelerAchievement(DatabaseHelper db) async {
    final regions = await db.getCachedRegions();
    
    if (regions.length >= 10) {
      return Achievement(
        id: 'traveler',
        title: 'Путешественник',
        description: 'Открыл 10 регионов',
        category: 'travel',
        unlockedAt: DateTime.now(),
      );
    }
    
    return null;
  }

  /// Проверяет ачивку "Коллекционер мест" (открыть 100 POI)
  Future<Achievement?> _checkCollectorAchievement(DatabaseHelper db) async {
    final openedCount = await db.getOpenedPOIsCount();
    
    if (openedCount >= 100) {
      return Achievement(
        id: 'collector',
        title: 'Коллекционер мест',
        description: 'Открыл 100 точек интереса',
        category: 'exploration',
        unlockedAt: DateTime.now(),
      );
    }
    
    return null;
  }

  /// Сохраняет разблокированную ачивку в БД
  Future<void> saveAchievement(Achievement achievement) async {
    // TODO: Реализовать сохранение ачивок в БД
    Logger.info('Ачивка разблокирована: ${achievement.title}');
  }

  /// Получает все разблокированные ачивки
  Future<List<Achievement>> getUnlockedAchievements() async {
    // TODO: Реализовать получение ачивок из БД
    return [];
  }
}
