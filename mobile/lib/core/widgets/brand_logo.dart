import 'dart:math' as math;

import 'package:flutter/material.dart';

/// Andes Padel brand logo. Always `assets/images/LOGOTIPO-ANDES-PADEL.png`.
///
/// Never uses Material/ISO icons as a logo. Only [height] is configurable;
/// width follows the asset aspect ratio via [FittedBox] so the logo never
/// distorts on any screen size.
class BrandLogo extends StatelessWidget {
  const BrandLogo({
    super.key,
    this.height = 48,
    this.semanticLabel,
  });

  static const assetPath = 'assets/images/LOGOTIPO-ANDES-PADEL.png';

  /// Rendered height in logical pixels. Width is derived from the asset.
  final double height;
  final String? semanticLabel;

  /// Auth-screen logo height: preferred 140, capped to `width * 0.45`,
  /// clamped to [96, 180].
  static double authHeight(BuildContext context) {
    final cap = MediaQuery.sizeOf(context).width * 0.45;
    return math.min(140.0, cap).clamp(96.0, 180.0);
  }

  @override
  Widget build(BuildContext context) {
    return FittedBox(
      fit: BoxFit.contain,
      child: Image.asset(
        assetPath,
        height: height,
        fit: BoxFit.contain,
        filterQuality: FilterQuality.medium,
        semanticLabel: semanticLabel ?? 'Andes Padel',
        errorBuilder: (context, error, stackTrace) => SizedBox(
          height: height,
          child: const SizedBox.shrink(),
        ),
      ),
    );
  }
}
