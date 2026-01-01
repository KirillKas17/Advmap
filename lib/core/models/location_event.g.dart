// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'location_event.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

LocationEvent _$LocationEventFromJson(Map<String, dynamic> json) => LocationEvent(
      id: json['id'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
      poiId: json['poiId'] as String?,
      regionId: json['regionId'] as String?,
      deviceId: json['deviceId'] as String,
      synced: json['synced'] as bool? ?? false,
      syncedAt: json['syncedAt'] == null
          ? null
          : DateTime.parse(json['syncedAt'] as String),
    );

Map<String, dynamic> _$LocationEventToJson(LocationEvent event) => <String, dynamic>{
      'id': event.id,
      'latitude': event.latitude,
      'longitude': event.longitude,
      'timestamp': event.timestamp.toIso8601String(),
      'poiId': event.poiId,
      'regionId': event.regionId,
      'deviceId': event.deviceId,
      'synced': event.synced,
      'syncedAt': event.syncedAt?.toIso8601String(),
    };
