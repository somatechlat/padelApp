import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'notification_preferences_screen.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key, this.onOpenBookings});

  final VoidCallback? onOpenBookings;

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<dynamic>? _notifications;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await context.read<ApiClient>().get('/notifications/');
      final list = data is Map ? data['results'] : data;
      setState(() {
        _notifications = (list as List<dynamic>? ?? []);
        _error = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  Future<void> _markRead(Map<String, dynamic> notification) async {
    if (notification['read_at'] != null) return;
    try {
      await context
          .read<ApiClient>()
          .post('/notifications/${notification['id']}/read/');
      if (mounted) _load();
    } catch (_) {
      // Ignore: reading is best-effort.
    }
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
          IconButton(
            icon: const Icon(Icons.tune),
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
              child: ListTile(
                leading: Icon(
                  _iconFor(n['event_type'] as String?),
                  color: read
                      ? Theme.of(context).colorScheme.onSurface.withValues(
                            alpha: 0.4,
                          )
                      : Theme.of(context).colorScheme.primary,
                ),
                title: Text(
                  '${n['title']}',
                  style: TextStyle(
                    fontWeight: read ? FontWeight.normal : FontWeight.w700,
                  ),
                ),
                subtitle: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if ('${n['body']}'.isNotEmpty)
                      Text(
                        '${n['body']}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                    Text(
                      relativeTime(l10n, n['created_at'] as String?),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
                isThreeLine: true,
                onTap: () => _handleTap(n),
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
