import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/theme/app_theme.dart';
import 'payment_method_screen.dart';

class BookingWizardScreen extends StatefulWidget {
  const BookingWizardScreen({super.key});

  @override
  State<BookingWizardScreen> createState() => _BookingWizardScreenState();
}

class _BookingWizardScreenState extends State<BookingWizardScreen> {
  static const _durations = [30, 60, 90, 120];
  static const _playersOptions = [2, 3, 4];

  int _step = 0;
  List<dynamic>? _courts;
  List<dynamic> _slots = [];
  Map<String, dynamic>? _court;
  Map<String, dynamic>? _slot;
  DateTime _date = DateTime.now().add(const Duration(days: 1));
  int _duration = 60;
  int _players = 4;
  String? _price;
  String? _error;
  bool _submitting = false;

  @override
  void initState() {
    super.initState();
    _date = DateTime.now();
    _loadCourts();
  }

  Future<void> _loadCourts() async {
    try {
      final data = await context.read<ApiClient>().get('/courts/');
      final list = data is Map ? data['results'] : data;
      if (!mounted) return;
      setState(() {
        _courts = (list as List<dynamic>? ?? []);
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  String _fmt(DateTime d) => DateFormat('yyyy-MM-dd').format(d);

  Future<void> _loadAvailability() async {
    final court = _court;
    if (court == null) return;
    try {
      final data = await context
          .read<ApiClient>()
          .get('/courts/${court['id']}/availability/', query: {'date': _fmt(_date)});
      if (!mounted) return;
      setState(() {
        _slots = (data as List<dynamic>? ?? [])
            .where((s) => (s as Map)['status'] == 'available')
            .toList();
        _slot = null;
        _price = null;
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  Future<void> _previewPrice() async {
    final court = _court;
    if (court == null || _slot == null) return;
    try {
      final data = await context.read<ApiClient>().post('/bookings/preview/', data: {
        'court': court['id'],
        'date': _fmt(_date),
        'start_time': _slot!['start'],
        'duration_minutes': _duration,
      });
      if (!mounted) return;
      setState(() {
        _price = '${data['price']}';
        _error = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    }
  }

  Future<void> _submitBooking() async {
    final l10n = AppLocalizations.of(context);
    final court = _court;
    final slot = _slot;
    if (court == null || slot == null) return;
    setState(() {
      _submitting = true;
      _error = null;
    });
    final api = context.read<ApiClient>();
    try {
      final booking = await api.post('/bookings/', data: {
        'court': court['id'],
        'date': _fmt(_date),
        'start_time': slot['start'],
        'duration_minutes': _duration,
        'players': _players,
      });
      final bookingId = booking['id'];
      await api.post('/bookings/$bookingId/confirm/');
      if (mounted) {
        setState(() {
          _submitting = false;
        });
        final paymentResult = await Navigator.of(context).push(
          MaterialPageRoute(
            builder: (_) => PaymentMethodScreen(
              bookingId: bookingId,
              amount: double.tryParse(_price ?? '0') ?? 0,
            ),
          ),
        );
        if (mounted) {
          setState(() {
            _step = 3;
          });
        }
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _submitting = false;
          _error = l10n.slotTaken;
        });
      }
    }
  }

  void _selectCourt(Map<String, dynamic> court) {
    setState(() {
      _court = court;
      _slot = null;
      _price = null;
      _step = 1;
      _error = null;
    });
    _loadAvailability();
  }

  void _selectDate(DateTime d) {
    setState(() {
      _date = d;
      _slot = null;
      _price = null;
    });
    _loadAvailability();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final steps = [
      l10n.stepCourt,
      l10n.stepSchedule,
      l10n.stepSummary,
      l10n.stepDone,
    ];
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.bookCourt),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(4),
          child: LinearProgressIndicator(
            value: (_step + 1) / steps.length,
          ),
        ),
      ),
      body: _buildBody(l10n),
    );
  }

  Widget _buildBody(AppLocalizations l10n) {
    if (_error != null && _courts == null && _step == 0) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              _error!,
              style: TextStyle(
                color: Theme.of(context).colorScheme.error,
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: _loadCourts, child: Text(l10n.retry)),
          ],
        ),
      );
    }
    switch (_step) {
      case 0:
        return _buildCourtStep(l10n);
      case 1:
        return _buildScheduleStep(l10n);
      case 2:
        return _buildSummaryStep(l10n);
      default:
        return _buildDoneStep(l10n);
    }
  }

