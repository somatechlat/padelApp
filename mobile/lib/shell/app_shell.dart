import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import '../features/bookings/bookings_screen.dart';
import '../features/events/events_screen.dart';
import '../features/home/home_screen.dart';
import '../features/notifications/notifications_screen.dart';
import '../features/notifications/unread_store.dart';
import '../features/profile/profile_screen.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final unread = context.watch<UnreadStore>().count;
    final screens = [
      HomeScreen(onOpenNotifications: () => setState(() => _index = 3)),
      const BookingsScreen(),
      const EventsScreen(),
      NotificationsScreen(onOpenBookings: () => setState(() => _index = 1)),
      const ProfileScreen(),
    ];
    return Scaffold(
      body: IndexedStack(index: _index, children: screens),
      // Icon-only bottom bar: labels are replaced by tooltips so the bar
      // never stretches or wraps text on small screens.
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysHide,
        destinations: [
          NavigationDestination(
            icon: Tooltip(
              message: l10n.home,
              child: const Icon(Icons.home_outlined),
            ),
            selectedIcon: Tooltip(
              message: l10n.home,
              child: const Icon(Icons.home),
            ),
            label: l10n.home,
          ),
          NavigationDestination(
            icon: Tooltip(
              message: l10n.navBookings,
              child: const Icon(Icons.event_note_outlined),
            ),
            selectedIcon: Tooltip(
              message: l10n.navBookings,
              child: const Icon(Icons.event_note),
            ),
            label: l10n.navBookings,
          ),
          NavigationDestination(
            icon: Tooltip(
              message: l10n.navEvents,
              child: const Icon(Icons.emoji_events_outlined),
            ),
            selectedIcon: Tooltip(
              message: l10n.navEvents,
              child: const Icon(Icons.emoji_events),
            ),
            label: l10n.navEvents,
          ),
          NavigationDestination(
            icon: Tooltip(
              message: l10n.navNotifications,
              child: _badge(unread, const Icon(Icons.notifications_outlined)),
            ),
            selectedIcon: Tooltip(
              message: l10n.navNotifications,
              child: _badge(unread, const Icon(Icons.notifications)),
            ),
            label: l10n.navNotifications,
          ),
          NavigationDestination(
            icon: Tooltip(
              message: l10n.profile,
              child: const Icon(Icons.person_outline),
            ),
            selectedIcon: Tooltip(
              message: l10n.profile,
              child: const Icon(Icons.person),
            ),
            label: l10n.profile,
          ),
        ],
      ),
    );
  }

  Widget _badge(int count, Widget child) {
    if (count <= 0) return child;
    return Badge(
      label: Text(count > 99 ? '99+' : '$count'),
      child: child,
    );
  }
}
