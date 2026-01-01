import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/location_service.dart';
import 'package:explorers_map/core/utils/validators.dart';

void main() {
  group('LocationService', () {
    test('createLocationEvent валидирует координаты', () async {
      final service = LocationService.instance;
      
      // Некорректные координаты должны вернуть null
      final invalidEvent = await service.createLocationEvent(
        latitude: 200.0, // Некорректная широта
        longitude: 0.0,
        deviceId: 'test-device',
      );
      
      expect(invalidEvent, isNull);
    });

    test('checkPOIGeofence использует валидацию', () async {
      final service = LocationService.instance;
      
      // Некорректные координаты должны вернуть null
      final result = await service.checkPOIGeofence(200.0, 0.0);
      
      expect(result, isNull);
    });
  });

  group('Validators', () {
    test('isValidLatitude проверяет диапазон', () {
      expect(Validators.isValidLatitude(0.0), isTrue);
      expect(Validators.isValidLatitude(90.0), isTrue);
      expect(Validators.isValidLatitude(-90.0), isTrue);
      expect(Validators.isValidLatitude(91.0), isFalse);
      expect(Validators.isValidLatitude(-91.0), isFalse);
    });

    test('isValidLongitude проверяет диапазон', () {
      expect(Validators.isValidLongitude(0.0), isTrue);
      expect(Validators.isValidLongitude(180.0), isTrue);
      expect(Validators.isValidLongitude(-180.0), isTrue);
      expect(Validators.isValidLongitude(181.0), isFalse);
      expect(Validators.isValidLongitude(-181.0), isFalse);
    });

    test('isValidCoordinates проверяет обе координаты', () {
      expect(Validators.isValidCoordinates(55.7558, 37.6173), isTrue);
      expect(Validators.isValidCoordinates(200.0, 37.6173), isFalse);
      expect(Validators.isValidCoordinates(55.7558, 200.0), isFalse);
    });
  });
}
