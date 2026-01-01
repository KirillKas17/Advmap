import 'dart:math';
import 'package:geolocator/geolocator.dart';

import '../config/app_config.dart';
import '../database/database_helper.dart';
import '../models/home_work_location.dart';
import '../models/visit_cluster.dart';

/// Сервис для определения дома и работы пользователя через кластеризацию
class HomeWorkDetector {
  static final HomeWorkDetector instance = HomeWorkDetector._internal();
  HomeWorkDetector._internal();

  /// Определяет дом и работу на основе истории посещений
  Future<List<HomeWorkLocation>> detectHomeAndWork({
    required DateTime startDate,
    required DateTime endDate,
  }) async {
    // Получаем данные посещений из БД
    final visitPoints = await _getVisitPoints(startDate, endDate);
    
    if (visitPoints.length < AppConfig.dbscanMinPoints) {
      return [];
    }

    // Применяем алгоритм DBSCAN для кластеризации
    final clusters = _dbscanClustering(visitPoints);

    if (clusters.isEmpty) {
      return [];
    }

    // Сортируем кластеры по общему времени пребывания
    clusters.sort((a, b) => b.totalDuration.compareTo(a.totalDuration));

    // Берём два самых больших кластера
    final topClusters = clusters.take(2).toList();
    if (topClusters.isEmpty) {
      return [];
    }

    // Определяем тип каждого кластера (дом/работа)
    final locations = <HomeWorkLocation>[];

    // Если только один кластер - определяем его тип
    if (topClusters.length == 1) {
      final cluster = topClusters.first;
      final locationType = _classifyCluster(cluster, visitPoints);
      
      locations.add(HomeWorkLocation(
        id: '${locationType.toString()}_${DateTime.now().millisecondsSinceEpoch}',
        type: locationType,
        latitude: cluster.centerLatitude,
        longitude: cluster.centerLongitude,
        radius: _calculateClusterRadius(cluster),
        detectedAt: DateTime.now(),
        verified: false,
      ));
    } else {
      // Если два кластера - определяем тип каждого
      for (int i = 0; i < topClusters.length; i++) {
        final cluster = topClusters[i];
        LocationType locationType;
        
        if (i == 0) {
          // Первый кластер - определяем по времени пребывания
          locationType = _classifyCluster(cluster, visitPoints);
        } else {
          // Второй кластер - противоположный тип
          final firstType = _classifyCluster(topClusters[0], visitPoints);
          locationType = firstType == LocationType.home 
              ? LocationType.work 
              : LocationType.home;
        }

        locations.add(HomeWorkLocation(
          id: '${locationType.toString()}_${DateTime.now().millisecondsSinceEpoch}',
          type: locationType,
          latitude: cluster.centerLatitude,
          longitude: cluster.centerLongitude,
          radius: _calculateClusterRadius(cluster),
          detectedAt: DateTime.now(),
          verified: false,
        ));
      }
    }

    // Сохраняем обнаруженные места в БД
    final db = DatabaseHelper.instance;
    for (final location in locations) {
      await db.insertHomeWorkLocation(location);
    }

    return locations;
  }

  /// Получает точки посещений из БД
  Future<List<VisitPoint>> _getVisitPoints(
    DateTime startDate,
    DateTime endDate,
  ) async {
    final db = DatabaseHelper.instance;
    final rawData = await db.getVisitPointsForClustering(
      startDate: startDate,
      endDate: endDate,
    );

    final visitPoints = <VisitPoint>[];

    for (final row in rawData) {
      final arrivalTime = DateTime.fromMillisecondsSinceEpoch(
        row['arrival_time'] as int,
      );
      final departureTime = row['departure_time'] != null
          ? DateTime.fromMillisecondsSinceEpoch(row['departure_time'] as int)
          : null;

      // Фильтруем слишком короткие посещения
      if (departureTime != null) {
        final duration = departureTime.difference(arrivalTime);
        if (duration.inMinutes < AppConfig.minStayDurationForHomeWork) {
          continue;
        }
      }

      visitPoints.add(VisitPoint(
        latitude: row['latitude'] as double,
        longitude: row['longitude'] as double,
        arrivalTime: arrivalTime,
        departureTime: departureTime,
      ));
    }

    return visitPoints;
  }

