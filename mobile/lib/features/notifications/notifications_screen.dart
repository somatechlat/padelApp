import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'notification_preferences_screen.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

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
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_error!),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: _load,
              child: Text(l10n.retry),
            ),
          ],
        ),
      );
    }
    final items = _notifications;
    if (items == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (items.isEmpty) {
      return Center(child: Text(l10n.noNotifications));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: items.length,
        itemBuilder: (context, i) {
          final n = items[i] as Map<String, dynamic>;
          final read = n['read_at'] != null;
          return Card(
            child: ListTile(
              leading: Icon(
                read ? Icons.notifications_none : Icons.notifications_active,
                color: read ? null : Theme.of(context).colorScheme.primary,
              ),
              title: Text(
                '${n['title']}',
                style: TextStyle(
                  fontWeight: read ? FontWeight.normal : FontWeight.bold,
                ),
              ),
              subtitle: Text(
                '${n['body']}',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              onTap: () => _markRead(n),
            ),
          );
        },
      ),
    );
  }
}
