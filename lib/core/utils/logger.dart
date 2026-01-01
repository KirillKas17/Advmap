import 'dart:developer' as developer;

/// Утилита для логирования
class Logger {
  static void info(String message, [String? tag]) {
    developer.log(message, name: tag ?? 'ExplorersMap');
  }

  static void error(String message, [Object? error, StackTrace? stackTrace]) {
    developer.log(
      message,
      name: 'ExplorersMap',
      error: error,
      stackTrace: stackTrace,
    );
  }

  static void warning(String message, [String? tag]) {
    developer.log(message, name: tag ?? 'ExplorersMap', level: 900);
  }

  static void debug(String message, [String? tag]) {
    developer.log(message, name: tag ?? 'ExplorersMap', level: 500);
  }
}
