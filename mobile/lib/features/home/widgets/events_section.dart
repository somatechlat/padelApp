import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';

/// Events (quedadas) horizontal strip (home layout step 3).
class HomeEventsSection extends StatelessWidget {
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

  String _formatDate(String raw) {
    if (raw.length < 10) return raw;
    try {
      final dt = DateTime.parse(raw);
      final months = [
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
          l10n.navEvents,
          style: theme.textTheme.titleMedium?.copyWith(
            fontSize: 18,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        if (events.isEmpty)
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
                  loadFailed ? l10n.networkError : l10n.eventsEmpty,
                  style: TextStyle(
                    color: scheme.onSurface.withValues(alpha: 0.55),
                    fontSize: 14,
                  ),
                ),
                if (loadFailed && onRetry != null) ...[
                  const SizedBox(height: AppSpacing.sm),
                  OutlinedButton(
                    onPressed: onRetry,
                    child: Text(l10n.retry),
                  ),
                ],
              ],
            ),
          )
        else
          SizedBox(
            height: 200,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: events.length,
              separatorBuilder: (_, __) => const SizedBox(width: 12),
              itemBuilder: (context, i) {
                final e = Map<String, dynamic>.from(events[i] as Map);
                return _EventCard(
                  scheme: scheme,
                  title: '${e['title_es'] ?? e['title'] ?? ''}',
                  date: _formatDate('${e['start_at'] ?? ''}'),
                  category: _categoryLabel('${e['category'] ?? ''}'),
                  imageUrl: '${e['image_url'] ?? ''}',
                  location: '${e['location'] ?? ''}',
                );
              },
            ),
          ),
      ],
    );
  }
}

class _EventCard extends StatelessWidget {
  const _EventCard({
    required this.scheme,
    required this.title,
    required this.date,
    required this.category,
    required this.imageUrl,
    required this.location,
  });

  final ColorScheme scheme;
  final String title;
  final String date;
  final String category;
  final String imageUrl;
  final String location;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 220,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        color: scheme.surface,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Image section (top 60%)
          Expanded(
            flex: 6,
            child: Stack(
              fit: StackFit.expand,
              children: [
                if (imageUrl.isNotEmpty)
                  Image.network(
                    imageUrl,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => _placeholderImage(),
                  )
                else
                  _placeholderImage(),
                // Category badge
                Positioned(
                  top: 8,
                  left: 8,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: AppColors.brandLight,
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      category,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          // Info section (bottom 40%)
          Expanded(
            flex: 4,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 10),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w800,
                      height: 1.2,
                    ),
                  ),
                  const Spacer(),
                  Row(
                    children: [
                      Icon(
                        Icons.calendar_today,
                        size: 12,
                        color: scheme.onSurface.withValues(alpha: 0.5),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        date,
                        style: TextStyle(
                          fontSize: 12,
                          color: scheme.onSurface.withValues(alpha: 0.5),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      if (location.isNotEmpty) ...[
                        const SizedBox(width: 8),
                        Icon(
                          Icons.location_on,
                          size: 12,
                          color: scheme.onSurface.withValues(alpha: 0.5),
                        ),
                        const SizedBox(width: 2),
                        Expanded(
                          child: Text(
                            location,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              fontSize: 12,
                              color: scheme.onSurface.withValues(alpha: 0.5),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _placeholderImage() {
    return Container(
      color: AppColors.brandLight.withValues(alpha: 0.15),
      child: Center(
        child: Icon(
          Icons.sports_tennis,
          size: 40,
          color: AppColors.brandLight.withValues(alpha: 0.4),
        ),
      ),
    );
  }
}