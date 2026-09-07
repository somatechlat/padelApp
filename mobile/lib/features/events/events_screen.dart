import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../../core/widgets/status_chip.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

class EventsScreen extends StatefulWidget {
  const EventsScreen({super.key});

  @override
  State<EventsScreen> createState() => _EventsScreenState();
}

class _EventsScreenState extends State<EventsScreen> {
  List<dynamic>? _quedadas;
  List<dynamic>? _torneos;
  List<dynamic>? _ligas;
  List<dynamic>? _academia;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final api = context.read<ApiClient>();
      final results = await Future.wait([
        api.get('/events/', query: {'category': 'quedada'}),
        api.get('/tournaments/'),
        api.get('/events/', query: {'category': 'liga'}),
        api.get('/events/', query: {'category': 'academia'}),
      ]);
      List<dynamic> list(dynamic data) {
        final l = data is Map ? data['results'] : data;
        return (l as List<dynamic>? ?? []);
      }

      if (!mounted) return;
      setState(() {
        _quedadas = list(results[0]);
        _torneos = list(results[1]);
        _ligas = list(results[2]);
        _academia = list(results[3]);
        _error = null;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = '');
    }
  }

  void _showMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _register(Map<String, dynamic> tournament) async {
    final l10n = AppLocalizations.of(context);
    final controller = TextEditingController();
    final api = context.read<ApiClient>();
    final id = tournament['id'];
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.registerNow),
        content: TextField(
          controller: controller,
          textCapitalization: TextCapitalization.words,
          decoration: InputDecoration(labelText: l10n.partnerName),
        ),
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
    if (confirmed != true) {
      controller.dispose();
      return;
    }
    try {
      await api.post('/tournaments/$id/register/',
          data: {'partner_name': controller.text.trim()});
      final isFree = double.tryParse('${tournament['price']}') == 0;
      if (isFree) {
        await api.post('/tournaments/$id/confirm/');
        _showMessage(l10n.registerSuccess);
      } else {
        _showMessage(l10n.registerPending);
      }
      _load();
    } on DioException catch (e) {
      final data = e.response?.data;
      final detail = data is Map ? data['detail'] : null;
      _showMessage(detail is String && detail.isNotEmpty ? detail : l10n.error);
    } catch (_) {
      _showMessage(l10n.error);
    } finally {
      controller.dispose();
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return DefaultTabController(
      length: 4,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.events),
          bottom: TabBar(
            isScrollable: true,
            tabs: [
              Tab(text: l10n.tabQuedadas),
              Tab(text: l10n.tabTorneos),
              Tab(text: l10n.tabLigas),
              Tab(text: l10n.tabAcademia),
            ],
          ),
        ),
        body: _buildBody(l10n),
      ),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_error != null) {
      return ErrorState(onRetry: _load);
    }
    if (_quedadas == null || _torneos == null || _ligas == null || _academia == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: TabBarView(
        children: [
          _buildEventList(l10n, _quedadas!, Icons.people_outline, l10n.noQuedadas),
          _buildTournaments(l10n),
          _buildEventList(l10n, _ligas!, Icons.leaderboard_outlined, l10n.noLigas),
          _buildEventList(l10n, _academia!, Icons.school_outlined, l10n.noAcademia),
        ],
      ),
    );
  }

  Widget _buildEventList(AppLocalizations l10n, List<dynamic> events, IconData icon, String emptyText) {
    if (events.isEmpty) {
      return SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: EmptyState(icon: icon, title: emptyText),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: events.length,
      itemBuilder: (context, i) {
        final e = events[i] as Map<String, dynamic>;
        final when = dateShort(l10n, e['start_at'] as String?);
        final location = (e['location'] as String?) ?? '';
        final description = (e['description_localized'] as String?) ?? '';
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    (e['title_localized'] as String?) ?? '',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  if (location.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.location_on_outlined, size: 14, color: Theme.of(context).colorScheme.primary),
                        const SizedBox(width: 4),
                        Text(location, style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ),
                  ],
                  if (when.isNotEmpty) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Icon(Icons.schedule_outlined, size: 14, color: Theme.of(context).colorScheme.primary),
                        const SizedBox(width: 4),
                        Text(when, style: Theme.of(context).textTheme.bodySmall),
                      ],
                    ),
                  ],
                  if (description.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(description, style: Theme.of(context).textTheme.bodyMedium, maxLines: 3, overflow: TextOverflow.ellipsis),
                  ],
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildTournaments(AppLocalizations l10n) {
    if (_torneos!.isEmpty) {
      return SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: EmptyState(
          icon: Icons.emoji_events_outlined,
          title: l10n.noEvents,
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: _torneos!.length,
      itemBuilder: (context, i) {
        final t = _torneos![i] as Map<String, dynamic>;
        final status = (t['status'] as String?) ?? '';
        final open = status == 'open';
        final confirmed = (t['confirmed_count'] as num?)?.toInt() ?? 0;
        final capacity = (t['capacity'] as num?)?.toInt() ?? 0;
        final price = (t['price'] as String?) ?? '0';
        final isFree = double.tryParse(price) == 0;
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Text(
                          (t['name_localized'] as String?) ?? '',
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      StatusChip(
                        label: _statusText(l10n, status),
                        color: _statusColor(status),
                      ),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    '${dateShort(l10n, t['start_date'] as String?)} → '
                    '${dateShort(l10n, t['end_date'] as String?)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: AppSpacing.xxs),
                  Text(
                    '${l10n.capacity}: $confirmed/$capacity · '
                    '${isFree ? l10n.free : '\$$price'}',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: isFree
                              ? Theme.of(context).colorScheme.onSurface
                              : AppColors.brandReadable,
                          fontWeight:
                              isFree ? FontWeight.normal : FontWeight.w600,
                        ),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton.icon(
                          onPressed: open ? () => _register(t) : null,
                          icon: const Icon(Icons.how_to_reg_outlined),
                          label: Text(
                            open ? l10n.registerNow : l10n.registered,
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'open':
        return AppColors.brandReadable;
      case 'in_progress':
        return AppColors.brandReadable;
      default:
        return AppColors.textMuted;
    }
  }

  String _statusText(AppLocalizations l10n, String status) {
    switch (status) {
      case 'open':
        return l10n.tournamentStatus_open;
      case 'in_progress':
        return l10n.tournamentStatus_in_progress;
      case 'closed':
        return l10n.tournamentStatus_closed;
      case 'finished':
        return l10n.tournamentStatus_finished;
      case 'draft':
        return l10n.tournamentStatus_draft;
      default:
        return status;
    }
  }
}
