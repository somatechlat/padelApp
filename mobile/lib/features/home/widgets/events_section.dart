import 'dart:async';

import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';

/// Events auto-sliding carousel (home layout step 3).
/// Slides to the next event every 4 seconds; user can swipe manually too.
class HomeEventsSection extends StatefulWidget {
  const HomeEventsSection({
    super.key,
    required this.l10n,
    required this.events,
    this.loadFailed = false,
    this.onRetry,
  });

  final AppLocalizations l10n;
  final List<dynamic> events;

  /// True when the list is empty because the request failed, not because the
  /// club has nothing scheduled. Showing "coming soon" for a load failure is
  /// a lie the user cannot act on.
  final bool loadFailed;
  final VoidCallback? onRetry;

  @override
  State<HomeEventsSection> createState() => _HomeEventsSectionState();
}

class _HomeEventsSectionState extends State<HomeEventsSection> {
  final PageController _pageController = PageController();
  Timer? _autoSlide;
  int _currentPage = 0;

  @override
  void initState() {
    super.initState();
    _startAutoSlide();
  }

  @override
  void dispose() {
    _autoSlide?.cancel();
    _pageController.dispose();
    super.dispose();
  }

  void _startAutoSlide() {
    _autoSlide?.cancel();
    if (widget.events.length < 2) return;
    _autoSlide = Timer.periodic(const Duration(seconds: 4), (_) {
      if (!mounted || !_pageController.hasClients) return;
      final next = (_currentPage + 1) % widget.events.length;
      _pageController.animateToPage(
        next,
        duration: const Duration(milliseconds: 500),
        curve: Curves.easeInOut,
      );
    });
  }

  String _formatDate(String raw) {
    if (raw.length < 10) return raw;
    try {
      final dt = DateTime.parse(raw);
      const months = [
        'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
        'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic',
      ];
      return '${dt.day} ${months[dt.month - 1]}';
    } catch (_) {
      return raw.substring(0, 10);
    }
  }

  String _categoryLabel(String? cat) {
    switch (cat) {
      case 'quedada':
        return 'Quedada';
      case 'torneo':
        return 'Torneo';
      case 'liga':
        return 'Liga';
      case 'academia':
        return 'Academia';
      case 'noticia':
        return 'Noticia';
      default:
        return 'Evento';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.l10n.navEvents,
          style: theme.textTheme.titleMedium?.copyWith(
            fontSize: 18,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        if (widget.events.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: scheme.surface,
              borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
              border: Border.all(color: scheme.outline),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.loadFailed
                      ? widget.l10n.networkError
                      : widget.l10n.eventsEmpty,
                  style: TextStyle(
                    color: scheme.onSurface.withValues(alpha: 0.55),
                    fontSize: 14,
                  ),
                ),
                if (widget.loadFailed && widget.onRetry != null) ...[
                  const SizedBox(height: AppSpacing.sm),
                  OutlinedButton(
                    onPressed: widget.onRetry,
                    child: Text(widget.l10n.retry),
                  ),
                ],
              ],
            ),
          )
        else ...[
          SizedBox(
            height: 220,
            child: PageView.builder(
              controller: _pageController,
              onPageChanged: (i) {
                setState(() => _currentPage = i);
                _startAutoSlide(); // reset timer on manual swipe
              },
              itemCount: widget.events.length,
              itemBuilder: (context, i) {
                final e = Map<String, dynamic>.from(widget.events[i] as Map);
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 2),
                  child: _EventSlideCard(
                    scheme: scheme,
                    title: '${e['title_es'] ?? e['title'] ?? ''}',
                    date: _formatDate('${e['start_at'] ?? ''}'),
                    category: _categoryLabel('${e['category'] ?? ''}'),
                    imageUrl: '${e['image_url'] ?? ''}',
                    location: '${e['location'] ?? ''}',
                    description: '${e['description_es'] ?? e['description'] ?? ''}',
                  ),
                );
              },
            ),
          ),
          if (widget.events.length > 1) ...[
            const SizedBox(height: AppSpacing.sm),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                for (int i = 0; i < widget.events.length; i++)
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 300),
                    margin: const EdgeInsets.symmetric(horizontal: 3),
                    width: _currentPage == i ? 20 : 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: _currentPage == i
                          ? AppColors.brandLight
                          : scheme.onSurface.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
              ],
            ),
          ],
        ],
      ],
    );
  }
}

class _EventSlideCard extends StatelessWidget {
  const _EventSlideCard({
    required this.scheme,
    required this.title,
    required this.date,
    required this.category,
    required this.imageUrl,
    required this.location,
    required this.description,
  });

  final ColorScheme scheme;
  final String title;
  final String date;
  final String category;
  final String imageUrl;
  final String location;
  final String description;

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
      child: Stack(
        fit: StackFit.expand,
        children: [
          // Full-bleed background image
          if (imageUrl.isNotEmpty)
            Image.network(
              imageUrl,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => _placeholderImage(),
            )
          else
            _placeholderImage(),
          // Dark gradient overlay for text readability
          Container(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  Colors.transparent,
                  Colors.black.withValues(alpha: 0.15),
                  Colors.black.withValues(alpha: 0.7),
                ],
                stops: const [0.0, 0.45, 1.0],
              ),
            ),
          ),
          // Content overlay
          Positioned(
            left: 16,
            right: 16,
            bottom: 16,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Category badge
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: AppColors.brandLight,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    category,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.3,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                    shadows: [
                      Shadow(
                        color: Colors.black54,
                        blurRadius: 4,
                        offset: Offset(0, 1),
                      ),
                    ],
                  ),
                ),
                if (description.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    description,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.85),
                      fontSize: 13,
                    ),
                  ),
                ],
                const SizedBox(height: 6),
                Row(
                  children: [
                    Icon(
                      Icons.calendar_today,
                      size: 13,
                      color: Colors.white.withValues(alpha: 0.8),
                    ),
                    const SizedBox(width: 5),
                    Text(
                      date,
                      style: TextStyle(
                        fontSize: 13,
                        color: Colors.white.withValues(alpha: 0.8),
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (location.isNotEmpty) ...[
                      const SizedBox(width: 12),
                      Icon(
                        Icons.location_on,
                        size: 13,
                        color: Colors.white.withValues(alpha: 0.8),
                      ),
                      const SizedBox(width: 3),
                      Expanded(
                        child: Text(
                          location,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 13,
                            color: Colors.white.withValues(alpha: 0.8),
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _placeholderImage() {
    return Container(
      color: AppColors.brandLight.withValues(alpha: 0.2),
      child: Center(
        child: Icon(
          Icons.sports_tennis,
          size: 56,
          color: AppColors.brandLight.withValues(alpha: 0.35),
        ),
      ),
    );
  }
}
