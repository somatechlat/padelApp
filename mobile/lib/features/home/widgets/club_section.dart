import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

import '../../../core/models/club_info.dart';
import '../../../core/theme/app_theme.dart';

/// Club info section (home layout step 5) — loading / error / card.
class HomeClubSection extends StatelessWidget {
  const HomeClubSection({
    super.key,
    required this.l10n,
    required this.club,
    required this.loading,
    required this.loadFailed,
    required this.onRetry,
    required this.onOpen,
  });

  final AppLocalizations l10n;
  final ClubInfo? club;
  final bool loading;
  final bool loadFailed;
  final VoidCallback onRetry;
  final ValueChanged<String> onOpen;

  @override
  Widget build(BuildContext context) {
    if (loading) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(AppSpacing.xl),
          child: CircularProgressIndicator(),
        ),
      );
    }
    final c = club;
    if (c == null) {
      return _ClubErrorBox(
        l10n: l10n,
        loadFailed: loadFailed,
        onRetry: onRetry,
      );
    }
    return ClubInfoCard(
      club: c,
      l10n: l10n,
      onOpen: onOpen,
    );
  }
}

class _ClubErrorBox extends StatelessWidget {
  const _ClubErrorBox({
    required this.l10n,
    required this.loadFailed,
    required this.onRetry,
  });

  final AppLocalizations l10n;
  final bool loadFailed;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: scheme.outline),
      ),
      child: Column(
        children: [
          Icon(
            loadFailed ? Icons.wifi_off_outlined : Icons.storefront_outlined,
            size: 40,
            color: scheme.onSurface.withValues(alpha: 0.35),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            loadFailed ? l10n.networkError : l10n.clubInfo,
            textAlign: TextAlign.center,
            style: TextStyle(
              color: scheme.onSurface.withValues(alpha: 0.6),
              fontSize: 15,
            ),
          ),
          if (loadFailed) ...[
            const SizedBox(height: AppSpacing.md),
            OutlinedButton(
              onPressed: onRetry,
              child: Text(l10n.retry),
            ),
          ],
        ],
      ),
    );
  }
}

/// Elegant club information card — brand palette, flat (no gradients).
///
/// Shows every contact channel from `GET /api/club/` with a clear action
/// per row (call / map / write / Instagram) plus a WhatsApp CTA.
class ClubInfoCard extends StatelessWidget {
  const ClubInfoCard({
    super.key,
    required this.club,
    required this.l10n,
    required this.onOpen,
  });

  final ClubInfo club;
  final AppLocalizations l10n;
  final ValueChanged<String> onOpen;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final mapsUrl = club.resolvedMapsUrl;
    final whatsappUrl = club.resolvedWhatsappUrl;
    final instagramUrl = club.resolvedInstagramUrl;
    final title = club.name.isNotEmpty ? club.name : l10n.appTitle;
    final tagline = club.homeGreetingTagline;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: scheme.surface,
        borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        border: Border.all(color: AppColors.outline),
        boxShadow: [
          BoxShadow(
            color: scheme.shadow.withValues(alpha: 0.08),
            blurRadius: 16,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _ClubHeader(title: title, tagline: tagline),
          _ClubContactList(
            l10n: l10n,
            club: club,
            mapsUrl: mapsUrl,
            instagramUrl: instagramUrl,
            whatsappUrl: whatsappUrl,
            onOpen: onOpen,
          ),
        ],
      ),
    );
  }
}

class _ClubContactList extends StatelessWidget {
  const _ClubContactList({
    required this.l10n,
    required this.club,
    required this.mapsUrl,
    required this.instagramUrl,
    required this.whatsappUrl,
    required this.onOpen,
  });

  final AppLocalizations l10n;
  final ClubInfo club;
  final String mapsUrl;
  final String instagramUrl;
  final String whatsappUrl;
  final ValueChanged<String> onOpen;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(
          AppSpacing.lg, AppSpacing.md, AppSpacing.lg, AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            l10n.clubInfo,
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  color: AppColors.brandLight,
                  fontWeight: FontWeight.w800,
                  letterSpacing: 0.4,
                ),
          ),
          const SizedBox(height: AppSpacing.sm),
          if (club.phone.isNotEmpty)
            _InfoRow(
              icon: Icons.phone_outlined,
              label: l10n.phone,
              value: club.phone,
              actionLabel: l10n.call,
              onAction: () => onOpen('tel:${club.phone}'),
            ),
          if (club.address.isNotEmpty)
            _InfoRow(
              icon: Icons.location_on_outlined,
              label: l10n.clubContact,
              value: club.address,
              actionLabel: mapsUrl.isNotEmpty ? l10n.openMaps : null,
              onAction: mapsUrl.isNotEmpty ? () => onOpen(mapsUrl) : null,
            ),
          if (club.email.isNotEmpty)
            _InfoRow(
              icon: Icons.mail_outline,
              label: l10n.email,
              value: club.email,
              actionLabel: l10n.write,
              onAction: () => onOpen('mailto:${club.email}'),
            ),
          if (instagramUrl.isNotEmpty)
            _InfoRow(
              icon: Icons.camera_alt_outlined,
              label: l10n.instagram,
              value: instagramUrl
                  .replaceFirst('https://instagram.com/', '@')
                  .replaceFirst('https://www.instagram.com/', '@'),
              actionLabel: l10n.instagram,
              onAction: () => onOpen(instagramUrl),
            ),
          if (whatsappUrl.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            _WhatsAppButton(onOpen: () => onOpen(whatsappUrl), l10n: l10n),
          ],
        ],
      ),
    );
  }
}

class _ClubHeader extends StatelessWidget {
  const _ClubHeader({required this.title, required this.tagline});

  final String title;
  final String tagline;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: AppColors.brand,
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 24,
              fontWeight: FontWeight.w900,
              height: 1.15,
            ),
          ),
          if (tagline.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              tagline,
              style: TextStyle(
                color: Colors.white.withValues(alpha: 0.9),
                fontSize: 15,
                fontWeight: FontWeight.w500,
                height: 1.3,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _WhatsAppButton extends StatelessWidget {
  const _WhatsAppButton({required this.onOpen, required this.l10n});

  final VoidCallback onOpen;
  final AppLocalizations l10n;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: FilledButton.icon(
        onPressed: onOpen,
        style: FilledButton.styleFrom(
          backgroundColor: const Color(0xFF25D366),
          foregroundColor: Colors.white,
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
          ),
        ),
        icon: const Icon(Icons.chat_bubble_outline, size: 22),
        label: Text(l10n.whatsapp, maxLines: 1),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String label;
  final String value;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: AppColors.accentSoft,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 22, color: AppColors.brand),
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    color: scheme.onSurface.withValues(alpha: 0.55),
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.3,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    color: AppColors.brandReadable,
                    fontSize: 16,
                    height: 1.3,
                    fontWeight: FontWeight.w600,
                  ),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
          if (onAction != null && actionLabel != null)
            TextButton(
              onPressed: onAction,
              style: TextButton.styleFrom(
                foregroundColor: AppColors.brandLight,
                textStyle: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w800,
                ),
              ),
              child: Text(actionLabel!),
            )
          else if (onAction != null)
            IconButton(
              onPressed: onAction,
              icon: const Icon(Icons.open_in_new, size: 22),
            ),
        ],
      ),
    );
  }
}