  /// Алгоритм DBSCAN для кластеризации точек посещений
  List<VisitCluster> _dbscanClustering(List<VisitPoint> points) {
    if (points.isEmpty) return [];

    final clusters = <VisitCluster>[];
    final visited = <int>{};
    final noise = <int>{};

    for (int i = 0; i < points.length; i++) {
      if (visited.contains(i)) continue;

      visited.add(i);
      final neighbors = _getNeighbors(points, i, AppConfig.dbscanEpsilon);

      if (neighbors.length < AppConfig.dbscanMinPoints) {
        noise.add(i);
        continue;
      }

      // Создаём новый кластер
      final clusterPoints = <VisitPoint>[];
      clusterPoints.add(points[i]);

      // Расширяем кластер
      for (int j = 0; j < neighbors.length; j++) {
        final neighborIdx = neighbors[j];
        if (!visited.contains(neighborIdx)) {
          visited.add(neighborIdx);
          final neighborNeighbors = _getNeighbors(
            points,
            neighborIdx,
            AppConfig.dbscanEpsilon,
          );
          if (neighborNeighbors.length >= AppConfig.dbscanMinPoints) {
            neighbors.addAll(neighborNeighbors);
          }
        }
        if (!noise.contains(neighborIdx)) {
          clusterPoints.add(points[neighborIdx]);
        }
      }

      // Вычисляем центр кластера и общее время
      final center = _calculateClusterCenter(clusterPoints);
      final totalDuration = clusterPoints.fold<Duration>(
        Duration.zero,
        (sum, point) => sum + point.duration,
      );

      clusters.add(VisitCluster(
        centerLatitude: center['lat'] as double,
        centerLongitude: center['lon'] as double,
        points: clusterPoints,
        totalVisits: clusterPoints.length,
        totalDuration: totalDuration,
      ));
    }

    return clusters;
  }

  /// Получает соседей точки в радиусе epsilon
  /// Оптимизированная версия с предварительной фильтрацией
  List<int> _getNeighbors(
    List<VisitPoint> points,
    int pointIndex,
    double epsilon,
  ) {
    final neighbors = <int>[];
    final point = points[pointIndex];

    // Конвертируем epsilon (в градусах) в метры (~111000 метров на градус)
    final epsilonMeters = epsilon * 111000;
    
    // Предварительная фильтрация по приближённому расстоянию (быстрее)
    final latDelta = epsilonMeters / 111000.0;
    final lonDelta = epsilonMeters / (111000.0 * (point.latitude.abs() / 90.0 + 0.1));

    for (int i = 0; i < points.length; i++) {
      if (i == pointIndex) continue;

      final otherPoint = points[i];
      
      // Быстрая проверка по приближённым координатам
      final latDiff = (otherPoint.latitude - point.latitude).abs();
      final lonDiff = (otherPoint.longitude - point.longitude).abs();
      
      if (latDiff > latDelta || lonDiff > lonDelta) {
        continue; // Точка точно не в радиусе
      }

      // Точная проверка расстояния
      final distance = Geolocator.distanceBetween(
        point.latitude,
        point.longitude,
        otherPoint.latitude,
        otherPoint.longitude,
      );

      if (distance <= epsilonMeters) {
        neighbors.add(i);
      }
    }

    return neighbors;
  }

  /// Вычисляет центр кластера (среднее арифметическое координат)
  Map<String, double> _calculateClusterCenter(List<VisitPoint> points) {
    if (points.isEmpty) {
      return {'lat': 0.0, 'lon': 0.0};
    }

    double sumLat = 0.0;
    double sumLon = 0.0;

    for (final point in points) {
      sumLat += point.latitude;
      sumLon += point.longitude;
    }

    return {
      'lat': sumLat / points.length,
      'lon': sumLon / points.length,
    };
  }

