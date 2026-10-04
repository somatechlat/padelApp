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
            height: 132,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: events.length,
              separatorBuilder: (_, __) => const SizedBox(width: AppSpacing.sm),
              itemBuilder: (context, i) {
                final e = Map<String, dynamic>.from(events[i] as Map);
                final title = '${e['title_es'] ?? e['title'] ?? ''}';
                final when = '${e['start_at'] ?? ''}';
                return _EventCard(scheme: scheme, title: title, when: when);
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
    required this.when,
  });

  final ColorScheme scheme;
  final String title;
  final String when;

  @override
  Widget build(BuildContext context) {
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
  }
}
