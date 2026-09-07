import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
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
    final description = (court['description'] as String?) ?? '';
    final courtType = court['court_type'] as String?;
    final hasLighting = court['has_lighting'] as bool? ?? false;
    final priceBase = court['price_base'] as String?;
    final imageUrl = court['image'] as String?;

    return Container(
      margin: const EdgeInsets.only(bottom: AppSpacing.md),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: scheme.outline),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image section
          if (imageUrl != null && imageUrl.isNotEmpty)
            AspectRatio(
              aspectRatio: 16 / 9,
              child: Image.network(
                imageUrl,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => _buildImagePlaceholder(scheme),
                loadingBuilder: (context, child, loadingProgress) {
                  if (loadingProgress == null) return child;
                  return _buildImagePlaceholder(scheme);
                },
              ),
            )
          else
            _buildImagePlaceholder(scheme),

          // Content section
          Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Name and tags
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        name,
                        style: TextStyle(
                          color: scheme.onSurface,
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                    ),
                    _buildTag(_courtTypeLabel(l10n, courtType), scheme),
                    if (hasLighting) ...[
                      const SizedBox(width: 6),
                      _buildTag(l10n.hasLighting, scheme),
                    ],
                  ],
                ),

                // Description
                if (description.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    description,
                    style: TextStyle(
                      color: scheme.onSurface.withValues(alpha: 0.6),
                      fontSize: 13,
                      height: 1.4,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],

                const SizedBox(height: AppSpacing.md),

                // Price and button
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    if (priceBase != null)
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '\$$priceBase',
                            style: TextStyle(
                              color: AppColors.accent,
                              fontSize: 22,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          Text(
                            l10n.perHour,
                            style: TextStyle(
                              color: scheme.onSurface.withValues(alpha: 0.5),
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
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
                        minimumSize: const Size(100, 48),
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(24)),
                        elevation: 0,
                      ),
                      child: Text(l10n.reserve,
                          style: const TextStyle(
                              fontWeight: FontWeight.w900, fontSize: 15)),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildImagePlaceholder(ColorScheme scheme) {
    return Container(
      width: double.infinity,
      height: 160,
      color: scheme.surfaceContainerHighest,
      child: Center(
        child: Icon(
          Icons.sports_tennis_outlined,
          size: 48,
          color: scheme.onSurface.withValues(alpha: 0.2),
        ),
      ),
    );
  }

  Widget _buildTag(String label, ColorScheme scheme) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppColors.accentSoft,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: AppColors.brand,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
