import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../../core/widgets/status_chip.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';

class EventsScreen extends StatefulWidget {
  const EventsScreen({super.key});

  @override
  State<EventsScreen> createState() => _EventsScreenState();
}

class _EventsScreenState extends State<EventsScreen> {
  List<dynamic>? _tournaments;
  List<dynamic>? _events;
  List<dynamic>? _news;
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
        api.get('/tournaments/'),
        api.get('/events/'),
        api.get('/news/'),
      ]);
      List<dynamic> list(dynamic data) {
        final l = data is Map ? data['results'] : data;
        return (l as List<dynamic>? ?? []);
      }

      if (!mounted) return;
      setState(() {
        _tournaments = list(results[0]);
        _events = list(results[1]);
        _news = list(results[2]);
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
    if (confirmed != true) return;
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
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return DefaultTabController(
      length: 3,
      child: Scaffold(
        appBar: AppBar(
          title: Text(l10n.events),
          bottom: TabBar(
            tabs: [
              Tab(text: l10n.tournaments),
              Tab(text: l10n.events),
              Tab(text: l10n.news),
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
    if (_tournaments == null || _events == null || _news == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: TabBarView(
        children: [
          _buildTournaments(l10n),
          _buildEvents(l10n),
          _buildNews(l10n),
        ],
      ),
    );
  }

  Widget _buildTournaments(AppLocalizations l10n) {
    if (_tournaments!.isEmpty) {
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
      itemCount: _tournaments!.length,
      itemBuilder: (context, i) {
        final t = _tournaments![i] as Map<String, dynamic>;
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

  Widget _buildEvents(AppLocalizations l10n) {
    if (_events!.isEmpty) {
      return SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: EmptyState(
          icon: Icons.event_outlined,
          title: l10n.noEvents,
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: _events!.length,
      itemBuilder: (context, i) {
        final e = _events![i] as Map<String, dynamic>;
        final when = dateShort(l10n, e['start_at'] as String?);
        final location = (e['location'] as String?) ?? '';
        final description = (e['description_localized'] as String?) ?? '';
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Card(
            child: ListTile(
              leading: Icon(
                Icons.event_outlined,
                color: Theme.of(context).colorScheme.primary,
              ),
              title: Text((e['title_localized'] as String?) ?? ''),
              subtitle: Text(
                [
                  [when, location].where((x) => x.isNotEmpty).join(' · '),
                  if (description.isNotEmpty) description,
                ].join('\n'),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _buildNews(AppLocalizations l10n) {
    if (_news!.isEmpty) {
      return SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: EmptyState(
          icon: Icons.article_outlined,
          title: l10n.noNews,
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: _news!.length,
      itemBuilder: (context, i) {
        final n = _news![i] as Map<String, dynamic>;
        final when = dateShort(l10n, n['published_at'] as String?);
        final body = (n['body_localized'] as String?) ?? '';
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Card(
            child: ListTile(
              leading: Icon(
                Icons.article_outlined,
                color: Theme.of(context).colorScheme.primary,
              ),
              title: Text((n['title_localized'] as String?) ?? ''),
              subtitle: Text(
                [when, body].join('\n'),
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
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