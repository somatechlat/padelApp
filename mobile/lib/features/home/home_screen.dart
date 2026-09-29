import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import '../../core/api_client.dart';
import '../../core/locale_controller.dart';
import '../../core/models/banner_item.dart';
import '../../core/models/club_info.dart';
import '../../core/theme/app_theme.dart';
import '../auth/auth_state.dart';
import 'widgets/banner_carousel.dart';
import 'widgets/club_section.dart';
import 'widgets/events_section.dart';
import 'widgets/hero_banner.dart';
import 'widgets/home_header.dart';
import 'widgets/reserve_button.dart';

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
    final user = context.watch<AuthState>().user;
    final userName = (user?['full_name'] as String?) ?? '';

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
                  child: HomeHeader(
                    l10n: l10n,
                    onOpenNotifications: widget.onOpenNotifications,
                  ),
                ),
              ),
              // ── 2. Hero greeting banner ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.lg, AppSpacing.md, 0),
                  child: HomeHeroBanner(l10n: l10n, userName: userName),
                ),
              ),
              // ── 3. Events (quedadas) ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.lg, AppSpacing.md, 0),
                  child: HomeEventsSection(l10n: l10n, events: _events),
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
                  child: HomeClubSection(
                    l10n: l10n,
                    club: _club,
                    loading: _loadingClub,
                    loadFailed: _clubLoadFailed,
                    onRetry: _loadClub,
                    onOpen: _openExternal,
                  ),
                ),
              ),
              // ── 6. One big reserve button ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(
                      AppSpacing.md, AppSpacing.xl, AppSpacing.md, 0),
                  child: HomeReserveButton(l10n: l10n, onPressed: _openBooking),
                ),
              ),
              const SliverToBoxAdapter(child: SizedBox(height: AppSpacing.xl)),
            ],
          ),
        ),
      ),
    );
  }
}
