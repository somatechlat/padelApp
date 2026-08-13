import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

const _eventTypes = [
  'booking_confirmed',
  'booking_cancelled',
  'booking_reminder',
  'payment_success',
  'payment_failed',
  'transfer_confirmed',
  'tournament_reminder',
  'tournament_confirmed',
  'marketing',
];

const _channels = ['email', 'push', 'inapp'];

class NotificationPreferencesScreen extends StatefulWidget {
  const NotificationPreferencesScreen({super.key});

  @override
  State<NotificationPreferencesScreen> createState() =>
      _NotificationPreferencesScreenState();
}

class _NotificationPreferencesScreenState
    extends State<NotificationPreferencesScreen> {
  Map<String, Set<String>> _disabled = {};
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final data = await context.read<ApiClient>().get('/notifications/preferences/');
      final prefs = data as List<dynamic>? ?? [];
      final disabled = <String, Set<String>>{};
      for (final p in prefs) {
        final e = (p as Map)['event_type'] as String;
        final c = p['channel'] as String;
        if (p['enabled'] != true) {
          disabled.putIfAbsent(e, () => {}).add(c);
        }
      }
      setState(() {
        _disabled = disabled;
        _loading = false;
        _error = null;
      });
    } catch (e) {
      setState(() {
        _loading = false;
        _error = e.toString();
      });
    }
  }

  Future<void> _save() async {
    final items = [
      for (final e in _eventTypes)
        for (final c in _channels)
          {
            'event_type': e,
            'channel': c,
            'enabled': !(_disabled[e]?.contains(c) ?? false),
          },
    ];
    try {
      await context.read<ApiClient>().put('/notifications/preferences/', data: items);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(AppLocalizations.of(context).success)),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(AppLocalizations.of(context).error)));
      }
    }
  }

  String _eventLabel(AppLocalizations l10n, String eventType) {
    switch (eventType) {
      case 'booking_confirmed':
        return '${l10n.bookingStatus_confirmed} · ${l10n.bookings}';
      case 'booking_cancelled':
        return '${l10n.bookingStatus_cancelled} · ${l10n.bookings}';
      case 'booking_reminder':
        return '${l10n.bookingReminder} · ${l10n.bookings}';
      case 'payment_success':
        return '${l10n.paymentSuccess} · ${l10n.payments}';
      case 'payment_failed':
        return '${l10n.paymentError} · ${l10n.payments}';
      case 'transfer_confirmed':
        return '${l10n.payTransfer} · ${l10n.payments}';
      case 'tournament_reminder':
        return '${l10n.tournamentReminder} · ${l10n.tournaments}';
      case 'tournament_confirmed':
        return '${l10n.tournamentConfirmed} · ${l10n.tournaments}';
      default:
        return l10n.marketing;
    }
  }

  String _channelLabel(AppLocalizations l10n, String channel) {
    switch (channel) {
      case 'email':
        return l10n.channelEmail;
      case 'push':
        return l10n.channelPush;
      default:
        return l10n.channelInApp;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.notificationSettings),
        actions: [
          TextButton(
            onPressed: _loading ? null : _save,
            child: Text(l10n.save),
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
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        for (final e in _eventTypes)
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _eventLabel(l10n, e),
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                  for (final c in _channels)
                    SwitchListTile(
                      dense: true,
                      title: Text(_channelLabel(l10n, c)),
                      value: !(_disabled[e]?.contains(c) ?? false),
                      onChanged: (enabled) {
                        setState(() {
                          if (enabled) {
                            _disabled[e]?.remove(c);
                          } else {
                            _disabled.putIfAbsent(e, () => {}).add(c);
                          }
                        });
                      },
                    ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
