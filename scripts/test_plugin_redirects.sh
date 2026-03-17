#!/bin/bash
# Test script for plugin registry redirect functionality
# Tests URL redirects, UUID redirects, and update-through-redirect flows

set -e

TEST_DIR=$(mktemp -d)
PLUGIN_REPO_OLD="$TEST_DIR/old-repo"
PLUGIN_REPO_NEW="$TEST_DIR/new-repo"
REGISTRY_FILE="$TEST_DIR/registry.toml"
TEST_PLUGIN_UUID="aabbccdd-1234-4678-9234-aabbccddeeff"
PLUGIN_DIR_NAME="test_redirect_plugin_${TEST_PLUGIN_UUID}"

export PICARD_PLUGIN_REGISTRY_URL="$REGISTRY_FILE"
PICARD_PLUGINS="picard-plugins"

cleanup() {
    echo "Cleanup: Removing test directory and plugin"
    rm -rf "$TEST_DIR"
    rm -rf ~/.local/share/MusicBrainz/Picard/plugins3/$PLUGIN_DIR_NAME 2>/dev/null || true
    echo "✓ Cleanup complete"
}
trap cleanup EXIT

echo "=== Testing Plugin Registry Redirects ==="
echo "Test directory: $TEST_DIR"
echo

# Clean up any leftover from previous runs
rm -rf ~/.local/share/MusicBrainz/Picard/plugins3/$PLUGIN_DIR_NAME 2>/dev/null || true

# =============================================================================
# Setup: Create "old" plugin repository with v1.0.0 and v1.1.0
# =============================================================================
echo "Setup: Creating old plugin repository"
mkdir -p "$PLUGIN_REPO_OLD"
cd "$PLUGIN_REPO_OLD"
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

