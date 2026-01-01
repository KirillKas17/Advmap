import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/models/visit_cluster.dart';

void main() {
  group('VisitCluster', () {
    test('создаёт кластер с корректными данными', () {
      final points = [
        VisitPoint(
          latitude: 55.7558,
          longitude: 37.6173,
          arrivalTime: DateTime(2024, 1, 1, 10, 0),
          departureTime: DateTime(2024, 1, 1, 12, 0),
        ),
        VisitPoint(
          latitude: 55.7560,
          longitude: 37.6175,
          arrivalTime: DateTime(2024, 1, 2, 10, 0),
          departureTime: DateTime(2024, 1, 2, 12, 0),
        ),
      ];

      final cluster = VisitCluster(
        centerLatitude: 55.7559,
        centerLongitude: 37.6174,
        points: points,
        totalVisits: 2,
        totalDuration: const Duration(hours: 4),
      );

      expect(cluster.centerLatitude, equals(55.7559));
      expect(cluster.centerLongitude, equals(37.6174));
      expect(cluster.totalVisits, equals(2));
      expect(cluster.totalDuration, equals(const Duration(hours: 4)));
      expect(cluster.averageDuration, equals(const Duration(hours: 2)));
    });

    test('distanceTo вычисляет расстояние до точки', () {
      final cluster = VisitCluster(
        centerLatitude: 55.7558,
        centerLongitude: 37.6173,
        points: [],
        totalVisits: 0,
        totalDuration: Duration.zero,
      );

      final distance = cluster.distanceTo(55.7658, 37.6173);
      expect(distance, greaterThan(0));
      expect(distance, lessThan(2000)); // Меньше 2 км
    });

    test('averageDuration вычисляет среднее время пребывания', () {
      final points = [
        VisitPoint(
          latitude: 55.7558,
          longitude: 37.6173,
          arrivalTime: DateTime(2024, 1, 1, 10, 0),
          departureTime: DateTime(2024, 1, 1, 12, 0), // 2 часа
        ),
        VisitPoint(
          latitude: 55.7560,
          longitude: 37.6175,
          arrivalTime: DateTime(2024, 1, 2, 10, 0),
          departureTime: DateTime(2024, 1, 2, 14, 0), // 4 часа
        ),
      ];

      final cluster = VisitCluster(
        centerLatitude: 55.7559,
        centerLongitude: 37.6174,
        points: points,
        totalVisits: 2,
        totalDuration: const Duration(hours: 6),
      );

      expect(cluster.averageDuration, equals(const Duration(hours: 3)));
    });
  });

  group('VisitPoint', () {
    test('создаёт точку посещения с корректными данными', () {
      final arrivalTime = DateTime(2024, 1, 1, 10, 0);
      final departureTime = DateTime(2024, 1, 1, 12, 0);
      final point = VisitPoint(
        latitude: 55.7558,
        longitude: 37.6173,
        arrivalTime: arrivalTime,
        departureTime: departureTime,
      );

      expect(point.latitude, equals(55.7558));
      expect(point.longitude, equals(37.6173));
      expect(point.arrivalTime, equals(arrivalTime));
      expect(point.departureTime, equals(departureTime));
      expect(point.duration, equals(const Duration(hours: 2)));
    });

    test('duration возвращает Duration.zero если departureTime отсутствует', () {
      final point = VisitPoint(
        latitude: 55.7558,
        longitude: 37.6173,
        arrivalTime: DateTime(2024, 1, 1, 10, 0),
      );

      expect(point.departureTime, isNull);
      expect(point.duration, equals(Duration.zero));
    });
  });
}
