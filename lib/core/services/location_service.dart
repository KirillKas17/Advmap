import 'package:geolocator/geolocator.dart';
import 'package:location/location.dart' as loc;
import 'package:shared_preferences/shared_preferences.dart';

import '../config/app_config.dart';
import '../config/app_constants.dart';
import '../models/poi.dart';
import '../database/database_helper.dart';
import '../models/location_event.dart';
import '../utils/validators.dart';
import '../utils/logger.dart';
import 'region_detector.dart';
import 'dart:io';

/// Сервис для работы с геолокацией
class LocationService {
  static final LocationService instance = LocationService._internal();
  LocationService._internal();

  final loc.Location _location = loc.Location();
  Position? _lastKnownPosition;
  bool _isTracking = false;

  /// Проверяет и запрашивает разрешения на геолокацию
  Future<bool> checkAndRequestPermissions() async {
    bool serviceEnabled = await _location.serviceEnabled();
    if (!serviceEnabled) {
      serviceEnabled = await _location.requestService();
      if (!serviceEnabled) {
        return false;
      }
    }

    loc.PermissionStatus permission = await _location.hasPermission();
    if (permission == loc.PermissionStatus.denied) {
      permission = await _location.requestPermission();
      if (permission != loc.PermissionStatus.granted) {
        return false;
      }
    }

    // Для фонового отслеживания требуется разрешение "Всегда"
    if (permission == loc.PermissionStatus.granted) {
      // Проверяем, есть ли разрешение на фоновое отслеживание
      final prefs = await SharedPreferences.getInstance();
      final backgroundEnabled = prefs.getBool('background_location_enabled') ?? false;
      
      if (backgroundEnabled && Platform.isAndroid) {
        // На Android может потребоваться дополнительное разрешение
        final androidPermission = await Geolocator.checkPermission();
        if (androidPermission != LocationPermission.always) {
          await Geolocator.requestPermission();
        }
      }
    }

    return permission == loc.PermissionStatus.granted ||
        permission == loc.PermissionStatus.grantedLimited;
  }

  /// Получает текущую позицию
  Future<Position?> getCurrentPosition({
    LocationAccuracy accuracy = LocationAccuracy.low,
  }) async {
    try {
      final hasPermission = await checkAndRequestPermissions();
      if (!hasPermission) {
        return null;
      }

      _lastKnownPosition = await Geolocator.getCurrentPosition(
        desiredAccuracy: accuracy,
        timeLimit: AppConfig.locationTimeout,
      );

      return _lastKnownPosition;
    } catch (e) {
      return null;
    }
  }

  /// Получает последнюю известную позицию
  Future<Position?> getLastKnownPosition() async {
    try {
      _lastKnownPosition = await Geolocator.getLastKnownPosition();
      return _lastKnownPosition;
    } catch (e) {
      return null;
    }
  }

  /// Проверяет, попадает ли позиция в геозону какого-либо POI
  /// Оптимизированная версия с фильтрацией по региону и радиусу
  Future<String?> checkPOIGeofence(double latitude, double longitude) async {
    // Валидация координат
    if (!Validators.isValidCoordinates(latitude, longitude)) {
      Logger.warning('Некорректные координаты: $latitude, $longitude');
      return null;
    }

    // Сначала определяем регион для фильтрации
    String? regionId;
    try {
      regionId = await detectRegion(latitude, longitude);
    } catch (e) {
      Logger.error('Ошибка определения региона', e);
    }

    // Ищем POI в радиусе от текущей позиции
    final searchRadius = AppConstants.defaultSearchRadiusMeters;
    final db = DatabaseHelper.instance;
    final nearbyPOIs = await db.getPOIsNearby(
      latitude: latitude,
      longitude: longitude,
      radiusMeters: searchRadius,
      regionId: regionId,
    );

    // Проверяем попадание в геозоны найденных POI
    for (final poi in nearbyPOIs) {
      if (poi.isPointInGeofence(latitude, longitude)) {
        return poi.id;
      }
    }

    return null;
  }

  /// Определяет регион по координатам
  Future<String?> detectRegion(double latitude, double longitude) async {
    final detector = RegionDetector.instance;
    return await detector.detectRegion(latitude, longitude);
  }

  /// Создаёт событие геолокации и сохраняет в БД
  Future<String?> createLocationEvent({
    required double latitude,
    required double longitude,
    required String deviceId,
  }) async {
    // Валидация входных данных
    if (!Validators.isValidCoordinates(latitude, longitude)) {
      Logger.warning('Попытка создать событие с некорректными координатами');
      return null;
    }

    if (!Validators.isValidId(deviceId)) {
      Logger.warning('Попытка создать событие с некорректным deviceId');
      return null;
    }

    try {
      final poiId = await checkPOIGeofence(latitude, longitude);
      final regionId = await detectRegion(latitude, longitude);

      // Если попали в POI, отмечаем его как открытый (с транзакцией для избежания race condition)
      if (poiId != null) {
        final db = DatabaseHelper.instance;
        await db.markPOIOpenedSafe(poiId);
      }

      final event = LocationEvent(
        id: '${DateTime.now().millisecondsSinceEpoch}_${deviceId.substring(0, 8)}',
        latitude: latitude,
        longitude: longitude,
        timestamp: DateTime.now(),
        poiId: poiId,
        regionId: regionId,
        deviceId: deviceId,
        synced: false,
      );

      await DatabaseHelper.instance.insertLocationEvent(event);
      return event.id;
    } catch (e, stackTrace) {
      Logger.error('Ошибка создания события геолокации', e, stackTrace);
      return null;
    }
  }

  /// Включает/выключает фоновое отслеживание
  Future<void> setBackgroundTrackingEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('background_location_enabled', enabled);
    _isTracking = enabled;
  }

  /// Проверяет, включено ли фоновое отслеживание
  Future<bool> isBackgroundTrackingEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool('background_location_enabled') ?? false;
  }

  /// Получает настройку точности геолокации
  Future<LocationAccuracy> getLocationAccuracy() async {
    final prefs = await SharedPreferences.getInstance();
    final accuracyString = prefs.getString('location_accuracy') ?? 'low';
    
    switch (accuracyString) {
      case 'high':
        return LocationAccuracy.high;
      case 'medium':
        return LocationAccuracy.medium;
      case 'low':
      default:
        return LocationAccuracy.low;
    }
  }

  /// Устанавливает точность геолокации
  Future<void> setLocationAccuracy(LocationAccuracy accuracy) async {
    final prefs = await SharedPreferences.getInstance();
    String accuracyString;
    switch (accuracy) {
      case LocationAccuracy.high:
        accuracyString = 'high';
        break;
      case LocationAccuracy.medium:
        accuracyString = 'medium';
        break;
      default:
        accuracyString = 'low';
    }
    await prefs.setString('location_accuracy', accuracyString);
  }
}
