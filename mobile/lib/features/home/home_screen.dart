import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import '../../core/api_client.dart';
import '../../core/theme/app_theme.dart';
import '../auth/auth_state.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<dynamic>? _courts;

  @override
  void initState() {
    super.initState();
    _loadCourts();
  }

  Future<void> _loadCourts() async {
    try {
      final data = await context.read<ApiClient>().get('/courts/');
      final list = data is Map ? data['results'] : data;
      if (!mounted) return;
      setState(() => _courts = list as List<dynamic>? ?? []);
    } catch (_) {
      if (!mounted) return;
      setState(() => _courts = const []);
    }
  }

  String _courtTypeLabel(AppLocalizations l10n, String? type) {
    switch (type) {
      case 'techada':
        return l10n.courtType_techada;
      case 'abierta':
        return l10n.courtType_abierta;
      default:
        return type ?? '';
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;
    final user = context.watch<AuthState>().user;
    final userName = (user?['full_name'] as String?) ?? '';
    final greeting = userName.isNotEmpty ? l10n.homeGreeting(userName) : l10n.homeWelcome;

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadCourts,
          child: CustomScrollView(
            slivers: [
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.md, AppSpacing.md, 0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildHeader(l10n, greeting, scheme),
                      const SizedBox(height: AppSpacing.lg),
                      _buildHeroBanner(l10n, scheme),
                      const SizedBox(height: AppSpacing.lg),
                    ],
                  ),
                ),
              ),
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                sliver: _buildCourtsSection(l10n, scheme),
              ),
              const SliverToBoxAdapter(
                  child: SizedBox(height: AppSpacing.xl)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(AppLocalizations l10n, String greeting, ColorScheme scheme) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: Image.asset(
            'assets/images/LOGOTIPO-ANDES-PADEL.png',
            height: 32,
            fit: BoxFit.contain,
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: scheme.surface,
            shape: BoxShape.circle,
            border: Border.all(color: scheme.outline),
          ),
          child: IconButton(
            icon: Icon(Icons.notifications_none, color: scheme.onSurface),
            onPressed: () {},
          ),
        ),
      ],
    );
  }

  Widget _buildHeroBanner(AppLocalizations l10n, ColorScheme scheme) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppColors.brand,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l10n.appTagline,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.8),
              fontSize: 14,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            l10n.appTitle,
            style: const TextStyle(
              color: AppColors.accent,
              fontSize: 32,
              fontWeight: FontWeight.w900,
              letterSpacing: -0.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCourtsSection(AppLocalizations l10n, ColorScheme scheme) {
    if (_courts == null) {
      return const SliverFillRemaining(
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (_courts!.isEmpty) {
      return SliverFillRemaining(
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.sports_tennis_outlined,
                  size: 48, color: scheme.onSurface.withValues(alpha: 0.4)),
              const SizedBox(height: AppSpacing.sm),
              Text(
                l10n.noCourtsAvailable,
                style: TextStyle(
                    color: scheme.onSurface.withValues(alpha: 0.6), fontSize: 14),
              ),
            ],
          ),
        ),
      );
    }
    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, i) {
          final c = _courts![i] as Map<String, dynamic>;
          return _buildCourtCard(c, l10n, scheme);
        },
        childCount: _courts!.length,
      ),
    );
  }

  Widget _buildCourtCard(
      Map<String, dynamic> court, AppLocalizations l10n, ColorScheme scheme) {
    final name = (court['name'] as String?) ?? '';
    final courtType = court['court_type'] as String?;
    final hasLighting = court['has_lighting'] as bool? ?? false;
    final priceBase = court['price_base'] as String?;

    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: scheme.outline),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        color: scheme.onSurface,
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_courtTypeLabel(l10n, courtType)} · ${hasLighting ? l10n.hasLighting : l10n.noLighting}',
                      style: TextStyle(
                        color: scheme.onSurface.withValues(alpha: 0.6),
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                hasLighting ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
                color: scheme.onSurface.withValues(alpha: 0.5),
                size: 20,
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              if (priceBase != null)
                Text(
                  '\$$priceBase ${l10n.perHour}',
                  style: TextStyle(
                    color: AppColors.accent,
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                  ),
                )
              else
                const SizedBox.shrink(),
              ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pushNamed('/bookings/new');
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.brand,
                  foregroundColor: Colors.white,
                  minimumSize: const Size(64, 48),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20)),
                ),
                child: Text(l10n.reserve,
                    style: const TextStyle(fontWeight: FontWeight.w900)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
