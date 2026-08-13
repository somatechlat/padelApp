import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class BookingsScreen extends StatefulWidget {
  const BookingsScreen({super.key});

  @override
  State<BookingsScreen> createState() => _BookingsScreenState();
}

class _BookingsScreenState extends State<BookingsScreen> {
  List<dynamic>? _bookings;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await context.read<ApiClient>().get('/bookings/');
      final list = data is Map ? data['results'] : data;
      setState(() {
        _bookings = (list as List<dynamic>? ?? []);
        _error = null;
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  String _statusLabel(BuildContext context, String status) {
    final l10n = AppLocalizations.of(context);
    switch (status) {
      case 'confirmed':
        return l10n.bookingStatus_confirmed;
      case 'pending':
        return l10n.bookingStatus_pending;
      case 'cancelled':
        return l10n.bookingStatus_cancelled;
      case 'held':
        return l10n.bookingStatus_held;
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.bookings)),
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
    final bookings = _bookings;
    if (bookings == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (bookings.isEmpty) {
      return Center(child: Text(l10n.noBookings));
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: bookings.length,
        itemBuilder: (context, i) {
          final b = bookings[i] as Map<String, dynamic>;
          final status = (b['status'] as String?) ?? '';
          return Card(
            child: ListTile(
              leading: const Icon(Icons.sports_tennis),
              title: Text('${b['court']}'),
              subtitle: Text(
                '${b['date']} · ${b['start_time']} · ${b['duration_minutes']} min',
              ),
              trailing: Chip(label: Text(_statusLabel(context, status))),
            ),
          );
        },
      ),
    );
  }
}
