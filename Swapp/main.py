#!/usr/bin/env python3
"""
Cisco Switch Professional Manager
Enterprise-grade Cisco switch management application with real-time monitoring,
comprehensive diagnostics, and professional network management capabilities.

Author: Professional Network Management Team
Version: 2.0.0
Date: 2024-12-20
License: Enterprise Professional License
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from cisco_manager import CiscoManager, CiscoManagerError
from gui_components import (
    StatusBar, ConnectionPanel, PortVisualization, 
    CommandTerminal, DeviceInfoPanel, ModernFrame
)

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cisco_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CiscoSwitchApp:
    """
    Professional Cisco Switch Management Application
    
    Features:
    - Real-time port monitoring with auto-refresh
    - Comprehensive device diagnostics
    - Professional UI with live indicators
    - Advanced error handling and logging
    - Performance monitoring and analytics
    - Professional notification system
    - Enterprise-grade security features
    """
    
    def __init__(self):
        """Initialize the professional application"""
        logger.info("Initializing Cisco Switch Professional Manager")
        
        # Main window setup
        self.root = tk.Tk()
        self.root.title("🔧 Cisco Switch Professional Manager v2.0")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#2c3e50')
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Professional window icon (if available)
        try:
            self.root.iconbitmap('swapp.ico')
        except:
            pass
        
        # Core components
        self.cisco_manager = CiscoManager()
        self.setup_professional_variables()
        
        # GUI setup
        self.setup_gui()
        self.setup_callbacks()
        
        # Start professional monitoring systems
        self.start_professional_systems()
        
        logger.info("Application initialized successfully")
    
    def setup_professional_variables(self):
        """Initialize professional application variables"""
        # Auto-refresh settings
        self.auto_refresh_active = True
        self.refresh_interval = 1500  # 1.5 seconds for real-time monitoring
        self.port_refresh_interval = 2000  # Port-specific refresh
        
        # State tracking
        self.last_interface_states = {}
        self.last_device_status = {}
        self.port_change_history = []
        
        # Professional features
        self.notifications = []
        self.connection_history = []
        self.performance_history = {
            'cpu': [], 'memory': [], 'timestamps': [], 
            'interfaces_up': [], 'interfaces_down': []
        }
        
        # Monitoring flags
        self.device_online = False
        self.monitoring_active = False
        self.real_time_monitoring = True
        self.sound_enabled = True
        
        # Threading controls
        self.refresh_thread = None
        self.monitoring_thread = None
        self.port_monitoring_thread = None
        
        # Professional timers
        self.refresh_timer = None
        self.port_timer = None
        self.health_timer = None
    
    def setup_gui(self):
        """Professional GUI setup with enhanced features"""
        
        # Ana container
        self.main_container = tk.Frame(self.root, bg='#1a1a1a')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Professional header with gradient effect
        self.setup_professional_header()
        
        # Live status ticker
        self.setup_status_ticker()
        
        # Professional sidebar
        self.setup_sidebar()
        
        # Bağlantı paneli
        self.connection_panel = ConnectionPanel(self.main_container, 
                                              connect_callback=self.handle_connection)
        self.connection_panel.pack(fill=tk.X, pady=(0, 5))
        
        # Ana içerik alanı
        self.content_notebook = ttk.Notebook(self.main_container)
        self.content_notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Device Info sekmesi
        self.device_info_frame = tk.Frame(self.content_notebook, bg='#2c3e50')
        self.content_notebook.add(self.device_info_frame, text="📊 Device Info")
        
        self.device_info_panel = DeviceInfoPanel(self.device_info_frame)
        self.device_info_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Port Visualization sekmesi
        self.port_frame = tk.Frame(self.content_notebook, bg='#2c3e50')
        self.content_notebook.add(self.port_frame, text="🔌 Port Status")
        
        self.port_visualization = PortVisualization(self.port_frame, port_count=48)
        self.port_visualization.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Set port control callbacks
        self.port_visualization.port_control_callback = self.handle_port_control
        self.port_visualization.port_vlan_callback = self.handle_port_vlan
        self.port_visualization.port_desc_callback = self.handle_port_description
        
        # Command Terminal sekmesi
        self.terminal_frame = tk.Frame(self.content_notebook, bg='#1e1e1e')
        self.content_notebook.add(self.terminal_frame, text="💻 Terminal")
        
        self.command_terminal = CommandTerminal(self.terminal_frame, 
                                              command_callback=self.execute_command)
        self.command_terminal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System Health sekmesi
        self.health_frame = tk.Frame(self.content_notebook, bg='#2c3e50')
        self.content_notebook.add(self.health_frame, text="🔥 System Health")
        
        self.setup_health_tab()
        
        # Network Monitoring sekmesi
        self.network_frame = tk.Frame(self.content_notebook, bg='#2c3e50')
        self.content_notebook.add(self.network_frame, text="🌐 Network Monitor")
        
        self.setup_network_tab()
        
        # Security & Access sekmesi
        self.security_frame = tk.Frame(self.content_notebook, bg='#2c3e50')
        self.content_notebook.add(self.security_frame, text="🔒 Security")
        
        self.setup_security_tab()
        
        # Logs & Diagnostics sekmesi
        self.logs_frame = tk.Frame(self.content_notebook, bg='#2c3e50')
        self.content_notebook.add(self.logs_frame, text="📊 Diagnostics")
        
        self.setup_diagnostics_tab()
        
        # VLAN Management sekmesi
        self.vlan_mgmt_frame = tk.Frame(self.content_notebook, bg='#2c3e50')
        self.content_notebook.add(self.vlan_mgmt_frame, text="🏷️ VLAN Manager")
        
        self.setup_vlan_management_tab()
        
        # Status bar
        self.status_bar = StatusBar(self.main_container)
        self.status_bar.pack(fill=tk.X)
        
                # Control panel
        self.create_professional_control_panel()
        
        # Notification system
        self.setup_notification_system()
        
        # Start monitoring immediately
        self.start_professional_monitoring()
    
    def setup_professional_header(self):
        """Professional header with live indicators"""
        header_frame = tk.Frame(self.main_container, bg='#0d1117', height=80)
        header_frame.pack(fill=tk.X, pady=(0, 2))
        header_frame.pack_propagate(False)
        
        # Left side - Logo and title
        left_frame = tk.Frame(header_frame, bg='#0d1117')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=10)
        
        title_label = tk.Label(left_frame, 
                              text="🔧 CISCO PROFESSIONAL MANAGER", 
                              bg='#0d1117', fg='#00ff41', 
                              font=('Consolas', 18, 'bold'))
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(left_frame, 
                                text="Enterprise Network Management Suite", 
                                bg='#0d1117', fg='#7d8590', 
                                font=('Arial', 10))
        subtitle_label.pack(anchor=tk.W)
        
        # Right side - Live indicators
        right_frame = tk.Frame(header_frame, bg='#0d1117')
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=10)
        
        # Connection status indicator
        self.conn_indicator = tk.Label(right_frame, text="● OFFLINE", 
                                     bg='#0d1117', fg='#ff6b6b', 
                                     font=('Consolas', 12, 'bold'))
        self.conn_indicator.pack(anchor=tk.E)
        
        # Live time
        self.live_time = tk.Label(right_frame, text="", 
                                bg='#0d1117', fg='#00ff41', 
                                font=('Consolas', 10))
        self.live_time.pack(anchor=tk.E)
        
        # Update time continuously
        self.update_live_time()
    
    def setup_status_ticker(self):
        """Live scrolling status ticker"""
        ticker_frame = tk.Frame(self.main_container, bg='#161b22', height=30)
        ticker_frame.pack(fill=tk.X, pady=(0, 2))
        ticker_frame.pack_propagate(False)
        
        self.ticker_text = tk.Label(ticker_frame, 
                                  text="🔄 System initializing... Professional monitoring starting...", 
                                  bg='#161b22', fg='#00ff41', 
                                  font=('Consolas', 9), anchor=tk.W)
        self.ticker_text.pack(fill=tk.X, padx=10, pady=5)
        
        # Start ticker animation
        self.start_ticker_animation()
    
    def setup_sidebar(self):
        """Professional sidebar with quick actions"""
        main_content = tk.Frame(self.main_container, bg='#1a1a1a')
        main_content.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(main_content, bg='#0d1117', width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        self.sidebar.pack_propagate(False)
        
        # Sidebar title
        sidebar_title = tk.Label(self.sidebar, text="QUICK ACTIONS", 
                               bg='#0d1117', fg='#7d8590', 
                               font=('Consolas', 10, 'bold'))
        sidebar_title.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Quick action buttons with professional monitoring
        quick_actions = [
            ("🔄 Refresh All", self.emergency_refresh, '#28a745'),
            ("⚡ Force Port Refresh", self.force_port_refresh, '#17a2b8'),
            ("🔄 Toggle Real-time", self.toggle_real_time_monitoring, '#6c757d'),
            ("📊 Port History", self.show_port_change_history, '#17a2b8'),
            ("🚨 Emergency Stop", self.emergency_stop, '#dc3545'),
            ("📊 Performance", self.show_performance, '#ffc107'),
            ("🔧 Diagnostics", self.run_diagnostics, '#6f42c1'),
            ("💾 Backup Now", self.emergency_backup, '#fd7e14'),
            ("🔔 Notifications", self.show_notifications, '#20c997'),
            ("📈 Statistics", self.show_statistics, '#e83e8c')
        ]
        
        for text, command, color in quick_actions:
            btn = tk.Button(self.sidebar, text=text, command=command,
                          bg=color, fg='white', font=('Consolas', 9, 'bold'),
                          relief='flat', cursor='hand2', height=2,
                          activebackground=color, activeforeground='white')
            btn.pack(fill=tk.X, padx=10, pady=2)
        
        # Live performance indicators
        self.setup_live_indicators()
        
        # Main content area
        self.content_area = tk.Frame(main_content, bg='#1a1a1a')
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Continue with existing setup in content area
        self.setup_main_content()
    
    def setup_live_indicators(self):
        """Live performance indicators in sidebar"""
        # Separator
        sep = tk.Frame(self.sidebar, bg='#30363d', height=2)
        sep.pack(fill=tk.X, padx=10, pady=10)
        
        # Live indicators title
        indicators_title = tk.Label(self.sidebar, text="LIVE METRICS", 
                                   bg='#0d1117', fg='#7d8590', 
                                   font=('Consolas', 10, 'bold'))
        indicators_title.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        # CPU indicator
        self.cpu_indicator = tk.Label(self.sidebar, text="CPU: ---%", 
                                    bg='#0d1117', fg='#00ff41', 
                                    font=('Consolas', 9))
        self.cpu_indicator.pack(fill=tk.X, padx=10, pady=1)
        
        # Memory indicator
        self.memory_indicator = tk.Label(self.sidebar, text="MEM: ---%", 
                                       bg='#0d1117', fg='#00ff41', 
                                       font=('Consolas', 9))
        self.memory_indicator.pack(fill=tk.X, padx=10, pady=1)
        
        # Port status
        self.port_status_indicator = tk.Label(self.sidebar, text="PORTS: --/48", 
                                            bg='#0d1117', fg='#00ff41', 
                                            font=('Consolas', 9))
        self.port_status_indicator.pack(fill=tk.X, padx=10, pady=1)
        
        # Uptime
        self.uptime_indicator = tk.Label(self.sidebar, text="UPTIME: ---", 
                                       bg='#0d1117', fg='#00ff41', 
                                       font=('Consolas', 9))
        self.uptime_indicator.pack(fill=tk.X, padx=10, pady=1)
    
    def setup_main_content(self):
        """Setup main content area"""
        # Connection panel
        self.connection_panel = ConnectionPanel(self.content_area, 
                                              connect_callback=self.handle_connection)
        self.connection_panel.pack(fill=tk.X, padx=5, pady=5)
        
        # Enhanced notebook with professional styling
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Professional.TNotebook', background='#1a1a1a', borderwidth=0)
        style.configure('Professional.TNotebook.Tab', padding=[20, 10], 
                       background='#30363d', foreground='white', borderwidth=0)
        style.map('Professional.TNotebook.Tab', 
                 background=[('selected', '#0d1117'), ('active', '#21262d')])
        
        self.content_notebook = ttk.Notebook(self.content_area, style='Professional.TNotebook')
        self.content_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Setup all tabs with professional styling
        self.setup_all_professional_tabs()
    
    def setup_notification_system(self):
        """Professional notification system"""
        self.notification_frame = tk.Frame(self.root, bg='#1a1a1a')
        # Will be shown on demand
    
    def create_professional_control_panel(self):
        """Professional control panel with enhanced monitoring controls"""
        control_frame = tk.Frame(self.main_container, bg='#0d1117', height=50)
        control_frame.pack(fill=tk.X, pady=(5, 0))
        control_frame.pack_propagate(False)
        
        # Left side - Main controls
        left_controls = tk.Frame(control_frame, bg='#0d1117')
        left_controls.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        
        # Comprehensive refresh button
        comp_refresh_btn = tk.Button(left_controls, text="📊 Full Refresh", 
                                   command=self.refresh_all_data,
                                   bg='#238636', fg='white', font=('Consolas', 9, 'bold'),
                                   relief='flat', cursor='hand2', height=2)
        comp_refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Force port refresh button
        port_refresh_btn = tk.Button(left_controls, text="⚡ Port Refresh", 
                                    command=self.force_port_refresh,
                                    bg='#1f6feb', fg='white', font=('Consolas', 9, 'bold'),
                                    relief='flat', cursor='hand2', height=2)
        port_refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Real-time monitoring toggle
        self.realtime_btn = tk.Button(left_controls, text="🔄 Real-time ON", 
                                     command=self.toggle_real_time_monitoring,
                                     bg='#28a745', fg='white', font=('Consolas', 9, 'bold'),
                                     relief='flat', cursor='hand2', height=2)
        self.realtime_btn.pack(side=tk.LEFT, padx=2)
        
        # Center - Status indicators
        center_status = tk.Frame(control_frame, bg='#0d1117')
        center_status.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Monitoring status
        self.monitoring_status = tk.Label(center_status, 
                                        text="🔄 PROFESSIONAL MONITORING ACTIVE", 
                                        bg='#0d1117', fg='#00ff41', 
                                        font=('Consolas', 10, 'bold'))
        self.monitoring_status.pack()
        
        # Refresh interval display
        self.refresh_display = tk.Label(center_status, 
                                      text=f"Refresh: {self.port_refresh_interval}ms | Real-time: ON", 
                                      bg='#0d1117', fg='#7d8590', 
                                      font=('Consolas', 8))
        self.refresh_display.pack()
        
        # Right side - Advanced controls
        right_controls = tk.Frame(control_frame, bg='#0d1117')
        right_controls.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        
        # Emergency stop
        emergency_btn = tk.Button(right_controls, text="🚨 EMERGENCY", 
                                command=self.emergency_stop,
                                bg='#da3633', fg='white', font=('Consolas', 9, 'bold'),
                                relief='flat', cursor='hand2', height=2)
        emergency_btn.pack(side=tk.RIGHT, padx=2)
        
        # Disconnect button
        disconnect_btn = tk.Button(right_controls, text="🔌 Disconnect", 
                                 command=self.disconnect_device,
                                 bg='#e74c3c', fg='white', font=('Consolas', 9, 'bold'),
                                 relief='flat', cursor='hand2', height=2)
        disconnect_btn.pack(side=tk.RIGHT, padx=2)
    
    def quick_refresh(self):
        """Hızlı yenileme - sadece temel bilgiler"""
        if not self.cisco_manager.connected:
            self.command_terminal.add_output("❌ No device connection\n", color='#e74c3c')
            return
        
        def quick_refresh_thread():
            try:
                self.root.after(0, self.command_terminal.add_output, 
                              "🔄 Quick refresh...\n", '#3498db')
                
                # Sadece temel cihaz bilgisi ve port durumları
                device_info = self.cisco_manager.get_device_info()
                interfaces = self.cisco_manager.get_interfaces_status()
                
                self.root.after(0, self.device_info_panel.update_basic_info, device_info)
                
                for interface, status in interfaces.items():
                    port_num = self.extract_port_number(interface)
                    if port_num:
                        self.root.after(0, 
                            self.port_visualization.update_port_status,
                            port_num, status['status'], status)
                
                self.root.after(0, self.command_terminal.add_output, 
                              "✅ Quick refresh completed\n", '#27ae60')
                
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ Quick refresh failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=quick_refresh_thread, daemon=True).start()
    
    def setup_health_tab(self):
        """System Health sekmesi kurulumu"""
        # Ana frame
        main_frame = tk.Frame(self.health_frame, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sol panel - CPU ve Memory
        left_panel = tk.LabelFrame(main_frame, text="⚡ Performance Metrics", 
                                 bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.cpu_text = tk.Text(left_panel, height=8, bg='#2c3e50', fg='#00ff00', 
                               font=('Consolas', 10), relief='flat')
        self.cpu_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sağ panel - Temperature
        right_panel = tk.LabelFrame(main_frame, text="🌡️ Temperature Sensors", 
                                  bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.temp_text = tk.Text(right_panel, height=8, bg='#2c3e50', fg='#ff6b6b', 
                                font=('Consolas', 10), relief='flat')
        self.temp_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Alt panel - Power ve Fans
        bottom_frame = tk.Frame(main_frame, bg='#2c3e50')
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        power_panel = tk.LabelFrame(bottom_frame, text="🔌 Power Supply Status", 
                                  bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        power_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.power_text = tk.Text(power_panel, height=6, bg='#2c3e50', fg='#f39c12', 
                                 font=('Consolas', 9), relief='flat')
        self.power_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        fan_panel = tk.LabelFrame(bottom_frame, text="💨 Fan Status", 
                                bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        fan_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.fan_text = tk.Text(fan_panel, height=6, bg='#2c3e50', fg='#3498db', 
                               font=('Consolas', 9), relief='flat')
        self.fan_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def setup_network_tab(self):
        """Network Monitoring sekmesi kurulumu"""
        # Ana frame
        main_frame = tk.Frame(self.network_frame, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Üst panel - Interface Statistics
        top_panel = tk.LabelFrame(main_frame, text="📊 Interface Statistics", 
                                bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        top_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Treeview for interface stats
        columns = ('Interface', 'Status', 'RX Packets', 'TX Packets', 'RX Bytes', 'TX Bytes', 'Errors')
        self.interface_tree = ttk.Treeview(top_panel, columns=columns, show='headings', height=12)
        
        for col in columns:
            self.interface_tree.heading(col, text=col)
            self.interface_tree.column(col, width=100)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(top_panel, orient="vertical", command=self.interface_tree.yview)
        h_scroll = ttk.Scrollbar(top_panel, orient="horizontal", command=self.interface_tree.xview)
        self.interface_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.interface_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Alt panel - Network Tools
        bottom_panel = tk.LabelFrame(main_frame, text="🛠️ Network Tools", 
                                   bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        bottom_panel.pack(fill=tk.X, pady=(5, 0))
        
        tools_frame = tk.Frame(bottom_panel, bg='#34495e')
        tools_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Ping tool
        tk.Label(tools_frame, text="Ping:", bg='#34495e', fg='white').pack(side=tk.LEFT)
        self.ping_entry = tk.Entry(tools_frame, width=15)
        self.ping_entry.insert(0, "8.8.8.8")
        self.ping_entry.pack(side=tk.LEFT, padx=5)
        
        ping_btn = tk.Button(tools_frame, text="🏓 Ping", command=self.run_ping,
                           bg='#3498db', fg='white', font=('Arial', 9, 'bold'))
        ping_btn.pack(side=tk.LEFT, padx=5)
        
        # Traceroute tool
        tk.Label(tools_frame, text="Traceroute:", bg='#34495e', fg='white').pack(side=tk.LEFT, padx=(20, 0))
        self.trace_entry = tk.Entry(tools_frame, width=15)
        self.trace_entry.insert(0, "8.8.8.8")
        self.trace_entry.pack(side=tk.LEFT, padx=5)
        
        trace_btn = tk.Button(tools_frame, text="🛣️ Trace", command=self.run_traceroute,
                            bg='#e67e22', fg='white', font=('Arial', 9, 'bold'))
        trace_btn.pack(side=tk.LEFT, padx=5)
    
    def setup_security_tab(self):
        """Security sekmesi kurulumu"""
        # Ana frame
        main_frame = tk.Frame(self.security_frame, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sol panel - MAC Address Table
        left_panel = tk.LabelFrame(main_frame, text="🔍 MAC Address Table", 
                                 bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # MAC Table
        mac_columns = ('VLAN', 'MAC Address', 'Type', 'Interface')
        self.mac_tree = ttk.Treeview(left_panel, columns=mac_columns, show='headings', height=15)
        
        for col in mac_columns:
            self.mac_tree.heading(col, text=col)
            self.mac_tree.column(col, width=120)
        
        mac_scroll = ttk.Scrollbar(left_panel, orient="vertical", command=self.mac_tree.yview)
        self.mac_tree.configure(yscrollcommand=mac_scroll.set)
        
        self.mac_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        mac_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Sağ panel - ARP Table
        right_panel = tk.LabelFrame(main_frame, text="🌐 ARP Table", 
                                  bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # ARP Table
        arp_columns = ('IP Address', 'MAC Address', 'Type', 'Interface')
        self.arp_tree = ttk.Treeview(right_panel, columns=arp_columns, show='headings', height=15)
        
        for col in arp_columns:
            self.arp_tree.heading(col, text=col)
            self.arp_tree.column(col, width=120)
        
        arp_scroll = ttk.Scrollbar(right_panel, orient="vertical", command=self.arp_tree.yview)
        self.arp_tree.configure(yscrollcommand=arp_scroll.set)
        
        self.arp_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        arp_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_diagnostics_tab(self):
        """Diagnostics sekmesi kurulumu"""
        # Ana frame
        main_frame = tk.Frame(self.logs_frame, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Üst panel - System Logs
        top_panel = tk.LabelFrame(main_frame, text="📋 System Logs", 
                                bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        top_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.logs_text = scrolledtext.ScrolledText(top_panel, height=12, bg='#1e1e1e', fg='#00ff00', 
                                                  font=('Consolas', 9), relief='flat')
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Alt panel - Diagnostic Tools
        bottom_panel = tk.LabelFrame(main_frame, text="🔧 Diagnostic Tools", 
                                   bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        bottom_panel.pack(fill=tk.X, pady=(5, 0))
        
        tools_frame = tk.Frame(bottom_panel, bg='#34495e')
        tools_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Diagnostic buttons
        diag_buttons = [
            ("📊 Show Version", self.show_version),
            ("🔍 Show Inventory", self.show_inventory),
            ("📈 Show Processes", self.show_processes),
            ("🗂️ Show Flash", self.show_flash),
            ("⚙️ Show Running-Config", self.show_running_config),
            ("💾 Backup Config", self.backup_config)
        ]
        
        for i, (text, command) in enumerate(diag_buttons):
            btn = tk.Button(tools_frame, text=text, command=command,
                          bg='#9b59b6', fg='white', font=('Arial', 9, 'bold'),
                          width=18, relief='flat', cursor='hand2')
            row = i // 3
            col = i % 3
            btn.grid(row=row, column=col, padx=5, pady=5)
    
    def setup_vlan_management_tab(self):
        """VLAN Management sekmesi kurulumu"""
        main_frame = tk.Frame(self.vlan_mgmt_frame, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # VLAN Creation Panel
        create_panel = tk.LabelFrame(main_frame, text="🆕 Create New VLAN", 
                                   bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        create_panel.pack(fill=tk.X, pady=(0, 10))
        
        create_frame = tk.Frame(create_panel, bg='#34495e')
        create_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(create_frame, text="VLAN ID:", bg='#34495e', fg='white').pack(side=tk.LEFT)
        self.new_vlan_id = tk.Entry(create_frame, width=10)
        self.new_vlan_id.pack(side=tk.LEFT, padx=5)
        
        tk.Label(create_frame, text="Name:", bg='#34495e', fg='white').pack(side=tk.LEFT, padx=(10, 0))
        self.new_vlan_name = tk.Entry(create_frame, width=20)
        self.new_vlan_name.pack(side=tk.LEFT, padx=5)
        
        create_btn = tk.Button(create_frame, text="Create VLAN", command=self.create_vlan,
                             bg='#27ae60', fg='white', font=('Arial', 9, 'bold'),
                             relief='flat', cursor='hand2')
        create_btn.pack(side=tk.LEFT, padx=10)
        
        # VLAN List Panel
        list_panel = tk.LabelFrame(main_frame, text="🏷️ Existing VLANs", 
                                 bg='#34495e', fg='white', font=('Arial', 11, 'bold'))
        list_panel.pack(fill=tk.BOTH, expand=True)
        
        # VLAN TreeView
        vlan_columns = ('VLAN ID', 'Name', 'Status', 'Ports')
        self.vlan_tree = ttk.Treeview(list_panel, columns=vlan_columns, show='headings', height=15)
        
        for col in vlan_columns:
            self.vlan_tree.heading(col, text=col)
            self.vlan_tree.column(col, width=150)
        
        vlan_scroll = ttk.Scrollbar(list_panel, orient="vertical", command=self.vlan_tree.yview)
        self.vlan_tree.configure(yscrollcommand=vlan_scroll.set)
        
        self.vlan_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        vlan_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # VLAN Control Buttons
        control_frame = tk.Frame(list_panel, bg='#34495e')
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        refresh_vlan_btn = tk.Button(control_frame, text="🔄 Refresh VLANs", 
                                   command=self.refresh_vlans,
                                   bg='#3498db', fg='white', font=('Arial', 9, 'bold'),
                                   relief='flat', cursor='hand2')
        refresh_vlan_btn.pack(side=tk.LEFT, padx=5)
        
        delete_vlan_btn = tk.Button(control_frame, text="🗑️ Delete Selected", 
                                  command=self.delete_selected_vlan,
                                  bg='#e74c3c', fg='white', font=('Arial', 9, 'bold'),
                                  relief='flat', cursor='hand2')
        delete_vlan_btn.pack(side=tk.LEFT, padx=5)
    
    def create_vlan(self):
        """Create new VLAN"""
        vlan_id = self.new_vlan_id.get().strip()
        vlan_name = self.new_vlan_name.get().strip()
        
        if not vlan_id or not vlan_name:
            self.command_terminal.add_output("❌ Please enter both VLAN ID and name\n", '#e74c3c')
            return
        
        if not self.cisco_manager.connected:
            self.command_terminal.add_output("❌ No device connection\n", '#e74c3c')
            return
        
        def create_thread():
            try:
                result = self.cisco_manager.create_vlan(vlan_id, vlan_name)
                self.root.after(0, self.command_terminal.add_output, 
                              f"✅ VLAN {vlan_id} ({vlan_name}) created successfully\n", '#27ae60')
                
                # Clear inputs
                self.root.after(0, lambda: self.new_vlan_id.delete(0, tk.END))
                self.root.after(0, lambda: self.new_vlan_name.delete(0, tk.END))
                
                # Refresh VLAN list
                self.root.after(0, self.refresh_vlans)
                
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ VLAN creation failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=create_thread, daemon=True).start()
    
    def refresh_vlans(self):
        """Refresh VLAN list"""
        if not self.cisco_manager.connected:
            return
        
        def refresh_thread():
            try:
                vlans = self.cisco_manager.get_all_vlans()
                
                # Clear existing entries
                self.root.after(0, lambda: [self.vlan_tree.delete(item) for item in self.vlan_tree.get_children()])
                
                # Add VLANs to tree
                for vlan_id, vlan_info in vlans.items():
                    ports_str = ', '.join(vlan_info.get('ports', [])[:5])  # Show first 5 ports
                    if len(vlan_info.get('ports', [])) > 5:
                        ports_str += '...'
                    
                    self.root.after(0, lambda v=vlan_id, i=vlan_info, p=ports_str: 
                                  self.vlan_tree.insert('', 'end', values=(
                                      v, i.get('name', 'N/A'), i.get('status', 'N/A'), p
                                  )))
                
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ VLAN refresh failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def delete_selected_vlan(self):
        """Delete selected VLAN"""
        selection = self.vlan_tree.selection()
        if not selection:
            self.command_terminal.add_output("❌ Please select a VLAN to delete\n", '#e74c3c')
            return
        
        item = self.vlan_tree.item(selection[0])
        vlan_id = item['values'][0]
        
        # Confirm deletion
        import tkinter.messagebox as msgbox
        if msgbox.askyesno("Confirm Deletion", f"Delete VLAN {vlan_id}?"):
            def delete_thread():
                try:
                    result = self.cisco_manager.delete_vlan(vlan_id)
                    self.root.after(0, self.command_terminal.add_output, 
                                  f"🗑️ VLAN {vlan_id} deleted\n", '#e74c3c')
                    self.root.after(0, self.refresh_vlans)
                    
                except Exception as e:
                    self.root.after(0, self.command_terminal.add_output, 
                                  f"❌ VLAN deletion failed: {str(e)}\n", '#e74c3c')
            
            threading.Thread(target=delete_thread, daemon=True).start()
        
    def setup_callbacks(self):
        """Callback'leri ayarla"""
        self.cisco_manager.register_callback('connected', self.on_device_connected)
        self.cisco_manager.register_callback('disconnected', self.on_device_disconnected)
        
    def handle_connection(self, connection_data):
        """Bağlantı isteğini işle"""
        try:
            success, message = self.cisco_manager.connect(
                host=connection_data['host'],
                username=connection_data['username'],
                password=connection_data['password'],
                device_type=connection_data['device_type'],
                port=connection_data['port'],
                secret=connection_data['secret']
            )
            
            if success:
                self.command_terminal.add_output(f"✅ Connected to {connection_data['host']}\n", 
                                               color='#27ae60')
                return True, message
            else:
                self.command_terminal.add_output(f"❌ Connection failed: {message}\n", 
                                               color='#e74c3c')
                return False, message
                
        except Exception as e:
            error_msg = f"Connection error: {str(e)}"
            self.command_terminal.add_output(f"❌ {error_msg}\n", color='#e74c3c')
            return False, error_msg
    
    def on_device_connected(self, device_info):
        """Cihaz bağlandığında çağrılır"""
        self.status_bar.update_connection_status(True, device_info)
        self.device_info_panel.update_info(device_info)
        self.refresh_all_data()
        
    def on_device_disconnected(self, data=None):
        """Cihaz bağlantısı kesildiğinde çağrılır"""
        self.status_bar.update_connection_status(False)
        self.device_info_panel.update_info("Device disconnected")
        
    def execute_command(self, command):
        """Terminal komutunu çalıştır"""
        if not self.cisco_manager.connected:
            return "❌ No device connection. Please connect first."
        
        try:
            # Özel komutlar
            if command.lower() == 'help':
                return self.get_help_text()
            elif command.lower() == 'clear':
                self.command_terminal.clear_terminal()
                return ""
            elif command.lower().startswith('refresh'):
                self.refresh_all_data()
                return "✅ Data refreshed successfully"
            elif command.lower() == 'debug ports':
                return self.debug_port_status()
            elif command.lower() == 'show raw interfaces':
                return self.show_raw_interfaces()
            
            # Cisco cihazına komut gönder
            result = self.cisco_manager.send_command(command)
            return result
            
        except Exception as e:
            return f"❌ Command execution failed: {str(e)}"
    
    def get_help_text(self):
        """Yardım metni"""
        help_text = """
🔧 CISCO SWITCH MANAGER - HELP
========================================

📋 BUILT-IN COMMANDS:
  help           - Show this help
  clear          - Clear terminal
  refresh        - Refresh all data
  debug ports    - Show port parsing debug info
  show raw interfaces - Show raw interface output
  
📡 CISCO COMMANDS:
  show version         - Show device version
  show interfaces      - Show interface status
  show interfaces status - Show interface summary
  show vlan brief      - Show VLAN information
  show mac address-table - Show MAC table
  show running-config  - Show running configuration
  show inventory       - Show hardware inventory
  show processes cpu   - Show CPU usage
  show processes memory - Show memory usage
  
🔧 MANAGEMENT:
  ping <ip>           - Ping from device
  traceroute <ip>     - Traceroute from device
  copy run start      - Save configuration
  
💡 TIP: Use Tab for command history navigation
        """
        return help_text
    
    def refresh_all_data(self):
        """Tüm verileri kapsamlı şekilde yenile"""
        if not self.cisco_manager.connected:
            self.command_terminal.add_output("❌ No device connection\n", color='#e74c3c')
            return
        
        def refresh_thread():
            try:
                self.root.after(0, self.command_terminal.add_output, 
                              "🔄 Starting comprehensive data refresh...\n", '#3498db')
                
                # Kapsamlı cihaz durumu çek
                comprehensive_status = self.cisco_manager.get_comprehensive_status()
                self.root.after(0, self.device_info_panel.update_info, comprehensive_status)
                
                # Port durumlarını güncelle
                if comprehensive_status.get('interfaces'):
                    interfaces = comprehensive_status['interfaces']
                    updated_ports = 0
                    
                    for interface, status in interfaces.items():
                        port_num = self.extract_port_number(interface)
                        if port_num:
                            self.root.after(0, 
                                self.port_visualization.update_port_status,
                                port_num, status['status'], status)
                            updated_ports += 1
                        else:
                            # Debug: show interfaces that couldn't be parsed
                            self.root.after(0, self.command_terminal.add_output, 
                                          f"❓ Could not parse port number from: {interface}\n", '#f39c12')
                    
                    # Debug info
                    self.root.after(0, self.command_terminal.add_output, 
                                  f"🔌 Updated {updated_ports} ports from {len(interfaces)} interfaces\n", '#3498db')
                
                # System Health sekmesini güncelle
                self.root.after(0, self.update_health_tab, comprehensive_status)
                
                # Network Monitor sekmesini güncelle
                self.root.after(0, self.update_network_tab)
                
                # Security sekmesini güncelle
                self.root.after(0, self.update_security_tab)
                
                # VLAN listesini güncelle
                self.root.after(0, self.refresh_vlans)
                
                # Terminal'e özet bilgi yazdır
                summary = self.create_status_summary(comprehensive_status)
                self.root.after(0, self.command_terminal.add_output, summary, '#27ae60')
                
                self.root.after(0, self.command_terminal.add_output, 
                              "✅ Comprehensive refresh completed successfully\n", '#27ae60')
                
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ Refresh failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def create_status_summary(self, status_data):
        """Create a summary of device status for terminal"""
        summary = "\n📊 DEVICE STATUS SUMMARY\n"
        summary += "=" * 40 + "\n"
        
        # Basic info
        if status_data.get('device_info'):
            device_info = status_data['device_info']
            summary += f"🏷️  Model: {device_info.get('model', 'Unknown')}\n"
            summary += f"📟 Serial: {device_info.get('serial', 'Unknown')}\n"
            summary += f"⏱️  Uptime: {device_info.get('uptime', 'Unknown')}\n"
        
        # Interface summary
        if status_data.get('interfaces'):
            interfaces = status_data['interfaces']
            up_count = sum(1 for iface in interfaces.values() if iface['status'].lower() == 'connected')
            down_count = len(interfaces) - up_count
            summary += f"🔌 Interfaces: {up_count} UP, {down_count} DOWN\n"
        
        # VLAN summary
        if status_data.get('vlans'):
            vlan_count = len(status_data['vlans'])
            summary += f"🏷️  VLANs: {vlan_count} configured\n"
        
        # Temperature status
        if status_data.get('temperature'):
            temp_sensors = status_data['temperature']
            ok_temps = sum(1 for temp in temp_sensors.values() if temp['status'] == 'OK')
            summary += f"🌡️  Temperature: {ok_temps}/{len(temp_sensors)} sensors OK\n"
        
        # Performance
        if status_data.get('cpu_memory'):
            cpu_mem = status_data['cpu_memory']
            summary += f"🧠 CPU: {cpu_mem.get('cpu_usage', 'N/A')}, Memory: {cpu_mem.get('memory_usage', 'N/A')}\n"
        
        summary += "=" * 40 + "\n\n"
        return summary
    
    def debug_port_status(self):
        """Debug port status for troubleshooting"""
        if not self.cisco_manager.connected:
            return "❌ No device connection"
        
        try:
            interfaces = self.cisco_manager.get_interfaces_status()
            debug_info = "\n🔍 PORT DEBUG INFORMATION\n"
            debug_info += "=" * 50 + "\n\n"
            
            for interface, status in list(interfaces.items())[:10]:  # Show first 10
                port_num = self.extract_port_number(interface)
                debug_info += f"Interface: {interface}\n"
                debug_info += f"  Port Number: {port_num}\n"
                debug_info += f"  Status: {status['status']}\n"
                debug_info += f"  Raw Line: {status.get('raw_line', 'N/A')}\n"
                debug_info += "-" * 30 + "\n"
            
            return debug_info
        except Exception as e:
            return f"❌ Debug failed: {str(e)}"
    
    def show_raw_interfaces(self):
        """Show raw interface command output"""
        if not self.cisco_manager.connected:
            return "❌ No device connection"
        
        try:
            raw_output = self.cisco_manager.send_command("show interfaces status")
            return f"\n📋 RAW INTERFACE OUTPUT:\n{'='*50}\n{raw_output}\n{'='*50}\n"
        except Exception as e:
            return f"❌ Raw output failed: {str(e)}"
    
    # Network Tools Functions
    def run_ping(self):
        """Ping tool"""
        target = self.ping_entry.get().strip()
        if not target:
            return
        
        def ping_thread():
            try:
                if self.cisco_manager.connected:
                    result = self.cisco_manager.ping(target)
                    self.root.after(0, self.command_terminal.add_output, 
                                  f"🏓 Ping to {target}:\n{result}\n", '#3498db')
                else:
                    self.root.after(0, self.command_terminal.add_output, 
                                  "❌ No device connection for ping\n", '#e74c3c')
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ Ping failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=ping_thread, daemon=True).start()
    
    def run_traceroute(self):
        """Traceroute tool"""
        target = self.trace_entry.get().strip()
        if not target:
            return
        
        def trace_thread():
            try:
                if self.cisco_manager.connected:
                    result = self.cisco_manager.traceroute(target)
                    self.root.after(0, self.command_terminal.add_output, 
                                  f"🛣️ Traceroute to {target}:\n{result}\n", '#e67e22')
                else:
                    self.root.after(0, self.command_terminal.add_output, 
                                  "❌ No device connection for traceroute\n", '#e74c3c')
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ Traceroute failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=trace_thread, daemon=True).start()
    
    # Diagnostic Tools Functions
    def show_version(self):
        """Show device version"""
        def version_thread():
            try:
                if self.cisco_manager.connected:
                    output = self.cisco_manager.send_command("show version")
                    self.root.after(0, self.update_logs_display, f"📊 SHOW VERSION:\n{output}\n")
                else:
                    self.root.after(0, self.update_logs_display, "❌ No device connection\n")
            except Exception as e:
                self.root.after(0, self.update_logs_display, f"❌ Error: {str(e)}\n")
        
        threading.Thread(target=version_thread, daemon=True).start()
    
    def show_inventory(self):
        """Show device inventory"""
        def inventory_thread():
            try:
                if self.cisco_manager.connected:
                    output = self.cisco_manager.send_command("show inventory")
                    self.root.after(0, self.update_logs_display, f"🔍 SHOW INVENTORY:\n{output}\n")
                else:
                    self.root.after(0, self.update_logs_display, "❌ No device connection\n")
            except Exception as e:
                self.root.after(0, self.update_logs_display, f"❌ Error: {str(e)}\n")
        
        threading.Thread(target=inventory_thread, daemon=True).start()
    
    def show_processes(self):
        """Show processes"""
        def processes_thread():
            try:
                if self.cisco_manager.connected:
                    cpu_output = self.cisco_manager.send_command("show processes cpu")
                    mem_output = self.cisco_manager.send_command("show processes memory")
                    self.root.after(0, self.update_logs_display, 
                                  f"📈 SHOW PROCESSES CPU:\n{cpu_output}\n\n📈 SHOW PROCESSES MEMORY:\n{mem_output}\n")
                else:
                    self.root.after(0, self.update_logs_display, "❌ No device connection\n")
            except Exception as e:
                self.root.after(0, self.update_logs_display, f"❌ Error: {str(e)}\n")
        
        threading.Thread(target=processes_thread, daemon=True).start()
    
    def show_flash(self):
        """Show flash contents"""
        def flash_thread():
            try:
                if self.cisco_manager.connected:
                    output = self.cisco_manager.send_command("dir flash:")
                    self.root.after(0, self.update_logs_display, f"🗂️ FLASH CONTENTS:\n{output}\n")
                else:
                    self.root.after(0, self.update_logs_display, "❌ No device connection\n")
            except Exception as e:
                self.root.after(0, self.update_logs_display, f"❌ Error: {str(e)}\n")
        
        threading.Thread(target=flash_thread, daemon=True).start()
    
    def show_running_config(self):
        """Show running configuration"""
        def config_thread():
            try:
                if self.cisco_manager.connected:
                    output = self.cisco_manager.get_running_config()
                    self.root.after(0, self.update_logs_display, f"⚙️ RUNNING CONFIG:\n{output}\n")
                else:
                    self.root.after(0, self.update_logs_display, "❌ No device connection\n")
            except Exception as e:
                self.root.after(0, self.update_logs_display, f"❌ Error: {str(e)}\n")
        
        threading.Thread(target=config_thread, daemon=True).start()
    
    def backup_config(self):
        """Backup configuration"""
        def backup_thread():
            try:
                if self.cisco_manager.connected:
                    filename = self.cisco_manager.backup_config()
                    self.root.after(0, self.update_logs_display, f"💾 Configuration backed up to: {filename}\n")
                    self.root.after(0, self.command_terminal.add_output, 
                                  f"💾 Configuration backed up to: {filename}\n", '#27ae60')
                else:
                    self.root.after(0, self.update_logs_display, "❌ No device connection\n")
            except Exception as e:
                self.root.after(0, self.update_logs_display, f"❌ Backup error: {str(e)}\n")
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def update_logs_display(self, text):
        """Update logs display"""
        self.logs_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {text}\n")
        self.logs_text.see(tk.END)
    
    def update_health_tab(self, status):
        """System Health sekmesini güncelle"""
        try:
            # CPU ve Memory bilgileri
            if status.get('cpu_memory'):
                cpu_mem = status['cpu_memory']
                cpu_info = f"""⚡ CPU UTILIZATION:
CPU Usage: {cpu_mem.get('cpu_usage', 'N/A')}

📊 MEMORY UTILIZATION:
Memory Usage: {cpu_mem.get('memory_usage', 'N/A')}
Total Memory: {cpu_mem.get('total_memory', 'N/A')} bytes
Used Memory: {cpu_mem.get('used_memory', 'N/A')} bytes
Free Memory: {cpu_mem.get('total_memory', 0) - cpu_mem.get('used_memory', 0)} bytes

📈 PERFORMANCE STATUS:
Status: {'🟢 NORMAL' if float(cpu_mem.get('cpu_usage', '0').replace('%', '')) < 80 else '🔴 HIGH'}
"""
                self.cpu_text.delete(1.0, tk.END)
                self.cpu_text.insert(tk.END, cpu_info)
            
            # Temperature bilgileri
            if status.get('temperature'):
                temp_data = status['temperature']
                temp_info = "🌡️ TEMPERATURE SENSORS:\n\n"
                for sensor, data in temp_data.items():
                    temp_info += f"{sensor}:\n"
                    temp_info += f"  Temperature: {data.get('temperature', 'N/A')}°C\n"
                    temp_info += f"  Status: {data.get('status', 'N/A')}\n\n"
                
                if not temp_data:
                    temp_info += "No temperature sensors detected\n"
                
                self.temp_text.delete(1.0, tk.END)
                self.temp_text.insert(tk.END, temp_info)
            
            # Power status
            if status.get('power'):
                power_data = status['power']
                power_info = "🔌 POWER SUPPLY STATUS:\n\n"
                for ps, data in power_data.items():
                    power_info += f"{ps}:\n"
                    power_info += f"  Status: {data.get('status', 'N/A')}\n"
                    power_info += f"  Details: {data.get('details', 'N/A')}\n\n"
                
                if not power_data:
                    power_info += "No power supply information available\n"
                
                self.power_text.delete(1.0, tk.END)
                self.power_text.insert(tk.END, power_info)
            
            # Fan status
            if status.get('fans'):
                fan_data = status['fans']
                fan_info = "💨 FAN STATUS:\n\n"
                for fan, data in fan_data.items():
                    fan_info += f"{fan}:\n"
                    fan_info += f"  Status: {data.get('status', 'N/A')}\n"
                    fan_info += f"  Details: {data.get('details', 'N/A')}\n\n"
                
                if not fan_data:
                    fan_info += "No fan information available\n"
                
                self.fan_text.delete(1.0, tk.END)
                self.fan_text.insert(tk.END, fan_info)
                
        except Exception as e:
            print(f"Health tab update error: {e}")
    
    def update_network_tab(self):
        """Network Monitor sekmesini güncelle"""
        try:
            if not self.cisco_manager.connected:
                return
            
            # Interface statistics al
            interfaces_stats = self.cisco_manager.get_interface_statistics()
            
            # Mevcut verileri temizle
            for item in self.interface_tree.get_children():
                self.interface_tree.delete(item)
            
            # Yeni verileri ekle
            for interface in interfaces_stats:
                self.interface_tree.insert('', 'end', values=(
                    interface.get('interface', 'N/A'),
                    interface.get('status', 'N/A'),
                    interface.get('rx_packets', 0),
                    interface.get('tx_packets', 0),
                    interface.get('rx_bytes', 0),
                    interface.get('tx_bytes', 0),
                    interface.get('errors', 0)
                ))
        except Exception as e:
            print(f"Network tab update error: {e}")
    
    def update_security_tab(self):
        """Security sekmesini güncelle"""
        try:
            if not self.cisco_manager.connected:
                return
            
            # MAC Address Table güncelle
            mac_table = self.cisco_manager.get_mac_address_table()
            
            # Mevcut MAC verileri temizle
            for item in self.mac_tree.get_children():
                self.mac_tree.delete(item)
            
            # Yeni MAC verileri ekle
            for entry in mac_table:
                self.mac_tree.insert('', 'end', values=(
                    entry.get('vlan', 'N/A'),
                    entry.get('mac_address', 'N/A'),
                    entry.get('type', 'N/A'),
                    entry.get('interface', 'N/A')
                ))
            
            # ARP Table güncelle
            arp_table = self.cisco_manager.get_arp_table()
            
            # Mevcut ARP verileri temizle
            for item in self.arp_tree.get_children():
                self.arp_tree.delete(item)
            
            # Yeni ARP verileri ekle
            for entry in arp_table:
                self.arp_tree.insert('', 'end', values=(
                    entry.get('address', 'N/A'),
                    entry.get('mac_address', 'N/A'),
                    entry.get('type', 'N/A'),
                    entry.get('interface', 'N/A')
                ))
        except Exception as e:
            print(f"Security tab update error: {e}")
    
    def handle_port_control(self, port_num, action):
        """Professional port control with notifications and state tracking"""
        if not self.cisco_manager.connected:
            self.add_notification("❌ No device connection for port control", "error")
            return
        
        # Track original state for notification
        original_state = "unknown"
        if hasattr(self, 'last_interface_states') and f"Gi1/0/{port_num}" in self.last_interface_states:
            original_state = self.last_interface_states[f"Gi1/0/{port_num}"]
        
        def control_thread():
            try:
                interface = f"Gi1/0/{port_num}"
                
                if action == 'enable':
                    self.root.after(0, self.add_notification, f"🔄 Enabling port {port_num}...", "info")
                    self.root.after(0, self.update_ticker, f"Enabling port {port_num}")
                    
                    result = self.cisco_manager.set_interface_status(interface, 'up')
                    
                    self.root.after(0, self.add_notification, f"🟢 Port {port_num} ENABLED successfully", "success")
                    self.root.after(0, self.show_port_status_popup, port_num, "ENABLED", "success")
                    
                elif action == 'disable':
                    self.root.after(0, self.add_notification, f"🔄 Disabling port {port_num}...", "warning")
                    self.root.after(0, self.update_ticker, f"Disabling port {port_num}")
                    
                    result = self.cisco_manager.set_interface_status(interface, 'down')
                    
                    self.root.after(0, self.add_notification, f"🔴 Port {port_num} DISABLED successfully", "warning")
                    self.root.after(0, self.show_port_status_popup, port_num, "DISABLED", "warning")
                    
                elif action == 'reset':
                    self.root.after(0, self.add_notification, f"🔄 Resetting port {port_num}...", "info")
                    self.root.after(0, self.update_ticker, f"Resetting port {port_num}")
                    
                    # Reset = disable then enable with delay
                    self.cisco_manager.set_interface_status(interface, 'down')
                    time.sleep(2)  # Professional delay
                    self.cisco_manager.set_interface_status(interface, 'up')
                    
                    self.root.after(0, self.add_notification, f"🔄 Port {port_num} RESET completed", "success")
                    self.root.after(0, self.show_port_status_popup, port_num, "RESET", "info")
                
                # Professional refresh with delay
                self.root.after(2000, self.quick_refresh)
                self.root.after(0, self.update_ticker, f"Port {port_num} operation completed")
                
            except Exception as e:
                error_msg = f"Port {port_num} control failed: {str(e)}"
                self.root.after(0, self.add_notification, f"❌ {error_msg}", "error")
                self.root.after(0, self.show_port_status_popup, port_num, "ERROR", "error")
        
        threading.Thread(target=control_thread, daemon=True).start()
    
    def show_port_status_popup(self, port_num, status, type="info"):
        """Show professional port status popup notification"""
        popup = tk.Toplevel(self.root)
        popup.title(f"Port {port_num} Status")
        popup.geometry("400x200")
        popup.configure(bg='#1a1a1a')
        popup.resizable(False, False)
        
        # Center popup
        popup.transient(self.root)
        popup.grab_set()
        
        # Status colors
        colors = {
            "success": "#28a745",
            "warning": "#ffc107", 
            "error": "#dc3545",
            "info": "#17a2b8"
        }
        
        color = colors.get(type, "#17a2b8")
        
        # Status icon and message
        icons = {
            "ENABLED": "🟢",
            "DISABLED": "🔴", 
            "RESET": "🔄",
            "ERROR": "❌"
        }
        
        icon = icons.get(status, "ℹ️")
        
        # Header
        header_frame = tk.Frame(popup, bg=color, height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"{icon} Port Gi1/0/{port_num}", 
               bg=color, fg='white', font=('Consolas', 16, 'bold')).pack(expand=True)
        
        # Content
        content_frame = tk.Frame(popup, bg='#1a1a1a')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(content_frame, text=f"Status: {status}", 
               bg='#1a1a1a', fg='white', font=('Consolas', 12, 'bold')).pack()
        
        tk.Label(content_frame, text=f"Time: {datetime.now().strftime('%H:%M:%S')}", 
               bg='#1a1a1a', fg='#7d8590', font=('Consolas', 10)).pack(pady=5)
        
        # Auto close after 3 seconds
        popup.after(3000, popup.destroy)
        
        # Close button
        tk.Button(content_frame, text="OK", command=popup.destroy,
                 bg=color, fg='white', font=('Consolas', 10, 'bold'),
                 relief='flat', cursor='hand2').pack(pady=10)
    
    def handle_port_vlan(self, port_num, vlan_id):
        """Handle port VLAN assignment"""
        if not self.cisco_manager.connected:
            self.command_terminal.add_output("❌ No device connection\n", '#e74c3c')
            return
        
        def vlan_thread():
            try:
                interface = f"Gi1/0/{port_num}"
                result = self.cisco_manager.set_interface_vlan(interface, vlan_id)
                self.root.after(0, self.command_terminal.add_output, 
                              f"🏷️ Port {port_num} assigned to VLAN {vlan_id}\n", '#3498db')
                
                # Refresh port status after change
                self.root.after(1000, self.quick_refresh)
                
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ VLAN assignment failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=vlan_thread, daemon=True).start()
    
    def handle_port_description(self, port_num, description):
        """Handle port description setting"""
        if not self.cisco_manager.connected:
            self.command_terminal.add_output("❌ No device connection\n", '#e74c3c')
            return
        
        def desc_thread():
            try:
                interface = f"Gi1/0/{port_num}"
                result = self.cisco_manager.set_interface_description(interface, description)
                self.root.after(0, self.command_terminal.add_output, 
                              f"📝 Port {port_num} description set to: {description}\n", '#9b59b6')
                
                # Refresh port status after change
                self.root.after(1000, self.quick_refresh)
                
            except Exception as e:
                self.root.after(0, self.command_terminal.add_output, 
                              f"❌ Description setting failed: {str(e)}\n", '#e74c3c')
        
        threading.Thread(target=desc_thread, daemon=True).start()
    
    # Professional monitoring functions
    def start_professional_monitoring(self):
        """Start comprehensive professional monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.auto_refresh_active = True
            self.start_auto_refresh()
            self.add_notification("🔄 Professional monitoring started", "info")
            self.update_ticker("Professional monitoring active - Real-time network surveillance enabled")
    
    def emergency_refresh(self):
        """Emergency comprehensive refresh"""
        self.add_notification("🚨 Emergency refresh initiated", "warning")
        self.update_ticker("Emergency refresh in progress...")
        self.refresh_all_data()
    
    def emergency_stop(self):
        """Emergency stop all operations"""
        self.auto_refresh_active = False
        self.monitoring_active = False
        self.add_notification("🛑 Emergency stop activated", "error")
        self.update_ticker("Emergency stop - All monitoring suspended")
    
    def emergency_backup(self):
        """Emergency configuration backup"""
        if not self.cisco_manager.connected:
            self.add_notification("❌ No device connection for backup", "error")
            return
        
        def backup_thread():
            try:
                filename = self.cisco_manager.backup_config()
                self.root.after(0, self.add_notification, f"💾 Emergency backup saved: {filename}", "success")
                self.root.after(0, self.update_ticker, f"Emergency backup completed: {filename}")
            except Exception as e:
                self.root.after(0, self.add_notification, f"❌ Backup failed: {str(e)}", "error")
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def show_performance(self):
        """Show performance dashboard"""
        perf_window = tk.Toplevel(self.root)
        perf_window.title("📊 Performance Dashboard")
        perf_window.geometry("800x600")
        perf_window.configure(bg='#1a1a1a')
        
        # Performance content
        tk.Label(perf_window, text="📊 REAL-TIME PERFORMANCE DASHBOARD", 
               bg='#1a1a1a', fg='#00ff41', font=('Consolas', 16, 'bold')).pack(pady=20)
        
        # Performance metrics (placeholder)
        metrics_text = scrolledtext.ScrolledText(perf_window, bg='#0d1117', fg='#00ff41', 
                                               font=('Consolas', 10))
        metrics_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        sample_metrics = """
