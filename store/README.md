# Store publishing kit — Andes Padel

Everything needed to publish on **Google Play** and **Apple App Store**.
Generated 2026-09-23.

## What's ready (drop-in)

| Asset | File | Spec |
|---|---|---|
| Play app icon | `google-play/images/app-icon-512.png` | 512×512 PNG |
| Play feature graphic | `google-play/images/feature-graphic-1024x500.png` | 1024×500 PNG |
| Apple app icon | `apple-app-store/images/app-icon-1024.png` | 1024×1024 PNG |
| Play listing EN | `google-play/listing/en-US/` | title, short + full description |
| Play listing ES | `google-play/listing/es-419/` | title, short + full description |
| Apple metadata EN | `apple-app-store/metadata/en-US/` | name, subtitle, description, keywords, release notes, URLs |
| Apple metadata ES | `apple-app-store/metadata/es-ES/` | same fields |
| App Privacy answers | `apple-app-store/metadata/app_privacy.txt` | Apple questionnaire |
| Data safety answers | `google-play/data-safety.txt` | Play questionnaire |
| Release AAB (signed) | `mobile/build/app/outputs/bundle/release/app-release.aab` | 55.5 MB, release keystore |
| Release IPA (TestFlight) | `mobile/build/ios/ipa/padel_app.ipa` | 22.9 MB, v1.0.0 (5) |

## Screenshots

Coming from `store/*/images/screenshots/` (captured on iPhone 17 Pro / Pro Max simulators).
Apple requires **6.9"** and **6.5"** (or 6.7"/6.5") sets. Play wants **phone** screenshots (min 2, max 8) at 16:9 or 9:16.

## ONLY YOU can do (account-owner actions)

Apple and Google legally require the account holder — no tool can do these:

1. **Paid agreements** — Apple Developer Program ($99/yr) and Google Play Console ($25 once) must be **paid and active**.
2. **Banking / tax info** — App Store Connect → Business and Paying; Play Console → Payments.
3. **Content rating questionnaire** — legal answers; I drafted the privacy/data ones above.
4. **Privacy policy URL must be live.** Draft lives at `landing/privacy.html` — publish it to `https://<new-domain>/privacy`.
5. **App Privacy / Data safety** — paste the answers above into the web forms (one-time click-through).
6. **Age rating** — pick "4+" / "Everyone" (sports, no gambling/UGC risk).
7. **First release** — Google requires a **closed test** with ~12 testers for 14 days before full production (new personal dev accounts). If the account is an **organization** account, you can go straight to production.

## Signing credentials — BACK THESE UP NOW

| File | Location | Notes |
|---|---|---|
| Android upload keystore | `mobile/android/upload-keystore.jks` | **gitignored** |
| Keystore passwords | `~/.android-upload-ks.pass` (and `~/.android-upload-key.pass`) | mode 600, outside repo |
| Gradle signing props | `mobile/android/key.properties` | **gitignored** |
| Apple Distribution cert | login keychain + `distribution.cer` | team 29NGPXM563 |
| Apple provisioning | `mobile/ios/Runner/ANDESPADELJOAQUIN.mobileprovision` | valid to 2027-08-28 |

**If you lose the Android keystore or its password, you can never update this app on Play.** Copy `upload-keystore.jks` + the password file to a password manager / external drive today.

## Repeatable build commands

```bash
# iOS → TestFlight (bumps build number, builds, uploads)
ASC_USER='info@loyallia.com' ASC_PASSWORD='xxxx-xxxx-xxxx-xxxx' make ship-ios

# Android → Play-ready AAB (already signed with release keystore)
cd mobile && flutter build appbundle --release
# output: mobile/build/app/outputs/bundle/release/app-release.aab
```
