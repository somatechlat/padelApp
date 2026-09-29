import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/theme/app_theme.dart';

/// Hero greeting banner (home layout step 2).
class HomeHeroBanner extends StatelessWidget {
  const HomeHeroBanner({super.key, required this.l10n, required this.userName});

  final AppLocalizations l10n;
  final String userName;

  @override
  Widget build(BuildContext context) {
    final greeting =
        userName.isNotEmpty ? l10n.homeGreeting(userName) : l10n.homeWelcome;
    return Container(
      width: double.infinity,
      padding:
          const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: 20),
      decoration: BoxDecoration(
        color: AppColors.brand,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  l10n.appTagline,
                  style: TextStyle(
                    color: Colors.white.withValues(alpha: 0.75),
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  greeting,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w800,
                    height: 1.2,
                  ),
                ),
              ],
            ),
          ),
          Container(
            width: 56,
            height: 56,
            decoration: BoxDecoration(
              color: AppColors.accentSoft.withValues(alpha: 0.25),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.sports_tennis_outlined,
              color: AppColors.accentSoft,
              size: 28,
            ),
          ),
        ],
      ),
    );
  }
}