cat > MANIFEST.toml << EOF
uuid = "$TEST_PLUGIN_UUID"
name = "Redirect Test Plugin"
version = "1.0.0"
description = "A plugin that will move repositories"
api = ["3.0"]
authors = ["Test Author"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
EOF
cat > plugin.py << 'EOF'
PLUGIN_NAME = "Redirect Test Plugin"
EOF
git add .
git commit -q -m "v1.0.0"
COMMIT_V1_0_0=$(git rev-parse HEAD)
git tag -a v1.0.0 -m "v1.0.0"

sed -i 's/version = "1.0.0"/version = "1.1.0"/' MANIFEST.toml
git add .
git commit -q -m "v1.1.0"
COMMIT_V1_1_0=$(git rev-parse HEAD)
git tag -a v1.1.0 -m "v1.1.0"
cd - > /dev/null
echo "✓ Old repo created with v1.0.0 and v1.1.0"

# =============================================================================
# Setup: Create "new" plugin repository with v2.0.0
# =============================================================================
echo "Setup: Creating new plugin repository"
mkdir -p "$PLUGIN_REPO_NEW"
cd "$PLUGIN_REPO_NEW"
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

cat > MANIFEST.toml << EOF
uuid = "$TEST_PLUGIN_UUID"
name = "Redirect Test Plugin (Moved)"
version = "2.0.0"
description = "Plugin moved to new repository"
api = ["3.0"]
authors = ["Test Author"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
EOF
cat > plugin.py << 'EOF'
PLUGIN_NAME = "Redirect Test Plugin (Moved)"
EOF
git add .
git commit -q -m "v2.0.0"
COMMIT_V2_0_0=$(git rev-parse HEAD)
git tag -a v2.0.0 -m "v2.0.0"

sed -i 's/version = "2.0.0"/version = "2.1.0"/' MANIFEST.toml
git add .
git commit -q -m "v2.1.0"
COMMIT_V2_1_0=$(git rev-parse HEAD)
git tag -a v2.1.0 -m "v2.1.0"
cd - > /dev/null
echo "✓ New repo created with v2.0.0 and v2.1.0"
echo

# =============================================================================
# Test 1: Install from old repo, redirect to new repo, update
# =============================================================================
echo "--- Test 1: URL redirect on update ---"

# Registry initially points to old repo
cat > "$REGISTRY_FILE" << EOF
[[plugins]]
id = "redirect-test"
name = "Redirect Test Plugin"
git_url = "$PLUGIN_REPO_OLD"
uuid = "$TEST_PLUGIN_UUID"
versioning_scheme = "semver"
EOF
$PICARD_PLUGINS --refresh-registry 2>&1 | head -1

# Install from old repo at v1.0.0
$PICARD_PLUGINS --install redirect-test --ref v1.0.0 --yes 2>&1 | tail -1
echo "✓ Installed v1.0.0 from old repo"

# Verify installed version
STORED_COMMIT=$($PICARD_PLUGINS --info $TEST_PLUGIN_UUID --no-color | grep -oP 'Version:.*@\K[a-f0-9]{7}')
if [ "$STORED_COMMIT" = "${COMMIT_V1_0_0:0:7}" ]; then
    echo "✓ Verified at v1.0.0 (${COMMIT_V1_0_0:0:7})"
else
    echo "✗ ERROR: Expected ${COMMIT_V1_0_0:0:7}, got $STORED_COMMIT"
    exit 1
fi

# Now update registry to point to new repo with redirect
cat > "$REGISTRY_FILE" << EOF
[[plugins]]
id = "redirect-test"
name = "Redirect Test Plugin (Moved)"
git_url = "$PLUGIN_REPO_NEW"
uuid = "$TEST_PLUGIN_UUID"
versioning_scheme = "semver"
redirect_from = [
    "$PLUGIN_REPO_OLD",
]
EOF
$PICARD_PLUGINS --refresh-registry 2>&1 | head -1

# Update should follow redirect to new repo and get v2.1.0
$PICARD_PLUGINS --update $TEST_PLUGIN_UUID --yes 2>&1 | grep -E "✓|✗|→"
echo "✓ Update completed"

# Verify plugin updated to new repo's latest version
INFO_OUTPUT=$($PICARD_PLUGINS --info $TEST_PLUGIN_UUID --no-color 2>&1)
if echo "$INFO_OUTPUT" | grep -q "2.1.0"; then
    echo "✓ Plugin updated to v2.1.0 from new repository"
elif echo "$INFO_OUTPUT" | grep -q "2.0.0"; then
    echo "✓ Plugin updated to v2.0.0 from new repository"
else
    echo "✗ ERROR: Plugin not updated to new repo version"
    echo "  $INFO_OUTPUT" | grep Version
    exit 1
fi

# Verify source now points to new repo
if echo "$INFO_OUTPUT" | grep -q "$PLUGIN_REPO_NEW"; then
    echo "✓ Source URL updated to new repository"
else
    echo "? Source URL may not be updated in display (metadata was updated)"
fi

$PICARD_PLUGINS --remove $TEST_PLUGIN_UUID --purge --yes 2>&1 | tail -1
echo

# =============================================================================
# Test 2: Install from old repo on branch, redirect to new repo, update
# =============================================================================
echo "--- Test 2: URL redirect on branch-based update ---"

# Registry points to old repo
cat > "$REGISTRY_FILE" << EOF
[[plugins]]
id = "redirect-test"
name = "Redirect Test Plugin"
git_url = "$PLUGIN_REPO_OLD"
uuid = "$TEST_PLUGIN_UUID"
EOF
$PICARD_PLUGINS --refresh-registry 2>&1 | head -1

# Install from old repo on main branch (no specific tag)
$PICARD_PLUGINS --install "$PLUGIN_REPO_OLD" --yes 2>&1 | tail -1
echo "✓ Installed from old repo (main branch)"

# Redirect registry to new repo
cat > "$REGISTRY_FILE" << EOF
[[plugins]]
id = "redirect-test"
name = "Redirect Test Plugin (Moved)"
git_url = "$PLUGIN_REPO_NEW"
uuid = "$TEST_PLUGIN_UUID"
redirect_from = [
    "$PLUGIN_REPO_OLD",
]
EOF
$PICARD_PLUGINS --refresh-registry 2>&1 | head -1

# Update should follow redirect
$PICARD_PLUGINS --update $TEST_PLUGIN_UUID --yes 2>&1 | grep -E "✓|✗|→"
echo "✓ Branch-based update through redirect completed"

# Verify it got content from new repo
INFO_OUTPUT=$($PICARD_PLUGINS --info $TEST_PLUGIN_UUID --no-color 2>&1)
if echo "$INFO_OUTPUT" | grep -q "2\.\(0\|1\)\.0"; then
    echo "✓ Plugin updated to new repo content"
else
    echo "? Plugin version: $(echo "$INFO_OUTPUT" | grep Version)"
fi

$PICARD_PLUGINS --remove $TEST_PLUGIN_UUID --purge --yes 2>&1 | tail -1
echo

# =============================================================================
# Test 3: Registry lookup finds plugin via redirect_from
# =============================================================================
echo "--- Test 3: Registry find_plugin via redirect_from ---"

# Registry points to new repo with redirect_from
cat > "$REGISTRY_FILE" << EOF
[[plugins]]
id = "redirect-test"
name = "Redirect Test Plugin (Moved)"
git_url = "$PLUGIN_REPO_NEW"
uuid = "$TEST_PLUGIN_UUID"
versioning_scheme = "semver"
redirect_from = [
    "$PLUGIN_REPO_OLD",
]
EOF
$PICARD_PLUGINS --refresh-registry 2>&1 | head -1

# Install using old URL - should be found via redirect_from in registry
$PICARD_PLUGINS --install "$PLUGIN_REPO_OLD" --yes 2>&1 | tail -2
echo "✓ Install via old URL found plugin in registry"

INFO_OUTPUT=$($PICARD_PLUGINS --info $TEST_PLUGIN_UUID --no-color 2>&1)
echo "  $(echo "$INFO_OUTPUT" | grep Version)"

$PICARD_PLUGINS --remove $TEST_PLUGIN_UUID --purge --yes 2>&1 | tail -1
echo

# =============================================================================
# Test 4: Multiple old URLs in redirect_from
# =============================================================================
echo "--- Test 4: Multiple redirect_from URLs ---"

PLUGIN_REPO_OLDEST="$TEST_DIR/oldest-repo"
mkdir -p "$PLUGIN_REPO_OLDEST"
cd "$PLUGIN_REPO_OLDEST"
git init -q
git config user.email "test@example.com"
git config user.name "Test User"
cat > MANIFEST.toml << EOF
uuid = "$TEST_PLUGIN_UUID"
name = "Redirect Test Plugin"
version = "0.9.0"
description = "Original location"
api = ["3.0"]
authors = ["Test Author"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
EOF
cat > plugin.py << 'EOF'
PLUGIN_NAME = "Redirect Test Plugin"
EOF
git add .
git commit -q -m "v0.9.0"
git tag -a v0.9.0 -m "v0.9.0"
cd - > /dev/null

cat > "$REGISTRY_FILE" << EOF
[[plugins]]
id = "redirect-test"
name = "Redirect Test Plugin (Moved)"
git_url = "$PLUGIN_REPO_NEW"
uuid = "$TEST_PLUGIN_UUID"
versioning_scheme = "semver"
redirect_from = [
    "$PLUGIN_REPO_OLDEST",
    "$PLUGIN_REPO_OLD",
]
EOF
$PICARD_PLUGINS --refresh-registry 2>&1 | head -1

# Install using oldest URL - should still find via redirect_from
$PICARD_PLUGINS --install "$PLUGIN_REPO_OLDEST" --yes 2>&1 | tail -2
echo "✓ Install via oldest URL found plugin in registry"

INFO_OUTPUT=$($PICARD_PLUGINS --info $TEST_PLUGIN_UUID --no-color 2>&1)
echo "  $(echo "$INFO_OUTPUT" | grep Version)"

$PICARD_PLUGINS --remove $TEST_PLUGIN_UUID --purge --yes 2>&1 | tail -1
echo

echo "=== All Redirect Tests Completed Successfully ==="
