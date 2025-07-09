#!/usr/bin/env python3
"""
Cisco Switch Management GUI
Professional GUI application for managing Cisco 9300 Catalyst switches

Author: Professional Network Management Team
Version: 2.0.0
Date: 2024-12-20
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging
from cisco_manager import CiscoManager, CiscoManagerError
from config import config
from performance_dashboard import PerformanceDashboard
from cache_manager import cache_manager

# Configure GUI logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CiscoGUI:
    """Main GUI class for Cisco switch management"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.cisco_manager = CiscoManager()
        self.connected = False
        self.auto_refresh = False
        self.refresh_interval = 1.5  # Normal refresh interval - faster
        self.fast_monitoring = False
        self.fast_monitoring_var = tk.BooleanVar()
        self.fast_refresh_interval = 0.5  # Ultra fast monitoring - 500ms for real-time
        self.current_interfaces = {}
        self.previous_interfaces = {}
        self.notifications = []
        
        self.setup_window()
        self.create_menu()
        self.create_widgets()
        self.setup_callbacks()
        
        # Add initial notification
        self.add_notification("🚀 Cisco Switch Manager başlatıldı - Bağlantı için bilgileri girin", "info")
        
    def setup_window(self):
        """Configure main window with professional settings"""
        self.root.title("Cisco Switch Manager - Professional Edition v2.0")
        self.root.geometry(f"{config.ui.window_width}x{config.ui.window_height}")
        self.root.minsize(config.ui.min_width, config.ui.min_height)
        
        # Configure professional style
        style = ttk.Style()
        style.theme_use(config.ui.theme)
        
        # Professional color scheme and fonts
        style.configure('Title.TLabel', 
                       font=(config.ui.font_family, config.ui.font_size + 3, 'bold'),
                       foreground='#2c3e50')
        style.configure('Header.TLabel', 
                       font=(config.ui.font_family, config.ui.font_size + 1, 'bold'),
                       foreground='#34495e')
        style.configure('Status.TLabel', 
                       font=(config.ui.font_family, config.ui.font_size),
                       foreground='#7f8c8d')
        style.configure('Performance.TLabel',
                       font=(config.ui.font_family, config.ui.font_size + 2, 'bold'),
                       foreground='#27ae60')
        
        # Warning button style
        style.configure('Warning.TButton',
                       font=(config.ui.font_family, config.ui.font_size, 'bold'),
                       foreground='#e74c3c')
        style.map('Warning.TButton',
                 background=[('active', '#f39c12'),
                           ('pressed', '#e67e22')])
        
        # Success button style
        style.configure('Success.TButton',
                       font=(config.ui.font_family, config.ui.font_size, 'bold'),
                       foreground='#27ae60')
        style.map('Success.TButton',
                 background=[('active', '#2ecc71'),
                           ('pressed', '#229954')])
        
        # Set window icon if available
        try:
            # You can add an icon file here
            # self.root.iconbitmap('cisco_icon.ico')
            pass
        except:
            pass
        
    def create_menu(self):
        """Create menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Bağlan", command=self.show_connection_dialog)
        file_menu.add_command(label="Bağlantıyı Kes", command=self.disconnect)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Araçlar", menu=tools_menu)
        tools_menu.add_command(label="Konfigürasyonu Kaydet", command=self.save_config)
        tools_menu.add_separator()
        tools_menu.add_command(label="MAC Adres Tablosu", command=self.show_mac_table)
        tools_menu.add_command(label="ARP Tablosu", command=self.show_arp_table)
        tools_menu.add_separator()
        tools_menu.add_command(label="Performans Raporu", command=self.show_performance_report)
        tools_menu.add_command(label="Sağlık Kontrolü", command=self.run_health_check)
        
        # Performance menu
        perf_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Performans", menu=perf_menu)
        perf_menu.add_command(label="Cache Temizle", command=self.clear_cache)
        perf_menu.add_command(label="Cache İstatistikleri", command=self.show_cache_stats)
        perf_menu.add_separator()
        perf_menu.add_command(label="Performans İzleme", command=self.show_performance_tab)
        perf_menu.add_command(label="Sistem Durumu", command=self.show_system_status)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayarlar", menu=settings_menu)
        settings_menu.add_command(label="Genel Ayarlar", command=self.show_settings)
        settings_menu.add_command(label="Performans Ayarları", command=self.show_performance_settings)
        settings_menu.add_separator()
        settings_menu.add_command(label="Varsayılana Sıfırla", command=self.reset_settings)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        help_menu.add_command(label="Kullanım Kılavuzu", command=self.show_help)
        help_menu.add_command(label="Kısayol Tuşları", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="Hakkında", command=self.show_about)

    def create_widgets(self):
        """Create professional GUI widgets with performance monitoring"""
        # Professional main container with notebook
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Main management tab
        main_tab_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(main_tab_frame, text="🖥️ Switch Yönetimi")
        
        # Performance monitoring tab
        performance_tab_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(performance_tab_frame, text="📊 Performans İzleme")
        
        # Create main management interface
        main_paned = ttk.PanedWindow(main_tab_frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for connection and device info
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel for interface management
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        
        self.create_connection_panel(left_frame)
        self.create_device_info_panel(left_frame)
        self.create_notification_panel(left_frame)
        self.create_interface_panel(right_frame)
        
        # Create performance dashboard
        self.performance_dashboard = PerformanceDashboard(performance_tab_frame, self.cisco_manager)
        
        self.create_status_bar()
        
    def create_connection_panel(self, parent):
        """Create connection panel"""
        # Connection frame
        conn_frame = ttk.LabelFrame(parent, text="Bağlantı", padding=10)
        conn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Connection fields
        ttk.Label(conn_frame, text="IP Adresi:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.host_var = tk.StringVar(value="192.168.20.1")
        self.host_entry = ttk.Entry(conn_frame, textvariable=self.host_var, width=20)
        self.host_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(conn_frame, text="Kullanıcı Adı:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.username_var = tk.StringVar(value="swapp")
        self.username_entry = ttk.Entry(conn_frame, textvariable=self.username_var, width=20)
        self.username_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(conn_frame, text="Şifre:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(conn_frame, textvariable=self.password_var, show="*", width=20)
        self.password_entry.grid(row=2, column=1, padx=5, pady=2)
        
        ttk.Label(conn_frame, text="Enable Şifresi:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.secret_var = tk.StringVar()
        self.secret_entry = ttk.Entry(conn_frame, textvariable=self.secret_var, show="*", width=20)
        self.secret_entry.grid(row=3, column=1, padx=5, pady=2)
        
        # Connection buttons
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        self.connect_btn = ttk.Button(button_frame, text="Bağlan", command=self.connect)
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = ttk.Button(button_frame, text="Bağlantıyı Kes", 
                                        command=self.disconnect, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Connection status
        self.conn_status_var = tk.StringVar(value="Bağlı değil")
        self.conn_status_label = ttk.Label(conn_frame, textvariable=self.conn_status_var,
                                          style='Status.TLabel')
        self.conn_status_label.grid(row=5, column=0, columnspan=2, pady=5)

    def create_device_info_panel(self, parent):
        """Create device information panel"""
        # Device info frame
        info_frame = ttk.LabelFrame(parent, text="Cihaz Bilgileri", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Device info tree
        self.device_tree = ttk.Treeview(info_frame, columns=('value',), show='tree')
        self.device_tree.heading('#0', text='Özellik')
        self.device_tree.heading('value', text='Değer')
        self.device_tree.column('#0', width=120)
        self.device_tree.column('value', width=200)
        
        # Scrollbar for device tree
        device_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=device_scroll.set)
        
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        device_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        refresh_frame = ttk.Frame(parent)
        refresh_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.auto_refresh_var = tk.BooleanVar()
        auto_refresh_check = ttk.Checkbutton(refresh_frame, text="Otomatik Yenileme (1.5sn)", 
                                           variable=self.auto_refresh_var,
                                           command=self.toggle_auto_refresh)
        auto_refresh_check.pack(side=tk.LEFT)
        
        # Fast monitoring checkbox for real-time updates
        self.fast_monitoring_check = ttk.Checkbutton(refresh_frame, text="⚡ Anlık İzleme (0.5sn)", 
                                                    variable=self.fast_monitoring_var,
                                                    command=self.toggle_fast_monitoring,
                                                    style='Success.TCheckbutton')
        self.fast_monitoring_check.pack(side=tk.LEFT, padx=(10, 0))
        
        self.refresh_btn = ttk.Button(refresh_frame, text="Yenile", 
                                    command=self.refresh_data, state=tk.DISABLED)
        self.refresh_btn.pack(side=tk.RIGHT)

    def create_notification_panel(self, parent):
        """Create notification/alert panel"""
        # Notification frame
        notif_frame = ttk.LabelFrame(parent, text="Port Durumu & Uyarılar", padding=10)
        notif_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Notification text area with scrollbar
        text_frame = ttk.Frame(notif_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notification_text = tk.Text(text_frame, height=8, wrap=tk.WORD, 
                                        font=('Consolas', 9), state=tk.DISABLED)
        
        # Scrollbar for notifications
        notif_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, 
                                    command=self.notification_text.yview)
        self.notification_text.configure(yscrollcommand=notif_scroll.set)
        
        self.notification_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        notif_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Clear notifications button
        clear_frame = ttk.Frame(notif_frame)
        clear_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(clear_frame, text="Temizle", 
                  command=self.clear_notifications).pack(side=tk.RIGHT)
        
        # Configure text colors
        self.notification_text.tag_configure("info", foreground="blue")
        self.notification_text.tag_configure("success", foreground="green")
        self.notification_text.tag_configure("warning", foreground="orange")
        self.notification_text.tag_configure("error", foreground="red")
        self.notification_text.tag_configure("timestamp", foreground="gray")

    def create_interface_panel(self, parent):
        """Create interface management panel"""
        # Interface frame with notebook for different views
        self.interface_notebook = ttk.Notebook(parent)
        self.interface_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Interface status tab
        self.interface_frame = ttk.Frame(self.interface_notebook)
        self.interface_notebook.add(self.interface_frame, text="Port Durumu")
        
        # Interface controls
        control_frame = ttk.Frame(self.interface_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Port Yönetimi", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Interface action buttons
        action_frame = ttk.Frame(control_frame)
        action_frame.pack(side=tk.RIGHT)
        
        self.enable_port_btn = ttk.Button(action_frame, text="Portu Etkinleştir", 
                                        command=self.enable_selected_port, state=tk.DISABLED)
        self.enable_port_btn.pack(side=tk.LEFT, padx=2)
        
        self.disable_port_btn = ttk.Button(action_frame, text="Portu Devre Dışı Bırak", 
                                         command=self.disable_selected_port, state=tk.DISABLED)
        self.disable_port_btn.pack(side=tk.LEFT, padx=2)
        
        self.config_port_btn = ttk.Button(action_frame, text="Port Ayarları", 
                                        command=self.configure_selected_port, state=tk.DISABLED)
        self.config_port_btn.pack(side=tk.LEFT, padx=2)
        
        # Separator
        ttk.Separator(action_frame, orient='vertical').pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Bulk operations
        self.disable_unused_btn = ttk.Button(action_frame, text="🔒 Kullanılmayan Portları Kapat", 
                                           command=self.disable_unused_ports, state=tk.DISABLED,
                                           style='Warning.TButton')
        self.disable_unused_btn.pack(side=tk.LEFT, padx=2)
        
        self.enable_disabled_btn = ttk.Button(action_frame, text="🔓 Kapalı Portları Aç", 
                                            command=self.enable_disabled_ports, state=tk.DISABLED,
                                            style='Success.TButton')
        self.enable_disabled_btn.pack(side=tk.LEFT, padx=2)
        
        # Progress frame for loading indicator
        self.progress_frame = ttk.Frame(self.interface_frame)
        self.progress_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.loading_label = ttk.Label(self.progress_frame, text="", font=(config.ui.font_family, 8))
        self.loading_label.pack(side=tk.LEFT)
        
        self.loading_progress = ttk.Progressbar(self.progress_frame, mode='indeterminate', length=200)
        # Initially hidden
        
        # Interface treeview
        tree_frame = ttk.Frame(self.interface_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview columns
        columns = ('status', 'vlan', 'duplex', 'speed', 'type', 'description')
        self.interface_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.interface_tree.heading('#0', text='Port')
        self.interface_tree.heading('status', text='Durum')
        self.interface_tree.heading('vlan', text='VLAN')
        self.interface_tree.heading('duplex', text='Duplex')
        self.interface_tree.heading('speed', text='Hız')
        self.interface_tree.heading('type', text='Tip')
        self.interface_tree.heading('description', text='Açıklama')
        
        # Configure column widths
        self.interface_tree.column('#0', width=100)
        self.interface_tree.column('status', width=100)
        self.interface_tree.column('vlan', width=60)
        self.interface_tree.column('duplex', width=80)
        self.interface_tree.column('speed', width=80)
        self.interface_tree.column('type', width=120)
        self.interface_tree.column('description', width=200)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.interface_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.interface_tree.xview)
        self.interface_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack treeview and scrollbars
        self.interface_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind selection event
        self.interface_tree.bind('<<TreeviewSelect>>', self.on_interface_select)

    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_var = tk.StringVar(value="Hazır")
        self.status_label = ttk.Label(self.status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Time label
        self.time_var = tk.StringVar()
        self.time_label = ttk.Label(self.status_frame, textvariable=self.time_var)
        self.time_label.pack(side=tk.RIGHT, padx=5)
        
        self.update_time()

    def setup_callbacks(self):
        """Setup manager callbacks and keyboard shortcuts"""
        self.cisco_manager.register_callback('connected', self.on_connected)
        self.cisco_manager.register_callback('disconnected', self.on_disconnected)
        self.cisco_manager.register_callback('connection_failed', self.on_connection_failed)
        
        # Close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Keyboard shortcuts
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<F5>', lambda e: self.refresh_data())
        self.root.bind('<F12>', lambda e: self.show_performance_tab())
        self.root.bind('<Control-d>', lambda e: self.disconnect())
        self.root.bind('<Control-s>', lambda e: self.save_config())
        self.root.bind('<Control-r>', lambda e: self.clear_cache())
        self.root.bind('<Control-h>', lambda e: self.run_health_check())
        self.root.bind('<Control-Shift-D>', lambda e: self.disable_unused_ports())  # Bulk disable unused ports
        self.root.bind('<Control-Shift-E>', lambda e: self.enable_disabled_ports())  # Bulk enable disabled ports
        self.root.bind('<Escape>', lambda e: self.clear_selection())

    def connect(self):
        """Connect to Cisco device"""
        host = self.host_var.get().strip()
        username = self.username_var.get().strip()
        password = self.password_var.get()
        secret = self.secret_var.get()
        
        if not host or not username or not password:
            messagebox.showerror("Hata", "Lütfen tüm gerekli alanları doldurun!")
            return
        
        self.set_status("Bağlanıyor...")
        self.connect_btn.config(state=tk.DISABLED)
        
        # Connect in separate thread to avoid GUI freezing
        def connect_thread():
            try:
                success = self.cisco_manager.connect(
                    host=host,
                    username=username,
                    password=password,
                    secret=secret if secret else None
                )
                
                if not success:
                    self.root.after(0, lambda: self.on_connection_failed(
                        self.cisco_manager.get_last_error() or "Bağlantı başarısız"
                    ))
                    
            except Exception as e:
                self.root.after(0, lambda: self.on_connection_failed(str(e)))
        
        threading.Thread(target=connect_thread, daemon=True).start()

    def disconnect(self):
        """Disconnect from device"""
        if self.cisco_manager.is_connected():
            self.cisco_manager.disconnect()
        
        self.on_disconnected()

    def on_connected(self, device_info):
        """Callback when device connects"""
        self.connected = True
        self.conn_status_var.set("Bağlandı")
        self.connect_btn.config(state=tk.DISABLED)
        self.disconnect_btn.config(state=tk.NORMAL)
        self.refresh_btn.config(state=tk.NORMAL)
        
        # Enable port management buttons
        self.enable_port_btn.config(state=tk.NORMAL)
        self.disable_port_btn.config(state=tk.NORMAL)
        self.config_port_btn.config(state=tk.NORMAL)
        self.disable_unused_btn.config(state=tk.NORMAL)
        self.enable_disabled_btn.config(state=tk.NORMAL)
        
        self.set_status("Başarıyla bağlandı - Portlar yükleniyor...")
        self.update_device_info(device_info)
        
        # Initial fast interface refresh with progress indicator
        def initial_refresh():
            try:
                self.root.after(0, self.show_loading_indicator)
                start_time = time.time()
                
                interfaces = self.cisco_manager.get_interfaces_status(use_cache=False, fast_mode=True)
                
                load_time = time.time() - start_time
                self.root.after(0, self.hide_loading_indicator)
                
                if interfaces:
                    self.root.after(0, lambda: self.update_interface_tree(interfaces))
                    interface_count = len([i for i in interfaces.keys() if not i.startswith('ConnectionTest') and not i.startswith('Error')])
                    self.root.after(0, lambda: self.set_status(f"✅ Hazır - {interface_count} port {load_time:.1f}s'de yüklendi"))
                else:
                    self.root.after(0, lambda: self.set_status("⚠️ Port bilgisi alınamadı"))
            except Exception as e:
                self.root.after(0, self.hide_loading_indicator)
                self.root.after(0, lambda: self.set_status(f"❌ Port yükleme hatası: {str(e)[:50]}"))
        
        # Run initial refresh in background
        threading.Thread(target=initial_refresh, daemon=True).start()
        
        # Bağlantı kurulduğunda anlık izlemeyi aktif et (en hızlı mod)
        self.fast_monitoring_var.set(True)
        self.toggle_fast_monitoring()
        
        # Add connection notification
        device_model = device_info.get('model', 'Unknown')
        device_hostname = device_info.get('hostname', 'Unknown')
        self.add_notification(f"📡 {device_hostname} ({device_model}) cihazına başarıyla bağlandı!", "success")
        
        messagebox.showinfo("Başarılı", "Cisco cihazına başarıyla bağlandı!")

    def on_disconnected(self):
        """Callback when device disconnects"""
        self.connected = False
        self.auto_refresh = False
        self.auto_refresh_var.set(False)
        self.fast_monitoring = False
        self.fast_monitoring_var.set(False)
        
        self.conn_status_var.set("Bağlı değil")
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.refresh_btn.config(state=tk.DISABLED)
        
        # Disable port management buttons
        self.enable_port_btn.config(state=tk.DISABLED)
        self.disable_port_btn.config(state=tk.DISABLED)
        self.config_port_btn.config(state=tk.DISABLED)
        self.disable_unused_btn.config(state=tk.DISABLED)
        self.enable_disabled_btn.config(state=tk.DISABLED)
        
        self.set_status("Bağlantı kesildi")
        self.add_notification("🔌 Cisco cihazından bağlantı kesildi", "warning")
        self.clear_data()

    def on_connection_failed(self, error_msg):
        """Callback when connection fails"""
        self.connect_btn.config(state=tk.NORMAL)
        self.set_status(f"Bağlantı hatası: {error_msg}")
        messagebox.showerror("Bağlantı Hatası", f"Cisco cihazına bağlanılamadı:\n{error_msg}")

    def refresh_data(self):
        """Refresh all data"""
        if not self.connected:
            return
        
        self.set_status("Veriler yenileniyor...")
        
        def refresh_thread():
            try:
                # Refresh device info
                device_info = self.cisco_manager.get_device_info()
                self.root.after(0, lambda: self.update_device_info(device_info))
                
                # Refresh interfaces
                self.root.after(0, self.refresh_interfaces)
                
                self.root.after(0, lambda: self.set_status("Veriler yenilendi"))
                
            except Exception as e:
                self.root.after(0, lambda: self.set_status(f"Veri yenileme hatası: {e}"))
        
        threading.Thread(target=refresh_thread, daemon=True).start()

    def refresh_interfaces(self):
        """Refresh interface data"""
        if not self.connected:
            return
        
        def refresh_thread():
            try:
                # Show progress indicator
                self.root.after(0, self.show_loading_indicator)
                self.root.after(0, lambda: self.set_status("⚡ Portlar hızlı yenileniyor..."))
                start_time = time.time()
                
                # Force fresh data after port operations (no cache)
                interfaces = self.cisco_manager.get_interfaces_status(use_cache=False, fast_mode=True)
                
                refresh_time = time.time() - start_time
                
                # Hide progress indicator
                self.root.after(0, self.hide_loading_indicator)
                
                if not interfaces:
                    self.root.after(0, lambda: self.set_status("Port bilgisi alınamadı - bağlantıyı kontrol edin"))
                    self.root.after(0, lambda: self.add_notification("⚠️ Port bilgileri alınamadı - cihaz kompatibilitesi kontrol ediliyor", "warning"))
                else:
                    self.root.after(0, lambda: self.update_interface_tree(interfaces))
                    interface_count = len([i for i in interfaces.keys() if not i.startswith('ConnectionTest') and not i.startswith('Error')])
                    self.root.after(0, lambda: self.set_status(f"⚡ {interface_count} port {refresh_time:.1f}s'de yenilendi"))
                
            except Exception as e:
                # Hide progress indicator on error
                self.root.after(0, self.hide_loading_indicator)
                
                logger.error(f"Error refreshing interfaces: {e}")
                error_detail = str(e)
                
                if "Pattern not detected" in error_detail:
                    error_msg = "🔄 Cisco cihazı prompt'u tanınamadı - alternatif yöntemler deneniyor..."
                    self.root.after(0, lambda: self.add_notification("🔄 Cisco prompt sorunu - farklı komutlar deneniyor", "warning"))
                elif "Authentication" in error_detail:
                    error_msg = "🔐 Kimlik doğrulama hatası - kullanıcı adı/şifre kontrol edin"
                    self.root.after(0, lambda: self.add_notification("🔐 Kimlik doğrulama sorunu tespit edildi", "error"))
                elif "timeout" in error_detail.lower():
                    error_msg = "⏱️ Zaman aşımı - cihaz yavaş yanıt veriyor"
                    self.root.after(0, lambda: self.add_notification("⏱️ Cihaz yavaş yanıt veriyor - timeout artırıldı", "warning"))
                elif "Device not connected" in error_detail:
                    error_msg = "🔌 Bağlantı kesildi - yeniden bağlanmayı deneyin"
                    self.root.after(0, lambda: self.add_notification("🔌 Bağlantı kesildi", "error"))
                else:
                    error_msg = f"❌ Port yenileme hatası: {error_detail[:100]}..."
                    self.root.after(0, lambda: self.add_notification(f"❌ Genel hata: {error_detail[:50]}...", "error"))
                
                self.root.after(0, lambda: self.set_status(error_msg))
        
        threading.Thread(target=refresh_thread, daemon=True).start()

    def show_loading_indicator(self):
        """Show loading progress indicator"""
        try:
            self.loading_label.config(text="⚡ Yükleniyor...")
            self.loading_progress.pack(side=tk.RIGHT, padx=(5, 0))
            self.loading_progress.start(10)  # 10ms intervals for smooth animation
        except Exception:
            pass  # Ignore if widgets don't exist yet
    
    def hide_loading_indicator(self):
        """Hide loading progress indicator"""
        try:
            self.loading_label.config(text="")
            self.loading_progress.stop()
            self.loading_progress.pack_forget()
        except Exception:
            pass  # Ignore if widgets don't exist yet

    def update_device_info(self, device_info):
        """Update device information display"""
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Add device information
        if device_info:
            for key, value in device_info.items():
                display_key = {
                    'hostname': 'Hostname',
                    'model': 'Model',
                    'serial': 'Seri No',
                    'ios_version': 'IOS Sürümü',
                    'uptime': 'Çalışma Süresi'
                }.get(key, key.title())
                
                self.device_tree.insert('', 'end', text=display_key, values=(value,))

    def update_interface_tree(self, interfaces):
        """Update interface tree with current data"""
        # Clear existing items
        for item in self.interface_tree.get_children():
            self.interface_tree.delete(item)
        
        # Check for interface changes before updating
        self.check_interface_changes(interfaces)
        
        # Store current interfaces
        self.previous_interfaces = self.current_interfaces.copy() if self.current_interfaces else {}
        self.current_interfaces = interfaces
        
        # Add interfaces to tree (filter out test interfaces)
        real_interfaces = {k: v for k, v in interfaces.items() if not k.startswith('ConnectionTest')}
        
        if not real_interfaces and interfaces:
            # If we only have test interface, show connection status message
            self.interface_tree.insert('', 'end', text="Bağlantı Test",
                                     values=("Çalışıyor", "Test", "N/A", "N/A", "Bağlantı testi başarılı", ""),
                                     tags=['connected'])
        else:
            for interface, info in real_interfaces.items():
                status = info.get('status', 'unknown')
                vlan = info.get('vlan', 'N/A')
                duplex = info.get('duplex', 'N/A')
                speed = info.get('speed', 'N/A')
                port_type = info.get('type', 'N/A')
                description = info.get('description', '')
                
                # Color coding based on status
                tags = []
                if status.lower() in ['connected', 'up']:
                    tags.append('connected')
                elif status.lower() in ['notconnect', 'down', 'shutdown']:
                    tags.append('disconnected')
                else:
                    tags.append('unknown')
                
                self.interface_tree.insert('', 'end', text=interface,
                                         values=(status, vlan, duplex, speed, port_type, description),
                                         tags=tags)
        
        # Configure tags for color coding
        self.interface_tree.tag_configure('connected', background='lightgreen')
        self.interface_tree.tag_configure('disconnected', background='lightcoral')
        self.interface_tree.tag_configure('unknown', background='lightyellow')

    def on_interface_select(self, event):
        """Handle interface selection"""
        selection = self.interface_tree.selection()
        if selection:
            self.enable_port_btn.config(state=tk.NORMAL)
            self.disable_port_btn.config(state=tk.NORMAL)
            self.config_port_btn.config(state=tk.NORMAL)
        else:
            self.enable_port_btn.config(state=tk.DISABLED)
            self.disable_port_btn.config(state=tk.DISABLED)
            self.config_port_btn.config(state=tk.DISABLED)

    def get_selected_interface(self):
        """Get currently selected interface"""
        selection = self.interface_tree.selection()
        if selection:
            item = selection[0]
            return self.interface_tree.item(item, 'text')
        return None

    def enable_selected_port(self):
        """Enable selected port"""
        interface = self.get_selected_interface()
        if not interface:
            messagebox.showwarning("Uyarı", "Lütfen bir port seçin!")
            return
        
        self.set_status(f"{interface} portu etkinleştiriliyor...")
        
        def enable_thread():
            try:
                success = self.cisco_manager.enable_interface(interface)
                if success:
                    self.root.after(0, lambda: self.set_status(f"{interface} portu etkinleştirildi"))
                    # Clear cache and immediate refresh for instant color update
                    self.cisco_manager.clear_cache()
                    time.sleep(0.1)  # Short delay for cache clear to take effect
                    self.root.after(100, self.refresh_interfaces)  # Immediate refresh after 100ms
                    # Anlık izlemeyi aktif et
                    if not self.fast_monitoring:
                        self.root.after(0, lambda: (self.fast_monitoring_var.set(True), self.toggle_fast_monitoring()))
                    # Add notification
                    self.root.after(0, lambda: self.add_notification(f"✅ {interface} portu manuel olarak etkinleştirildi", "success"))
                    self.root.after(0, lambda: messagebox.showinfo("Başarılı", 
                                    f"{interface} portu başarıyla etkinleştirildi!"))
                else:
                    self.root.after(0, lambda: self.set_status(f"{interface} portu etkinleştirilemedi"))
                    self.root.after(0, lambda: messagebox.showerror("Hata", 
                                    f"{interface} portu etkinleştirilemedi!"))
            except Exception as e:
                self.root.after(0, lambda: self.set_status(f"Hata: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Port etkinleştirme hatası:\n{e}"))
        
        threading.Thread(target=enable_thread, daemon=True).start()

    def disable_selected_port(self):
        """Disable selected port"""
        interface = self.get_selected_interface()
        if not interface:
            messagebox.showwarning("Uyarı", "Lütfen bir port seçin!")
            return
        
        # Confirm action
        if not messagebox.askyesno("Onay", 
                                  f"{interface} portunu devre dışı bırakmak istediğinizden emin misiniz?"):
            return
        
        self.set_status(f"{interface} portu devre dışı bırakılıyor...")
        
        def disable_thread():
            try:
                success = self.cisco_manager.disable_interface(interface)
                if success:
                    self.root.after(0, lambda: self.set_status(f"{interface} portu devre dışı bırakıldı"))
                    # Clear cache and immediate refresh for instant color update
                    self.cisco_manager.clear_cache()
                    time.sleep(0.1)  # Short delay for cache clear to take effect
                    self.root.after(100, self.refresh_interfaces)  # Immediate refresh after 100ms
                    # Anlık izlemeyi aktif et
                    if not self.fast_monitoring:
                        self.root.after(0, lambda: (self.fast_monitoring_var.set(True), self.toggle_fast_monitoring()))
                    # Add notification
                    self.root.after(0, lambda: self.add_notification(f"❌ {interface} portu manuel olarak devre dışı bırakıldı", "warning"))
                    self.root.after(0, lambda: messagebox.showinfo("Başarılı", 
                                    f"{interface} portu başarıyla devre dışı bırakıldı!"))
                else:
                    self.root.after(0, lambda: self.set_status(f"{interface} portu devre dışı bırakılamadı"))
                    self.root.after(0, lambda: messagebox.showerror("Hata", 
                                    f"{interface} portu devre dışı bırakılamadı!"))
            except Exception as e:
                self.root.after(0, lambda: self.set_status(f"Hata: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Port devre dışı bırakma hatası:\n{e}"))
        
        threading.Thread(target=disable_thread, daemon=True).start()

    def configure_selected_port(self):
        """Configure selected port"""
        interface = self.get_selected_interface()
        if not interface:
            messagebox.showwarning("Uyarı", "Lütfen bir port seçin!")
            return
        
        self.show_port_config_dialog(interface)

    def show_port_config_dialog(self, interface):
        """Show port configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Port Ayarları - {interface}")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Port description
        ttk.Label(main_frame, text="Açıklama:").grid(row=0, column=0, sticky=tk.W, pady=5)
        desc_var = tk.StringVar()
        if interface in self.current_interfaces:
            desc_var.set(self.current_interfaces[interface].get('description', ''))
        desc_entry = ttk.Entry(main_frame, textvariable=desc_var, width=30)
        desc_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # VLAN setting
        ttk.Label(main_frame, text="Access VLAN:").grid(row=1, column=0, sticky=tk.W, pady=5)
        vlan_var = tk.StringVar()
        if interface in self.current_interfaces:
            current_vlan = self.current_interfaces[interface].get('vlan', '1')
            if current_vlan.isdigit():
                vlan_var.set(current_vlan)
            else:
                vlan_var.set('1')
        else:
            vlan_var.set('1')
        vlan_entry = ttk.Entry(main_frame, textvariable=vlan_var, width=10)
        vlan_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        def apply_config():
            description = desc_var.get().strip()
            vlan = vlan_var.get().strip()
            
            if vlan and not vlan.isdigit():
                messagebox.showerror("Hata", "VLAN numarası geçerli bir sayı olmalıdır!")
                return
            
            dialog.destroy()
            self.apply_port_config(interface, description, int(vlan) if vlan else None)
        
        ttk.Button(button_frame, text="Uygula", command=apply_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="İptal", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def apply_port_config(self, interface, description, vlan):
        """Apply port configuration"""
        self.set_status(f"{interface} portu yapılandırılıyor...")
        
        def config_thread():
            try:
                success = True
                
                # Set description if provided
                if description:
                    if not self.cisco_manager.set_interface_description(interface, description):
                        success = False
                
                # Set VLAN if provided
                if vlan and success:
                    if not self.cisco_manager.set_interface_vlan(interface, vlan):
                        success = False
                
                if success:
                    self.root.after(0, lambda: self.set_status(f"{interface} portu yapılandırıldı"))
                    # Clear cache and immediate refresh for instant color update
                    self.cisco_manager.clear_cache()
                    time.sleep(0.1)  # Short delay for cache clear to take effect
                    self.root.after(100, self.refresh_interfaces)  # Immediate refresh after 100ms
                    # Anlık izlemeyi aktif et
                    if not self.fast_monitoring:
                        self.root.after(0, lambda: (self.fast_monitoring_var.set(True), self.toggle_fast_monitoring()))
                    # Add notification
                    config_details = []
                    if description:
                        config_details.append(f"Açıklama: {description}")
                    if vlan:
                        config_details.append(f"VLAN: {vlan}")
                    details_str = " | ".join(config_details) if config_details else "Yapılandırma"
                    self.root.after(0, lambda: self.add_notification(f"⚙️ {interface} - {details_str} güncellendi", "info"))
                    self.root.after(0, lambda: messagebox.showinfo("Başarılı", 
                                    f"{interface} portu başarıyla yapılandırıldı!"))
                else:
                    self.root.after(0, lambda: self.set_status(f"{interface} portu yapılandırılamadı"))
                    self.root.after(0, lambda: messagebox.showerror("Hata", 
                                    f"{interface} portu yapılandırılamadı!"))
                    
            except Exception as e:
                self.root.after(0, lambda: self.set_status(f"Hata: {e}"))
                self.root.after(0, lambda: messagebox.showerror("Hata", f"Port yapılandırma hatası:\n{e}"))
        
        threading.Thread(target=config_thread, daemon=True).start()

    def disable_unused_ports(self):
        """Disable all unused (notconnect) ports"""
        if not self.connected:
            messagebox.showwarning("Uyarı", "Önce bir cihaza bağlanın!")
            return
        
        if not self.current_interfaces:
            messagebox.showwarning("Uyarı", "Port bilgileri henüz yüklenmedi. Lütfen bekleyin.")
            return
        
        # Find unused ports
        unused_ports = []
        for interface, info in self.current_interfaces.items():
            status = info.get('status', '').lower()
            if status in ['notconnect', 'notconnected', 'down'] and not status in ['disabled', 'shutdown']:
                unused_ports.append(interface)
        
        if not unused_ports:
            messagebox.showinfo("Bilgi", "Kapatılacak kullanılmayan port bulunamadı.")
            return
        
        # Show confirmation dialog with details
        unused_count = len(unused_ports)
        confirm_msg = f"""
UYARI: GÜVENLİK İŞLEMİ

{unused_count} adet kullanılmayan port tespit edildi.
Bu portlar otomatik olarak kapatılacak (disabled).

KAPATILACAK PORTLAR:
{', '.join(unused_ports[:10])}{'...' if len(unused_ports) > 10 else ''}

Bu işlem geri alınamaz!
Devam etmek istediğinizden emin misiniz?
        """
        
        if not messagebox.askyesno("⚠️ Güvenlik Onayı", confirm_msg):
            return
        
        # Create progress dialog
        self.show_bulk_disable_progress(unused_ports)

    def enable_disabled_ports(self):
        """Enable all disabled/shutdown ports"""
        if not self.connected:
            messagebox.showwarning("Uyarı", "Önce bir cihaza bağlanın!")
            return
        
        if not self.current_interfaces:
            messagebox.showwarning("Uyarı", "Port bilgileri henüz yüklenmedi. Lütfen bekleyin.")
            return
        
        # Find disabled ports
        disabled_ports = []
        for interface, info in self.current_interfaces.items():
            status = info.get('status', '').lower()
            if status in ['disabled', 'shutdown', 'administratively down', 'admin down']:
                disabled_ports.append(interface)
        
        if not disabled_ports:
            messagebox.showinfo("Bilgi", "Açılacak kapalı port bulunamadı.")
            return
        
        # Show confirmation dialog with details
        disabled_count = len(disabled_ports)
        confirm_msg = f"""
ONAY: PORT AÇMA İŞLEMİ

{disabled_count} adet kapalı port tespit edildi.
Bu portlar otomatik olarak açılacak (enabled).

AÇILACAK PORTLAR:
{', '.join(disabled_ports[:10])}{'...' if len(disabled_ports) > 10 else ''}

Bu işlem tüm kapalı portları aktif hale getirecek!
Devam etmek istediğinizden emin misiniz?
        """
        
        if not messagebox.askyesno("✅ Port Açma Onayı", confirm_msg):
            return
        
        # Create progress dialog
        self.show_bulk_enable_progress(disabled_ports)

    def show_bulk_disable_progress(self, ports_to_disable):
        """Show progress dialog for bulk port disable operation"""
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("🔒 Kullanılmayan Portları Kapatma")
        progress_window.geometry("500x300")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Center the window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
        y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
        progress_window.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(progress_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Kullanılmayan Portlar Kapatılıyor", 
                               font=(config.ui.font_family, 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Progress info
        self.progress_info = tk.StringVar(value=f"0 / {len(ports_to_disable)} port işlendi")
        info_label = ttk.Label(main_frame, textvariable=self.progress_info)
        info_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar['maximum'] = len(ports_to_disable)
        
        # Current port being processed
        self.current_port_var = tk.StringVar(value="Başlatılıyor...")
        current_label = ttk.Label(main_frame, textvariable=self.current_port_var, 
                                 font=(config.ui.console_font, 10))
        current_label.pack(pady=(0, 10))
        
        # Results text area
        results_frame = ttk.LabelFrame(main_frame, text="İşlem Sonuçları")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.results_text = tk.Text(results_frame, height=8, wrap=tk.WORD, 
                                   font=(config.ui.console_font, 9))
        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, 
                                      command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scroll.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Control button (initially disabled)
        self.progress_close_btn = ttk.Button(main_frame, text="İşlem Devam Ediyor...", 
                                           state=tk.DISABLED)
        self.progress_close_btn.pack(pady=(10, 0))
        
        # Start the bulk operation
        self.bulk_disable_operation(ports_to_disable, progress_window)

    def show_bulk_enable_progress(self, ports_to_enable):
        """Show progress dialog for bulk port enable operation"""
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("🔓 Kapalı Portları Açma")
        progress_window.geometry("500x300")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Center the window
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - (progress_window.winfo_width() // 2)
        y = (progress_window.winfo_screenheight() // 2) - (progress_window.winfo_height() // 2)
        progress_window.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(progress_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Kapalı Portlar Açılıyor", 
                               font=(config.ui.font_family, 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Progress info
        self.enable_progress_info = tk.StringVar(value=f"0 / {len(ports_to_enable)} port işlendi")
        info_label = ttk.Label(main_frame, textvariable=self.enable_progress_info)
        info_label.pack(pady=(0, 10))
        
        # Progress bar
        self.enable_progress_bar = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.enable_progress_bar.pack(pady=(0, 20))
        self.enable_progress_bar['maximum'] = len(ports_to_enable)
        
        # Current port being processed
        self.enable_current_port_var = tk.StringVar(value="Başlatılıyor...")
        current_label = ttk.Label(main_frame, textvariable=self.enable_current_port_var, 
                                 font=(config.ui.console_font, 10))
        current_label.pack(pady=(0, 10))
        
        # Results text area
        results_frame = ttk.LabelFrame(main_frame, text="İşlem Sonuçları")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.enable_results_text = tk.Text(results_frame, height=8, wrap=tk.WORD, 
                                          font=(config.ui.console_font, 9))
        results_scroll = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, 
                                      command=self.enable_results_text.yview)
        self.enable_results_text.configure(yscrollcommand=results_scroll.set)
        
        self.enable_results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Control button (initially disabled)
        self.enable_progress_close_btn = ttk.Button(main_frame, text="İşlem Devam Ediyor...", 
                                                   state=tk.DISABLED)
        self.enable_progress_close_btn.pack(pady=(10, 0))
        
        # Start the bulk operation
        self.bulk_enable_operation(ports_to_enable, progress_window)

    def bulk_disable_operation(self, ports_to_disable, progress_window):
        """Perform optimized bulk disable operation using interface ranges"""
        def operation_thread():
            try:
                # Update progress display
                self.root.after(0, lambda: self.update_progress("Aralık hesaplanıyor...", 0))
                
                # Add initial message
                self.root.after(0, lambda: self.add_result_text("🔄 Optimize edilmiş toplu kapatma başlatılıyor...", "info"))
                self.root.after(0, lambda: self.add_result_text(f"📊 Toplam {len(ports_to_disable)} port kapatılacak", "info"))
                
                # Use optimized bulk disable with ranges
                results = self.cisco_manager.bulk_disable_interfaces_optimized(
                    ports_to_disable, 
                    max_batch_size=12
                )
                
                # Process results
                successful = 0
                failed = 0
                failed_ports = []
                
                for i, (port, success) in enumerate(results.items()):
                    # Update progress
                    self.root.after(0, lambda p=port, idx=i: self.update_progress(f"Sonuç: {p}", idx))
                    
                    if success:
                        successful += 1
                        result_msg = f"✅ {port} - Başarıyla kapatıldı (range)"
                        self.root.after(0, lambda msg=result_msg: self.add_result_text(msg, "success"))
                        # Add notification
                        self.root.after(0, lambda p=port: self.add_notification(f"🔒 {p} portu güvenlik için kapatıldı", "info"))
                    else:
                        failed += 1
                        failed_ports.append(port)
                        result_msg = f"❌ {port} - Kapatılamadı"
                        self.root.after(0, lambda msg=result_msg: self.add_result_text(msg, "error"))
                
                # Add performance summary
                total = len(ports_to_disable)
                perf_msg = f"⚡ Performans: Range komutları kullanıldı, buffer karışması önlendi"
                self.root.after(0, lambda: self.add_result_text(perf_msg, "info"))
                
                # Operation completed
                self.root.after(0, lambda: self.complete_bulk_operation(
                    successful, failed, total, failed_ports, progress_window
                ))
                
            except Exception as e:
                error_msg = f"Toplu işlem sırasında kritik hata: {e}"
                self.root.after(0, lambda: messagebox.showerror("Kritik Hata", error_msg))
                self.root.after(0, lambda: progress_window.destroy())
        
        # Start operation in background thread
        threading.Thread(target=operation_thread, daemon=True).start()

    def bulk_enable_operation(self, ports_to_enable, progress_window):
        """Perform optimized bulk enable operation using interface ranges"""
        def operation_thread():
            try:
                # Update progress display
                self.root.after(0, lambda: self.update_enable_progress("Aralık hesaplanıyor...", 0))
                
                # Add initial message
                self.root.after(0, lambda: self.add_enable_result_text("🔄 Optimize edilmiş toplu açma başlatılıyor...", "info"))
                self.root.after(0, lambda: self.add_enable_result_text(f"📊 Toplam {len(ports_to_enable)} port açılacak", "info"))
                
                # Use optimized bulk enable with ranges
                results = self.cisco_manager.bulk_enable_interfaces_optimized(
                    ports_to_enable, 
                    max_batch_size=12
                )
                
                # Process results
                successful = 0
                failed = 0
                failed_ports = []
                
                for i, (port, success) in enumerate(results.items()):
                    # Update progress
                    self.root.after(0, lambda p=port, idx=i: self.update_enable_progress(f"Sonuç: {p}", idx))
                    
                    if success:
                        successful += 1
                        result_msg = f"✅ {port} - Başarıyla açıldı (range)"
                        self.root.after(0, lambda msg=result_msg: self.add_enable_result_text(msg, "success"))
                        # Add notification
                        self.root.after(0, lambda p=port: self.add_notification(f"🔓 {p} portu açıldı", "success"))
                    else:
                        failed += 1
                        failed_ports.append(port)
                        result_msg = f"❌ {port} - Açılamadı"
                        self.root.after(0, lambda msg=result_msg: self.add_enable_result_text(msg, "error"))
                
                # Add performance summary
                total = len(ports_to_enable)
                perf_msg = f"⚡ Performans: Range komutları kullanıldı, buffer karışması önlendi"
                self.root.after(0, lambda: self.add_enable_result_text(perf_msg, "info"))
                
                # Operation completed
                self.root.after(0, lambda: self.complete_bulk_enable_operation(
                    successful, failed, total, failed_ports, progress_window
                ))
                
            except Exception as e:
                error_msg = f"Toplu açma işlemi sırasında kritik hata: {e}"
                self.root.after(0, lambda: messagebox.showerror("Kritik Hata", error_msg))
                self.root.after(0, lambda: progress_window.destroy())
        
        # Start operation in background thread
        threading.Thread(target=operation_thread, daemon=True).start()

    def update_progress(self, current_port, index):
        """Update progress display"""
        self.current_port_var.set(f"İşleniyor: {current_port}")
        self.progress_bar['value'] = index + 1
        self.progress_info.set(f"{index + 1} / {self.progress_bar['maximum']} port işlendi")

    def update_enable_progress(self, current_port, index):
        """Update enable progress display"""
        self.enable_current_port_var.set(f"İşleniyor: {current_port}")
        self.enable_progress_bar['value'] = index + 1
        self.enable_progress_info.set(f"{index + 1} / {self.enable_progress_bar['maximum']} port işlendi")

    def add_result_text(self, message, msg_type):
        """Add result message to text area"""
        self.results_text.config(state=tk.NORMAL)
        
        # Color coding
        if msg_type == "success":
            self.results_text.insert(tk.END, message + "\n", "success")
        elif msg_type == "error":
            self.results_text.insert(tk.END, message + "\n", "error")
        else:
            self.results_text.insert(tk.END, message + "\n")
        
        # Configure text colors
        self.results_text.tag_configure("success", foreground="green")
        self.results_text.tag_configure("error", foreground="red")
        
        # Auto-scroll to bottom
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)

    def add_enable_result_text(self, message, msg_type):
        """Add enable result message to text area"""
        self.enable_results_text.config(state=tk.NORMAL)
        
        # Color coding
        if msg_type == "success":
            self.enable_results_text.insert(tk.END, message + "\n", "success")
        elif msg_type == "error":
            self.enable_results_text.insert(tk.END, message + "\n", "error")
        else:
            self.enable_results_text.insert(tk.END, message + "\n")
        
        # Configure text colors
        self.enable_results_text.tag_configure("success", foreground="green")
        self.enable_results_text.tag_configure("error", foreground="red")
        
        # Auto-scroll to bottom
        self.enable_results_text.see(tk.END)
        self.enable_results_text.config(state=tk.DISABLED)

    def complete_bulk_operation(self, successful, failed, total, failed_ports, progress_window):
        """Complete the bulk operation and show final results"""
        self.current_port_var.set("✅ İşlem Tamamlandı!")
        
        # Final summary
        summary_msg = f"\n{'='*50}\n"
        summary_msg += f"TOPLU İŞLEM SONUCU:\n"
        summary_msg += f"Toplam Port: {total}\n"
        summary_msg += f"Başarılı: {successful}\n"
        summary_msg += f"Başarısız: {failed}\n"
        
        if failed_ports:
            summary_msg += f"\nBaşarısız Portlar: {', '.join(failed_ports[:5])}"
            if len(failed_ports) > 5:
                summary_msg += f"... (+{len(failed_ports)-5} daha)"
        
        summary_msg += f"\n{'='*50}"
        
        self.add_result_text(summary_msg, "info")
        
        # Enable close button
        self.progress_close_btn.config(
            text="Kapat", 
            state=tk.NORMAL,
            command=progress_window.destroy
        )
        
        # Add final notification
        if successful > 0:
            self.add_notification(f"🔒 Güvenlik: {successful} kullanılmayan port kapatıldı", "success")
        
        # Immediate refresh with cache clear for instant color update
        self.cisco_manager.clear_cache()  # Clear cache to force fresh data
        time.sleep(0.2)  # Delay for cache clear and port state stabilization
        self.root.after(200, self.refresh_interfaces)  # Refresh after 200ms
        
        # Show completion message
        if failed == 0:
            messagebox.showinfo("✅ Başarılı", f"Tüm {successful} kullanılmayan port başarıyla kapatıldı!")
        else:
            messagebox.showwarning("⚠️ Kısmi Başarı", 
                                 f"{successful} port kapatıldı, {failed} port kapatılamadı.")

    def complete_bulk_enable_operation(self, successful, failed, total, failed_ports, progress_window):
        """Complete the bulk enable operation and show final results"""
        self.enable_current_port_var.set("✅ İşlem Tamamlandı!")
        
        # Final summary
        summary_msg = f"\n{'='*50}\n"
        summary_msg += f"TOPLU AÇMA İŞLEMİ SONUCU:\n"
        summary_msg += f"Toplam Port: {total}\n"
        summary_msg += f"Başarılı: {successful}\n"
        summary_msg += f"Başarısız: {failed}\n"
        
        if failed_ports:
            summary_msg += f"\nBaşarısız Portlar: {', '.join(failed_ports[:5])}"
            if len(failed_ports) > 5:
                summary_msg += f"... (+{len(failed_ports)-5} daha)"
        
        summary_msg += f"\n{'='*50}"
        
        self.add_enable_result_text(summary_msg, "info")
        
        # Enable close button
        self.enable_progress_close_btn.config(
            text="Kapat", 
            state=tk.NORMAL,
            command=progress_window.destroy
        )
        
        # Add final notification
        if successful > 0:
            self.add_notification(f"🔓 Toplu Açma: {successful} kapalı port açıldı", "success")
        
        # Immediate refresh with cache clear for instant color update
        self.cisco_manager.clear_cache()  # Clear cache to force fresh data
        time.sleep(0.2)  # Delay for cache clear and port state stabilization
        self.root.after(200, self.refresh_interfaces)  # Refresh after 200ms
        
        # Show completion message
        if failed == 0:
            messagebox.showinfo("✅ Başarılı", f"Tüm {successful} kapalı port başarıyla açıldı!")
        else:
            messagebox.showwarning("⚠️ Kısmi Başarı", 
                                 f"{successful} port açıldı, {failed} port açılamadı.")

    def add_notification(self, message, msg_type="info"):
        """Add notification to the notification panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to notifications list
        self.notifications.append({
            'timestamp': timestamp,
            'message': message,
            'type': msg_type
        })
        
        # Keep only last 50 notifications
        if len(self.notifications) > 50:
            self.notifications = self.notifications[-50:]
        
        # Update notification display
        self.notification_text.config(state=tk.NORMAL)
        
        # Insert timestamp
        self.notification_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Insert message with appropriate color
        self.notification_text.insert(tk.END, f"{message}\n", msg_type)
        
        # Auto-scroll to bottom
        self.notification_text.see(tk.END)
        
        self.notification_text.config(state=tk.DISABLED)

    def clear_notifications(self):
        """Clear all notifications"""
        self.notifications.clear()
        self.notification_text.config(state=tk.NORMAL)
        self.notification_text.delete(1.0, tk.END)
        self.notification_text.config(state=tk.DISABLED)

    def check_interface_changes(self, new_interfaces):
        """Check for interface status changes and notify"""
        if not self.previous_interfaces or not self.connected:
            return
        
        for interface, new_info in new_interfaces.items():
            old_info = self.previous_interfaces.get(interface, {})
            old_status = old_info.get('status', '').lower()
            new_status = new_info.get('status', '').lower()
            
            # Check for status changes
            if old_status != new_status:
                if new_status in ['connected', 'up']:
                    if old_status in ['notconnect', 'down', 'shutdown']:
                        vlan = new_info.get('vlan', 'N/A')
                        speed = new_info.get('speed', 'N/A')
                        msg = f"🟢 {interface} - Yeni bağlantı! VLAN: {vlan}, Hız: {speed}"
                        self.add_notification(msg, "success")
                        
                        # Try to get MAC address for this port
                        self.check_new_device_on_port(interface)
                        
                elif new_status in ['notconnect', 'down', 'shutdown']:
                    if old_status in ['connected', 'up']:
                        msg = f"🔴 {interface} - Bağlantı kesildi!"
                        self.add_notification(msg, "warning")
                        
                elif new_status == 'disabled':
                    msg = f"⚫ {interface} - Port devre dışı bırakıldı"
                    self.add_notification(msg, "info")
        
        # Check for new interfaces
        for interface in new_interfaces:
            if interface not in self.previous_interfaces:
                status = new_interfaces[interface].get('status', '').lower()
                if status in ['connected', 'up']:
                    msg = f"🆕 {interface} - Yeni port tespit edildi (Aktif)"
                    self.add_notification(msg, "info")

    def check_new_device_on_port(self, interface):
        """Check for new device connected to port (async)"""
        def check_mac_thread():
            try:
                # Small delay to let the device settle
                time.sleep(2)
                
                mac_table = self.cisco_manager.get_mac_address_table()
                for entry in mac_table:
                    if interface in entry.get('ports', ''):
                        mac = entry.get('mac_address', 'Unknown')
                        vlan = entry.get('vlan', 'N/A')
                        msg = f"💻 {interface} - Yeni cihaz: MAC {mac} (VLAN {vlan})"
                        self.root.after(0, lambda: self.add_notification(msg, "info"))
                        break
                        
            except Exception as e:
                logger.debug(f"Could not check MAC for {interface}: {e}")
        
        if self.connected:
            threading.Thread(target=check_mac_thread, daemon=True).start()

    def toggle_auto_refresh(self):
        """Toggle auto refresh functionality"""
        self.auto_refresh = self.auto_refresh_var.get()
        
        # If fast monitoring is on, turn it off when normal auto refresh is enabled
        if self.auto_refresh and self.fast_monitoring:
            self.fast_monitoring = False
            self.fast_monitoring_var.set(False)
        
        if self.auto_refresh and self.connected:
            self.auto_refresh_loop()
        
    def toggle_fast_monitoring(self):
        """Toggle fast monitoring functionality for real-time updates"""
        self.fast_monitoring = self.fast_monitoring_var.get()
        
        # If fast monitoring is enabled, turn off normal auto refresh
        if self.fast_monitoring:
            self.auto_refresh = False
            self.auto_refresh_var.set(False)
            if self.connected:
                self.fast_refresh_loop()
        
    def auto_refresh_loop(self):
        """Auto refresh loop"""
        if self.auto_refresh and self.connected and not self.fast_monitoring:
            self.refresh_interfaces()  # Only refresh interfaces for speed
            self.root.after(int(self.refresh_interval * 1000), self.auto_refresh_loop)
    
    def fast_refresh_loop(self):
        """Fast refresh loop for real-time monitoring"""
        if self.fast_monitoring and self.connected:
            self.refresh_interfaces()  # Ultra fast interface refresh only
            self.root.after(int(self.fast_refresh_interval * 1000), self.fast_refresh_loop)

    def clear_data(self):
        """Clear all displayed data"""
        # Clear device info
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Clear interface tree
        for item in self.interface_tree.get_children():
            self.interface_tree.delete(item)
        
        self.current_interfaces = {}

    def set_status(self, message):
        """Set status bar message"""
        self.status_var.set(message)
        self.root.update_idletasks()

    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)

    def show_connection_dialog(self):
        """Show connection dialog"""
        if self.connected:
            messagebox.showinfo("Bilgi", "Zaten bir cihaza bağlısınız!")
            return
        
        self.connect()

    def save_config(self):
        """Save device configuration"""
        if not self.connected:
            messagebox.showwarning("Uyarı", "Önce bir cihaza bağlanın!")
            return
        
        if messagebox.askyesno("Onay", "Konfigürasyonu kaydetmek istediğinizden emin misiniz?"):
            self.set_status("Konfigürasyon kaydediliyor...")
            
            def save_thread():
                try:
                    success = self.cisco_manager.save_config()
                    if success:
                        self.root.after(0, lambda: self.set_status("Konfigürasyon kaydedildi"))
                        self.root.after(0, lambda: messagebox.showinfo("Başarılı", 
                                        "Konfigürasyon başarıyla kaydedildi!"))
                    else:
                        self.root.after(0, lambda: self.set_status("Konfigürasyon kaydedilemedi"))
                        self.root.after(0, lambda: messagebox.showerror("Hata", 
                                        "Konfigürasyon kaydedilemedi!"))
                except Exception as e:
                    self.root.after(0, lambda: self.set_status(f"Hata: {e}"))
                    self.root.after(0, lambda: messagebox.showerror("Hata", f"Kaydetme hatası:\n{e}"))
            
            threading.Thread(target=save_thread, daemon=True).start()

    def show_mac_table(self):
        """Show MAC address table"""
        if not self.connected:
            messagebox.showwarning("Uyarı", "Önce bir cihaza bağlanın!")
            return
        
        self.show_table_window("MAC Adres Tablosu", self.get_mac_table_data, 
                              ['VLAN', 'MAC Adresi', 'Tip', 'Port'])

    def show_arp_table(self):
        """Show ARP table"""
        if not self.connected:
            messagebox.showwarning("Uyarı", "Önce bir cihaza bağlanın!")
            return
        
        self.show_table_window("ARP Tablosu", self.get_arp_table_data, 
                              ['IP Adresi', 'Yaş', 'MAC Adresi', 'Tip', 'Arayüz'])

    def get_mac_table_data(self):
        """Get MAC table data"""
        try:
            return self.cisco_manager.get_mac_address_table()
        except Exception as e:
            logger.error(f"Error getting MAC table: {e}")
            return []

    def get_arp_table_data(self):
        """Get ARP table data"""
        try:
            return self.cisco_manager.get_arp_table()
        except Exception as e:
            logger.error(f"Error getting ARP table: {e}")
            return []

    def show_table_window(self, title, data_func, columns):
        """Show a table window with given data"""
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("800x600")
        window.transient(self.root)
        
        # Create treeview
        frame = ttk.Frame(window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tree = ttk.Treeview(frame, columns=columns[1:], show='tree headings')
        
        # Configure columns
        tree.heading('#0', text=columns[0])
        for i, col in enumerate(columns[1:], 1):
            tree.heading(f'#{i}', text=col)
            tree.column(f'#{i}', width=120)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        h_scroll = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack
        tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        # Load data
        def load_data():
            self.set_status(f"{title} yükleniyor...")
            
            def data_thread():
                try:
                    data = data_func()
                    
                    def update_tree():
                        for item in tree.get_children():
                            tree.delete(item)
                        
                        for entry in data:
                            if isinstance(entry, dict):
                                values = list(entry.values())
                                if values:
                                    tree.insert('', 'end', text=values[0], values=values[1:])
                        
                        self.set_status(f"{title} yüklendi - {len(data)} kayıt")
                    
                    window.after(0, update_tree)
                    
                except Exception as e:
                    window.after(0, lambda: self.set_status(f"Veri yükleme hatası: {e}"))
                    window.after(0, lambda: messagebox.showerror("Hata", f"Veri yüklenemedi:\n{e}"))
            
            threading.Thread(target=data_thread, daemon=True).start()
        
        # Refresh button
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Yenile", command=load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kapat", command=window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Load initial data
        load_data()

    def show_performance_report(self):
        """Show performance report"""
        try:
            if hasattr(self.performance_dashboard, 'generate_performance_report'):
                self.performance_dashboard.generate_performance_report()
            else:
                messagebox.showinfo("Performans Raporu", "Performans raporu özelliği henüz aktif değil.")
        except Exception as e:
            messagebox.showerror("Hata", f"Performans raporu gösterilemedi: {e}")
    
    def run_health_check(self):
        """Run health check"""
        try:
            if hasattr(self.performance_dashboard, 'run_health_check'):
                self.performance_dashboard.run_health_check()
            else:
                messagebox.showinfo("Sağlık Kontrolü", "Sağlık kontrolü özelliği henüz aktif değil.")
        except Exception as e:
            messagebox.showerror("Hata", f"Sağlık kontrolü çalıştırılamadı: {e}")
    
    def clear_cache(self):
        """Clear all caches"""
        try:
            self.cisco_manager.clear_cache()
            messagebox.showinfo("Başarılı", "Tüm cache temizlendi!")
        except Exception as e:
            messagebox.showerror("Hata", f"Cache temizlenemedi: {e}")
    
    def show_cache_stats(self):
        """Show cache statistics"""
        try:
            if hasattr(self.performance_dashboard, 'show_detailed_cache_stats'):
                self.performance_dashboard.show_detailed_cache_stats()
            else:
                messagebox.showinfo("Cache İstatistikleri", "Cache istatistikleri özelliği henüz aktif değil.")
        except Exception as e:
            messagebox.showerror("Hata", f"Cache istatistikleri gösterilemedi: {e}")
    
    def show_performance_tab(self):
        """Switch to performance monitoring tab"""
        try:
            self.main_notebook.select(1)  # Select performance tab
        except Exception as e:
            messagebox.showerror("Hata", f"Performans sekmesi açılamadı: {e}")
    
    def show_system_status(self):
        """Show system status"""
        try:
            stats = self.cisco_manager.get_performance_stats()
            health = self.cisco_manager.health_check()
            
            status_text = f"""
SISTEM DURUMU RAPORU
==================

Bağlantı Durumu: {"✅ Bağlı" if self.connected else "❌ Bağlı Değil"}
Bağlantı Sağlık: {"✅ Sağlıklı" if health.get('connection_healthy', False) else "❌ Sorunlu"}

PERFORMANS İSTATİSTİKLERİ:
- Toplam Komut: {stats.get('command_stats', {}).get('commands_executed', 0)}
- Cache Hit Rate: {stats.get('command_stats', {}).get('cache_hit_rate', 0):.1f}%
- Hata Oranı: {stats.get('command_stats', {}).get('error_rate', 0):.1f}%
- Bellek Kullanımı: {stats.get('memory_usage', {}).get('total_cache_memory', 0) // (1024*1024):.1f} MB

CACHE DURUMU:
- Interface Cache: {stats.get('cache_stats', {}).get('interface', {}).get('hit_rate', 0):.1f}%
- Command Cache: {stats.get('cache_stats', {}).get('command', {}).get('hit_rate', 0):.1f}%
- MAC Cache: {stats.get('cache_stats', {}).get('mac', {}).get('hit_rate', 0):.1f}%
            """
            
            messagebox.showinfo("Sistem Durumu", status_text)
        except Exception as e:
            messagebox.showerror("Hata", f"Sistem durumu alınamadı: {e}")
    
    def show_settings(self):
        """Show general settings"""
        messagebox.showinfo("Ayarlar", "Genel ayarlar özelliği geliştirilme aşamasında.")
    
    def show_performance_settings(self):
        """Show performance settings"""
        messagebox.showinfo("Performans Ayarları", "Performans ayarları özelliği geliştirilme aşamasında.")
    
    def reset_settings(self):
        """Reset settings to default"""
        if messagebox.askyesno("Onay", "Tüm ayarları varsayılana sıfırlamak istediğinizden emin misiniz?"):
            try:
                config.reset_to_defaults()
                messagebox.showinfo("Başarılı", "Ayarlar varsayılana sıfırlandı. Uygulamayı yeniden başlatın.")
            except Exception as e:
                messagebox.showerror("Hata", f"Ayarlar sıfırlanamadı: {e}")
    
    def show_help(self):
        """Show help"""
        help_text = """
CISCO SWITCH MANAGER - KULLANIM KILAVUZU
========================================

BAĞLANTI:
1. Sol panelde IP, kullanıcı adı ve şifre girin
2. "Bağlan" butonuna tıklayın
3. Bağlantı başarılı olduğunda otomatik yenileme başlar

PORT YÖNETİMİ:
1. Sağ panelde port listesini görün
2. Port seçip etkinleştir/devre dışı bırak
3. "Port Ayarları" ile VLAN ve açıklama değiştirin

PERFORMANS İZLEME:
1. "Performans İzleme" sekmesine gidin
2. "İzlemeyi Başlat" ile anlık takip yapın
3. Cache ve sistem performansını izleyin

MENÜ ÖZELLİKLERİ:
- Araçlar > MAC/ARP tabloları
- Performans > Cache yönetimi
- Ayarlar > Konfigürasyon
        """
        
        messagebox.showinfo("Kullanım Kılavuzu", help_text)
    
    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = """
KISAYOL TUŞLARI
===============

F1: Yardım
F5: Yenile
F12: Performans sekmesi
Ctrl+D: Bağlantıyı kes
Ctrl+S: Konfigürasyonu kaydet
Ctrl+R: Cache temizle
Ctrl+H: Sağlık kontrolü
Ctrl+Shift+D: Kullanılmayan portları kapat (Güvenlik)
Ctrl+Shift+E: Kapalı portları aç (Toplu)
Esc: Seçimi temizle

💡 İpuçları:
• Ctrl+Shift+D: Tüm "notconnect" portları güvenlik için otomatik kapatır
• Ctrl+Shift+E: Tüm "disabled" portları toplu olarak açar
• ⚡ Anlık İzleme: Kablo takınca anında yeşil, çıkarınca anında kırmızı!
        """
        
        messagebox.showinfo("Kısayol Tuşları", shortcuts_text)

    def clear_selection(self):
        """Clear interface selection"""
        try:
            self.interface_tree.selection_remove(self.interface_tree.selection())
            self.enable_port_btn.config(state=tk.DISABLED)
            self.disable_port_btn.config(state=tk.DISABLED)
            self.config_port_btn.config(state=tk.DISABLED)
        except Exception:
            pass  # Ignore errors if nothing selected

    def show_about(self):
        """Show about dialog"""
        about_text = """
Cisco Switch Manager - Professional Edition
Version: 2.0.0

Cisco 9300 Catalyst switch'ler için profesyonel yönetim arayüzü.

Özellikler:
• SSH ile güvenli bağlantı
• Anlık port durumu izleme
• Port etkinleştirme/devre dışı bırakma
• VLAN yapılandırması
• Port açıklama ayarlama
• MAC adres tablosu görüntüleme
• ARP tablosu görüntüleme
• Otomatik veri yenileme
• Konfigürasyon kaydetme
• Gerçek zamanlı port uyarıları
• Cihaz bağlantı takibi (MAC)
• Profesyonel performans izleme
• Akıllı cache sistemi
• Detaylı sistem raporları

© 2024 Professional Network Management Team
        """
        
        messagebox.showinfo("Hakkında", about_text)

    def on_closing(self):
        """Handle application closing"""
        if self.connected:
            if messagebox.askyesno("Çıkış", "Bağlantı aktif. Çıkmak istediğinizden emin misiniz?"):
                self.cisco_manager.disconnect()
                self.root.destroy()
        else:
            self.root.destroy()

    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = CiscoGUI()
    app.run() 