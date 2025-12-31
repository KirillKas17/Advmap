import 'package:json_annotation/json_annotation.dart';

part 'home_work_location.g.dart';

/// Определённое место жизни (дом или работа)
@JsonSerializable()
class HomeWorkLocation {
  final String id;
  final LocationType type; // home или work
  final double latitude;
  final double longitude;
  final double radius; // Радиус в метрах
  final DateTime detectedAt;
  final bool verified; // Подтверждено ли пользователем
  final DateTime? verifiedAt;
  final String? customName; // Кастомное имя от пользователя

  HomeWorkLocation({
    required this.id,
    required this.type,
    required this.latitude,
    required this.longitude,
    required this.radius,
    required this.detectedAt,
    this.verified = false,
    this.verifiedAt,
    this.customName,
  });

  factory HomeWorkLocation.fromJson(Map<String, dynamic> json) => _$HomeWorkLocationFromJson(json);
  Map<String, dynamic> toJson() => _$HomeWorkLocationToJson(this);
  
  String get displayName {
    if (customName != null && customName!.isNotEmpty) {
      return customName!;
    }
    return type == LocationType.home ? 'Дом' : 'Работа';
  }
}

enum LocationType {
  @JsonValue('home')
  home,
  @JsonValue('work')
  work,
}
