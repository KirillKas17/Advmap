import 'package:workmanager/workmanager.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:io';

import '../config/app_config.dart';
import 'location_service.dart';
import '../database/database_helper.dart';
import 'sync_service.dart';
import '../utils/logger.dart';
import 'package:device_info_plus/device_info_plus.dart';

/// Top-level функция для фонового воркера
@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    try {
      if (task == "locationTrackingTask") {
        await _performBackgroundLocationTracking();
        return Future.value(true);
      }
      return Future.value(false);
  } catch (e, stackTrace) {
    Logger.error('Ошибка в фоновом воркере', e, stackTrace);
    return Future.value(false);
  }
});
}

/// Выполняет фоновое отслеживание геолокации
Future<void> _performBackgroundLocationTracking() async {
  // Проверяем, включено ли фоновое отслеживание
  final prefs = await SharedPreferences.getInstance();
  final enabled = prefs.getBool('background_location_enabled') ?? false;
  
  if (!enabled) {
    return;
  }

  // Проверяем разрешения
  final locationService = LocationService.instance;
  final hasPermission = await locationService.checkAndRequestPermissions();
  if (!hasPermission) {
    return;
  }

  // Получаем текущую позицию с низкой точностью для экономии батареи
  final accuracy = await locationService.getLocationAccuracy();
  final position = await locationService.getCurrentPosition(accuracy: accuracy);
  
  if (position == null) {
    return;
  }

  // Получаем device ID
  final deviceId = await _getDeviceId();

  // Создаём событие геолокации
  await locationService.createLocationEvent(
    latitude: position.latitude,
    longitude: position.longitude,
    deviceId: deviceId,
  );

  // Пытаемся синхронизировать неотправленные события
  final syncService = SyncService.instance;
  final hasInternet = await syncService.checkInternetConnection();
  if (hasInternet) {
    await syncService.syncPendingEvents();
  }

  return;
}

/// Получает уникальный ID устройства
Future<String> _getDeviceId() async {
  final prefs = await SharedPreferences.getInstance();
  String? deviceId = prefs.getString('device_id');
  
  if (deviceId == null) {
    final deviceInfo = DeviceInfoPlugin();
    if (Platform.isAndroid) {
      final androidInfo = await deviceInfo.androidInfo;
      deviceId = androidInfo.id;
    } else if (Platform.isIOS) {
      final iosInfo = await deviceInfo.iosInfo;
      deviceId = iosInfo.identifierForVendor;
    } else {
      deviceId = DateTime.now().millisecondsSinceEpoch.toString();
    }
    await prefs.setString('device_id', deviceId);
  }
  
  return deviceId;
}
