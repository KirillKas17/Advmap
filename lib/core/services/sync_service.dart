import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'dart:convert';

import '../config/app_config.dart';
import '../database/database_helper.dart';
import '../models/location_event.dart';
import '../models/poi.dart';
import '../models/region.dart';
import '../models/achievement.dart';
import '../services/achievement_service.dart';
import '../utils/logger.dart';
import 'dart:convert';

/// Сервис синхронизации данных с сервером
class SyncService {
  static final SyncService instance = SyncService._internal();
  SyncService._internal();

  final Dio _dio = Dio(BaseOptions(
    baseUrl: AppConfig.apiBaseUrl,
    connectTimeout: AppConfig.syncTimeout,
    receiveTimeout: AppConfig.syncTimeout,
  ));

  /// Проверяет наличие интернет-соединения
  Future<bool> checkInternetConnection() async {
    try {
      final connectivityResult = await Connectivity().checkConnectivity();
      return connectivityResult != ConnectivityResult.none;
    } catch (e) {
      return false;
    }
  }

  /// Синхронизирует неотправленные события геолокации с сервером
  Future<bool> syncPendingEvents({int batchSize = 50}) async {
    final hasInternet = await checkInternetConnection();
    if (!hasInternet) {
      return false;
    }

    final db = DatabaseHelper.instance;
    final unsyncedEvents = await db.getUnsyncedEvents(limit: batchSize);

    if (unsyncedEvents.isEmpty) {
      return true;
    }

    try {
      // Отправляем события пачкой на сервер
      final response = await _dio.post(
        '/api/v1/events/sync',
        data: {
          'events': unsyncedEvents.map((e) => e.toJson()).toList(),
        },
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        // Помечаем события как синхронизированные
        final eventIds = unsyncedEvents.map((e) => e.id).toList();
        await db.markEventsAsSynced(eventIds);
        
        // Проверяем, есть ли в ответе информация о разблокированных ачивках
        if (response.data is Map && response.data['achievements'] != null) {
          final achievementsData = response.data['achievements'] as List;
          // Обрабатываем разблокированные ачивки с сервера
          final achievementService = AchievementService.instance;
          for (final achievementJson in achievementsData) {
            try {
              final achievement = Achievement.fromJson(
                achievementJson as Map<String, dynamic>,
              );
              await achievementService.saveAchievement(achievement);
            } catch (e) {
              Logger.error('Ошибка обработки ачивки с сервера', e);
            }
          }
        }
        
        return true;
      }

      return false;
    } catch (e, stackTrace) {
      // Ошибка синхронизации - события останутся в очереди
      Logger.error('Ошибка синхронизации событий', e, stackTrace);
      return false;
    }
  }

  /// Загружает POI для региона с сервера
  Future<List<POI>> loadPOIsForRegion(String regionId) async {
    final hasInternet = await checkInternetConnection();
    if (!hasInternet) {
      // Возвращаем POI из локального кэша
      final db = DatabaseHelper.instance;
      return await db.getPOIsByRegion(regionId);
    }

    try {
      final response = await _dio.get('/api/v1/regions/$regionId/pois');

      if (response.statusCode == 200) {
        final List<dynamic> poisData = response.data['pois'] ?? [];
        final db = DatabaseHelper.instance;

        for (final poiData in poisData) {
          final poi = POI.fromJson(poiData as Map<String, dynamic>);
          await db.insertPOI(poi);
        }

        return await db.getPOIsByRegion(regionId);
      }

      return [];
    } catch (e, stackTrace) {
      // При ошибке возвращаем кэш
      Logger.error('Ошибка загрузки POI региона', e, stackTrace);
      final db = DatabaseHelper.instance;
      return await db.getPOIsByRegion(regionId);
    }
  }

  /// Загружает данные региона для офлайн-карт
  Future<bool> downloadRegionForOffline(String regionId) async {
    final hasInternet = await checkInternetConnection();
    if (!hasInternet) {
      return false;
    }

    try {
      // Загружаем POI региона
      await loadPOIsForRegion(regionId);

      // Загружаем данные карты региона (векторные тайлы)
      final response = await _dio.get('/api/v1/regions/$regionId/map-data');

      if (response.statusCode == 200) {
        final mapData = response.data;
        // Сохраняем данные карты в локальную БД
        final db = DatabaseHelper.instance;
        final mapDataJson = jsonEncode(mapData);
        await db.updateRegionMapData(regionId, mapDataJson);
        
        // Если региона нет в кэше, создаём запись
        final existingRegion = await db.getCachedRegion(regionId);
        if (existingRegion == null) {
          // Создаём регион с базовыми данными
          final region = Region(
            id: regionId,
            name: mapData['name'] as String? ?? regionId,
            bounds: RegionBounds.fromJson(
              mapData['bounds'] as Map<String, dynamic>,
            ),
            downloadedAt: DateTime.now(),
            lastUpdated: DateTime.now(),
          );
          await db.insertCachedRegion(region, mapData: mapDataJson);
        }
        
        return true;
      }

      return false;
    } catch (e, stackTrace) {
      Logger.error('Ошибка загрузки региона', e, stackTrace);
      return false;
    }
  }

  /// Отправляет информацию о разблокированной ачивке на сервер
  Future<bool> reportAchievementUnlocked(String achievementId) async {
    final hasInternet = await checkInternetConnection();
    if (!hasInternet) {
      return false;
    }

    try {
      await _dio.post(
        '/api/v1/achievements/unlock',
        data: {'achievement_id': achievementId},
      );
      return true;
    } catch (e, stackTrace) {
      Logger.error('Ошибка отправки достижения', e, stackTrace);
      return false;
    }
  }

  /// Регистрирует FCM токен устройства на сервере
  Future<bool> registerDeviceToken(String token) async {
    final hasInternet = await checkInternetConnection();
    if (!hasInternet) {
      return false;
    }

    try {
      await _dio.post(
        '/api/v1/devices/register',
        data: {'fcm_token': token},
      );
      return true;
    } catch (e, stackTrace) {
      Logger.error('Ошибка регистрации токена устройства', e, stackTrace);
      return false;
    }
  }
}
