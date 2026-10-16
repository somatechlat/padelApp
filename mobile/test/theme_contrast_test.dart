import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:padel_app/core/theme/app_theme.dart';

/// WCAG 2.1 relative luminance.
double _luminance(Color c) {
  // `Color.r/.g/.b` are already 0.0–1.0, so no /255 here.
  double channel(double s) {
    return s <= 0.03928 ? s / 12.92 : math.pow((s + 0.055) / 1.055, 2.4).toDouble();
  }

  return 0.2126 * channel(c.r) + 0.7152 * channel(c.g) + 0.0722 * channel(c.b);
}

/// WCAG contrast ratio between two opaque colours (1.0 … 21.0).
double contrastRatio(Color a, Color b) {
  final la = _luminance(a);
  final lb = _luminance(b);
  return (math.max(la, lb) + 0.05) / (math.min(la, lb) + 0.05);
}

void main() {
  // WCAG 2.1 AA: 4.5:1 for body text, 3:1 for large text and UI components
  // (icons, borders, focus rings).
  const textAA = 4.5;
  const uiAA = 3.0;

  final themes = <String, ThemeData>{
    'light': AppTheme.light,
    'dark': AppTheme.dark,
  };

  themes.forEach((name, theme) {
    group('$name theme contrast', () {
      test('selected bottom-nav label and icon clear AA on their indicator', () {
        final nav = theme.navigationBarTheme;
        final indicator = nav.indicatorColor!;
        final label = nav.labelTextStyle!.resolve({WidgetState.selected})!.color!;
        final icon = nav.iconTheme!.resolve({WidgetState.selected})!.color!;

        expect(
          contrastRatio(label, indicator),
          greaterThanOrEqualTo(textAA),
          reason: 'menu button label ($label) on its $indicator pill',
        );
        expect(
          contrastRatio(icon, indicator),
          greaterThanOrEqualTo(uiAA),
          reason: 'menu button icon ($icon) on its $indicator pill',
        );
      });

      test('unselected bottom-nav label and icon clear AA on the bar', () {
        final nav = theme.navigationBarTheme;
        final bg = nav.backgroundColor!;
        // "unselected" is the *absence* of WidgetState.selected, so resolve
        // with an empty state set.
        const none = <WidgetState>{};
        final label = nav.labelTextStyle!.resolve(none)!.color!;
        final icon = nav.iconTheme!.resolve(none)!.color!;

        expect(contrastRatio(label, bg), greaterThanOrEqualTo(textAA),
            reason: 'unselected menu label ($label) on $bg');
        expect(contrastRatio(icon, bg), greaterThanOrEqualTo(uiAA),
            reason: 'unselected menu icon ($icon) on $bg');
      });

      test('chip label clears AA on both its idle and selected fills', () {
        final chip = theme.chipTheme;
        final label = chip.labelStyle!.color!;

        expect(contrastRatio(label, chip.selectedColor!), greaterThanOrEqualTo(textAA),
            reason: 'selected chip label ($label) on ${chip.selectedColor}');
        expect(contrastRatio(label, chip.backgroundColor!), greaterThanOrEqualTo(textAA),
            reason: 'idle chip label ($label) on ${chip.backgroundColor}');
      });

      test('body and muted text clear AA on the surfaces they sit on', () {
        final onSurface = theme.textTheme.bodyMedium!.color!;
        final muted = theme.textTheme.bodySmall!.color!;
        final surfaces = [theme.scaffoldBackgroundColor, theme.colorScheme.surface];

        for (final bg in surfaces) {
          expect(contrastRatio(onSurface, bg), greaterThanOrEqualTo(textAA),
              reason: 'body text ($onSurface) on $bg');
          expect(contrastRatio(muted, bg), greaterThanOrEqualTo(textAA),
              reason: 'muted text ($muted) on $bg');
        }
      });

      test('app bar title clears AA on the app bar background', () {
        final appBar = theme.appBarTheme;
        final title = appBar.titleTextStyle!.color!;
        expect(contrastRatio(title, appBar.backgroundColor!), greaterThanOrEqualTo(textAA));
      });
    });
  });

  group('de-emphasised content', () {
    // AppColors.mutedFor replaces the old `onSurface.withValues(alpha: 0.4)`,
    // which measured only 2.3:1 on a white card and 3.4:1 in dark mode.
    test('mutedFor clears AA on its own surface in both themes', () {
      expect(
        contrastRatio(AppColors.mutedFor(Brightness.light), AppColors.surface),
        greaterThanOrEqualTo(textAA),
        reason: 'read notification icon, light',
      );
      expect(
        contrastRatio(AppColors.mutedFor(Brightness.dark), AppColors.surfaceDark),
        greaterThanOrEqualTo(textAA),
        reason: 'read notification icon, dark',
      );
    });
  });
}
