import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/friendly_error.dart';
import '../../core/theme/app_theme.dart';
import 'payment_method_screen.dart';

/// Reservation wizard.
///
/// Flow (order matters — do not regress):
///   1. WHEN  — ONE screen: full calendar + duration + schedule (06:00–21:30)
///   2. COURTS free for that date + time + duration
///   3. summary + confirm → payment (transfer / pay-at-venue)
///   4. done
class BookingWizardScreen extends StatefulWidget {
  const BookingWizardScreen({super.key});

  @override
  State<BookingWizardScreen> createState() => _BookingWizardScreenState();
}

class _BookingWizardScreenState extends State<BookingWizardScreen> {
  /// Only 90 and 120 minutes (product decision).
  static const _durations = [90, 120];
  static const _slotMinutes = 30;

  // 0 when · 1 courts · 2 summary · 3 done
  int _step = 0;
  List<dynamic>? _allCourts;
  List<Map<String, dynamic>> _courtsFree = [];
  Map<String, dynamic>? _court;
  DateTime _date = DateTime.now();
  DateTime _visibleMonth = DateTime.now();
  Duration? _start;
  int _duration = 90;
  String? _price;
  String? _error;
  bool _submitting = false;
  bool _loadingCourts = false;
  bool _loadingStarts = false;
  List<Map<String, dynamic>> _starts = [];

  @override
  void initState() {
    super.initState();
    _date = DateTime.now();
    _visibleMonth = DateTime(DateTime.now().year, DateTime.now().month);
    _loadAllCourts();
    _loadAvailableStarts();
  }

  String _fmtDate(DateTime d) => DateFormat('yyyy-MM-dd').format(d);

  String _fmtTime(Duration d) {
    final h = d.inHours.toString().padLeft(2, '0');
    final m = (d.inMinutes % 60).toString().padLeft(2, '0');
    return '$h:$m';
  }

  /// Real free starts from occupancy (TimeSlot), not a hardcoded grid.
  Future<void> _loadAvailableStarts() async {
    setState(() {
      _loadingStarts = true;
      _starts = [];
      _start = null;
    });
    try {
      final data = await context.read<ApiClient>().get(
        '/bookings/available-starts/',
        query: {
          'date': _fmtDate(_date),
          'duration_minutes': '$_duration',
        },
      );
      if (!mounted) return;
      final raw = (data as Map)['starts'] as List<dynamic>? ?? [];
      setState(() {
        _starts = raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        _loadingStarts = false;
      });
    } catch (e) {
      debugPrint('BOOK available-starts failed: $e');
      if (!mounted) return;
      setState(() {
        _loadingStarts = false;
        _starts = [];
      });
    }
  }

  Duration? _parseStart(String hhmm) {
    final parts = hhmm.split(':');
    if (parts.length < 2) return null;
    final h = int.tryParse(parts[0]);
    final m = int.tryParse(parts[1]);
    if (h == null || m == null) return null;
    return Duration(hours: h, minutes: m);
  }

  Future<void> _loadAllCourts() async {
    try {
      final data = await context.read<ApiClient>().get('/courts/');
      final list = data is Map ? data['results'] : data;
      if (!mounted) return;
      setState(() => _allCourts = list as List<dynamic>? ?? []);
    } catch (e) {
      debugPrint('BOOK courts load failed: $e');
    }
  }