  Widget _buildCourtStep(AppLocalizations l10n) {
    final courts = _courts;
    if (courts == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.md),
      itemCount: courts.length,
      itemBuilder: (context, i) {
        final c = courts[i] as Map<String, dynamic>;
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: Card(
            child: ListTile(
              leading: Icon(
                Icons.sports_tennis_outlined,
                color: Theme.of(context).colorScheme.primary,
              ),
              title: Text('${c['name']}'),
              subtitle: Text(
                  '${c['court_type']} · \$${c['price_base']} ${l10n.perHour}'),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => _selectCourt(c),
            ),
          ),
        );
      },
    );
  }

  Widget _buildScheduleStep(AppLocalizations l10n) {
    final today = DateTime.now();
    final dates = List.generate(7, (i) => today.add(Duration(days: i)));
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        Text(l10n.selectDate, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: AppSpacing.xs),
        SizedBox(
          height: 72,
          child: ListView.separated(
            scrollDirection: Axis.horizontal,
            itemCount: dates.length,
            separatorBuilder: (_, __) => const SizedBox(width: 8),
            itemBuilder: (context, i) {
              final d = dates[i];
              final selected = _date.year == d.year && _date.month == d.month && _date.day == d.day;
              final today = d.day == DateTime.now().day && d.month == DateTime.now().month;
              return ChoiceChip(
                label: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(DateFormat('EEE', l10n.localeName).format(d)),
                    Text('${d.day}'),
                  ],
                ),
                selected: selected,
                onSelected: (_) => _selectDate(d),
                tooltip: today ? '${d.day}/${d.month}' : '${d.day}/${d.month}',
              );
            },
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        Row(
          children: [
            Expanded(
              child: _dropdown<int>(
                l10n.duration,
                _duration,
                _durations,
                (v) => '$v ${l10n.durationMin}',
                (v) => setState(() {
                  _duration = v;
                  _price = null;
                  _slot = null;
                }),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: _dropdown<int>(
                l10n.minPlayers,
                _players,
                _playersOptions,
                (v) => '$v',
                (v) => setState(() => _players = v),
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.lg),
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        if (_slots.isEmpty && _error == null)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Center(child: Text(l10n.noAvailableSlots)),
          )
        else ...[
          const SizedBox(height: AppSpacing.lg),
          Text(l10n.selectSlot, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.xs),
          Wrap(
            spacing: AppSpacing.xs,
            runSpacing: AppSpacing.xs,
            children: _slots.map((s) {
              final start = timeShort('${s['start']}');
              final selected = _slot == s;
              return ChoiceChip(
                label: Text(start),
                selected: selected,
                onSelected: (_) => setState(() {
                  _slot = s;
                  _error = null;
                }),
              );
            }).toList(),
          ),
        ],
        const SizedBox(height: AppSpacing.lg),
        Row(
          children: [
            TextButton(
              onPressed: () => setState(() {
                _step = 0;
                _error = null;
              }),
              child: Text(l10n.back),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _slot == null
                  ? null
                  : () {
                      setState(() => _step = 2);
                      _previewPrice();
                    },
              child: Text(l10n.next),
            ),
          ],
        ),
      ],
    );
  }

  Widget _dropdown<T>(
    String label,
    T value,
    List<T> options,
    String Function(T) format,
    ValueChanged<T> onChanged,
  ) {
    return InputDecorator(
      decoration: InputDecoration(
        labelText: label,
        border: const OutlineInputBorder(),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<T>(
          value: value,
          isExpanded: true,
          items: [
            for (final option in options)
              DropdownMenuItem(value: option, child: Text(format(option))),
          ],
          onChanged: (v) {
            if (v != null) onChanged(v);
          },
        ),
      ),
    );
  }

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
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: AppSpacing.xs),
                _row(l10n.selectDate,
                    DateFormat('EEEE, d MMM', l10n.localeName).format(_date)),
                _row(l10n.duration, '$_duration min'),
                _row(l10n.minPlayers, '$_players'),
                if (_slot != null)
                  _row(l10n.selectSlot, timeShort('${_slot!['start']}')),
                const Divider(height: AppSpacing.lg),
                Row(
                  children: [
                    Text(l10n.total,
                        style: Theme.of(context).textTheme.titleMedium),
                    const Spacer(),
                    Text(
                      _price == null ? l10n.loading : '\$$_price',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
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
        if (_error != null)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        Row(
          children: [
            TextButton(
              onPressed: _submitting
                  ? null
                  : () => setState(() {
                        _step = 1;
                        _error = null;
                      }),
              child: Text(l10n.back),
            ),
            const Spacer(),
            FilledButton(
              onPressed: _submitting ? null : _submitBooking,
              child: _submitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text('${l10n.confirm} · \$$_price'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _row(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
          const Spacer(),
          Text(value, style: Theme.of(context).textTheme.bodyMedium),
        ],
      ),
    );
  }

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
              size: 72,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(l10n.paymentSuccess,
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.xs),
            Text(l10n.paymentPending, textAlign: TextAlign.center),
            const SizedBox(height: AppSpacing.lg),
            FilledButton(
              onPressed: () {
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              child: Text(l10n.bookings),
            ),
          ],
        ),
      ),
    );
  }
}
