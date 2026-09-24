import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:padel_app/core/friendly_error.dart';
import 'package:padel_app/core/widgets/password_field.dart';
import '../../core/api_client.dart';
import 'auth_state.dart';
import 'verify_screen.dart';
import 'widgets/auth_scaffold.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _firstName = TextEditingController();
  final _lastName = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  DateTime? _birthDate;
  int? _skillLevelId;
  List<Map<String, dynamic>> _skillLevels = [];
  bool _accepted = false;

  @override
  void initState() {
    super.initState();
    _loadSkillLevels();
  }

  /// Combo-box options come from the API so admins can edit them.
  Future<void> _loadSkillLevels() async {
    try {
      final data = await context.read<ApiClient>().get('/auth/skill-levels/');
      final list = data is Map ? data['results'] : data;
      if (!mounted) return;
      setState(() {
        _skillLevels = [
          for (final item in (list as List<dynamic>? ?? []))
            Map<String, dynamic>.from(item as Map),
        ];
        if (_skillLevelId == null && _skillLevels.isNotEmpty) {
          _skillLevelId = _skillLevels.first['id'] as int?;
        }
      });
    } catch (e) {
      debugPrint('SKILL LEVELS load failed: $e');
    }
  }

  @override
  void dispose() {
    _firstName.dispose();
    _lastName.dispose();
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _pickBirthDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime(now.year - 18, now.month, now.day),
      firstDate: DateTime(now.year - 90),
      lastDate: DateTime(now.year - 10, now.month, now.day),
    );
    if (picked != null) {
      setState(() => _birthDate = picked);
    }
  }

  Future<void> _submit() async {
    final l10n = AppLocalizations.of(context);
    if (!_accepted) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(l10n.acceptTermsRequired)));
      return;
    }
    if (_birthDate == null) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(l10n.birthDateRequired)));
      return;
    }
    final d = _birthDate!;
    final birth =
        '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    final auth = context.read<AuthState>();
    await auth.register(
      email: _email.text,
      password: _password.text,
      firstName: _firstName.text,
      lastName: _lastName.text,
      birthDate: birth,
      skillLevelId: _skillLevelId,
    );
    if (!mounted) return;
    if (!auth.hasError) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute<void>(
          builder: (_) => VerifyScreen(email: _email.text.trim().toLowerCase()),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return AuthScaffold(
      title: l10n.register,
      subtitle: l10n.registerSubtitle,
      appBarTitle: l10n.register,
      showBackButton: true,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          TextField(
            controller: _firstName,
            textInputAction: TextInputAction.next,
            textCapitalization: TextCapitalization.words,
            decoration: InputDecoration(
              labelText: l10n.firstName,
              prefixIcon: const Icon(Icons.person_outline),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _lastName,
            textInputAction: TextInputAction.next,
            textCapitalization: TextCapitalization.words,
            decoration: InputDecoration(
              labelText: l10n.lastName,
              prefixIcon: const Icon(Icons.person_outline),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            autofillHints: const [AutofillHints.email],
            decoration: InputDecoration(
              labelText: l10n.email,
              prefixIcon: const Icon(Icons.mail_outline),
              border: const OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          PasswordField(
            controller: _password,
            label: l10n.password,
            textInputAction: TextInputAction.next,
            onSubmitted: (_) => _pickBirthDate(),
          ),
          const SizedBox(height: 16),
          // Fecha de nacimiento
          InkWell(
            onTap: _pickBirthDate,
            borderRadius: BorderRadius.circular(8),
            child: InputDecorator(
              decoration: InputDecoration(
                labelText: l10n.birthDate,
                prefixIcon: const Icon(Icons.cake_outlined),
                border: const OutlineInputBorder(),
              ),
              child: Text(
                _birthDate == null
                    ? l10n.selectDate
                    : '${_birthDate!.day.toString().padLeft(2, '0')}/${_birthDate!.month.toString().padLeft(2, '0')}/${_birthDate!.year}',
                style: const TextStyle(fontSize: 16),
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Nivel de juego — combo box, options editable in admin
          DropdownButtonFormField<int>(
            value: _skillLevelId,
            isExpanded: true,
            decoration: InputDecoration(
              labelText: l10n.skillLevel,
              prefixIcon: const Icon(Icons.sports_tennis_outlined),
              border: const OutlineInputBorder(),
            ),
            items: [
              for (final level in _skillLevels)
                DropdownMenuItem<int>(
                  value: level['id'] as int,
                  child: Text(
                    '${level['name']}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
            onChanged: (v) => setState(() => _skillLevelId = v),
          ),
          const SizedBox(height: 16),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            controlAffinity: ListTileControlAffinity.leading,
            value: _accepted,
            onChanged: (v) => setState(() => _accepted = v ?? false),
            title: Text(l10n.acceptTerms),
          ),
          Consumer<AuthState>(
            builder: (context, auth, _) {
              if (auth.hasError) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    friendlyErrorMessage(auth.lastError!, l10n),
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                    textAlign: TextAlign.center,
                  ),
                );
              }
              return const SizedBox.shrink();
            },
          ),
          Consumer<AuthState>(
            builder: (context, auth, _) => FilledButton(
              onPressed: auth.loading ? null : _submit,
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: auth.loading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(l10n.registerButton),
            ),
          ),
        ],
      ),
    );
  }
}
