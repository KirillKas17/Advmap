import 'package:flutter_test/flutter_test.dart';
import 'package:explorers_map/core/services/note_service.dart';
import 'package:explorers_map/core/database/database_helper.dart';
import 'package:explorers_map/core/models/poi.dart';

void main() {
  late DatabaseHelper db;
  late NoteService service;

  setUp(() async {
    db = DatabaseHelper.instance;
    await db.initDatabase();
    service = NoteService.instance;
    
    // Очищаем БД
    final database = await db.database;
    await database.delete('poi_notes');
    await database.delete('pois');
    
    // Добавляем тестовый POI
    await db.insertPOI(POI(
      id: 'poi-1',
      name: 'Test POI',
      description: 'Test',
      latitude: 55.7558,
      longitude: 37.6173,
      type: 'landmark',
      geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
      regionId: 'region-1',
    ));
  });

  tearDown(() async {
    await db.close();
  });

  group('NoteService', () {
    test('сохраняет заметку к POI', () async {
      final success = await service.saveNoteToPOI('poi-1', 'Test note');
      expect(success, isTrue);

      final note = await service.getNoteForPOI('poi-1');
      expect(note, equals('Test note'));
    });

    test('получает заметку к POI', () async {
      await service.saveNoteToPOI('poi-1', 'Test note');

      final note = await service.getNoteForPOI('poi-1');
      expect(note, equals('Test note'));
    });

    test('возвращает null для несуществующей заметки', () async {
      final note = await service.getNoteForPOI('poi-nonexistent');
      expect(note, isNull);
    });

    test('удаляет заметку при сохранении пустой строки', () async {
      await service.saveNoteToPOI('poi-1', 'Test note');
      await service.saveNoteToPOI('poi-1', '');

      final note = await service.getNoteForPOI('poi-1');
      expect(note, isNull);
    });

    test('удаляет заметку к POI', () async {
      await service.saveNoteToPOI('poi-1', 'Test note');
      final deleted = await service.deleteNoteFromPOI('poi-1');
      expect(deleted, isTrue);

      final note = await service.getNoteForPOI('poi-1');
      expect(note, isNull);
    });

    test('получает все заметки пользователя', () async {
      await db.insertPOI(POI(
        id: 'poi-2',
        name: 'Test POI 2',
        description: 'Test',
        latitude: 55.7558,
        longitude: 37.6173,
        type: 'landmark',
        geofence: [GeoPoint(latitude: 55.0, longitude: 37.0)],
        regionId: 'region-1',
      ));

      await service.saveNoteToPOI('poi-1', 'Note 1');
      await service.saveNoteToPOI('poi-2', 'Note 2');

      final notes = await service.getAllNotes();
      expect(notes.length, equals(2));
      expect(notes['poi-1'], equals('Note 1'));
      expect(notes['poi-2'], equals('Note 2'));
    });
  });
}
