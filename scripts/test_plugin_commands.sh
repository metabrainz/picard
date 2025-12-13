#!/bin/bash
# Test script for plugin CLI commands
# Tests most plugin commands with actual plugins and registry

set -e

PICARD_PLUGINS="picard-plugins"
TEST_PLUGIN_ID="additional-artists-variables"
TEST_PLUGIN_UUID="2eae631a-1696-4bdc-841f-f75aaa3ae294"
TEST_PLUGIN_URL="https://github.com/rdswift/picard-plugin-additional-artists-variables"

echo "=== Testing Plugin Commands ==="
echo

# Test 1: Browse all plugins from registry
echo "1. Browse all plugins from registry"
$PICARD_PLUGINS --browse
echo

# Test 2: Search plugins
echo "2. Search for 'artist' in plugins"
$PICARD_PLUGINS --search artist
echo

# Test 3: Search with category filter
echo "3. Browse with category filter (metadata)"
$PICARD_PLUGINS --browse --category metadata
echo

# Test 4: Browse with trust level filter
echo "4. Browse with trust level filter (official)"
$PICARD_PLUGINS --browse --trust official
echo

# Test 5: Refresh registry cache
echo "5. Refresh registry cache"
$PICARD_PLUGINS --refresh-registry
echo

# Test 6: Show manifest template
echo "6. Show manifest template"
$PICARD_PLUGINS --manifest
echo

# Test 7: Validate plugin from URL
echo "7. Validate plugin from URL"
$PICARD_PLUGINS --validate $TEST_PLUGIN_URL
echo

# Test 8: Check blacklist for URL
echo "8. Check blacklist for URL"
$PICARD_PLUGINS --check-blacklist $TEST_PLUGIN_URL
echo

# Test 9: Install a plugin
echo "9. Install $TEST_PLUGIN_ID"
$PICARD_PLUGINS --install $TEST_PLUGIN_ID --yes
echo

# Test 10: List installed plugins
echo "10. List installed plugins"
$PICARD_PLUGINS --list
echo

# Test 11: Show plugin info by ID
echo "11. Show plugin info for $TEST_PLUGIN_ID"
$PICARD_PLUGINS --info $TEST_PLUGIN_ID
echo

# Test 12: Show plugin info by UUID
echo "12. Show plugin info by UUID"
$PICARD_PLUGINS --info $TEST_PLUGIN_UUID
echo

# Test 13: Show plugin manifest
echo "13. Show plugin manifest"
$PICARD_PLUGINS --manifest $TEST_PLUGIN_ID
echo

# Test 14: List refs for plugin
echo "14. List refs for $TEST_PLUGIN_ID"
$PICARD_PLUGINS --list-refs $TEST_PLUGIN_ID
echo

# Test 15: Enable plugin
echo "15. Enable plugin"
$PICARD_PLUGINS --enable $TEST_PLUGIN_ID
echo

# Test 16: Disable plugin
echo "16. Disable plugin"
$PICARD_PLUGINS --disable $TEST_PLUGIN_ID
echo

# Test 17: Check for updates
echo "17. Check for updates"
$PICARD_PLUGINS --check-updates
echo

# Test 18: Update plugin
echo "18. Update plugin"
$PICARD_PLUGINS --update $TEST_PLUGIN_ID --yes
echo

# Test 19: Switch to specific ref
echo "19. Switch to specific ref (v1.0.0)"
$PICARD_PLUGINS --switch-ref $TEST_PLUGIN_ID v1.0.0 --yes
echo

# Test 20: Verify switch
echo "20. Verify ref switch"
$PICARD_PLUGINS --info $TEST_PLUGIN_ID
echo

# Test 21: Update all plugins
echo "21. Update all plugins"
$PICARD_PLUGINS --update-all --yes
echo

# Test 22: Test with --no-color flag
echo "22. List plugins with --no-color"
$PICARD_PLUGINS --list --no-color
echo

# Test 23: Clean plugin config
echo "23. Clean plugin config"
$PICARD_PLUGINS --clean-config $TEST_PLUGIN_ID --yes
echo

# Test 24: Uninstall plugin
echo "24. Uninstall $TEST_PLUGIN_ID"
$PICARD_PLUGINS --remove $TEST_PLUGIN_ID --yes
echo

# Test 25: Verify uninstall
echo "25. Verify uninstall"
$PICARD_PLUGINS --list
echo

# Test 26: Install with specific ref
echo "26. Install with specific ref (v1.0.0)"
$PICARD_PLUGINS --install $TEST_PLUGIN_ID --ref v1.0.0 --yes
echo

# Test 27: Verify installation
echo "27. Verify installation"
$PICARD_PLUGINS --info $TEST_PLUGIN_ID
echo

# Test 28: Validate plugin with specific ref
echo "28. Validate plugin with specific ref"
$PICARD_PLUGINS --validate $TEST_PLUGIN_URL --ref v1.0.0
echo

# Test 29: Reinstall plugin
echo "29. Reinstall plugin"
$PICARD_PLUGINS --install $TEST_PLUGIN_ID --reinstall --yes
echo

# Test 30: Uninstall with purge
echo "30. Uninstall with purge (delete config)"
$PICARD_PLUGINS --remove $TEST_PLUGIN_ID --purge --yes
echo

# Test 31: Verify final cleanup
echo "31. Verify final cleanup"
$PICARD_PLUGINS --list
echo

echo "=== All Tests Completed Successfully ==="
