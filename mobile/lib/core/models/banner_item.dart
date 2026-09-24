/// Promo/event banner from `GET /api/banners/?lang=<code>`.
class BannerItem {
  const BannerItem({
    this.id,
    this.title = '',
    this.subtitle = '',
    required this.image,
    this.linkUrl = '',
    this.linkType = '',
    this.sortOrder = 0,
  });

  final int? id;
  final String title;
  final String subtitle;

  /// Absolute image URL.
  final String image;
  final String linkUrl;
  final String linkType;
  final int sortOrder;

  factory BannerItem.fromJson(Map<String, dynamic> json) {
    String s(String key) {
      final v = json[key];
      return v is String ? v.trim() : '';
    }

    int i(String key) {
      final v = json[key];
      if (v is int) return v;
      if (v is String) return int.tryParse(v) ?? 0;
      return 0;
    }

    return BannerItem(
      id: json['id'] is int ? json['id'] as int : null,
      title: s('title'),
      subtitle: s('subtitle'),
      image: s('image'),
      linkUrl: s('link_url'),
      linkType: s('link_type'),
      sortOrder: i('sort_order'),
    );
  }

  bool get hasLink => linkUrl.isNotEmpty;

  static List<BannerItem> listFrom(dynamic data) {
    final raw = data is Map ? data['results'] : data;
    if (raw is! List) return const [];
    final items = <BannerItem>[];
    for (final entry in raw) {
      if (entry is Map<String, dynamic>) {
        final item = BannerItem.fromJson(entry);
        if (item.image.isNotEmpty) items.add(item);
      } else if (entry is Map) {
        final item = BannerItem.fromJson(Map<String, dynamic>.from(entry));
        if (item.image.isNotEmpty) items.add(item);
      }
    }
    items.sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
    return items;
  }
}
