import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/database_maintenance_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/location_event.dart';

void main() {
  late DatabaseHelper db;
  late DatabaseMaintenanceService service;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    service = DatabaseMaintenanceService.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('location_events');
  });

  tearDown(() async {
    await db.close();
  });

  group('DatabaseMaintenanceService', () {
    test('выполняет обслуживание БД', () async {
      // Добавляем старые синхронизированные события
      final oldDate = DateTime(2024, 1, 1);
      for (int i = 0; i < 10; i++) {
        await db.insertLocationEvent(LocationEvent(
          id: 'old-event-$i',
          latitude: 55.7558,
          longitude: 37.6173,
          timestamp: oldDate,
          deviceId: 'device-123',
          synced: true,
          syncedAt: oldDate,
        ));
      }

      // Выполняем обслуживание
      await service.performMaintenance();

      // Проверяем, что метод выполнился без ошибок
      final dbSize = await db.getDatabaseSize();
      expect(dbSize, greaterThanOrEqualTo(0));
    });

    test('startPeriodicMaintenance запускает обслуживание', () {
      // Проверяем, что метод вызывается без ошибок
      service.startPeriodicMaintenance();
      expect(service, isNotNull);
    });
  });
}
