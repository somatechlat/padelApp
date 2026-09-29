/// Only 90 and 120 minutes (product decision).
const kBookingDurations = [90, 120];

/// Occupancy grid granularity in minutes.
const kSlotMinutes = 30;

/// Formats a [Duration] as `HH:mm`.
String fmtBookTime(Duration d) {
  final h = d.inHours.toString().padLeft(2, '0');
  final m = (d.inMinutes % 60).toString().padLeft(2, '0');
  return '$h:$m';
}

/// Parses `HH:mm` into a [Duration]; null when the shape is wrong.
Duration? parseBookTime(String hhmm) {
  final parts = hhmm.split(':');
  if (parts.length < 2) return null;
  final h = int.tryParse(parts[0]);
  final m = int.tryParse(parts[1]);
  if (h == null || m == null) return null;
  return Duration(hours: h, minutes: m);
}

/// Repeated layout tokens for the booking flow (feature-local, not a global
/// design system — `AppSpacing` stays the source of truth for the scale).
abstract final class BookDim {
  static const double sectionTitleSize = 18;
  static const double buttonLabelSize = 16;
  static const double bodySize = 16;
  static const double chipLabelSize = 16;
  static const double dayNumberSize = 15;
  static const double freeCountSize = 11;
  static const double courtTitleSize = 17;
  static const double courtSubtitleSize = 14;
  static const double tileRadius = 10;
  static const double timeGridChildAspect = 2.4;
  static const int timeGridColumns = 3;
  static const double timeGridSpacing = 8;
  static const double calendarDayInset = 2;
  static const double progressSize = 22;
  static const double progressStroke = 2;
}
