import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:padel_app/core/l10n/app_localizations.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/models/club_info.dart';
import '../../core/theme/app_theme.dart';
import 'widgets/booking_constants.dart';

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
  ClubInfo? _club;
  bool _clubLoaded = false;

  @override
  void initState() {
    super.initState();
    _loadClub();
  }

  Future<void> _loadClub() async {
    try {
      final data = await context.read<ApiClient>().get('/club/');
      if (!mounted) return;
      if (data is Map) {
        setState(() {
          _club = ClubInfo.fromJson(Map<String, dynamic>.from(data));
          _clubLoaded = true;
        });
      } else {
        setState(() {
          _club = null;
          _clubLoaded = true;
        });
      }
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _club = null;
        _clubLoaded = true;
      });
    }
  }

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
        _BankDetailsCard(
          l10n: l10n,
          scheme: scheme,
          club: _club,
          clubLoaded: _clubLoaded,
          amount: widget.amount,
        ),
        const SizedBox(height: AppSpacing.lg),
        _ProofPicker(
          l10n: l10n,
          scheme: scheme,
          image: _image,
          uploading: _uploading,
          error: _error,
          onPickCamera: () => _pickImage(ImageSource.camera),
          onPickGallery: () => _pickImage(ImageSource.gallery),
          onUpload: _uploadProof,
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
              onPressed: () => Navigator.of(context).pop(true),
              child: Text(l10n.home),
            ),
          ],
        ),
      ),
    );
  }
}

/// Transfer instructions + bank details + amount row.
class _BankDetailsCard extends StatelessWidget {
  const _BankDetailsCard({
    required this.l10n,
    required this.scheme,
    required this.club,
    required this.clubLoaded,
    required this.amount,
  });

  final AppLocalizations l10n;
  final ColorScheme scheme;
  final ClubInfo? club;
  final bool clubLoaded;
  final double amount;

  @override
  Widget build(BuildContext context) {
    final c = club;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.transferInstructions,
                style: Theme.of(context).textTheme.titleMedium),
            const Divider(height: AppSpacing.lg),
            if (!clubLoaded)
              const Center(
                child: Padding(
                  padding: EdgeInsets.all(AppSpacing.md),
                  child: CircularProgressIndicator(),
                ),
              )
            else if (c == null || !c.hasBank)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
                child: Text(
                  l10n.error,
                  style: TextStyle(color: scheme.onSurface),
                ),
              )
            else ...[
              if (c.bankName.isNotEmpty)
                _bankRow(context, l10n.bankName, c.bankName),
              if (c.bankAccountNumber.isNotEmpty)
                _bankRow(context, l10n.accountNumber, c.bankAccountNumber),
              if (c.bankAccountHolder.isNotEmpty)
                _bankRow(context, l10n.accountHolder, c.bankAccountHolder),
              if (c.bankAccountCode.isNotEmpty)
                _bankRow(context, l10n.beneficiaryCode, c.bankAccountCode),
              if (c.bankExtra.isNotEmpty)
                _bankRow(context, l10n.extraInfo, c.bankExtra),
            ],
            const Divider(height: AppSpacing.lg),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(l10n.transferAmount,
                    style: Theme.of(context).textTheme.bodyMedium),
                Text(
                  '\$$amount',
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
    );
  }

  Widget _bankRow(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodyMedium),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.end,
              style: Theme.of(context)
                  .textTheme
                  .bodyMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}

/// Proof image preview + camera/gallery pickers + upload button.
class _ProofPicker extends StatelessWidget {
  const _ProofPicker({
    required this.l10n,
    required this.scheme,
    required this.image,
    required this.uploading,
    required this.error,
    required this.onPickCamera,
    required this.onPickGallery,
    required this.onUpload,
  });

  final AppLocalizations l10n;
  final ColorScheme scheme;
  final File? image;
  final bool uploading;
  final String? error;
  final VoidCallback onPickCamera;
  final VoidCallback onPickGallery;
  final VoidCallback onUpload;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(l10n.uploadProof, style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: AppSpacing.xs),
        Text(l10n.maxFileSize, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: AppSpacing.md),
        if (image != null) ...[
          ClipRRect(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
            child: Image.file(
              image!,
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
                onPressed: uploading ? null : onPickCamera,
                icon: const Icon(Icons.camera_alt_outlined),
                label: Text(l10n.camera),
              ),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: uploading ? null : onPickGallery,
                icon: const Icon(Icons.photo_library_outlined),
                label: Text(l10n.gallery),
              ),
            ),
          ],
        ),
        if (error != null) ...[
          const SizedBox(height: AppSpacing.sm),
          Text(error!, style: TextStyle(color: scheme.error)),
        ],
        const SizedBox(height: AppSpacing.lg),
        FilledButton(
          onPressed: (image != null && !uploading) ? onUpload : null,
          child: uploading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                      strokeWidth: BookDim.progressStroke),
                )
              : Text(l10n.send),
        ),
      ],
    );
  }
}
