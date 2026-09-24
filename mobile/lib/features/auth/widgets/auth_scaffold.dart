import 'package:flutter/material.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import '../../../core/widgets/brand_logo.dart';

/// Shared auth layout: Andes brand logo on top, then title/subtitle and form.
class AuthScaffold extends StatelessWidget {
  const AuthScaffold({
    super.key,
    required this.title,
    required this.subtitle,
    required this.child,
    this.appBarTitle,
    this.showBackButton = false,
  });

  final String title;
  final String subtitle;
  final Widget child;

  /// When set, shows an [AppBar] with this title (implies back navigation).
  final String? appBarTitle;
  final bool showBackButton;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final logoHeight = BrandLogo.authHeight(context);
    final showAppBar = showBackButton || appBarTitle != null;
    return Scaffold(
      appBar: showAppBar
          ? AppBar(title: appBarTitle != null ? Text(appBarTitle!) : null)
          : null,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Center(
                    child: BrandLogo(
                      height: logoHeight,
                      semanticLabel: l10n.appTitle,
                    ),
                  ),
                  const SizedBox(height: 32),
                  Text(
                    title,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 24),
                  child,
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