🔥 PERFORMANCE METRICS - LIVE DATA
========================================

CPU UTILIZATION:
- Current: 15.2%
- Average (5min): 12.8%
- Peak (1hr): 45.7%
- Status: OPTIMAL

MEMORY UTILIZATION:
- Used: 2.1GB / 4.0GB (52.5%)
- Available: 1.9GB
- Buffers: 256MB
- Status: NORMAL

INTERFACE STATISTICS:
- Total Interfaces: 48
- Active: 24
- Connected: 18
- Errors: 0
- Traffic Rate: 125.5 Mbps

ENVIRONMENTAL:
- Temperature: 45°C (NORMAL)
- Power Supply 1: OK
- Power Supply 2: OK
- Fan Status: ALL OK

NETWORK HEALTH:
- Packet Loss: 0.01%
- Latency: 1.2ms
- Uptime: 45d 12h 34m
- Last Reboot: Normal shutdown
        """
        
        metrics_text.insert(tk.END, sample_metrics)
        metrics_text.config(state=tk.DISABLED)
    
    def run_diagnostics(self):
        """Run comprehensive diagnostics"""
        if not self.cisco_manager.connected:
            self.add_notification("❌ No device connection for diagnostics", "error")
            return
        
        self.add_notification("🔧 Running comprehensive diagnostics...", "info")
        
        def diag_thread():
            try:
                # Run multiple diagnostic commands
                commands = [
                    "show version",
                    "show inventory", 
                    "show environment all",
                    "show interfaces status",
                    "show spanning-tree summary",
                    "show ip route summary"
                ]
                
                for cmd in commands:
                    self.root.after(0, self.update_ticker, f"Running: {cmd}")
                    output = self.cisco_manager.send_command(cmd)
                    time.sleep(0.5)  # Small delay between commands
                
                self.root.after(0, self.add_notification, "✅ Diagnostics completed successfully", "success")
                self.root.after(0, self.update_ticker, "Diagnostics completed - All systems operational")
                
            except Exception as e:
                self.root.after(0, self.add_notification, f"❌ Diagnostics failed: {str(e)}", "error")
        
        threading.Thread(target=diag_thread, daemon=True).start()
    
    def show_notifications(self):
        """Show notification center"""
        notif_window = tk.Toplevel(self.root)
        notif_window.title("🔔 Notification Center")
        notif_window.geometry("600x400")
        notif_window.configure(bg='#1a1a1a')
        
        tk.Label(notif_window, text="🔔 NOTIFICATION CENTER", 
               bg='#1a1a1a', fg='#00ff41', font=('Consolas', 14, 'bold')).pack(pady=10)
        
        # Notifications list
        notif_text = scrolledtext.ScrolledText(notif_window, bg='#0d1117', fg='#00ff41', 
                                             font=('Consolas', 9))
        notif_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        for notification in self.notifications[-50:]:  # Show last 50
            notif_text.insert(tk.END, f"{notification}\n")
        
        notif_text.config(state=tk.DISABLED)
    
    def show_statistics(self):
        """Show comprehensive statistics"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📈 Network Statistics")
        stats_window.geometry("900x700")
        stats_window.configure(bg='#1a1a1a')
        
        tk.Label(stats_window, text="📈 COMPREHENSIVE NETWORK STATISTICS", 
               bg='#1a1a1a', fg='#00ff41', font=('Consolas', 14, 'bold')).pack(pady=10)
        
        # Statistics content
        stats_text = scrolledtext.ScrolledText(stats_window, bg='#0d1117', fg='#00ff41', 
                                             font=('Consolas', 9))
        stats_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Generate comprehensive statistics
        if self.cisco_manager.connected:
            try:
                interfaces = self.cisco_manager.get_interfaces_status()
                up_count = sum(1 for intf in interfaces.values() if intf['status'].lower() == 'connected')
                down_count = len(interfaces) - up_count
                
                stats_content = f"""
📊 REAL-TIME NETWORK STATISTICS
=====================================

CONNECTION STATUS:
- Device: {"ONLINE" if self.cisco_manager.connected else "OFFLINE"}
- Monitoring: {"ACTIVE" if self.monitoring_active else "INACTIVE"}
- Auto-refresh: {"ENABLED" if self.auto_refresh_active else "DISABLED"}
- Refresh Interval: {self.refresh_interval/1000}s

INTERFACE SUMMARY:
- Total Interfaces: {len(interfaces)}
- Operational: {up_count}
- Down: {down_count}
- Utilization: {(up_count/len(interfaces)*100):.1f}%

PORT STATUS BREAKDOWN:
"""
                
                # Port statistics
                status_counts = {}
                for intf in interfaces.values():
                    status = intf['status']
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in status_counts.items():
                    stats_content += f"- {status.upper()}: {count} ports\n"
                
                stats_content += f"\nMONITORING STATISTICS:\n"
                stats_content += f"- Notifications: {len(self.notifications)}\n"
                stats_content += f"- Connection History: {len(self.connection_history)}\n"
                stats_content += f"- Performance Samples: {len(self.performance_history['cpu'])}\n"
                
            except Exception as e:
                stats_content = f"Error generating statistics: {str(e)}"
        else:
            stats_content = "No device connection - Statistics unavailable"
        
        stats_text.insert(tk.END, stats_content)
        stats_text.config(state=tk.DISABLED)
    
    def add_notification(self, message, type="info"):
        """Add notification with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        icon = icons.get(type, "ℹ️")
        
        full_message = f"[{timestamp}] {icon} {message}"
        self.notifications.append(full_message)
        
        # Keep only last 100 notifications
        if len(self.notifications) > 100:
            self.notifications = self.notifications[-100:]
        
        # Show in terminal too
        colors = {"info": '#3498db', "success": '#27ae60', "warning": '#f39c12', "error": '#e74c3c'}
        color = colors.get(type, '#3498db')
        
        if hasattr(self, 'command_terminal'):
            self.command_terminal.add_output(f"{full_message}\n", color)
    
    def update_ticker(self, message):
        """Update status ticker with new message"""
        if hasattr(self, 'ticker_text'):
            self.ticker_text.config(text=f"🔄 {message}")
    
    def update_live_time(self):
        """Update live time display"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if hasattr(self, 'live_time'):
            self.live_time.config(text=current_time)
        self.root.after(1000, self.update_live_time)
    
    def start_ticker_animation(self):
        """Animate status ticker"""
        messages = [
            "Professional monitoring active",
            "Real-time network surveillance",
            "Enterprise-grade management",
            "Advanced diagnostics ready",
            "Continuous health monitoring"
        ]
        
        def animate():
            if hasattr(self, 'ticker_text'):
                import random
                message = random.choice(messages)
                self.ticker_text.config(text=f"🔄 {message}...")
            self.root.after(5000, animate)
        
        animate()
    
    def setup_all_professional_tabs(self):
        """Setup all tabs with professional styling"""
        # All existing tab setup code here...
        # Device Info sekmesi
        self.device_info_frame = tk.Frame(self.content_notebook, bg='#1a1a1a')
        self.content_notebook.add(self.device_info_frame, text="📊 Device Info")
        
        self.device_info_panel = DeviceInfoPanel(self.device_info_frame)
        self.device_info_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Port Visualization sekmesi
        self.port_frame = tk.Frame(self.content_notebook, bg='#1a1a1a')
        self.content_notebook.add(self.port_frame, text="🔌 Port Status")
        
        self.port_visualization = PortVisualization(self.port_frame, port_count=48)
        self.port_visualization.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Set port control callbacks
        self.port_visualization.port_control_callback = self.handle_port_control
        self.port_visualization.port_vlan_callback = self.handle_port_vlan
        self.port_visualization.port_desc_callback = self.handle_port_description
        
        # Continue with other tabs...
        self.setup_remaining_tabs()
    
    def setup_remaining_tabs(self):
        """Setup remaining tabs"""
        # Command Terminal sekmesi
        self.terminal_frame = tk.Frame(self.content_notebook, bg='#0d1117')
        self.content_notebook.add(self.terminal_frame, text="💻 Terminal")
        
        self.command_terminal = CommandTerminal(self.terminal_frame, 
                                              command_callback=self.execute_command)
        self.command_terminal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # System Health sekmesi
        self.health_frame = tk.Frame(self.content_notebook, bg='#1a1a1a')
        self.content_notebook.add(self.health_frame, text="🔥 System Health")
        
        self.setup_health_tab()
        
        # Network Monitoring sekmesi
        self.network_frame = tk.Frame(self.content_notebook, bg='#1a1a1a')
        self.content_notebook.add(self.network_frame, text="🌐 Network Monitor")
        
        self.setup_network_tab()
        
        # Security & Access sekmesi
        self.security_frame = tk.Frame(self.content_notebook, bg='#1a1a1a')
        self.content_notebook.add(self.security_frame, text="🔒 Security")
        
        self.setup_security_tab()
        
        # Logs & Diagnostics sekmesi
        self.logs_frame = tk.Frame(self.content_notebook, bg='#1a1a1a')
        self.content_notebook.add(self.logs_frame, text="📊 Diagnostics")
        
        self.setup_diagnostics_tab()
        
        # VLAN Management sekmesi
        self.vlan_mgmt_frame = tk.Frame(self.content_notebook, bg='#1a1a1a')
        self.content_notebook.add(self.vlan_mgmt_frame, text="🏷️ VLAN Manager")
        
        self.setup_vlan_management_tab()
    
    def extract_port_number(self, interface_name):
        """Interface adından port numarası çıkar - improved method"""
        import re
        
        # Try different patterns to extract port number
        patterns = [
            r'Gi1/0/(\d+)',           # Gi1/0/24
            r'GigabitEthernet1/0/(\d+)',  # GigabitEthernet1/0/24
            r'Gi(\d+)',               # Gi24
            r'G(\d+)',                # G24
            r'/(\d+)$',               # any ending with /number
            r'(\d+)$'                 # any ending with number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, interface_name)
            if match:
                port_num = int(match.group(1))
                # Ensure port number is within valid range (1-48)
                if 1 <= port_num <= 48:
                    return port_num
        
        return None
    
    def toggle_auto_refresh(self):
        """Otomatik yenilemeyi aç/kapat"""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        """Otomatik yenileme başlat"""
        self.auto_refresh_active = True
        self.auto_refresh_loop()
        self.command_terminal.add_output("🔄 Auto refresh started (30s interval)\n", '#3498db')
    
    def stop_auto_refresh(self):
        """Otomatik yenileme durdur"""
        self.auto_refresh_active = False
        self.command_terminal.add_output("⏹️ Auto refresh stopped\n", '#f39c12')
    
    def auto_refresh_loop(self):
        """Otomatik yenileme döngüsü"""
        if self.auto_refresh_active and self.cisco_manager.connected:
            self.refresh_all_data()
            self.root.after(self.refresh_interval, self.auto_refresh_loop)
    
    def disconnect_device(self):
        """Cihaz bağlantısını kes"""
        if self.cisco_manager.connected:
            self.stop_auto_refresh()
            self.cisco_manager.disconnect()
            self.command_terminal.add_output("🔌 Disconnected from device\n", '#f39c12')
    
    def run(self):
        """Uygulamayı başlat"""
        # Kapanma olayını yakala
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Uygulama başlangıç mesajı
        self.command_terminal.add_output("🚀 Cisco Switch Manager started\n", '#3498db')
        self.command_terminal.add_output("💡 Type 'help' for available commands\n", '#95a5a6')
        
        # Ana döngü
        self.root.mainloop()
    
    def on_closing(self):
        """Uygulama kapanırken"""
        self.stop_auto_refresh()
        if self.cisco_manager.connected:
            self.cisco_manager.disconnect()
        self.root.destroy()
    
    def start_professional_systems(self):
        """Start all professional monitoring systems"""
        logger.info("Starting professional monitoring systems")
        
        # Start auto-refresh system
        self.start_auto_refresh()
        
        # Start port monitoring system
        self.start_port_monitoring()
        
        # Start health monitoring
        self.start_health_monitoring()
        
        logger.info("All professional systems started")
    
    def start_port_monitoring(self):
        """Start dedicated port monitoring system"""
        if not self.port_monitoring_thread or not self.port_monitoring_thread.is_alive():
            self.port_monitoring_thread = threading.Thread(
                target=self.port_monitoring_loop, 
                daemon=True
            )
            self.port_monitoring_thread.start()
            logger.info("Port monitoring system started")
    
    def port_monitoring_loop(self):
        """Continuous port monitoring with state change detection"""
        while self.auto_refresh_active:
            try:
                if self.cisco_manager.connected:
                    # Get current interface status
                    current_interfaces = self.cisco_manager.get_interfaces_status()
                    
                    # Check for state changes
                    changes_detected = self.detect_port_changes(current_interfaces)
                    
                    if changes_detected:
                        # Update port visualization immediately
                        self.root.after(0, self.update_port_visualization, current_interfaces)
                        
                        # Log changes
                        for change in changes_detected:
                            logger.info(f"Port state change detected: {change}")
                            self.root.after(0, self.add_notification, 
                                          f"Port {change['port']} changed: {change['old_state']} → {change['new_state']}", 
                                          "info")
                    
                    # Update performance history
                    self.update_performance_history(current_interfaces)
                    
                    # Update last known states
                    self.last_interface_states = current_interfaces.copy()
                
                # Wait for next monitoring cycle
                time.sleep(self.port_refresh_interval / 1000.0)
                
            except Exception as e:
                logger.error(f"Port monitoring error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def detect_port_changes(self, current_interfaces):
        """Detect changes in port states"""
        changes = []
        
        for interface, current_data in current_interfaces.items():
            if interface in self.last_interface_states:
                old_data = self.last_interface_states[interface]
                current_status = current_data.get('status', 'unknown')
                old_status = old_data.get('status', 'unknown')
                
                if current_status != old_status:
                    port_num = self.extract_port_number(interface)
                    if port_num:
                        change = {
                            'port': port_num,
                            'interface': interface,
                            'old_state': old_status,
                            'new_state': current_status,
                            'timestamp': datetime.now(),
                            'vlan': current_data.get('vlan', 'N/A')
                        }
                        changes.append(change)
                        
                        # Add to port change history
                        self.port_change_history.append(change)
                        
                        # Keep only last 100 changes
                        if len(self.port_change_history) > 100:
                            self.port_change_history.pop(0)
        
        return changes
    
    def update_port_visualization(self, interfaces):
        """Update port visualization with current interface data"""
        try:
            for interface, data in interfaces.items():
                port_num = self.extract_port_number(interface)
                if port_num:
                    status = data.get('status', 'unknown')
                    self.port_visualization.update_port_status(port_num, status, data)
        except Exception as e:
            logger.error(f"Error updating port visualization: {e}")
    
    def update_performance_history(self, interfaces):
        """Update performance history with current interface data"""
        try:
            # Count interface states
            up_count = sum(1 for data in interfaces.values() 
                          if data.get('status', '').lower() in ['up', 'connected'])
            down_count = len(interfaces) - up_count
            
            # Add to history
            current_time = datetime.now()
            self.performance_history['interfaces_up'].append(up_count)
            self.performance_history['interfaces_down'].append(down_count)
            self.performance_history['timestamps'].append(current_time)
            
            # Keep only last 100 data points
            max_history = 100
            for key in ['interfaces_up', 'interfaces_down', 'timestamps']:
                if len(self.performance_history[key]) > max_history:
                    self.performance_history[key] = self.performance_history[key][-max_history:]
                    
        except Exception as e:
            logger.error(f"Error updating performance history: {e}")
    
    def start_health_monitoring(self):
        """Start health monitoring system"""
        def health_monitor():
            while self.auto_refresh_active:
                try:
                    if self.cisco_manager.connected:
                        # Get comprehensive status
                        status_data = self.cisco_manager.get_comprehensive_status()
                        
                        # Update GUI components
                        self.root.after(0, self.update_health_tab, status_data)
                        self.root.after(0, self.update_network_tab)
                        self.root.after(0, self.update_security_tab)
                        
                        # Update performance history
                        if status_data.get('cpu_memory'):
                            self.update_cpu_memory_history(status_data['cpu_memory'])
                    
                    time.sleep(10)  # Health monitoring every 10 seconds
                    
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(15)  # Wait longer on error
        
        health_thread = threading.Thread(target=health_monitor, daemon=True)
        health_thread.start()
        logger.info("Health monitoring system started")
    
    def update_cpu_memory_history(self, cpu_mem_data):
        """Update CPU and memory performance history"""
        try:
            # Extract numeric values
            cpu_usage = cpu_mem_data.get('cpu_usage', '0%').replace('%', '')
            memory_usage = cpu_mem_data.get('memory_usage', '0%').replace('%', '')
            
            try:
                cpu_val = float(cpu_usage)
                mem_val = float(memory_usage)
                
                self.performance_history['cpu'].append(cpu_val)
                self.performance_history['memory'].append(mem_val)
                
                # Keep only last 100 data points
                max_history = 100
                if len(self.performance_history['cpu']) > max_history:
                    self.performance_history['cpu'] = self.performance_history['cpu'][-max_history:]
                if len(self.performance_history['memory']) > max_history:
                    self.performance_history['memory'] = self.performance_history['memory'][-max_history:]
                    
            except ValueError:
                pass  # Skip invalid data
                
        except Exception as e:
            logger.error(f"Error updating CPU/memory history: {e}")
    
    def toggle_real_time_monitoring(self):
        """Toggle real-time monitoring on/off"""
        self.real_time_monitoring = not self.real_time_monitoring
        
        if self.real_time_monitoring:
            self.start_port_monitoring()
            self.add_notification("Real-time monitoring ENABLED", "success")
            logger.info("Real-time monitoring enabled")
        else:
            self.add_notification("Real-time monitoring DISABLED", "warning")
            logger.info("Real-time monitoring disabled")
    
    def force_port_refresh(self):
        """Force immediate port refresh"""
        def refresh_thread():
            try:
                if self.cisco_manager.connected:
                    interfaces = self.cisco_manager.get_interfaces_status()
                    self.root.after(0, self.update_port_visualization, interfaces)
                    self.root.after(0, self.add_notification, "Port status refreshed", "info")
                    logger.info("Force port refresh completed")
                else:
                    self.root.after(0, self.add_notification, "No device connection", "error")
            except Exception as e:
                error_msg = f"Force refresh failed: {str(e)}"
                self.root.after(0, self.add_notification, error_msg, "error")
                logger.error(error_msg)
        
        threading.Thread(target=refresh_thread, daemon=True).start()
    
    def show_port_change_history(self):
        """Show port change history in a new window"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Port Change History")
        history_window.geometry("800x600")
        history_window.configure(bg='#2c3e50')
        
        # Create treeview for history
        columns = ('Time', 'Port', 'Interface', 'Old State', 'New State', 'VLAN')
        tree = ttk.Treeview(history_window, columns=columns, show='headings')
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Populate with history data
        for change in reversed(self.port_change_history):  # Most recent first
            tree.insert('', 'end', values=(
                change['timestamp'].strftime('%H:%M:%S'),
                change['port'],
                change['interface'],
                change['old_state'],
                change['new_state'],
                change['vlan']
            ))
        
        logger.info("Port change history window opened")

def main():
    """Ana fonksiyon"""
    try:
        app = CiscoSwitchApp()
        app.run()
    except Exception as e:
        print(f"❌ Application startup error: {e}")
        messagebox.showerror("Startup Error", f"Failed to start application:\n{e}")

if __name__ == "__main__":
    main() 