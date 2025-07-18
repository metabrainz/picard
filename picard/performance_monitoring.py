# -*- coding: utf-8 -*-
"""
Performance Monitoring System for Picard

Tracks performance metrics and identifies bottlenecks in core operations.
"""

import time
import threading
from collections import defaultdict, namedtuple
from contextlib import contextmanager
from functools import wraps

from picard import log


PerformanceMetric = namedtuple('PerformanceMetric', [
    'operation', 'duration', 'timestamp', 'thread_id', 'details'
])


class PerformanceTracker:
    """Tracks performance metrics across Picard operations."""
    
    def __init__(self, max_metrics=10000):
        self.metrics = []
        self.max_metrics = max_metrics
        self.operation_stats = defaultdict(list)
        self.lock = threading.Lock()
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            'file_loading': 2.0,
            'metadata_processing': 1.0,
            'fingerprinting': 5.0,
            'web_request': 3.0,
            'plugin_execution': 1.0,
            'ui_operation': 0.5
        }
    
    @contextmanager
    def track(self, operation, **details):
        """Context manager to track operation performance."""
        start_time = time.time()
        thread_id = threading.get_ident()
        
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            metric = PerformanceMetric(
                operation=operation,
                duration=duration,
                timestamp=start_time,
                thread_id=thread_id,
                details=details
            )
            
            self._record_metric(metric)
            self._check_performance_threshold(metric)
    
    def _record_metric(self, metric):
        """Record a performance metric."""
        with self.lock:
            self.metrics.append(metric)
            self.operation_stats[metric.operation].append(metric.duration)
            
            # Maintain maximum size
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
    
    def _check_performance_threshold(self, metric):
        """Check if metric exceeds performance thresholds."""
        threshold = self.thresholds.get(metric.operation, 2.0)
        
        if metric.duration > threshold * 2:
            log.warning(f"[performance] SLOW: {metric.operation} took {metric.duration:.2f}s "
                       f"(threshold: {threshold}s) - {metric.details}")
        elif metric.duration > threshold:
            log.info(f"[performance] {metric.operation} took {metric.duration:.2f}s "
                    f"(threshold: {threshold}s)")
    
    def get_operation_stats(self, operation):
        """Get statistics for a specific operation."""
        durations = self.operation_stats[operation]
        if not durations:
            return None
        
        return {
            'count': len(durations),
            'total_time': sum(durations),
            'avg_time': sum(durations) / len(durations),
            'min_time': min(durations),
            'max_time': max(durations),
            'recent_avg': sum(durations[-10:]) / min(10, len(durations))
        }
    
    def get_performance_report(self):
        """Generate a comprehensive performance report."""
        report = {}
        
        for operation in self.operation_stats:
            stats = self.get_operation_stats(operation)
            if stats and stats['count'] > 0:
                report[operation] = stats
        
        return report
    
    def get_slow_operations(self, min_duration=1.0):
        """Get operations that are consistently slow."""
        slow_operations = []
        
        for operation, durations in self.operation_stats.items():
            if durations:
                avg_duration = sum(durations) / len(durations)
                if avg_duration > min_duration:
                    slow_operations.append({
                        'operation': operation,
                        'avg_duration': avg_duration,
                        'count': len(durations)
                    })
        
        return sorted(slow_operations, key=lambda x: x['avg_duration'], reverse=True)


# Global instance
performance_tracker = PerformanceTracker()


def track_performance(operation_name, **details):
    """Decorator to track function performance."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with performance_tracker.track(operation_name, function=func.__name__, **details):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def log_performance_summary():
    """Log a performance summary."""
    report = performance_tracker.get_performance_report()
    slow_ops = performance_tracker.get_slow_operations()
    
    log.info("[performance] === Performance Summary ===")
    for operation, stats in report.items():
        log.info(f"[performance] {operation}: {stats['count']} ops, "
                f"avg: {stats['avg_time']:.3f}s, max: {stats['max_time']:.3f}s")
    
    if slow_ops:
        log.warning("[performance] Slow operations detected:")
        for op in slow_ops[:5]:  # Top 5 slowest
            log.warning(f"[performance]   {op['operation']}: avg {op['avg_duration']:.3f}s "
                       f"({op['count']} operations)")
