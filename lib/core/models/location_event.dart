import 'package:json_annotation/json_annotation.dart';

part 'location_event.g.dart';

/// Событие геолокации для синхронизации
@JsonSerializable()
class LocationEvent {
  final String id;
  final double latitude;
  final double longitude;
  final DateTime timestamp;
  final String? poiId; // ID POI, если попали в геозону
  final String? regionId; // ID региона
  final String deviceId;
  final bool synced; // Синхронизировано ли с сервером
  final DateTime? syncedAt;

  LocationEvent({
    required this.id,
    required this.latitude,
    required this.longitude,
    required this.timestamp,
    this.poiId,
    this.regionId,
    required this.deviceId,
    this.synced = false,
    this.syncedAt,
  });

  factory LocationEvent.fromJson(Map<String, dynamic> json) => _$LocationEventFromJson(json);
  Map<String, dynamic> toJson() => _$LocationEventToJson(this);
  
  LocationEvent copyWith({
    String? id,
    double? latitude,
    double? longitude,
    DateTime? timestamp,
    String? poiId,
    String? regionId,
    String? deviceId,
    bool? synced,
    DateTime? syncedAt,
  }) {
    return LocationEvent(
      id: id ?? this.id,
      latitude: latitude ?? this.latitude,
      longitude: longitude ?? this.longitude,
      timestamp: timestamp ?? this.timestamp,
      poiId: poiId ?? this.poiId,
      regionId: regionId ?? this.regionId,
      deviceId: deviceId ?? this.deviceId,
      synced: synced ?? this.synced,
      syncedAt: syncedAt ?? this.syncedAt,
    );
  }
}
