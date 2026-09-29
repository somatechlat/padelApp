import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';
import 'booking_constants.dart';
import 'calendar_step.dart';
import 'time_grid.dart';

/// Step 0 of the booking wizard: ONE screen — calendar + duration + free times.
class BookingWhenStep extends StatelessWidget {
  const BookingWhenStep({
    super.key,
    required this.l10n,
    required this.selectedDate,
    required this.visibleMonth,
    required this.duration,
    required this.start,
    required this.starts,
    required this.loadingStarts,
    required this.onMonthChanged,
    required this.onDateSelected,
    required this.onDurationSelected,
    required this.onStartSelected,
    required this.onContinue,
  });

  final AppLocalizations l10n;
  final DateTime selectedDate;
  final DateTime visibleMonth;
  final int duration;
  final Duration? start;
  final List<Map<String, dynamic>> starts;
  final bool loadingStarts;
  final ValueChanged<DateTime> onMonthChanged;
  final ValueChanged<DateTime> onDateSelected;
  final ValueChanged<int> onDurationSelected;
  final ValueChanged<Duration?> onStartSelected;
  final VoidCallback onContinue;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final canContinue = start != null;
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        // ── 1. Pick a day ──
        Text(
          l10n.stepDate,
          style: theme.textTheme.titleMedium?.copyWith(
              fontSize: BookDim.sectionTitleSize, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: AppSpacing.sm),
        BookingCalendar(
          l10n: l10n,
          visibleMonth: visibleMonth,
          selectedDate: selectedDate,
          onMonthChanged: onMonthChanged,
          onDateSelected: onDateSelected,
        ),
        const SizedBox(height: AppSpacing.lg),
        // ── 2. Duration ──
        Text(
          l10n.stepDuration,
          style: theme.textTheme.titleMedium?.copyWith(
              fontSize: BookDim.sectionTitleSize, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: AppSpacing.sm),
        _DurationRow(
          l10n: l10n,
          duration: duration,
          onDurationSelected: onDurationSelected,
        ),
        const SizedBox(height: AppSpacing.lg),
        // ── 3. Real free times ──
        Text(
          l10n.stepStartTime,
          style: theme.textTheme.titleMedium?.copyWith(
              fontSize: BookDim.sectionTitleSize, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: AppSpacing.xs),
        Text(
          l10n.freeSlotsOnlyHint,
          style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.55)),
        ),
        const SizedBox(height: AppSpacing.sm),
        if (loadingStarts)
          const Padding(
            padding: EdgeInsets.all(AppSpacing.lg),
            child: Center(child: CircularProgressIndicator()),
          )
        else if (starts.isEmpty)
          _EmptyStartsBox(theme: theme, l10n: l10n)
        else
          BookingTimeGrid(
            l10n: l10n,
            starts: starts,
            selectedStart: start,
            onStartSelected: onStartSelected,
          ),
        const SizedBox(height: AppSpacing.xl),
        FilledButton(
          onPressed: canContinue ? onContinue : null,
          child: Text(l10n.next,
              style: const TextStyle(fontSize: BookDim.buttonLabelSize)),
        ),
      ],
    );
  }
}

class _DurationRow extends StatelessWidget {
  const _DurationRow({
    required this.l10n,
    required this.duration,
    required this.onDurationSelected,
  });

  final AppLocalizations l10n;
  final int duration;
  final ValueChanged<int> onDurationSelected;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (final d in kBookingDurations) ...[
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(
                  right: d == kBookingDurations.first ? AppSpacing.sm : 0),
              child: ChoiceChip(
                label: SizedBox(
                  width: double.infinity,
                  child: Text(
                    '$d ${l10n.durationMin}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(
                        fontSize: BookDim.chipLabelSize,
                        fontWeight: FontWeight.w700),
                  ),
                ),
                selected: duration == d,
                onSelected: (_) => onDurationSelected(d),
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _EmptyStartsBox extends StatelessWidget {
  const _EmptyStartsBox({required this.theme, required this.l10n});

  final ThemeData theme;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: theme.colorScheme.outline),
      ),
      child: Text(
        l10n.noFreeSlotsForSelection,
        style: TextStyle(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
      ),
    );
  }
}
