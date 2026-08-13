import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/state_views.dart';
import '../auth/auth_state.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<dynamic>? _events;

  @override
  void initState() {
    super.initState();
    _loadEvents();
  }

  Future<void> _loadEvents() async {
    try {
      final data = await context.read<ApiClient>().get('/events/');
      final list = data is Map ? data['results'] : data;
      if (!mounted) return;
      setState(() {
        _events = (list as List<dynamic>? ?? []).take(3).toList();
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _events = const []);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final user = context.watch<AuthState>().user;
    final name = (user?['full_name'] as String?) ?? '';
    return Scaffold(
      appBar: AppBar(title: Text(l10n.appTitle)),
      body: RefreshIndicator(
        onRefresh: _loadEvents,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.md),
          children: [
            Text(
              '$l10n.homeWelcome${name.isNotEmpty ? ', $name' : ''}',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              l10n.homeSubtitle,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: AppSpacing.lg),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      l10n.bookCourt,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: AppSpacing.md),
                    FilledButton.icon(
                      onPressed: () {
                        Navigator.of(context).pushNamed('/bookings/new');
                      },
                      icon: const Icon(Icons.event_available),
                      label: Text(l10n.bookNow),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            Text(
              l10n.upcomingEvents,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: AppSpacing.xs),
            if (_events == null)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_events!.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 24),
                child: EmptyState(
                  icon: Icons.event_outlined,
                  title: l10n.noEvents,
                ),
              )
            else
              for (final e in _events!) ..._eventCards(e as Map<String, dynamic>, l10n),
          ],
        ),
      ),
    );
  }

  List<Widget> _eventCards(Map<String, dynamic> e, AppLocalizations l10n) {
    final when = dateShort(l10n, e['start_at'] as String?);
    final location = (e['location'] as String?) ?? '';
    return [
      Card(
        child: ListTile(
          leading: Icon(
            Icons.event_outlined,
            color: Theme.of(context).colorScheme.primary,
          ),
          title: Text((e['title_localized'] as String?) ?? ''),
          subtitle: Text(
            [when, location].where((x) => x.isNotEmpty).join(' · '),
          ),
        ),
      ),
      const SizedBox(height: AppSpacing.xs),
    ];
  }
}
