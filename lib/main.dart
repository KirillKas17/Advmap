import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:workmanager/workmanager.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:geolocator/geolocator.dart';

import 'core/database/database_helper.dart';
import 'core/services/location_service.dart';
import 'core/services/background_service.dart';
import 'core/services/sync_service.dart';
import 'core/services/home_work_detector.dart';
import 'core/services/push_notification_service.dart';
import 'core/services/database_maintenance_service.dart';
import 'ui/screens/home_screen.dart';
import 'ui/screens/map_screen.dart';
import 'ui/screens/profile_screen.dart';
import 'core/config/app_config.dart';
import 'core/navigation/app_router.dart';
import 'core/utils/logger.dart';

// Глобальный ключ навигатора для доступа из сервисов
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  bool initializationSuccess = true;
  String? errorMessage;

  // Инициализация Firebase для push-уведомлений
  try {
    await Firebase.initializeApp();
    Logger.info('Firebase инициализирован');
  } catch (e, stackTrace) {
    Logger.error('Ошибка инициализации Firebase', e, stackTrace);
    initializationSuccess = false;
    errorMessage = 'Не удалось инициализировать Firebase. Push-уведомления будут недоступны.';
  }
  
  // Инициализация БД
  try {
    await DatabaseHelper.instance.initDatabase();
    Logger.info('База данных инициализирована');
  } catch (e, stackTrace) {
    Logger.error('Ошибка инициализации БД', e, stackTrace);
    initializationSuccess = false;
    errorMessage = 'Не удалось инициализировать базу данных. Приложение может работать некорректно.';
  }
  
  // Инициализация фонового сервиса
  try {
    await BackgroundService.initialize();
    Logger.info('Фоновый сервис инициализирован');
  } catch (e, stackTrace) {
    Logger.error('Ошибка инициализации фонового сервиса', e, stackTrace);
    // Не критично, продолжаем работу
  }
  
  // Инициализация push-уведомлений (только если Firebase инициализирован)
  if (initializationSuccess) {
    try {
      await PushNotificationService.instance.initialize();
      Logger.info('Push-уведомления инициализированы');
    } catch (e, stackTrace) {
      Logger.error('Ошибка инициализации push-уведомлений', e, stackTrace);
      // Не критично, продолжаем работу
    }
  }
  
  // Запуск фонового воркера
  try {
    await Workmanager().registerPeriodicTask(
      "locationTracking",
      "locationTrackingTask",
      frequency: const Duration(minutes: 15),
      constraints: Constraints(
        networkType: NetworkType.not_required,
        requiresBatteryNotLow: false,
        requiresCharging: false,
        requiresDeviceIdle: false,
        requiresStorageNotLow: false,
      ),
    );
    Logger.info('Фоновый воркер зарегистрирован');
  } catch (e, stackTrace) {
    Logger.error('Ошибка регистрации фонового воркера', e, stackTrace);
    // Не критично, продолжаем работу
  }
  
  // Запуск обслуживания БД
  try {
    DatabaseMaintenanceService.instance.startPeriodicMaintenance();
  } catch (e, stackTrace) {
    Logger.error('Ошибка запуска обслуживания БД', e, stackTrace);
    // Не критично, продолжаем работу
  }
  
  runApp(ExplorersMapApp(
    initializationError: errorMessage,
  ));
}

class ExplorersMapApp extends StatelessWidget {
  final String? initializationError;
  
  const ExplorersMapApp({
    super.key,
    this.initializationError,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Карта Исследователя',
      navigatorKey: navigatorKey,
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: initializationError != null
          ? _ErrorScreen(message: initializationError!)
          : const MainNavigationScreen(),
      debugShowCheckedModeBanner: false,
      onGenerateRoute: AppRouter.generateRoute,
    );
  }
}

class _ErrorScreen extends StatelessWidget {
  final String message;
  
  const _ErrorScreen({required this.message});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.orange),
              const SizedBox(height: 16),
              Text(
                'Предупреждение',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              Text(
                message,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pushReplacement(
                    MaterialPageRoute(
                      builder: (_) => const MainNavigationScreen(),
                    ),
                  );
                },
                child: const Text('Продолжить'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;

  final List<Widget> _screens = [
    const MapScreen(),
    const HomeScreen(),
    const ProfileScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.map_outlined),
            selectedIcon: Icon(Icons.map),
            label: 'Карта',
          ),
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'Главная',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Профиль',
          ),
        ],
      ),
    );
  }
}
