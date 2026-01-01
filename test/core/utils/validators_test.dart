import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/utils/validators.dart';

void main() {
  group('Validators', () {
    group('isValidLatitude', () {
      test('валидирует корректные значения широты', () {
        expect(Validators.isValidLatitude(0.0), isTrue);
        expect(Validators.isValidLatitude(90.0), isTrue);
        expect(Validators.isValidLatitude(-90.0), isTrue);
        expect(Validators.isValidLatitude(45.5), isTrue);
        expect(Validators.isValidLatitude(-45.5), isTrue);
      });

      test('отклоняет некорректные значения широты', () {
        expect(Validators.isValidLatitude(91.0), isFalse);
        expect(Validators.isValidLatitude(-91.0), isFalse);
        expect(Validators.isValidLatitude(180.0), isFalse);
        expect(Validators.isValidLatitude(-180.0), isFalse);
      });
    });

    group('isValidLongitude', () {
      test('валидирует корректные значения долготы', () {
        expect(Validators.isValidLongitude(0.0), isTrue);
        expect(Validators.isValidLongitude(180.0), isTrue);
        expect(Validators.isValidLongitude(-180.0), isTrue);
        expect(Validators.isValidLongitude(45.5), isTrue);
        expect(Validators.isValidLongitude(-45.5), isTrue);
      });

      test('отклоняет некорректные значения долготы', () {
        expect(Validators.isValidLongitude(181.0), isFalse);
        expect(Validators.isValidLongitude(-181.0), isFalse);
        expect(Validators.isValidLongitude(360.0), isFalse);
        expect(Validators.isValidLongitude(-360.0), isFalse);
      });
    });

    group('isValidCoordinates', () {
      test('валидирует корректные координаты', () {
        expect(Validators.isValidCoordinates(55.7558, 37.6173), isTrue);
        expect(Validators.isValidCoordinates(0.0, 0.0), isTrue);
        expect(Validators.isValidCoordinates(90.0, 180.0), isTrue);
        expect(Validators.isValidCoordinates(-90.0, -180.0), isTrue);
      });

      test('отклоняет некорректные координаты', () {
        expect(Validators.isValidCoordinates(200.0, 37.6173), isFalse);
        expect(Validators.isValidCoordinates(55.7558, 200.0), isFalse);
        expect(Validators.isValidCoordinates(91.0, 37.6173), isFalse);
        expect(Validators.isValidCoordinates(55.7558, 181.0), isFalse);
      });
    });

    group('isValidRadius', () {
      test('валидирует корректные радиусы', () {
        expect(Validators.isValidRadius(1.0), isTrue);
        expect(Validators.isValidRadius(100.0), isTrue);
        expect(Validators.isValidRadius(100000.0), isTrue);
        expect(Validators.isValidRadius(null), isTrue);
      });

      test('отклоняет некорректные радиусы', () {
        expect(Validators.isValidRadius(0.0), isFalse);
        expect(Validators.isValidRadius(-1.0), isFalse);
        expect(Validators.isValidRadius(100001.0), isFalse);
      });
    });

    group('isValidId', () {
      test('валидирует корректные ID', () {
        expect(Validators.isValidId('test-id'), isTrue);
        expect(Validators.isValidId('a'), isTrue);
        expect(Validators.isValidId('a' * 255), isTrue);
      });

      test('отклоняет некорректные ID', () {
        expect(Validators.isValidId(null), isFalse);
        expect(Validators.isValidId(''), isFalse);
        expect(Validators.isValidId('a' * 256), isFalse);
      });
    });

    group('isValidName', () {
      test('валидирует корректные названия', () {
        expect(Validators.isValidName('Test Name'), isTrue);
        expect(Validators.isValidName('a'), isTrue);
        expect(Validators.isValidName('a' * 500), isTrue);
      });

      test('отклоняет некорректные названия', () {
        expect(Validators.isValidName(null), isFalse);
        expect(Validators.isValidName(''), isFalse);
        expect(Validators.isValidName('a' * 501), isFalse);
      });
    });

    group('isValidGeofence', () {
      test('валидирует корректные геозоны', () {
        final validGeofence = [
          {'latitude': 55.0, 'longitude': 37.0},
          {'latitude': 56.0, 'longitude': 37.0},
          {'latitude': 56.0, 'longitude': 38.0},
          {'latitude': 55.0, 'longitude': 38.0},
        ];
        expect(Validators.isValidGeofence(validGeofence), isTrue);
      });

      test('отклоняет геозоны с недостаточным количеством точек', () {
        final invalidGeofence = [
          {'latitude': 55.0, 'longitude': 37.0},
          {'latitude': 56.0, 'longitude': 37.0},
        ];
        expect(Validators.isValidGeofence(invalidGeofence), isFalse);
        expect(Validators.isValidGeofence([]), isFalse);
      });

      test('отклоняет геозоны с некорректными координатами', () {
        final invalidGeofence = [
          {'latitude': 200.0, 'longitude': 37.0},
          {'latitude': 56.0, 'longitude': 37.0},
          {'latitude': 56.0, 'longitude': 38.0},
        ];
        expect(Validators.isValidGeofence(invalidGeofence), isFalse);
      });

      test('отклоняет геозоны с некорректной структурой', () {
        expect(Validators.isValidGeofence(['invalid']), isFalse);
        expect(Validators.isValidGeofence([null]), isFalse);
      });
    });
  });
}
