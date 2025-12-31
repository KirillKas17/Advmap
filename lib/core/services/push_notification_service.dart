import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/material.dart';

import '../models/achievement.dart';
import '../navigation/app_router.dart';
import '../services/sync_service.dart';
import '../../main.dart';
import '../utils/logger.dart';

/// Сервис для работы с push-уведомлениями
class PushNotificationService {
  static final PushNotificationService instance = PushNotificationService._internal();
  PushNotificationService._internal();

  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();

  bool _initialized = false;

  /// Инициализация сервиса push-уведомлений
  Future<void> initialize() async {
    if (_initialized) return;

    // Запрашиваем разрешение на уведомления
    final settings = await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    if (settings.authorizationStatus == AuthorizationStatus.authorized ||
        settings.authorizationStatus == AuthorizationStatus.provisional) {
      // Инициализируем локальные уведомления
      const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
      const iosSettings = DarwinInitializationSettings();
      const initSettings = InitializationSettings(
        android: androidSettings,
        iOS: iosSettings,
      );

      await _localNotifications.initialize(
        initSettings,
        onDidReceiveNotificationResponse: _onNotificationTapped,
      );

      // Настраиваем обработчики сообщений
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      FirebaseMessaging.onMessageOpenedApp.listen(_handleBackgroundMessage);

      // Получаем токен FCM
      final token = await _firebaseMessaging.getToken();
      if (token != null) {
        await _saveFCMToken(token);
      }

      // Обработка обновления токена
      _firebaseMessaging.onTokenRefresh.listen(_saveFCMToken);

      _initialized = true;
    }
  }

  /// Обработка уведомления при нажатии
  void _onNotificationTapped(NotificationResponse response) {
    if (response.payload != null) {
      // Если payload содержит ID достижения, открываем его
      final achievementId = response.payload;
      if (achievementId != null && achievementId.isNotEmpty) {
        _navigateToAchievement(achievementId);
      }
    }
  }

  void _navigateToAchievement(String achievementId) {
    // Навигация выполняется через глобальный navigatorKey
    try {
      final context = navigatorKey.currentContext;
      if (context != null) {
        // В реальном приложении здесь будет загрузка достижения по ID
        // и навигация к экрану деталей
        AppRouter.navigateToAchievement(
          context,
          Achievement(
            id: achievementId,
            title: 'Достижение',
            description: 'Описание достижения',
            category: 'general',
          ),
        );
      }
    } catch (e) {
      Logger.error('Ошибка навигации к достижению', e);
    }
  }

  /// Обработка сообщения в foreground
  Future<void> _handleForegroundMessage(RemoteMessage message) async {
    // Показываем локальное уведомление
    final achievementId = message.data['achievement_id'] as String?;
    await _showLocalNotification(
      title: message.notification?.title ?? 'Новое уведомление',
      body: message.notification?.body ?? '',
      payload: achievementId ?? message.data.toString(),
    );
  }

  /// Обработка сообщения при открытии из фона
  void _handleBackgroundMessage(RemoteMessage message) {
    final achievementId = message.data['achievement_id'] as String?;
    if (achievementId != null && achievementId.isNotEmpty) {
      _navigateToAchievement(achievementId);
    }
  }

  /// Показывает локальное уведомление
  Future<void> _showLocalNotification({
    required String title,
    required String body,
    String? payload,
  }) async {
    const androidDetails = AndroidNotificationDetails(
      'achievements_channel',
      'Достижения',
      channelDescription: 'Уведомления о разблокированных достижениях',
      importance: Importance.high,
      priority: Priority.high,
    );

    const iosDetails = DarwinNotificationDetails();

    const notificationDetails = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );

    await _localNotifications.show(
      DateTime.now().millisecondsSinceEpoch.remainder(100000),
      title,
      body,
      notificationDetails,
      payload: payload,
    );
  }

  /// Сохраняет FCM токен на устройстве и отправляет на сервер
  Future<void> _saveFCMToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('fcm_token', token);

    // Отправляем токен на сервер для регистрации устройства
    await _registerDeviceToken(token);
  }

  /// Регистрирует токен устройства на сервере
  Future<void> _registerDeviceToken(String token) async {
    try {
      final syncService = SyncService.instance;
      final hasInternet = await syncService.checkInternetConnection();
      
      if (hasInternet) {
        // Отправляем токен на сервер
        await syncService.registerDeviceToken(token);
      }
    } catch (e) {
      // Ошибка регистрации токена не критична
      // Токен будет отправлен при следующей синхронизации
    }
  }

  /// Получает сохранённый FCM токен
  Future<String?> getFCMToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('fcm_token');
  }

  /// Показывает уведомление о разблокированной ачивке
  Future<void> showAchievementNotification(Achievement achievement) async {
    await _showLocalNotification(
      title: '🎉 Достижение разблокировано!',
      body: '${achievement.title}\n${achievement.description}',
      payload: achievement.id,
    );
  }
}
