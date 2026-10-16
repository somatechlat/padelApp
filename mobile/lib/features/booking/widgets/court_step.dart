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
              duration: duration,
              price: entry['price'] as String?,
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
    required this.duration,
    required this.price,
    required this.selected,
    required this.onTap,
  });

  final ThemeData theme;
  final AppLocalizations l10n;
  final Map<String, dynamic> court;
  final int duration;
  final String? price;
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
          // Selection is carried by the leading mark and the card border, so
          // the trailing slot is free for the price — the one number the
          // customer is deciding on.
          leading: Icon(
            selected ? Icons.check_circle : Icons.sports_tennis_outlined,
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
            '$duration ${l10n.durationMin} · ${l10n.total}',
            style: const TextStyle(fontSize: BookDim.courtSubtitleSize),
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          trailing: _PriceTag(price: price),
          onTap: onTap,
        ),
      ),
    );
  }
}

/// Price for this court at the chosen date and start time.
///
/// Deliberately not a court's static `price_base`: the club charges per
/// franja horaria, so the same court quotes a different amount at 07:00 than
/// at 19:00. While the quote is in flight the slot shows a spinner rather
/// than a number the court may not honour.
class _PriceTag extends StatelessWidget {
  const _PriceTag({required this.price});

  final String? price;

  @override
  Widget build(BuildContext context) {
    if (price == null) {
      return const SizedBox(
        width: 18,
        height: 18,
        child: CircularProgressIndicator(strokeWidth: 2),
      );
    }
    return Text(
      '\$$price',
      textAlign: TextAlign.end,
      style: TextStyle(
        fontSize: BookDim.courtTitleSize,
        fontWeight: FontWeight.w700,
        color: Theme.of(context).colorScheme.primary,
      ),
    );
  }
}
