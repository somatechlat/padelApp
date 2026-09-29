import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';
import 'booking_constants.dart';

/// Month calendar for the booking WHEN step (Monday-first grid).
class BookingCalendar extends StatelessWidget {
  const BookingCalendar({
    super.key,
    required this.l10n,
    required this.visibleMonth,
    required this.selectedDate,
    required this.onMonthChanged,
    required this.onDateSelected,
  });

  final AppLocalizations l10n;
  final DateTime visibleMonth;
  final DateTime selectedDate;
  final ValueChanged<DateTime> onMonthChanged;
  final ValueChanged<DateTime> onDateSelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final firstOfMonth = DateTime(visibleMonth.year, visibleMonth.month, 1);
    final daysInMonth =
        DateTime(visibleMonth.year, visibleMonth.month + 1, 0).day;
    // Monday-first grid (locale ES/PT/CA/EN all start the week on Monday here).
    final startWeekday = (firstOfMonth.weekday + 6) % 7; // Mon=0 … Sun=6
    final today = DateTime.now();
    final todayDate = DateTime(today.year, today.month, today.day);
    final selected =
        DateTime(selectedDate.year, selectedDate.month, selectedDate.day);

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: theme.colorScheme.outline),
      ),
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          _MonthHeader(
            l10n: l10n,
            visibleMonth: visibleMonth,
            onMonthChanged: onMonthChanged,
          ),
          const SizedBox(height: AppSpacing.xs),
          _WeekdayRow(l10n: l10n),
          const SizedBox(height: AppSpacing.xs),
          _DayGrid(
            visibleMonth: visibleMonth,
            startWeekday: startWeekday,
            daysInMonth: daysInMonth,
            todayDate: todayDate,
            selected: selected,
            onDateSelected: onDateSelected,
          ),
        ],
      ),
    );
  }
}

String _monthLabel(AppLocalizations l10n, DateTime visibleMonth) {
  // Never crash on missing intl locale data (ca/pt edge cases).
  String monthLabel;
  try {
    monthLabel = DateFormat('MMMM yyyy', l10n.localeName).format(visibleMonth);
  } catch (_) {
    monthLabel = DateFormat('MMMM yyyy', 'es').format(visibleMonth);
  }
  if (monthLabel.isEmpty) return '';
  return monthLabel[0].toUpperCase() + monthLabel.substring(1);
}

class _MonthHeader extends StatelessWidget {
  const _MonthHeader({
    required this.l10n,
    required this.visibleMonth,
    required this.onMonthChanged,
  });

  final AppLocalizations l10n;
  final DateTime visibleMonth;
  final ValueChanged<DateTime> onMonthChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        IconButton(
          tooltip: l10n.back,
          onPressed: () => onMonthChanged(
            DateTime(visibleMonth.year, visibleMonth.month - 1, 1),
          ),
          icon: const Icon(Icons.chevron_left),
        ),
        Expanded(
          child: Text(
            _monthLabel(l10n, visibleMonth),
            textAlign: TextAlign.center,
            style: theme.textTheme.titleMedium?.copyWith(
              fontSize: BookDim.sectionTitleSize,
              fontWeight: FontWeight.w800,
            ),
          ),
        ),
        IconButton(
          tooltip: l10n.next,
          onPressed: () => onMonthChanged(
            DateTime(visibleMonth.year, visibleMonth.month + 1, 1),
          ),
          icon: const Icon(Icons.chevron_right),
        ),
      ],
    );
  }
}

class _WeekdayRow extends StatelessWidget {
  const _WeekdayRow({required this.l10n});

  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        for (final label in weekdayLabels(l10n))
          Expanded(
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.w700,
                color: theme.colorScheme.onSurface.withValues(alpha: 0.5),
              ),
            ),
          ),
      ],
    );
  }
}

/// One letter per weekday, localized via DateFormat. Monday first.
List<String> weekdayLabels(AppLocalizations l10n) {
  final out = <String>[];
  // 2024-01-01 is a Monday — perfect for building Mon..Sun labels.
  final monday = DateTime(2024, 1, 1);
  for (var i = 0; i < 7; i++) {
    final d = monday.add(Duration(days: i));
    out.add(DateFormat('EEE', l10n.localeName).format(d).substring(0, 2));
  }
  return out;
}

class _DayGrid extends StatelessWidget {
  const _DayGrid({
    required this.visibleMonth,
    required this.startWeekday,
    required this.daysInMonth,
    required this.todayDate,
    required this.selected,
    required this.onDateSelected,
  });

  final DateTime visibleMonth;
  final int startWeekday;
  final int daysInMonth;
  final DateTime todayDate;
  final DateTime selected;
  final ValueChanged<DateTime> onDateSelected;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 7,
        childAspectRatio: 1,
      ),
      itemCount: startWeekday + daysInMonth,
      itemBuilder: (context, i) {
        if (i < startWeekday) return const SizedBox.shrink();
        final day = i - startWeekday + 1;
        final d = DateTime(visibleMonth.year, visibleMonth.month, day);
        final isPast = d.isBefore(todayDate);
        final isSelected = d == selected;
        final isToday = d == todayDate;
        return Padding(
          padding: const EdgeInsets.all(BookDim.calendarDayInset),
          child: Material(
            color: isSelected
                ? AppColors.brand
                : isToday
                    ? AppColors.accentSoft
                    : Colors.transparent,
            borderRadius: BorderRadius.circular(BookDim.tileRadius),
            child: InkWell(
              borderRadius: BorderRadius.circular(BookDim.tileRadius),
              onTap: isPast ? null : () => onDateSelected(d),
              child: Center(
                child: Text(
                  '$day',
                  style: TextStyle(
                    fontSize: BookDim.dayNumberSize,
                    fontWeight: isSelected || isToday
                        ? FontWeight.w800
                        : FontWeight.w500,
                    color: isSelected
                        ? Colors.white
                        : isPast
                            ? theme.colorScheme.onSurface.withValues(alpha: 0.3)
                            : theme.colorScheme.onSurface,
                  ),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
