# -*- coding: utf-8 -*-
"""
Plugin Development Tools for Picard

Provides utilities and helpers for plugin developers.
"""

import ast
import inspect
import time
from pathlib import Path
from typing import List, Dict, Any

from picard import log


class PluginValidator:
    """Validates plugin structure and compatibility."""
    
    REQUIRED_ATTRIBUTES = ['PLUGIN_NAME', 'PLUGIN_API_VERSIONS']
    RECOMMENDED_ATTRIBUTES = ['PLUGIN_AUTHOR', 'PLUGIN_DESCRIPTION', 'PLUGIN_VERSION']
    
    def __init__(self):
        self.validation_results = {}
    
    def validate_plugin(self, plugin_module, plugin_path=None):
        """Comprehensive plugin validation."""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'recommendations': [],
            'score': 100
        }
        
        # Check required attributes
        for attr in self.REQUIRED_ATTRIBUTES:
            if not hasattr(plugin_module, attr):
                results['errors'].append(f"Missing required attribute: {attr}")
                results['valid'] = False
                results['score'] -= 25
        
        # Check recommended attributes
        for attr in self.RECOMMENDED_ATTRIBUTES:
            if not hasattr(plugin_module, attr):
                results['warnings'].append(f"Missing recommended attribute: {attr}")
                results['score'] -= 5
        
        # Check API version compatibility
        if hasattr(plugin_module, 'PLUGIN_API_VERSIONS'):
            api_versions = getattr(plugin_module, 'PLUGIN_API_VERSIONS')
            if not self._check_api_compatibility(api_versions):
                results['errors'].append(f"Incompatible API versions: {api_versions}")
                results['valid'] = False
                results['score'] -= 50
        
        # Check for known hooks
        hooks_found = self._find_plugin_hooks(plugin_module)
        if not hooks_found:
            results['warnings'].append("No known hook functions found")
            results['score'] -= 20
        else:
            results['recommendations'].append(f"Found hooks: {', '.join(hooks_found)}")
        
        # Check code quality if path is available
        if plugin_path:
            code_issues = self._analyze_code_quality(plugin_path)
            results['recommendations'].extend(code_issues)
        
        self.validation_results[getattr(plugin_module, 'PLUGIN_NAME', 'unknown')] = results
        return results
    
    def _check_api_compatibility(self, api_versions):
        """Check if API versions are compatible."""
        # Simplified check - in reality this would check against current Picard API
        if isinstance(api_versions, (list, tuple)):
            return any(version.startswith(('2.', '3.')) for version in api_versions)
        return str(api_versions).startswith(('2.', '3.'))
    
    def _find_plugin_hooks(self, plugin_module):
        """Find known hook functions in the plugin."""
        known_hooks = [
            'register_file_post_load_processor',
            'register_album_metadata_processor',
            'register_track_metadata_processor',
            'register_file_post_save_processor',
            'file_post_load_processor',
            'album_metadata_processor',
            'track_metadata_processor'
        ]
        
        found_hooks = []
        for hook in known_hooks:
            if hasattr(plugin_module, hook):
                found_hooks.append(hook)
        
        return found_hooks
    
    def _analyze_code_quality(self, plugin_path):
        """Basic code quality analysis."""
        issues = []
        
        try:
            if plugin_path.endswith('.zip'):
                # Skip analysis for zip files for now
                return issues
            
            with open(plugin_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse AST for basic analysis
            try:
                tree = ast.parse(source)
                
                # Check for docstrings
                if not ast.get_docstring(tree):
                    issues.append("Consider adding a module docstring")
                
                # Count functions without docstrings
                functions_without_docs = 0
                total_functions = 0
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        total_functions += 1
                        if not ast.get_docstring(node):
                            functions_without_docs += 1
                
                if total_functions > 0 and functions_without_docs / total_functions > 0.5:
                    issues.append(f"Consider adding docstrings to functions "
                                f"({functions_without_docs}/{total_functions} missing)")
                
            except SyntaxError as e:
                issues.append(f"Syntax error in plugin: {e}")
                
        except Exception as e:
            issues.append(f"Could not analyze code quality: {e}")
        
        return issues
    
    def generate_plugin_report(self, plugin_name):
        """Generate a detailed report for a plugin."""
        if plugin_name not in self.validation_results:
            return "No validation results found for this plugin"
        
        results = self.validation_results[plugin_name]
        
        report = [
            f"=== Plugin Validation Report: {plugin_name} ===",
            f"Overall Score: {results['score']}/100",
            f"Valid: {'✅' if results['valid'] else '❌'}",
            ""
        ]
        
        if results['errors']:
            report.append("🚨 ERRORS:")
            for error in results['errors']:
                report.append(f"  - {error}")
            report.append("")
        
        if results['warnings']:
            report.append("⚠️  WARNINGS:")
            for warning in results['warnings']:
                report.append(f"  - {warning}")
            report.append("")
        
        if results['recommendations']:
            report.append("💡 RECOMMENDATIONS:")
            for rec in results['recommendations']:
                report.append(f"  - {rec}")
        
        return "\n".join(report)


class PluginProfiler:
    """Profiles plugin performance and behavior."""
    
    def __init__(self):
        self.profile_data = {}
    
    def profile_plugin_hook(self, plugin_name, hook_name, execution_time, args_info=None):
        """Record performance data for a plugin hook."""
        if plugin_name not in self.profile_data:
            self.profile_data[plugin_name] = {}
        
        if hook_name not in self.profile_data[plugin_name]:
            self.profile_data[plugin_name][hook_name] = []
        
        self.profile_data[plugin_name][hook_name].append({
            'execution_time': execution_time,
            'args_info': args_info,
            'timestamp': time.time()
        })
    
    def get_plugin_performance_summary(self, plugin_name):
        """Get performance summary for a plugin."""
        if plugin_name not in self.profile_data:
            return None
        
        summary = {}
        for hook_name, executions in self.profile_data[plugin_name].items():
            times = [e['execution_time'] for e in executions]
            summary[hook_name] = {
                'call_count': len(times),
                'total_time': sum(times),
                'avg_time': sum(times) / len(times) if times else 0,
                'max_time': max(times) if times else 0,
                'min_time': min(times) if times else 0
            }
        
        return summary


# Global instances
plugin_validator = PluginValidator()
plugin_profiler = PluginProfiler()


def log_plugin_development_tips():
    """Log helpful tips for plugin development."""
    tips = [
        "💡 Plugin Development Tips:",
        "  - Always include PLUGIN_NAME and PLUGIN_API_VERSIONS",
        "  - Add proper error handling in your hook functions",
        "  - Use descriptive function and variable names",
        "  - Test your plugin with different file types",
        "  - Check performance with large music collections",
        "  - Add logging for debugging purposes"
    ]
    
    for tip in tips:
        log.info(f"[plugin-dev] {tip}")
