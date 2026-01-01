import 'package:flutter/material.dart';
import '../../core/database/database_helper.dart';
import '../../core/models/region.dart';
import '../../core/services/sync_service.dart';

/// Диалог выбора региона для загрузки
class RegionSelectionDialog extends StatefulWidget {
  const RegionSelectionDialog({super.key});

  @override
  State<RegionSelectionDialog> createState() => _RegionSelectionDialogState();
}

class _RegionSelectionDialogState extends State<RegionSelectionDialog> {
  List<Region> _availableRegions = [];
  bool _isLoading = true;
  bool _isDownloading = false;
  String? _downloadingRegionId;

  @override
  void initState() {
    super.initState();
    _loadAvailableRegions();
  }

  Future<void> _loadAvailableRegions() async {
    setState(() {
      _isLoading = true;
    });

    // В реальном приложении здесь будет запрос к серверу
    // Для примера используем список популярных регионов
    final popularRegions = [
      Region(
        id: 'moscow',
        name: 'Москва и область',
        bounds: RegionBounds(
          north: 56.0,
          south: 55.0,
          east: 38.0,
          west: 37.0,
        ),
      ),
      Region(
        id: 'spb',
        name: 'Санкт-Петербург и область',
        bounds: RegionBounds(
          north: 60.5,
          south: 59.5,
          east: 31.0,
          west: 29.0,
        ),
      ),
      Region(
        id: 'russia',
        name: 'Вся Россия',
        bounds: RegionBounds(
          north: 82.0,
          south: 41.0,
          east: 180.0,
          west: 19.0,
        ),
      ),
    ];

    // Проверяем, какие регионы уже загружены
    final db = DatabaseHelper.instance;
    final cachedRegions = await db.getCachedRegions();
    final cachedIds = cachedRegions.map((r) => r.id).toSet();

    setState(() {
      _availableRegions = popularRegions;
      _isLoading = false;
    });
  }

  Future<void> _downloadRegion(Region region) async {
    setState(() {
      _isDownloading = true;
      _downloadingRegionId = region.id;
    });

    try {
      final syncService = SyncService.instance;
      final success = await syncService.downloadRegionForOffline(region.id);

      if (mounted) {
        if (success) {
          Navigator.of(context).pop(true);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Регион "${region.name}" успешно загружен'),
            ),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Ошибка загрузки региона'),
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Ошибка: $e'),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isDownloading = false;
          _downloadingRegionId = null;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Выберите регион для загрузки'),
      content: SizedBox(
        width: double.maxFinite,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView.builder(
                shrinkWrap: true,
                itemCount: _availableRegions.length,
                itemBuilder: (context, index) {
                  final region = _availableRegions[index];
                  final isDownloading = _downloadingRegionId == region.id;

                  return ListTile(
                    title: Text(region.name),
                    subtitle: Text(
                      '${region.bounds.north.toStringAsFixed(2)}, ${region.bounds.south.toStringAsFixed(2)}',
                    ),
                    trailing: isDownloading
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.download),
                    onTap: isDownloading ? null : () => _downloadRegion(region),
                  );
                },
              ),
      ),
      actions: [
        TextButton(
          onPressed: _isDownloading
              ? null
              : () => Navigator.of(context).pop(),
          child: const Text('Отмена'),
        ),
      ],
    );
  }
}
