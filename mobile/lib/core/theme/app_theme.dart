import 'package:flutter/material.dart';

/// Brand palette: Andes Pádel Club corporate identity.
/// Midnight Blue (#002F48) + Celeste (#3571B8) + Verde Limón (#CEDC29) + White.
/// Flat, clean, no gradients or emojis anywhere in the UI.
abstract final class AppColors {
  // ── Corporate brand palette (from BRANDING CORPORATIVO) ──
  static const brand = Color(0xFF002F48); // Midnight Blue — primary
  static const brandDeep = Color(0xFF001A2A); // Darker Midnight Blue
  static const brandLight = Color(0xFF3571B8); // Celeste — secondary

  static const accent = Color(0xFFCEDC29); // Verde Limón — highlight
  static const accentSoft = Color(0xFFE8EFB0); // Light Verde Limón

  /// Readable on light backgrounds (WCAG AA >= 4.5:1).
  static const brandReadable = Color(0xFF002F48); // Midnight Blue

  static const success = Color(0xFF2E7D32);
  static const warning = Color(0xFFFFC107);
  static const danger = Color(0xFFD32F2F);

  // ── Light mode ──
  static const background = Color(0xFFF5F7FA);
  static const surface = Color(0xFFFFFFFF);
  static const onSurface = Color(0xFF002F48);
  static const textMuted = Color(0xFF5B6472);
  static const outline = Color(0xFFD8DEE6);

  // ── Dark mode ──
  static const backgroundDark = Color(0xFF001219);
  static const surfaceDark = Color(0xFF001F2E);
  static const onSurfaceDark = Color(0xFFFFFFFF);
  static const textMutedDark = Color(0xFF90A4AE);
  static const outlineDark = Color(0xFF1A3A4A);
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
    final readable = isDark ? AppColors.brandLight : AppColors.brandReadable;
    final navSelected = isDark ? AppColors.accent : AppColors.brand;
    final scheme = ColorScheme.fromSeed(
      seedColor: AppColors.brand,
      brightness: brightness,
    ).copyWith(
      primary: brandBg,
      onPrimary: isDark ? AppColors.brandDeep : Colors.white,
      secondary: AppColors.accent,
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
          foregroundColor: isDark ? Colors.white : Colors.white,
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
        backgroundColor: AppColors.brand,
        contentTextStyle: const TextStyle(color: Colors.white),
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
        foregroundColor: isDark ? Colors.white : Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radiusCard),
        ),
      ),
      progressIndicatorTheme: ProgressIndicatorThemeData(color: readable),
      listTileTheme: ListTileThemeData(iconColor: muted),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith((states) {
          return states.contains(WidgetState.selected)
              ? Colors.white
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
