# Тесты проекта Explorers Map

## Структура тестов

Проект покрыт комплексными тестами на всех уровнях:

### Юнит тесты (`test/core/`)

#### Утилиты (`test/core/utils/`)
- `validators_test.dart` - тесты валидации координат, ID, названий, геозон
- `coordinate_utils_test.dart` - тесты работы с координатами и расстояниями

#### Модели (`test/core/models/`)
- `location_event_test.dart` - тесты модели события геолокации
- `poi_test.dart` - тесты модели точки интереса (POI)
- `achievement_test.dart` - тесты модели достижения
- `home_work_location_test.dart` - тесты модели локации дома/работы
- `region_test.dart` - тесты модели региона
- `visit_cluster_test.dart` - тесты модели кластера посещений

#### База данных (`test/core/database/`)
- `database_helper_test.dart` - тесты всех методов работы с БД:
  - События геолокации (вставка, получение, синхронизация)
  - POI (вставка, поиск, открытие)
  - Локации дома/работы
  - Регионы
  - Достижения
  - Очистка данных

#### Сервисы (`test/core/services/`)
- `location_service_test.dart` - тесты сервиса геолокации
- `achievement_service_test.dart` - тесты сервиса достижений
- `region_detector_test.dart` - тесты определения региона
- `home_work_detector_test.dart` - тесты определения дома/работы
- `note_service_test.dart` - тесты сервиса заметок
- `recommendation_service_test.dart` - тесты сервиса рекомендаций
- `database_maintenance_service_test.dart` - тесты обслуживания БД

### Интеграционные тесты (`test/integration/`)

- `location_sync_integration_test.dart` - интеграция создания событий и синхронизации
- `achievement_unlock_integration_test.dart` - интеграция открытия POI и разблокировки ачивок
- `home_work_detection_integration_test.dart` - интеграция определения дома/работы

### E2E тесты (`test/e2e/`)

- `main_user_flows_test.dart` - основные пользовательские сценарии:
  - Открытие новых мест и получение ачивок
  - Определение дома и работы
  - Получение рекомендаций мест
  - Синхронизация данных с сервером

## Запуск тестов

```bash
# Все тесты
flutter test

# Конкретная группа тестов
flutter test test/core/utils/validators_test.dart

# Интеграционные тесты
flutter test test/integration/

# E2E тесты
flutter test test/e2e/
```

## Покрытие функционала

### ✅ Полностью покрыто тестами:

1. **Валидация данных** - все валидаторы
2. **Работа с координатами** - вычисление расстояний, нормализация
3. **Модели данных** - все модели с сериализацией
4. **База данных** - все CRUD операции
5. **Сервисы**:
   - LocationService - создание событий, проверка геозон
   - AchievementService - проверка и разблокировка ачивок
   - RegionDetector - определение региона
   - HomeWorkDetector - определение дома/работы
   - NoteService - работа с заметками
   - RecommendationService - рекомендации мест
   - DatabaseMaintenanceService - обслуживание БД

### ⚠️ Требуют моков для полного покрытия:

1. **SyncService** - требует мокирования HTTP запросов
2. **PushNotificationService** - требует мокирования Firebase
3. **BackgroundService** - требует мокирования Workmanager

## Примечания

- Тесты используют реальную SQLite БД в памяти для изоляции
- Каждый тест очищает БД перед выполнением
- Интеграционные тесты проверяют взаимодействие компонентов
- E2E тесты покрывают основные пользовательские сценарии
