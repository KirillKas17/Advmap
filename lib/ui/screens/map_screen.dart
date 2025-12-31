import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/services/location_service.dart';
import '../../core/services/sync_service.dart';
import '../../core/services/region_detector.dart';
import '../../core/database/database_helper.dart';
import '../../core/models/poi.dart';
import '../widgets/region_selection_dialog.dart';
import 'package:flutter_map/flutter_map.dart';
import 'dart:math' as math;

/// Экран карты с туманом войны
class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final MapController _mapController = MapController();
  Position? _currentPosition;
  List<POI> _pois = [];
  Set<String> _openedPOIIds = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _initializeMap();
  }

  Future<void> _initializeMap() async {
    // Получаем текущую позицию
    final locationService = LocationService.instance;
    final position = await locationService.getCurrentPosition();
    
    if (position != null) {
      setState(() {
        _currentPosition = position;
      });
    }

    // Загружаем POI для текущего региона
    await _loadPOIs();

    setState(() {
      _isLoading = false;
    });
  }

  Future<void> _loadPOIs() async {
    String? regionId;
    
    // Определяем текущий регион по позиции
    if (_currentPosition != null) {
      final detector = RegionDetector.instance;
      regionId = await detector.detectRegion(
        _currentPosition!.latitude,
        _currentPosition!.longitude,
      );
    }

    // Если регион не определён, используем первый загруженный или дефолтный
    if (regionId == null) {
      final db = DatabaseHelper.instance;
      final cachedRegions = await db.getCachedRegions();
      if (cachedRegions.isNotEmpty) {
        regionId = cachedRegions.first.id;
      } else {
        regionId = 'default_region';
      }
    }

    final syncService = SyncService.instance;
    final pois = await syncService.loadPOIsForRegion(regionId);
    
    // Загружаем список открытых POI
    final db = DatabaseHelper.instance;
    final openedIds = await db.getOpenedPOIIds();
    
    setState(() {
      _pois = pois;
      _openedPOIIds = openedIds.toSet();
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

import '../../core/config/app_constants.dart';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Карта Исследователя'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              _loadPOIs();
            },
          ),
          IconButton(
            icon: const Icon(Icons.my_location),
            onPressed: () async {
              final locationService = LocationService.instance;
              final position = await locationService.getCurrentPosition();
              if (position != null) {
                _mapController.move(
                  LatLng(position.latitude, position.longitude),
                  _mapController.camera.zoom,
                );
                setState(() {
                  _currentPosition = position;
                });
              }
            },
          ),
        ],
      ),
      body: FlutterMap(
        mapController: _mapController,
        options: MapOptions(
          initialCenter: center,
          initialZoom: 13.0,
          minZoom: 3.0,
          maxZoom: 18.0,
        ),
        children: [
          TileLayer(
            urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            userAgentPackageName: 'com.explorersmap.app',
          ),
          // Визуализация тумана войны - затемнение закрытых зон
          PolygonLayer(
            polygons: _buildFogOfWarPolygons(),
            polygonCulling: false,
          ),
          // Маркеры POI с разными цветами для открытых/закрытых
          MarkerLayer(
            markers: _pois.map((poi) {
              final isOpened = _openedPOIIds.contains(poi.id);
              return Marker(
                point: LatLng(poi.latitude, poi.longitude),
                width: 40,
                height: 40,
                child: Icon(
                  isOpened ? Icons.place : Icons.place_outlined,
                  color: isOpened ? Colors.green : Colors.grey,
                  size: 40,
                ),
              );
            }).toList(),
          ),
          // Текущая позиция
          if (_currentPosition != null)
            MarkerLayer(
              markers: [
                Marker(
                  point: LatLng(
                    _currentPosition!.latitude,
                    _currentPosition!.longitude,
                  ),
                  width: 30,
                  height: 30,
                  child: const Icon(
                    Icons.my_location,
                    color: Colors.blue,
                    size: 30,
                  ),
                ),
              ],
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () async {
          // Показываем диалог выбора региона
          final result = await showDialog<bool>(
            context: context,
            builder: (context) => const RegionSelectionDialog(),
          );
          
          if (result == true && mounted) {
            // Обновляем список POI после загрузки региона
            await _loadPOIs();
          }
        },
        child: const Icon(Icons.download),
        tooltip: 'Загрузить регион офлайн',
      ),
    );
  }

  /// Создаёт полигоны для визуализации тумана войны
  List<Polygon> _buildFogOfWarPolygons() {
    final polygons = <Polygon>[];
    
    // Для каждого закрытого POI создаём затемнённую область вокруг него
    for (final poi in _pois) {
      if (!_openedPOIIds.contains(poi.id)) {
        // Создаём полигон затемнения вокруг закрытого POI
        final radius = poi.radius ?? 500.0; // Радиус в метрах
        final points = _createCirclePolygon(
          poi.latitude,
          poi.longitude,
          radius,
        );
        
        polygons.add(Polygon(
          points: points,
          color: Colors.black.withOpacity(0.3),
          borderColor: Colors.black.withOpacity(0.5),
          borderStrokeWidth: 2,
          isFilled: true,
        ));
      }
    }
    
    return polygons;
  }

  /// Создаёт полигон окружности вокруг точки
  List<LatLng> _createCirclePolygon(
    double centerLat,
    double centerLon,
    double radiusMeters,
  ) {
    const int points = 32; // Количество точек для окружности
    final pointsList = <LatLng>[];
    
    // Конвертируем радиус из метров в градусы (приблизительно)
    final latDelta = radiusMeters / 111000.0;
    final lonDelta = radiusMeters / (111000.0 * math.cos(centerLat * math.pi / 180));
    
    for (int i = 0; i < points; i++) {
      final angle = 2 * math.pi * i / points;
      final lat = centerLat + latDelta * math.sin(angle);
      final lon = centerLon + lonDelta * math.cos(angle);
      pointsList.add(LatLng(lat, lon));
    }
    
    return pointsList;
  }
}
