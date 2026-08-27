import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/theme/app_theme.dart';

class TransferProofScreen extends StatefulWidget {
  final int paymentId;
  final double amount;

  const TransferProofScreen({
    super.key,
    required this.paymentId,
    required this.amount,
  });

  @override
  State<TransferProofScreen> createState() => _TransferProofScreenState();
}

class _TransferProofScreenState extends State<TransferProofScreen> {
  File? _image;
  bool _uploading = false;
  bool _uploaded = false;
  String? _error;

  static const _bankName = 'Banco Pichincha';
  static const _accountNumber = '21001234567890';
  static const _accountHolder = 'Andes Pádel S.A.';
  static const _beneficiaryCode = 'ANDESPADEL';

  Future<void> _pickImage(ImageSource source) async {
    final l10n = AppLocalizations.of(context);
    final picker = ImagePicker();
    try {
      final picked = await picker.pickImage(
        source: source,
        maxWidth: 1920,
        maxHeight: 1920,
        imageQuality: 85,
      );
      if (picked == null) return;

      final file = File(picked.path);
      final size = await file.length();
      if (size > 5 * 1024 * 1024) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(l10n.imageTooLarge)),
          );
        }
        return;
      }
      setState(() {
        _image = file;
        _error = null;
      });
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l10n.error)),
        );
      }
    }
  }

  Future<void> _uploadProof() async {
    if (_image == null) return;
    final l10n = AppLocalizations.of(context);
    setState(() {
      _uploading = true;
      _error = null;
    });
    try {
      final api = context.read<ApiClient>();
      final formData = FormData.fromMap({
        'proof_image': await MultipartFile.fromFile(
          _image!.path,
          filename: 'comprobante_${widget.paymentId}.jpg',
        ),
      });
      await api.post(
        '/payments/${widget.paymentId}/upload-proof/',
        data: formData,
      );
      if (mounted) {
        setState(() {
          _uploaded = true;
          _uploading = false;
        });
      }
    } on DioException catch (e) {
      if (mounted) {
        final msg = e.response?.data is Map
            ? (e.response?.data['detail'] ?? l10n.proofUploadError)
            : l10n.proofUploadError;
        setState(() {
          _error = msg;
          _uploading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = l10n.proofUploadError;
          _uploading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.transferInstructions)),
      body: _uploaded ? _buildSuccess(l10n) : _buildForm(l10n, scheme),
    );
  }

  Widget _buildForm(AppLocalizations l10n, ColorScheme scheme) {
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.md),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l10n.transferInstructions,
                    style: Theme.of(context).textTheme.titleMedium),
                const Divider(height: AppSpacing.lg),
                _bankRow(l10n.bankName, _bankName),
                _bankRow(l10n.accountNumber, _accountNumber),
                _bankRow(l10n.accountHolder, _accountHolder),
                _bankRow(l10n.beneficiaryCode, _beneficiaryCode),
                const Divider(height: AppSpacing.lg),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(l10n.transferAmount,
                        style: Theme.of(context).textTheme.bodyMedium),
                    Text(
                      '\$${widget.amount}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            color: scheme.primary,
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        Text(l10n.uploadProof,
            style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: AppSpacing.xs),
        Text(l10n.maxFileSize,
            style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: AppSpacing.md),
        if (_image != null) ...[
          ClipRRect(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
            child: Image.file(
              _image!,
              height: 200,
              width: double.infinity,
              fit: BoxFit.cover,
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
        ],
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _uploading ? null : () => _pickImage(ImageSource.camera),
                icon: const Icon(Icons.camera_alt_outlined),
                label: Text(l10n.camera),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: _uploading ? null : () => _pickImage(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: Text(l10n.gallery),
              ),
            ),
          ],
        ),
        if (_error != null) ...[
          const SizedBox(height: AppSpacing.sm),
          Text(_error!, style: TextStyle(color: scheme.error)),
        ],
        const SizedBox(height: AppSpacing.lg),
        FilledButton(
          onPressed: (_image != null && !_uploading) ? _uploadProof : null,
          child: _uploading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(l10n.send),
        ),
      ],
    );
  }

  Widget _buildSuccess(AppLocalizations l10n) {
    final scheme = Theme.of(context).colorScheme;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              Icons.check_circle_outlined,
              color: scheme.primary,
              size: 72,
            ),
            const SizedBox(height: AppSpacing.md),
            Text(l10n.proofUploaded,
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.xs),
            Text(
              l10n.transferPending,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: AppSpacing.lg),
            FilledButton(
              onPressed: () =>
                  Navigator.of(context).popUntil((route) => route.isFirst),
              child: Text(l10n.home),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bankRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
          Text(value,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
