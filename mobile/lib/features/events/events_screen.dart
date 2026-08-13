import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class EventsScreen extends StatefulWidget {
  const EventsScreen({super.key});

  @override
  State<EventsScreen> createState() => _EventsScreenState();
}

class _EventsScreenState extends State<EventsScreen> {
  List<dynamic>? _events;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await context.read<ApiClient>().get('/tournaments/');
      final list = data is Map ? data['results'] : data;
      setState(() {
        _events = (list as List<dynamic>? ?? []);
        _error = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.events)),
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
    final events = _events;
    if (events == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (events.isEmpty) {
      return Center(child: Text(l10n.noEvents));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: events.length,
        itemBuilder: (context, i) {
          final e = events[i] as Map<String, dynamic>;
          final name = (e['name'] as String?) ?? '';
          final dates = '${e['start_date']} → ${e['end_date']}';
          final confirmed = (e['confirmed_count'] as num?)?.toInt() ?? 0;
          final capacity = (e['capacity'] as num?)?.toInt() ?? 0;
          final price = (e['price'] as String?) ?? '0';
          return Card(
            child: ListTile(
              leading: const Icon(Icons.emoji_events_outlined),
              title: Text(name),
              subtitle: Text(
                  '$dates\n$l10n.capacity: $confirmed/$capacity · \$$price'),
            ),
          );
        },
      ),
    );
  }
}
