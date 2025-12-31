import 'package:workmanager/workmanager.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../config/app_config.dart';
import 'background_callback.dart';

/// Сервис для фонового отслеживания геолокации
class BackgroundService {
  static const String taskName = "locationTrackingTask";

  /// Инициализация фонового сервиса
  static Future<void> initialize() async {
    await Workmanager().initialize(
      callbackDispatcher,
      isInDebugMode: false,
    );
  }

  /// Регистрирует периодическую задачу фонового отслеживания
  static Future<void> registerPeriodicTask() async {
    final prefs = await SharedPreferences.getInstance();
    final enabled = prefs.getBool('background_location_enabled') ?? false;
    
    if (!enabled) {
      await Workmanager().cancelByUniqueName(taskName);
      return;
    }

    // Определяем интервал на основе настроек батареи
    final batterySaving = prefs.getBool('battery_saving_mode') ?? false;
    final interval = batterySaving
        ? AppConfig.batterySavingLocationUpdateInterval
        : AppConfig.defaultLocationUpdateInterval;

    await Workmanager().registerPeriodicTask(
      taskName,
      taskName,
      frequency: Duration(minutes: interval),
      constraints: Constraints(
        networkType: NetworkType.not_required,
        requiresBatteryNotLow: false,
        requiresCharging: false,
        requiresDeviceIdle: false,
        requiresStorageNotLow: false,
      ),
    );
  }

  /// Отменяет фоновое отслеживание
  static Future<void> cancelBackgroundTracking() async {
    await Workmanager().cancelByUniqueName(taskName);
  }
}
