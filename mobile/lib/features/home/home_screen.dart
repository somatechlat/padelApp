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
    final user = context.watch<AuthState>().user;
    final userName = (user?['full_name'] as String?) ?? '';
    final greeting = userName.isNotEmpty ? l10n.homeGreeting(userName) : l10n.homeWelcome;

    return Scaffold(
      backgroundColor: AppColors.backgroundDark,
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
                      _buildHeader(l10n, greeting),
                      const SizedBox(height: AppSpacing.lg),
                      _buildHeroBanner(l10n),
                      const SizedBox(height: AppSpacing.lg),
                    ],
                  ),
                ),
              ),
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.md),
                sliver: _buildCourtsSection(l10n),
              ),
              const SliverToBoxAdapter(
                  child: SizedBox(height: AppSpacing.xl)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(AppLocalizations l10n, String greeting) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.brand,
            borderRadius: BorderRadius.circular(24),
          ),
          child: Text(
            l10n.appTitle,
            style: const TextStyle(
              color: AppColors.backgroundDark,
              fontWeight: FontWeight.w900,
              fontSize: 16,
            ),
          ),
        ),
        Container(
          decoration: const BoxDecoration(
            color: AppColors.surfaceDark,
            shape: BoxShape.circle,
          ),
          child: IconButton(
            icon: const Icon(Icons.notifications_none, color: Colors.white),
            onPressed: () {},
          ),
        ),
      ],
    );
  }

  Widget _buildHeroBanner(AppLocalizations l10n) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: AppColors.outlineDark),
        gradient: const LinearGradient(
          colors: [AppColors.surfaceDark, Color(0xFF1A2210)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l10n.appTagline,
            style: TextStyle(
              color: Colors.white.withOpacity(0.8),
              fontSize: 14,
              fontWeight: FontWeight.w800,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            l10n.appTitle,
            style: const TextStyle(
              color: AppColors.brand,
              fontSize: 32,
              fontWeight: FontWeight.w900,
              letterSpacing: -0.5,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildCourtsSection(AppLocalizations l10n) {
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
                  size: 48, color: AppColors.textMutedDark),
              const SizedBox(height: AppSpacing.sm),
              Text(
                l10n.noCourtsAvailable,
                style: const TextStyle(
                    color: AppColors.textMutedDark, fontSize: 14),
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
          return _buildCourtCard(c, l10n);
        },
        childCount: _courts!.length,
      ),
    );
  }

  Widget _buildCourtCard(Map<String, dynamic> court, AppLocalizations l10n) {
    final name = (court['name'] as String?) ?? '';
    final courtType = court['court_type'] as String?;
    final hasLighting = court['has_lighting'] as bool? ?? false;
    final priceBase = court['price_base'] as String?;

    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.surfaceDark,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: AppColors.outlineDark),
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
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${_courtTypeLabel(l10n, courtType)} · ${hasLighting ? l10n.hasLighting : l10n.noLighting}',
                      style: const TextStyle(
                        color: AppColors.textMutedDark,
                        fontSize: 14,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                hasLighting ? Icons.light_mode_outlined : Icons.dark_mode_outlined,
                color: AppColors.textMutedDark,
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
                  style: const TextStyle(
                    color: AppColors.brand,
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
                  foregroundColor: AppColors.backgroundDark,
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
