import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/friendly_error.dart';
import '../../core/theme/app_theme.dart';
import 'transfer_proof_screen.dart';
import 'widgets/booking_constants.dart';

/// Choosing how to pay. Both methods are a single POST and on a bad network
/// that can take several seconds, so the tiles lock and the tapped one shows a
/// spinner for the duration. Without this the screen looked frozen, customers
/// tapped again because nothing said the app was working, and production
/// booking #20 ended up with six cash payments (and six "Pago en el
/// establecimiento" notices) from one reservation.
///
/// The backend is idempotent too — `PaymentService._record_cash_payment` hands
/// back the payment that already exists rather than creating another — because
/// no client can promise a single tap across a flaky network. The two together
/// are the fix.
class PaymentMethodScreen extends StatefulWidget {
  final int bookingId;
  final double amount;

  const PaymentMethodScreen({
    super.key,
    required this.bookingId,
    required this.amount,
  });

  @override
  State<PaymentMethodScreen> createState() => _PaymentMethodScreenState();
}

class _PaymentMethodScreenState extends State<PaymentMethodScreen> {
  /// Which method the customer tapped, while its request is still in flight.
  /// `null` means nothing is being sent, so both tiles are tappable again.
  String? _pending;

  bool get _submitting => _pending != null;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;

    return PopScope(
      // Backing out mid-request leaves the booking confirmed but unpaid with
      // no way back to finish, so navigation is blocked while a POST is live.
      canPop: !_submitting,
      child: Scaffold(
        appBar: AppBar(title: Text(l10n.paymentMethod)),
        body: ListView(
          padding: const EdgeInsets.all(AppSpacing.md),
          children: [
            if (_submitting) ...[
              Card(
                color: scheme.primaryContainer,
                child: Padding(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Row(
                    children: [
                      const SizedBox(
                        height: BookDim.progressSize,
                        width: BookDim.progressSize,
                        child: CircularProgressIndicator(
                          strokeWidth: BookDim.progressStroke,
                        ),
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Text(
                          l10n.paymentProcessing,
                          style: Theme.of(context)
                              .textTheme
                              .bodyMedium
                              ?.copyWith(color: scheme.onPrimaryContainer),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.sm),
            ],
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.lg),
              child: Text(
                l10n.paymentMethodSubtitle,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).textTheme.bodySmall?.color,
                    ),
              ),
            ),
          _MethodTile(
            icon: Icons.account_balance_outlined,
            title: l10n.payWithTransfer,
            subtitle: l10n.transferDescription,
            busy: _pending == 'transfer',
            enabled: !_submitting,
            onTap: _payWithTransfer,
          ),
          const SizedBox(height: AppSpacing.sm),
          _MethodTile(
            icon: Icons.payments_outlined,
            title: l10n.payWithCash,
            subtitle: l10n.cashDescription,
            busy: _pending == 'cash',
            enabled: !_submitting,
            onTap: _payWithCash,
          ),
          const SizedBox(height: AppSpacing.lg),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Row(
                children: [
                  Icon(Icons.info_outline, color: scheme.primary, size: 20),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Text(
                      l10n.transferAmount,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                  Text(
                    '\$${widget.amount}',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: scheme.primary,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ],
              ),
            ),
          ),
          ],
        ),
      ),
    );
  }

  // Card payments are disabled for now — only transfer and pay-at-venue.

  Future<void> _payWithTransfer() async {
    if (_submitting) return;
    setState(() => _pending = 'transfer');
    final api = context.read<ApiClient>();
    try {
      final payment = await api.post(
        '/bookings/${widget.bookingId}/payments/',
        data: {'method': 'transfer'},
      );
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => TransferProofScreen(
            paymentId: payment['id'],
            amount: widget.amount,
          ),
        ),
      );
    } catch (e) {
      debugPrint('TRANSFER pay failed: $e');
      if (!mounted) return;
      final l10n = AppLocalizations.of(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(friendlyErrorMessage(e, l10n))),
      );
      setState(() => _pending = null);
    }
  }

  Future<void> _payWithCash() async {
    if (_submitting) return;
    setState(() => _pending = 'cash');
    final api = context.read<ApiClient>();
    try {
      await api.post(
        '/bookings/${widget.bookingId}/payments/',
        data: {'method': 'cash', 'amount': widget.amount},
      );
      if (!mounted) return;
      // No confirmation copy here: the wizard's done step is the single
      // message both payment methods share (see `paymentPending`).
      Navigator.of(context).pop(true);
    } catch (e) {
      debugPrint('CASH pay failed: $e');
      if (!mounted) return;
      final l10n = AppLocalizations.of(context);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(friendlyErrorMessage(e, l10n))),
      );
      setState(() => _pending = null);
    }
  }
}

class _MethodTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  /// This tile's request is in flight — show a spinner where the chevron was.
  final bool busy;

  /// False while any request is in flight, so a second tap cannot be sent.
  final bool enabled;

  const _MethodTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
    this.busy = false,
    this.enabled = true,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Opacity(
      opacity: enabled ? 1 : 0.6,
      child: Card(
        child: InkWell(
          onTap: enabled ? onTap : null,
          borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: AppColors.accentSoft,
                    borderRadius: BorderRadius.circular(AppSpacing.radius),
                  ),
                  child: Icon(icon, color: scheme.primary),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.xxs),
                      Text(
                        subtitle,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                busy
                    ? const SizedBox(
                        height: BookDim.progressSize,
                        width: BookDim.progressSize,
                        child: CircularProgressIndicator(
                          strokeWidth: BookDim.progressStroke,
                        ),
                      )
                    : Icon(
                        Icons.chevron_right,
                        color: scheme.onSurface.withValues(alpha: 0.4),
                      ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
