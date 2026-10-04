# Store publishing kit — Andes Padel

Everything needed to publish on **Google Play** and **Apple App Store**.
Generated 2026-09-23; screenshots and metadata updated 2026-10-04.

## Status

| Store | Status |
|---|---|
| **Apple App Store** | Build 8 **submitted for review** (2026-10-04). Age rating 4+, category Sports, price Free, `es-MX` + `en-US` listings, all screenshot sets filled. |
| **Google Play** | AAB built and signed. **Not uploaded** — needs the three Play Console forms (below). |

See `AGENTS.md` §10b for the full release record.

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
| Release AAB (signed) | `mobile/build/app/outputs/bundle/release/app-release.aab` | 56.6 MB, release keystore, alias `upload` |
| Release IPA | built by `make ship-ios` | v1.0.0 (build 8), uploaded to TestFlight |

## Screenshots — DONE

All sets captured and committed under `store/*/images/screenshots/`:

| Set | Size | Files | Captured on |
|---|---|---|---|
| `apple-app-store/images/screenshots/iPhone_6.9/` | 1320×2868 | 7 | iPhone 17 Pro Max sim |
| `apple-app-store/images/screenshots/iPhone_6.5/` | 1242×2688 | 7 | downscaled from 6.9" |
| `apple-app-store/images/screenshots/iPad_13/` | 2064×2752 | 5 | iPad Pro 13-inch (M5) sim |
| `google-play/images/screenshots/phone/` | 1320×2347 (9:16) | 7 | cropped from 6.9" |

Screens, in order: login, register, home, bookings, events, notifications,
profile. Apple requires the iPad set because the app is universal
(`TARGETED_DEVICE_FAMILY = "1,2"`).

Reproduce with `mobile/integration_test/capture_store_test.dart` — see
`AGENTS.md` §5 for the exact `flutter drive` invocation.

## ONLY YOU can do (account-owner actions)

Apple and Google legally require the account holder — no tool can do these:

1. **Paid agreements** — Apple Developer Program ($99/yr) and Google Play Console ($25 once) must be **paid and active**.
2. **Banking / tax info** — App Store Connect → Business and Paying; Play Console → Payments.
3. **Content rating questionnaire** — legal answers; I drafted the privacy/data ones above.
4. **Privacy policy URL must be live.** Served from `landing/privacy.html` at
   `https://app.andespadelclub.com/privacy` — verified answering. Note the
   apex/`www` of `andespadelclub.com` is a different machine that does not
   serve `/privacy`; every URL in this kit therefore uses the `app.` subdomain.
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

Both release paths **must** pass `API_BASE_URL`. A release binary without it
falls back to `http://127.0.0.1:28002/api`, which on a device is the phone
itself — the app installs and then cannot reach any API. The Dart side now
throws at startup in release mode rather than shipping that, so a missing define
is a loud build failure instead of a silent dead app.

```bash
# iOS → TestFlight (bumps build number, builds, uploads)
# API_BASE_URL defaults to https://app.andespadelclub.com/api inside the script.
ASC_USER='info@loyallia.com' ASC_PASSWORD='xxxx-xxxx-xxxx-xxxx' make ship-ios

# Android → Play-ready AAB (already signed with release keystore)
make ship-android
# equivalently:
cd mobile && flutter build appbundle --release \
  --dart-define=API_BASE_URL=https://app.andespadelclub.com/api
# output: mobile/build/app/outputs/bundle/release/app-release.aab
```

`make ship-android` fails if `mobile/android/key.properties` is absent, rather
than silently signing with the debug key. A debug-signed bundle uploads once and
can never be replaced afterwards, so losing the upload key ends the listing.
