import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'dart:convert';

import '../config/app_config.dart';
import '../database/database_helper.dart';
import '../models/location_event.dart';
import '../models/poi.dart';

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

      if (response.statusCode == 200) {
        // Помечаем события как синхронизированные
        final eventIds = unsyncedEvents.map((e) => e.id).toList();
        await db.markEventsAsSynced(eventIds);
        return true;
      }

      return false;
    } catch (e) {
      // Ошибка синхронизации - события останутся в очереди
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
    } catch (e) {
      // При ошибке возвращаем кэш
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
        // TODO: Реализовать сохранение данных карты
        return true;
      }

      return false;
    } catch (e) {
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
    } catch (e) {
      return false;
    }
  }
}
