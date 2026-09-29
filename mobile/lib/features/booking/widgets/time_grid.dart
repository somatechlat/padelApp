import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';
import 'booking_constants.dart';

/// Clear 3-column time grid, grouped by morning / afternoon / evening.
/// Stable grouping key — never shown to the user.
const String _kMorning = 'morning';
const String _kAfternoon = 'afternoon';
const String _kEvening = 'evening';

class BookingTimeGrid extends StatelessWidget {
  const BookingTimeGrid({
    super.key,
    required this.l10n,
    required this.starts,
    required this.selectedStart,
    required this.onStartSelected,
  });

  final AppLocalizations l10n;
  final List<Map<String, dynamic>> starts;
  final Duration? selectedStart;
  final ValueChanged<Duration?> onStartSelected;

  String _groupLabel(String key) {
    switch (key) {
      case _kMorning:
        return l10n.timeMorning;
      case _kAfternoon:
        return l10n.timeAfternoon;
      default:
        return l10n.timeEvening;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final groups = <String, List<Map<String, dynamic>>>{
      _kMorning: [],
      _kAfternoon: [],
      _kEvening: [],
    };
    for (final s in starts) {
      final start = '${s['start']}';
      final hour = int.tryParse(start.split(':').first) ?? 0;
      if (hour < 12) {
        groups[_kMorning]!.add(s);
      } else if (hour < 18) {
        groups[_kAfternoon]!.add(s);
      } else {
        groups[_kEvening]!.add(s);
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final entry in groups.entries)
          if (entry.value.isNotEmpty) ...[
            _GroupLabel(theme: theme, label: _groupLabel(entry.key)),
            _SlotGrid(
              theme: theme,
              l10n: l10n,
              slots: entry.value,
              selectedStart: selectedStart,
              onStartSelected: onStartSelected,
            ),
          ],
      ],
    );
  }
}

class _GroupLabel extends StatelessWidget {
  const _GroupLabel({required this.theme, required this.label});

  final ThemeData theme;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.sm, bottom: 6),
      child: Text(
        label,
        style: theme.textTheme.labelLarge?.copyWith(
          fontWeight: FontWeight.w800,
          color: theme.colorScheme.onSurface.withValues(alpha: 0.55),
        ),
      ),
    );
  }
}

class _SlotGrid extends StatelessWidget {
  const _SlotGrid({
    required this.theme,
    required this.l10n,
    required this.slots,
    required this.selectedStart,
    required this.onStartSelected,
  });

  final ThemeData theme;
  final AppLocalizations l10n;
  final List<Map<String, dynamic>> slots;
  final Duration? selectedStart;
  final ValueChanged<Duration?> onStartSelected;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: BookDim.timeGridColumns,
        mainAxisSpacing: BookDim.timeGridSpacing,
        crossAxisSpacing: BookDim.timeGridSpacing,
        childAspectRatio: BookDim.timeGridChildAspect,
      ),
      itemCount: slots.length,
      itemBuilder: (context, i) {
        final s = slots[i];
        final label = '${s['start']}';
        final free = (s['courts_free'] as num?)?.toInt() ?? 0;
        final selected =
            selectedStart != null && fmtBookTime(selectedStart!) == label;
        return _SlotTile(
          l10n: l10n,
          theme: theme,
          label: label,
          free: free,
          selected: selected,
          onTap: () => onStartSelected(parseBookTime(label)),
        );
      },
    );
  }
}

class _SlotTile extends StatelessWidget {
  const _SlotTile({
    required this.l10n,
    required this.theme,
    required this.label,
    required this.free,
    required this.selected,
    required this.onTap,
  });

  final AppLocalizations l10n;
  final ThemeData theme;
  final String label;
  final int free;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? AppColors.brand : theme.colorScheme.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(BookDim.tileRadius),
        side: BorderSide(
          color: selected ? AppColors.brand : theme.colorScheme.outline,
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(BookDim.tileRadius),
        onTap: onTap,
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                label,
                style: TextStyle(
                  fontSize: BookDim.chipLabelSize,
                  fontWeight: FontWeight.w800,
                  color: selected ? Colors.white : theme.colorScheme.onSurface,
                ),
              ),
              Text(
                free == 1 ? l10n.freeCourtsCountOne(free) : l10n.freeCourtsCountOther(free),
                style: TextStyle(
                  fontSize: BookDim.freeCountSize,
                  color: selected
                      ? Colors.white70
                      : theme.colorScheme.onSurface.withValues(alpha: 0.5),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
