import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/widgets/brand_logo.dart';

/// Hero logo + notifications bell (home layout step 1).
class HomeHeader extends StatelessWidget {
  const HomeHeader({super.key, required this.l10n, this.onOpenNotifications});

  final AppLocalizations l10n;
  final VoidCallback? onOpenNotifications;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Row(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        // Hero logo — the brand mark is the first thing on the page.
        Expanded(
          child: Align(
            alignment: Alignment.centerLeft,
            child: BrandLogo(height: BrandLogo.authHeight(context)),
          ),
        ),
        Container(
          decoration: BoxDecoration(
            color: scheme.surface,
            shape: BoxShape.circle,
            border: Border.all(color: scheme.outline),
          ),
          child: IconButton(
            tooltip: l10n.notifications,
            icon: Icon(Icons.notifications_none, color: scheme.onSurface),
            onPressed: onOpenNotifications,
          ),
        ),
      ],
    );
  }
}
