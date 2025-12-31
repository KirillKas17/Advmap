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
    
    setState(() {
      _pois = pois;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    final center = _currentPosition != null
        ? LatLng(_currentPosition!.latitude, _currentPosition!.longitude)
        : const LatLng(55.7558, 37.6173); // Москва по умолчанию

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
          // Маркеры POI
          MarkerLayer(
            markers: _pois.map((poi) {
              return Marker(
                point: LatLng(poi.latitude, poi.longitude),
                width: 40,
                height: 40,
                child: Icon(
                  Icons.place,
                  color: Colors.red,
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
}
