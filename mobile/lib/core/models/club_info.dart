/// Club settings loaded from `GET /api/club/`.
///
/// All contact, bank, and home title values come from the API — never
/// hardcode them in Dart. Empty strings mean "hide this field in the UI".
class ClubInfo {
  const ClubInfo({
    this.name = '',
    this.address = '',
    this.mapsUrl = '',
    this.mapsQuery = '',
    this.phone = '',
    this.email = '',
    this.whatsappNumber = '',
    this.whatsappMessage = '',
    this.instagramUrl = '',
    this.homeSectionTitle = '',
    this.homeGreetingTagline = '',
    this.logoUrl = '',
    this.bankName = '',
    this.bankAccountNumber = '',
    this.bankAccountHolder = '',
    this.bankAccountCode = '',
    this.bankExtra = '',
  });

  final String name;
  final String address;
  final String mapsUrl;
  final String mapsQuery;
  final String phone;
  final String email;
  final String whatsappNumber;
  final String whatsappMessage;
  final String instagramUrl;
  final String homeSectionTitle;
  final String homeGreetingTagline;
  final String logoUrl;
  final String bankName;
  final String bankAccountNumber;
  final String bankAccountHolder;
  final String bankAccountCode;
  final String bankExtra;

  factory ClubInfo.fromJson(Map<String, dynamic> json) {
    String s(String key) {
      final v = json[key];
      return v is String ? v.trim() : '';
    }

    return ClubInfo(
      name: s('name'),
      address: s('address'),
      mapsUrl: s('maps_url'),
      mapsQuery: s('maps_query'),
      phone: s('phone'),
      email: s('email'),
      whatsappNumber: s('whatsapp_number'),
      whatsappMessage: s('whatsapp_message'),
      instagramUrl: s('instagram_url'),
      homeSectionTitle: s('home_section_title'),
      homeGreetingTagline: s('home_greeting_tagline'),
      logoUrl: s('logo_url'),
      bankName: s('bank_name'),
      bankAccountNumber: s('bank_account_number'),
      bankAccountHolder: s('bank_account_holder'),
      bankAccountCode: s('bank_account_code'),
      bankExtra: s('bank_extra'),
    );
  }

  bool get hasContact =>
      address.isNotEmpty ||
      phone.isNotEmpty ||
      email.isNotEmpty ||
      instagramUrl.isNotEmpty ||
      whatsappNumber.isNotEmpty;

  bool get hasBank =>
      bankName.isNotEmpty ||
      bankAccountNumber.isNotEmpty ||
      bankAccountHolder.isNotEmpty ||
      bankAccountCode.isNotEmpty ||
      bankExtra.isNotEmpty;

  /// Absolute URL to open in a maps app/browser. Empty when no location.
  String get resolvedMapsUrl {
    if (mapsUrl.isNotEmpty) return mapsUrl;
    final query = mapsQuery.isNotEmpty ? mapsQuery : address;
    if (query.isEmpty) return '';
    return 'https://www.google.com/maps/search/?api=1&query=${Uri.encodeComponent(query)}';
  }

  /// `https://wa.me/...` deep link. Empty when no WhatsApp number.
  String get resolvedWhatsappUrl {
    final digits = whatsappNumber.replaceAll(RegExp(r'[^0-9]'), '');
    if (digits.isEmpty) return '';
    final base = 'https://wa.me/$digits';
    if (whatsappMessage.isNotEmpty) {
      return '$base?text=${Uri.encodeComponent(whatsappMessage)}';
    }
    return base;
  }

  String get resolvedInstagramUrl {
    if (instagramUrl.isEmpty) return '';
    if (instagramUrl.startsWith('http://') || instagramUrl.startsWith('https://')) {
      return instagramUrl;
    }
    final handle = instagramUrl.replaceFirst(RegExp(r'^@'), '');
    return 'https://instagram.com/$handle';
  }
}
