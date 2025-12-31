import '../database/database_helper.dart';
import '../utils/logger.dart';
import '../config/app_constants.dart';

/// Сервис для обслуживания базы данных
class DatabaseMaintenanceService {
  static final DatabaseMaintenanceService instance = DatabaseMaintenanceService._internal();
  DatabaseMaintenanceService._internal();

  /// Выполняет периодическое обслуживание БД
  Future<void> performMaintenance() async {
    try {
      Logger.info('Начало обслуживания БД');
      
      final db = DatabaseHelper.instance;
      
      // Проверяем размер БД
      final dbSize = await db.getDatabaseSize();
      final dbSizeMB = dbSize / (1024 * 1024);
      
      Logger.info('Размер БД: ${dbSizeMB.toStringAsFixed(2)} MB');
      
      // Если БД слишком большая, выполняем очистку
      if (dbSizeMB > AppConstants.maxDatabaseSizeMB) {
        Logger.warning('БД превышает максимальный размер, выполняется очистка');
        await _performCleanup();
      } else {
        // Периодическая очистка старых данных
        await _performCleanup();
      }
      
      Logger.info('Обслуживание БД завершено');
    } catch (e, stackTrace) {
      Logger.error('Ошибка обслуживания БД', e, stackTrace);
    }
  }

  /// Выполняет очистку старых данных
  Future<void> _performCleanup() async {
    final db = DatabaseHelper.instance;
    
    final cleanupResult = await db.performDatabaseCleanup(
      daysToKeepSynced: AppConstants.keepSyncedEventsDays,
      keepLastUnsynced: AppConstants.maxEventsInQueue,
    );
    
    Logger.info(
      'Очистка БД: удалено ${cleanupResult['synced_deleted']} синхронизированных '
      'и ${cleanupResult['unsynced_deleted']} несинхронизированных событий',
    );
  }

  /// Запускает периодическое обслуживание
  void startPeriodicMaintenance() {
    // Выполняем обслуживание при запуске
    performMaintenance();
    
    // Периодическое обслуживание будет выполняться при каждом запуске приложения
    // Для более частого обслуживания можно настроить через Workmanager
    // с отдельной задачей, но это не критично для продакшена
  }
}
