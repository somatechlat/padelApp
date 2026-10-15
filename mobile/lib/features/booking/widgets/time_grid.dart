import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';
import 'booking_constants.dart';

/// Clear slot picker, grouped by morning / afternoon / evening.
///
/// Every value on this screen comes from `/bookings/available-starts/`, which
/// derives it from the hours the owner set in the admin (Venue + the courts'
/// schedules). Nothing here invents an hour, a court count or an opening
/// time: the widget only arranges what the API returns.
///
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
    this.totalCourts = 0,
  });

  final AppLocalizations l10n;
  final List<Map<String, dynamic>> starts;
  final Duration? selectedStart;
  final ValueChanged<Duration?> onStartSelected;

  /// Active courts in the club — the denominator of the availability meter.
  /// 0 while unknown, which hides the meter instead of guessing.
  final int totalCourts;

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

  IconData _groupIcon(String key) {
    switch (key) {
      case _kMorning:
        return Icons.wb_sunny_outlined;
      case _kAfternoon:
        return Icons.wb_twilight_outlined;
      default:
        return Icons.nights_stay_outlined;
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
            _GroupHeader(
              theme: theme,
              icon: _groupIcon(entry.key),
              label: _groupLabel(entry.key),
              range: _rangeOf(entry.value),
            ),
            _SlotGrid(
              theme: theme,
              l10n: l10n,
              slots: entry.value,
              totalCourts: totalCourts,
              selectedStart: selectedStart,
              onStartSelected: onStartSelected,
            ),
          ],
      ],
    );
  }

  /// The span this period actually offers ("06:00 – 11:30"), computed from
  /// the payload — a single string, so it is never mistaken for a slot.
  static String _rangeOf(List<Map<String, dynamic>> slots) {
    final times = slots.map((s) => _hhmm('${s['start']}')).toList()..sort();
    if (times.isEmpty) return '';
    return times.first == times.last ? times.first : '${times.first} – ${times.last}';
  }

  static String _hhmm(String raw) {
    final parts = raw.split(':');
    return parts.length >= 2 ? '${parts[0]}:${parts[1]}' : raw;
  }
}

class _GroupHeader extends StatelessWidget {
  const _GroupHeader({
    required this.theme,
    required this.icon,
    required this.label,
    required this.range,
  });

  final ThemeData theme;
  final IconData icon;
  final String label;
  final String range;

  @override
  Widget build(BuildContext context) {
    final muted = theme.colorScheme.onSurface.withValues(alpha: 0.55);
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.sm, bottom: 6),
      child: Row(
        children: [
          Icon(icon, size: 16, color: muted),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              label,
              style: theme.textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w800,
                color: muted,
              ),
            ),
          ),
          Text(
            range,
            style: TextStyle(
              fontSize: BookDim.freeCountSize,
              color: theme.colorScheme.onSurface.withValues(alpha: 0.45),
            ),
          ),
        ],
      ),
    );
  }
}

class _SlotGrid extends StatelessWidget {
  const _SlotGrid({
    required this.theme,
    required this.l10n,
    required this.slots,
    required this.totalCourts,
    required this.selectedStart,
    required this.onStartSelected,
  });

