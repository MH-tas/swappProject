import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime
import threading
import time

class ModernFrame(tk.Frame):
    """Modern styled frame with gradient-like appearance"""
    def __init__(self, parent, bg_color='#2c3e50', **kwargs):
        # Remove bg from kwargs if it exists to avoid conflict
        kwargs.pop('bg', None)
        super().__init__(parent, bg=bg_color, relief='flat', bd=0, **kwargs)

class StatusBar(tk.Frame):
    """Professional status bar with multiple indicators"""
    def __init__(self, parent):
        super().__init__(parent, bg='#34495e', height=25)
        self.pack_propagate(False)
        
        # Connection status
        self.connection_label = tk.Label(self, text="● Disconnected", 
                                       bg='#34495e', fg='#e74c3c', font=('Arial', 9))
        self.connection_label.pack(side=tk.LEFT, padx=10)
        
        # Device info
        self.device_label = tk.Label(self, text="No Device", 
                                   bg='#34495e', fg='#bdc3c7', font=('Arial', 9))
        self.device_label.pack(side=tk.LEFT, padx=10)
        
        # Last update time
        self.time_label = tk.Label(self, text="", 
                                 bg='#34495e', fg='#bdc3c7', font=('Arial', 9))
        self.time_label.pack(side=tk.RIGHT, padx=10)
        
        self.update_time()
    
    def update_connection_status(self, connected, device_info=None):
        if connected:
            self.connection_label.config(text="● Connected", fg='#27ae60')
            if device_info:
                model = device_info.get('model', 'Unknown')
                self.device_label.config(text=f"Device: {model}")
        else:
            self.connection_label.config(text="● Disconnected", fg='#e74c3c')
            self.device_label.config(text="No Device")
    
    def update_time(self):
        current_time = datetime.now().strftime('%H:%M:%S')
        self.time_label.config(text=current_time)
        self.after(1000, lambda: self.update_time())

