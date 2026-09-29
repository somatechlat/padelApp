import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';
import 'booking_constants.dart';

/// Step 1 of the booking wizard: courts free for the chosen slot.
class BookingCourtStep extends StatelessWidget {
  const BookingCourtStep({
    super.key,
    required this.l10n,
    required this.date,
    required this.start,
    required this.duration,
    required this.courtsFree,
    required this.selectedCourt,
    required this.loadingCourts,
    required this.error,
    required this.onCourtSelected,
    required this.onBack,
    required this.onContinue,
  });

  final AppLocalizations l10n;
  final DateTime date;
  final Duration? start;
  final int duration;
  final List<Map<String, dynamic>> courtsFree;
  final Map<String, dynamic>? selectedCourt;
  final bool loadingCourts;
  final String? error;
  final ValueChanged<Map<String, dynamic>> onCourtSelected;
  final VoidCallback onBack;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dateLabel = DateFormat('EEEE, d MMM', l10n.localeName).format(date);
    final timeLabel = start == null ? '' : fmtBookTime(start!);
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        Text(
          '$dateLabel · $timeLabel · $duration ${l10n.durationMin}',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontSize: BookDim.sectionTitleSize),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: AppSpacing.sm),
        Text(
          l10n.availableCourts,
          style: theme.textTheme.titleMedium
              ?.copyWith(fontSize: BookDim.sectionTitleSize),
        ),
        const SizedBox(height: AppSpacing.md),
        _ErrorBox(error: error),
        if (loadingCourts)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 32),
            child: Center(child: CircularProgressIndicator()),
          )
        else if (courtsFree.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Center(
              child: Text(
                l10n.noCourtsAvailable,
                style: const TextStyle(fontSize: BookDim.buttonLabelSize),
              ),
            ),
          )
        else
          ...courtsFree.map((entry) {
            final c = entry['court'] as Map<String, dynamic>;
            final selected = selectedCourt?['id'] == c['id'];
            return _CourtTile(
              theme: theme,
              l10n: l10n,
              court: c,
              selected: selected,
              onTap: () => onCourtSelected(c),
            );
          }),
        const SizedBox(height: AppSpacing.lg),
        Row(
          children: [
            TextButton(
              onPressed: onBack,
              child: Text(l10n.back,
                  style: const TextStyle(fontSize: BookDim.buttonLabelSize)),
            ),
            const Spacer(),
            FilledButton(
              onPressed: selectedCourt == null ? null : onContinue,
              child: Text(l10n.next,
                  style: const TextStyle(fontSize: BookDim.buttonLabelSize)),
            ),
          ],
        ),
      ],
    );
  }
}

class _ErrorBox extends StatelessWidget {
  const _ErrorBox({required this.error});

  final String? error;

  @override
  Widget build(BuildContext context) {
    if (error == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Text(
        error!,
        style: TextStyle(color: Theme.of(context).colorScheme.error),
      ),
    );
  }
}

class _CourtTile extends StatelessWidget {
  const _CourtTile({
    required this.theme,
    required this.l10n,
    required this.court,
    required this.selected,
    required this.onTap,
  });

  final ThemeData theme;
  final AppLocalizations l10n;
  final Map<String, dynamic> court;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Card(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
          side: BorderSide(
            color: selected
                ? theme.colorScheme.primary
                : theme.colorScheme.outline,
            width: selected ? 2 : 1,
          ),
        ),
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md, vertical: AppSpacing.xs),
          leading: Icon(
            Icons.sports_tennis_outlined,
            size: 28,
            color: theme.colorScheme.primary,
          ),
          title: Text(
            '${court['name']}',
            style: const TextStyle(
                fontSize: BookDim.courtTitleSize, fontWeight: FontWeight.w700),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          subtitle: Text(
            '${court['court_type']} · \$${court['price_base']} ${l10n.perHour}',
            style: const TextStyle(fontSize: BookDim.courtSubtitleSize),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          trailing: selected
              ? Icon(Icons.check_circle, color: theme.colorScheme.primary)
              : const Icon(Icons.chevron_right),
          onTap: onTap,
        ),
      ),
    );
  }
}
