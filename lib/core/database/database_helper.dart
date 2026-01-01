import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import '../models/location_event.dart';
import '../models/home_work_location.dart';
import '../models/poi.dart';
import '../models/region.dart';
import '../models/achievement.dart';
import 'package:geolocator/geolocator.dart';

/// Хелпер для работы с локальной SQLite БД
class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._internal();
  static Database? _database;

  DatabaseHelper._internal();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await initDatabase();
    return _database!;
  }

  Future<Database> initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'explorers_map.db');

    return await openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
      onUpgrade: _onUpgrade,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    // Таблица событий геолокации
    await db.execute('''
      CREATE TABLE location_events (
        id TEXT PRIMARY KEY,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        timestamp INTEGER NOT NULL,
        poi_id TEXT,
        region_id TEXT,
        device_id TEXT NOT NULL,
        synced INTEGER NOT NULL DEFAULT 0,
        synced_at INTEGER
      )
    ''');

    // Таблица POI (кэш с сервера)
    await db.execute('''
      CREATE TABLE pois (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        type TEXT NOT NULL,
        geofence TEXT NOT NULL,
        radius REAL,
        region_id TEXT NOT NULL,
        icon_url TEXT,
        achievement_category TEXT,
        updated_at INTEGER NOT NULL
      )
    ''');

    // Таблица определённых мест (дом/работа)
    await db.execute('''
      CREATE TABLE home_work_locations (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        radius REAL NOT NULL,
        detected_at INTEGER NOT NULL,
        verified INTEGER NOT NULL DEFAULT 0,
        verified_at INTEGER,
        custom_name TEXT
      )
    ''');

    // Таблица открытых регионов (для офлайн-карт)
    await db.execute('''
      CREATE TABLE cached_regions (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        bounds TEXT NOT NULL,
        map_data TEXT,
        downloaded_at INTEGER NOT NULL,
        last_updated INTEGER NOT NULL
      )
    ''');

    // Таблица открытых POI пользователем
    await db.execute('''
      CREATE TABLE opened_pois (
        poi_id TEXT PRIMARY KEY,
        opened_at INTEGER NOT NULL,
        opened_hour INTEGER NOT NULL,
        FOREIGN KEY (poi_id) REFERENCES pois(id)
      )
    ''');

    // Таблица достижений
    await db.execute('''
      CREATE TABLE achievements (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        icon_url TEXT,
        unlocked_at INTEGER,
        progress TEXT
      )
    ''');

    // Таблица заметок пользователя к POI
    await db.execute('''
      CREATE TABLE poi_notes (
        poi_id TEXT PRIMARY KEY,
        note TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL,
        FOREIGN KEY (poi_id) REFERENCES pois(id)
      )
    ''');

    // Индексы
    await db.execute('CREATE INDEX idx_opened_pois_opened_at ON opened_pois(opened_at)');
    await db.execute('CREATE INDEX idx_opened_pois_opened_hour ON opened_pois(opened_hour)');
    await db.execute('CREATE INDEX idx_achievements_category ON achievements(category)');
    await db.execute('CREATE INDEX idx_achievements_unlocked_at ON achievements(unlocked_at)');
    await db.execute('CREATE INDEX idx_poi_notes_poi_id ON poi_notes(poi_id)');

    // Индексы для оптимизации запросов
    await db.execute('CREATE INDEX idx_location_events_synced ON location_events(synced, timestamp)');
    await db.execute('CREATE INDEX idx_location_events_timestamp ON location_events(timestamp)');
    await db.execute('CREATE INDEX idx_pois_region ON pois(region_id)');
  }

  Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Миграции при обновлении версии БД
    if (oldVersion < newVersion) {
      // Здесь будут миграции при необходимости
    }
  }

  // ========== Методы для работы с событиями геолокации ==========

  Future<String> insertLocationEvent(LocationEvent event) async {
    final db = await database;
    await db.insert(
      'location_events',
      {
        'id': event.id,
        'latitude': event.latitude,
        'longitude': event.longitude,
        'timestamp': event.timestamp.millisecondsSinceEpoch,
        'poi_id': event.poiId,
        'region_id': event.regionId,
        'device_id': event.deviceId,
        'synced': event.synced ? 1 : 0,
        'synced_at': event.syncedAt?.millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
    return event.id;
  }

  Future<List<LocationEvent>> getUnsyncedEvents({int limit = 100}) async {
    final db = await database;
    final results = await db.query(
      'location_events',
      where: 'synced = ?',
      whereArgs: [0],
      orderBy: 'timestamp ASC',
      limit: limit,
    );

    return results.map((row) => _locationEventFromMap(row)).toList();
  }

  /// Получает синхронизированные события за период
  Future<List<LocationEvent>> getSyncedEvents({
    required DateTime startDate,
    required DateTime endDate,
    int limit = 10000,
  }) async {
    final db = await database;
    final results = await db.query(
      'location_events',
      where: 'synced = ? AND timestamp >= ? AND timestamp <= ?',
      whereArgs: [
        1,
        startDate.millisecondsSinceEpoch,
        endDate.millisecondsSinceEpoch,
      ],
      orderBy: 'timestamp ASC',
      limit: limit,
    );

    return results.map((row) => _locationEventFromMap(row)).toList();
  }

  Future<void> markEventsAsSynced(List<String> eventIds) async {
    final db = await database;
    final now = DateTime.now().millisecondsSinceEpoch;
    
    await db.update(
      'location_events',
      {
        'synced': 1,
        'synced_at': now,
      },
      where: 'id IN (${eventIds.map((_) => '?').join(',')})',
      whereArgs: eventIds,
    );
  }

  Future<int> getUnsyncedEventsCount() async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM location_events WHERE synced = 0',
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  LocationEvent _locationEventFromMap(Map<String, dynamic> map) {
    return LocationEvent(
      id: map['id'] as String,
      latitude: map['latitude'] as double,
      longitude: map['longitude'] as double,
      timestamp: DateTime.fromMillisecondsSinceEpoch(map['timestamp'] as int),
      poiId: map['poi_id'] as String?,
      regionId: map['region_id'] as String?,
      deviceId: map['device_id'] as String,
      synced: (map['synced'] as int) == 1,
      syncedAt: map['synced_at'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['synced_at'] as int)
          : null,
    );
  }

  // ========== Методы для работы с POI ==========

  Future<void> insertPOI(POI poi) async {
    final db = await database;
    await db.insert(
      'pois',
      {
        'id': poi.id,
        'name': poi.name,
        'description': poi.description,
        'latitude': poi.latitude,
        'longitude': poi.longitude,
        'type': poi.type,
        'geofence': jsonEncode(poi.geofence.map((p) => p.toJson()).toList()),
        'radius': poi.radius,
        'region_id': poi.regionId,
        'icon_url': poi.iconUrl,
        'achievement_category': poi.achievementCategory,
        'updated_at': DateTime.now().millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<POI>> getPOIsByRegion(String regionId) async {
    final db = await database;
    final results = await db.query(
      'pois',
      where: 'region_id = ?',
      whereArgs: [regionId],
    );

    return results.map((row) => _poiFromMap(row)).toList();
  }

  Future<POI?> getPOIById(String poiId) async {
    final db = await database;
    final results = await db.query(
      'pois',
      where: 'id = ?',
      whereArgs: [poiId],
      limit: 1,
    );

    if (results.isEmpty) return null;
    return _poiFromMap(results.first);
  }

  Future<List<POI>> getAllPOIs() async {
    final db = await database;
    final results = await db.query('pois');
    return results.map((row) => _poiFromMap(row)).toList();
  }

  /// Получает POI в радиусе от точки (оптимизированный запрос)
  Future<List<POI>> getPOIsNearby({
    required double latitude,
    required double longitude,
    required double radiusMeters,
    String? regionId,
  }) async {
    final db = await database;
    
    // Используем приближённую формулу для предварительной фильтрации
    // 1 градус широты ≈ 111 км, 1 градус долготы ≈ 111 км * cos(широта)
    final latDelta = radiusMeters / 111000.0;
    final lonDelta = radiusMeters / (111000.0 * (latitude.abs() / 90.0 + 0.1));
    
    final minLat = latitude - latDelta;
    final maxLat = latitude + latDelta;
    final minLon = longitude - lonDelta;
    final maxLon = longitude + lonDelta;
    
    String whereClause = '''
      latitude >= ? AND latitude <= ? AND
      longitude >= ? AND longitude <= ?
    ''';
    List<dynamic> whereArgs = [minLat, maxLat, minLon, maxLon];
    
    if (regionId != null) {
      whereClause += ' AND region_id = ?';
      whereArgs.add(regionId);
    }
    
    final results = await db.query(
      'pois',
      where: whereClause,
      whereArgs: whereArgs,
    );
    
    final pois = results.map((row) => _poiFromMap(row)).toList();
    
    // Фильтруем по точному расстоянию
    return pois.where((poi) {
      final distance = Geolocator.distanceBetween(
        latitude,
        longitude,
        poi.latitude,
        poi.longitude,
      );
      return distance <= radiusMeters;
    }).toList();
  }

  POI _poiFromMap(Map<String, dynamic> map) {
    final geofenceJson = jsonDecode(map['geofence'] as String) as List;
    return POI(
      id: map['id'] as String,
      name: map['name'] as String,
      description: map['description'] as String? ?? '',
      latitude: map['latitude'] as double,
      longitude: map['longitude'] as double,
      type: map['type'] as String,
      geofence: geofenceJson
          .map((p) => GeoPoint.fromJson(p as Map<String, dynamic>))
          .toList(),
      radius: map['radius'] as double?,
      regionId: map['region_id'] as String,
      iconUrl: map['icon_url'] as String?,
      achievementCategory: map['achievement_category'] as String?,
    );
  }

  // ========== Методы для работы с домом/работой ==========

  Future<void> insertHomeWorkLocation(HomeWorkLocation location) async {
    final db = await database;
    await db.insert(
      'home_work_locations',
      {
        'id': location.id,
        'type': location.type.toString().split('.').last,
        'latitude': location.latitude,
        'longitude': location.longitude,
        'radius': location.radius,
        'detected_at': location.detectedAt.millisecondsSinceEpoch,
        'verified': location.verified ? 1 : 0,
        'verified_at': location.verifiedAt?.millisecondsSinceEpoch,
        'custom_name': location.customName,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<HomeWorkLocation>> getHomeWorkLocations({bool verifiedOnly = false}) async {
    final db = await database;
    final results = verifiedOnly
        ? await db.query(
            'home_work_locations',
            where: 'verified = ?',
            whereArgs: [1],
          )
        : await db.query('home_work_locations');

    return results.map((row) => _homeWorkLocationFromMap(row)).toList();
  }

  Future<void> updateHomeWorkLocationVerification(
    String id,
    bool verified,
    String? customName,
  ) async {
    final db = await database;
    await db.update(
      'home_work_locations',
      {
        'verified': verified ? 1 : 0,
        'verified_at': verified ? DateTime.now().millisecondsSinceEpoch : null,
        'custom_name': customName,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  HomeWorkLocation _homeWorkLocationFromMap(Map<String, dynamic> map) {
    return HomeWorkLocation(
      id: map['id'] as String,
      type: map['type'] == 'home' ? LocationType.home : LocationType.work,
      latitude: map['latitude'] as double,
      longitude: map['longitude'] as double,
      radius: map['radius'] as double,
      detectedAt: DateTime.fromMillisecondsSinceEpoch(map['detected_at'] as int),
      verified: (map['verified'] as int) == 1,
      verifiedAt: map['verified_at'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['verified_at'] as int)
          : null,
      customName: map['custom_name'] as String?,
    );
  }

  // ========== Методы для получения данных посещений (для кластеризации) ==========

  Future<List<Map<String, dynamic>>> getVisitPointsForClustering({
    required DateTime startDate,
    required DateTime endDate,
  }) async {
    final db = await database;
    
    // Получаем все события за период, отсортированные по времени
    final events = await db.query(
      'location_events',
      where: 'timestamp >= ? AND timestamp <= ?',
      whereArgs: [
        startDate.millisecondsSinceEpoch,
        endDate.millisecondsSinceEpoch,
      ],
      orderBy: 'timestamp ASC',
    );

    if (events.isEmpty) return [];

    final visitPoints = <Map<String, dynamic>>[];
    
    // Группируем события по близким координатам и времени
    for (int i = 0; i < events.length; i++) {
      final currentEvent = events[i];
      final currentLat = currentEvent['latitude'] as double;
      final currentLon = currentEvent['longitude'] as double;
      final currentTime = currentEvent['timestamp'] as int;
      
      // Ищем следующее событие, которое достаточно далеко или через большой промежуток времени
      DateTime? departureTime;
      
      for (int j = i + 1; j < events.length; j++) {
        final nextEvent = events[j];
        final nextLat = nextEvent['latitude'] as double;
        final nextLon = nextEvent['longitude'] as double;
        final nextTime = nextEvent['timestamp'] as int;
        
        final timeDiff = nextTime - currentTime;
        final distance = Geolocator.distanceBetween(
          currentLat,
          currentLon,
          nextLat,
          nextLon,
        );
        
        // Если следующее событие далеко (>100м) или через большой промежуток (>30 мин)
        // считаем, что время убытия - это время следующего события
        if (distance > 100 || timeDiff > 30 * 60 * 1000) {
          departureTime = DateTime.fromMillisecondsSinceEpoch(nextTime);
          break;
        }
      }
      
      // Если не нашли время убытия, используем время следующего события или текущее + 1 час
      if (departureTime == null) {
        if (i + 1 < events.length) {
          departureTime = DateTime.fromMillisecondsSinceEpoch(
            events[i + 1]['timestamp'] as int,
          );
        } else {
          // Последнее событие - добавляем час к времени прибытия
          departureTime = DateTime.fromMillisecondsSinceEpoch(currentTime)
              .add(const Duration(hours: 1));
        }
      }
      
      visitPoints.add({
        'latitude': currentLat,
        'longitude': currentLon,
        'arrival_time': currentTime,
        'departure_time': departureTime.millisecondsSinceEpoch,
      });
    }

    return visitPoints;
  }

  // ========== Методы для работы с регионами ==========

  Future<void> insertCachedRegion(Region region, {String? mapData}) async {
    final db = await database;
    await db.insert(
      'cached_regions',
      {
        'id': region.id,
        'name': region.name,
        'bounds': jsonEncode(region.bounds.toJson()),
        'map_data': mapData,
        'downloaded_at': region.downloadedAt?.millisecondsSinceEpoch ??
            DateTime.now().millisecondsSinceEpoch,
        'last_updated': region.lastUpdated?.millisecondsSinceEpoch ??
            DateTime.now().millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Region>> getCachedRegions() async {
    final db = await database;
    final results = await db.query('cached_regions');

    return results.map((row) => _regionFromMap(row)).toList();
  }

  Future<Region?> getCachedRegion(String regionId) async {
    final db = await database;
    final results = await db.query(
      'cached_regions',
      where: 'id = ?',
      whereArgs: [regionId],
      limit: 1,
    );

    if (results.isEmpty) return null;
    return _regionFromMap(results.first);
  }

  Region _regionFromMap(Map<String, dynamic> map) {
    final boundsJson = jsonDecode(map['bounds'] as String) as Map<String, dynamic>;
    return Region(
      id: map['id'] as String,
      name: map['name'] as String,
      bounds: RegionBounds.fromJson(boundsJson),
      downloadedAt: map['downloaded_at'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['downloaded_at'] as int)
          : null,
      lastUpdated: map['last_updated'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['last_updated'] as int)
          : null,
    );
  }

  Future<void> updateRegionMapData(String regionId, String mapData) async {
    final db = await database;
    await db.update(
      'cached_regions',
      {
        'map_data': mapData,
        'last_updated': DateTime.now().millisecondsSinceEpoch,
      },
      where: 'id = ?',
      whereArgs: [regionId],
    );
  }

  // ========== Методы для работы с открытыми POI ==========

  Future<void> markPOIOpened(String poiId) async {
    final db = await database;
    await db.insert(
      'opened_pois',
      {
        'poi_id': poiId,
        'opened_at': DateTime.now().millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Безопасное открытие POI с проверкой через транзакцию (избегает race condition)
  Future<void> markPOIOpenedSafe(String poiId) async {
    final db = await database;
    final now = DateTime.now();
    await db.transaction((txn) async {
      // Проверяем, не открыт ли уже POI
      final existing = await txn.query(
        'opened_pois',
        where: 'poi_id = ?',
        whereArgs: [poiId],
        limit: 1,
      );

      if (existing.isEmpty) {
        await txn.insert(
          'opened_pois',
          {
            'poi_id': poiId,
            'opened_at': now.millisecondsSinceEpoch,
            'opened_hour': now.hour, // Сохраняем час открытия для проверки ночных ачивок
          },
        );
      }
    });
  }

  Future<bool> isPOIOpened(String poiId) async {
    final db = await database;
    final results = await db.query(
      'opened_pois',
      where: 'poi_id = ?',
      whereArgs: [poiId],
      limit: 1,
    );
    return results.isNotEmpty;
  }

  Future<int> getOpenedPOIsCount() async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM opened_pois',
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  Future<int> getRegionsCount() async {
    final db = await database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) as count FROM cached_regions',
    );
    return Sqflite.firstIntValue(result) ?? 0;
  }

  Future<List<String>> getOpenedPOIIds() async {
    final db = await database;
    final results = await db.query('opened_pois');
    return results.map((row) => row['poi_id'] as String).toList();
  }

  /// Получает POI, открытые в указанный час (для ночных ачивок)
  Future<List<String>> getPOIsOpenedAtHour(int hour) async {
    final db = await database;
    final results = await db.query(
      'opened_pois',
      where: 'opened_hour = ?',
      whereArgs: [hour],
    );
    return results.map((row) => row['poi_id'] as String).toList();
  }

  /// Получает POI, открытые в ночное время (20:00-08:00)
  Future<List<String>> getPOIsOpenedAtNight() async {
    final db = await database;
    // Ночное время: 20-23 и 0-7 часов
    final results = await db.rawQuery('''
      SELECT DISTINCT poi_id FROM opened_pois
      WHERE opened_hour >= 20 OR opened_hour < 8
    ''');
    return results.map((row) => row['poi_id'] as String).toList();
  }

  // ========== Методы для работы с достижениями ==========

  Future<void> insertAchievement(Achievement achievement) async {
    final db = await database;
    await db.insert(
      'achievements',
      {
        'id': achievement.id,
        'title': achievement.title,
        'description': achievement.description,
        'category': achievement.category,
        'icon_url': achievement.iconUrl,
        'unlocked_at': achievement.unlockedAt?.millisecondsSinceEpoch,
        'progress': achievement.progress != null
            ? jsonEncode(achievement.progress)
            : null,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<List<Achievement>> getAchievements({bool unlockedOnly = false}) async {
    final db = await database;
    final results = unlockedOnly
        ? await db.query(
            'achievements',
            where: 'unlocked_at IS NOT NULL',
            orderBy: 'unlocked_at DESC',
          )
        : await db.query('achievements', orderBy: 'unlocked_at DESC');

    return results.map((row) => _achievementFromMap(row)).toList();
  }

  Future<Achievement?> getAchievementById(String id) async {
    final db = await database;
    final results = await db.query(
      'achievements',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );

    if (results.isEmpty) return null;
    return _achievementFromMap(results.first);
  }

  Achievement _achievementFromMap(Map<String, dynamic> map) {
    return Achievement(
      id: map['id'] as String,
      title: map['title'] as String,
      description: map['description'] as String,
      category: map['category'] as String,
      iconUrl: map['icon_url'] as String?,
      unlockedAt: map['unlocked_at'] != null
          ? DateTime.fromMillisecondsSinceEpoch(map['unlocked_at'] as int)
          : null,
      progress: map['progress'] != null
          ? jsonDecode(map['progress'] as String) as Map<String, dynamic>
          : null,
    );
  }

  /// Очищает старые синхронизированные события (старше указанного количества дней)
  Future<int> cleanupOldSyncedEvents({int daysToKeep = 30}) async {
    final db = await database;
    final cutoffDate = DateTime.now().subtract(Duration(days: daysToKeep));
    
    final deleted = await db.delete(
      'location_events',
      where: 'synced = 1 AND synced_at < ?',
      whereArgs: [cutoffDate.millisecondsSinceEpoch],
    );
    
    return deleted;
  }

  /// Очищает старые несинхронизированные события (если их слишком много)
  /// Оставляет только последние N событий
  Future<int> cleanupOldUnsyncedEvents({int keepLast = 10000}) async {
    final db = await database;
    
    // Получаем количество несинхронизированных событий
    final countResult = await db.rawQuery(
      'SELECT COUNT(*) as count FROM location_events WHERE synced = 0',
    );
    final count = Sqflite.firstIntValue(countResult) ?? 0;
    
    if (count <= keepLast) {
      return 0;
    }
    
    // Удаляем самые старые события, оставляя только последние keepLast
    final deleted = await db.rawDelete('''
      DELETE FROM location_events
      WHERE synced = 0 AND id IN (
        SELECT id FROM location_events
        WHERE synced = 0
        ORDER BY timestamp ASC
        LIMIT ?
      )
    ''', [count - keepLast]);
    
    return deleted;
  }

  /// Получает размер БД в байтах
  Future<int> getDatabaseSize() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'explorers_map.db');
    final file = File(path);
    
    if (await file.exists()) {
      return await file.length();
    }
    
    return 0;
  }

  /// Выполняет очистку БД от старых данных
  Future<Map<String, int>> performDatabaseCleanup({
    int daysToKeepSynced = 30,
    int keepLastUnsynced = 10000,
  }) async {
    final syncedDeleted = await cleanupOldSyncedEvents(daysToKeep: daysToKeepSynced);
    final unsyncedDeleted = await cleanupOldUnsyncedEvents(keepLast: keepLastUnsynced);
    
    // Оптимизируем БД после удаления
    final db = await database;
    await db.execute('VACUUM');
    
    return {
      'synced_deleted': syncedDeleted,
      'unsynced_deleted': unsyncedDeleted,
    };
  }

  Future<void> close() async {
    final db = await database;
    await db.close();
  }
}
