# Build & Deploy — Andes Pádel

**Last updated:** 2026-08-26  
**Covers:** Android APK (Docker + local), iOS build (macOS + Xcode)

---

## Prerequisites

### Android (Docker — recommended)

| Requirement | Version | Check |
|-------------|---------|-------|
| Docker Desktop | Latest | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |
| Git | Any | `git --version` |

That's it. Flutter, Dart, Gradle, and Android SDK run inside the Docker container.

### Android (Local build — no Docker)

| Requirement | Version | Install |
|-------------|---------|---------|
| Flutter SDK | 3.27.3 | `brew install flutter` or download from flutter.dev |
| Java (OpenJDK) | 21 | `brew install openjdk@21` |
| Android SDK | API 35 | `flutter doctor` will guide setup |

### iOS (macOS only)

| Requirement | Version | Install |
|-------------|---------|---------|
| Xcode | 15+ | Mac App Store |
| CocoaPods | 1.15+ | `sudo gem install cocoapods` |
| Apple Developer account | — | developer.apple.com ($99/yr) |
| Flutter SDK | 3.27.3 | Same as Android |

---

## 1. Configure API Server

The API base URL is configured in a single file:

**File:** `mobile/lib/core/api_client.dart` (line 17)

```dart
_dio.options.baseUrl = baseUrl ??
    const String.fromEnvironment('API_BASE_URL',
        defaultValue: 'https://andespadel.yachaq.io/api');
```

### Current production URL

```
https://andespadel.yachaq.io/api
```

### Override at build time (without changing code)

```bash
--dart-define=API_BASE_URL=https://your-server.com/api
```

This override works with both `flutter build apk` and `flutter build ios`.

---

## 2. Build APK (Docker — Recommended)

### Quick build

```bash
cd padelApp
make flapk
```

This runs:
1. `flutter build apk --debug` inside the Flutter Docker container
2. Copies the APK to `./padelapp-debug.apk`

### Step by step

```bash
# 1. Start the Flutter container (background not needed for build)
docker compose run --rm flutter sh

# 2. Inside the container, get dependencies
flutter pub get

# 3. Build the debug APK
flutter build apk --debug

# 4. Exit container (APK is in the mounted volume)
exit
```

The APK output is at:
```
mobile/build/app/outputs/flutter-apk/app-debug.apk
```

### Makefile commands

| Command | What it does |
|---------|-------------|
| `make flcheck` | Run Flutter static analysis |
| `make fltest` | Run Flutter unit tests |
| `make flbuild` | Build debug APK in Docker |
| `make flapk` | Build APK + copy to project root |

---

## 3. Build APK (Local — No Docker)

For machines with Flutter installed locally:

```bash
cd padelApp/mobile

# 1. Get dependencies
flutter pub get

# 2. Run static analysis (optional but recommended)
flutter analyze

# 3. Run tests (optional but recommended)
flutter test

# 4. Build debug APK
flutter build apk --debug

# 5. Build release APK (requires signing config)
flutter build apk --release
```

### Output locations

| Build type | Output path |
|------------|-------------|
| Debug | `mobile/build/app/outputs/flutter-apk/app-debug.apk` |
| Release | `mobile/build/app/outputs/flutter-apk/app-release.apk` |

### Build with custom server URL

```bash
flutter build apk --debug --dart-define=API_BASE_URL=https://other-server.com/api
```

---

## 4. Install APK on Phone

### Option 1: ADB (USB)

```bash
# Connect phone via USB with USB debugging enabled
adb install ./padelapp-debug.apk
```

### Option 2: ADB (Wireless)

```bash
# Phone and computer on same WiFi
adb connect <phone-ip>:5555
adb install ./padelapp-debug.apk
```

### Option 3: Manual

1. Copy `padelapp-debug.apk` to phone (USB, email, Google Drive, AirDrop)
2. On phone: Open file manager → tap the APK → Install
3. Enable "Install from unknown sources" if prompted

---

## 5. Build iOS

> **Requires:** macOS with Xcode installed, CocoaPods, Apple Developer account (for signed builds)

### 5.1 Setup

```bash
# Verify Xcode
xcodebuild -version

# Install CocoaPods (if not installed)
sudo gem install cocoapods

# Point xcode-select to Xcode (not CommandLineTools)
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer

# Verify Flutter sees Xcode
flutter doctor
```

### 5.2 Build (debug — no signing)

```bash
cd padelApp/mobile

# 1. Get dependencies
flutter pub get

# 2. Install iOS pods
cd ios
pod install
cd ..

# 3. Build iOS (debug, no codesign)
flutter build ios --debug --no-codesign
```

### 5.3 Build (release — requires signing)

```bash
# Build release (Xcode handles signing)
flutter build ios --release
```

### 5.4 Export IPA for client delivery

