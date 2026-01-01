// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'region.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

Region _$RegionFromJson(Map<String, dynamic> json) => Region(
      id: json['id'] as String,
      name: json['name'] as String,
      bounds: RegionBounds.fromJson(json['bounds'] as Map<String, dynamic>),
      downloadedAt: json['downloadedAt'] == null
          ? null
          : DateTime.parse(json['downloadedAt'] as String),
      lastUpdated: json['lastUpdated'] == null
          ? null
          : DateTime.parse(json['lastUpdated'] as String),
    );

Map<String, dynamic> _$RegionToJson(Region instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'bounds': instance.bounds,
      'downloadedAt': instance.downloadedAt?.toIso8601String(),
      'lastUpdated': instance.lastUpdated?.toIso8601String(),
    };

RegionBounds _$RegionBoundsFromJson(Map<String, dynamic> json) =>
    RegionBounds(
      north: (json['north'] as num).toDouble(),
      south: (json['south'] as num).toDouble(),
      east: (json['east'] as num).toDouble(),
      west: (json['west'] as num).toDouble(),
    );

Map<String, dynamic> _$RegionBoundsToJson(RegionBounds instance) =>
    <String, dynamic>{
      'north': instance.north,
      'south': instance.south,
      'east': instance.east,
      'west': instance.west,
    };
