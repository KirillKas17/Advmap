import '../database/database_helper.dart';
import '../utils/logger.dart';
import 'dart:convert';

/// Сервис для работы с заметками пользователя к местам
/// Согласно ТЗ: "Заметки пользователя к местам"
class NoteService {
  static final NoteService instance = NoteService._internal();
  NoteService._internal();

  /// Сохраняет заметку к POI
  Future<bool> saveNoteToPOI(String poiId, String note) async {
    try {
      if (note.isEmpty) {
        return await deleteNoteFromPOI(poiId);
      }

      final db = DatabaseHelper.instance;
      final now = DateTime.now().millisecondsSinceEpoch;
      
      await db.database.then((database) async {
        await database.insert(
          'poi_notes',
          {
            'poi_id': poiId,
            'note': note,
            'created_at': now,
            'updated_at': now,
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      });
      
      Logger.info('Заметка сохранена для POI: $poiId');
      return true;
    } catch (e, stackTrace) {
      Logger.error('Ошибка сохранения заметки', e, stackTrace);
      return false;
    }
  }

  /// Получает заметку к POI
  Future<String?> getNoteForPOI(String poiId) async {
    try {
      final db = DatabaseHelper.instance;
      final database = await db.database;
      final results = await database.query(
        'poi_notes',
        where: 'poi_id = ?',
        whereArgs: [poiId],
        limit: 1,
      );

      if (results.isEmpty) return null;
      return results.first['note'] as String?;
    } catch (e, stackTrace) {
      Logger.error('Ошибка получения заметки', e, stackTrace);
      return null;
    }
  }

  /// Удаляет заметку к POI
  Future<bool> deleteNoteFromPOI(String poiId) async {
    try {
      final db = DatabaseHelper.instance;
      final database = await db.database;
      await database.delete(
        'poi_notes',
        where: 'poi_id = ?',
        whereArgs: [poiId],
      );
      return true;
    } catch (e, stackTrace) {
      Logger.error('Ошибка удаления заметки', e, stackTrace);
      return false;
    }
  }

  /// Получает все заметки пользователя
  Future<Map<String, String>> getAllNotes() async {
    try {
      final db = DatabaseHelper.instance;
      final database = await db.database;
      final results = await database.query('poi_notes');
      
      final notes = <String, String>{};
      for (final row in results) {
        notes[row['poi_id'] as String] = row['note'] as String;
      }
      
      return notes;
    } catch (e, stackTrace) {
      Logger.error('Ошибка получения всех заметок', e, stackTrace);
      return {};
    }
  }
}
