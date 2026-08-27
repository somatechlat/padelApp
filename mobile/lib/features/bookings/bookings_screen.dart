import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../../core/widgets/status_chip.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

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
      if (!mounted) return;
      setState(() {
        _bookings = (list as List<dynamic>? ?? []);
        _error = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = '');
    }
  }

  (String, Color) _status(BuildContext context, String status) {
    final l10n = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    switch (status) {
      case 'confirmed':
        return (l10n.bookingStatus_confirmed, AppColors.success);
      case 'pending':
        return (l10n.bookingStatus_pending, AppColors.warning);
      case 'cancelled':
        return (l10n.bookingStatus_cancelled, AppColors.danger);
      case 'held':
        return (l10n.bookingStatus_held, scheme.primary);
      default:
        return (status, scheme.onSurface);
    }
  }

  Future<void> _cancelBooking(Map<String, dynamic> booking) async {
    final l10n = AppLocalizations.of(context);
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.cancelBooking),
        content: Text(l10n.cancelBookingConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text(l10n.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: Text(l10n.confirm),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await context.read<ApiClient>().post('/bookings/${booking['id']}/cancel/');
      if (mounted) _load();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(l10n.error)));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.bookings)),
      body: _buildBody(l10n),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.of(context).pushNamed('/bookings/new');
          if (mounted) _load();
        },
        icon: const Icon(Icons.add),
        label: Text(l10n.bookNow),
      ),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_error != null) {
      return ErrorState(onRetry: _load);
    }
    final bookings = _bookings;
    if (bookings == null) {
      return const Center(child: CircularProgressIndicator());
    }
    if (bookings.isEmpty) {
      return EmptyState(
        icon: Icons.event_note_outlined,
        title: l10n.noBookings,
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(AppSpacing.md),
        itemCount: bookings.length,
        itemBuilder: (context, i) {
          final b = bookings[i] as Map<String, dynamic>;
          final status = (b['status'] as String?) ?? '';
          final cancellable = status == 'confirmed' || status == 'pending';
          final (label, color) = _status(context, status);
          return Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.sm),
            child: Card(
              child: ListTile(
                leading: Icon(
                  Icons.sports_tennis_outlined,
                  color: Theme.of(context).colorScheme.primary,
                ),
                title: Text('${b['court']}'),
                subtitle: Text(
                  '${dateShort(l10n, b['date'] as String?)} · '
                  '${timeShort(b['start_time'] as String?)} · '
                  '${b['duration_minutes']} ${l10n.durationMin}',
                ),
                trailing: StatusChip(label: label, color: color),
                onTap: cancellable ? () => _cancelBooking(b) : null,
              ),
            ),
          );
        },
      ),
    );
  }
}
