import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import '../../core/api_client.dart';
import '../../core/locale_controller.dart';
import '../../core/models/banner_item.dart';
import '../../core/models/club_info.dart';
import '../../core/theme/app_theme.dart';
import '../../core/widgets/brand_logo.dart';
import '../auth/auth_state.dart';

/// Home layout order (do not regress):
///   1. LOGO (hero size) + notifications bell
///   2. Hero greeting banner
///   3. Events (quedadas) strip + banners (promos)
///   4. Club info — elegant card (NO court cards on home)
///   5. One big RESERVA AHORA button
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, this.onOpenNotifications});

  final VoidCallback? onOpenNotifications;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  List<BannerItem> _banners = const [];
  List<dynamic> _events = const [];
  ClubInfo? _club;
  bool _clubLoadFailed = false;
  bool _loadingClub = true;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  Future<void> _loadAll() async {
    await Future.wait([_loadBanners(), _loadClub(), _loadEvents()]);
  }

  Future<void> _loadEvents() async {
    try {
      final data = await context.read<ApiClient>().get(
        '/events/',
        query: {'category': 'quedada'},
      );
      final list = data is Map ? data['results'] : data;
      if (!mounted) return;
      setState(() => _events = (list as List<dynamic>?) ?? const []);
    } catch (_) {
      if (!mounted) return;
      setState(() => _events = const []);
    }
  }

  Future<void> _loadBanners() async {
    try {
      final lang = context.read<LocaleController>().code;
      final data = await context.read<ApiClient>().get(
        '/banners/',
        query: {'lang': lang},
      );
      if (!mounted) return;
      setState(() => _banners = BannerItem.listFrom(data));
    } catch (_) {
      if (!mounted) return;
      setState(() => _banners = const []);
    }
  }

  Future<void> _loadClub() async {
    setState(() {
      _loadingClub = true;
      _clubLoadFailed = false;
    });
    try {
      final data = await context.read<ApiClient>().get('/club/');
      if (!mounted) return;
      if (data is Map<String, dynamic>) {
        setState(() {
          _club = ClubInfo.fromJson(data);
          _loadingClub = false;
        });
      } else if (data is Map) {
        setState(() {
          _club = ClubInfo.fromJson(Map<String, dynamic>.from(data));
          _loadingClub = false;
        });
      } else {
        setState(() {
          _club = null;
          _loadingClub = false;
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _club = null;
        _clubLoadFailed = true;
        _loadingClub = false;
      });
    }
  }

  void _openBooking() {
    Navigator.of(context).pushNamed('/bookings/new');
  }

  Future<void> _openExternal(String url) async {
    final uri = Uri.tryParse(url);
    if (uri == null) return;
    try {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    } catch (_) {
      // Silently ignore unreachable links — never crash the home screen.
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);

    return Scaffold(
      body: SafeArea(
        child: RefreshIndicator(
          onRefresh: _loadAll,
          child: CustomScrollView(
            slivers: [
              // ── 1. Hero logo + bell ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.md, AppSpacing.md, 0),
                  child: _buildHeader(l10n),
                ),
              ),
              // ── 2. Hero greeting banner ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.lg, AppSpacing.md, 0),
                  child: _buildHeroBanner(l10n),
                ),
              ),
              // ── 3. Events (quedadas) ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.lg, AppSpacing.md, 0),
                  child: _buildEventsSection(l10n),
                ),
              ),
              // ── 4. Banners (promos / events) ──
              if (_banners.isNotEmpty)
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(
                        AppSpacing.md, AppSpacing.lg, AppSpacing.md, 0),
                    child: BannerCarousel(
                      banners: _banners,
                      onOpen: _openExternal,
                    ),
                  ),
                ),
              // ── 5. Elegant club info (no court cards) ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.lg, AppSpacing.md, 0),
                  child: _buildClubSection(l10n),
                ),
              ),
              // ── 6. One big reserve button ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.xl, AppSpacing.md, 0),
                  child: _buildReserveButton(l10n),
                ),
              ),
              const SliverToBoxAdapter(child: SizedBox(height: AppSpacing.xl)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeader(AppLocalizations l10n) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Hero logo — the brand mark is the first thing on the page.
        Expanded(
          child: Align(
            alignment: Alignment.centerLeft,
            child: BrandLogo(height: BrandLogo.authHeight(context)),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: scheme.surface,
            shape: BoxShape.circle,
            border: Border.all(color: scheme.outline),
          ),
          child: IconButton(
            tooltip: l10n.notifications,
            icon: Icon(Icons.notifications_none, color: scheme.onSurface),
            onPressed: widget.onOpenNotifications,
          ),
        ),
      ],
    );
  }

  Widget _buildHeroBanner(AppLocalizations l10n) {
    final user = context.watch<AuthState>().user;
    final userName = (user?['full_name'] as String?) ?? '';
    final greeting =
        userName.isNotEmpty ? l10n.homeGreeting(userName) : l10n.homeWelcome;
    return Container(
      width: double.infinity,
      padding:
          const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: 20),
      decoration: BoxDecoration(
        color: AppColors.brand,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.appTagline,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.75),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  greeting,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: AppColors.accentSoft.withValues(alpha: 0.25),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.sports_tennis_outlined,
              color: AppColors.accentSoft,
              size: 28,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildEventsSection(AppLocalizations l10n) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          l10n.navEvents,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
        ),
        const SizedBox(height: AppSpacing.sm),
        if (_events.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: scheme.surface,
              borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
              border: Border.all(color: scheme.outline),
            ),
            child: Text(
              l10n.eventsEmpty,
              style: TextStyle(
                color: scheme.onSurface.withValues(alpha: 0.55),
                fontSize: 14,
              ),
            ),
          )
        else
          SizedBox(
            height: 132,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: _events.length,
              separatorBuilder: (_, __) => const SizedBox(width: AppSpacing.sm),
              itemBuilder: (context, i) {
                final e = Map<String, dynamic>.from(_events[i] as Map);
                final title = '${e['title_es'] ?? e['title'] ?? ''}';
                final when = '${e['start_at'] ?? ''}';
                return Container(
                  width: 240,
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: scheme.surface,
                    borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
                    border: Border.all(color: scheme.outline),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.emoji_events_outlined,
                          color: AppColors.brandLight, size: 22),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.w800,
                          height: 1.2,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        when.length >= 10 ? when.substring(0, 10) : when,
                        style: TextStyle(
                          fontSize: 13,
                          color: scheme.onSurface.withValues(alpha: 0.55),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
      ],
    );
  }

  Widget _buildClubSection(AppLocalizations l10n) {
    if (_loadingClub) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(AppSpacing.xl),
          child: CircularProgressIndicator(),
        ),
      );
    }
    if (_club == null) {
      final scheme = Theme.of(context).colorScheme;
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(AppSpacing.lg),
        decoration: BoxDecoration(
          color: scheme.surface,
          borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
          border: Border.all(color: scheme.outline),
        ),
        child: Column(
          children: [
            Icon(
              _clubLoadFailed
                  ? Icons.wifi_off_outlined
                  : Icons.storefront_outlined,
              size: 40,
              color: scheme.onSurface.withValues(alpha: 0.35),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              _clubLoadFailed ? l10n.networkError : l10n.clubInfo,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: scheme.onSurface.withValues(alpha: 0.6),
                fontSize: 15,
              ),
            ),
            if (_clubLoadFailed) ...[
              const SizedBox(height: AppSpacing.md),
              OutlinedButton(
                onPressed: _loadClub,
                child: Text(l10n.retry),
              ),
            ],
          ],
        ),
      );
    }
    return ClubInfoCard(
      club: _club!,
      l10n: l10n,
      onOpen: _openExternal,
    );
  }

  Widget _buildReserveButton(AppLocalizations l10n) {
    return SizedBox(
      width: double.infinity,
      height: 64,
      child: FilledButton.icon(
        onPressed: _openBooking,
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.brand,
          foregroundColor: Colors.white,
          textStyle: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w900,
            letterSpacing: 0.6,
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
          ),
        ),
        icon: const Icon(Icons.sports_tennis, size: 26),
        label: Text(
          l10n.reserveNow.toUpperCase(),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
      ),
    );
  }
}

