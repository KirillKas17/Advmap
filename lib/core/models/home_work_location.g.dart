// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'home_work_location.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

HomeWorkLocation _$HomeWorkLocationFromJson(Map<String, dynamic> json) =>
    HomeWorkLocation(
      id: json['id'] as String,
      type: $enumDecode(_$LocationTypeEnumMap, json['type']),
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      radius: (json['radius'] as num).toDouble(),
      detectedAt: DateTime.parse(json['detectedAt'] as String),
      verified: json['verified'] as bool? ?? false,
      verifiedAt: json['verifiedAt'] == null
          ? null
          : DateTime.parse(json['verifiedAt'] as String),
      customName: json['customName'] as String?,
    );

Map<String, dynamic> _$HomeWorkLocationToJson(HomeWorkLocation instance) =>
    <String, dynamic>{
      'id': instance.id,
      'type': $enumDecode(_$LocationTypeEnumMap, instance.type),
      'latitude': instance.latitude,
      'longitude': instance.longitude,
      'radius': instance.radius,
      'detectedAt': instance.detectedAt.toIso8601String(),
      'verified': instance.verified,
      'verifiedAt': instance.verifiedAt?.toIso8601String(),
      'customName': instance.customName,
    };

const _$LocationTypeEnumMap = {
  LocationType.home: 'home',
  LocationType.work: 'work',
};

T $enumDecode<T>(
  Map<T, Object> enumValues,
  Object? source, {
  T? unknownValue,
}) {
  if (source == null) {
    throw ArgumentError(
      'A value must be provided. Supported values: '
      '${enumValues.values.join(', ')}',
    );
  }

  return enumValues.entries.singleWhere(
    (e) => e.value == source,
    orElse: () {
      if (unknownValue == null) {
        throw ArgumentError(
          '`$source` is not one of the supported values: '
          '${enumValues.values.join(', ')}',
        );
      }
      return MapEntry(unknownValue as T, unknownValue as Object);
    },
  ).key;
}