  /// ONLY courts free for the full duration at the chosen start.
  Future<void> _loadCourtsForSlot() async {
    final start = _start;
    if (start == null) return;
    setState(() {
      _loadingCourts = true;
      _error = null;
      _court = null;
      _price = null;
      _courtsFree = [];
    });
    try {
      if (_allCourts == null) await _loadAllCourts();
      final courts = _allCourts ?? [];
      final needed = (_duration / _slotMinutes).ceil();
      final results = await Future.wait(courts.map((raw) async {
        final c = Map<String, dynamic>.from(raw as Map);
        try {
          final data = await context.read<ApiClient>().get(
            '/courts/${c['id']}/availability/',
            query: {'date': _fmtDate(_date)},
          );
          final slots = (data as List<dynamic>? ?? []);
          final freeStarts = <String>{
            for (final s in slots)
              if ((s as Map)['status'] == 'available') '${s['start']}',
          };
          // Need `needed` consecutive 30-min slots from the chosen start.
          var ok = true;
          for (var i = 0; i < needed; i++) {
            final t = DateTime(2000, 1, 1)
                .add(start + Duration(minutes: _slotMinutes * i));
            final hh = t.hour.toString().padLeft(2, '0');
            final mm = t.minute.toString().padLeft(2, '0');
            if (!freeStarts.contains('$hh:$mm:00') &&
                !freeStarts.contains('$hh:$mm')) {
              ok = false;
              break;
            }
          }
          // A court with no slot rows at all is closed / not bookable that day.
          if (slots.isEmpty) ok = false;
          if (!ok) return null;
          return <String, dynamic>{'court': c};
        } catch (_) {
          return null;
        }
      }));
      if (!mounted) return;
      setState(() {
        _courtsFree = results.whereType<Map<String, dynamic>>().toList();
        _loadingCourts = false;
      });
    } catch (e) {
      debugPrint('BOOK courts-for-slot load failed: $e');
      if (!mounted) return;
      final l10n = AppLocalizations.of(context);
      setState(() {
        _loadingCourts = false;
        _error = friendlyErrorMessage(e, l10n);
      });
    }
  }

  Future<void> _previewPrice() async {
    final court = _court;
    final start = _start;
    if (court == null || start == null) return;
    try {
      final data =
          await context.read<ApiClient>().post('/bookings/preview/', data: {
        'court': court['id'],
        'date': _fmtDate(_date),
        'start_time': _fmtTime(start),
        'duration_minutes': _duration,
      });
      if (!mounted) return;
      setState(() {
        _price = '${data['price']}';
        _error = null;
      });
    } catch (e) {
      debugPrint('BOOK price preview failed: $e');
      if (!mounted) return;
      final l10n = AppLocalizations.of(context);
      setState(() => _error = friendlyErrorMessage(e, l10n));
    }
  }

