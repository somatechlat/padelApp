import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/friendly_error.dart';
import '../../core/theme/app_theme.dart';
import 'payment_method_screen.dart';
import 'widgets/booking_constants.dart';
import 'widgets/court_step.dart';
import 'widgets/when_step.dart';

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
      final needed = (_duration / kSlotMinutes).ceil();
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
                .add(start + Duration(minutes: kSlotMinutes * i));
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
        'start_time': fmtBookTime(start),
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
        'start_time': fmtBookTime(start),
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

  void _onMonthChanged(DateTime month) {
    setState(() => _visibleMonth = month);
  }

  void _onDateSelected(DateTime d) {
    setState(() {
      _date = d;
      _start = null;
      _court = null;
      _price = null;
    });
    _loadAvailableStarts();
  }

  void _onDurationSelected(int d) {
    setState(() {
      _duration = d;
      _start = null;
      _court = null;
      _price = null;
    });
    _loadAvailableStarts();
  }

  void _onStartSelected(Duration? d) {
    setState(() {
      _start = d;
      _court = null;
      _price = null;
      _error = null;
    });
  }

  void _onCourtSelected(Map<String, dynamic> c) {
    setState(() {
      _court = c;
      _error = null;
    });
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
        return BookingWhenStep(
          l10n: l10n,
          selectedDate: _date,
          visibleMonth: _visibleMonth,
          duration: _duration,
          start: _start,
          starts: _starts,
          loadingStarts: _loadingStarts,
          onMonthChanged: _onMonthChanged,
          onDateSelected: _onDateSelected,
          onDurationSelected: _onDurationSelected,
          onStartSelected: _onStartSelected,
          onContinue: () {
            setState(() => _step = 1);
            _loadCourtsForSlot();
          },
        );
      case 1:
        return BookingCourtStep(
          l10n: l10n,
          date: _date,
          start: _start,
          duration: _duration,
          courtsFree: _courtsFree,
          selectedCourt: _court,
          loadingCourts: _loadingCourts,
          error: _error,
          onCourtSelected: _onCourtSelected,
          onBack: () {
            setState(() {
              _step = 0;
              _error = null;
            });
          },
          onContinue: () {
            setState(() => _step = 2);
            _previewPrice();
          },
        );
      case 2:
        return _buildSummaryStep(l10n);
      default:
        return _buildDoneStep(l10n);
    }
  }

  Widget _errorBox() {
    if (_error == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Text(
        _error!,
        style: TextStyle(color: Theme.of(context).colorScheme.error),
      ),
    );
  }

  // ── Step 2: SUMMARY + CONFIRM ──────────────────────────────────────────
  Widget _buildSummaryStep(AppLocalizations l10n) {
    final court = _court!;
    final theme = Theme.of(context);
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
                    style: theme.textTheme.titleLarge
                        ?.copyWith(fontSize: BookDim.sectionTitleSize + 4),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis),
                const SizedBox(height: AppSpacing.sm),
                _row(l10n.selectDate,
                    DateFormat('EEEE, d MMM', l10n.localeName).format(_date)),
                if (_start != null) _row(l10n.selectSlot, fmtBookTime(_start!)),
                _row(l10n.duration, '$_duration ${l10n.durationMin}'),
                const Divider(height: AppSpacing.lg),
                Row(
                  children: [
                    Text(l10n.total,
                        style: theme.textTheme.titleMedium
                            ?.copyWith(fontSize: BookDim.sectionTitleSize)),
                    const Spacer(),
                    Text(
                      _price == null ? l10n.loading : '\$$_price',
                      style: theme.textTheme.titleLarge?.copyWith(
                        fontSize: 24,
                        color: theme.colorScheme.primary,
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
              child: Text(l10n.back,
                  style: const TextStyle(fontSize: BookDim.buttonLabelSize)),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _submitting ? null : _submitBooking,
              child: _submitting
                  ? const SizedBox(
                      height: BookDim.progressSize,
                      width: BookDim.progressSize,
                      child: CircularProgressIndicator(
                          strokeWidth: BookDim.progressStroke),
                    )
                  : Text(
                      '${l10n.confirm} · \$$_price',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: BookDim.buttonLabelSize),
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
              style: const TextStyle(fontSize: BookDim.bodySize),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: AppSpacing.xs),
          Flexible(
            child: Text(
              value,
              style: const TextStyle(
                  fontSize: BookDim.bodySize, fontWeight: FontWeight.w600),
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
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.check_circle_outlined,
              color: theme.colorScheme.primary,
              size: 80,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              l10n.paymentSuccess,
              style: theme.textTheme.titleLarge?.copyWith(fontSize: 24),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(l10n.paymentPending,
                style: const TextStyle(fontSize: BookDim.bodySize),
                textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.lg),
            FilledButton(
              onPressed: () {
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              child: Text(l10n.bookings,
                  style: const TextStyle(fontSize: BookDim.buttonLabelSize)),
            ),
          ],
        ),
      ),
    );
  }
}
