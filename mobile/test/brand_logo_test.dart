import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:padel_app/core/widgets/brand_logo.dart';

void main() {
  testWidgets('BrandLogo renders Image.asset of Andes logo without width',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: Center(child: BrandLogo(height: 48)),
        ),
      ),
    );
    await tester.pump();

    final image = tester.widget<Image>(find.byType(Image));
    expect(image.image, isA<AssetImage>());
    final asset = image.image as AssetImage;
    expect(asset.assetName, BrandLogo.assetPath);
    expect(asset.assetName, 'assets/images/LOGOTIPO-ANDES-PADEL.png');
    expect(image.fit, BoxFit.contain);
  });

  testWidgets('BrandLogo authHeight clamps between 96 and 180', (tester) async {
    double height = 0;
    await tester.pumpWidget(
      MaterialApp(
        home: Builder(
          builder: (context) {
            height = BrandLogo.authHeight(context);
            return const SizedBox.shrink();
          },
        ),
      ),
    );

    // Default test surface is 800x600 → 800 * 0.45 = 360, min(140, 360) = 140.
    expect(height, 140.0);

    // Narrow surface caps below 140 but stays >= 96.
    final narrow = MediaQuery(
      data: const MediaQueryData(size: Size(200, 400)),
      child: Builder(
        builder: (context) {
          height = BrandLogo.authHeight(context);
          return const SizedBox.shrink();
        },
      ),
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: narrow)));
    // 200 * 0.45 = 90 → clamped to 96.
    expect(height, 96.0);

    final wide = MediaQuery(
      data: const MediaQueryData(size: Size(400, 400)),
      child: Builder(
        builder: (context) {
          height = BrandLogo.authHeight(context);
          return const SizedBox.shrink();
        },
      ),
    );
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: wide)));
    // 400 * 0.45 = 180 → min(140, 180) = 140.
    expect(height, 140.0);
  });

  testWidgets('BrandLogo never sets both width and height on Image',
      (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: BrandLogo(height: 72),
        ),
      ),
    );
    await tester.pump();

    final image = tester.widget<Image>(find.byType(Image));
    // width must stay null so FittedBox preserves aspect ratio.
    expect(image.width, isNull);
    expect(image.height, 72);
  });
}