/// Auto-advancing promo/event banner carousel (16:9).
class BannerCarousel extends StatefulWidget {
  const BannerCarousel({
    super.key,
    required this.banners,
    required this.onOpen,
  });

  final List<BannerItem> banners;
  final ValueChanged<String> onOpen;

  @override
  State<BannerCarousel> createState() => _BannerCarouselState();
}

class _BannerCarouselState extends State<BannerCarousel> {
  final _controller = PageController();
  Timer? _timer;
  int _page = 0;

  @override
  void initState() {
    super.initState();
    _scheduleAutoAdvance();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  void _scheduleAutoAdvance() {
    _timer?.cancel();
    if (widget.banners.length <= 1) return;
    _timer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (!mounted || !_controller.hasClients) return;
      final next = (_page + 1) % widget.banners.length;
      _controller.animateToPage(
        next,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      children: [
        AspectRatio(
          aspectRatio: 16 / 9,
          child: ClipRRect(
            borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
            child: PageView.builder(
              controller: _controller,
              itemCount: widget.banners.length,
              onPageChanged: (i) => setState(() => _page = i),
              itemBuilder: (context, i) {
                final banner = widget.banners[i];
                return _BannerSlide(
                  banner: banner,
                  onTap: banner.hasLink
                      ? () => widget.onOpen(banner.linkUrl)
                      : null,
                );
              },
            ),
          ),
        ),
        if (widget.banners.length > 1) ...[
          const SizedBox(height: AppSpacing.xs),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(widget.banners.length, (i) {
              final active = i == _page;
              return AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                margin: const EdgeInsets.symmetric(horizontal: 3),
                width: active ? 18 : 8,
                height: 8,
                decoration: BoxDecoration(
                  color: active
                      ? AppColors.brand
                      : scheme.onSurface.withValues(alpha: 0.25),
                  borderRadius: BorderRadius.circular(4),
                ),
              );
            }),
          ),
        ],
      ],
    );
  }
}