  /// Вычисляет радиус кластера (максимальное расстояние от центра до точки)
  double _calculateClusterRadius(VisitCluster cluster) {
    if (cluster.points.isEmpty) {
      return AppConfig.defaultGeofenceRadius;
    }

    double maxDistance = 0.0;

    for (final point in cluster.points) {
      final distance = cluster.distanceTo(
        point.latitude,
        point.longitude,
      );
      if (distance > maxDistance) {
        maxDistance = distance;
      }
    }

    // Добавляем запас 20%
    return maxDistance * 1.2;
  }

  /// Классифицирует кластер как дом или работу
  LocationType _classifyCluster(
    VisitCluster cluster,
    List<VisitPoint> allPoints,
  ) {
    // Подсчитываем время пребывания в разные периоды суток
    int homeScore = 0;
    int workScore = 0;

    for (final point in cluster.points) {
      final hour = point.arrivalTime.hour;
      final weekday = point.arrivalTime.weekday; // 1 = понедельник, 7 = воскресенье
      final isWeekend = weekday == 6 || weekday == 7;

      // Дом: вечер/ночь (20:00-08:00) в будни или весь день в выходные
      if (isWeekend ||
          (hour >= AppConfig.homeStartHour || hour < AppConfig.homeEndHour)) {
        homeScore += point.duration.inMinutes;
      }

      // Работа: день (10:00-18:00) в будни
      if (!isWeekend &&
          hour >= AppConfig.workStartHour &&
          hour < AppConfig.workEndHour) {
        workScore += point.duration.inMinutes;
      }
    }

    // Если кластер первый по размеру и больше похож на дом - это дом
    // Иначе - работа
    return homeScore > workScore ? LocationType.home : LocationType.work;
  }

  /// Проверяет, готовы ли данные для определения дома/работы
  Future<bool> isReadyForDetection() async {
    final db = DatabaseHelper.instance;
    final weekAgo = DateTime.now().subtract(const Duration(days: 7));
    final now = DateTime.now();

    final visitPoints = await _getVisitPoints(weekAgo, now);
    
    // Нужно минимум минимальное количество точек для кластеризации
    if (visitPoints.length < AppConfig.dbscanMinPoints) {
      return false;
    }
    
    // Проверяем, есть ли хотя бы один кластер с достаточным количеством точек
    final clusters = _dbscanClustering(visitPoints);
    if (clusters.isEmpty) {
      return false;
    }
    
    // Проверяем, что есть хотя бы один кластер с достаточным временем пребывания
    final significantClusters = clusters.where((c) {
      return c.totalVisits >= AppConfig.dbscanMinPoints &&
          c.totalDuration.inMinutes >= AppConfig.minStayDurationForHomeWork * 2;
    }).toList();
    
    return significantClusters.isNotEmpty;
  }
  
  /// Проверяет, путешествует ли пользователь (нет постоянного места)
  Future<bool> isTraveling() async {
    final db = DatabaseHelper.instance;
    final monthAgo = DateTime.now().subtract(const Duration(days: 30));
    final now = DateTime.now();
    
    final visitPoints = await _getVisitPoints(monthAgo, now);
    if (visitPoints.length < AppConfig.dbscanMinPoints * 2) {
      return false; // Недостаточно данных
    }
    
    final clusters = _dbscanClustering(visitPoints);
    
    // Если кластеров много (>5) и они распределены по большой территории - путешествие
    if (clusters.length > 5) {
      // Проверяем разброс кластеров
      double maxDistance = 0;
      for (int i = 0; i < clusters.length; i++) {
        for (int j = i + 1; j < clusters.length; j++) {
          final distance = clusters[i].distanceTo(
            clusters[j].centerLatitude,
            clusters[j].centerLongitude,
          );
          if (distance > maxDistance) {
            maxDistance = distance;
          }
        }
      }
      
      // Если максимальное расстояние между кластерами > 1000 км - путешествие
      return maxDistance > 1000000; // 1000 км
    }
    
    return false;
  }
}
