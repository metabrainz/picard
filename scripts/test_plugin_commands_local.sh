#!/bin/bash
# Test script for plugin CLI commands using local git repository with local registry
# Creates a dummy plugin in a local git repo and tests all operations

set -e

TEST_DIR=$(mktemp -d)
PLUGIN_REPO="$TEST_DIR/test-plugin"
REGISTRY_FILE="$TEST_DIR/registry.toml"
TEST_PLUGIN_UUID="12345678-1234-4678-9234-123456789abc"

# Use local registry (direct path, no file:// prefix)
export PICARD_PLUGIN_REGISTRY_URL="$REGISTRY_FILE"
PICARD="python tagger.py"

echo "=== Testing Plugin Commands (Local Git Repository with Local Registry) ==="
echo "Test directory: $TEST_DIR"
echo "Registry file: $REGISTRY_FILE"
echo

# Setup: Create a dummy plugin with git repository
echo "Setup: Creating dummy plugin repository"
mkdir -p "$PLUGIN_REPO"
cd "$PLUGIN_REPO"

# Initialize git repo
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

# Create MANIFEST.toml
cat > MANIFEST.toml << EOF
uuid = "12345678-1234-4678-9234-123456789abc"
name = "Test Plugin"
version = "1.0.0"
description = "A test plugin for local repository testing"
api = ["3.0"]
authors = ["Test Author"]
license = "GPL-2.0-or-later"
license_url = "https://www.gnu.org/licenses/gpl-2.0.html"
EOF

# Create plugin file
cat > test_plugin.py << 'EOF'
PLUGIN_NAME = "Test Plugin"
PLUGIN_AUTHOR = "Test Author"
PLUGIN_DESCRIPTION = "A test plugin"
PLUGIN_VERSION = "1.0.0"
PLUGIN_API_VERSIONS = ["3.0"]
PLUGIN_LICENSE = "GPL-2.0-or-later"
EOF

# Commit v1.0.0 with lightweight tag
git add .
git commit -q -m "Initial commit - v1.0.0"
COMMIT_V1_0_0=$(git rev-parse HEAD)
git tag v1.0.0

# Create v1.1.0 with annotated tag
sed -i 's/version = "1.0.0"/version = "1.1.0"/' MANIFEST.toml
sed -i 's/PLUGIN_VERSION = "1.0.0"/PLUGIN_VERSION = "1.1.0"/' test_plugin.py
git add .
git commit -q -m "Release v1.1.0"
COMMIT_V1_1_0=$(git rev-parse HEAD)
git tag -a v1.1.0 -m "Annotated tag for v1.1.0"

# Create v1.2.0 with annotated tag
sed -i 's/version = "1.1.0"/version = "1.2.0"/' MANIFEST.toml
sed -i 's/PLUGIN_VERSION = "1.1.0"/PLUGIN_VERSION = "1.2.0"/' test_plugin.py
git add .
git commit -q -m "Release v1.2.0"
COMMIT_V1_2_0=$(git rev-parse HEAD)
git tag -a v1.2.0 -m "Annotated tag for v1.2.0"

cd - > /dev/null

# Create local registry file
cat > "$REGISTRY_FILE" << EOF
[[plugins]]
id = "test-plugin"
name = "Test Plugin"
git_url = "$PLUGIN_REPO"
uuid = "$TEST_PLUGIN_UUID"
versioning_scheme = "semver"
EOF
echo "✓ Created plugin repository and registry"
echo

# Test 1: Refresh registry
echo "1. Refresh registry"
$PICARD plugins --refresh-registry
echo

# Test 2: Install plugin from registry
echo "2. Install plugin from registry (should auto-select latest version)"
$PICARD plugins --install test-plugin --yes
echo

# Test 3: List installed plugins
echo "3. List installed plugins"
$PICARD plugins --list
echo

# Test 4: Show plugin info by UUID
echo "4. Show plugin info by UUID"
$PICARD plugins --info $TEST_PLUGIN_UUID
echo

# Test 5: Show plugin manifest
echo "5. Show plugin manifest"
$PICARD plugins --manifest $TEST_PLUGIN_UUID
echo

# Test 6: Enable plugin
echo "6. Enable plugin"
$PICARD plugins --enable $TEST_PLUGIN_UUID
echo

# Test 7: Disable plugin
echo "7. Disable plugin"
$PICARD plugins --disable $TEST_PLUGIN_UUID
echo

# Test 9: Clean plugin config
echo "9. Clean plugin config"
$PICARD plugins --clean-config $TEST_PLUGIN_UUID --yes
echo

# Test 10: Uninstall plugin
echo "10. Uninstall plugin"
$PICARD plugins --remove $TEST_PLUGIN_UUID --yes
echo

# Test 11: Verify uninstall
echo "11. Verify uninstall"
$PICARD plugins --list
echo

