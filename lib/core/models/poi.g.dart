// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'poi.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

POI _$POIFromJson(Map<String, dynamic> json) => POI(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      type: json['type'] as String,
      geofence: (json['geofence'] as List<dynamic>)
          .map((e) => GeoPoint.fromJson(e as Map<String, dynamic>))
          .toList(),
      radius: (json['radius'] as num?)?.toDouble(),
      regionId: json['regionId'] as String,
      iconUrl: json['iconUrl'] as String?,
      achievementCategory: json['achievementCategory'] as String?,
    );

Map<String, dynamic> _$POIToJson(POI instance) => <String, dynamic>{
      'id': instance.id,
      'name': instance.name,
      'description': instance.description,
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'type': instance.type,
      'geofence': instance.geofence,
      'radius': instance.radius,
      'regionId': instance.regionId,
      'iconUrl': instance.iconUrl,
      'achievementCategory': instance.achievementCategory,
    };

GeoPoint _$GeoPointFromJson(Map<String, dynamic> json) => GeoPoint(
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
    );

Map<String, dynamic> _$GeoPointToJson(GeoPoint instance) => <String, dynamic>{
      'latitude': instance.latitude,
      'longitude': instance.longitude,
    };
