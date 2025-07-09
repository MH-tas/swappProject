#!/usr/bin/env python3
"""
Professional Performance Dashboard
Real-time performance monitoring for Cisco Switch Manager

Author: Professional Network Management Team
Version: 2.0.0
Date: 2024-12-20
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PerformanceDashboard:
    """Professional performance monitoring dashboard"""
    
    def __init__(self, parent: tk.Widget, cisco_manager):
        self.parent = parent
        self.cisco_manager = cisco_manager
        self.update_thread = None
        self.is_monitoring = False
        self.update_interval = 2.0  # seconds
        
        # Performance history
        self.performance_history = {
            'timestamps': [],
            'cache_hit_rates': [],
            'command_times': [],
            'memory_usage': [],
            'connection_health': []
        }
        self.max_history_points = 100
        
        self.create_dashboard()
        
    def create_dashboard(self) -> None:
        """Create the performance dashboard UI"""
        # Main dashboard frame
        self.dashboard_frame = ttk.LabelFrame(self.parent, text="📊 Performans İzleme", padding=10)
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for different views
        self.notebook = ttk.Notebook(self.dashboard_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Real-time tab
        self.realtime_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.realtime_frame, text="Anlık")
        
        # Statistics tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="İstatistikler")
        
        # Cache tab
        self.cache_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cache_frame, text="Cache")
        
        self.create_realtime_view()
        self.create_statistics_view()
        self.create_cache_view()
        
        # Control buttons
        self.create_controls()
        
    def create_realtime_view(self) -> None:
        """Create real-time performance view"""
        # Connection status
        status_frame = ttk.LabelFrame(self.realtime_frame, text="Bağlantı Durumu", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.connection_status = tk.StringVar(value="🔴 Bağlı Değil")
        ttk.Label(status_frame, textvariable=self.connection_status, 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        self.health_indicator = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.health_indicator).pack(side=tk.RIGHT)
        
        # Performance metrics grid
        metrics_frame = ttk.LabelFrame(self.realtime_frame, text="Performans Metrikleri", padding=10)
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create metrics display
        self.metrics = {}
        metrics_config = [
            ("Cache Hit Rate", "cache_hit_rate", "%"),
            ("Komut Sayısı", "commands_executed", ""),
            ("Ortalama Yanıt", "avg_response_time", "ms"),
            ("Bellek Kullanımı", "memory_usage", "MB"),
            ("Hata Oranı", "error_rate", "%"),
            ("Bağlantı Başarı", "connection_success_rate", "%")
        ]
        
        row = 0
        for i, (label, key, unit) in enumerate(metrics_config):
            col = i % 3
            if col == 0 and i > 0:
                row += 1
                
            metric_frame = ttk.Frame(metrics_frame)
            metric_frame.grid(row=row, column=col, padx=10, pady=5, sticky='ew')
            
            ttk.Label(metric_frame, text=label, font=('Arial', 9, 'bold')).pack()
            
            value_var = tk.StringVar(value=f"0 {unit}")
            value_label = ttk.Label(metric_frame, textvariable=value_var, 
                                  font=('Arial', 14), foreground='blue')
            value_label.pack()
            
            self.metrics[key] = value_var
        
        # Configure grid weights
        for i in range(3):
            metrics_frame.columnconfigure(i, weight=1)
    
    def create_statistics_view(self) -> None:
        """Create detailed statistics view"""
        # Statistics tree
        columns = ('Metrik', 'Değer', 'Birim', 'Durum')
        self.stats_tree = ttk.Treeview(self.stats_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.stats_tree.heading(col, text=col)
            self.stats_tree.column(col, width=100)
        
        # Scrollbar for stats tree
        stats_scroll = ttk.Scrollbar(self.stats_frame, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scroll.set)
        
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_cache_view(self) -> None:
        """Create cache performance view"""
        cache_info_frame = ttk.LabelFrame(self.cache_frame, text="Cache Bilgileri", padding=10)
        cache_info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Cache statistics
        self.cache_stats = {}
        cache_types = ['interface', 'device', 'command', 'mac']
        
        for i, cache_type in enumerate(cache_types):
            frame = ttk.Frame(cache_info_frame)
            frame.grid(row=i//2, column=i%2, padx=10, pady=5, sticky='ew')
            
            ttk.Label(frame, text=f"{cache_type.title()} Cache", 
                     font=('Arial', 10, 'bold')).pack()
            
            stats_var = tk.StringVar(value="Hit Rate: 0%\nSize: 0/0\nMemory: 0MB")
            ttk.Label(frame, textvariable=stats_var, justify=tk.LEFT).pack()
            
            self.cache_stats[cache_type] = stats_var
        
        # Configure grid
        for i in range(2):
            cache_info_frame.columnconfigure(i, weight=1)
        
        # Cache controls
        controls_frame = ttk.Frame(self.cache_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Cache Temizle", 
                  command=self.clear_cache).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Cache İstatistikleri", 
                  command=self.show_detailed_cache_stats).pack(side=tk.LEFT, padx=5)
    
    def create_controls(self) -> None:
        """Create dashboard control buttons"""
        controls_frame = ttk.Frame(self.dashboard_frame)
        controls_frame.pack(fill=tk.X, pady=5)
        
        self.monitor_btn = ttk.Button(controls_frame, text="İzlemeyi Başlat", 
                                     command=self.toggle_monitoring)
        self.monitor_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Yenile", 
                  command=self.update_display).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Sağlık Kontrolü", 
                  command=self.run_health_check).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(controls_frame, text="Performans Raporu", 
                  command=self.generate_performance_report).pack(side=tk.LEFT, padx=5)
        
        # Update interval control
        ttk.Label(controls_frame, text="Güncelleme (sn):").pack(side=tk.RIGHT, padx=5)
        
        self.interval_var = tk.StringVar(value="2.0")
        interval_spin = ttk.Spinbox(controls_frame, from_=0.5, to=10.0, increment=0.5,
                                  textvariable=self.interval_var, width=5,
                                  command=self.update_interval_changed)
        interval_spin.pack(side=tk.RIGHT, padx=5)
    
    def toggle_monitoring(self) -> None:
        """Toggle performance monitoring"""
        if self.is_monitoring:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_btn.config(text="İzlemeyi Durdur")
            
            self.update_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.update_thread.start()
            
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        self.is_monitoring = False
        self.monitor_btn.config(text="İzlemeyi Başlat")
        logger.info("Performance monitoring stopped")
    
    def monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                self.update_display()
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(1)
    
    def update_display(self) -> None:
        """Update all dashboard displays"""
        try:
            if not hasattr(self.cisco_manager, 'get_performance_stats'):
                return
                
            # Get performance stats
            stats = self.cisco_manager.get_performance_stats()
            health = self.cisco_manager.health_check()
            
            # Update real-time view
            self.update_realtime_view(stats, health)
            
            # Update statistics view
            self.update_statistics_view(stats)
            
            # Update cache view
            self.update_cache_view(stats.get('cache_stats', {}))
            
            # Update performance history
            self.update_performance_history(stats)
            
        except Exception as e:
            logger.error(f"Error updating performance display: {e}")
    
    def update_realtime_view(self, stats: Dict[str, Any], health: Dict[str, Any]) -> None:
        """Update real-time performance view"""
        # Connection status
        if health.get('connected', False):
            if health.get('connection_healthy', False):
                self.connection_status.set("🟢 Bağlı ve Sağlıklı")
            else:
                self.connection_status.set("🟡 Bağlı ama Sorunlu")
        else:
            self.connection_status.set("🔴 Bağlı Değil")
        
        # Health indicator
        health_indicators = []
        if not health.get('cache_healthy', True):
            health_indicators.append("Cache Sorunu")
        if not health.get('memory_usage_ok', True):
            health_indicators.append("Bellek Sorunu")
        if health.get('connection_stale', False):
            health_indicators.append("Eski Bağlantı")
        
        self.health_indicator.set(" | ".join(health_indicators) if health_indicators else "✅ Sorun Yok")
        
        # Update metrics
        command_stats = stats.get('command_stats', {})
        connection_stats = stats.get('connection_stats', {})
        memory_stats = stats.get('memory_usage', {})
        
        self.metrics['cache_hit_rate'].set(f"{command_stats.get('cache_hit_rate', 0):.1f}%")
        self.metrics['commands_executed'].set(f"{command_stats.get('commands_executed', 0)}")
        self.metrics['avg_response_time'].set("N/A")  # Would need timing data
        self.metrics['memory_usage'].set(f"{memory_stats.get('total_cache_memory', 0) // (1024*1024):.1f}MB")
        self.metrics['error_rate'].set(f"{command_stats.get('error_rate', 0):.1f}%")
        self.metrics['connection_success_rate'].set(f"{connection_stats.get('success_rate', 0):.1f}%")
    
    def update_statistics_view(self, stats: Dict[str, Any]) -> None:
        """Update detailed statistics view"""
        # Clear existing items
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Add connection statistics
        connection_stats = stats.get('connection_stats', {})
        self.stats_tree.insert('', 'end', values=(
            'Bağlantı Denemeleri', connection_stats.get('connection_attempts', 0), '', '📊'
        ))
        self.stats_tree.insert('', 'end', values=(
            'Başarılı Bağlantılar', connection_stats.get('successful_connections', 0), '', '✅'
        ))
        self.stats_tree.insert('', 'end', values=(
            'Bağlantı Başarı Oranı', f"{connection_stats.get('success_rate', 0):.1f}", '%', '📈'
        ))
        
        # Add command statistics
        command_stats = stats.get('command_stats', {})
        self.stats_tree.insert('', 'end', values=(
            'Toplam Komut', command_stats.get('commands_executed', 0), '', '⚡'
        ))
        self.stats_tree.insert('', 'end', values=(
            'Cache Hit', command_stats.get('cache_hits', 0), '', '🎯'
        ))
        self.stats_tree.insert('', 'end', values=(
            'Cache Miss', command_stats.get('cache_misses', 0), '', '❌'
        ))
        self.stats_tree.insert('', 'end', values=(
            'Cache Hit Oranı', f"{command_stats.get('cache_hit_rate', 0):.1f}", '%', '📊'
        ))
        self.stats_tree.insert('', 'end', values=(
            'Hata Sayısı', command_stats.get('errors', 0), '', '🚨'
        ))
        
        # Add memory statistics
        memory_stats = stats.get('memory_usage', {})
        self.stats_tree.insert('', 'end', values=(
            'Cache Bellek Kullanımı', f"{memory_stats.get('total_cache_memory', 0) // (1024*1024):.1f}", 'MB', '💾'
        ))
        self.stats_tree.insert('', 'end', values=(
            'Cache Verimliliği', f"{memory_stats.get('cache_efficiency', 0):.1f}", '%', '⚡'
        ))
    
    def update_cache_view(self, cache_stats: Dict[str, Any]) -> None:
        """Update cache performance view"""
        for cache_type, stats_var in self.cache_stats.items():
            if cache_type in cache_stats:
                stats = cache_stats[cache_type]
                text = (f"Hit Rate: {stats.get('hit_rate', 0):.1f}%\n"
                       f"Size: {stats.get('size', 0)}/{stats.get('max_size', 0)}\n"
                       f"Memory: {stats.get('memory_usage', 0) // 1024:.1f}KB")
                stats_var.set(text)
            else:
                stats_var.set("Hit Rate: 0%\nSize: 0/0\nMemory: 0KB")
    
    def update_performance_history(self, stats: Dict[str, Any]) -> None:
        """Update performance history for trending"""
        timestamp = datetime.now()
        
        # Add to history
        self.performance_history['timestamps'].append(timestamp)
        self.performance_history['cache_hit_rates'].append(
            stats.get('command_stats', {}).get('cache_hit_rate', 0)
        )
        self.performance_history['memory_usage'].append(
            stats.get('memory_usage', {}).get('total_cache_memory', 0)
        )
        
        # Trim history if too long
        if len(self.performance_history['timestamps']) > self.max_history_points:
            for key in self.performance_history:
                self.performance_history[key] = self.performance_history[key][-self.max_history_points:]
    
    def update_interval_changed(self) -> None:
        """Update monitoring interval"""
        try:
            self.update_interval = float(self.interval_var.get())
        except ValueError:
            self.interval_var.set("2.0")
            self.update_interval = 2.0
    
    def clear_cache(self) -> None:
        """Clear all caches"""
        try:
            self.cisco_manager.clear_cache()
            self.update_display()
            logger.info("All caches cleared from dashboard")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def show_detailed_cache_stats(self) -> None:
        """Show detailed cache statistics in a popup"""
        try:
            stats = self.cisco_manager.get_performance_stats()
            cache_stats = stats.get('cache_stats', {})
            
            # Create popup window
            popup = tk.Toplevel(self.parent)
            popup.title("Detaylı Cache İstatistikleri")
            popup.geometry("600x400")
            popup.transient(self.parent)
            popup.grab_set()
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(popup)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Format cache statistics
            content = "DETAYLI CACHE İSTATİSTİKLERİ\n"
            content += "=" * 50 + "\n\n"
            
            for cache_type, stats in cache_stats.items():
                content += f"{cache_type.upper()} CACHE:\n"
                content += f"  Hit Rate: {stats.get('hit_rate', 0):.2f}%\n"
                content += f"  Hits: {stats.get('hits', 0)}\n"
                content += f"  Misses: {stats.get('misses', 0)}\n"
                content += f"  Size: {stats.get('size', 0)}/{stats.get('max_size', 0)}\n"
                content += f"  Memory Usage: {stats.get('memory_usage', 0):,} bytes\n"
                content += f"  Evictions: {stats.get('evictions', 0)}\n"
                content += f"  Compressions: {stats.get('compressions', 0)}\n"
                content += "-" * 30 + "\n\n"
            
            text_widget.insert('1.0', content)
            text_widget.config(state=tk.DISABLED)
            
        except Exception as e:
            logger.error(f"Error showing cache stats: {e}")
    
    def run_health_check(self) -> None:
        """Run and display health check results"""
        try:
            health = self.cisco_manager.health_check()
            
            # Create popup window
            popup = tk.Toplevel(self.parent)
            popup.title("Sistem Sağlık Kontrolü")
            popup.geometry("400x300")
            popup.transient(self.parent)
            popup.grab_set()
            
            # Health check results
            content_frame = ttk.Frame(popup)
            content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            ttk.Label(content_frame, text="Sistem Sağlık Durumu", 
                     font=('Arial', 14, 'bold')).pack(pady=10)
            
            # Display health indicators
            for key, value in health.items():
                frame = ttk.Frame(content_frame)
                frame.pack(fill=tk.X, pady=2)
                
                indicator = "✅" if value else "❌"
                if key == 'last_command_age' and value is not None:
                    indicator = "⏰"
                    value = f"{value:.1f} saniye önce"
                elif isinstance(value, bool):
                    value = "TAMAM" if value else "SORUN"
                
                ttk.Label(frame, text=f"{indicator} {key.replace('_', ' ').title()}:").pack(side=tk.LEFT)
                ttk.Label(frame, text=str(value), font=('Arial', 9, 'bold')).pack(side=tk.RIGHT)
            
            ttk.Button(content_frame, text="Kapat", command=popup.destroy).pack(pady=20)
            
        except Exception as e:
            logger.error(f"Error running health check: {e}")
    
    def generate_performance_report(self) -> None:
        """Generate and display performance report"""
        try:
            stats = self.cisco_manager.get_performance_stats()
            
            # Create popup window
            popup = tk.Toplevel(self.parent)
            popup.title("Performans Raporu")
            popup.geometry("700x500")
            popup.transient(self.parent)
            
            # Create text widget with scrollbar
            text_frame = ttk.Frame(popup)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
            text_widget.configure(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Generate report content
            report = self._generate_report_content(stats)
            text_widget.insert('1.0', report)
            text_widget.config(state=tk.DISABLED)
            
            # Add close button
            ttk.Button(popup, text="Kapat", command=popup.destroy).pack(pady=5)
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
    
    def _generate_report_content(self, stats: Dict[str, Any]) -> str:
        """Generate detailed performance report content"""
        report = f"""
