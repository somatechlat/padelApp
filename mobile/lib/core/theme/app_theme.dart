import 'package:flutter/material.dart';

/// Brand palette: Electric Volt Green with dark obsidian accents.
/// Flat, clean, no gradients or emojis anywhere in the UI.
/// Contrast rule: #D4FF00 (92% luminance) MUST pair with dark (#121418)
/// text. Never white-on-green or green-on-white — both fail WCAG AA (1.2:1).
abstract final class AppColors {
  static const brand = Color(0xFFD4FF00); // Electric Volt Green
  static const brandDeep = Color(0xFF121418); // Deep Obsidian
  static const brandLight = Color(0xFFE5FF66); // Light Volt

  static const accent = Color(0xFFD4FF00);
  static const accentSoft = Color(0xFF262C18);

  /// Readable green for text/icons on light backgrounds (WCAG AA ≥ 4.5:1).
  static const brandReadable = Color(0xFF3A6B00); // Dark forest green

  static const success = Color(0xFF3A6B00);
  static const warning = Color(0xFFFFC107);
  static const danger = Color(0xFFFF4D4D);

  static const background = Color(0xFFF5F7FA);
  static const surface = Color(0xFFFFFFFF);
  static const onSurface = Color(0xFF121418);
  static const textMuted = Color(0xFF5B6472);
  static const outline = Color(0xFFD8DEE6);

  static const backgroundDark = Color(0xFF121418);
  static const surfaceDark = Color(0xFF1E2229);
  static const onSurfaceDark = Color(0xFFFFFFFF);
  static const textMutedDark = Color(0xFF9AA5B1);
  static const outlineDark = Color(0xFF2E3440);
}

/// Design tokens for spacing and shape.
abstract final class AppSpacing {
  static const xxs = 4.0;
  static const xs = 8.0;
  static const sm = 12.0;
  static const md = 16.0;
  static const lg = 24.0;
  static const xl = 32.0;
  static const radius = 12.0;
  static const radiusCard = 16.0;
  static const radiusDialog = 20.0;
  static const buttonHeight = 48.0;
}

abstract final class AppTheme {
  static ThemeData get light => _build(Brightness.light);
  static ThemeData get dark => _build(Brightness.dark);

  static ThemeData _build(Brightness brightness) {
    final isDark = brightness == Brightness.dark;
    final brandBg = isDark ? AppColors.brandLight : AppColors.brand;
    final brandText = isDark ? AppColors.brandDeep : AppColors.brandDeep;
    final readable = isDark ? AppColors.brandLight : AppColors.brandReadable;
    final navSelected = isDark ? AppColors.brandLight : AppColors.brandDeep;
    final scheme = ColorScheme.fromSeed(seedColor: AppColors.brand).copyWith(
      brightness: brightness,
      primary: brandBg,
      onPrimary: AppColors.brandDeep,
      secondary: isDark ? const Color(0xFFE3C06E) : AppColors.accent,
      onSecondary: AppColors.brandDeep,
      error: AppColors.danger,
      surface: isDark ? AppColors.surfaceDark : AppColors.surface,
      onSurface: isDark ? AppColors.onSurfaceDark : AppColors.onSurface,
    );
    final onSurface = scheme.onSurface;
    final muted = isDark ? AppColors.textMutedDark : AppColors.textMuted;
    final outline = isDark ? AppColors.outlineDark : AppColors.outline;
    final background = isDark ? AppColors.backgroundDark : AppColors.background;

    return ThemeData(
      useMaterial3: true,
      brightness: brightness,
      colorScheme: scheme,
      scaffoldBackgroundColor: background,
      appBarTheme: AppBarTheme(
        backgroundColor: background,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: TextStyle(
          color: onSurface,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
        iconTheme: IconThemeData(color: onSurface),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        color: scheme.surface,
        surfaceTintColor: Colors.transparent,
        margin: EdgeInsets.zero,
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
          side: BorderSide(color: outline),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: scheme.surface,
        contentPadding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        labelStyle: TextStyle(color: muted),
        hintStyle: TextStyle(color: muted),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          borderSide: BorderSide(color: outline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          borderSide: BorderSide(color: outline),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          borderSide: BorderSide(color: scheme.primary, width: 1.6),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          borderSide: BorderSide(color: scheme.error),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(64, AppSpacing.buttonHeight),
          backgroundColor: brandBg,
          foregroundColor: AppColors.brandDeep,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(64, AppSpacing.buttonHeight),
          side: BorderSide(color: outline),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
          ),
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: scheme.surface,
        selectedColor: AppColors.accentSoft,
        side: BorderSide(color: outline),
        shape: const StadiumBorder(),
        labelStyle: TextStyle(color: onSurface),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.xs,
          vertical: AppSpacing.xxs,
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        indicatorColor: AppColors.accentSoft,
        height: 68,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return TextStyle(
            fontSize: 12,
            fontWeight: selected ? FontWeight.w700 : FontWeight.w500,
            color: selected ? navSelected : muted,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(color: selected ? navSelected : muted);
        }),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radius),
        ),
        backgroundColor: AppColors.onSurface,
        contentTextStyle: TextStyle(color: AppColors.surface),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: scheme.surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusDialog),
        ),
        titleTextStyle: TextStyle(
          color: onSurface,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
        contentTextStyle: TextStyle(color: onSurface, fontSize: 15),
      ),
      tabBarTheme: TabBarThemeData(
        labelColor: navSelected,
        unselectedLabelColor: muted,
        indicatorColor: navSelected,
        labelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
        unselectedLabelStyle: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 14,
        ),
      ),
      dividerTheme: DividerThemeData(color: outline, thickness: 1, space: 1),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: brandBg,
        foregroundColor: AppColors.brandDeep,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        ),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(color: readable),
      listTileTheme: ListTileThemeData(iconColor: muted),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected)
              ? AppColors.brandDeep
              : muted;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected)
              ? brandBg
              : outline;
        }),
      ),
      textTheme: TextTheme(
        headlineMedium: TextStyle(
          color: onSurface,
          fontSize: 28,
          fontWeight: FontWeight.w700,
        ),
        titleLarge: TextStyle(
          color: onSurface,
          fontSize: 20,
          fontWeight: FontWeight.w700,
        ),
        titleMedium: TextStyle(
          color: onSurface,
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
        titleSmall: TextStyle(
          color: onSurface,
          fontSize: 14,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: TextStyle(color: onSurface, fontSize: 16),
        bodyMedium: TextStyle(color: onSurface, fontSize: 14),
        bodySmall: TextStyle(color: muted, fontSize: 12),
      ),
    );
  }
}
