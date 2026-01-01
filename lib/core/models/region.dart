import 'package:json_annotation/json_annotation.dart';

part 'region.g.dart';

/// Регион для офлайн-карт
@JsonSerializable()
class Region {
  final String id;
  final String name;
  final RegionBounds bounds;
  final DateTime? downloadedAt;
  final DateTime? lastUpdated;

  Region({
    required this.id,
    required this.name,
    required this.bounds,
    this.downloadedAt,
    this.lastUpdated,
  });

  factory Region.fromJson(Map<String, dynamic> json) => _$RegionFromJson(json);
  Map<String, dynamic> toJson() => _$RegionToJson(this);
}

@JsonSerializable()
class RegionBounds {
  final double north;
  final double south;
  final double east;
  final double west;

  RegionBounds({
    required this.north,
    required this.south,
    required this.east,
    required this.west,
  });

  factory RegionBounds.fromJson(Map<String, dynamic> json) =>
      _$RegionBoundsFromJson(json);
  Map<String, dynamic> toJson() => _$RegionBoundsToJson(this);
}
