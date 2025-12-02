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

# Test 3: Search with category filter
echo "3. Browse with category filter (metadata)"
$PICARD plugins --browse --category metadata
echo

# Test 4: Show manifest template
echo "4. Show manifest template"
$PICARD plugins --manifest
echo

# Test 5: Install a plugin
echo "5. Install $TEST_PLUGIN_ID"
$PICARD plugins --install $TEST_PLUGIN_ID --yes
echo

# Test 6: List installed plugins
echo "6. List installed plugins"
$PICARD plugins --list
echo

# Test 7: Show plugin info by ID
echo "7. Show plugin info for $TEST_PLUGIN_ID"
$PICARD plugins --info $TEST_PLUGIN_ID
echo

# Test 8: Show plugin info by UUID
echo "8. Show plugin info by UUID"
$PICARD plugins --info $TEST_PLUGIN_UUID
echo

# Test 9: Show plugin manifest
echo "9. Show plugin manifest"
$PICARD plugins --manifest $TEST_PLUGIN_ID
echo

# Test 10: List refs for plugin
echo "10. List refs for $TEST_PLUGIN_ID"
$PICARD plugins --list-refs $TEST_PLUGIN_ID
echo

# Test 11: Enable plugin
echo "11. Enable plugin"
$PICARD plugins --enable $TEST_PLUGIN_ID
echo

# Test 12: Disable plugin
echo "12. Disable plugin"
$PICARD plugins --disable $TEST_PLUGIN_ID
echo

# Test 13: Check for updates
echo "13. Check for updates"
$PICARD plugins --check-updates
echo

# Test 14: Update plugin
echo "14. Update plugin"
$PICARD plugins --update $TEST_PLUGIN_ID --yes
echo

# Test 15: Update all plugins
echo "15. Update all plugins"
$PICARD plugins --update-all --yes
echo

# Test 16: Uninstall plugin
echo "16. Uninstall $TEST_PLUGIN_ID"
$PICARD plugins --uninstall $TEST_PLUGIN_ID --yes
echo

# Test 17: Verify uninstall
echo "17. Verify uninstall"
$PICARD plugins --list
echo

# Test 18: Install with specific ref
echo "18. Install with specific ref (v1.0.0)"
$PICARD plugins --install $TEST_PLUGIN_ID --ref v1.0.0 --yes
echo

# Test 19: Verify installation
echo "19. Verify installation"
$PICARD plugins --info $TEST_PLUGIN_ID
echo

# Test 20: Reinstall plugin
echo "20. Reinstall plugin"
$PICARD plugins --install $TEST_PLUGIN_ID --reinstall --yes
echo

# Test 21: Uninstall with purge
echo "21. Uninstall with purge (delete config)"
$PICARD plugins --uninstall $TEST_PLUGIN_ID --purge --yes
echo

# Test 22: Verify final cleanup
echo "22. Verify final cleanup"
$PICARD plugins --list
echo

echo "=== All Tests Completed Successfully ==="
