import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/widgets/password_field.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';

void main() {
  testWidgets('PasswordField toggles obscureText via suffix icon',
      (tester) async {
    final controller = TextEditingController();
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('es'),
        home: Scaffold(
          body: PasswordField(
            controller: controller,
            label: 'Contraseña',
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    final field = tester.widget<TextField>(find.byType(TextField));
    expect(field.obscureText, isTrue);
    expect(find.byIcon(Icons.visibility_off), findsOneWidget);

    await tester.tap(find.byIcon(Icons.visibility_off));
    await tester.pumpAndSettle();

    final revealed = tester.widget<TextField>(find.byType(TextField));
    expect(revealed.obscureText, isFalse);
    expect(find.byIcon(Icons.visibility), findsOneWidget);

    await tester.tap(find.byIcon(Icons.visibility));
    await tester.pumpAndSettle();

    final hiddenAgain = tester.widget<TextField>(find.byType(TextField));
    expect(hiddenAgain.obscureText, isTrue);
    expect(find.byIcon(Icons.visibility_off), findsOneWidget);
  });

  testWidgets('PasswordField uses controller and onSubmitted', (tester) async {
    final controller = TextEditingController();
    addTearDown(controller.dispose);
    String? submitted;

    await tester.pumpWidget(
      MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        locale: const Locale('es'),
        home: Scaffold(
          body: PasswordField(
            controller: controller,
            label: 'Contraseña',
            onSubmitted: (v) => submitted = v,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), 'secret');
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await tester.pump();

    expect(controller.text, 'secret');
    expect(submitted, 'secret');
  });
}
