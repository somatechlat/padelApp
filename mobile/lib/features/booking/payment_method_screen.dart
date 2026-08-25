import 'package:flutter/material.dart';
import 'package:flutter_gen/gen_l10n/app_localizations.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/theme/app_theme.dart';
import 'transfer_proof_screen.dart';

class PaymentMethodScreen extends StatelessWidget {
  final int bookingId;
  final double amount;

  const PaymentMethodScreen({
    super.key,
    required this.bookingId,
    required this.amount,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.paymentMethod)),
      body: ListView(
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
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
            icon: Icons.credit_card_outlined,
            title: l10n.payWithCard,
            subtitle: l10n.cardDescription,
            onTap: () => _payWithCard(context),
          ),
          const SizedBox(height: AppSpacing.sm),
          _MethodTile(
            icon: Icons.account_balance_outlined,
            title: l10n.payWithTransfer,
            subtitle: l10n.transferDescription,
            onTap: () => _payWithTransfer(context),
          ),
          const SizedBox(height: AppSpacing.sm),
          _MethodTile(
            icon: Icons.payments_outlined,
            title: l10n.payWithCash,
            subtitle: l10n.cashDescription,
            onTap: () => _payWithCash(context),
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
                    '\$$amount',
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
    );
  }

  Future<void> _payWithCard(BuildContext context) async {
    final l10n = AppLocalizations.of(context);
    final api = context.read<ApiClient>();
    try {
      final payment = await api.post(
        '/bookings/$bookingId/payments/',
        data: {'method': 'stripe'},
      );
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.paymentProcessing)),
        );
        Navigator.of(context).pop(payment);
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.error)),
        );
      }
    }
  }

  Future<void> _payWithTransfer(BuildContext context) async {
    final api = context.read<ApiClient>();
    try {
      final payment = await api.post(
        '/bookings/$bookingId/payments/',
        data: {'method': 'transfer'},
      );
      if (context.mounted) {
        Navigator.of(context).pushReplacement(
          MaterialPageRoute(
            builder: (_) => TransferProofScreen(
              paymentId: payment['id'],
              amount: amount,
            ),
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        final l10n = AppLocalizations.of(context);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.error)),
        );
      }
    }
  }

  Future<void> _payWithCash(BuildContext context) async {
    final l10n = AppLocalizations.of(context);
    final api = context.read<ApiClient>();
    try {
      await api.post(
        '/bookings/$bookingId/payments/',
        data: {'method': 'cash', 'amount': amount},
      );
      if (context.mounted) {
        Navigator.of(context).pop({'method': 'cash'});
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.error)),
        );
      }
    }
  }
}

class _MethodTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _MethodTile({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      child: InkWell(
        onTap: onTap,
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
              Icon(Icons.chevron_right, color: scheme.onSurface.withValues(alpha: 0.4)),
            ],
          ),
        ),
      ),
    );
  }
}
