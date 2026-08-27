import 'package:intl/intl.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';

/// "18:00:00" -> "18:00"
String timeShort(String? iso) {
  if (iso == null || iso.isEmpty) return '';
  final parts = iso.split(':');
  if (parts.length < 2) return iso;
  return '${parts[0]}:${parts[1]}';
}

/// "2026-08-14" -> localized short date
String dateShort(AppLocalizations l10n, String? iso) {
  final parsed = DateTime.tryParse(iso ?? '');
  if (parsed == null) return iso ?? '';
  return DateFormat('d MMM', l10n.localeName).format(parsed);
}

/// "2026-08-14 18:00" -> localized date and time
String dateTimeShort(AppLocalizations l10n, String? iso) {
  final parsed = DateTime.tryParse(iso ?? '');
  if (parsed == null) return iso ?? '';
  return DateFormat('d MMM · HH:mm', l10n.localeName).format(parsed);
}

/// Human-friendly relative time for notifications.
String relativeTime(AppLocalizations l10n, String? iso) {
  final parsed = DateTime.tryParse(iso ?? '');
  if (parsed == null) return '';
  final diff = DateTime.now().difference(parsed);
  if (diff.inMinutes < 1) return l10n.timeNow;
  if (diff.inHours < 1) return l10n.timeAgoMinutes(diff.inMinutes);
  if (diff.inDays < 1) return l10n.timeAgoHours(diff.inHours);
  if (diff.inDays == 1) return l10n.timeYesterday;
  if (diff.inDays < 7) return l10n.timeAgoDays(diff.inDays);
  return DateFormat('d MMM yyyy', l10n.localeName).format(parsed);
}
