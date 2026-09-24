import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/friendly_error.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'notification_preferences_screen.dart';
import 'unread_store.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key, this.onOpenBookings});

  final VoidCallback? onOpenBookings;

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<dynamic>? _notifications;
  String? _error;
  UnreadStore? _store;
  int _lastSeenCount = 0;

  int get _unreadCount {
    final items = _notifications;
    if (items == null) return 0;
    return items
        .where((n) => (n as Map<String, dynamic>)['read_at'] == null)
        .length;
  }

  void _syncBadge() {
    _store?.setCount(_unreadCount);
  }

  void _onStoreChanged() {
    final store = _store;
    if (store == null || !mounted) return;
    // Badge grew (a push landed) while we already have a list — refresh so the
    // new row appears as unread without the user pulling to refresh.
    if (store.count > _lastSeenCount) {
      _load();
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final store = context.read<UnreadStore>();
    if (!identical(store, _store)) {
      _store?.removeListener(_onStoreChanged);
      _store = store;
      _store!.addListener(_onStoreChanged);
      _lastSeenCount = store.count;
    }
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _store?.removeListener(_onStoreChanged);
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final data = await context.read<ApiClient>().get('/notifications/');
      final list = data is Map ? data['results'] : data;
      if (!mounted) return;
      setState(() {
        _notifications = (list as List<dynamic>? ?? []);
        _error = null;
      });
      _lastSeenCount = _unreadCount;
      _syncBadge();
    } catch (e) {
      debugPrint('NOTIF load failed: $e');
      if (!mounted) return;
      final l10n = AppLocalizations.of(context);
      setState(() => _error = friendlyErrorMessage(e, l10n));
    }
  }

  /// Optimistic: flip `read_at` in place so the row updates instantly, then
  /// confirm against the API (and reload if the server disagrees).
  Future<void> _markRead(Map<String, dynamic> notification) async {
    if (notification['read_at'] != null) return;
    setState(() {
      notification['read_at'] = DateTime.now().toIso8601String();
    });
    _lastSeenCount = _unreadCount;
    _syncBadge();
    try {
      await context
          .read<ApiClient>()
          .post('/notifications/${notification['id']}/read/');
    } catch (_) {
      if (mounted) _load();
    }
  }

  Future<void> _markAllRead() async {
    if (_unreadCount == 0) return;
    setState(() {
      for (final n in _notifications ?? []) {
        final map = n as Map<String, dynamic>;
        map['read_at'] ??= DateTime.now().toIso8601String();
      }
    });
    _lastSeenCount = 0;
    _syncBadge();
    try {
      await context.read<ApiClient>().post('/notifications/read-all/');
    } catch (_) {
      // read-all is optional on older backends; local state already shows read.
    }
    if (mounted) _load();
  }

  void _handleTap(Map<String, dynamic> notification) {
    _markRead(notification);
    final eventType = (notification['event_type'] as String?) ?? '';
    if (eventType.contains('booking') || eventType.contains('payment')) {
      widget.onOpenBookings?.call();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.notifications),
        actions: [
          if (_unreadCount > 0)
            TextButton(
              onPressed: _markAllRead,
              child: Text(
                l10n.markAllRead,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          IconButton(
            icon: const Icon(Icons.tune),
            iconSize: 22,
            style: IconButton.styleFrom(
              minimumSize: const Size(44, 44),
              tapTargetSize: MaterialTapTargetSize.padded,
            ),
            tooltip: l10n.notificationSettings,
            onPressed: () async {
              await Navigator.of(context).push(MaterialPageRoute(
                builder: (_) => const NotificationPreferencesScreen(),
              ));
              if (mounted) _load();
            },
          ),
        ],
      ),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_error != null) {
      return ErrorState(onRetry: _load);
    }
    final items = _notifications;
    if (items == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (items.isEmpty) {
      return EmptyState(
        icon: Icons.notifications_none,
        title: l10n.noNotifications,
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(AppSpacing.md),
        itemCount: items.length,
        itemBuilder: (context, i) {
          final n = items[i] as Map<String, dynamic>;
          final read = n['read_at'] != null;
          return Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.sm),
            child: Card(
              // Unread rows get a brand border so "new" is obvious at a glance.
              shape: read
                  ? null
                  : RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
                      side: BorderSide(
                        color: Theme.of(context).colorScheme.primary,
                        width: 1.4,
                      ),
                    ),
              child: ListTile(
                leading: Stack(
                  clipBehavior: Clip.none,
                  children: [
                    Icon(
                      _iconFor(n['event_type'] as String?),
                      size: 28,
                      color: read
                          ? Theme.of(context).colorScheme.onSurface.withValues(
                                alpha: 0.4,
                              )
                          : Theme.of(context).colorScheme.primary,
                    ),
                    if (!read)
                      Positioned(
                        top: -2,
                        right: -2,
                        child: Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            color: AppColors.danger,
                            shape: BoxShape.circle,
                            border: Border.all(
                              color: Theme.of(context).colorScheme.surface,
                              width: 1.5,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
                title: Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${n['title']}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontWeight: read ? FontWeight.normal : FontWeight.w800,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    if (!read) ...[
                      const SizedBox(width: 8),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 3,
                        ),
                        decoration: BoxDecoration(
                          color: AppColors.accentSoft,
                          borderRadius: BorderRadius.circular(999),
                        ),
                        child: Text(
                          l10n.newBadge,
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            color: AppColors.brandReadable,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if ('${n['body']}'.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        '${n['body']}',
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontWeight: read ? FontWeight.normal : FontWeight.w500,
                        ),
                      ),
                    ],
                    const SizedBox(height: 4),
                    Text(
                      relativeTime(l10n, n['created_at'] as String?),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
                isThreeLine: true,
                onTap: () => _handleTap(n),
                onLongPress: read ? null : () => _markRead(n),
                trailing: read
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.done),
                        iconSize: 22,
                        tooltip: l10n.markRead,
                        onPressed: () => _markRead(n),
                      ),
              ),
            ),
          );
        },
      ),
    );
  }

  IconData _iconFor(String? eventType) {
    if (eventType == null) return Icons.notifications_none;
    if (eventType.contains('booking')) return Icons.event_available_outlined;
    if (eventType.contains('payment') || eventType.contains('transfer')) return Icons.payments_outlined;
    if (eventType.contains('tournament')) return Icons.emoji_events_outlined;
    if (eventType.contains('news')) return Icons.article_outlined;
    if (eventType.contains('no_show')) return Icons.person_off_outlined;
    return Icons.notifications_none;
  }
}
