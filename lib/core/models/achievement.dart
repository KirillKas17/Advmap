import 'package:json_annotation/json_annotation.dart';

part 'achievement.g.dart';

/// Достижение (ачивка)
@JsonSerializable()
class Achievement {
  final String id;
  final String title;
  final String description;
  final String category;
  final String? iconUrl;
  final DateTime? unlockedAt;
  final Map<String, dynamic>? progress; // Прогресс выполнения

  Achievement({
    required this.id,
    required this.title,
    required this.description,
    required this.category,
    this.iconUrl,
    this.unlockedAt,
    this.progress,
  });

  factory Achievement.fromJson(Map<String, dynamic> json) => _$AchievementFromJson(json);
  Map<String, dynamic> toJson() => _$AchievementToJson(this);
  
  bool get isUnlocked => unlockedAt != null;
}