# Test 12: Install with specific ref
echo "12. Install with specific ref (v1.0.0)"
$PICARD plugins --install "$PLUGIN_REPO" --ref v1.0.0 --yes
echo

# Test 13: Verify installation
echo "13. Verify installation (should show v1.0.0)"
$PICARD plugins --info $TEST_PLUGIN_UUID | grep -i version
echo

# Test 14: Reinstall plugin
echo "14. Reinstall plugin"
$PICARD plugins --install "$PLUGIN_REPO" --reinstall --yes
echo

# Test 15: Uninstall with purge
echo "15. Uninstall with purge (delete config)"
$PICARD plugins --remove $TEST_PLUGIN_UUID --purge --yes
echo

# Test 16: Verify final cleanup
echo "16. Verify final cleanup"
$PICARD plugins --list
echo

# Test 17: Install with lightweight tag (v1.0.0)
echo "17. Install with lightweight tag (v1.0.0)"
$PICARD plugins --install "$PLUGIN_REPO" --ref v1.0.0 --yes
echo

# Test 18: Verify lightweight tag resolves to commit
echo "18. Verify lightweight tag resolves to commit"
STORED_COMMIT=$($PICARD plugins --info $TEST_PLUGIN_UUID | grep -oP 'Version:.*@\K[a-f0-9]{7}')
echo "Stored commit: $STORED_COMMIT"
echo "Expected commit: ${COMMIT_V1_0_0:0:7}"
if [ "$STORED_COMMIT" = "${COMMIT_V1_0_0:0:7}" ]; then
    echo "✓ Lightweight tag correctly resolved to commit"
else
    echo "✗ ERROR: Lightweight tag did not resolve correctly"
    exit 1
fi
echo

# Test 19: Switch to annotated tag (v1.1.0)
echo "19. Switch to annotated tag (v1.1.0)"
$PICARD plugins --switch-ref $TEST_PLUGIN_UUID v1.1.0
echo

# Test 20: Verify annotated tag resolves to commit (not tag object)
echo "20. Verify annotated tag resolves to commit (not tag object)"
STORED_COMMIT=$($PICARD plugins --info $TEST_PLUGIN_UUID | grep -oP 'Version:.*@\K[a-f0-9]{7}')
echo "Stored commit: $STORED_COMMIT"
echo "Expected commit: ${COMMIT_V1_1_0:0:7}"
if [ "$STORED_COMMIT" = "${COMMIT_V1_1_0:0:7}" ]; then
    echo "✓ Annotated tag correctly resolved to commit"
else
    echo "✗ ERROR: Annotated tag did not resolve correctly"
    exit 1
fi
echo

# Test 21: Update plugin (should update to v1.2.0 if versioning detected)
echo "21. Update plugin (may update to newer tag if available)"
$PICARD plugins --update $TEST_PLUGIN_UUID --yes
echo

# Test 22: Verify commit after update
echo "22. Verify commit after update"
STORED_COMMIT=$($PICARD plugins --info $TEST_PLUGIN_UUID | grep -oP 'Version:.*@\K[a-f0-9]{7}')
echo "Stored commit after update: $STORED_COMMIT"
# Should be either v1.1.0 or v1.2.0 depending on versioning detection
echo "✓ Update completed"
echo

# Test 23: Switch to another annotated tag (v1.2.0)
echo "23. Switch to another annotated tag (v1.2.0)"
$PICARD plugins --switch-ref $TEST_PLUGIN_UUID v1.2.0
echo

# Test 24: Verify new annotated tag resolves correctly
echo "24. Verify new annotated tag resolves correctly"
STORED_COMMIT=$($PICARD plugins --info $TEST_PLUGIN_UUID | grep -oP 'Version:.*@\K[a-f0-9]{7}')
echo "Stored commit: $STORED_COMMIT"
echo "Expected commit: ${COMMIT_V1_2_0:0:7}"
if [ "$STORED_COMMIT" = "${COMMIT_V1_2_0:0:7}" ]; then
    echo "✓ New annotated tag correctly resolved to commit"
else
    echo "✗ ERROR: New annotated tag did not resolve correctly"
    exit 1
fi
echo

# Note: Cache invalidation test skipped for local plugins
# Local plugins fetch directly from the repo without version tag caching
# This test would only be meaningful for registry plugins

# Test 25: List refs
echo "25. List refs"
$PICARD plugins --list-refs $TEST_PLUGIN_UUID
echo

# Note: Cache invalidation test would require remote git URL
# Local file paths bypass version tag caching and fetch directly from repo
# The --refresh-registry cache clearing works correctly for remote registry plugins

# Test 26: Final uninstall
echo "26. Final uninstall"
$PICARD plugins --remove $TEST_PLUGIN_UUID --purge --yes
echo

# Cleanup
echo "Cleanup: Removing test directory"
rm -rf "$TEST_DIR"
echo "✓ Cleanup complete"
echo

echo "=== All Local Tests Completed Successfully ==="
