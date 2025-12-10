#!/bin/bash
# Test script for plugin CLI commands
# Tests most plugin commands with actual plugins and registry

set -e

PICARD="python tagger.py"
TEST_PLUGIN_ID="additional-artists-variables"
TEST_PLUGIN_UUID="2eae631a-1696-4bdc-841f-f75aaa3ae294"
TEST_PLUGIN_URL="https://github.com/rdswift/picard-plugin-additional-artists-variables"

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

# Test 4: Browse with trust level filter
echo "4. Browse with trust level filter (official)"
$PICARD plugins --browse --trust official
echo

# Test 5: Refresh registry cache
echo "5. Refresh registry cache"
$PICARD plugins --refresh-registry
echo

# Test 6: Show manifest template
echo "6. Show manifest template"
$PICARD plugins --manifest
echo

# Test 7: Validate plugin from URL
echo "7. Validate plugin from URL"
$PICARD plugins --validate $TEST_PLUGIN_URL
echo

# Test 8: Check blacklist for URL
echo "8. Check blacklist for URL"
$PICARD plugins --check-blacklist $TEST_PLUGIN_URL
echo

# Test 9: Install a plugin
echo "9. Install $TEST_PLUGIN_ID"
$PICARD plugins --install $TEST_PLUGIN_ID --yes
echo

# Test 10: List installed plugins
echo "10. List installed plugins"
$PICARD plugins --list
echo

# Test 11: Show plugin info by ID
echo "11. Show plugin info for $TEST_PLUGIN_ID"
$PICARD plugins --info $TEST_PLUGIN_ID
echo

# Test 12: Show plugin info by UUID
echo "12. Show plugin info by UUID"
$PICARD plugins --info $TEST_PLUGIN_UUID
echo

# Test 13: Show plugin manifest
echo "13. Show plugin manifest"
$PICARD plugins --manifest $TEST_PLUGIN_ID
echo

# Test 14: List refs for plugin
echo "14. List refs for $TEST_PLUGIN_ID"
$PICARD plugins --list-refs $TEST_PLUGIN_ID
echo

# Test 15: Enable plugin
echo "15. Enable plugin"
$PICARD plugins --enable $TEST_PLUGIN_ID
echo

# Test 16: Disable plugin
echo "16. Disable plugin"
$PICARD plugins --disable $TEST_PLUGIN_ID
echo

# Test 17: Check for updates
echo "17. Check for updates"
$PICARD plugins --check-updates
echo

# Test 18: Update plugin
echo "18. Update plugin"
$PICARD plugins --update $TEST_PLUGIN_ID --yes
echo

# Test 19: Switch to specific ref
echo "19. Switch to specific ref (v1.0.0)"
$PICARD plugins --switch-ref $TEST_PLUGIN_ID v1.0.0 --yes
echo

# Test 20: Verify switch
echo "20. Verify ref switch"
$PICARD plugins --info $TEST_PLUGIN_ID
echo

# Test 21: Update all plugins
echo "21. Update all plugins"
$PICARD plugins --update-all --yes
echo

# Test 22: Test with --no-color flag
echo "22. List plugins with --no-color"
$PICARD plugins --list --no-color
echo

# Test 23: Clean plugin config
echo "23. Clean plugin config"
$PICARD plugins --clean-config $TEST_PLUGIN_ID --yes
echo

# Test 24: Uninstall plugin
echo "24. Uninstall $TEST_PLUGIN_ID"
$PICARD plugins --remove $TEST_PLUGIN_ID --yes
echo

# Test 25: Verify uninstall
echo "25. Verify uninstall"
$PICARD plugins --list
echo

# Test 26: Install with specific ref
echo "26. Install with specific ref (v1.0.0)"
$PICARD plugins --install $TEST_PLUGIN_ID --ref v1.0.0 --yes
echo

# Test 27: Verify installation
echo "27. Verify installation"
$PICARD plugins --info $TEST_PLUGIN_ID
echo

# Test 28: Validate plugin with specific ref
echo "28. Validate plugin with specific ref"
$PICARD plugins --validate $TEST_PLUGIN_URL --ref v1.0.0
echo

# Test 29: Reinstall plugin
echo "29. Reinstall plugin"
$PICARD plugins --install $TEST_PLUGIN_ID --reinstall --yes
echo

# Test 30: Uninstall with purge
echo "30. Uninstall with purge (delete config)"
$PICARD plugins --remove $TEST_PLUGIN_ID --purge --yes
echo

# Test 31: Verify final cleanup
echo "31. Verify final cleanup"
$PICARD plugins --list
echo

echo "=== All Tests Completed Successfully ==="
