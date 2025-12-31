import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/services/location_service.dart';
import '../../core/services/sync_service.dart';
import '../../core/database/database_helper.dart';
import '../../core/models/poi.dart';

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
    // TODO: Определить текущий регион
    final syncService = SyncService.instance;
    // Для примера используем тестовый регион
    final pois = await syncService.loadPOIsForRegion('default_region');
    
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
          // Загрузить регион для офлайн-доступа
          final syncService = SyncService.instance;
          // TODO: Показать диалог выбора региона
          await syncService.downloadRegionForOffline('default_region');
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(
                content: Text('Регион загружен для офлайн-доступа'),
              ),
            );
          }
        },
        child: const Icon(Icons.download),
        tooltip: 'Загрузить регион офлайн',
      ),
    );
  }
}
