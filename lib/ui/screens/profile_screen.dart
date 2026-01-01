import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/services/location_service.dart';
import '../../core/services/background_service.dart';
import '../../core/services/sync_service.dart';
import '../../core/database/database_helper.dart';

/// Экран профиля с настройками
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _backgroundTrackingEnabled = false;
  String _locationAccuracy = 'low';
  bool _batterySavingMode = false;
  int _unsyncedEventsCount = 0;

  @override
  void initState() {
    super.initState();
    _loadSettings();
    _loadUnsyncedCount();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    final locationService = LocationService.instance;

    setState(() {
      _backgroundTrackingEnabled =
          prefs.getBool('background_location_enabled') ?? false;
      _locationAccuracy = prefs.getString('location_accuracy') ?? 'low';
      _batterySavingMode = prefs.getBool('battery_saving_mode') ?? false;
    });
  }

  Future<void> _loadUnsyncedCount() async {
    final db = DatabaseHelper.instance;
    final count = await db.getUnsyncedEventsCount();
    setState(() {
      _unsyncedEventsCount = count;
    });
  }

  Future<void> _toggleBackgroundTracking(bool value) async {
    final locationService = LocationService.instance;
    await locationService.setBackgroundTrackingEnabled(value);

    if (value) {
      await BackgroundService.registerPeriodicTask();
    } else {
      await BackgroundService.cancelBackgroundTracking();
    }

    setState(() {
      _backgroundTrackingEnabled = value;
    });
  }

  Future<void> _setLocationAccuracy(String accuracy) async {
    final locationService = LocationService.instance;
    final accuracyEnum = accuracy == 'high'
        ? LocationAccuracy.high
        : accuracy == 'medium'
            ? LocationAccuracy.medium
            : LocationAccuracy.low;

    await locationService.setLocationAccuracy(accuracyEnum);

    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('location_accuracy', accuracy);

    setState(() {
      _locationAccuracy = accuracy;
    });
  }

  Future<void> _toggleBatterySavingMode(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('battery_saving_mode', value);

    // Перерегистрируем фоновую задачу с новым интервалом
    if (_backgroundTrackingEnabled) {
      await BackgroundService.registerPeriodicTask();
    }

    setState(() {
      _batterySavingMode = value;
    });
  }

  Future<void> _syncNow() async {
    final syncService = SyncService.instance;
    final hasInternet = await syncService.checkInternetConnection();

    if (!hasInternet) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Нет подключения к интернету'),
          ),
        );
      }
      return;
    }

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Синхронизация...')),
      );
    }

    final success = await syncService.syncPendingEvents();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(success
              ? 'Синхронизация завершена'
              : 'Ошибка синхронизации'),
        ),
      );
    }

    _loadUnsyncedCount();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Профиль'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16.0),
        children: [
          // Настройки геолокации
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Геолокация',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  SwitchListTile(
                    title: const Text('Фоновое отслеживание'),
                    subtitle: const Text(
                      'Автоматически фиксировать посещения мест',
                    ),
                    value: _backgroundTrackingEnabled,
                    onChanged: _toggleBackgroundTracking,
                  ),
                  const Divider(),
                  ListTile(
                    title: const Text('Точность геолокации'),
                    subtitle: Text(_getAccuracyDescription(_locationAccuracy)),
                    trailing: DropdownButton<String>(
                      value: _locationAccuracy,
                      items: const [
                        DropdownMenuItem(
                          value: 'low',
                          child: Text('Низкая (экономия батареи)'),
                        ),
                        DropdownMenuItem(
                          value: 'medium',
                          child: Text('Средняя'),
                        ),
                        DropdownMenuItem(
                          value: 'high',
                          child: Text('Высокая'),
                        ),
                      ],
                      onChanged: (value) {
                        if (value != null) {
                          _setLocationAccuracy(value);
                        }
                      },
                    ),
                  ),
                  SwitchListTile(
                    title: const Text('Режим экономии батареи'),
                    subtitle: const Text(
                      'Увеличивает интервал обновления геолокации',
                    ),
                    value: _batterySavingMode,
                    onChanged: _toggleBatterySavingMode,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Синхронизация
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Синхронизация',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ListTile(
                    title: const Text('Несинхронизированных событий'),
                    trailing: Text(
                      _unsyncedEventsCount.toString(),
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _syncNow,
                      child: const Text('Синхронизировать сейчас'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // О приложении
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'О приложении',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  const ListTile(
                    title: Text('Версия'),
                    trailing: Text('1.0.0'),
                  ),
                  const ListTile(
                    title: Text('Лицензия'),
                    trailing: Text('Проприетарная'),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _getAccuracyDescription(String accuracy) {
    switch (accuracy) {
      case 'high':
        return 'Высокая точность, больше расход батареи';
      case 'medium':
        return 'Средняя точность, баланс точности и батареи';
      case 'low':
      default:
        return 'Низкая точность, экономия батареи';
    }
  }
}
