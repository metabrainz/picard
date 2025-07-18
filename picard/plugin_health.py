# -*- coding: utf-8 -*-
"""
Plugin Health Monitoring System for Picard

Provides advanced diagnostics and monitoring for plugin performance and reliability.
"""

import time
from collections import defaultdict, deque
from contextlib import contextmanager
from enum import Enum

from picard import log


class PluginStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PluginHealthMonitor:
    """Monitors plugin performance and health metrics."""
    
    def __init__(self, max_history=1000):
        self.execution_times = defaultdict(lambda: deque(maxlen=max_history))
        self.error_counts = defaultdict(int)
        self.warning_counts = defaultdict(int)
        self.total_executions = defaultdict(int)
        
    @contextmanager
    def track_execution(self, plugin_name, hook_type):
        """Context manager to track plugin execution time and errors."""
        start_time = time.time()
        try:
            yield
            # Successful execution
            execution_time = time.time() - start_time
            self.execution_times[f"{plugin_name}:{hook_type}"].append(execution_time)
            self.total_executions[plugin_name] += 1
            
            # Log performance warnings
            if execution_time > 2.0:
                log.warning(f"[plugin-health] Plugin {plugin_name} ({hook_type}) took {execution_time:.2f}s - SLOW")
                self.warning_counts[plugin_name] += 1
            elif execution_time > 5.0:
                log.error(f"[plugin-health] Plugin {plugin_name} ({hook_type}) took {execution_time:.2f}s - CRITICAL")
                
        except Exception as e:
            execution_time = time.time() - start_time
            self.error_counts[plugin_name] += 1
            log.error(f"[plugin-health] Plugin {plugin_name} ({hook_type}) failed after {execution_time:.2f}s: {e}")
            raise
    
    def get_plugin_status(self, plugin_name):
        """Get overall health status of a plugin."""
        total = self.total_executions[plugin_name]
        errors = self.error_counts[plugin_name]
        warnings = self.warning_counts[plugin_name]
        
        if total == 0:
            return PluginStatus.HEALTHY
        
        error_rate = errors / total
        warning_rate = warnings / total
        
        if error_rate > 0.1:  # More than 10% errors
            return PluginStatus.CRITICAL
        elif error_rate > 0.05 or warning_rate > 0.2:  # 5% errors or 20% warnings
            return PluginStatus.ERROR
        elif warning_rate > 0.1:  # More than 10% warnings
            return PluginStatus.WARNING
        
        return PluginStatus.HEALTHY
    
    def get_performance_report(self):
        """Generate a performance report for all plugins."""
        report = {}
        for plugin_name in self.total_executions:
            times = []
            for key in self.execution_times:
                if key.startswith(f"{plugin_name}:"):
                    times.extend(self.execution_times[key])
            
            if times:
                report[plugin_name] = {
                    'status': self.get_plugin_status(plugin_name).value,
                    'total_executions': self.total_executions[plugin_name],
                    'errors': self.error_counts[plugin_name],
                    'warnings': self.warning_counts[plugin_name],
                    'avg_time': sum(times) / len(times),
                    'max_time': max(times),
                    'min_time': min(times)
                }
        
        return report


# Global instance
plugin_health_monitor = PluginHealthMonitor()
