import 'package:flutter/foundation.dart';

/// Shared unread-notification count for the nav badge and the list screen.
///
/// Kept deliberately tiny: the list screen owns the truth (it already loads
/// every notification) and pushes its count here after load / mark-read. A
/// foreground push also bumps the count so the badge moves before the user
/// opens the tab.
class UnreadStore extends ChangeNotifier {
  int _count = 0;

  int get count => _count;

  void setCount(int value) {
    final next = value < 0 ? 0 : value;
    if (next == _count) return;
    _count = next;
    notifyListeners();
  }

  void increment() => setCount(_count + 1);

  void decrement() => setCount(_count - 1);

  void clear() => setCount(0);
}
