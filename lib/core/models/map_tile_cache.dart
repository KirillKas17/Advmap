import 'package:json_annotation/json_annotation.dart';

part 'map_tile_cache.g.dart';

/// Кэш тайла карты для офлайн-режима
@JsonSerializable()
class MapTileCache {
  final int z; // Zoom level
  final int x;
  final int y;
  final String regionId;
  final List<int> tileData; // PNG/JPEG данные
  final DateTime cachedAt;

  MapTileCache({
    required this.z,
    required this.x,
    required this.y,
    required this.regionId,
    required this.tileData,
    required this.cachedAt,
  });

  factory MapTileCache.fromJson(Map<String, dynamic> json) =>
      _$MapTileCacheFromJson(json);
  Map<String, dynamic> toJson() => _$MapTileCacheToJson(this);
  
  String get cacheKey => '$regionId/$z/$x/$y';
}