  Future<void> _submitBooking() async {
    final l10n = AppLocalizations.of(context);
    final court = _court;
    final start = _start;
    if (court == null || start == null) {
      setState(() => _error = l10n.selectSlot);
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(l10n.selectSlot)));
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    final api = context.read<ApiClient>();
    try {
      final booking = await api.post('/bookings/', data: {
        'court': court['id'],
        'date': _fmtDate(_date),
        'start_time': _fmtTime(start),
        'duration_minutes': _duration,
      });
      final bookingId = booking['id'];
      await api.post('/bookings/$bookingId/confirm/');
      if (mounted) {
        setState(() => _submitting = false);
        final paymentResult = await Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => PaymentMethodScreen(
              bookingId: bookingId,
              amount: double.tryParse(_price ?? '0') ?? 0,
            ),
          ),
        );
        if (mounted) {
          setState(() => _step = paymentResult == true ? 3 : 2);
        }
      }
    } on DioException catch (e) {
      if (mounted) {
        final data = e.response?.data;
        final detail = data is Map ? data['detail'] : null;
        final isNetwork = e.type == DioExceptionType.connectionTimeout ||
            e.type == DioExceptionType.sendTimeout ||
            e.type == DioExceptionType.receiveTimeout ||
            e.type == DioExceptionType.connectionError;
        setState(() {
          _submitting = false;
          if (isNetwork) {
            _error = friendlyErrorMessage(e, l10n);
          } else if (detail is String &&
              detail.isNotEmpty &&
              detail.length < 180 &&
              !detail.contains('Exception')) {
            _error = detail;
          } else {
            _error = l10n.slotTaken;
          }
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = friendlyErrorMessage(e, l10n);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    const steps = 4;
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.bookCourt),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(4),
          child: LinearProgressIndicator(value: (_step + 1) / steps),
        ),
      ),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    switch (_step) {
      case 0:
        return _buildWhenStep(l10n);
      case 1:
        return _buildCourtStep(l10n);
      case 2:
        return _buildSummaryStep(l10n);
      default:
        return _buildDoneStep(l10n);
    }
  }

  Widget _errorBox() {
    if (_error == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        _error!,
        style: TextStyle(color: Theme.of(context).colorScheme.error),
      ),
    );
  }

  // ── Step 0: ONE screen — calendar + duration + real free times ─────────
  Widget _buildWhenStep(AppLocalizations l10n) {
    final theme = Theme.of(context);
    final canContinue = _start != null;
    final starts = _starts;
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        // ── 1. Pick a day ──
        Text(
          '1. Elige el dia',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontSize: 18, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: AppSpacing.sm),
        _buildCalendar(l10n, theme),
        const SizedBox(height: AppSpacing.lg),
        // ── 2. Duration ──
        Text(
          '2. Duracion',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontSize: 18, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: AppSpacing.sm),
        Row(
          children: [
            for (final d in _durations) ...[
              Expanded(
                child: Padding(
                  padding: EdgeInsets.only(
                      right: d == _durations.first ? AppSpacing.sm : 0),
                  child: ChoiceChip(
                    label: SizedBox(
                      width: double.infinity,
                      child: Text(
                        '$d min',
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w700),
                      ),
                    ),
                    selected: _duration == d,
                    onSelected: (_) {
                      setState(() {
                        _duration = d;
                        _start = null;
                        _court = null;
                        _price = null;
                      });
                      _loadAvailableStarts();
                    },
                  ),
                ),
              ),
            ],
          ],
        ),
        const SizedBox(height: AppSpacing.lg),
        // ── 3. Real free times ──
        Text(
          '3. Hora de inicio',
          style: theme.textTheme.titleMedium
              ?.copyWith(fontSize: 18, fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: AppSpacing.xs),
        Text(
          'Solo horarios con cancha libre (según ocupación real).',
          style: theme.textTheme.bodySmall?.copyWith(
              color: theme.colorScheme.onSurface.withValues(alpha: 0.55)),
        ),
        const SizedBox(height: AppSpacing.sm),
        if (_loadingStarts)
          const Padding(
            padding: EdgeInsets.all(AppSpacing.lg),
            child: Center(child: CircularProgressIndicator()),
          )
        else if (starts.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
              border: Border.all(color: theme.colorScheme.outline),
            ),
            child: Text(
              'No hay horas libres para este dia y duracion. Prueba otro dia.',
              style: TextStyle(
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.6)),
            ),
          )
        else
          _buildTimeGrid(theme, starts),
        const SizedBox(height: AppSpacing.xl),
        FilledButton(
          onPressed: canContinue
              ? () {
                  setState(() => _step = 1);
                  _loadCourtsForSlot();
                }
              : null,
          child: Text(l10n.next, style: const TextStyle(fontSize: 16)),
        ),
      ],
    );
  }

  /// Clear 3-column time grid, grouped by morning / afternoon / evening.
  Widget _buildTimeGrid(ThemeData theme, List<Map<String, dynamic>> starts) {
    final groups = <String, List<Map<String, dynamic>>>{
      'Manana': [],
      'Tarde': [],
      'Noche': [],
    };
    for (final s in starts) {
      final t = '${s['start']}';
      final hour = int.tryParse(t.split(':').first) ?? 0;
      if (hour < 12) {
        groups['Manana']!.add(s);
      } else if (hour < 18) {
        groups['Tarde']!.add(s);
      } else {
        groups['Noche']!.add(s);
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final entry in groups.entries)
          if (entry.value.isNotEmpty) ...[
            Padding(
              padding: const EdgeInsets.only(top: AppSpacing.sm, bottom: 6),
              child: Text(
                entry.key,
                style: theme.textTheme.labelLarge?.copyWith(
                  fontWeight: FontWeight.w800,
                  color: theme.colorScheme.onSurface.withValues(alpha: 0.55),
                ),
              ),
            ),
            GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                mainAxisSpacing: 8,
                crossAxisSpacing: 8,
                childAspectRatio: 2.4,
              ),
              itemCount: entry.value.length,
              itemBuilder: (context, i) {
                final s = entry.value[i];
                final label = '${s['start']}';
                final free = (s['courts_free'] as num?)?.toInt() ?? 0;
                final selected = _start != null && _fmtTime(_start!) == label;
                return Material(
                  color: selected ? AppColors.brand : theme.colorScheme.surface,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                    side: BorderSide(
                      color: selected
                          ? AppColors.brand
                          : theme.colorScheme.outline,
                    ),
                  ),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: () {
                      final d = _parseStart(label);
                      setState(() {
                        _start = d;
                        _court = null;
                        _price = null;
                        _error = null;
                      });
                    },
                    child: Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            label,
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w800,
                              color: selected
                                  ? Colors.white
                                  : theme.colorScheme.onSurface,
                            ),
                          ),
                          Text(
                            '$free libre${free == 1 ? '' : 's'}',
                            style: TextStyle(
                              fontSize: 11,
                              color: selected
                                  ? Colors.white70
                                  : theme.colorScheme.onSurface
                                      .withValues(alpha: 0.5),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ],
      ],
    );
  }

  Widget _buildCalendar(AppLocalizations l10n, ThemeData theme) {
    final firstOfMonth = DateTime(_visibleMonth.year, _visibleMonth.month, 1);
    final daysInMonth =
        DateTime(_visibleMonth.year, _visibleMonth.month + 1, 0).day;
    // Monday-first grid (locale ES/PT/CA/EN all start the week on Monday here).
    final startWeekday = (firstOfMonth.weekday + 6) % 7; // Mon=0 … Sun=6
    final today = DateTime.now();
    final todayDate = DateTime(today.year, today.month, today.day);
    final selected = DateTime(_date.year, _date.month, _date.day);
    // Never crash on missing intl locale data (ca/pt edge cases).
    String monthLabel;
    try {
      monthLabel =
          DateFormat('MMMM yyyy', l10n.localeName).format(_visibleMonth);
    } catch (_) {
      monthLabel = DateFormat('MMMM yyyy', 'es').format(_visibleMonth);
    }

    return Container(
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: theme.colorScheme.outline),
      ),
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          Row(
            children: [
              IconButton(
                tooltip: l10n.back,
                onPressed: () => setState(() {
                  _visibleMonth =
                      DateTime(_visibleMonth.year, _visibleMonth.month - 1, 1);
                }),
                icon: const Icon(Icons.chevron_left),
              ),
              Expanded(
                child: Text(
                  monthLabel.isEmpty
                      ? ''
                      : monthLabel[0].toUpperCase() + monthLabel.substring(1),
                  textAlign: TextAlign.center,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              IconButton(
                tooltip: l10n.next,
                onPressed: () => setState(() {
                  _visibleMonth =
                      DateTime(_visibleMonth.year, _visibleMonth.month + 1, 1);
                }),
                icon: const Icon(Icons.chevron_right),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Row(
            children: [
              for (final label in _weekdayLabels(l10n))
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
          ),
          const SizedBox(height: AppSpacing.xs),
          GridView.builder(
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
              final d = DateTime(_visibleMonth.year, _visibleMonth.month, day);
              final isPast = d.isBefore(todayDate);
              final isSelected = d == selected;
              final isToday = d == todayDate;
              return Padding(
                padding: const EdgeInsets.all(2),
                child: Material(
                  color: isSelected
                      ? AppColors.brand
                      : isToday
                          ? AppColors.accentSoft
                          : Colors.transparent,
                  borderRadius: BorderRadius.circular(10),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: isPast
                        ? null
                        : () {
                            setState(() {
                              _date = d;
                              _start = null;
                              _court = null;
                              _price = null;
                            });
                            _loadAvailableStarts();
                          },
                    child: Center(
                      child: Text(
                        '$day',
                        style: TextStyle(
                          fontSize: 15,
                          fontWeight: isSelected || isToday
                              ? FontWeight.w800
                              : FontWeight.w500,
                          color: isSelected
                              ? Colors.white
                              : isPast
                                  ? theme.colorScheme.onSurface
                                      .withValues(alpha: 0.3)
                                  : theme.colorScheme.onSurface,
                        ),
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  List<String> _weekdayLabels(AppLocalizations l10n) {
    // One letter per weekday, localized via DateFormat.
    final out = <String>[];
    // 2024-01-01 is a Monday — perfect for building Mon..Sun labels.
    final monday = DateTime(2024, 1, 1);
    for (var i = 0; i < 7; i++) {
      final d = monday.add(Duration(days: i));
      out.add(DateFormat('EEE', l10n.localeName).format(d).substring(0, 2));
    }
    return out;
  }

  // ── Step 1: COURTS free for the chosen slot ────────────────────────────
  Widget _buildCourtStep(AppLocalizations l10n) {
    final dateLabel = DateFormat('EEEE, d MMM', l10n.localeName).format(_date);
    final timeLabel = _start == null ? '' : _fmtTime(_start!);
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        Text(
          '$dateLabel · $timeLabel · $_duration ${l10n.durationMin}',
          style:
              Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 18),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
        ),
        const SizedBox(height: AppSpacing.sm),
        Text(
          l10n.availableCourts,
          style:
              Theme.of(context).textTheme.titleMedium?.copyWith(fontSize: 18),
        ),
        const SizedBox(height: AppSpacing.md),
        _errorBox(),
        if (_loadingCourts)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 32),
            child: Center(child: CircularProgressIndicator()),
          )
        else if (_courtsFree.isEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Center(
              child: Text(
                l10n.noCourtsAvailable,
                style: const TextStyle(fontSize: 16),
              ),
            ),
          )
        else
          ..._courtsFree.map((entry) {
            final c = entry['court'] as Map<String, dynamic>;
            final selected = _court?['id'] == c['id'];
            return Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: Card(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
                  side: BorderSide(
                    color: selected
                        ? Theme.of(context).colorScheme.primary
                        : Theme.of(context).colorScheme.outline,
                    width: selected ? 2 : 1,
                  ),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.md, vertical: AppSpacing.xs),
                  leading: Icon(
                    Icons.sports_tennis_outlined,
                    size: 28,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  title: Text(
                    '${c['name']}',
                    style: const TextStyle(
                        fontSize: 17, fontWeight: FontWeight.w700),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  subtitle: Text(
                    '${c['court_type']} · \$${c['price_base']} ${l10n.perHour}',
                    style: const TextStyle(fontSize: 14),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  trailing: selected
                      ? Icon(Icons.check_circle,
                          color: Theme.of(context).colorScheme.primary)
                      : const Icon(Icons.chevron_right),
                  onTap: () => setState(() {
                    _court = c;
                    _error = null;
                  }),
                ),
              ),
            );
          }),
        const SizedBox(height: AppSpacing.lg),
        Row(
          children: [
            TextButton(
              onPressed: () => setState(() {
                _step = 0;
                _error = null;
              }),
              child: Text(l10n.back, style: const TextStyle(fontSize: 16)),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _court == null
                  ? null
                  : () {
                      setState(() => _step = 2);
                      _previewPrice();
                    },
              child: Text(l10n.next, style: const TextStyle(fontSize: 16)),
            ),
          ],
        ),
      ],
    );
  }

  // ── Step 2: SUMMARY + CONFIRM ──────────────────────────────────────────
  Widget _buildSummaryStep(AppLocalizations l10n) {
    final court = _court!;
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${court['name']}',
                    style: Theme.of(context)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontSize: 22),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis),
                const SizedBox(height: AppSpacing.sm),
                _row(l10n.selectDate,
                    DateFormat('EEEE, d MMM', l10n.localeName).format(_date)),
                if (_start != null) _row(l10n.selectSlot, _fmtTime(_start!)),
                _row(l10n.duration, '$_duration ${l10n.durationMin}'),
                const Divider(height: AppSpacing.lg),
                Row(
                  children: [
                    Text(l10n.total,
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontSize: 18)),
                    const Spacer(),
                    Text(
                      _price == null ? l10n.loading : '\$$_price',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                            fontSize: 24,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        _errorBox(),
        Row(
          children: [
            TextButton(
              onPressed: _submitting
                  ? null
                  : () => setState(() {
                        _step = 1;
                        _error = null;
                      }),
              child: Text(l10n.back, style: const TextStyle(fontSize: 16)),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _submitting ? null : _submitBooking,
              child: _submitting
                  ? const SizedBox(
                      height: 22,
                      width: 22,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(
                      '${l10n.confirm} · \$$_price',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 16),
                    ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Flexible(
            child: Text(
              label,
              style: const TextStyle(fontSize: 16),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 8),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              textAlign: TextAlign.end,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  // ── Step 3: DONE ───────────────────────────────────────────────────────
  Widget _buildDoneStep(AppLocalizations l10n) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.check_circle_outlined,
              color: Theme.of(context).colorScheme.primary,
              size: 80,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              l10n.paymentSuccess,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontSize: 24),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(l10n.paymentPending,
                style: const TextStyle(fontSize: 16),
                textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.lg),
            FilledButton(
              onPressed: () {
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              child: Text(l10n.bookings, style: const TextStyle(fontSize: 16)),
            ),
          ],
        ),
      ),
    );
  }
}
