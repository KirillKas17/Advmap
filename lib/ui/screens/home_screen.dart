import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/database/database_helper.dart';
import '../../core/models/achievement.dart';
import '../../core/models/home_work_location.dart';
import '../../core/services/home_work_detector.dart';
import '../../core/services/location_service.dart';
import '../../core/services/sync_service.dart';

/// Главный экран с статистикой и достижениями
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<Achievement> _achievements = [];
  List<HomeWorkLocation> _homeWorkLocations = [];
  int _totalVisitedPOIs = 0;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
    _checkHomeWorkDetection();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });

    // Загружаем определённые места
    final db = DatabaseHelper.instance;
    final locations = await db.getHomeWorkLocations(verifiedOnly: true);
    
    // Подсчитываем посещённые POI
    final allPOIs = await db.getAllPOIs();
    // TODO: Получить список открытых POI с сервера или из локальной БД
    _totalVisitedPOIs = allPOIs.length; // Временная заглушка

    setState(() {
      _homeWorkLocations = locations;
      _isLoading = false;
    });
  }

  Future<void> _checkHomeWorkDetection() async {
    final detector = HomeWorkDetector.instance;
    final isReady = await detector.isReadyForDetection();
    
    if (isReady && _homeWorkLocations.isEmpty) {
      // Пытаемся определить дом и работу
      final weekAgo = DateTime.now().subtract(const Duration(days: 7));
      final detected = await detector.detectHomeAndWork(
        startDate: weekAgo,
        endDate: DateTime.now(),
      );

      if (detected.isNotEmpty && mounted) {
        // Показываем диалог подтверждения
        _showHomeWorkConfirmationDialog(detected);
      }
    }
  }

  void _showHomeWorkConfirmationDialog(List<HomeWorkLocation> locations) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Обнаружены ваши места'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: locations.map((location) {
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 8.0),
              child: Text(
                '${location.displayName}: ${location.latitude.toStringAsFixed(4)}, ${location.longitude.toStringAsFixed(4)}',
              ),
            );
          }).toList(),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
            },
            child: const Text('Отклонить'),
          ),
          TextButton(
            onPressed: () async {
              final db = DatabaseHelper.instance;
              for (final location in locations) {
                await db.updateHomeWorkLocationVerification(
                  location.id,
                  true,
                  null,
                );
              }
              Navigator.of(context).pop();
              _loadData();
            },
            child: const Text('Подтвердить'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Главная'),
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: ListView(
          padding: const EdgeInsets.all(16.0),
          children: [
            // Статистика
            _buildStatisticsCard(),
            const SizedBox(height: 16),
            
            // География жизни
            if (_homeWorkLocations.isNotEmpty) ...[
              _buildHomeWorkCard(),
              const SizedBox(height: 16),
            ],
            
            // Достижения
            _buildAchievementsCard(),
          ],
        ),
      ),
    );
  }

  Widget _buildStatisticsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Статистика',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStatItem(
                  'Открыто мест',
                  _totalVisitedPOIs.toString(),
                  Icons.place,
                ),
                _buildStatItem(
                  'Регионов',
                  '0', // TODO: Реализовать подсчёт
                  Icons.map,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatItem(String label, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, size: 32, color: Theme.of(context).primaryColor),
        const SizedBox(height: 8),
        Text(
          value,
          style: const TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            color: Colors.grey[600],
          ),
        ),
      ],
    );
  }

  Widget _buildHomeWorkCard() {
    if (_homeWorkLocations.length < 2) {
      return const SizedBox.shrink();
    }

    final home = _homeWorkLocations.firstWhere(
      (l) => l.type == LocationType.home,
      orElse: () => _homeWorkLocations.first,
    );
    final work = _homeWorkLocations.firstWhere(
      (l) => l.type == LocationType.work,
      orElse: () => _homeWorkLocations.last,
    );

    final distance = Geolocator.distanceBetween(
      home.latitude,
      home.longitude,
      work.latitude,
      work.longitude,
    );

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Ваша география жизни',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      home.displayName,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      '${home.latitude.toStringAsFixed(4)}, ${home.longitude.toStringAsFixed(4)}',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      work.displayName,
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      '${work.latitude.toStringAsFixed(4)}, ${work.longitude.toStringAsFixed(4)}',
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
            Divider(),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Расстояние:'),
                Text(
                  '${(distance / 1000).toStringAsFixed(1)} км',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAchievementsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Достижения',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            if (_achievements.isEmpty)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(32.0),
                  child: Text('Пока нет достижений'),
                ),
              )
            else
              ..._achievements.map((achievement) {
                return ListTile(
                  leading: achievement.iconUrl != null
                      ? Image.network(achievement.iconUrl!)
                      : const Icon(Icons.emoji_events),
                  title: Text(achievement.title),
                  subtitle: Text(achievement.description),
                  trailing: achievement.isUnlocked
                      ? const Icon(Icons.check_circle, color: Colors.green)
                      : null,
                );
              }),
          ],
        ),
      ),
    );
  }
}