  final ThemeData theme;
  final AppLocalizations l10n;
  final List<Map<String, dynamic>> slots;
  final int totalCourts;
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
        final selected = selectedStart != null && fmtBookTime(selectedStart!) == label;
        return _SlotTile(
          l10n: l10n,
          theme: theme,
          label: label,
          free: free,
          totalCourts: totalCourts,
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
    required this.totalCourts,
    required this.selected,
    required this.onTap,
  });

  final AppLocalizations l10n;
  final ThemeData theme;
  final String label;
  final int free;
  final int totalCourts;
  final bool selected;
  final VoidCallback onTap;

  /// Share of the club's courts free at this start; null while unknown.
  double get _ratio => totalCourts <= 0 ? 0 : (free / totalCourts).clamp(0.0, 1.0).toDouble();

  static Color _heat(double ratio) {
    if (ratio >= 0.66) return AppColors.success;
    if (ratio >= 0.34) return AppColors.warning;
    return AppColors.danger;
  }

  @override
  Widget build(BuildContext context) {
    final known = totalCourts > 0;
    final ratio = _ratio;
    final heat = known ? _heat(ratio) : null;

    final Color bg;
    if (selected) {
      bg = AppColors.brand;
    } else if (heat == null) {
      bg = theme.colorScheme.surface;
    } else {
      bg = heat.withValues(alpha: 0.06 + 0.09 * ratio);
    }
    final Color border = selected
        ? AppColors.brand
        : heat?.withValues(alpha: 0.55) ?? theme.colorScheme.outline;
    final countLabel =
        free == 1 ? l10n.freeCourtsCountOne(free) : l10n.freeCourtsCountOther(free);

    return Semantics(
      button: true,
      selected: selected,
      label: '$label, $countLabel',
      child: AnimatedScale(
        scale: selected ? 1.04 : 1,
        duration: const Duration(milliseconds: 150),
        curve: Curves.easeOut,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          curve: Curves.easeOut,
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(BookDim.tileRadius),
            border: Border.all(color: border, width: selected ? 2 : 1),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: AppColors.brand.withValues(alpha: 0.25),
                      blurRadius: 10,
                      offset: const Offset(0, 3),
                    ),
                  ]
                : const [],
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              borderRadius: BorderRadius.circular(BookDim.tileRadius),
              onTap: onTap,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          label,
                          style: TextStyle(
                            fontSize: BookDim.chipLabelSize,
                            fontWeight: FontWeight.w800,
                            color: selected ? Colors.white : theme.colorScheme.onSurface,
                            height: 1.1,
                          ),
                        ),
                        if (selected) ...[
                          const SizedBox(width: 4),
                          const Icon(Icons.check_circle_rounded, size: 15, color: Colors.white),
                        ],
                      ],
                    ),
                    const SizedBox(height: 4),
                    Text(
                      countLabel,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: BookDim.freeCountSize,
                        color: selected
                            ? Colors.white70
                            : theme.colorScheme.onSurface.withValues(alpha: 0.6),
                      ),
                    ),
                    if (heat != null) ...[
                      const SizedBox(height: 4),
                      _Meter(ratio: ratio, fill: heat, onBrand: selected),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Thin bar showing how much of the club is free at this start. Animated so
/// it fills in when the grid arrives.
class _Meter extends StatelessWidget {
  const _Meter({required this.ratio, required this.fill, required this.onBrand});

  final double ratio;
  final Color fill;
  final bool onBrand;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = constraints.maxWidth;
        return ClipRRect(
          borderRadius: BorderRadius.circular(AppSpacing.xxs),
          child: SizedBox(
            height: 4,
            width: width,
            child: Stack(
              alignment: Alignment.centerLeft,
              children: [
                Positioned.fill(
                  child: Container(
                    color: onBrand ? Colors.white24 : fill.withValues(alpha: 0.18),
                  ),
                ),
                TweenAnimationBuilder<double>(
                  tween: Tween<double>(begin: 0, end: width * ratio),
                  duration: const Duration(milliseconds: 350),
                  curve: Curves.easeOutCubic,
                  builder: (context, value, _) => Container(
                    width: value,
                    height: 4,
                    color: onBrand ? Colors.white : fill,
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

/// Pulsing placeholder with the same geometry as the real grid, so the chips
/// do not jump the page when they land.
class BookingSlotsSkeleton extends StatefulWidget {
  const BookingSlotsSkeleton({super.key});

  @override
  State<BookingSlotsSkeleton> createState() => _BookingSlotsSkeletonState();
}

class _BookingSlotsSkeletonState extends State<BookingSlotsSkeleton>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller = AnimationController(
    vsync: this,
    duration: const Duration(milliseconds: 850),
  )..repeat(reverse: true);

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        final opacity = 0.30 + 0.35 * Curves.easeInOut.transform(_controller.value);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (var group = 0; group < 3; group++) ...[
              Opacity(
                opacity: opacity,
                child: Align(
                  alignment: Alignment.centerLeft,
                  child: Container(
                    height: 14,
                    width: 132,
                    decoration: BoxDecoration(
                      color: theme.colorScheme.onSurface.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(AppSpacing.xxs),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 6),
              Opacity(
                opacity: opacity,
                child: GridView.count(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  crossAxisCount: BookDim.timeGridColumns,
                  mainAxisSpacing: BookDim.timeGridSpacing,
                  crossAxisSpacing: BookDim.timeGridSpacing,
                  childAspectRatio: BookDim.timeGridChildAspect,
                  children: [
                    for (var i = 0; i < 6; i++) _SkeletonTile(theme: theme),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
            ],
          ],
        );
      },
    );
  }
}

class _SkeletonTile extends StatelessWidget {
  const _SkeletonTile({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(BookDim.tileRadius),
        border: Border.all(color: theme.colorScheme.outline),
      ),
      child: Center(
        child: Container(
          width: 56,
          height: 10,
          decoration: BoxDecoration(
            color: theme.colorScheme.onSurface.withValues(alpha: 0.10),
            borderRadius: BorderRadius.circular(3),
          ),
        ),
      ),
    );
  }
}
