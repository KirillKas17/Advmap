import 'package:flutter/material.dart';
import '../../ui/screens/map_screen.dart';
import '../../ui/screens/home_screen.dart';
import '../../ui/screens/profile_screen.dart';
import '../../core/models/achievement.dart';

/// Роутер для навигации в приложении
class AppRouter {
  static const String map = '/map';
  static const String home = '/home';
  static const String profile = '/profile';
  static const String achievement = '/achievement';

  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case map:
        return MaterialPageRoute(builder: (_) => const MapScreen());
      case home:
        return MaterialPageRoute(builder: (_) => const HomeScreen());
      case profile:
        return MaterialPageRoute(builder: (_) => const ProfileScreen());
      case achievement:
        final achievement = settings.arguments as Achievement?;
        return MaterialPageRoute(
          builder: (_) => AchievementDetailScreen(achievement: achievement),
        );
      default:
        return MaterialPageRoute(builder: (_) => const HomeScreen());
    }
  }

  /// Навигация к экрану достижения
  static void navigateToAchievement(
    BuildContext context,
    Achievement achievement,
  ) {
    Navigator.of(context).pushNamed(
      achievement,
      arguments: achievement,
    );
  }
}

/// Экран деталей достижения
class AchievementDetailScreen extends StatelessWidget {
  final Achievement? achievement;

  const AchievementDetailScreen({
    super.key,
    this.achievement,
  });

  @override
  Widget build(BuildContext context) {
    if (achievement == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Достижение')),
        body: const Center(child: Text('Достижение не найдено')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Достижение'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (achievement!.iconUrl != null)
              Center(
                child: Image.network(
                  achievement!.iconUrl!,
                  width: 100,
                  height: 100,
                ),
              ),
            const SizedBox(height: 16),
            Text(
              achievement!.title,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: 8),
            Text(
              achievement!.description,
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            const SizedBox(height: 16),
            if (achievement!.isUnlocked && achievement!.unlockedAt != null)
              Text(
                'Разблокировано: ${achievement!.unlockedAt!.toString().split('.')[0]}',
                style: TextStyle(color: Colors.green[700]),
              ),
          ],
        ),
      ),
    );
  }
}
