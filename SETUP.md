# Инструкция по настройке и запуску

## Предварительные требования

1. **Flutter SDK** версии 3.0.0 или выше
2. **Android Studio** или **Xcode** (для iOS)
3. **Git**

## Установка зависимостей

```bash
flutter pub get
```

## Генерация кода

Для генерации файлов сериализации JSON:

```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

## Настройка Firebase

### Android

1. Создайте проект в [Firebase Console](https://console.firebase.google.com/)
2. Добавьте Android приложение с package name: `com.explorersmap.app`
3. Скачайте `google-services.json`
4. Поместите файл в `android/app/google-services.json`
5. Добавьте в `android/build.gradle`:
```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```
6. Добавьте в `android/app/build.gradle` в конец файла:
```gradle
apply plugin: 'com.google.gms.google-services'
```

### iOS

1. В Firebase Console добавьте iOS приложение с bundle ID из Xcode проекта
2. Скачайте `GoogleService-Info.plist`
3. Поместите файл в `ios/Runner/GoogleService-Info.plist`
4. Добавьте в `ios/Podfile`:
```ruby
pod 'Firebase/Messaging'
```

## Настройка разрешений

### Android

Разрешения уже настроены в `android/app/src/main/AndroidManifest.xml`:
- `ACCESS_FINE_LOCATION`
- `ACCESS_COARSE_LOCATION`
- `ACCESS_BACKGROUND_LOCATION`
- `INTERNET`
- `WAKE_LOCK`
- `RECEIVE_BOOT_COMPLETED`

### iOS

Разрешения настроены в `ios/Runner/Info.plist`:
- `NSLocationWhenInUseUsageDescription`
- `NSLocationAlwaysAndWhenInUseUsageDescription`
- `NSLocationAlwaysUsageDescription`

## Запуск приложения

### Android

```bash
flutter run
```

Или через Android Studio:
1. Откройте проект в Android Studio
2. Выберите устройство/эмулятор
3. Нажмите Run

### iOS

```bash
flutter run
```

Или через Xcode:
1. Откройте `ios/Runner.xcworkspace`
2. Выберите устройство/симулятор
3. Нажмите Run

## Настройка сервера

Приложение ожидает API сервера по адресу, указанному в `lib/core/config/app_config.dart`:
- `apiBaseUrl`: `https://api.explorersmap.com`

### Endpoints API

1. **POST /api/v1/events/sync** - синхронизация событий геолокации
   ```json
   {
     "events": [
       {
         "id": "string",
         "latitude": 0.0,
         "longitude": 0.0,
         "timestamp": "ISO8601",
         "poiId": "string?",
         "regionId": "string?",
         "deviceId": "string"
       }
     ]
   }
   ```

2. **GET /api/v1/regions/{regionId}/pois** - получение POI региона
   ```json
   {
     "pois": [...]
   }
   ```

3. **GET /api/v1/regions/{regionId}/map-data** - получение данных карты региона

4. **POST /api/v1/achievements/unlock** - разблокировка ачивки
   ```json
   {
     "achievement_id": "string"
   }
   ```

## Тестирование

Для запуска тестов:

```bash
flutter test
```

## Сборка релизной версии

### Android

```bash
flutter build apk --release
```

или для App Bundle:

```bash
flutter build appbundle --release
```

### iOS

```bash
flutter build ios --release
```

## Отладка

### Проверка фонового отслеживания

1. Включите фоновое отслеживание в настройках профиля
2. Предоставьте разрешение "Всегда" для геолокации
3. Сверните приложение
4. Проверьте логи:
```bash
flutter logs
```

### Проверка синхронизации

1. Отключите интернет
2. Посетите несколько мест
3. Включите интернет
4. Откройте приложение и проверьте синхронизацию в профиле

## Известные ограничения

1. Для работы фонового отслеживания на Android требуется разрешение "Всегда"
2. На iOS фоновое отслеживание работает только когда приложение активно или в фоновом режиме
3. Для полной функциональности требуется настроенный сервер API
