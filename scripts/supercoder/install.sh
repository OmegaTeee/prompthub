bash -lc 'set -euo pipefail

REPO="huytd/supercoder"
BASE_DIR="$HOME/.local/supercoder"
BIN_DIR="$HOME/.local/bin"
CURRENT_LINK="$BASE_DIR/current"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$BASE_DIR" "$BIN_DIR"

ASSET_URL="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assets = data.get(\"assets\", [])
cands = []

for a in assets:
    name = a.get(\"name\", \"\").lower()
    url = a.get(\"browser_download_url\", \"\")
    if (
        name.endswith(\".zip\")
        and any(k in name for k in [\"mac\", \"darwin\", \"osx\"])
        and any(k in name for k in [\"arm64\", \"aarch64\"])
    ):
        cands.append(url)

if not cands:
    for a in assets:
        name = a.get(\"name\", \"\").lower()
        url = a.get(\"browser_download_url\", \"\")
        if name.endswith(\".zip\") and any(k in name for k in [\"mac\", \"darwin\", \"osx\"]):
            cands.append(url)

if not cands:
    for a in assets:
        name = a.get(\"name\", \"\").lower()
        url = a.get(\"browser_download_url\", \"\")
        if name.endswith(\".zip\"):
            cands.append(url)

print(cands[0] if cands else \"\")
")"

[ -n "$ASSET_URL" ] || {
  echo "Could not find a ZIP asset for the latest release."
  exit 1
}

ZIP_PATH="$TMP_DIR/supercoder.zip"
EXTRACT_DIR="$TMP_DIR/extracted"

mkdir -p "$EXTRACT_DIR"
curl -fL "$ASSET_URL" -o "$ZIP_PATH"
unzip -q "$ZIP_PATH" -d "$EXTRACT_DIR"

FOUND_BIN="$(find "$EXTRACT_DIR" -type f -path "*/bin/supercoder" | head -n 1)"
[ -n "$FOUND_BIN" ] || {
  echo "Install completed, but supercoder binary was not found in the archive."
  exit 1
}

FOUND_ROOT="$(cd "$(dirname "$FOUND_BIN")/.." && pwd)"
VERSION_NAME="$(basename "$FOUND_ROOT")"
TARGET_DIR="$BASE_DIR/$VERSION_NAME"

rm -rf "$TARGET_DIR"
mkdir -p "$BASE_DIR"
cp -R "$FOUND_ROOT" "$TARGET_DIR"

chmod +x "$TARGET_DIR/bin/supercoder"
ln -sfn "$TARGET_DIR" "$CURRENT_LINK"
ln -sfn "$CURRENT_LINK/bin/supercoder" "$BIN_DIR/supercoder"

grep -qs '\''export PATH="$HOME/.local/bin:$PATH"'\'' "$HOME/.zshrc" || \
  echo '\''export PATH="$HOME/.local/bin:$PATH"'\'' >> "$HOME/.zshrc"

echo
echo "Installed SuperCoder to: $TARGET_DIR"
echo "Stable link: $CURRENT_LINK"
echo "Command link: $BIN_DIR/supercoder"
echo
echo "Next steps:"
echo "  source ~/.zshrc"
echo "  supercoder"
'
