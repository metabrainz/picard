#!/bin/bash
# Test script for plugin CLI commands
# Tests most plugin commands with actual plugins and registry

set -e

PICARD="python tagger.py"
TEST_PLUGIN_ID="additional-artists-variables"
TEST_PLUGIN_UUID="2eae631a-1696-4bdc-841f-f75aaa3ae294"

echo "=== Testing Plugin Commands ==="
echo

# Test 1: Browse all plugins from registry
echo "1. Browse all plugins from registry"
$PICARD plugins --browse
echo

# Test 2: Search plugins
echo "2. Search for 'artist' in plugins"
$PICARD plugins --search artist
echo

# Test 3: Install a plugin
echo "3. Install $TEST_PLUGIN_ID"
$PICARD plugins --install $TEST_PLUGIN_ID --yes
echo

# Test 4: List installed plugins
echo "4. List installed plugins"
$PICARD plugins --list
echo

# Test 5: Show plugin info by ID
echo "5. Show plugin info for $TEST_PLUGIN_ID"
$PICARD plugins --info $TEST_PLUGIN_ID
echo

# Test 6: Show plugin info by UUID
echo "6. Show plugin info by UUID"
$PICARD plugins --info $TEST_PLUGIN_UUID
echo

# Test 7: Enable plugin
echo "7. Enable plugin"
$PICARD plugins --enable $TEST_PLUGIN_ID
echo

# Test 8: Disable plugin
echo "8. Disable plugin"
$PICARD plugins --disable $TEST_PLUGIN_ID
echo

# Test 9: Check for updates
echo "9. Check for updates"
$PICARD plugins --check-updates
echo

# Test 10: Uninstall plugin
echo "10. Uninstall $TEST_PLUGIN_ID"
$PICARD plugins --uninstall $TEST_PLUGIN_ID --yes
echo

# Test 11: Verify uninstall
echo "11. Verify uninstall"
$PICARD plugins --list
echo

# Test 12: Install with specific ref
echo "12. Install with specific ref (v1.0.0)"
$PICARD plugins --install $TEST_PLUGIN_ID --ref v1.0.0 --yes
echo

# Test 13: Verify installation
echo "13. Verify installation"
$PICARD plugins --info $TEST_PLUGIN_ID
echo

# Test 14: Reinstall plugin
echo "14. Reinstall plugin"
$PICARD plugins --install $TEST_PLUGIN_ID --reinstall --yes
echo

# Test 15: Search with category filter
echo "15. Search with category filter"
$PICARD plugins --browse --category metadata
echo

# Test 16: Final cleanup
echo "16. Final cleanup - uninstall"
$PICARD plugins --uninstall $TEST_PLUGIN_ID --yes
echo

# Test 17: Verify final cleanup
echo "17. Verify final cleanup"
$PICARD plugins --list
echo

echo "=== All Tests Completed Successfully ==="