CISCO SWITCH MANAGER - PERFORMANS RAPORU
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 60}

BAĞLANTI İSTATİSTİKLERİ:
{'-' * 30}
Connection Attempts: {stats.get('connection_stats', {}).get('connection_attempts', 0)}
Successful Connections: {stats.get('connection_stats', {}).get('successful_connections', 0)}
Success Rate: {stats.get('connection_stats', {}).get('success_rate', 0):.2f}%
Connection Health: {'✅ SAĞLIKLI' if stats.get('connection_stats', {}).get('connection_health', False) else '❌ SORUNLU'}

KOMUT İSTATİSTİKLERİ:
{'-' * 30}
Total Commands Executed: {stats.get('command_stats', {}).get('commands_executed', 0)}
Cache Hits: {stats.get('command_stats', {}).get('cache_hits', 0)}
Cache Misses: {stats.get('command_stats', {}).get('cache_misses', 0)}
Cache Hit Rate: {stats.get('command_stats', {}).get('cache_hit_rate', 0):.2f}%
Error Count: {stats.get('command_stats', {}).get('errors', 0)}
Error Rate: {stats.get('command_stats', {}).get('error_rate', 0):.2f}%

BELLEK KULLANIMI:
{'-' * 30}
Total Cache Memory: {stats.get('memory_usage', {}).get('total_cache_memory', 0) // (1024*1024):.1f} MB
Cache Efficiency: {stats.get('memory_usage', {}).get('cache_efficiency', 0):.2f}%

CACHE DETAYLARI:
{'-' * 30}
"""
        
        cache_stats = stats.get('cache_stats', {})
        for cache_type, cache_info in cache_stats.items():
            report += f"""
{cache_type.upper()} Cache:
  Hit Rate: {cache_info.get('hit_rate', 0):.2f}%
  Size: {cache_info.get('size', 0)}/{cache_info.get('max_size', 0)}
  Memory: {cache_info.get('memory_usage', 0):,} bytes
  Hits: {cache_info.get('hits', 0)}
  Misses: {cache_info.get('misses', 0)}
  Evictions: {cache_info.get('evictions', 0)}
  Compressions: {cache_info.get('compressions', 0)}
"""
        
        report += f"""

PERFORMANS ÖNERİLERİ:
{'-' * 30}
"""
        
        # Add performance recommendations
        cache_hit_rate = stats.get('command_stats', {}).get('cache_hit_rate', 0)
        if cache_hit_rate < 50:
            report += "• Cache hit rate düşük. Cache TTL değerlerini artırmayı düşünün.\n"
        
        error_rate = stats.get('command_stats', {}).get('error_rate', 0)
        if error_rate > 5:
            report += "• Hata oranı yüksek. Bağlantı ayarlarını kontrol edin.\n"
        
        memory_usage = stats.get('memory_usage', {}).get('total_cache_memory', 0)
        if memory_usage > 50 * 1024 * 1024:  # 50MB
            report += "• Bellek kullanımı yüksek. Cache boyutlarını azaltmayı düşünün.\n"
        
        if cache_hit_rate > 80 and error_rate < 2:
            report += "• Performans optimum seviyede. Hiçbir değişiklik gerekli değil.\n"
        
        return report 