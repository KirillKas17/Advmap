// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'map_tile_cache.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

MapTileCache _$MapTileCacheFromJson(Map<String, dynamic> json) =>
    MapTileCache(
      z: json['z'] as int,
      x: json['x'] as int,
      y: json['y'] as int,
      regionId: json['regionId'] as String,
      tileData: (json['tileData'] as List<dynamic>).map((e) => e as int).toList(),
      cachedAt: DateTime.parse(json['cachedAt'] as String),
    );

Map<String, dynamic> _$MapTileCacheToJson(MapTileCache instance) =>
    <String, dynamic>{
      'z': instance.z,
      'x': instance.x,
      'y': instance.y,
      'regionId': instance.regionId,
      'tileData': instance.tileData,
      'cachedAt': instance.cachedAt.toIso8601String(),
    };
