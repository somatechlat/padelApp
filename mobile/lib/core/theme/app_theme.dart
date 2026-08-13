import 'package:flutter/material.dart';

/// Brand palette: tasteful navy blue and muted gold accents.
/// Flat, clean, no gradients or emojis anywhere in the UI.
abstract final class AppColors {
  static const brand = Color(0xFF17456E);
  static const brandDeep = Color(0xFF0E2F4C);
  static const brandLight = Color(0xFF9CC3E8);

  static const accent = Color(0xFFC89B3C);
  static const accentSoft = Color(0xFFF3E7C9);

  static const success = Color(0xFF2E7D4F);
  static const warning = Color(0xFFB07D12);
  static const danger = Color(0xFFB3261E);

  static const background = Color(0xFFF5F7FA);
  static const surface = Color(0xFFFFFFFF);
  static const onSurface = Color(0xFF1B2430);
  static const textMuted = Color(0xFF5B6472);
  static const outline = Color(0xFFD8DEE6);

  static const backgroundDark = Color(0xFF0B1219);
  static const surfaceDark = Color(0xFF141D27);
  static const onSurfaceDark = Color(0xFFE6EBF1);
  static const textMutedDark = Color(0xFF9AA5B1);
  static const outlineDark = Color(0xFF2A3743);
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
    final scheme = ColorScheme.fromSeed(seedColor: AppColors.brand)
        .copyWith(
      brightness: brightness,
      primary: isDark ? AppColors.brandLight : AppColors.brand,
      secondary: isDark ? const Color(0xFFE3C06E) : AppColors.accent,
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
            color: selected ? scheme.primary : muted,
          );
        }),
        iconTheme: WidgetStateProperty.resolveWith((states) {
          final selected = states.contains(WidgetState.selected);
          return IconThemeData(color: selected ? scheme.primary : muted);
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
        labelColor: scheme.primary,
        unselectedLabelColor: muted,
        indicatorColor: scheme.primary,
        labelStyle: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
        unselectedLabelStyle: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 14,
        ),
      ),
      dividerTheme: DividerThemeData(color: outline, thickness: 1, space: 1),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: scheme.primary,
        foregroundColor: AppColors.surface,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        ),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(color: scheme.primary),
      listTileTheme: ListTileThemeData(iconColor: muted),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected)
              ? scheme.primary
              : muted;
        }),
        trackColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected)
              ? AppColors.accentSoft
              : outline;
        }),
      ),
      textTheme: TextTheme(
        headlineMedium: TextStyle(
          color: onSurface,
          fontSize: 26,
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
        bodyLarge: TextStyle(color: onSurface, fontSize: 16),
        bodyMedium: TextStyle(color: onSurface, fontSize: 14),
        bodySmall: TextStyle(color: muted, fontSize: 12),
      ),
    );
  }
}
