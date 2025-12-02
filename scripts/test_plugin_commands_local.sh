#!/bin/bash
# Test script for plugin CLI commands using local git repository (no registry)
# Creates a dummy plugin in a local git repo and tests all operations

set -e

PICARD="python tagger.py"
TEST_DIR=$(mktemp -d)
PLUGIN_REPO="$TEST_DIR/test-plugin"
TEST_PLUGIN_UUID="12345678-1234-4678-9234-123456789abc"

echo "=== Testing Plugin Commands (Local Git Repository) ==="
echo "Test directory: $TEST_DIR"
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

# Commit v1.0.0
git add .
git commit -q -m "Initial commit - v1.0.0"
git tag v1.0.0

# Create v1.1.0
sed -i 's/version = "1.0.0"/version = "1.1.0"/' MANIFEST.toml
sed -i 's/PLUGIN_VERSION = "1.0.0"/PLUGIN_VERSION = "1.1.0"/' test_plugin.py
git add .
git commit -q -m "Release v1.1.0"
git tag v1.1.0

cd - > /dev/null
echo "✓ Created plugin repository at $PLUGIN_REPO"
echo

# Test 1: Validate plugin from local path
echo "1. Validate plugin from local path"
$PICARD plugins --validate "$PLUGIN_REPO"
echo

# Test 2: Validate plugin with specific ref
echo "2. Validate plugin with specific ref (v1.0.0)"
$PICARD plugins --validate "$PLUGIN_REPO" --ref v1.0.0
echo

# Test 3: Install plugin from local path
echo "3. Install plugin from local path"
$PICARD plugins --install "$PLUGIN_REPO" --yes
echo

# Test 4: List installed plugins
echo "4. List installed plugins"
$PICARD plugins --list
echo

# Test 5: Show plugin info by UUID
echo "5. Show plugin info by UUID"
$PICARD plugins --info $TEST_PLUGIN_UUID
echo

# Test 6: Show plugin manifest
echo "6. Show plugin manifest"
$PICARD plugins --manifest $TEST_PLUGIN_UUID
echo

# Test 7: Enable plugin
echo "7. Enable plugin"
$PICARD plugins --enable $TEST_PLUGIN_UUID
echo

# Test 8: Disable plugin
echo "8. Disable plugin"
$PICARD plugins --disable $TEST_PLUGIN_UUID
echo

# Test 9: Clean plugin config
echo "9. Clean plugin config"
$PICARD plugins --clean-config $TEST_PLUGIN_UUID --yes
echo

# Test 10: Uninstall plugin
echo "10. Uninstall plugin"
$PICARD plugins --uninstall $TEST_PLUGIN_UUID --yes
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
$PICARD plugins --uninstall $TEST_PLUGIN_UUID --purge --yes
echo

# Test 16: Verify final cleanup
echo "16. Verify final cleanup"
$PICARD plugins --list
echo

# Cleanup
echo "Cleanup: Removing test directory"
rm -rf "$TEST_DIR"
echo "✓ Cleanup complete"
echo

echo "=== All Local Tests Completed Successfully ==="