class ConnectionPanel(ModernFrame):
    """Advanced connection panel with multiple device support"""
    def __init__(self, parent, connect_callback=None):
        super().__init__(parent, bg_color='#34495e')
        self.connect_callback = connect_callback
        self.setup_ui()
    
    def setup_ui(self):
        # Title
        title_label = tk.Label(self, text="🌐 Network Connection Manager", 
                             bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=6, pady=10, sticky='ew')
        
        # Connection fields
        fields = [
            ("Host IP:", "host_entry", "192.168.20.1"),
            ("Username:", "username_entry", "swapp"),
            ("Password:", "password_entry", ""),
            ("Enable Secret:", "secret_entry", ""),
            ("Port:", "port_entry", "22"),
            ("Device Type:", "device_type_combo", "cisco_ios")
        ]
        
        self.entries = {}
        
        for i, (label_text, entry_name, default_value) in enumerate(fields):
            # Label
            label = tk.Label(self, text=label_text, bg='#34495e', fg='white', font=('Arial', 9))
            label.grid(row=1, column=i, padx=5, pady=5, sticky='w')
            
            # Entry or Combobox
            if entry_name == "device_type_combo":
                widget = ttk.Combobox(self, width=12, values=[
                    'cisco_ios', 'cisco_xe', 'cisco_nxos', 'cisco_asa', 'cisco_wlc'
                ])
                widget.set(default_value)
            elif "password" in entry_name or "secret" in entry_name:
                widget = tk.Entry(self, width=12, show="*", bg='#ecf0f1', relief='flat')
            else:
                widget = tk.Entry(self, width=12, bg='#ecf0f1', relief='flat')
                widget.insert(0, default_value)
            
            widget.grid(row=2, column=i, padx=5, pady=5)
            self.entries[entry_name] = widget
        
        # Action buttons
        button_frame = tk.Frame(self, bg='#34495e')
        button_frame.grid(row=3, column=0, columnspan=6, pady=10)
        
        # Connect button
        self.connect_btn = tk.Button(button_frame, text="🔗 Connect", 
                                   command=self.connect,
                                   bg='#27ae60', fg='white', font=('Arial', 9, 'bold'),
                                   width=12, relief='flat', cursor='hand2')
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        # Disconnect button
        self.disconnect_btn = tk.Button(button_frame, text="🔌 Disconnect", 
                                      command=self.disconnect,
                                      bg='#e74c3c', fg='white', font=('Arial', 9, 'bold'),
                                      width=12, relief='flat', cursor='hand2', state='disabled')
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Quick connect presets
        preset_btn = tk.Button(button_frame, text="📋 Presets", 
                             command=self.show_presets,
                             bg='#3498db', fg='white', font=('Arial', 9, 'bold'),
                             width=12, relief='flat', cursor='hand2')
        preset_btn.pack(side=tk.LEFT, padx=5)
    
    def connect(self):
        """Connect to device"""
        if self.connect_callback:
            connection_data = {
                'host': self.entries['host_entry'].get(),
                'username': self.entries['username_entry'].get(),
                'password': self.entries['password_entry'].get(),
                'secret': self.entries['secret_entry'].get(),
                'port': int(self.entries['port_entry'].get()) if self.entries['port_entry'].get().isdigit() else 22,
                'device_type': self.entries['device_type_combo'].get()
            }
            
            self.connect_btn.config(state='disabled', text='Connecting...')
            threading.Thread(target=self._connect_thread, args=(connection_data,), daemon=True).start()
    
    def _connect_thread(self, connection_data):
        success, message = self.connect_callback(connection_data)
        self.after(0, self._connection_result, success, message)
    
    def _connection_result(self, success, message):
        if success:
            self.connect_btn.config(state='disabled', text='🔗 Connected')
            self.disconnect_btn.config(state='normal')
        else:
            self.connect_btn.config(state='normal', text='🔗 Connect')
            messagebox.showerror("Connection Error", message)
    
    def disconnect(self):
        """Disconnect from device"""
        if self.connect_callback:
            # Assume we have a disconnect method
            self.connect_btn.config(state='normal', text='🔗 Connect')
            self.disconnect_btn.config(state='disabled')
    
    def show_presets(self):
        """Show connection presets dialog"""
        preset_window = tk.Toplevel(self)
        preset_window.title("Connection Presets")
        preset_window.geometry("400x300")
        preset_window.configure(bg='#2c3e50')
        
        # Sample presets (in real app, these would be saved/loaded)
        presets = [
            {"name": "Production Switch", "host": "192.168.1.1", "username": "admin"},
            {"name": "Test Lab", "host": "192.168.20.1", "username": "swapp"},
            {"name": "Core Switch", "host": "10.0.0.1", "username": "network"}
        ]
        
        listbox = tk.Listbox(preset_window, bg='#34495e', fg='white', 
                           selectbackground='#3498db', font=('Arial', 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for preset in presets:
            listbox.insert(tk.END, f"{preset['name']} ({preset['host']})")

class PortVisualization(ModernFrame):
    """Advanced port visualization with real-time monitoring"""
    def __init__(self, parent, port_count=48):
        super().__init__(parent, bg='#2c3e50')
        self.port_count = port_count
        self.port_widgets = []
        self.port_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        # Title with controls
        header_frame = tk.Frame(self, bg='#2c3e50')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = tk.Label(header_frame, text="🔌 Port Status Dashboard", 
                             bg='#2c3e50', fg='white', font=('Arial', 14, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        # View controls
        control_frame = tk.Frame(header_frame, bg='#2c3e50')
        control_frame.pack(side=tk.RIGHT)
        
        tk.Label(control_frame, text="View:", bg='#2c3e50', fg='white').pack(side=tk.LEFT, padx=5)
        
        self.view_var = tk.StringVar(value="Grid")
        view_combo = ttk.Combobox(control_frame, textvariable=self.view_var, 
                                width=10, values=["Grid", "List", "Statistics"])
        view_combo.pack(side=tk.LEFT, padx=5)
        view_combo.bind('<<ComboboxSelected>>', self.change_view)
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        auto_check = tk.Checkbutton(control_frame, text="Auto Refresh", 
                                  variable=self.auto_refresh_var,
                                  bg='#2c3e50', fg='white', selectcolor='#34495e')
        auto_check.pack(side=tk.LEFT, padx=10)
        
        # Main container
        self.main_container = tk.Frame(self, bg='#2c3e50')
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create grid view by default
        self.create_grid_view()
        
        # Legend
        self.create_legend()
    
    def create_grid_view(self):
        """Create realistic switch port layout (48 ports in 4 groups of 12)"""
        # Clear existing widgets
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Create main container with switch background
        switch_frame = tk.Frame(self.main_container, bg='#1a1a1a', relief='solid', bd=2)
        switch_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Switch title/model
        title_frame = tk.Frame(switch_frame, bg='#1a1a1a')
        title_frame.pack(fill=tk.X, pady=10)
        
        model_label = tk.Label(title_frame, text="Cisco Catalyst 9300", 
                              bg='#1a1a1a', fg='white', font=('Arial', 14, 'bold'))
        model_label.pack()
        
        # Port groups container
        ports_container = tk.Frame(switch_frame, bg='#1a1a1a')
        ports_container.pack(expand=True, fill=tk.BOTH, padx=20, pady=10)
        
        self.port_widgets = []
        
        # Create 4 groups of 12 ports each (total 48 ports)
        # Layout: Group 1: Ports 1-12, Group 2: Ports 13-24, Group 3: Ports 25-36, Group 4: Ports 37-48
        for group in range(4):
            group_frame = tk.Frame(ports_container, bg='#2a2a2a', relief='solid', bd=1)
            group_frame.grid(row=0, column=group, padx=5, pady=5, sticky='nsew')
            
            # Group label
            start_port = group * 12 + 1
            end_port = (group + 1) * 12
            group_label = tk.Label(group_frame, text=f"Ports {start_port}-{end_port}", 
                                 bg='#2a2a2a', fg='#cccccc', font=('Arial', 9, 'bold'))
            group_label.pack(pady=5)
            
            # Create 2 rows of 6 ports each for this group
            ports_grid = tk.Frame(group_frame, bg='#2a2a2a')
            ports_grid.pack(padx=10, pady=5)
            
            # Create ports in Cisco physical layout: odd numbers top row, even numbers bottom row
            # Top row: 1, 3, 5, 7, 9, 11    Bottom row: 2, 4, 6, 8, 10, 12
            for local_port in range(1, 13):  # 1 to 12 within this group
                port_num = group * 12 + local_port  # Global port number
                
                # Calculate grid position: odd ports top row, even ports bottom row
                if local_port % 2 == 1:  # Odd numbers (1,3,5,7,9,11)
                    row = 0  # Top row
                    col = (local_port - 1) // 2  # Column 0-5
                else:  # Even numbers (2,4,6,8,10,12)
                    row = 1  # Bottom row
                    col = (local_port - 2) // 2  # Column 0-5
                
                # Port frame with realistic switch port look
                port_frame = tk.Frame(ports_grid, bg='#ff8c00', relief='solid', bd=1, 
                                    width=35, height=25)  # Orange/amber default color
                port_frame.grid(row=row, column=col, padx=1, pady=1)
                port_frame.grid_propagate(False)
                
                # Port number label (small text below port)
                port_label = tk.Label(ports_grid, text=str(port_num), 
                                    bg='#2a2a2a', fg='white', font=('Arial', 7))
                port_label.grid(row=row+3, column=col, pady=1)  # Row +3 to place below both port rows
                
                # Status text on the port
                status_text = tk.Label(port_frame, text="---", 
                                     bg='#ff8c00', fg='black', font=('Arial', 6, 'bold'))
                status_text.place(relx=0.5, rely=0.5, anchor='center')
                
                # Bind click events
                def make_click_handler(port_number):
                    return lambda e: self.show_port_details(port_number)
                
                click_handler = make_click_handler(port_num)
                port_frame.bind("<Button-1>", click_handler)
                status_text.bind("<Button-1>", click_handler)
                port_label.bind("<Button-1>", click_handler)
                
                # Bind hover events for tooltip
                def make_tooltip_handler(port_number):
                    return lambda e: self.show_port_tooltip(e, port_number)
                
                def hide_tooltip_handler(e):
                    self.hide_port_tooltip()
                
                tooltip_handler = make_tooltip_handler(port_num)
                
                # Bind events to port frame and status text
                for widget in [port_frame, status_text]:
                    widget.bind("<Enter>", tooltip_handler)
                    widget.bind("<Leave>", hide_tooltip_handler)
                    # Also bind to mouse movement to ensure tooltips work properly
                    widget.bind("<Motion>", lambda e, pn=port_num: self.on_port_motion(e, pn))
                
                # Also bind to label to ensure consistent behavior
                port_label.bind("<Enter>", tooltip_handler)
                port_label.bind("<Leave>", hide_tooltip_handler)
                
                # Store widget references
            self.port_widgets.append({
                'frame': port_frame,
                'label': port_label,
                    'status': status_text,
                    'port_num': port_num
            })
        
        # Configure grid weights for equal spacing
        for i in range(4):
            ports_container.grid_columnconfigure(i, weight=1)
    
    def create_list_view(self):
        """Create list view of ports"""
        # Clear existing widgets
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Create treeview
        columns = ('Port', 'Status', 'VLAN', 'Speed', 'Duplex', 'Type')
        tree = ttk.Treeview(self.main_container, columns=columns, show='headings', height=15)
        
        # Define headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=tree.yview)
        h_scrollbar = ttk.Scrollbar(self.main_container, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack
        tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.port_tree = tree
    
    def create_statistics_view(self):
        """Create statistics view with charts"""
        # Clear existing widgets
        for widget in self.main_container.winfo_children():
            widget.destroy()
        
        # Create matplotlib figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.patch.set_facecolor('#2c3e50')
        
        # Port status pie chart
        statuses = ['Connected', 'Disconnected', 'Disabled', 'Error']
        sizes = [15, 20, 10, 3]  # Sample data
        colors = ['#27ae60', '#e74c3c', '#95a5a6', '#f39c12']
        
        ax1.pie(sizes, labels=statuses, colors=colors, autopct='%1.1f%%')
        ax1.set_title('Port Status Distribution', color='white')
        
        # VLAN distribution
        vlans = ['VLAN 1', 'VLAN 10', 'VLAN 20', 'VLAN 30']
        vlan_counts = [20, 15, 8, 5]
        
        ax2.bar(vlans, vlan_counts, color='#3498db')
        ax2.set_title('VLAN Distribution', color='white')
        ax2.tick_params(colors='white')
        
        # Traffic over time (sample data)
        time_points = list(range(24))
        traffic_data = [np.random.randint(100, 1000) for _ in range(24)]
        
        ax3.plot(time_points, traffic_data, color='#e67e22', linewidth=2)
        ax3.set_title('Traffic Over Time (24h)', color='white')
        ax3.set_xlabel('Hour', color='white')
        ax3.set_ylabel('Packets/sec', color='white')
        ax3.tick_params(colors='white')
        
        # Error statistics
        error_types = ['CRC', 'Collision', 'Late Collision', 'Runts']
        error_counts = [5, 2, 1, 3]
        
        ax4.barh(error_types, error_counts, color='#e74c3c')
        ax4.set_title('Error Statistics', color='white')
        ax4.tick_params(colors='white')
        
        # Style all subplots
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_facecolor('#34495e')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')
        
        # Create canvas
        canvas = FigureCanvasTkAgg(fig, self.main_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def change_view(self, event=None):
        """Change visualization view"""
        view = self.view_var.get()
        if view == "Grid":
            self.create_grid_view()
        elif view == "List":
            self.create_list_view()
        elif view == "Statistics":
            self.create_statistics_view()
    
    def update_port_status(self, port_num, status, details=None):
        """Update individual port status with realistic switch colors"""
        if self.view_var.get() == "Grid" and port_num <= len(self.port_widgets):
            widget = self.port_widgets[port_num - 1]
            
            # Realistic switch port colors
            if status.lower() in ['up', 'connected']:
                color = '#00ff00'  # Bright green for UP ports
                text_color = 'black'
                status_text = 'UP'
            elif status.lower() in ['down', 'notconnected', 'notconnect']:
                color = '#ff0000'  # Red for DOWN ports  
                text_color = 'white'
                status_text = 'DOWN'
            elif status.lower() in ['disabled', 'administratively down']:
                color = '#808080'  # Gray for disabled ports
                text_color = 'white'
                status_text = 'DIS'
            else:
                color = '#ff8c00'  # Orange/amber for unknown status
                text_color = 'black'
                status_text = '---'
            
            # Update port visual appearance
            widget['frame'].config(bg=color)
            widget['status'].config(bg=color, fg=text_color, text=status_text)
            
            # Store port data
            self.port_data[port_num] = {
                'status': status,
                'details': details or {},
                'last_update': datetime.now()
            }
    
    def show_port_details(self, port_num):
        """Show detailed port information with control options"""
        details_window = tk.Toplevel(self)
        details_window.title(f"Port Gi1/0/{port_num} Control & Details")
        details_window.geometry("600x500")
        details_window.configure(bg='#2c3e50')
        details_window.resizable(True, True)
        
        # Port header
        header_frame = tk.Frame(details_window, bg='#34495e')
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(header_frame, text=f"🔌 Port Gi1/0/{port_num} Control Panel", 
               bg='#34495e', fg='white', font=('Arial', 14, 'bold')).pack()
        
        # Quick Control Buttons
        control_frame = tk.Frame(details_window, bg='#2c3e50')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(control_frame, text="Quick Actions:", bg='#2c3e50', fg='white', 
               font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        button_frame = tk.Frame(control_frame, bg='#2c3e50')
        button_frame.pack(fill=tk.X, pady=5)
        
        # Control buttons
        enable_btn = tk.Button(button_frame, text="🟢 Enable Port", 
                             command=lambda: self.control_port(port_num, 'enable'),
                             bg='#27ae60', fg='white', font=('Arial', 9, 'bold'),
                             width=12, relief='flat', cursor='hand2')
        enable_btn.pack(side=tk.LEFT, padx=5)
        
        disable_btn = tk.Button(button_frame, text="🔴 Disable Port", 
                              command=lambda: self.control_port(port_num, 'disable'),
                              bg='#e74c3c', fg='white', font=('Arial', 9, 'bold'),
                              width=12, relief='flat', cursor='hand2')
        disable_btn.pack(side=tk.LEFT, padx=5)
        
        reset_btn = tk.Button(button_frame, text="🔄 Reset Port", 
                            command=lambda: self.control_port(port_num, 'reset'),
                            bg='#f39c12', fg='white', font=('Arial', 9, 'bold'),
                            width=12, relief='flat', cursor='hand2')
        reset_btn.pack(side=tk.LEFT, padx=5)
        
        # VLAN Configuration
        vlan_frame = tk.Frame(details_window, bg='#2c3e50')
        vlan_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(vlan_frame, text="VLAN Configuration:", bg='#2c3e50', fg='white', 
               font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        vlan_control_frame = tk.Frame(vlan_frame, bg='#2c3e50')
        vlan_control_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(vlan_control_frame, text="VLAN ID:", bg='#2c3e50', fg='white').pack(side=tk.LEFT)
        
        self.vlan_entry = tk.Entry(vlan_control_frame, width=10, font=('Arial', 10))
        self.vlan_entry.pack(side=tk.LEFT, padx=5)
        # Set current VLAN if available
        current_vlan = port_details.get('vlan', '1')
        self.vlan_entry.insert(0, current_vlan)
        
        vlan_set_btn = tk.Button(vlan_control_frame, text="Set VLAN", 
                               command=lambda: self.set_port_vlan(port_num),
                               bg='#3498db', fg='white', font=('Arial', 9, 'bold'),
                               relief='flat', cursor='hand2')
        vlan_set_btn.pack(side=tk.LEFT, padx=5)
        
        # Description Configuration
        desc_frame = tk.Frame(details_window, bg='#2c3e50')
        desc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(desc_frame, text="Port Description:", bg='#2c3e50', fg='white', 
               font=('Arial', 11, 'bold')).pack(anchor=tk.W)
        
        desc_control_frame = tk.Frame(desc_frame, bg='#2c3e50')
        desc_control_frame.pack(fill=tk.X, pady=5)
        
        self.desc_entry = tk.Entry(desc_control_frame, width=30, font=('Arial', 10))
        self.desc_entry.pack(side=tk.LEFT, padx=5)
        
        desc_set_btn = tk.Button(desc_control_frame, text="Set Description", 
                               command=lambda: self.set_port_description(port_num),
                               bg='#9b59b6', fg='white', font=('Arial', 9, 'bold'),
                               relief='flat', cursor='hand2')
        desc_set_btn.pack(side=tk.LEFT, padx=5)
        
        # Details notebook
        notebook = ttk.Notebook(details_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Status tab
        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="📊 Status")
        
        # Configuration tab  
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="⚙️ Configuration")
        
        # Statistics tab
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="📈 Statistics")
        
        # Sample data display
        port_info = self.port_data.get(port_num, {})
        status_text = scrolledtext.ScrolledText(status_frame, height=12, width=70,
                                               bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        status_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Get actual port data if available
        port_details = port_info.get('details', {})
        current_vlan = port_details.get('vlan', '1')
        current_status = port_details.get('status', 'Unknown')
        current_speed = port_details.get('speed', 'Unknown')
        current_duplex = port_details.get('duplex', 'Unknown')
        
        sample_status = f"""
🔌 Port: Gi1/0/{port_num}
Status: {current_status}
Administrative Status: up
Operational Status: {current_status}
Speed: {current_speed}
Duplex: {current_duplex}
VLAN: {current_vlan}
Type: 10/100/1000BaseTX
MAC Address: 00:1e:14:a4:33:0{port_num:02d}
Last Input: 00:00:01
Last Output: 00:00:00
Input Packets: 15,234,567
Output Packets: 12,345,678
Input Errors: 0
Output Errors: 0

📈 Interface Counters:
- Bytes Input: 1,234,567,890
- Bytes Output: 987,654,321
- Packets Input: 15,234,567
- Packets Output: 12,345,678
- Input Rate: 1000 bits/sec
- Output Rate: 800 bits/sec

🔧 Configuration:
- Port Mode: Access
- Access VLAN: {current_vlan}
- Voice VLAN: None
- Port Security: Disabled
- Storm Control: Disabled

📊 Raw Interface Data:
{port_details.get('raw_line', 'No raw data available')}
        """
        
        status_text.insert(tk.END, sample_status)
        status_text.config(state=tk.DISABLED)
        
        # Configuration tab content
        config_text = scrolledtext.ScrolledText(config_frame, height=12, width=70,
                                               bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        sample_config = f"""
interface GigabitEthernet1/0/{port_num}
 description User Port {port_num}
 switchport mode access
 switchport access vlan 1
 spanning-tree portfast
 spanning-tree bpduguard enable
!
        """
        
        config_text.insert(tk.END, sample_config)
        config_text.config(state=tk.DISABLED)
        
        # Statistics tab content
        stats_text = scrolledtext.ScrolledText(stats_frame, height=12, width=70,
                                              bg='#1e1e1e', fg='#00ff00', font=('Consolas', 9))
        stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        sample_stats = f"""
📊 Interface Statistics for Gi1/0/{port_num}:

Input Statistics:
  Total Packets: 15,234,567
  Total Bytes: 1,234,567,890
  Unicast: 14,000,000
  Multicast: 1,200,000
  Broadcast: 34,567
  Input Errors: 0
  CRC Errors: 0
  Frame Errors: 0
  Overruns: 0
  Ignored: 0

Output Statistics:
  Total Packets: 12,345,678
  Total Bytes: 987,654,321
  Unicast: 11,000,000
  Multicast: 1,300,000
  Broadcast: 45,678
  Output Errors: 0
  Collisions: 0
  Interface Resets: 0
  Late Collisions: 0
  Lost Carrier: 0
  No Carrier: 0

📈 Rate Information:
  Input Rate: 1000 bits/sec, 1 packets/sec
  Output Rate: 800 bits/sec, 1 packets/sec
  5 minute input rate: 950 bits/sec, 1 packets/sec
  5 minute output rate: 750 bits/sec, 1 packets/sec
        """
        
        stats_text.insert(tk.END, sample_stats)
        stats_text.config(state=tk.DISABLED)
        
        # Store references for control functions
        self.current_port_window = details_window
        self.current_port_num = port_num
    
    def show_port_tooltip(self, event, port_num):
        """Show tooltip with port information"""
        # Cancel any pending tooltip
        if hasattr(self, 'tooltip_job'):
            self.after_cancel(self.tooltip_job)
        
        # Hide any existing tooltip first
        self.hide_port_tooltip()
        
        def create_tooltip():
            try:
                # Double check that we still need to show tooltip
                if not hasattr(self, 'tooltip_should_show') or not self.tooltip_should_show:
                    return
                
                # Create tooltip window
                self.tooltip = tk.Toplevel(self)
                self.tooltip.wm_overrideredirect(True)
                self.tooltip.configure(bg='#1a1a1a', relief='solid', bd=2)
                
                # Make tooltip stay on top but not grab focus
                self.tooltip.attributes('-topmost', True)
                
                # Position tooltip near mouse but adjust if near screen edge
                try:
                    x = event.widget.winfo_rootx() + 25
                    y = event.widget.winfo_rooty() + 25
                    
                    # Get screen dimensions
                    screen_width = self.tooltip.winfo_screenwidth()
                    screen_height = self.tooltip.winfo_screenheight()
                    
                    # Adjust position if tooltip would go off screen
                    if x + 200 > screen_width:
                        x = event.widget.winfo_rootx() - 200
                    if y + 150 > screen_height:
                        y = event.widget.winfo_rooty() - 150
                    
                    self.tooltip.geometry(f"+{x}+{y}")
                except:
                    # Fallback position
                    self.tooltip.geometry(f"+{event.x_root + 20}+{event.y_root + 20}")
                
                # Get port data
                port_data = self.port_data.get(port_num, {})
                port_details = port_data.get('details', {})
                
                # Create tooltip content with better formatting
                status = port_details.get('status', 'Unknown')
                status_icon = "🟢" if status.lower() in ['up', 'connected'] else "🔴" if status.lower() in ['down', 'notconnect'] else "🟡"
                
                tooltip_text = f"""{status_icon} Port Gi1/0/{port_num}
📊 Status: {status}
🏷️  VLAN: {port_details.get('vlan', 'N/A')}
⚡ Speed: {port_details.get('speed', 'N/A')}
🔗 Duplex: {port_details.get('duplex', 'N/A')}

💡 Click for detailed controls"""
                
                # Create main label with better styling
                label = tk.Label(self.tooltip, text=tooltip_text,
                               bg='#1a1a1a', fg='white', font=('Arial', 9),
                               justify=tk.LEFT, padx=12, pady=8)
                label.pack()
                
                # Add subtle border effect
                self.tooltip.configure(highlightbackground='#3498db', highlightthickness=1)
                
            except Exception as e:
                print(f"Tooltip error: {e}")
                self.hide_port_tooltip()
        
        # Set flag to show tooltip and schedule creation with delay
        self.tooltip_should_show = True
        self.tooltip_job = self.after(500, create_tooltip)  # 500ms delay to avoid flashing
    
    def hide_port_tooltip(self):
        """Hide port tooltip immediately"""
        try:
            # Cancel any pending tooltip
            if hasattr(self, 'tooltip_job'):
                self.after_cancel(self.tooltip_job)
                delattr(self, 'tooltip_job')
            
            # Set flag to not show tooltip
            self.tooltip_should_show = False
            
            # Destroy existing tooltip
            if hasattr(self, 'tooltip') and self.tooltip:
                try:
                    self.tooltip.destroy()
                except:
                    pass
                self.tooltip = None
        except Exception as e:
            print(f"Hide tooltip error: {e}")
        
        # Ensure cleanup
        if hasattr(self, 'tooltip'):
            self.tooltip = None
    
    def on_port_motion(self, event, port_num):
        """Handle mouse motion over port (helps with tooltip stability)"""
        try:
            # If mouse is moving within the same port, no need to recreate tooltip
            if hasattr(self, 'current_tooltip_port') and self.current_tooltip_port == port_num:
                return
            
            # Store current port for motion tracking
            self.current_tooltip_port = port_num
            
        except Exception as e:
            print(f"Port motion error: {e}")
    
    def control_port(self, port_num, action):
        """Control port status"""
        # This will be called by main app through callback
        if hasattr(self, 'port_control_callback') and self.port_control_callback:
            self.port_control_callback(port_num, action)
    
    def set_port_vlan(self, port_num):
        """Set port VLAN"""
        vlan_id = self.vlan_entry.get().strip()
        if vlan_id and hasattr(self, 'port_vlan_callback') and self.port_vlan_callback:
            self.port_vlan_callback(port_num, vlan_id)
    
    def set_port_description(self, port_num):
        """Set port description"""
        description = self.desc_entry.get().strip()
        if description and hasattr(self, 'port_desc_callback') and self.port_desc_callback:
            self.port_desc_callback(port_num, description)
    
    def create_legend(self):
        """Create status legend"""
        legend_frame = tk.Frame(self, bg='#2c3e50')
        legend_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(legend_frame, text="Legend:", bg='#2c3e50', fg='white', 
               font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10)
        
        legends = [
            ("🟢 Connected", '#27ae60'),
            ("🔴 Disconnected", '#e74c3c'),
            ("🟡 Other", '#f39c12'),
            ("⚫ Disabled", '#95a5a6')
        ]
        
        for text, color in legends:
            tk.Label(legend_frame, text=text, bg='#2c3e50', fg=color, 
                   font=('Arial', 9)).pack(side=tk.LEFT, padx=10)

class CommandTerminal(ModernFrame):
    """Advanced command terminal with history and auto-completion"""
    def __init__(self, parent, command_callback=None):
        super().__init__(parent, bg='#1e1e1e')
        self.command_callback = command_callback
        self.command_history = []
        self.history_index = -1
        self.setup_ui()
    
    def setup_ui(self):
        # Terminal header
        header_frame = tk.Frame(self, bg='#333333', height=30)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="💻 Command Terminal", 
               bg='#333333', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=10, pady=5)
        
        # Clear button
        clear_btn = tk.Button(header_frame, text="Clear", command=self.clear_terminal,
                            bg='#e74c3c', fg='white', font=('Arial', 8), 
                            relief='flat', cursor='hand2')
        clear_btn.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Terminal output
        self.output_text = scrolledtext.ScrolledText(
            self, bg='#1e1e1e', fg='#00ff00', font=('Consolas', 10),
            insertbackground='#00ff00', selectbackground='#333333'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Command input frame
        input_frame = tk.Frame(self, bg='#1e1e1e')
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(input_frame, text="cisco>", bg='#1e1e1e', fg='#00ff00', 
               font=('Consolas', 10, 'bold')).pack(side=tk.LEFT)
        
        self.command_entry = tk.Entry(input_frame, bg='#2c2c2c', fg='#00ff00', 
                                    font=('Consolas', 10), relief='flat',
                                    insertbackground='#00ff00')
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.command_entry.bind("<Return>", self.execute_command)
        self.command_entry.bind("<Up>", self.previous_command)
        self.command_entry.bind("<Down>", self.next_command)
        
        send_btn = tk.Button(input_frame, text="Send", command=self.execute_command,
                           bg='#27ae60', fg='white', font=('Arial', 9), 
                           relief='flat', cursor='hand2')
        send_btn.pack(side=tk.RIGHT, padx=5)
        
        self.add_output("Terminal ready. Type 'help' for available commands.\n")
    
    def execute_command(self, event=None):
        """Execute command"""
        command = self.command_entry.get().strip()
        if not command:
            return
        
        # Add to history
        if command not in self.command_history:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Display command
        self.add_output(f"cisco> {command}\n", color='#00ffff')
        
        # Clear input
        self.command_entry.delete(0, tk.END)
        
        # Execute command
        if self.command_callback:
            try:
                result = self.command_callback(command)
                self.add_output(f"{result}\n")
            except Exception as e:
                self.add_output(f"Error: {str(e)}\n", color='#ff6b6b')
        else:
            self.add_output("No connection established.\n", color='#ff6b6b')
    
    def add_output(self, text, color='#00ff00'):
        """Add text to terminal output"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        
        # Apply color to the last inserted text
        if color != '#00ff00':
            start_pos = f"{self.output_text.index(tk.END)}-{len(text)}c"
            self.output_text.tag_add("colored", start_pos, tk.END)
            self.output_text.tag_config("colored", foreground=color)
        
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(tk.END)
    
    def clear_terminal(self):
        """Clear terminal output"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.add_output("Terminal cleared.\n")
    
    def previous_command(self, event):
        """Navigate to previous command in history"""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
    
    def next_command(self, event):
        """Navigate to next command in history"""
        if self.command_history and self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, tk.END)

class DeviceInfoPanel(ModernFrame):
    """Comprehensive device information display panel"""
    def __init__(self, parent):
        super().__init__(parent, bg_color='#34495e')
        self.setup_ui()
    
    def setup_ui(self):
        # Create notebook for different info categories
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Basic Info Tab
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="📊 Basic Info")
        
        self.basic_text = scrolledtext.ScrolledText(
            self.basic_frame, height=10, bg='#2c3e50', fg='white', font=('Consolas', 9),
            relief='flat', bd=0
        )
        self.basic_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Environment Tab (Temperature, Power, Fans)
        self.env_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.env_frame, text="🌡️ Environment")
        
        self.env_text = scrolledtext.ScrolledText(
            self.env_frame, height=10, bg='#2c3e50', fg='white', font=('Consolas', 9),
            relief='flat', bd=0
        )
        self.env_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # VLAN Info Tab
        self.vlan_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.vlan_frame, text="🏷️ VLANs")
        
        self.vlan_text = scrolledtext.ScrolledText(
            self.vlan_frame, height=10, bg='#2c3e50', fg='white', font=('Consolas', 9),
            relief='flat', bd=0
        )
        self.vlan_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # CPU/Memory Tab
        self.perf_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.perf_frame, text="⚡ Performance")
        
        self.perf_text = scrolledtext.ScrolledText(
            self.perf_frame, height=10, bg='#2c3e50', fg='white', font=('Consolas', 9),
            relief='flat', bd=0
        )
        self.perf_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Default messages
        self.update_info("No device connected")
    
    def update_info(self, device_info):
        """Update comprehensive device information display"""
        if isinstance(device_info, dict) and 'device_info' in device_info:
            # This is comprehensive status data
            self.update_comprehensive_info(device_info)
        elif isinstance(device_info, dict):
            # This is basic device info
            self.update_basic_info(device_info)
        else:
            # String message
            self.clear_all_tabs()
            self.basic_text.config(state=tk.NORMAL)
            self.basic_text.insert(tk.END, str(device_info))
            self.basic_text.config(state=tk.DISABLED)
    
    def update_basic_info(self, device_info):
        """Update basic device information"""
        self.basic_text.config(state=tk.NORMAL)
        self.basic_text.delete(1.0, tk.END)
        
            info_text = "🖥️  DEVICE INFORMATION\n"
        info_text += "=" * 50 + "\n\n"
        
            for key, value in device_info.items():
            info_text += f"{key.upper():<20}: {value}\n"
        
        self.basic_text.insert(tk.END, info_text)
        self.basic_text.config(state=tk.DISABLED)
    
    def update_comprehensive_info(self, status_data):
        """Update comprehensive device status"""
        # Update Basic Info
        if status_data.get('device_info'):
            self.update_basic_info(status_data['device_info'])
        
        # Update Environment Info
        self.env_text.config(state=tk.NORMAL)
        self.env_text.delete(1.0, tk.END)
        
        env_text = "🌡️  ENVIRONMENT STATUS\n"
        env_text += "=" * 50 + "\n\n"
        
        # Temperature
        if status_data.get('temperature'):
            env_text += "🌡️ TEMPERATURE SENSORS:\n"
            env_text += "-" * 30 + "\n"
            for sensor, data in status_data['temperature'].items():
                status_icon = "✅" if data['status'] == 'OK' else "❌"
                env_text += f"{status_icon} {sensor:<15}: {data['temperature']}°C ({data['status']})\n"
            env_text += "\n"
        
        # Power Supply
        if status_data.get('power'):
            env_text += "🔌 POWER SUPPLIES:\n"
            env_text += "-" * 30 + "\n"
            for ps, data in status_data['power'].items():
                status_icon = "✅" if data['status'] == 'OK' else "❌"
                env_text += f"{status_icon} {ps:<15}: {data['status']}\n"
            env_text += "\n"
        
        # Fans
        if status_data.get('fans'):
            env_text += "💨 FANS:\n"
            env_text += "-" * 30 + "\n"
            for fan, data in status_data['fans'].items():
                status_icon = "✅" if data['status'] == 'OK' else "❌"
                env_text += f"{status_icon} {fan:<15}: {data['status']}\n"
        
        self.env_text.insert(tk.END, env_text)
        self.env_text.config(state=tk.DISABLED)
        
        # Update VLAN Info
        self.vlan_text.config(state=tk.NORMAL)
        self.vlan_text.delete(1.0, tk.END)
        
        vlan_text = "🏷️  VLAN INFORMATION\n"
        vlan_text += "=" * 50 + "\n\n"
        
        if status_data.get('vlans'):
            for vlan_id, vlan_data in status_data['vlans'].items():
                vlan_text += f"VLAN {vlan_id:<5}: {vlan_data['name']:<20} ({vlan_data['status']})\n"
                if vlan_data.get('ports'):
                    vlan_text += f"   Ports: {', '.join(vlan_data['ports'][:10])}"
                    if len(vlan_data['ports']) > 10:
                        vlan_text += f" ... (+{len(vlan_data['ports'])-10} more)"
                    vlan_text += "\n"
                vlan_text += "\n"
        
        self.vlan_text.insert(tk.END, vlan_text)
        self.vlan_text.config(state=tk.DISABLED)
        
        # Update Performance Info
        self.perf_text.config(state=tk.NORMAL)
        self.perf_text.delete(1.0, tk.END)
        
        perf_text = "⚡  PERFORMANCE METRICS\n"
        perf_text += "=" * 50 + "\n\n"
        
        if status_data.get('cpu_memory'):
            cpu_mem = status_data['cpu_memory']
            perf_text += "🧠 CPU & MEMORY:\n"
            perf_text += "-" * 30 + "\n"
            perf_text += f"CPU Usage      : {cpu_mem.get('cpu_usage', 'N/A')}\n"
            perf_text += f"Memory Usage   : {cpu_mem.get('memory_usage', 'N/A')}\n"
            perf_text += f"Total Memory   : {cpu_mem.get('total_memory', 'N/A'):,} bytes\n"
            perf_text += f"Used Memory    : {cpu_mem.get('used_memory', 'N/A'):,} bytes\n"
        
        self.perf_text.insert(tk.END, perf_text)
        self.perf_text.config(state=tk.DISABLED)
    
    def clear_all_tabs(self):
        """Clear all tab contents"""
        for text_widget in [self.basic_text, self.env_text, self.vlan_text, self.perf_text]:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            text_widget.config(state=tk.DISABLED) 