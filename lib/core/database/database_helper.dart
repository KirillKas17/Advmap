import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'dart:async';
import 'dart:convert';

import '../models/location_event.dart';
import '../models/home_work_location.dart';
import '../models/poi.dart';
import '../models/region.dart';

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
        FOREIGN KEY (poi_id) REFERENCES pois(id)
      )
    ''');

    // Индексы
    await db.execute('CREATE INDEX idx_opened_pois_opened_at ON opened_pois(opened_at)');

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
    final results = await db.rawQuery('''
      SELECT 
        latitude,
        longitude,
        timestamp as arrival_time,
        LEAD(timestamp) OVER (ORDER BY timestamp) as departure_time
      FROM location_events
      WHERE timestamp >= ? AND timestamp <= ?
      ORDER BY timestamp ASC
    ''', [
      startDate.millisecondsSinceEpoch,
      endDate.millisecondsSinceEpoch,
    ]);

    return results;
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

  Future<void> close() async {
    final db = await database;
    await db.close();
  }
}