class _BannerSlide extends StatelessWidget {
  const _BannerSlide({required this.banner, this.onTap});

  final BannerItem banner;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Stack(
        fit: StackFit.expand,
        children: [
          Image.network(
            banner.image,
            fit: BoxFit.cover,
            errorBuilder: (_, __, ___) => Container(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              child: const Icon(Icons.image_not_supported_outlined),
            ),
            loadingBuilder: (context, child, progress) {
              if (progress == null) return child;
              return Container(
                color: Theme.of(context).colorScheme.surfaceContainerHighest,
                child: const Center(child: CircularProgressIndicator()),
              );
            },
          ),
          if (banner.title.isNotEmpty)
            Align(
              alignment: Alignment.bottomLeft,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md,
                  vertical: AppSpacing.sm,
                ),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Colors.transparent,
                      Colors.black.withValues(alpha: 0.65),
                    ],
                  ),
                ),
                child: Text(
                  banner.title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// Elegant club information card — brand palette, flat (no gradients).
///
/// Shows every contact channel from `GET /api/club/` with a clear action
/// per row (call / map / write / Instagram) plus a WhatsApp CTA.
class ClubInfoCard extends StatelessWidget {
  const ClubInfoCard({
    super.key,
    required this.club,
    required this.l10n,
    required this.onOpen,
  });

  final ClubInfo club;
  final AppLocalizations l10n;
  final ValueChanged<String> onOpen;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final mapsUrl = club.resolvedMapsUrl;
    final whatsappUrl = club.resolvedWhatsappUrl;
    final instagramUrl = club.resolvedInstagramUrl;
    final title = club.name.isNotEmpty ? club.name : l10n.appTitle;
    final tagline = club.homeGreetingTagline;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: AppColors.outline),
        boxShadow: [
          BoxShadow(
            color: scheme.shadow.withValues(alpha: 0.08),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Brand header strip ──
          Container(
            width: double.infinity,
            color: AppColors.brand,
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg, AppSpacing.lg, AppSpacing.lg, AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 24,
                    fontWeight: FontWeight.w900,
                    height: 1.15,
                  ),
                ),
                if (tagline.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  Text(
                    tagline,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.9),
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                      height: 1.3,
                    ),
                  ),
                ],
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg, AppSpacing.md, AppSpacing.lg, AppSpacing.lg),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.clubInfo,
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        color: AppColors.brandLight,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.4,
                      ),
                ),
                const SizedBox(height: AppSpacing.sm),
                if (club.phone.isNotEmpty)
                  _InfoRow(
                    icon: Icons.phone_outlined,
                    label: l10n.phone,
                    value: club.phone,
                    actionLabel: l10n.call,
                    onAction: () => onOpen('tel:${club.phone}'),
                  ),
                if (club.address.isNotEmpty)
                  _InfoRow(
                    icon: Icons.location_on_outlined,
                    label: l10n.clubContact,
                    value: club.address,
                    actionLabel: mapsUrl.isNotEmpty ? l10n.openMaps : null,
                    onAction: mapsUrl.isNotEmpty ? () => onOpen(mapsUrl) : null,
                  ),
                if (club.email.isNotEmpty)
                  _InfoRow(
                    icon: Icons.mail_outline,
                    label: l10n.email,
                    value: club.email,
                    actionLabel: l10n.write,
                    onAction: () => onOpen('mailto:${club.email}'),
                  ),
                if (instagramUrl.isNotEmpty)
                  _InfoRow(
                    icon: Icons.camera_alt_outlined,
                    label: l10n.instagram,
                    value: instagramUrl
                        .replaceFirst('https://instagram.com/', '@')
                        .replaceFirst('https://www.instagram.com/', '@'),
                    actionLabel: l10n.instagram,
                    onAction: () => onOpen(instagramUrl),
                  ),
                if (whatsappUrl.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.md),
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: FilledButton.icon(
                      onPressed: () => onOpen(whatsappUrl),
                      style: FilledButton.styleFrom(
                        backgroundColor: const Color(0xFF25D366),
                        foregroundColor: Colors.white,
                        textStyle: const TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w700),
                        shape: RoundedRectangleBorder(
                          borderRadius:
                              BorderRadius.circular(AppSpacing.radius),
                        ),
                      ),
                      icon: const Icon(Icons.chat_bubble_outline, size: 22),
                      label: Text(l10n.whatsapp, maxLines: 1),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String label;
  final String value;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.accentSoft,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 22, color: AppColors.brand),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    color: scheme.onSurface.withValues(alpha: 0.55),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.3,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    color: AppColors.brandReadable,
                    fontSize: 16,
                    height: 1.3,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          if (onAction != null && actionLabel != null)
            TextButton(
              onPressed: onAction,
              style: TextButton.styleFrom(
                foregroundColor: AppColors.brandLight,
                textStyle: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                ),
              ),
              child: Text(actionLabel!),
            )
          else if (onAction != null)
            IconButton(
              onPressed: onAction,
              icon: const Icon(Icons.open_in_new, size: 22),
            ),
        ],
      ),
    );
  }
}