**Option A: From Xcode**

1. Open `mobile/ios/Runner.xcworkspace` in Xcode
2. Select the Runner target → Signing & Capabilities
3. Set your Team and Bundle Identifier (`com.andes.padel.padel_app`)
4. Product → Archive → Distribute App → Ad Hoc or Development

**Option B: Command line**

```bash
flutter build ipa --release
```

Output at: `mobile/build/ios/ipa/`

### 5.5 Install on physical iPhone

| Method | Requirements |
|--------|-------------|
| Xcode | USB cable, Apple Developer account |
| TestFlight | Apple Developer account, upload to App Store Connect |
| `ios-deploy` | `npm install -g ios-deploy`, USB cable |

### iOS signing checklist

- [ ] Apple Developer account active
- [ ] Bundle ID registered: `com.andes.padel.padel_app`
- [ ] Provisioning profile created for the bundle ID
- [ ] Xcode project signed with correct team
- [ ] `ios/Podfile` generated and `pod install` run

---

## 6. Server Configuration

### Production server

| Setting | Value |
|---------|-------|
| Host | `140.82.155.48` (LOYALLIA) |
| Domain | `andespadel.yachaq.io` |
| API URL | `https://andespadel.yachaq.io/api` |
| SSL | Handled by host nginx (port 443) |
| Django port | 8000 (internal), proxied via nginx |

### Port mapping (Docker)

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| PostgreSQL | 34000 | 5432 |
| Redis | 34001 | 6379 |
| Backend | 34002 | 8000 |
| Nginx | 34003 | 80 |

### Django settings chain

```
padel/settings/base.py   → shared config, imports secrets
padel/settings/dev.py    → DEBUG=True, localhost
padel/settings/prod.py   → DEBUG=False, andespadel.yachaq.io, SSL
```

---

## 7. Troubleshooting

### Gradle zip corruption (Docker)

**Symptom:** `java.util.zip.ZipException: zip END header not found`

```bash
# Clean the gradle cache volume
docker volume rm padelapp_gradle_home

# Rebuild
make flapk
```

### "Matrix4 isn't a type" (Docker)

**Symptom:** Hundreds of Flutter SDK internal compile errors

**Cause:** Corrupted Flutter SDK cache in Docker volumes

```bash
# Clean all Flutter-related volumes
docker volume rm padelapp_flutter_home padelapp_gradle_home padelapp_android_sdk

# Rebuild
make flapk
```

### APK won't install on phone

- Enable "Install from unknown sources" in Android settings
- Check Android version (min SDK 24)
- Clear old install first: `adb shell pm clear com.andes.padel.padel_app`

### Can't connect to backend from phone

- Ensure phone is on same network as the server
- Test in phone browser: `https://andespadel.yachaq.io/api/auth/me/`
- Should see: `{"detail":"Las credenciales de autenticación no se proveyeron."}`

### iOS: "pod install" fails

```bash
cd ios
pod deintegrate
pod install --verbose
```

### iOS: Xcode signing errors

1. Open `Runner.xcworkspace` in Xcode
2. Select Runner target → Signing & Capabilities
3. Select your Team (personal or organization)
4. If no team: add Apple Developer account in Xcode → Settings → Accounts

---

## Quick Reference

### Build commands

| Target | Command |
|--------|---------|
| Android APK (Docker) | `make flapk` |
| Android APK (local) | `cd mobile && flutter build apk --debug` |
| Android APK (custom URL) | `flutter build apk --debug --dart-define=API_BASE_URL=https://...` |
| iOS debug | `cd mobile && flutter build ios --debug --no-codesign` |
| iOS release | `cd mobile && flutter build ios --release` |
| iOS IPA | `cd mobile && flutter build ipa --release` |
| Flutter analyze | `make flcheck` or `flutter analyze` |
| Flutter tests | `make fltest` or `flutter test` |

### Install commands

| Target | Command |
|--------|---------|
| Android (ADB) | `adb install ./padelapp-debug.apk` |
| Android (wireless) | `adb connect <ip>:5555 && adb install ./padelapp-debug.apk` |
| iOS (Xcode) | Open `.xcworkspace` → Run on device |
| iOS (TestFlight) | Upload IPA to App Store Connect → invite testers |

### Useful Docker commands

| Command | Purpose |
|---------|---------|
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Follow service logs |
| `make build` | Rebuild Docker images |
| `make migrate` | Run database migrations |
| `make seeddemo` | Load demo data |
| `make shell` | Django management shell |
| `make psql` | PostgreSQL shell |
| `make test` | Run backend tests |
| `make lint` | Lint backend code |

---

**Last APK built:** `./padelapp-debug.apk` (86 MB, 2026-08-26)  
**Production server:** https://andespadel.yachaq.io
