import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/models/achievement.dart';

void main() {
  group('Achievement', () {
    test('создаёт достижение с корректными данными', () {
      final achievement = Achievement(
        id: 'achievement-123',
        title: 'Test Achievement',
        description: 'Test Description',
        category: 'exploration',
      );

      expect(achievement.id, equals('achievement-123'));
      expect(achievement.title, equals('Test Achievement'));
      expect(achievement.description, equals('Test Description'));
      expect(achievement.category, equals('exploration'));
      expect(achievement.isUnlocked, isFalse);
    });

    test('создаёт разблокированное достижение', () {
      final unlockedAt = DateTime(2024, 1, 1);
      final achievement = Achievement(
        id: 'achievement-123',
        title: 'Test Achievement',
        description: 'Test Description',
        category: 'exploration',
        unlockedAt: unlockedAt,
      );

      expect(achievement.isUnlocked, isTrue);
      expect(achievement.unlockedAt, equals(unlockedAt));
    });

    test('isUnlocked возвращает true только при наличии unlockedAt', () {
      final locked = Achievement(
        id: 'achievement-123',
        title: 'Test',
        description: 'Test',
        category: 'exploration',
      );
      expect(locked.isUnlocked, isFalse);

      final unlocked = Achievement(
        id: 'achievement-123',
        title: 'Test',
        description: 'Test',
        category: 'exploration',
        unlockedAt: DateTime.now(),
      );
      expect(unlocked.isUnlocked, isTrue);
    });

    test('toJson и fromJson работают корректно', () {
      final original = Achievement(
        id: 'achievement-123',
        title: 'Test Achievement',
        description: 'Test Description',
        category: 'exploration',
        iconUrl: 'https://example.com/icon.png',
        unlockedAt: DateTime(2024, 1, 1),
        progress: {'value': 50, 'max': 100},
      );

      final json = original.toJson();
      final restored = Achievement.fromJson(json);

      expect(restored.id, equals(original.id));
      expect(restored.title, equals(original.title));
      expect(restored.description, equals(original.description));
      expect(restored.category, equals(original.category));
      expect(restored.iconUrl, equals(original.iconUrl));
      expect(restored.progress, equals(original.progress));
    });
  });
}
