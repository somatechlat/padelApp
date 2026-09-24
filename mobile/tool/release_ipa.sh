#!/usr/bin/env bash
# One-command iOS release: bump build number -> build IPA -> upload to TestFlight.
#
# Usage:
#   ASC_USER='info@loyallia.com' ASC_PASSWORD='xxxx-xxxx-xxxx-xxxx' ./tool/release_ipa.sh
#
# Second and later runs are FAST: SwiftPM packages are cached under
# ~/Library/Caches/org.swift.swiftpm/ (the first run pays the download cost once).
set -euo pipefail

cd "$(dirname "$0")/.."   # -> mobile/

: "${ASC_USER:?Set ASC_USER (Apple ID, e.g. info@loyallia.com)}"
: "${ASC_PASSWORD:?Set ASC_PASSWORD (app-specific password from appleid.apple.com)}"

PUBSPEC=pubspec.yaml

# --- bump build number so App Store Connect always accepts the upload ---
current=$(grep -E '^version:' "$PUBSPEC" | sed -E 's/^version: *([0-9.]+)\+([0-9]+)/\1 \2/')
name=$(echo "$current" | cut -d' ' -f1)
build=$(echo "$current" | cut -d' ' -f2)
next=$((build + 1))
sed -i '' -E "s/^version: .*/version: ${name}+${next}/" "$PUBSPEC"
echo "==> Version ${name} (build ${next})"

FLUTTER="${FLUTTER:-/usr/local/bin/flutter}"

echo "==> flutter pub get"
"$FLUTTER" pub get

echo "==> flutter build ipa --release (SPM packages cached from first run)"
# Never let a stale IPA from a previous run get uploaded: remove it first.
rm -f build/ios/ipa/padel_app.ipa
"$FLUTTER" build ipa --release --export-options-plist ios/ExportOptions.plist

IPA=build/ios/ipa/padel_app.ipa
test -f "$IPA" || { echo "ERROR: $IPA was not produced (export failed). Not uploading."; exit 1; }

echo "==> Uploading $IPA to TestFlight as ${ASC_USER}"
xcrun altool --upload-app --type ios -f "$IPA" -u "$ASC_USER" -p "$ASC_PASSWORD"

echo ""
echo "==> DONE. Build ${next} is uploading. It appears in App Store Connect > TestFlight after Apple processes it (~5-15 min)."
