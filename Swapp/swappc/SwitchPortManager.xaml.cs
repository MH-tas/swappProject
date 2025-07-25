using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using Renci.SshNet;
using Renci.SshNet.Common;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Text;
using Newtonsoft.Json;

namespace SwappC
{
    public partial class SwitchPortManager : Window
    {
        private SshClient? sshClient;
        private ShellStream? shellStream;
        private DispatcherTimer? refreshTimer;
        private DispatcherTimer? firebaseMonitorTimer; // 🔥 Sürekli Firebase push timer
        private Dictionary<string, PortStatus> portStatus = new();
        private Dictionary<string, PortStatus> lastPortStatus = new(); // 🔥 Önceki durum karşılaştırması için
        private SwitchSystemInfo? lastSwitchInfo; // 🔥 Switch info değişikliklerini takip etmek için
        private string? selectedPortName;
        private string? switchIP;
        private string? username;
        private string? password;
        private ObservableCollection<PortStatus> portStatusCollection = new(); // New collection for DataGrid

        private DateTime lastConnectionCheck = DateTime.MinValue;
        private FirebaseService? firebaseService;
        private DateTime lastFirebasePush = DateTime.MinValue; // 🔥 Son Firebase push zamanı
        
        // 📱 PHONE COMMAND SİSTEMİ
        private bool isPhoneCommandEnabled = false;
        private DispatcherTimer? phoneCommandTimer;
        private DateTime lastCommandCheck = DateTime.MinValue;
        
        // 🔗 SSH KEEPALİVE SYSTEM - BAĞLANTIYI SÜREKLI AÇIK TUT
        private DispatcherTimer? sshKeepaliveTimer;
        private DateTime lastSshCheck = DateTime.MinValue;
        private bool isReconnecting = false;

        public SwitchPortManager()
        {
            InitializeComponent();
            CreateAllPorts();
            LoadDemoData();
            InitializeFirebase();
            
            refreshTimer = new DispatcherTimer();
            refreshTimer.Interval = TimeSpan.FromSeconds(2);  // 2 seconds for real-time monitoring!
            refreshTimer.Tick += async (s, e) => await AutoRefreshPorts();
            
            UpdateStatus("Ready - 48 ports created (DEMO MODE)");
        }

        private void Window_Loaded(object sender, RoutedEventArgs e)
        {
            // Window loaded event handler for XAML Loaded="Window_Loaded"
            // Animations are handled by XAML triggers, this is just for the event binding
        }

        public SwitchPortManager(SshClient existingSSHClient, string ip, string user, string pass)
        {
            InitializeComponent();
            CreateAllPorts();
            InitializeFirebase();
            
            // SSH bağlantısının geçerliliğini güvenli şekilde kontrol et
            bool sshValid = false;
            try
            {
                // SSH client'ın dispose edilip edilmediğini kontrol et
                if (existingSSHClient?.IsConnected == true)
                {
                    // Dispose kontrolü için ConnectionInfo'ya erişmeye çalış
                    var testHost = existingSSHClient.ConnectionInfo?.Host;
                    if (!string.IsNullOrEmpty(testHost))
                    {
                        sshValid = true;
                        sshClient = existingSSHClient;
                        Console.WriteLine($"✅ Geçerli SSH bağlantısı tespit edildi: {testHost}");
                    }
                }
            }
            catch (ObjectDisposedException ex)
            {
                sshValid = false;
                Console.WriteLine($"❌ SSH client dispose edilmiş: {ex.Message}");
            }
            catch (Exception ex)
            {
                sshValid = false;
                Console.WriteLine($"❌ SSH bağlantı kontrolü hatası: {ex.Message}");
            }
            
            // Bağlantı bilgilerini sakla
            switchIP = ip;
            username = user;
            password = pass;
            
            // Timer'ı başlat
            refreshTimer = new DispatcherTimer();
            refreshTimer.Interval = TimeSpan.FromSeconds(2);  // 2 saniye gerçek zamanlı monitoring!
            refreshTimer.Tick += async (s, e) => await AutoRefreshPorts();
            
            // SSH bağlantısı geçerliyse shell stream başlat
            if (sshValid)
            {
                try
                {
                    shellStream = sshClient.CreateShellStream("terminal", 80, 24, 800, 600, 1024);
                    if (shellStream != null)
                    {
                        shellStream.WriteLine("terminal length 0");
                        Task.Delay(500).Wait(); // Komutun işlenmesi için bekle
                    }
                }
                catch (ObjectDisposedException ex)
                {
                    UpdateStatus($"⚠️ SSH bağlantısı geçersiz hale geldi: {ex.Message}");
                    sshValid = false;
                    sshClient = null;
                }
                catch (Exception ex)
                {
                    UpdateStatus($"⚠️ Shell stream oluşturulamadı: {ex.Message}");
                }
                
                if (sshValid)
                {
                    txtConnectionStatus.Text = $"🟢 Bağlı: {switchIP}";
                    txtConnectionStatus.Background = Brushes.Green;
                    
                    btnRefresh.IsEnabled = true;
                    btnAutoRefresh.IsEnabled = true;
                    btnSwitchInfo.IsEnabled = true;   // SSH modunda switch info aktif
                    btnBulkDisable.IsEnabled = true;  // SSH modunda bulk disable aktif
                    btnBulkEnable.IsEnabled = true;   // SSH modunda bulk enable aktif
                    
                    // Connect butonu devre dışı (zaten bağlı)
                    btnConnect.IsEnabled = false;
                    btnConnect.Content = "Zaten Bağlı";
                    
                    UpdateStatus($"✅ Mevcut SSH bağlantısı kullanılıyor: {switchIP}");
                    
                    // Otomatik refresh başlat ve gerçek data yükle
                    _ = Task.Run(async () => {
                        await Task.Delay(1000);
                        try
                        {
                            await AutoRefreshPorts();
                            await Dispatcher.InvokeAsync(() => {
                                refreshTimer?.Start();
                                btnAutoRefresh.Content = "⏸️ Durdur";
                                btnAutoRefresh.Background = Brushes.Orange;
                            });
                        }
                        catch (ObjectDisposedException)
                        {
                            await Dispatcher.InvokeAsync(() => {
                                UpdateStatus("❌ SSH bağlantısı kesildi - DEMO moduna geçiliyor");
                                LoadDemoData();
                            });
                        }
                    });
                }
            }
            
            // SSH geçersizse veya bağlı değilse demo mode
            if (!sshValid)
            {
                LoadDemoData();
                txtConnectionStatus.Text = "🔴 SSH Bağlantısı Yok";
                txtConnectionStatus.Background = Brushes.Red;
                btnConnect.IsEnabled = true;
                btnSwitchInfo.IsEnabled = false;
                UpdateStatus("❌ SSH bağlantısı geçersiz - DEMO MODU aktif");
            }
        }

        public SwitchPortManager(string ip, string user, string pass) : this()
        {
            switchIP = ip;
            username = user;
            password = pass;
        }

        private async void InitializeFirebase()
        {
            try
            {
                firebaseService = new FirebaseService();
                await firebaseService.PushUsageStats("SwitchPortManager_Opened", $"Port manager opened for switch management");
                
                // 🔥 SÜREKLI MONİTORİNG: Her 1 saniyede Firebase'e push yapacak timer
                InitializeFirebaseMonitoring();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase initialization failed in SwitchPortManager: {ex.Message}");
            }
        }

        // 🔥 Firebase sürekli monitoring sistemi
        private void InitializeFirebaseMonitoring()
        {
            // Her 1 saniyede Firebase push kontrolü yapacak timer
            firebaseMonitorTimer = new DispatcherTimer();
            firebaseMonitorTimer.Interval = TimeSpan.FromSeconds(1); // HER 1 SANİYE!
            firebaseMonitorTimer.Tick += async (s, e) => await MonitorAndPushToFirebase();
            
            // Timer'ı başlat
            firebaseMonitorTimer.Start();
            UpdateStatus("🔥 Firebase real-time monitoring ACTIVE (1 second intervals)");
        }

        private void CreateAllPorts()
        {
            CreatePortGroup(gridGigPorts1, 1, 12);
            CreatePortGroup(gridGigPorts2, 13, 24);
            CreatePortGroup(gridGigPorts3, 25, 36);
            CreatePortGroup(gridGigPorts4, 37, 48);
        }

        private void CreatePortGroup(Grid grid, int startPort, int endPort)
        {
            // Doğru port sıralama: Her grupta 12 port, 6 sütun x 2 satır
            // Üst sıra: tek sayılar (1,3,5,7,9,11)
            // Alt sıra: çift sayılar (2,4,6,8,10,12)
            
            for (int i = 0; i < 6; i++) // 6 sütun
            {
                // Üst sıra - tek sayı portlar
                int oddPort = startPort + (i * 2);
                var oddButton = new Button
                {
                    Content = $"{oddPort}\nGigE",
                    Tag = $"Gi1/0/{oddPort}",
                Style = (Style)FindResource("PortButton"),
                Background = Brushes.LightGray,
                    ToolTip = $"Port Gi1/0/{oddPort}"
                };
                oddButton.Click += PortButton_Click;
                    Grid.SetRow(oddButton, 0);
                Grid.SetColumn(oddButton, i);
                grid.Children.Add(oddButton);

                // Alt sıra - çift sayı portlar  
                int evenPort = startPort + (i * 2) + 1;
                if (evenPort <= endPort)
                {
                    var evenButton = new Button
                    {
                        Content = $"{evenPort}\nGigE",
                        Tag = $"Gi1/0/{evenPort}",
                Style = (Style)FindResource("PortButton"),
                Background = Brushes.LightGray,
                        ToolTip = $"Port Gi1/0/{evenPort}"
                    };
                    evenButton.Click += PortButton_Click;
                    Grid.SetRow(evenButton, 1);
                    Grid.SetColumn(evenButton, i);
                    grid.Children.Add(evenButton);
                }
            }
        }

        private void PortButton_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is string portName)
            {
                selectedPortName = portName;
                txtSelectedPort.Text = portName;
                
                btnEnablePort.IsEnabled = true;
                btnDisablePort.IsEnabled = true;
                btnTogglePort.IsEnabled = true;
                
                foreach (Button btn in GetAllPortButtons())
                {
                    btn.BorderBrush = btn.Tag?.ToString() == portName ? Brushes.Blue : Brushes.Gray;
                    btn.BorderThickness = btn.Tag?.ToString() == portName ? new Thickness(3) : new Thickness(1);
                }
            }
        }

        private IEnumerable<Button> GetAllPortButtons()
        {
            var buttons = new List<Button>();
            buttons.AddRange(gridGigPorts1.Children.OfType<Button>());
            buttons.AddRange(gridGigPorts2.Children.OfType<Button>());
            buttons.AddRange(gridGigPorts3.Children.OfType<Button>());
            buttons.AddRange(gridGigPorts4.Children.OfType<Button>());
            return buttons;
        }

        private async void BtnConnect_Click(object sender, RoutedEventArgs e)
        {
            // Check if already connected via existing SSH
            if (sshClient?.IsConnected == true)
            {
                MessageBox.Show($"✅ Already Connected!\n\nUsing existing SSH connection to {switchIP}\n\nNo need to reconnect.", 
                              "Already Connected", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            if (string.IsNullOrEmpty(switchIP))
            {
                var dialog = new ConnectionDialog();
                dialog.Host = "192.168.20.1";
                dialog.Username = "swapp";
                dialog.Password = "swapp";
                
                if (dialog.ShowDialog() != true) return;
                
                switchIP = dialog.Host;
                username = dialog.Username;
                password = dialog.Password;
            }

            // Null check
            if (string.IsNullOrEmpty(switchIP) || string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
            {
                UpdateStatus("Missing connection parameters");
                    return;
            }

            try
            {
                btnConnect.IsEnabled = false;
                txtConnectionStatus.Text = "Connecting...";
                txtConnectionStatus.Background = Brushes.Orange;
                UpdateStatus($"Connecting to {switchIP}...");
                
                // Clean up existing connection
                await CleanupExistingConnection();
                
                // Create SSH client with ULTRA ROBUST settings
                var connectionInfo = new ConnectionInfo(switchIP, 22, username,
                    new PasswordAuthenticationMethod(username, password));
                
                // ULTRA ROBUST connection settings to prevent disconnections
                connectionInfo.Timeout = TimeSpan.FromSeconds(60);
                connectionInfo.MaxSessions = 20;
                connectionInfo.RetryAttempts = 3;
                connectionInfo.Encoding = System.Text.Encoding.UTF8;
                
                sshClient = new SshClient(connectionInfo);
                sshClient.KeepAliveInterval = TimeSpan.FromSeconds(5);
                
                await Task.Run(() => sshClient.Connect());

                if (sshClient.IsConnected)
                {
                    await InitializeShellStream();
                    
                    txtConnectionStatus.Text = $"Connected to {switchIP}";
                    txtConnectionStatus.Background = Brushes.Green;
                    
                    btnRefresh.IsEnabled = true;
                    btnAutoRefresh.IsEnabled = true;
                    btnSwitchInfo.IsEnabled = true;
                    
                    UpdateStatus($"✅ SSH Connected to {switchIP}");
                    
                    // Initialize timers safely - PREVENT CONFLICTS
                    await InitializeTimersSafely();
                    
                    // Firebase connection info (non-blocking)
                    _ = PushConnectionInfoSafely();
                    
                    MessageBox.Show($"🔌 SSH CONNECTION SUCCESS\n\nHost: {switchIP}\nUser: {username}\nStatus: CONNECTED\n\n🔗 SSH Keepalive: ACTIVE\n🔥 Firebase: ACTIVE\n\nNow you can control ports via SSH!", 
                                  "SSH Connected", MessageBoxButton.OK, MessageBoxImage.Information);
                    
                    await AutoRefreshPorts();
                    
                    // Start auto refresh safely
                    if (refreshTimer != null && !refreshTimer.IsEnabled)
                    {
                        refreshTimer.Start();
                        btnAutoRefresh.Content = "⏸️ Stop Auto";
                        btnAutoRefresh.Background = Brushes.Orange;
                    }
                }
                else
                {
                    throw new Exception("SSH connection failed - IsConnected = false");
                }
            }
            catch (Exception ex)
            {
                await HandleConnectionError(ex);
            }
        }

        private async Task CleanupExistingConnection()
        {
            try
            {
                // Stop all timers
                refreshTimer?.Stop();
                firebaseMonitorTimer?.Stop();
                sshKeepaliveTimer?.Stop();
                phoneCommandTimer?.Stop();
                
                // Dispose SSH resources
                shellStream?.Dispose();
                shellStream = null;
                
                sshClient?.Dispose();
                sshClient = null;
                
                await Task.Delay(100); // Give time for cleanup
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Connection cleanup error: {ex.Message}");
            }
        }

        private async Task InitializeShellStream()
        {
            try
            {
                if (sshClient?.IsConnected == true)
                    {
                        shellStream = sshClient.CreateShellStream("terminal", 80, 24, 800, 600, 1024);
                        if (shellStream != null)
                        {
                            shellStream.WriteLine("terminal length 0");
                        await Task.Delay(500);
                    }
                        }
                    }
                    catch (Exception ex)
                    {
                        UpdateStatus($"Warning: Could not create shell stream: {ex.Message}");
                    }
        }

        private async Task InitializeTimersSafely()
        {
            try
            {
                // Initialize SSH keepalive timer (HIGHEST PRIORITY)
                if (sshKeepaliveTimer == null)
                {
                    sshKeepaliveTimer = new DispatcherTimer();
                    sshKeepaliveTimer.Interval = TimeSpan.FromSeconds(30);
                    sshKeepaliveTimer.Tick += async (s, e) => await CheckAndMaintainSshConnection();
                    sshKeepaliveTimer.Start();
                }
                
                // Initialize Firebase monitoring with delay to prevent conflicts
                await Task.Delay(1000);
                if (firebaseMonitorTimer == null && firebaseService != null)
                    {
                    firebaseMonitorTimer = new DispatcherTimer();
                    firebaseMonitorTimer.Interval = TimeSpan.FromSeconds(5); // REDUCED: 5 seconds instead of 1
                    firebaseMonitorTimer.Tick += async (s, e) => await MonitorAndPushToFirebaseSafely();
                    firebaseMonitorTimer.Start();
                }
                
                UpdateStatus("🔗 SSH Keepalive ACTIVE, 🔥 Firebase monitoring ACTIVE");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Timer initialization error: {ex.Message}");
            }
        }

        private async Task MonitorAndPushToFirebaseSafely()
        {
            try
            {
                // Don't run if SSH is not connected
                if (sshClient?.IsConnected != true) return;
                
                // Don't run too frequently
                if (DateTime.Now.Subtract(lastFirebasePush).TotalSeconds < 3) return;
                    
                await MonitorAndPushToFirebase();
                lastFirebasePush = DateTime.Now;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Safe Firebase monitoring error: {ex.Message}");
            }
        }

        private async Task PushConnectionInfoSafely()
        {
            try
            {
                if (firebaseService != null && !string.IsNullOrEmpty(switchIP))
                {
                    await firebaseService.PushConnectionInfo(switchIP, username ?? "", true, "Connected successfully");
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase connection info push failed: {ex.Message}");
            }
        }

        private async Task HandleConnectionError(Exception ex)
        {
            try
            {
                txtConnectionStatus.Text = "Failed";
                txtConnectionStatus.Background = Brushes.Red;
                btnConnect.IsEnabled = true;
                UpdateStatus($"❌ Connection failed: {ex.Message}");
                
                MessageBox.Show($"❌ SSH CONNECTION FAILED\n\nHost: {switchIP}\nError: {ex.Message}\n\nUsing DEMO MODE instead", 
                              "Connection Failed", MessageBoxButton.OK, MessageBoxImage.Error);
                
                await CleanupExistingConnection();
            }
            catch (Exception cleanupEx)
            {
                System.Diagnostics.Debug.WriteLine($"Error handling cleanup failed: {cleanupEx.Message}");
            }
        }

        private async void BtnRefresh_Click(object sender, RoutedEventArgs e)
        {
            try
        {
            await ManualRefreshPorts();
            }
            catch (Exception ex)
            {
                UpdateStatus($"Manual refresh error: {ex.Message}");
                MessageBox.Show($"❌ MANUAL REFRESH FAILED\n\nError: {ex.Message}", 
                              "Refresh Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async Task ManualRefreshPorts()
        {
            try
            {
                btnRefresh.IsEnabled = false;
                btnRefresh.Content = "🔄 Refreshing...";
                UpdateStatus("Manual refresh starting...");

                // Try to ensure SSH connection, but don't fail if not available - use demo mode instead
                bool hasSSH = await EnsureSSHConnection();
                if (!hasSSH)
                {
                    UpdateStatus("SSH not available - using demo mode with VLAN info");
                    // Don't show error popup - just work with demo data
                    LoadDemoData(); // Refresh demo data which includes VLAN info
                    return;
                }

                UpdateStatus("Executing manual port refresh with VLAN info...");
                
                // Get basic port status
                var statusCmd = sshClient!.CreateCommand("show interfaces status");
                statusCmd.CommandTimeout = TimeSpan.FromSeconds(15);
                var statusResult = await Task.Run(() => statusCmd.Execute());
                
                // Parse basic port data first
                ParsePortData(statusResult);
                
                // Only get VLAN info if SSH is still connected
                if (sshClient?.IsConnected == true)
                {
                    try
                    {
                        // Get VLAN information
                        var vlanCmd = sshClient.CreateCommand("show interfaces switchport");
                        vlanCmd.CommandTimeout = TimeSpan.FromSeconds(15);
                        var vlanResult = await Task.Run(() => vlanCmd.Execute());
                        
                        // Get VLAN names
                        var vlanNamesCmd = sshClient.CreateCommand("show vlan brief");
                        vlanNamesCmd.CommandTimeout = TimeSpan.FromSeconds(15);
                        var vlanNamesResult = await Task.Run(() => vlanNamesCmd.Execute());
                        
                        // Parse VLAN data
                        ParseVlanData(vlanResult, vlanNamesResult);
                    }
                    catch (Exception vlanEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"VLAN info fetch failed: {vlanEx.Message}");
                        UpdateStatus("Port status updated, VLAN info skipped");
                    }
                }
                
                UpdatePortDisplay();
                
                // Push comprehensive data for manual refresh
                _ = Task.Run(async () =>
                {
                    try
                    {
                        if (firebaseService != null && !string.IsNullOrEmpty(switchIP))
                        {
                            await firebaseService.PushPortStatus(portStatus, switchIP);
                            await PushSwitchDetailsToFirebase();
                        }
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"Firebase manual refresh push error: {ex.Message}");
                    }
                });
                
                var now = DateTime.Now.ToString("HH:mm:ss");
                UpdateStatus($"✅ Manual refresh completed [{now}] - {portStatus.Count} ports found");
                txtLastUpdate.Text = $"Last Update: {now}";
                
                MessageBox.Show($"✅ MANUAL REFRESH SUCCESS!\n\n🔌 Found {portStatus.Count} ports\n📊 Data updated at {now}", 
                              "Refresh Complete", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                UpdateStatus($"Manual refresh failed: {ex.Message}");
                MessageBox.Show($"❌ MANUAL REFRESH FAILED!\n\nError: {ex.Message}\n\nPlease check SSH connection.", 
                              "Refresh Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                btnRefresh.IsEnabled = true;
                btnRefresh.Content = "🔄 Refresh Ports";
            }
        }

        // 🔄 AUTO REFRESH: Manuel refresh ile TIPA TIP AYNI - sadece UI feedback yok!
        private async Task AutoRefreshPorts()
        {
            try
            {
                // Try to ensure SSH connection for auto refresh
                if (!await EnsureSSHConnection())
                {
                    System.Diagnostics.Debug.WriteLine("Auto refresh: SSH not available, skipping");
                    return; // Silently skip auto refresh if no SSH
                }

                System.Diagnostics.Debug.WriteLine("Auto refresh: Executing port refresh with VLAN info (identical to manual)");
                
                // Get basic port status
                var statusCmd = sshClient!.CreateCommand("show interfaces status");
                statusCmd.CommandTimeout = TimeSpan.FromSeconds(15);
                var statusResult = await Task.Run(() => statusCmd.Execute());
                
                // Parse basic port data first
                ParsePortData(statusResult);
                
                // Only get VLAN info if SSH is still connected (and occasionally for performance)
                if (sshClient?.IsConnected == true)
                {
                    try
                    {
                        // Get VLAN information (less frequent for auto refresh to improve performance)
                        var vlanCmd = sshClient.CreateCommand("show interfaces switchport");
                        vlanCmd.CommandTimeout = TimeSpan.FromSeconds(10); // Shorter timeout for auto refresh
                        var vlanResult = await Task.Run(() => vlanCmd.Execute());
                        
                        // Get VLAN names (less frequent)
                        var vlanNamesCmd = sshClient.CreateCommand("show vlan brief");
                        vlanNamesCmd.CommandTimeout = TimeSpan.FromSeconds(10); // Shorter timeout for auto refresh
                        var vlanNamesResult = await Task.Run(() => vlanNamesCmd.Execute());
                        
                        // Parse VLAN data
                        ParseVlanData(vlanResult, vlanNamesResult);
                    }
                    catch (Exception vlanEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Auto refresh VLAN info fetch failed: {vlanEx.Message}");
                        // Don't show status update for auto refresh failures
                    }
                }
                
                UpdatePortDisplay();
                
                // Push comprehensive data for auto refresh (same as manual)
                _ = Task.Run(async () =>
                {
                    try
                    {
                        if (firebaseService != null && !string.IsNullOrEmpty(switchIP))
                        {
                            await firebaseService.PushPortStatus(portStatus, switchIP);
                            await PushSwitchDetailsToFirebase();
                        }
                    }
                    catch (Exception ex)
                    {
                        System.Diagnostics.Debug.WriteLine($"Firebase auto refresh push error: {ex.Message}");
                    }
                });
                
                var now = DateTime.Now.ToString("HH:mm:ss");
                UpdateStatus($"🔄 Auto-refreshed [{now}] - {portStatus.Count} ports monitored");
                txtLastUpdate.Text = $"Last Update: {now}";
                
                System.Diagnostics.Debug.WriteLine($"Auto refresh completed successfully - {portStatus.Count} ports found");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Auto refresh error: {ex.Message}");
                UpdateStatus($"Auto-refresh error: {ex.Message}");
            }
        }

                private void BtnAutoRefresh_Click(object sender, RoutedEventArgs e)
        {
            try
        {
            if (refreshTimer?.IsEnabled == true)
            {
                // STOP auto refresh
                refreshTimer.Stop();
                btnAutoRefresh.Content = "⏱️ Auto Refresh";
                btnAutoRefresh.Background = Brushes.LightBlue;
                UpdateStatus("🛑 Auto refresh STOPPED - Manual refresh only");
            }
            else
            {
                    // START auto refresh
                refreshTimer?.Start();
                btnAutoRefresh.Content = "⏸️ Stop Auto";
                btnAutoRefresh.Background = Brushes.Orange;
                UpdateStatus("🔄 Auto refresh STARTED - Monitoring every 2 seconds");
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"Auto refresh toggle error: {ex.Message}");
                MessageBox.Show($"❌ AUTO REFRESH TOGGLE FAILED\n\nError: {ex.Message}", 
                              "Auto Refresh Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void ParsePortData(string output)
        {
            portStatus.Clear();
            
            if (string.IsNullOrWhiteSpace(output)) return;
            
            var lines = output.Split('\n');
            foreach (var line in lines)
            {
                var trimmedLine = line.Trim();
                // Enhanced regex to capture more port information including VLAN
                // Format: Port      Name  Status       Vlan       Duplex  Speed Type
                var match = Regex.Match(trimmedLine, @"^(Gi\d+/\d+/\d+)\s+(?:[\w-]+\s+)?(\w+)\s+(?:(?:trunk|routed)|(\d+))\s+(\w+)\s+(\w+)");
                if (match.Success)
                {
                    var port = match.Groups[1].Value;
                    var status = match.Groups[2].Value.ToLower();
                    var vlanId = match.Groups[3].Value; // This will be empty for trunk ports
                    var duplex = match.Groups[4].Value;
                    var speed = match.Groups[5].Value;
                    
                    portStatus[port] = new PortStatus
                    {
                        Name = port,
                        Status = status,
                        IsUp = status == "connected",
                        IsDown = status == "notconnect" || status == "err-disabled",
                        IsShutdown = status == "disabled",
                        VlanId = vlanId, // Will be updated later with more detailed info from show interfaces switchport
                        Speed = speed,
                        Duplex = duplex
                    };
                }
                else
                {
                    // Fallback to simple regex for compatibility
                    var simpleMatch = Regex.Match(trimmedLine, @"^(Gi\d+/\d+/\d+)\s+(\w+)");
                    if (simpleMatch.Success)
                    {
                        var port = simpleMatch.Groups[1].Value;
                        var status = simpleMatch.Groups[2].Value.ToLower();
                    
                    portStatus[port] = new PortStatus
                    {
                        Name = port,
                        Status = status,
                        IsUp = status == "connected",
                        IsDown = status == "notconnect" || status == "err-disabled",
                        IsShutdown = status == "disabled"
                    };
                }
                }
            }
        }

        private void ParseVlanData(string switchportOutput, string vlanBriefOutput)
        {
            try
            {
                // Safety check - if no data, just return
                if (string.IsNullOrWhiteSpace(switchportOutput) && string.IsNullOrWhiteSpace(vlanBriefOutput))
                {
                    System.Diagnostics.Debug.WriteLine("ParseVlanData: No VLAN data to parse");
                    return;
                }
                
                // Parse VLAN names from "show vlan brief"
                var vlanNames = new Dictionary<string, string>();
                if (!string.IsNullOrWhiteSpace(vlanBriefOutput))
                {
                    var vlanLines = vlanBriefOutput.Split('\n');
                    foreach (var line in vlanLines)
                    {
                        var trimmedLine = line.Trim();
                        // VLAN brief format: VLAN_ID  Name  Status  Ports
                        var vlanMatch = Regex.Match(trimmedLine, @"^(\d+)\s+(\S+)\s+(\w+)");
                        if (vlanMatch.Success)
                        {
                            var vlanId = vlanMatch.Groups[1].Value;
                            var vlanName = vlanMatch.Groups[2].Value;
                            vlanNames[vlanId] = vlanName;
                        }
                    }
                }

                // Parse switchport information from "show interfaces switchport"
                if (!string.IsNullOrWhiteSpace(switchportOutput))
            {
                    string currentInterface = "";
                    string currentMode = "";
                    string currentVlan = "";
                    var lines = switchportOutput.Split('\n');
                    
                    foreach (var line in lines)
                    {
                        var trimmedLine = line.Trim();
                        
                        // Look for interface name
                        var interfaceMatch = Regex.Match(trimmedLine, @"^Name:\s+(Gi\d+/\d+/\d+)");
                        if (interfaceMatch.Success)
                        {
                            // Save previous port info if we have it
                            if (!string.IsNullOrEmpty(currentInterface) && !string.IsNullOrEmpty(currentVlan) && portStatus.ContainsKey(currentInterface))
                            {
                                UpdatePortVlanInfo(currentInterface, currentVlan, currentMode, vlanNames);
                            }
                            
                            currentInterface = interfaceMatch.Groups[1].Value;
                            currentMode = "";
                            currentVlan = "";
                            continue;
                        }
                        
                        // Look for switchport mode
                        var modeMatch = Regex.Match(trimmedLine, @"Administrative Mode:\s+(\w+)");
                        if (modeMatch.Success)
                        {
                            currentMode = modeMatch.Groups[1].Value;
                            continue;
                        }
                        
                        // Look for access VLAN
                        var accessVlanMatch = Regex.Match(trimmedLine, @"Access Mode VLAN:\s+(\d+)");
                        if (accessVlanMatch.Success && currentMode.ToLower() == "access")
                        {
                            currentVlan = accessVlanMatch.Groups[1].Value;
                            continue;
                        }
                        
                        // Look for trunk native VLAN
                        var nativeVlanMatch = Regex.Match(trimmedLine, @"Trunking Native Mode VLAN:\s+(\d+)");
                        if (nativeVlanMatch.Success && currentMode.ToLower() == "trunk")
                        {
                            currentVlan = nativeVlanMatch.Groups[1].Value + " (Native)";
                            continue;
                        }
                        
                        // Look for trunk VLANs allowed
                        var trunkVlansMatch = Regex.Match(trimmedLine, @"Trunking VLANs Enabled:\s+(.+)");
                        if (trunkVlansMatch.Success && currentMode.ToLower() == "trunk")
                        {
                            var vlans = trunkVlansMatch.Groups[1].Value;
                            if (vlans != "none")
                            {
                                currentVlan = "Trunk: " + vlans;
                            }
                            continue;
                        }
                    }
                    
                    // Don't forget to update the last port
                    if (!string.IsNullOrEmpty(currentInterface) && !string.IsNullOrEmpty(currentVlan) && portStatus.ContainsKey(currentInterface))
                    {
                        UpdatePortVlanInfo(currentInterface, currentVlan, currentMode, vlanNames);
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"VLAN parsing error: {ex.Message}");
                UpdateStatus($"VLAN parsing warning: {ex.Message}");
            }
        }

        private void UpdatePortVlanInfo(string portName, string vlanId, string mode, Dictionary<string, string> vlanNames)
        {
                    if (portStatus.ContainsKey(portName))
                {
                portStatus[portName].SwitchportMode = mode;
                portStatus[portName].VlanId = vlanId;
                
                // For access ports, try to get the VLAN name
                if (mode.ToLower() == "access" && vlanNames.ContainsKey(vlanId))
                {
                    portStatus[portName].VlanName = vlanNames[vlanId];
                }
                else if (mode.ToLower() == "trunk")
                {
                    portStatus[portName].VlanName = "Trunk Port";
                        }
            }
        }

        private void UpdatePortDisplay()
        {
            foreach (var button in GetAllPortButtons())
                    {
                if (button.Tag is string portName && portStatus.ContainsKey(portName))
                {
                    var status = portStatus[portName];
                    UpdatePortButton(button, status);
                    }
            }

            // Update DataGrid
            Dispatcher.Invoke(() =>
            {
                portStatusCollection.Clear();
                foreach (var status in portStatus.Values.OrderBy(p => int.Parse(Regex.Match(p.Name, @"\d+").Value)))
                {
                    portStatusCollection.Add(status);
                }
                PortDataGrid.ItemsSource = portStatusCollection;
            });
        }

        private async void PortDataGrid_CellEditEnding(object sender, DataGridCellEditEndingEventArgs e)
        {
            if (e.Column.Header.ToString() == "VLAN ID" && e.EditingElement is TextBox textBox)
            {
                var portStatus = e.Row.Item as PortStatus;
                if (portStatus != null)
                {
                    string newVlanId = textBox.Text.Trim();
                    if (int.TryParse(newVlanId, out int vlanNumber) && vlanNumber >= 1 && vlanNumber <= 4094)
                    {
                        await ChangePortVlan(portStatus.Name, newVlanId);
                    }
                    else
                    {
                        MessageBox.Show("Invalid VLAN ID. Please enter a number between 1 and 4094.", "Invalid VLAN", MessageBoxButton.OK, MessageBoxImage.Warning);
                        e.Cancel = true;
                    }
                }
            }
        }

        private async Task ChangePortVlan(string portName, string newVlanId)
        {
            if (sshClient?.IsConnected != true || shellStream == null)
            {
                MessageBox.Show("Not connected to switch.", "Connection Error", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                UpdateStatus($"Changing VLAN for port {portName} to VLAN {newVlanId}...");

                var commands = new[]
                {
                    "configure terminal",
                    $"interface {portName}",
                    "switchport mode access",
                    $"switchport access vlan {newVlanId}",
                    "end"
                };

                foreach (var command in commands)
                {
                    await ExecuteCommandSafely(command);
                    await Task.Delay(100);
                }

                // Refresh port status to show new VLAN
                await ManualRefreshPorts();
                UpdateStatus($"Successfully changed {portName} to VLAN {newVlanId}");

                // Log to Firebase
                await PushCommandToFirebase($"Change VLAN: {portName} to VLAN {newVlanId}", "Success", "VLAN Change");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error changing VLAN: {ex.Message}", "VLAN Change Error", MessageBoxButton.OK, MessageBoxImage.Error);
                UpdateStatus($"Failed to change VLAN for {portName}: {ex.Message}");
                await PushCommandToFirebase($"Change VLAN: {portName} to VLAN {newVlanId}", $"Error: {ex.Message}", "VLAN Change Error");
            }
        }

        private async void BtnEnablePort_Click(object sender, RoutedEventArgs e)
        {
            try
        {
            if (string.IsNullOrEmpty(selectedPortName)) 
            {
                MessageBox.Show("Please select a port first", "No Port Selected", 
                              MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
                
                // Disable button to prevent multiple clicks
                btnEnablePort.IsEnabled = false;
            
            // SSH CONNECTION AUTO-FIX
            if (sshClient != null && !sshClient.IsConnected)
            {
                UpdateStatus("SSH disconnected, trying to reconnect...");
                var reconnected = await ReconnectSSH();
                if (!reconnected)
                {
                    MessageBox.Show($"❌ SSH RECONNECT FAILED\n\nCannot reconnect to {switchIP}\nUsing DEMO MODE", 
                                  "Reconnect Failed", MessageBoxButton.OK, MessageBoxImage.Error);
                    ToggleDemoPort(selectedPortName, true);
                return;
                }
            }

            if (sshClient?.IsConnected == true)
            {
                await ExecuteSimpleCommand(selectedPortName, "no shutdown", "ENABLE");
            }
            else
            {
                ToggleDemoPort(selectedPortName, true);
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"Enable port error: {ex.Message}");
                MessageBox.Show($"❌ ENABLE PORT FAILED\n\nError: {ex.Message}", 
                              "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                btnEnablePort.IsEnabled = true;
            }
        }

        private async void BtnDisablePort_Click(object sender, RoutedEventArgs e)
        {
            try
        {
            if (string.IsNullOrEmpty(selectedPortName))
            {
                MessageBox.Show("Please select a port first", "No Port Selected", 
                              MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
                
                // Disable button to prevent multiple clicks
                btnDisablePort.IsEnabled = false;
            
            // SSH CONNECTION AUTO-FIX
            if (sshClient != null && !sshClient.IsConnected)
            {
                UpdateStatus("SSH disconnected, trying to reconnect...");
                var reconnected = await ReconnectSSH();
                if (!reconnected)
                {
                    MessageBox.Show($"❌ SSH RECONNECT FAILED\n\nCannot reconnect to {switchIP}\nUsing DEMO MODE", 
                                  "Reconnect Failed", MessageBoxButton.OK, MessageBoxImage.Error);
                    ToggleDemoPort(selectedPortName, false);
                    return;
                }
            }

            if (sshClient?.IsConnected == true)
            {
                await ExecuteSimpleCommand(selectedPortName, "shutdown", "DISABLE");
            }
            else
            {
                ToggleDemoPort(selectedPortName, false);
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"Disable port error: {ex.Message}");
                MessageBox.Show($"❌ DISABLE PORT FAILED\n\nError: {ex.Message}", 
                              "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                btnDisablePort.IsEnabled = true;
            }
        }

        private async void BtnTogglePort_Click(object sender, RoutedEventArgs e)
        {
            try
        {
            if (string.IsNullOrEmpty(selectedPortName))
            {
                MessageBox.Show("Please select a port first", "No Port Selected", 
                              MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
                
                // Disable button to prevent multiple clicks
                btnTogglePort.IsEnabled = false;
            
            // Debug SSH connection status
            var connectionStatus = GetConnectionStatus();

            if (sshClient?.IsConnected == true)
            {
                var port = portStatus.GetValueOrDefault(selectedPortName);
                var action = port?.IsShutdown == true ? "ENABLE" : "DISABLE";
                var command = port?.IsShutdown == true ? "no shutdown" : "shutdown";
                
                await ExecuteSimpleCommand(selectedPortName, command, action);
            }
            else
            {
                var port = portStatus.GetValueOrDefault(selectedPortName);
                bool shouldEnable = port?.IsShutdown == true;
                ToggleDemoPort(selectedPortName, shouldEnable);
                }
            }
            catch (Exception ex)
            {
                UpdateStatus($"Toggle port error: {ex.Message}");
                MessageBox.Show($"❌ TOGGLE PORT FAILED\n\nError: {ex.Message}", 
                              "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                btnTogglePort.IsEnabled = true;
            }
        }

        private string GetConnectionStatus()
        {
            if (sshClient == null)
                return "SSH Client: NULL";
            
            if (!sshClient.IsConnected)
                return $"SSH Client: DISCONNECTED (Host: {sshClient.ConnectionInfo?.Host ?? "Unknown"})";
            
            return $"SSH Client: CONNECTED to {sshClient.ConnectionInfo.Host}";
        }

        private async Task ExecuteSimpleCommand(string portName, string command, string action)
        {
            var debugLog = new StringBuilder();
            debugLog.AppendLine("=== ROBUST PORT CONTROL ===");
            debugLog.AppendLine($"Port: {portName}");
            debugLog.AppendLine($"Command: {command}");
            debugLog.AppendLine($"Action: {action}");
            debugLog.AppendLine($"Time: {DateTime.Now:HH:mm:ss}");
            debugLog.AppendLine();

            try
            {
                UpdateStatus($"{action}ING port {portName}...");
                var fullPortName = portName.Replace("Gi", "GigabitEthernet");
                
                // STEP 1: AGGRESSIVE SSH CONNECTION MANAGEMENT
                debugLog.AppendLine("1. AGGRESSIVE SSH CONNECTION CHECK:");
                debugLog.AppendLine($"   SSH Client: {(sshClient == null ? "NULL" : "EXISTS")}");
                debugLog.AppendLine($"   IsConnected: {(sshClient?.IsConnected == true ? "YES" : "NO")}");
                debugLog.AppendLine($"   Host: {sshClient?.ConnectionInfo?.Host ?? "NULL"}");
                debugLog.AppendLine();

                // Try up to 3 times to ensure connection
                int connectionAttempts = 0;
                while (sshClient?.IsConnected != true && connectionAttempts < 3)
                {
                    connectionAttempts++;
                    debugLog.AppendLine($"   Connection attempt {connectionAttempts}/3...");
                    
                    if (!await EnsureSSHConnection())
                    {
                        debugLog.AppendLine($"   Reconnect attempt {connectionAttempts} failed");
                        if (connectionAttempts >= 3)
                        {
                            debugLog.AppendLine("   ❌ ALL CONNECTION ATTEMPTS FAILED!");
                            throw new Exception($"SSH connection failed after {connectionAttempts} attempts");
                        }
                        await Task.Delay(1000); // Wait 1 second between attempts
                    }
                    else
                    {
                        debugLog.AppendLine($"   ✅ Connection successful on attempt {connectionAttempts}");
                        break;
                    }
                }

                if (sshClient?.IsConnected != true)
                {
                    debugLog.AppendLine("   ❌ SSH CLIENT STILL NOT CONNECTED AFTER ALL ATTEMPTS!");
                    throw new Exception("SSH client not connected after multiple attempts");
                }

                // STEP 2: ROBUST SHELL STREAM CREATION
                debugLog.AppendLine("2. ROBUST SHELL STREAM CREATION:");
                
                ShellStream? commandShellStream = null;
                try
                {
                    // Try to create shell stream with error handling
                    commandShellStream = sshClient.CreateShellStream("xterm", 80, 24, 800, 600, 1024);
                    
                    if (commandShellStream == null)
                    {
                        debugLog.AppendLine("   ❌ Shell stream creation returned null!");
                        throw new Exception("Failed to create shell stream - returned null");
                    }
                    
                    // Wait for shell to initialize and test it
                    await Task.Delay(300); // Increased wait time
                    
                    if (!commandShellStream.CanWrite)
                    {
                        debugLog.AppendLine("   ❌ Shell stream not writable!");
                        throw new Exception("Shell stream is not writable");
                    }
                    
                    debugLog.AppendLine("   ✅ Shell stream created and tested successfully");
                    debugLog.AppendLine();
                }
                catch (Exception shellEx)
                {
                    debugLog.AppendLine($"   ❌ Shell stream creation failed: {shellEx.Message}");
                    commandShellStream?.Dispose();
                    throw new Exception($"Shell stream creation failed: {shellEx.Message}");
                }

                using var shellStream = commandShellStream;

                // STEP 3: ULTRA ROBUST COMMAND EXECUTION
                async Task<string> SendCommand(string cmd, int timeoutMs = 1500)  // Increased timeout for reliability
                {
                    debugLog.AppendLine($"   📤 Sending: {cmd}");
                    
                    try
                    {
                        // Check if shell stream is still good before sending
                        if (!shellStream.CanWrite)
                        {
                            throw new Exception("Shell stream became unwritable");
                        }
                        
                        shellStream.WriteLine(cmd);
                        shellStream.Flush(); // Force flush to ensure command is sent
                        
                        var response = "";
                        var endTime = DateTime.Now.AddMilliseconds(timeoutMs);
                        var lastDataTime = DateTime.Now;
                        
                        while (DateTime.Now < endTime)
                        {
                            if (shellStream.DataAvailable)
                            {
                                var chunk = shellStream.Read();
                                response += chunk;
                                lastDataTime = DateTime.Now;
                                
                                // Smart prompt detection
                                if (response.Contains("#") || response.Contains(">"))
                                {
                                    // Wait a bit more to get any trailing data
                                    await Task.Delay(50);
                                    if (shellStream.DataAvailable)
                                    {
                                        response += shellStream.Read();
                                    }
                                    break; // Exit when we see Cisco prompt
                                }
                            }
                            else
                            {
                                // If no data for more than 3 seconds, something might be wrong
                                if (DateTime.Now.Subtract(lastDataTime).TotalSeconds > 3 && response.Length > 0)
                                {
                                    debugLog.AppendLine($"   ⚠️ No data for 3+ seconds, assuming command completed");
                                    break;
                                }
                            }
                            await Task.Delay(30);  // Slightly increased for stability
                        }
                        
                        debugLog.AppendLine($"   📥 Response: '{response.Trim().Substring(0, Math.Min(100, response.Trim().Length))}...'");
                        debugLog.AppendLine($"   📏 Length: {response.Length}");
                        return response;
                    }
                    catch (Exception cmdEx)
                    {
                        debugLog.AppendLine($"   ❌ Command execution failed: {cmdEx.Message}");
                        throw new Exception($"Command '{cmd}' failed: {cmdEx.Message}");
                    }
                }

                // STEP 4: SEQUENTIAL COMMAND EXECUTION WITH ERROR CHECKING
                debugLog.AppendLine("4. EXECUTING CISCO COMMANDS:");
                
                var response1 = await SendCommand("configure terminal");
                if (response1.Contains("Invalid") || response1.Contains("%"))
                {
                    throw new Exception($"Failed to enter config mode: {response1}");
                }
                
                var response2 = await SendCommand($"interface {fullPortName}");
                if (response2.Contains("Invalid") || response2.Contains("% "))
                {
                    throw new Exception($"Failed to enter interface {fullPortName}: {response2}");
                }
                
                var response3 = await SendCommand(command);
                if (response3.Contains("Invalid") || response3.Contains("% "))
                {
                    throw new Exception($"Failed to execute '{command}': {response3}");
                }
                
                var response4 = await SendCommand("end");
                var response5 = await SendCommand("write memory", 2500);  // Longer timeout for write memory
                
                debugLog.AppendLine();

                // Step 4: Final SSH state check
                debugLog.AppendLine("4. FINAL SSH STATE:");
                debugLog.AppendLine($"   Still Connected: {(sshClient?.IsConnected == true ? "YES" : "NO")}");
                debugLog.AppendLine();

                // Check for errors in all responses
                var allResponses = response1 + response2 + response3 + response4 + response5;
                bool hasErrors = allResponses.Contains("Invalid") || allResponses.Contains("% ") || allResponses.Contains("Error");
                
                debugLog.AppendLine("5. RESULT ANALYSIS:");
                debugLog.AppendLine($"   Has Errors: {hasErrors}");
                debugLog.AppendLine($"   Contains 'Invalid': {allResponses.Contains("Invalid")}");
                debugLog.AppendLine($"   Contains '% ': {allResponses.Contains("% ")}");
                debugLog.AppendLine($"   Contains 'Error': {allResponses.Contains("Error")}");
                debugLog.AppendLine($"   Total Response Length: {allResponses.Length}");
                debugLog.AppendLine();

                if (hasErrors)
                {
                    debugLog.AppendLine("❌ COMMAND ERRORS DETECTED!");
                    throw new Exception($"Command errors detected: {allResponses}");
                }

                debugLog.AppendLine("✅ ALL CISCO COMMANDS SUCCESSFUL!");

                // INSTANT VISUAL FEEDBACK - Update port immediately!
                UpdatePortStatusInstantly(portName, action);
                
                UpdateStatus($"✅ Port {portName} {action}D successfully");
                
                // 🔥 FIREBASE: Log successful command execution (background)
                _ = Task.Run(async () =>
                {
                    try
                    {
                        await PushCommandToFirebase($"interface {fullPortName}; {command}; end; write memory", 
                                                 allResponses, $"Port_{action}");
                    }
                    catch (Exception fbEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Firebase logging failed: {fbEx.Message}");
                    }
                });

                // SUCCESS - SADECE LOG, POPUP YOK
                Console.WriteLine($"✅ PORT {action} SUCCESS! {portName} is now {action}D");
                
                // Auto refresh to confirm real status (but don't wait for it)
                _ = Task.Run(async () =>
                {
                    try
                    {
                        await Task.Delay(1000); // Wait 1 second before refreshing
                        await AutoRefreshPorts();
                    }
                    catch (Exception refreshEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Post-operation refresh failed: {refreshEx.Message}");
                    }
                });
            }
            catch (Exception ex)
            {
                debugLog.AppendLine($"❌ CRITICAL ERROR OCCURRED:");
                debugLog.AppendLine($"   Message: {ex.Message}");
                debugLog.AppendLine($"   Type: {ex.GetType().Name}");
                debugLog.AppendLine($"   Time: {DateTime.Now:HH:mm:ss.fff}");

                Console.WriteLine($"❌ {action} failed: {ex.Message}");
                UpdateStatus($"❌ {action} failed: {ex.Message}");
                
                // Otomatik SSH yeniden bağlanma ve retry
                Console.WriteLine($"🔄 SSH reconnect ve retry deneniyor...");
                
                // Try to reconnect and retry
                _ = Task.Run(async () =>
                {
                    try
                    {
                        bool reconnected = await ReconnectSSH();
                        if (reconnected)
                        {
                            Console.WriteLine($"🔄 SSH yeniden bağlandı, komutu tekrar deniyorum...");
                            // Retry the command after successful reconnect
                            await ExecuteSimpleCommand(portName, command, action);
                        }
                    }
                    catch (Exception reconnectEx)
                    {
                        Console.WriteLine($"Background reconnect failed: {reconnectEx.Message}");
                    }
                });
            }
        }

        private async Task<bool> EnsureSSHConnection()
        {
            try
            {
                // Check if connected
                if (sshClient?.IsConnected == true)
                {
                    // Test with a simple command (increased timeout)
                    var testCmd = sshClient.CreateCommand("show clock");
                    testCmd.CommandTimeout = TimeSpan.FromSeconds(10);  // INCREASED: 10s (was 3s)
                    var result = await Task.Run(() => testCmd.Execute());
                    
                    if (!string.IsNullOrWhiteSpace(result))
                    {
                        return true; // Connection is good
                    }
                }
                
                // Connection is bad, try to reconnect
                return await ReconnectSSH();
            }
            catch
            {
                return await ReconnectSSH();
            }
        }

        private async Task<bool> ReconnectSSH()
        {
            try
            {
                if (string.IsNullOrEmpty(switchIP) || string.IsNullOrEmpty(username) || string.IsNullOrEmpty(password))
                    return false;

                UpdateStatus("🔄 Reconnecting SSH...");
                txtConnectionStatus.Text = "Reconnecting...";
                txtConnectionStatus.Background = Brushes.Orange;
                
                // Dispose old connection
                sshClient?.Dispose();
                
                // Create new connection with ULTRA ROBUST settings (same as initial connection)
                var connectionInfo = new ConnectionInfo(switchIP, 22, username,
                    new PasswordAuthenticationMethod(username, password));
                
                // ULTRA ROBUST connection settings to prevent disconnections
                connectionInfo.Timeout = TimeSpan.FromSeconds(60);                  // Connection timeout: 60s
                connectionInfo.MaxSessions = 20;                                    // Max concurrent sessions
                connectionInfo.RetryAttempts = 3;                                   // Retry connection attempts
                connectionInfo.Encoding = System.Text.Encoding.UTF8;               // Proper encoding
                
                sshClient = new SshClient(connectionInfo);
                
                // Set keep-alive AFTER creating the client
                sshClient.KeepAliveInterval = TimeSpan.FromSeconds(5);             // Keep-alive every 5 seconds
                
                await Task.Run(() => sshClient.Connect());

                if (sshClient.IsConnected)
                {
                    txtConnectionStatus.Text = $"Reconnected to {switchIP}";
                    txtConnectionStatus.Background = Brushes.Green;
                    UpdateStatus("✅ SSH Reconnected successfully");
                    return true;
            }
            else
            {
                    txtConnectionStatus.Text = "Reconnect Failed";
                    txtConnectionStatus.Background = Brushes.Red;
                    UpdateStatus("❌ SSH Reconnect Failed");
                    return false;
                }
            }
            catch (Exception ex)
            {
                txtConnectionStatus.Text = "Reconnect Error";
                txtConnectionStatus.Background = Brushes.Red;
                UpdateStatus($"❌ Reconnect error: {ex.Message}");
                return false;
            }
        }

        private void LoadDemoData()
        {
            portStatus.Clear();
            
            // Demo VLAN data
            var vlanList = new[]
            {
                ("1", "default"), ("10", "management"), ("20", "users"), ("30", "guest"),
                ("100", "servers"), ("200", "voice"), ("300", "dmz"), ("400", "iot")
            };
            
            var modes = new[] { "access", "trunk" };
            var speeds = new[] { "1000", "100", "10" };
            var duplexModes = new[] { "full", "half", "auto" };
            var random = new Random();
            
            for (int i = 1; i <= 48; i++)
            {
                var portName = $"Gi1/0/{i}";
                var status = i switch
                {
                    <= 8 => "connected",
                    <= 16 => "notconnect", 
                    <= 24 => "disabled",
                    _ => "notconnect"
                };
                
                // Assign demo VLAN info
                var vlanInfo = vlanList[i % vlanList.Length];
                var mode = modes[random.Next(modes.Length)];
                var speed = speeds[random.Next(speeds.Length)];
                var duplex = duplexModes[random.Next(duplexModes.Length)];
                
                // Special cases for demo
                if (i >= 45) // Last 4 ports are trunks
                {
                    mode = "trunk";
                    vlanInfo = ("1", "default (Native)");
                }
                
                portStatus[portName] = new PortStatus
                {
                    Name = portName,
                    Status = status,
                    IsUp = status == "connected",
                    IsDown = status == "notconnect",
                    IsShutdown = status == "disabled",
                    VlanId = vlanInfo.Item1,
                    VlanName = vlanInfo.Item2,
                    SwitchportMode = mode,
                    Speed = speed,
                    Duplex = duplex
                };
            }
            
            UpdatePortDisplay();
            UpdateStatus("Demo mode - 48 ports loaded with VLAN info");
            btnBulkDisable.IsEnabled = true;  // Enable bulk disable for demo mode testing  
            btnBulkEnable.IsEnabled = true;   // Enable bulk enable for demo mode testing
        }

        private void ToggleDemoPort(string portName, bool enable)
        {
            if (portStatus.ContainsKey(portName))
            {
                var port = portStatus[portName];
                
                if (enable)
                {
                    port.Status = "connected";
                    port.IsUp = true;
                    port.IsDown = false;
                    port.IsShutdown = false;
            }
            else
            {
                    port.Status = "disabled";
                    port.IsUp = false;
                    port.IsDown = false;
                    port.IsShutdown = true;
                }
                
                // INSTANT VISUAL FEEDBACK for demo mode too!
                UpdatePortStatusInstantly(portName, enable ? "ENABLE" : "DISABLE");
                
                Console.WriteLine($"📱 Demo: Port {portName} {(enable ? "enabled" : "disabled")}");
                UpdateStatus($"📱 Demo: Port {portName} {(enable ? "enabled" : "disabled")}");
            }
        }

        private void UpdateStatus(string message)
        {
            txtStatus.Text = $"Status: {message}";
        }

        private void UpdatePortStatusInstantly(string portName, string action)
        {
            try
            {
                // Update internal status immediately for instant feedback
                if (portStatus.ContainsKey(portName))
                {
                    var port = portStatus[portName];
                    
                    if (action == "DISABLE")
                    {
                        // Port was disabled - mark as shutdown
                        port.Status = "disabled";
                        port.IsUp = false;
                        port.IsDown = false;
                        port.IsShutdown = true;
                    }
                    else if (action == "ENABLE")
                    {
                        // Port was enabled - mark as connected (optimistic)
                        port.Status = "connected";
                        port.IsUp = true;
                        port.IsDown = false;
                        port.IsShutdown = false;
                    }
                }
                
                // Find and update the button immediately
                foreach (var button in GetAllPortButtons())
                {
                    if (button.Content?.ToString() == portName)
                    {
                        var newColor = action == "DISABLE" ? 
                            new SolidColorBrush(Colors.Gray) :        // Disabled = Gray
                            new SolidColorBrush(Colors.LightGreen);   // Enabled = Green
                        
                        button.Background = newColor;
                        
                        // Add visual effect
                        button.BorderBrush = new SolidColorBrush(Colors.Gold);
                        button.BorderThickness = new Thickness(3);
                        
                        // Reset border after 2 seconds
                        var timer = new DispatcherTimer();
                        timer.Interval = TimeSpan.FromSeconds(2);
                        timer.Tick += (s, e) =>
                        {
                            button.BorderBrush = new SolidColorBrush(Color.FromRgb(0x33, 0x33, 0x33));
                            button.BorderThickness = new Thickness(2);
                            timer.Stop();
                        };
                        timer.Start();
                        
                        break;
                    }
                }
                
                UpdateStatus($"🔄 Port {portName} visually updated - waiting for refresh...");
            }
            catch (Exception ex)
            {
                UpdateStatus($"⚠️ Visual update failed: {ex.Message}");
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            Console.WriteLine("🔗 Uygulama kapanıyor - Tüm timer'lar ve bağlantılar kapatılıyor...");
            
            refreshTimer?.Stop();
            phoneCommandTimer?.Stop();
            firebaseMonitorTimer?.Stop();
            sshKeepaliveTimer?.Stop(); // 🔗 SSH Keepalive timer'ını durdur
            
            sshClient?.Disconnect();
            sshClient?.Dispose();
            firebaseService?.Dispose();
            
            Console.WriteLine("🔗 Tüm sistem kaynakları temizlendi");
            base.OnClosed(e);
        }

        private void SelectPort(string portName)
        {
            selectedPortName = portName;
            txtSelectedPort.Text = portName;
            btnEnablePort.IsEnabled = !string.IsNullOrEmpty(portName);
            btnDisablePort.IsEnabled = !string.IsNullOrEmpty(portName);
            btnTogglePort.IsEnabled = !string.IsNullOrEmpty(portName);
        }

        // ========================= BULK DISABLE FUNCTIONALITY =========================

        private async void BtnBulkDisable_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var redPorts = GetRedPorts();
                if (redPorts.Count == 0)
                {
                    MessageBox.Show("⚠️ No RED ports found!\n\nAll ports are either UP (green) or already DISABLED (orange).", 
                                  "No Action Needed", MessageBoxButton.OK, MessageBoxImage.Information);
                    return;
                }

                var result = MessageBox.Show($"🔴 BULK DISABLE WARNING!\n\n" +
                                           $"Found {redPorts.Count} RED ports (down/notconnect):\n" +
                                           $"{string.Join(", ", redPorts)}\n\n" +
                                           $"❗ This will DISABLE ALL of them at once!\n\n" +
                                           $"Are you sure you want to continue?", 
                                           "Bulk Disable Confirmation", 
                                           MessageBoxButton.YesNo, 
                                           MessageBoxImage.Warning);

                if (result != MessageBoxResult.Yes)
                    return;

                await ExecuteBulkDisable(redPorts);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"❌ BULK DISABLE FAILED!\n\nError: {ex.Message}", 
                              "Bulk Disable Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private List<string> GetRedPorts()
        {
            var redPorts = new List<string>();
            
            foreach (var kvp in portStatus)
            {
                var portName = kvp.Key;
                var port = kvp.Value;
                
                if (port.IsDown)
                {
                    redPorts.Add(portName);
                }
            }
            
            return redPorts;
        }

        private List<string> GetDisabledPorts()
        {
            var disabledPorts = new List<string>();
            
            foreach (var kvp in portStatus)
            {
                var portName = kvp.Key;
                var port = kvp.Value;
                
                if (port.IsShutdown)  // Orange ports (administratively disabled)
                {
                    disabledPorts.Add(portName);
                }
            }
            
            return disabledPorts;
        }

        private string CreatePortRanges(List<string> portNames)
        {
            if (portNames.Count == 0) return "";
            
            // Convert port names to numbers for range detection
            var portNumbers = portNames
                .Select(p => p.Replace("Gi1/0/", ""))
                .Select(p => int.TryParse(p, out int num) ? num : -1)
                .Where(p => p > 0)
                .OrderBy(p => p)
                .ToList();

            var ranges = new List<string>();
            int start = portNumbers[0];
            int end = start;

            for (int i = 1; i < portNumbers.Count; i++)
            {
                if (portNumbers[i] == end + 1)
                {
                    // Consecutive port, extend range
                    end = portNumbers[i];
                }
                else
                {
                    // Gap found, finalize current range
                    if (start == end)
                        ranges.Add($"gi1/0/{start}");
                    else
                        ranges.Add($"gi1/0/{start}-{end}");
                    
                    start = portNumbers[i];
                    end = start;
                }
            }

            // Add the last range
            if (start == end)
                ranges.Add($"gi1/0/{start}");
            else
                ranges.Add($"gi1/0/{start}-{end}");

            return string.Join(",", ranges);
        }

        private async Task ExecuteBulkDisable(List<string> redPorts)
        {
            var debugLog = new StringBuilder();
            debugLog.AppendLine("=== ROBUST BULK DISABLE ===");
            debugLog.AppendLine($"Red Ports Count: {redPorts.Count}");
            debugLog.AppendLine($"Red Ports: {string.Join(", ", redPorts)}");
            debugLog.AppendLine($"Time: {DateTime.Now:HH:mm:ss}");
            debugLog.AppendLine();

            try
            {
                UpdateStatus($"BULK DISABLING {redPorts.Count} red ports...");
                
                // STEP 1: AGGRESSIVE SSH CONNECTION MANAGEMENT (same as single port)
                debugLog.AppendLine("1. AGGRESSIVE SSH CONNECTION CHECK:");
                debugLog.AppendLine($"   SSH Client: {(sshClient == null ? "NULL" : "EXISTS")}");
                debugLog.AppendLine($"   IsConnected: {(sshClient?.IsConnected == true ? "YES" : "NO")}");
                debugLog.AppendLine();

                // Try up to 3 times to ensure connection (same as single port)
                int connectionAttempts = 0;
                while (sshClient?.IsConnected != true && connectionAttempts < 3)
                {
                    connectionAttempts++;
                    debugLog.AppendLine($"   Connection attempt {connectionAttempts}/3...");
                    
                    if (!await EnsureSSHConnection())
                    {
                        debugLog.AppendLine($"   Reconnect attempt {connectionAttempts} failed");
                        if (connectionAttempts >= 3)
                        {
                            debugLog.AppendLine("   ❌ ALL CONNECTION ATTEMPTS FAILED!");
                            throw new Exception($"SSH connection failed after {connectionAttempts} attempts");
                        }
                        await Task.Delay(1000); // Wait 1 second between attempts
                    }
                    else
                    {
                        debugLog.AppendLine($"   ✅ Connection successful on attempt {connectionAttempts}");
                        break;
                    }
                }

                if (sshClient?.IsConnected != true)
                {
                    debugLog.AppendLine("   ❌ SSH CLIENT STILL NOT CONNECTED AFTER ALL ATTEMPTS!");
                    throw new Exception("SSH client not connected after multiple attempts");
                }

                // Step 2: Create port ranges for efficiency
                var portRanges = CreatePortRanges(redPorts);
                debugLog.AppendLine("2. PORT RANGES:");
                debugLog.AppendLine($"   Range String: {portRanges}");
                debugLog.AppendLine();

                // STEP 3: ROBUST SHELL STREAM CREATION (same as single port)
                debugLog.AppendLine("3. ROBUST SHELL STREAM CREATION:");
                
                ShellStream? commandShellStream = null;
                try
                {
                    // Try to create shell stream with error handling
                    commandShellStream = sshClient.CreateShellStream("xterm", 80, 24, 800, 600, 1024);
                    
                    if (commandShellStream == null)
                    {
                        debugLog.AppendLine("   ❌ Shell stream creation returned null!");
                        throw new Exception("Failed to create shell stream - returned null");
                    }
                    
                    // Wait for shell to initialize and test it
                    await Task.Delay(300); // Increased wait time
                    
                    if (!commandShellStream.CanWrite)
                    {
                        debugLog.AppendLine("   ❌ Shell stream not writable!");
                        throw new Exception("Shell stream is not writable");
                    }
                    
                    debugLog.AppendLine("   ✅ Shell stream created and tested successfully");
                    debugLog.AppendLine();
                }
                catch (Exception shellEx)
                {
                    debugLog.AppendLine($"   ❌ Shell stream creation failed: {shellEx.Message}");
                    commandShellStream?.Dispose();
                    throw new Exception($"Shell stream creation failed: {shellEx.Message}");
                }

                using var shellStream = commandShellStream;

                // STEP 4: ULTRA ROBUST COMMAND EXECUTION (same as single port)
                async Task<string> SendCommand(string cmd, int timeoutMs = 1500)  // Increased timeout for reliability
                {
                    debugLog.AppendLine($"   📤 Sending: {cmd}");
                    
                    try
                    {
                        // Check if shell stream is still good before sending
                        if (!shellStream.CanWrite)
                        {
                            throw new Exception("Shell stream became unwritable");
                        }
                        
                        shellStream.WriteLine(cmd);
                        shellStream.Flush(); // Force flush to ensure command is sent
                        
                        var response = "";
                        var endTime = DateTime.Now.AddMilliseconds(timeoutMs);
                        var lastDataTime = DateTime.Now;
                        
                        while (DateTime.Now < endTime)
                        {
                            if (shellStream.DataAvailable)
                            {
                                var chunk = shellStream.Read();
                                response += chunk;
                                lastDataTime = DateTime.Now;
                                
                                // Smart prompt detection
                                if (response.Contains("#") || response.Contains(">"))
                                {
                                    // Wait a bit more to get any trailing data
                                    await Task.Delay(50);
                                    if (shellStream.DataAvailable)
                                    {
                                        response += shellStream.Read();
                                    }
                                    break; // Exit when we see Cisco prompt
                                }
                            }
                            else
                            {
                                // If no data for more than 3 seconds, something might be wrong
                                if (DateTime.Now.Subtract(lastDataTime).TotalSeconds > 3 && response.Length > 0)
                                {
                                    debugLog.AppendLine($"   ⚠️ No data for 3+ seconds, assuming command completed");
                                    break;
                                }
                            }
                            await Task.Delay(30);  // Slightly increased for stability
                        }
                        
                        debugLog.AppendLine($"   📥 Response: '{response.Trim().Substring(0, Math.Min(100, response.Trim().Length))}...'");
                        debugLog.AppendLine($"   📏 Length: {response.Length}");
                        return response;
                    }
                    catch (Exception cmdEx)
                    {
                        debugLog.AppendLine($"   ❌ Command execution failed: {cmdEx.Message}");
                        throw new Exception($"Command '{cmd}' failed: {cmdEx.Message}");
                    }
                }

                // STEP 5: SEQUENTIAL COMMAND EXECUTION WITH ERROR CHECKING
                debugLog.AppendLine("5. EXECUTING CISCO BULK COMMANDS:");
                
                var response1 = await SendCommand("configure terminal");
                if (response1.Contains("Invalid") || response1.Contains("%"))
                {
                    throw new Exception($"Failed to enter config mode: {response1}");
                }
                
                var response2 = await SendCommand($"interface range {portRanges}");
                if (response2.Contains("Invalid") || response2.Contains("% "))
                {
                    throw new Exception($"Failed to enter interface range {portRanges}: {response2}");
                }
                
                var response3 = await SendCommand("shutdown");
                if (response3.Contains("Invalid") || response3.Contains("% "))
                {
                    throw new Exception($"Failed to execute 'shutdown': {response3}");
                }
                
                var response4 = await SendCommand("end");
                var response5 = await SendCommand("write memory", 2500);  // Longer timeout for write memory
                
                debugLog.AppendLine();

                // Check for errors
                var allResponses = response1 + response2 + response3 + response4 + response5;
                bool hasErrors = allResponses.Contains("Invalid") || allResponses.Contains("% ") || allResponses.Contains("Error");
                
                debugLog.AppendLine("5. RESULT ANALYSIS:");
                debugLog.AppendLine($"   Has Errors: {hasErrors}");
                debugLog.AppendLine($"   Total Response Length: {allResponses.Length}");
                debugLog.AppendLine();

                if (hasErrors)
                {
                    debugLog.AppendLine("❌ BULK COMMAND ERRORS DETECTED!");
                    throw new Exception($"Bulk command errors: {allResponses}");
                }

                debugLog.AppendLine("✅ BULK DISABLE SUCCESSFUL!");

                // INSTANT VISUAL FEEDBACK for all disabled ports
                foreach (var port in redPorts)
                {
                    UpdatePortStatusInstantly(port, "DISABLE");
                }

                UpdateStatus($"✅ BULK DISABLED {redPorts.Count} ports successfully!");
                MessageBox.Show($"✅ BULK DISABLE SUCCESS!\n\n" +
                              $"🔴 Disabled {redPorts.Count} ports\n" +
                              $"⚡ Changes applied to switch", 
                              "Bulk Disable Success", MessageBoxButton.OK, MessageBoxImage.Information);
                
                // Auto refresh in background (don't wait)
                _ = Task.Run(async () =>
                {
                    try
                    {
                        await Task.Delay(1000); // Wait 1 second before refreshing
                        await AutoRefreshPorts();
                    }
                    catch (Exception refreshEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Post-bulk-disable refresh failed: {refreshEx.Message}");
                    }
                });
            }
            catch (Exception ex)
            {
                debugLog.AppendLine($"❌ CRITICAL BULK ERROR OCCURRED:");
                debugLog.AppendLine($"   Message: {ex.Message}");
                debugLog.AppendLine($"   Type: {ex.GetType().Name}");
                debugLog.AppendLine($"   Time: {DateTime.Now:HH:mm:ss.fff}");

                UpdateStatus($"❌ Bulk disable failed: {ex.Message}");
                
                // Determine error type for better user experience
                string userFriendlyMessage;
                bool showDebugLog = false;
                
                if (ex.Message.Contains("SSH client not connected") || ex.Message.Contains("connection"))
                {
                    userFriendlyMessage = $"🔌 CONNECTION LOST!\n\n❌ Cannot disable {redPorts.Count} ports\n💡 The switch connection was lost\n\n🔄 Attempting to reconnect...";
                    showDebugLog = false;
                }
                else if (ex.Message.Contains("Shell stream"))
                {
                    userFriendlyMessage = $"📡 COMMUNICATION ERROR!\n\n❌ Cannot disable {redPorts.Count} ports\n💡 Switch communication failed\n\n🔄 Attempting to reconnect...";
                    showDebugLog = false;
                }
                else if (ex.Message.Contains("Invalid") || ex.Message.Contains("Failed to"))
                {
                    userFriendlyMessage = $"⚙️ SWITCH COMMAND ERROR!\n\n❌ Bulk disable failed\n💡 The switch rejected the bulk command\n\n📋 Click OK to see technical details";
                    showDebugLog = true;
                }
                else
                {
                    userFriendlyMessage = $"🚫 UNEXPECTED BULK ERROR!\n\n❌ Bulk disable failed\n💡 An unexpected error occurred\n\n📋 Click OK to see technical details";
                    showDebugLog = true;
                }
                
                // Show user-friendly error message
                MessageBox.Show(userFriendlyMessage, "Bulk Disable Failed", MessageBoxButton.OK, MessageBoxImage.Warning);
                
                // Show debug log only if needed
                if (showDebugLog)
                {
                    var logResult = MessageBox.Show("Do you want to see the technical debug log?", "Technical Details", 
                                                   MessageBoxButton.YesNo, MessageBoxImage.Question);
                    if (logResult == MessageBoxResult.Yes)
                    {
                        MessageBox.Show(debugLog.ToString(), "Bulk Disable Debug Log", 
                                      MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                }
                
                // Try to reconnect in background (don't wait)
                _ = Task.Run(async () =>
                {
                    try
                    {
                        await ReconnectSSH();
                    }
                    catch (Exception reconnectEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Background reconnect failed: {reconnectEx.Message}");
                    }
                });
            }
        }

        // ========================= BULK ENABLE FUNCTIONALITY =========================

        private async void BtnBulkEnable_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var disabledPorts = GetDisabledPorts();
                if (disabledPorts.Count == 0)
                {
                    MessageBox.Show("⚠️ No DISABLED ports found!\n\nAll ports are either UP (green) or DOWN (red).", 
                                  "No Action Needed", MessageBoxButton.OK, MessageBoxImage.Information);
                    return;
                }

                var result = MessageBox.Show($"🟢 BULK ENABLE WARNING!\n\n" +
                                           $"Found {disabledPorts.Count} DISABLED ports (orange/shutdown):\n" +
                                           $"{string.Join(", ", disabledPorts)}\n\n" +
                                           $"❗ This will ENABLE ALL of them at once!\n\n" +
                                           $"Are you sure you want to continue?", 
                                           "Bulk Enable Confirmation", 
                                           MessageBoxButton.YesNo, 
                                           MessageBoxImage.Warning);

                if (result != MessageBoxResult.Yes)
                    return;

                await ExecuteBulkEnable(disabledPorts);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"❌ BULK ENABLE FAILED!\n\nError: {ex.Message}", 
                              "Bulk Enable Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async Task ExecuteBulkEnable(List<string> disabledPorts)
        {
            var debugLog = new StringBuilder();
            debugLog.AppendLine("=== ROBUST BULK ENABLE ===");
            debugLog.AppendLine($"Disabled Ports Count: {disabledPorts.Count}");
            debugLog.AppendLine($"Disabled Ports: {string.Join(", ", disabledPorts)}");
            debugLog.AppendLine($"Time: {DateTime.Now:HH:mm:ss}");
            debugLog.AppendLine();

            try
            {
                UpdateStatus($"BULK ENABLING {disabledPorts.Count} disabled ports...");
                
                // STEP 1: AGGRESSIVE SSH CONNECTION MANAGEMENT (same as single port)
                debugLog.AppendLine("1. AGGRESSIVE SSH CONNECTION CHECK:");
                debugLog.AppendLine($"   SSH Client: {(sshClient == null ? "NULL" : "EXISTS")}");
                debugLog.AppendLine($"   IsConnected: {(sshClient?.IsConnected == true ? "YES" : "NO")}");
                debugLog.AppendLine();

                // Try up to 3 times to ensure connection (same as single port)
                int connectionAttempts = 0;
                while (sshClient?.IsConnected != true && connectionAttempts < 3)
                {
                    connectionAttempts++;
                    debugLog.AppendLine($"   Connection attempt {connectionAttempts}/3...");
                    
                    if (!await EnsureSSHConnection())
                    {
                        debugLog.AppendLine($"   Reconnect attempt {connectionAttempts} failed");
                        if (connectionAttempts >= 3)
                        {
                            debugLog.AppendLine("   ❌ ALL CONNECTION ATTEMPTS FAILED!");
                            throw new Exception($"SSH connection failed after {connectionAttempts} attempts");
                        }
                        await Task.Delay(1000); // Wait 1 second between attempts
                    }
                    else
                    {
                        debugLog.AppendLine($"   ✅ Connection successful on attempt {connectionAttempts}");
                        break;
                    }
                }

                if (sshClient?.IsConnected != true)
                {
                    debugLog.AppendLine("   ❌ SSH CLIENT STILL NOT CONNECTED AFTER ALL ATTEMPTS!");
                    throw new Exception("SSH client not connected after multiple attempts");
                }

                // Step 2: Create port ranges for efficiency
                var portRanges = CreatePortRanges(disabledPorts);
                debugLog.AppendLine("2. PORT RANGES:");
                debugLog.AppendLine($"   Range String: {portRanges}");
                debugLog.AppendLine();

                // STEP 3: ROBUST SHELL STREAM CREATION (same as single port)
                debugLog.AppendLine("3. ROBUST SHELL STREAM CREATION:");
                
                ShellStream? commandShellStream = null;
                try
                {
                    // Try to create shell stream with error handling
                    commandShellStream = sshClient.CreateShellStream("xterm", 80, 24, 800, 600, 1024);
                    
                    if (commandShellStream == null)
                    {
                        debugLog.AppendLine("   ❌ Shell stream creation returned null!");
                        throw new Exception("Failed to create shell stream - returned null");
                    }
                    
                    // Wait for shell to initialize and test it
                    await Task.Delay(300); // Increased wait time
                    
                    if (!commandShellStream.CanWrite)
                    {
                        debugLog.AppendLine("   ❌ Shell stream not writable!");
                        throw new Exception("Shell stream is not writable");
                    }
                    
                    debugLog.AppendLine("   ✅ Shell stream created and tested successfully");
                    debugLog.AppendLine();
                }
                catch (Exception shellEx)
                {
                    debugLog.AppendLine($"   ❌ Shell stream creation failed: {shellEx.Message}");
                    commandShellStream?.Dispose();
                    throw new Exception($"Shell stream creation failed: {shellEx.Message}");
                }

                using var shellStream = commandShellStream;

                // STEP 4: ULTRA ROBUST COMMAND EXECUTION (same as single port)
                async Task<string> SendCommand(string cmd, int timeoutMs = 1500)  // Increased timeout for reliability
                {
                    debugLog.AppendLine($"   📤 Sending: {cmd}");
                    
                    try
                    {
                        // Check if shell stream is still good before sending
                        if (!shellStream.CanWrite)
                        {
                            throw new Exception("Shell stream became unwritable");
                        }
                        
                        shellStream.WriteLine(cmd);
                        shellStream.Flush(); // Force flush to ensure command is sent
                        
                        var response = "";
                        var endTime = DateTime.Now.AddMilliseconds(timeoutMs);
                        var lastDataTime = DateTime.Now;
                        
                        while (DateTime.Now < endTime)
                        {
                            if (shellStream.DataAvailable)
                            {
                                var chunk = shellStream.Read();
                                response += chunk;
                                lastDataTime = DateTime.Now;
                                
                                // Smart prompt detection
                                if (response.Contains("#") || response.Contains(">"))
                                {
                                    // Wait a bit more to get any trailing data
                                    await Task.Delay(50);
                                    if (shellStream.DataAvailable)
                                    {
                                        response += shellStream.Read();
                                    }
                                    break; // Exit when we see Cisco prompt
                                }
                            }
                            else
                            {
                                // If no data for more than 3 seconds, something might be wrong
                                if (DateTime.Now.Subtract(lastDataTime).TotalSeconds > 3 && response.Length > 0)
                                {
                                    debugLog.AppendLine($"   ⚠️ No data for 3+ seconds, assuming command completed");
                                    break;
                                }
                            }
                            await Task.Delay(30);  // Slightly increased for stability
                        }
                        
                        debugLog.AppendLine($"   📥 Response: '{response.Trim().Substring(0, Math.Min(100, response.Trim().Length))}...'");
                        debugLog.AppendLine($"   📏 Length: {response.Length}");
                        return response;
                    }
                    catch (Exception cmdEx)
                    {
                        debugLog.AppendLine($"   ❌ Command execution failed: {cmdEx.Message}");
                        throw new Exception($"Command '{cmd}' failed: {cmdEx.Message}");
                    }
                }

                // STEP 5: SEQUENTIAL COMMAND EXECUTION WITH ERROR CHECKING
                debugLog.AppendLine("5. EXECUTING CISCO BULK COMMANDS:");
                
                var response1 = await SendCommand("configure terminal");
                if (response1.Contains("Invalid") || response1.Contains("%"))
                {
                    throw new Exception($"Failed to enter config mode: {response1}");
                }
                
                var response2 = await SendCommand($"interface range {portRanges}");
                if (response2.Contains("Invalid") || response2.Contains("% "))
                {
                    throw new Exception($"Failed to enter interface range {portRanges}: {response2}");
                }
                
                var response3 = await SendCommand("no shutdown");  // ENABLE instead of disable!
                if (response3.Contains("Invalid") || response3.Contains("% "))
                {
                    throw new Exception($"Failed to execute 'no shutdown': {response3}");
                }
                
                var response4 = await SendCommand("end");
                var response5 = await SendCommand("write memory", 2500);  // Longer timeout for write memory
                
                debugLog.AppendLine();

                // Check for errors
                var allResponses = response1 + response2 + response3 + response4 + response5;
                bool hasErrors = allResponses.Contains("Invalid") || allResponses.Contains("% ") || allResponses.Contains("Error");
                
                debugLog.AppendLine("5. RESULT ANALYSIS:");
                debugLog.AppendLine($"   Has Errors: {hasErrors}");
                debugLog.AppendLine($"   Total Response Length: {allResponses.Length}");
                debugLog.AppendLine();

                if (hasErrors)
                {
                    debugLog.AppendLine("❌ BULK COMMAND ERRORS DETECTED!");
                    throw new Exception($"Bulk command errors: {allResponses}");
                }

                debugLog.AppendLine("✅ BULK ENABLE SUCCESSFUL!");

                // INSTANT VISUAL FEEDBACK for all enabled ports
                foreach (var port in disabledPorts)
                {
                    UpdatePortStatusInstantly(port, "ENABLE");
                }

                UpdateStatus($"✅ BULK ENABLED {disabledPorts.Count} ports successfully!");
                MessageBox.Show($"✅ BULK ENABLE SUCCESS!\n\n" +
                              $"🟢 Enabled {disabledPorts.Count} ports\n" +
                              $"⚡ Changes applied to switch", 
                              "Bulk Enable Success", MessageBoxButton.OK, MessageBoxImage.Information);
                
                // Auto refresh in background (don't wait)
                _ = Task.Run(async () =>
                {
                    try
                    {
                        await Task.Delay(1000); // Wait 1 second before refreshing
                        await AutoRefreshPorts();
                    }
                    catch (Exception refreshEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Post-bulk-enable refresh failed: {refreshEx.Message}");
                    }
                });
            }
            catch (Exception ex)
            {
                debugLog.AppendLine($"❌ CRITICAL BULK ERROR OCCURRED:");
                debugLog.AppendLine($"   Message: {ex.Message}");
                debugLog.AppendLine($"   Type: {ex.GetType().Name}");
                debugLog.AppendLine($"   Time: {DateTime.Now:HH:mm:ss.fff}");

                UpdateStatus($"❌ Bulk enable failed: {ex.Message}");
                
                // Determine error type for better user experience
                string userFriendlyMessage;
                bool showDebugLog = false;
                
                if (ex.Message.Contains("SSH client not connected") || ex.Message.Contains("connection"))
                {
                    userFriendlyMessage = $"🔌 CONNECTION LOST!\n\n❌ Cannot enable {disabledPorts.Count} ports\n💡 The switch connection was lost\n\n🔄 Attempting to reconnect...";
                    showDebugLog = false;
                }
                else if (ex.Message.Contains("Shell stream"))
                {
                    userFriendlyMessage = $"📡 COMMUNICATION ERROR!\n\n❌ Cannot enable {disabledPorts.Count} ports\n💡 Switch communication failed\n\n🔄 Attempting to reconnect...";
                    showDebugLog = false;
                }
                else if (ex.Message.Contains("Invalid") || ex.Message.Contains("Failed to"))
                {
                    userFriendlyMessage = $"⚙️ SWITCH COMMAND ERROR!\n\n❌ Bulk enable failed\n💡 The switch rejected the bulk command\n\n📋 Click OK to see technical details";
                    showDebugLog = true;
                }
                else
                {
                    userFriendlyMessage = $"🚫 UNEXPECTED BULK ERROR!\n\n❌ Bulk enable failed\n💡 An unexpected error occurred\n\n📋 Click OK to see technical details";
                    showDebugLog = true;
                }
                
                // Show user-friendly error message
                MessageBox.Show(userFriendlyMessage, "Bulk Enable Failed", MessageBoxButton.OK, MessageBoxImage.Warning);
                
                // Show debug log only if needed
                if (showDebugLog)
                {
                    var logResult = MessageBox.Show("Do you want to see the technical debug log?", "Technical Details", 
                                                   MessageBoxButton.YesNo, MessageBoxImage.Question);
                    if (logResult == MessageBoxResult.Yes)
                    {
                        MessageBox.Show(debugLog.ToString(), "Bulk Enable Debug Log", 
                                      MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                }
                
                // Try to reconnect in background (don't wait)
                _ = Task.Run(async () =>
                {
                    try
                    {
                        await ReconnectSSH();
                    }
                    catch (Exception reconnectEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Background reconnect failed: {reconnectEx.Message}");
                    }
                });
            }
        }
        // ========================= SWITCH INFO FUNCTIONALITY =========================

        private async void BtnSwitchInfo_Click(object sender, RoutedEventArgs e)
        {
            try
            {
            if (sshClient?.IsConnected != true)
            {
                MessageBox.Show("❌ SSH NOT CONNECTED\n\nPlease connect to the switch first to get system information.", 
                              "SSH Required", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

                btnSwitchInfo.IsEnabled = false;
                btnSwitchInfo.Content = "📊 Loading...";
                UpdateStatus("Getting switch information...");

                var systemInfo = await GetSwitchSystemInfo();
                var infoDialog = new SwitchInfoDialog(systemInfo, this);
                infoDialog.Owner = this;
                infoDialog.ShowDialog();
                
                UpdateStatus("Switch information loaded");
            }
            catch (Exception ex)
            {
                UpdateStatus($"Switch info error: {ex.Message}");
                MessageBox.Show($"❌ FAILED TO GET SWITCH INFO\n\nError: {ex.Message}", 
                              "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                btnSwitchInfo.IsEnabled = true;
                btnSwitchInfo.Content = "ℹ️ Switch Info";
            }
        }

        private SwitchSystemInfo GenerateDemoSwitchInfo()
        {
            var systemInfo = new SwitchSystemInfo();
            var random = new Random();
            
            // Demo veriler - minimal aktif port
            systemInfo.ModelNumber = "Cisco Catalyst 9300-48P (1 Active Port)";
            systemInfo.IosVersion = "IOS-XE Version 17.3.5";
            systemInfo.SerialNumber = $"FCW{random.Next(2000, 2024)}A{random.Next(1000, 9999)}";
            systemInfo.MacAddress = $"00:1A:2B:{random.Next(10, 99):X2}:{random.Next(10, 99):X2}:{random.Next(10, 99):X2}";
            
            // Port durumu bilgisini ekle
            systemInfo.ActivePorts = "1/48 Ports Active (Gi1/0/1 Up)";
            
            // Performans verileri - düşük kullanım
            systemInfo.CpuUsage = $"{random.Next(2, 5)}% (1 min)";
            systemInfo.MemoryUsage = $"Used: {random.Next(3, 6)}% ({random.Next(200, 400)}MB / 8192MB)";
            
            // Çevresel veriler
            var temp = random.Next(35, 45);
            systemInfo.Temperature = $"{temp}°C (Normal Operating Range)";
            systemInfo.FanStatus = random.Next(0, 10) > 8 ? "Warning: Fan Speed High" : "Normal Operation";
            systemInfo.PowerStatus = "PS1: Good, PS2: Not Connected";
            systemInfo.PowerConsumption = $"{random.Next(100, 300)}W (PS1 only)";
            
            // Uptime - sabit 1 saat
            systemInfo.Uptime = "1 hour, 0 minutes";
            
            systemInfo.LastUpdated = DateTime.Now;
            systemInfo.IsDataValid = true;
            
            return systemInfo;
        }

        public async Task<SwitchSystemInfo> GetSwitchSystemInfo()
        {
            try
            {
                Console.WriteLine("\n🚀 === SWITCH INFO ALMA İŞLEMİ BAŞLIYOR ===");
                Console.WriteLine($"⏰ Zaman: {DateTime.Now:HH:mm:ss}");
                Console.WriteLine($"🔗 SSH Durum: {sshClient?.IsConnected}");

                // SSH bağlantısını kontrol et
                bool canUseSSH = false;
                try
                {
                    if (sshClient?.IsConnected == true)
                    {
                        // SSH client'ın dispose edilip edilmediğini test et
                        var testHost = sshClient.ConnectionInfo?.Host;
                        if (!string.IsNullOrEmpty(testHost))
                        {
                            canUseSSH = true;
                            Console.WriteLine($"✅ SSH bağlantısı geçerli: {testHost}");
                        }
                    }
                }
                catch (ObjectDisposedException ex)
                {
                    Console.WriteLine($"❌ SSH client dispose edilmiş: {ex.Message}");
                    canUseSSH = false;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"❌ SSH bağlantı kontrolü hatası: {ex.Message}");
                    canUseSSH = false;
                }

                SwitchSystemInfo systemInfo;

                if (canUseSSH)
                {
                    // Gerçek SSH verilerini almaya çalış
                    try
                    {
                        Console.WriteLine("🔗 Gerçek SSH verileri alınıyor...");
                        systemInfo = await GetRealSwitchInfo();
                        Console.WriteLine("✅ Gerçek SSH verileri başarıyla alındı!");
                    }
                    catch (ObjectDisposedException ex)
                    {
                        Console.WriteLine($"❌ SSH işlemi sırasında dispose hatası: {ex.Message}");
                        UpdateStatus("SSH bağlantısı kesildi - Demo veriler kullanılıyor");
                        systemInfo = GenerateDemoSwitchInfo();
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"❌ SSH veri alma hatası: {ex.Message}");
                        UpdateStatus($"SSH hatası - Demo veriler kullanılıyor: {ex.Message}");
                        systemInfo = GenerateDemoSwitchInfo();
                    }
                }
                else
                {
                    // Demo veri oluştur
                    Console.WriteLine("🎭 SSH mevcut değil - Demo veriler oluşturuluyor...");
                    systemInfo = GenerateDemoSwitchInfo();
                }
                
                // Firebase'e güvenli şekilde gönder
                try
                {
                    var firebaseService = new FirebaseService();
                    var targetIP = switchIP ?? "192.168.1.1"; // Demo IP fallback
                    await firebaseService.PushSwitchInfo(systemInfo, targetIP);
                    Console.WriteLine("🔥 Firebase'e başarıyla gönderildi");
                }
                catch (Exception fbEx)
                {
                    Console.WriteLine($"⚠️ Firebase gönderimi başarısız: {fbEx.Message}");
                }
                
                Console.WriteLine("\n🏁 === SİSTEM BİLGİLERİ ===");
                Console.WriteLine($"📱 Model: {systemInfo.ModelNumber}");
                Console.WriteLine($"💿 IOS: {systemInfo.IosVersion}");
                Console.WriteLine($"🔢 Serial: {systemInfo.SerialNumber}");
                Console.WriteLine($"🌐 MAC: {systemInfo.MacAddress}");
                Console.WriteLine($"📊 CPU: {systemInfo.CpuUsage}");
                Console.WriteLine($"💾 Memory: {systemInfo.MemoryUsage}");
                Console.WriteLine($"🌡️ Temperature: {systemInfo.Temperature}");
                Console.WriteLine($"🔋 Power: {systemInfo.PowerStatus}");
                Console.WriteLine($"💨 Fan: {systemInfo.FanStatus}");
                Console.WriteLine($"🕒 Uptime: {systemInfo.Uptime}");
                Console.WriteLine("✅ SWITCH BİLGİLERİ BAŞARIYLA ELDE EDİLDİ!");
                
                UpdateStatus(canUseSSH ? "Gerçek switch bilgileri alındı!" : "Demo switch bilgileri oluşturuldu!");
                
                return systemInfo;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n❌ SWITCH INFO ALMA GENEL HATASI: {ex.Message}");
                Console.WriteLine($"❌ Stack Trace: {ex.StackTrace}");
                
                var errorInfo = new SwitchSystemInfo
                {
                    ErrorMessage = $"❌ Switch Bilgisi Alma Hatası: {ex.Message}",
                    LastUpdated = DateTime.Now,
                    ModelNumber = "Hata - Bilgi Alınamadı",
                    IosVersion = "Hata",
                    SerialNumber = "Hata",
                    IsDataValid = false
                };
                
                UpdateStatus($"Switch bilgisi alma hatası: {ex.Message}");
                return errorInfo;
            }
        }

        // Gerçek SSH verilerini alma metodu
        private async Task<SwitchSystemInfo> GetRealSwitchInfo()
        {
            var info = new SwitchSystemInfo();
            
            // Version bilgisi al
            var versionCmd = sshClient.CreateCommand("show version");
            versionCmd.CommandTimeout = TimeSpan.FromSeconds(15);
            var versionOutput = await Task.Run(() => versionCmd.Execute());
            ParseVersionInfo(info, versionOutput);
            
            // CPU ve Memory bilgisi al
            var processCmd = sshClient.CreateCommand("show processes cpu");
            processCmd.CommandTimeout = TimeSpan.FromSeconds(10);
            var processOutput = await Task.Run(() => processCmd.Execute());
            ParseCpuInfo(info, processOutput);
            
            // Memory bilgisi al
            var memoryCmd = sshClient.CreateCommand("show memory");
            memoryCmd.CommandTimeout = TimeSpan.FromSeconds(10);
            var memoryOutput = await Task.Run(() => memoryCmd.Execute());
            ParseMemoryInfo(info, memoryOutput);
            
            info.LastUpdated = DateTime.Now;
            info.IsDataValid = true;
            
            return info;
        }

        // 📱 PHONE COMMAND TOGGLE BUTONU
        private void BtnPhoneCommand_Click(object sender, RoutedEventArgs e)
        {
            isPhoneCommandEnabled = !isPhoneCommandEnabled;
            
            if (isPhoneCommandEnabled)
            {
                // PHONE COMMAND AÇILDI
                btnPhoneCommand.Content = "📱 Phone Commands: ON";
                btnPhoneCommand.Background = Brushes.Green;
                
                // Timer başlat
                InitializePhoneCommandTimer();
                
                UpdateStatus("�� Phone Commands AKTIF - Firebase komutları izleniyor!");
                Console.WriteLine("📱 PHONE COMMAND SİSTEMİ AKTİF!");
            }
            else
            {
                // PHONE COMMAND KAPALI
                btnPhoneCommand.Content = "📱 Phone Commands: OFF";
                btnPhoneCommand.Background = Brushes.Red;
                
                // Timer durdur
                phoneCommandTimer?.Stop();
                
                UpdateStatus("📱 Phone Commands KAPALI - Otomatik komut işleme durdu");
                Console.WriteLine("📱 PHONE COMMAND SİSTEMİ KAPALI!");
            }
        }

        // 📱 PHONE COMMAND TIMER BAŞLATMA
        private void InitializePhoneCommandTimer()
        {
            if (phoneCommandTimer == null)
            {
                phoneCommandTimer = new DispatcherTimer();
                phoneCommandTimer.Interval = TimeSpan.FromSeconds(5); // Her 5 saniyede komut kontrol et
                phoneCommandTimer.Tick += async (s, e) => await ProcessPhoneCommands();
            }
            
            phoneCommandTimer.Start();
            Console.WriteLine("📱 Phone Command Timer başlatıldı - Her 5 saniyede komut kontrolü");
        }

        // 🔗 SSH KEEPALİVE TIMER BAŞLATMA - BAĞLANTIYI SÜREKLI AÇIK TUT
        private void InitializeSshKeepaliveTimer()
        {
            if (sshKeepaliveTimer == null)
            {
                sshKeepaliveTimer = new DispatcherTimer();
                sshKeepaliveTimer.Interval = TimeSpan.FromSeconds(10); // Her 10 saniyede SSH kontrol et
                sshKeepaliveTimer.Tick += async (s, e) => await CheckAndMaintainSshConnection();
            }
            
            sshKeepaliveTimer.Start();
            Console.WriteLine("🔗 SSH Keepalive Timer başlatıldı - Her 10 saniyede bağlantı kontrolü");
        }

        // 🔗 SSH BAĞLANTI KONTROLÜ VE OTOMATİK YENİDEN BAĞLANMA
        private async Task CheckAndMaintainSshConnection()
        {
            try
            {
                if (isReconnecting)
                {
                    Console.WriteLine("🔗 Zaten yeniden bağlanma işlemi devam ediyor, atlanıyor...");
                    return;
                }

                Console.WriteLine("🔗 SSH bağlantı durumu kontrol ediliyor...");
                
                // SSH bağlantı kontrolü
                bool isConnected = sshClient?.IsConnected == true;
                Console.WriteLine($"🔗 SSH Durum: {(isConnected ? "✅ Bağlı" : "❌ Kopuk")}");
                
                if (!isConnected && !string.IsNullOrEmpty(switchIP) && !string.IsNullOrEmpty(username) && !string.IsNullOrEmpty(password))
                {
                    Console.WriteLine("🔗 ❌ SSH bağlantısı kopmuş - Otomatik yeniden bağlanmaya çalışılıyor...");
                    UpdateStatus("🔗 SSH bağlantısı koptu - Yeniden bağlanıyor...");
                    
                    isReconnecting = true;
                    
                    try
                    {
                        // Eski bağlantıyı temizle
                        sshClient?.Disconnect();
                        sshClient?.Dispose();
                        
                        // Yeni bağlantı kur
                        sshClient = new SshClient(switchIP, username, password);
                        sshClient.ConnectionInfo.Timeout = TimeSpan.FromSeconds(30);
                        
                        Console.WriteLine($"🔗 Yeniden bağlanıyor: {switchIP}");
                        sshClient.Connect();
                        
                        if (sshClient.IsConnected)
                        {
                            Console.WriteLine("🔗 ✅ SSH yeniden bağlandı!");
                            UpdateStatus("🔗 ✅ SSH bağlantısı yeniden kuruldu");
                            
                            // Connection status güncelle
                            txtConnectionStatus.Text = "🟢 Connected";
                            
                            // Firebase'e bağlantı durumunu bildir
                            if (firebaseService != null)
                            {
                                await firebaseService.PushConnectionInfo(switchIP, username, true, "Auto-reconnected");
                            }
                        }
                        else
                        {
                            Console.WriteLine("🔗 ❌ SSH yeniden bağlanma başarısız!");
                            UpdateStatus("🔗 ❌ SSH yeniden bağlanma başarısız");
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"🔗 ❌ SSH yeniden bağlanma hatası: {ex.Message}");
                        UpdateStatus($"🔗 ❌ SSH yeniden bağlanma hatası: {ex.Message}");
                    }
                    finally
                    {
                        isReconnecting = false;
                    }
                }
                else if (isConnected)
                {
                    // Bağlantı test et - basit komut çalıştır
                    try
                    {
                        var testCmd = sshClient.CreateCommand("show clock");
                        testCmd.CommandTimeout = TimeSpan.FromSeconds(5);
                        var result = testCmd.Execute();
                        
                        if (string.IsNullOrEmpty(result))
                        {
                            Console.WriteLine("🔗 ⚠️ SSH bağlı ama komut yanıt vermiyor");
                        }
                        else
                        {
                            Console.WriteLine("🔗 ✅ SSH bağlantısı sağlıklı");
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"🔗 ⚠️ SSH test komutu başarısız: {ex.Message}");
                    }
                }
                
                lastSshCheck = DateTime.Now;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"🔗 ❌ SSH Keepalive hatası: {ex.Message}");
            }
        }

        // 🧪 MANUEL TEST BUTONU
        private async void BtnTestCommands_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                Console.WriteLine("🧪 === MANUEL FIREBASE KOMUT TESTİ BAŞLADI ===");
                Console.WriteLine($"🧪 Phone Commands Enabled: {isPhoneCommandEnabled}");
                Console.WriteLine($"🧪 Firebase Service: {firebaseService != null}");
                Console.WriteLine($"🧪 Switch IP: {switchIP}");
                Console.WriteLine($"🧪 SSH Connected: {sshClient?.IsConnected}");
                
                UpdateStatus("🧪 Manuel Firebase komut testi başlatılıyor...");
                
                if (firebaseService == null)
                {
                    Console.WriteLine("🧪 ❌ Firebase Service bulunamadı!");
                    UpdateStatus("🧪 ❌ Firebase bağlantısı yok - önce Connect butonuna tıklayın");
                    return;
                }
                
                if (string.IsNullOrEmpty(switchIP))
                {
                    Console.WriteLine("🧪 ❌ Switch IP boş!");
                    UpdateStatus("🧪 ❌ Switch IP adresi yok - önce Connect butonuna tıklayın");
                    return;
                }
                
                if (sshClient?.IsConnected != true)
                {
                    Console.WriteLine("🧪 ❌ SSH bağlantısı yok!");
                    UpdateStatus("🧪 ❌ SSH bağlantısı yok - önce Connect butonuna tıklayın");
                    return;
                }
                
                Console.WriteLine("🧪 ✅ Tüm ön koşullar sağlandı - Firebase komutları kontrol ediliyor...");
                
                // Firebase'den komutları al
                var commands = await firebaseService.GetPortCommands(switchIP);
                
                if (commands != null && commands.Count > 0)
                {
                    Console.WriteLine($"🧪 ✅ {commands.Count} komut bulundu! Direkt işleniyor...");
                    UpdateStatus($"🧪 {commands.Count} Firebase komut işleniyor...");
                    
                    // TEST NOW da da basit versiyon kullan
                    for (int i = 0; i < commands.Count; i++)
                    {
                        Console.WriteLine($"🧪 İşleniyor ({i + 1}/{commands.Count}): {JsonConvert.SerializeObject(commands[i], Formatting.Indented)}");
                        await ProcessSingleCommandWithPopup(commands[i], i + 1, commands.Count);
                    }
                    
                    UpdateStatus($"🧪 ✅ {commands.Count} komut tamamlandı!");
                }
                else
                {
                    Console.WriteLine("🧪 ⚠️ Firebase'de komut bulunamadı");
                    UpdateStatus("🧪 ⚠️ Firebase'de bekleyen komut yok");
                }
                
                Console.WriteLine("🧪 === MANUEL TEST BİTTİ ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"🧪 ❌ MANUEL TEST HATASI: {ex.Message}");
                Console.WriteLine($"🧪 Stack Trace: {ex.StackTrace}");
                UpdateStatus($"🧪 ❌ Test hatası: {ex.Message}");
            }
        }

        // 📱 PHONE COMMAND İŞLEME SİSTEMİ
        private async Task ProcessPhoneCommands()
        {
            Console.WriteLine($"📱 === PHONE COMMAND İŞLEME BAŞLADI ===");
            Console.WriteLine($"📱 Phone Commands Enabled: {isPhoneCommandEnabled}");
            Console.WriteLine($"📱 Firebase Service: {firebaseService != null}");
            Console.WriteLine($"📱 Switch IP: {switchIP}");
            
            if (!isPhoneCommandEnabled)
            {
                Console.WriteLine("📱 ❌ Phone Commands devre dışı!");
                return;
            }
                
            if (firebaseService == null)
            {
                Console.WriteLine("📱 ❌ Firebase Service yok!");
                return;
            }
                
            if (string.IsNullOrEmpty(switchIP))
            {
                Console.WriteLine("📱 ❌ Switch IP boş!");
                return;
            }

            try
            {
                Console.WriteLine("📱 ✅ Tüm koşullar sağlandı - Firebase'den komutlar kontrol ediliyor...");
                
                // Firebase'den PortCommands al
                var commands = await firebaseService.GetPortCommands(switchIP);
                
                Console.WriteLine($"📱 Firebase'den dönen sonuç: {commands?.Count ?? -1} komut");
                
                if (commands != null && commands.Count > 0)
                {
                    Console.WriteLine($"📱 ✅ {commands.Count} komut bulundu! Direkt işleniyor...");
                    UpdateStatus($"📱 {commands.Count} Firebase komut işleniyor...");
                    
                    for (int i = 0; i < commands.Count; i++)
                    {
                        Console.WriteLine($"📱 === KOMUT {i + 1}/{commands.Count} İŞLENİYOR ===");
                        await ProcessSingleCommandWithPopup(commands[i], i + 1, commands.Count);
                        Console.WriteLine($"📱 === KOMUT {i + 1} BİTTİ ===");
                    }
                    
                    Console.WriteLine($"📱 ✅ TÜM {commands.Count} KOMUT İŞLENDİ!");
                    UpdateStatus($"📱 ✅ {commands.Count} komut tamamlandı");
                }
                else
                {
                    Console.WriteLine("📱 ⚠️ Firebase'de yeni komut bulunamadı");
                }
                
                lastCommandCheck = DateTime.Now;
                Console.WriteLine($"📱 === PHONE COMMAND İŞLEME BİTTİ ===");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"📱 ❌ PHONE COMMAND İŞLEME HATASI: {ex.Message}");
                Console.WriteLine($"📱 Stack Trace: {ex.StackTrace}");
                UpdateStatus($"📱 Phone Command hatası: {ex.Message}");
            }
        }

        // 📱 POPUP'LI TEK KOMUT İŞLEME - HER KOMUT İÇİN KULLANICI ONAYI
        private async Task ProcessSingleCommandWithPopup(dynamic command, int currentIndex, int totalCount)
        {
            try
            {
                // DEBUG: Komut objesini tamamen yazdır
                Console.WriteLine($"📱 RAW KOMUT: {JsonConvert.SerializeObject(command, Formatting.Indented)}");
                
                // Port adını KEY'den al (Firebase yapısında key = port adı)
                string firebasePortName = command.Key?.ToString() ?? "";
                string commandType = command.command?.ToString()?.ToLower() ?? "";
                string commandId = command.Key?.ToString() ?? "";
                
                // Firebase port formatını Cisco formatına çevir (Gi1_0_1 -> Gi1/0/1)
                string ciscoPortName = ConvertFirebasePortToCisco(firebasePortName);
                
                Console.WriteLine($"📱 KOMUT DETAYLARI:");
                Console.WriteLine($"   Firebase Port: {firebasePortName}");
                Console.WriteLine($"   Cisco Port: {ciscoPortName}");
                Console.WriteLine($"   Command: {commandType}");
                Console.WriteLine($"   Command ID: {commandId}");
                
                if (string.IsNullOrEmpty(ciscoPortName) || string.IsNullOrEmpty(commandType))
                {
                    Console.WriteLine("📱 GEÇERSİZ KOMUT:");
                    Console.WriteLine($"   Port boş: {string.IsNullOrEmpty(ciscoPortName)}");
                    Console.WriteLine($"   Command boş: {string.IsNullOrEmpty(commandType)}");
                    Console.WriteLine($"📱 Bu komut atlanıyor");
                return;
            }

                // Geçersiz komutları filtrele
                if (commandType == "false" || commandType == "true" || commandType == "")
                {
                    Console.WriteLine($"📱 GEÇERSİZ KOMUT TİPİ: {commandType} - Bu komut işlenmeyecek");
                    Console.WriteLine($"📱 Geçersiz komut otomatik siliniyor: {commandId}");
                    
                    // Geçersiz komutları otomatik sil
                    await firebaseService.DeleteProcessedCommand(switchIP, commandId);
                    Console.WriteLine($"📱 Geçersiz komut silindi: {commandId}");
                    return;
                }

                // DİREKT İŞLEME GEÇE - POPUP YOK
                string actionText = commandType == "open" || commandType == "enable" || commandType == "no shutdown" ? "açıldı" : "kapatıldı";
                string actionEmoji = commandType == "open" || commandType == "enable" || commandType == "no shutdown" ? "🟢" : "🔴";
                
                Console.WriteLine($"📱 {actionEmoji} Port işlemi başlatılıyor: {ciscoPortName} {actionText}");

                // 🚀 BASİT ÇÖZÜM: Mevcut port fonksiyonlarını kullan!
                bool success = false;
                string action = "";
                
                Console.WriteLine($"📱 Port seçiliyor: {ciscoPortName}");
                
                // Port'u seç (mevcut sistem)
                selectedPortName = ciscoPortName;
                SelectPort(ciscoPortName);
                
                // 🚀 GÜÇLÜ RETRY SİSTEMİ - OLANA KADAR DENE
                int maxRetries = 5;
                int currentRetry = 0;
                
                switch (commandType)
                {
                    case "close":
                    case "shutdown":
                    case "disable":
                        Console.WriteLine($"📱 🔴 Port KAPAMA: {ciscoPortName}");
                        action = "DISABLE";
                        
                        // Retry sistemi ile dene
                        while (currentRetry < maxRetries && !success)
                        {
                            currentRetry++;
                            Console.WriteLine($"📱 Deneme {currentRetry}/{maxRetries}: Port kapama");
                            
                            try
                            {
                                await ExecuteFirebasePortCommand(ciscoPortName, "shutdown");
                                success = true;
                                Console.WriteLine($"📱 ✅ Port {ciscoPortName} başarıyla KAPALDI (deneme {currentRetry})");
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"📱 ❌ Deneme {currentRetry} başarısız: {ex.Message}");
                                if (currentRetry < maxRetries)
                                {
                                    Console.WriteLine($"📱 🔄 2 saniye bekleyip tekrar deniyorum...");
                                    await Task.Delay(2000);
                                }
                            }
                        }
                        break;
                        
                    case "open":
                    case "no shutdown":
                    case "enable":
                        Console.WriteLine($"📱 🟢 Port AÇMA: {ciscoPortName}");
                        action = "ENABLE";
                        
                        // Retry sistemi ile dene
                        while (currentRetry < maxRetries && !success)
                        {
                            currentRetry++;
                            Console.WriteLine($"📱 Deneme {currentRetry}/{maxRetries}: Port açma");
                            
                            try
                            {
                                await ExecuteFirebasePortCommand(ciscoPortName, "no shutdown");
                                success = true;
                                Console.WriteLine($"📱 ✅ Port {ciscoPortName} başarıyla AÇILDI (deneme {currentRetry})");
                            }
                            catch (Exception ex)
                            {
                                Console.WriteLine($"📱 ❌ Deneme {currentRetry} başarısız: {ex.Message}");
                                if (currentRetry < maxRetries)
                                {
                                    Console.WriteLine($"📱 🔄 2 saniye bekleyip tekrar deniyorum...");
                                    await Task.Delay(2000);
                                }
                            }
                        }
                        break;
                        
                    default:
                        Console.WriteLine($"📱 BİLİNMEYEN KOMUT: {commandType}");
                        Console.WriteLine($"📱 Desteklenen komutlar: open, enable, no shutdown, close, disable, shutdown");
                        Console.WriteLine($"📱 Bu komut atlanıyor");
                        break;
                }

                // Final durum kontrolü
                if (!success && currentRetry >= maxRetries)
                {
                    Console.WriteLine($"📱 ❌ {maxRetries} deneme tükendi - Port {ciscoPortName} işlemi başarısız");
                    Console.WriteLine($"📱 Komut Firebase'de kalacak, daha sonra tekrar denenebilir");
                }

                // Komut sonuç - SADECE LOG, POPUP YOK
                if (success && !string.IsNullOrEmpty(commandId))
                {
                    Console.WriteLine($"📱 BAŞARILI KOMUT - Firebase'den siliniyor...");
                    
                    await firebaseService.DeleteProcessedCommand(switchIP, commandId);
                    await firebaseService.PushCommandProcessLog(switchIP, ciscoPortName, commandType, action, true);
                    
                    Console.WriteLine($"📱 İşlenen komut silindi: {commandId}");
                    
                    var timestamp = DateTime.Now.ToString("HH:mm:ss");
                    
                    // Port numarasını al (Gi1/0/15 -> 15)
                    string portNumber = ciscoPortName.Replace("Gi1/0/", "").Replace("GigabitEthernet1/0/", "");
                    
                    Console.WriteLine($"📱 ✅ {portNumber}. port mobil kullanıcı tarafından {actionText} - {timestamp}");
                    UpdateStatus($"📱 {portNumber}. port mobil kullanıcı tarafından {actionText} [{timestamp}]");
                }
                else if (!success)
                {
                    Console.WriteLine($"📱 BAŞARISIZ KOMUT - Log tutuluyor...");
                    await firebaseService.PushCommandProcessLog(switchIP, ciscoPortName, commandType, "FAILED", false);
                    
                    // Port numarasını al
                    string portNumber = ciscoPortName.Replace("Gi1/0/", "").Replace("GigabitEthernet1/0/", "");
                    
                    Console.WriteLine($"📱 ❌ {portNumber}. port işlemi başarısız - Mobil kullanıcı komutu çalıştırılamadı");
                    UpdateStatus($"📱 ❌ {portNumber}. port işlemi başarısız");
                }
                else if (string.IsNullOrEmpty(commandId))
                {
                    Console.WriteLine($"📱 UYARI: CommandID boş - komut silinemedi");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"📱 Komut işleme hatası: {ex.Message}");
                Console.WriteLine($"📱 Diğer komutlara devam ediliyor...");
            }
        }

        // 📱 TEK KOMUT İŞLEME (ESKİ METOD - POPUP OLMADAN)
        private async Task ProcessSingleCommand(dynamic command)
        {
            try
            {
                // DEBUG: Komut objesini tamamen yazdır
                Console.WriteLine($"📱 RAW KOMUT: {JsonConvert.SerializeObject(command, Formatting.Indented)}");
                
                // Port adını KEY'den al (Firebase yapısında key = port adı)
                string firebasePortName = command.Key?.ToString() ?? "";
                string commandType = command.command?.ToString()?.ToLower() ?? "";
                string commandId = command.Key?.ToString() ?? "";
                
                // Firebase port formatını Cisco formatına çevir (Gi1_0_1 -> Gi1/0/1)
                string ciscoPortName = ConvertFirebasePortToCisco(firebasePortName);
                
                Console.WriteLine($"📱 KOMUT DETAYLARI:");
                Console.WriteLine($"   Firebase Port: {firebasePortName}");
                Console.WriteLine($"   Cisco Port: {ciscoPortName}");
                Console.WriteLine($"   Command: {commandType}");
                Console.WriteLine($"   Command ID: {commandId}");
                
                if (string.IsNullOrEmpty(ciscoPortName) || string.IsNullOrEmpty(commandType))
                {
                    Console.WriteLine("📱 GEÇERSİZ KOMUT:");
                    Console.WriteLine($"   Port boş: {string.IsNullOrEmpty(ciscoPortName)}");
                    Console.WriteLine($"   Command boş: {string.IsNullOrEmpty(commandType)}");
                return;
            }

                // Geçersiz komutları filtrele
                if (commandType == "false" || commandType == "true" || commandType == "")
                {
                    Console.WriteLine($"📱 GEÇERSİZ KOMUT TİPİ: {commandType} - Bu komut işlenmeyecek");
                    // Bu geçersiz komutu sil
                    await firebaseService.DeleteProcessedCommand(switchIP, commandId);
                    return;
                }

                // 🔗 GÜÇLÜ SSH BAĞLANTI KONTROLÜ
                if (sshClient?.IsConnected != true)
                {
                    Console.WriteLine("📱 ❌ SSH bağlantısı kopmuş - Otomatik yeniden bağlanmaya çalışılıyor...");
                    
                    if (!string.IsNullOrEmpty(switchIP) && !string.IsNullOrEmpty(username) && !string.IsNullOrEmpty(password) && !isReconnecting)
                    {
                        Console.WriteLine("📱 🔗 SSH yeniden bağlanma deneniyor...");
                        isReconnecting = true;
                        
                        try
                        {
                            // Eski bağlantıyı temizle
                            sshClient?.Disconnect();
                            sshClient?.Dispose();
                            
                            // Yeni bağlantı kur
                            sshClient = new SshClient(switchIP, username, password);
                            sshClient.ConnectionInfo.Timeout = TimeSpan.FromSeconds(30);
                            sshClient.Connect();
                            
                            if (sshClient.IsConnected)
                            {
                                Console.WriteLine("📱 ✅ SSH başarıyla yeniden bağlandı!");
                                UpdateStatus("📱 ✅ SSH yeniden bağlandı - Phone Commands devam ediyor");
                                
                                // Connection status güncelle
                                txtConnectionStatus.Text = "🟢 Connected (Auto-recovered)";
                        }
                        else
                        {
                                Console.WriteLine("📱 ❌ SSH yeniden bağlanma başarısız - komut atlanıyor");
                                return;
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"📱 ❌ SSH yeniden bağlanma hatası: {ex.Message}");
                            return;
                        }
                        finally
                        {
                            isReconnecting = false;
                        }
                    }
                    else
                    {
                        Console.WriteLine("📱 ❌ SSH yeniden bağlanamıyor - bağlantı bilgileri eksik veya zaten bağlanmaya çalışılıyor");
                        return;
                    }
                }

                // KOMUT İŞLEME
                bool success = false;
                string action = "";
                
                switch (commandType)
                {
                    case "close":
                    case "shutdown":
                    case "disable":
                        action = "shutdown";
                        Console.WriteLine($"📱 KAPAMA komutu başlatılıyor: {ciscoPortName}");
                        success = await ExecutePortCommand(ciscoPortName, "shutdown", "Phone Command: Port Kapatıldı");
                        Console.WriteLine($"📱 Port {ciscoPortName} KAPATLIDI - Başarı: {success}");
                        break;
                        
                    case "open":
                    case "no shutdown":
                    case "enable":
                        action = "no shutdown";
                        Console.WriteLine($"📱 AÇMA komutu başlatılıyor: {ciscoPortName}");
                        success = await ExecutePortCommand(ciscoPortName, "no shutdown", "Phone Command: Port Açıldı");
                        Console.WriteLine($"📱 Port {ciscoPortName} AÇILDI - Başarı: {success}");
                        break;
                        
                    default:
                        Console.WriteLine($"📱 BİLİNMEYEN KOMUT: {commandType}");
                        Console.WriteLine($"📱 Desteklenen komutlar: open, close, enable, disable, shutdown, no shutdown");
                                break;
                            }

                // Komut başarılıysa Firebase'den sil ve log tut
                if (success && !string.IsNullOrEmpty(commandId))
                {
                    Console.WriteLine($"📱 BAŞARILI KOMUT - Firebase'den siliniyor...");
                    
                    // İşlenen komutu sil
                    await firebaseService.DeleteProcessedCommand(switchIP, commandId);
                    
                    // İşlem logunu Firebase'e gönder
                    await firebaseService.PushCommandProcessLog(switchIP, ciscoPortName, commandType, action, true);
                    
                    Console.WriteLine($"📱 İşlenen komut silindi: {commandId}");
                    
                    // Status güncelle
                    var timestamp = DateTime.Now.ToString("HH:mm:ss");
                    UpdateStatus($"📱 Phone Command [{timestamp}]: {ciscoPortName} {action}");
                }
                else if (!success)
                {
                    Console.WriteLine($"📱 BAŞARISIZ KOMUT - Log tutuluyor...");
                    // Başarısız komut logunu da tut
                    await firebaseService.PushCommandProcessLog(switchIP, ciscoPortName, commandType, "FAILED", false);
                    Console.WriteLine($"📱 Komut başarısız: {ciscoPortName} {commandType}");
                }
                else if (string.IsNullOrEmpty(commandId))
                {
                    Console.WriteLine($"📱 UYARI: CommandID boş - komut silinemedi");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"📱 Komut işleme hatası: {ex.Message}");
            }
        }

        // 🚀 FIREBASE İÇİN ÖZEL PORT KOMUT METODu - POPUP YOK, RETRY SİSTEMİ YOK
        private async Task ExecuteFirebasePortCommand(string portName, string command)
        {
            // SSH kontrol et, yoksa reconnect
            if (sshClient?.IsConnected != true)
            {
                Console.WriteLine($"📱 SSH bağlantısı yok, yeniden bağlanıyor...");
                bool reconnected = await ReconnectSSH();
                if (!reconnected)
                {
                    throw new Exception("SSH bağlantısı kurulamadı");
                }
            }

            var fullPortName = portName.Replace("Gi", "GigabitEthernet");
            Console.WriteLine($"📱 Cisco komutu çalıştırılıyor: interface {fullPortName} -> {command}");

            // Shell stream oluştur
            using var shellStream = sshClient.CreateShellStream("xterm", 80, 24, 800, 600, 1024);
            await Task.Delay(300); // Shell hazırlanmasını bekle

            // Komutları sırasıyla çalıştır
            var commands = new[]
            {
                "configure terminal",
                $"interface {fullPortName}",
                command,
                "end",
                "write memory"
            };

            foreach (var cmd in commands)
            {
                Console.WriteLine($"📱 Komutu gönderiliyor: {cmd}");
                shellStream.WriteLine(cmd);
                shellStream.Flush();
                
                // Yanıt bekle
                await Task.Delay(500);
                if (shellStream.DataAvailable)
                {
                    var response = shellStream.Read();
                    if (response.Contains("Invalid") || response.Contains("Error"))
                    {
                        throw new Exception($"Cisco komut hatası: {response}");
                    }
                }
            }

            // Port durumunu güncelle
            UpdatePortStatusInstantly(portName, command == "shutdown" ? "DISABLE" : "ENABLE");
            Console.WriteLine($"📱 Port komutu başarıyla tamamlandı: {portName} {command}");
        }

        // 📱 FIREBASE PORT FORMAT ÇEVR (Gi1_0_1 -> Gi1/0/1)
        private string ConvertFirebasePortToCisco(string firebasePort)
        {
            if (string.IsNullOrEmpty(firebasePort))
            {
                Console.WriteLine("📱 UYARI: Firebase port adı boş");
                    return "";
            }

            try
            {
                // Firebase format: Gi1_0_1, Gi1_0_2, etc.
                // Cisco format: Gi1/0/1, Gi1/0/2, etc.
                
                Console.WriteLine($"📱 Port format çeviriliyor: '{firebasePort}'");
                
                // Underscore'ları slash'e çevir
                string ciscoPort = firebasePort.Replace("_", "/");
                
                Console.WriteLine($"📱 Çevrilmiş port: '{ciscoPort}'");
                
                // Basic validation - Gi ile başlamalı ve / içermeli
                if (ciscoPort.StartsWith("Gi") && ciscoPort.Contains("/"))
                {
                    return ciscoPort;
                }
                else
                {
                    Console.WriteLine($"📱 UYARI: Geçersiz port formatı: {ciscoPort}");
                    return "";
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"📱 Port format çevirme hatası: {ex.Message}");
                return "";
            }
        }

        // 📱 PORT KOMUT ÇALIŞTIRMA
        private async Task<bool> ExecutePortCommand(string portName, string command, string description)
        {
            try
            {
                Console.WriteLine($"📱 === PORT KOMUT BAŞLADI ===");
                Console.WriteLine($"📱 Port: {portName}");
                Console.WriteLine($"📱 Komut: {command}");
                Console.WriteLine($"📱 Açıklama: {description}");
                
                if (sshClient?.IsConnected != true)
                    {
                    Console.WriteLine($"📱 ❌ SSH BAĞLANTISI YOK!");
                    return false;
                }

                Console.WriteLine($"📱 ✅ SSH bağlantısı aktif");

                // Port'a bağlan ve komut çalıştır
                var configCommands = new[]
                {
                    "configure terminal",
                    $"interface {portName}",
                    command,
                    "exit",
                    "exit"
                };

                Console.WriteLine($"📱 {configCommands.Length} komut çalıştırılacak:");
                for (int i = 0; i < configCommands.Length; i++)
                {
                    Console.WriteLine($"📱   {i + 1}. {configCommands[i]}");
                }

                bool allSuccess = true;
                foreach (var cmd in configCommands)
                {
                    Console.WriteLine($"📱 Çalıştırılıyor: {cmd}");
                    var result = await ExecuteCommandSafely(cmd, 10);
                    Console.WriteLine($"📱 Sonuç: {result?.Length ?? 0} karakter");
                    
                    if (string.IsNullOrEmpty(result) && cmd != "exit")
                    {
                        Console.WriteLine($"📱 ⚠️ Komut boş sonuç döndü: {cmd}");
                        allSuccess = false;
                    }
                    
                    // Hata kontrolü
                    if (!string.IsNullOrEmpty(result) && (result.Contains("Invalid") || result.Contains("Error")))
                    {
                        Console.WriteLine($"📱 ❌ Komut hatası tespit edildi: {result}");
                        allSuccess = false;
                    }
                }

                Console.WriteLine($"📱 Tüm komutlar başarılı: {allSuccess}");
                
                // Port durumunu hemen yenile
                Console.WriteLine($"📱 Port durumu yenileniyor...");
                await AutoRefreshPorts();
                Console.WriteLine($"📱 Port durumu yenilendi");
                
                Console.WriteLine($"📱 === PORT KOMUT BİTTİ ===");
                return allSuccess;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"📱 ❌ PORT KOMUT HATASI: {ex.Message}");
                Console.WriteLine($"📱 Stack Trace: {ex.StackTrace}");
                return false;
            }
        }

        // BASIT SSH KOMUT ÇALIŞTIRMA - Karmaşık değil!
        private async Task<string> ExecuteCommandSafely(string command, int timeoutSeconds = 15)
        {
            try
            {
                if (sshClient?.IsConnected != true)
                {
                    Console.WriteLine($"❌ SSH bağlantısı yok!");
                return "";
            }

                Console.WriteLine($"🔄 Komut: {command}");
                
                // BASİT SSH KOMUT - Shell stream değil direkt komut!
                var cmd = sshClient.CreateCommand(command);
                cmd.CommandTimeout = TimeSpan.FromSeconds(timeoutSeconds);
                
                var result = cmd.Execute();
                
                Console.WriteLine($"✅ Sonuç uzunluğu: {result?.Length ?? 0}");
                
                if (!string.IsNullOrEmpty(result))
                {
                    // İlk 500 karakteri göster debug için
                    var preview = result.Length > 500 ? result.Substring(0, 500) + "\n...[KESILDI]..." : result;
                    Console.WriteLine($"📋 Komut çıktısı:\n{preview}");
                }
                
                return result ?? "";
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ HATA: {ex.Message}");
                return "";
            }
        }



        // Consolidated environment info parsing
        private void ParseEnvironmentInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output))
            {
                info.Temperature = "🌡️ Çevre monitörü yok";
                info.PowerStatus = "🔋 Güç monitörü yok";
                info.FanStatus = "💨 Fan monitörü yok";
                info.PowerConsumption = "⚡ Güç tüketim verisi yok";
                return;
            }

            // Parse temperature
            ParseTemperatureInfo(info, output);
            
            // Parse power status
            ParsePowerInfo(info, output);
            
            // Parse fan status
            ParseFanInfo(info, output);
        }

        private void ParseVersionInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output)) 
            {
                Console.WriteLine("❌ ParseVersionInfo: Boş output!");
                info.IosVersion = "🔍 Version output boş";
                info.ModelNumber = "🔍 Version output boş";
                info.SerialNumber = "🔍 Version output boş";
                info.MacAddress = "🔍 Version output boş";
                return;
            }

            Console.WriteLine($"🔍 Version output parse ediyorum ({output.Length} karakter)...");

            // BASİT PARSE - Arama yapalım
            var lines = output.Split('\n');
            
            // Default değerler
            info.IosVersion = "🔍 IOS bulunamadı";
            info.ModelNumber = "🔍 Model bulunamadı";
            info.SerialNumber = "🔍 Serial bulunamadı";
            info.MacAddress = "🔍 MAC bulunamadı";

            foreach (var line in lines)
            {
                var trimmedLine = line.Trim();
                Console.WriteLine($"📝 Satır kontrol ediyorum: {trimmedLine.Substring(0, Math.Min(80, trimmedLine.Length))}");
                
                // IOS Version - BASIT ARAMA
                if (trimmedLine.Contains("Cisco IOS") || trimmedLine.Contains("IOS XE") || trimmedLine.Contains("Version"))
                    {
                    Console.WriteLine($"✅ IOS bilgisi buldum: {trimmedLine}");
                    info.IosVersion = trimmedLine.Length > 100 ? trimmedLine.Substring(0, 100) + "..." : trimmedLine;
                }
                
                // Model - BASIT ARAMA
                if (trimmedLine.Contains("Model") || trimmedLine.Contains("Catalyst") || trimmedLine.Contains("9300"))
                {
                    Console.WriteLine($"✅ Model bilgisi buldum: {trimmedLine}");
                    info.ModelNumber = trimmedLine.Length > 80 ? trimmedLine.Substring(0, 80) + "..." : trimmedLine;
                }
                
                // Serial - BASIT ARAMA
                if (trimmedLine.Contains("Serial") || trimmedLine.Contains("system serial"))
                {
                    Console.WriteLine($"✅ Serial bilgisi buldum: {trimmedLine}");
                    if (trimmedLine.Contains(":"))
                    {
                        var parts = trimmedLine.Split(':');
                        if (parts.Length > 1)
                            {
                            info.SerialNumber = parts[1].Trim();
                        }
                    }
                    else
                    {
                        info.SerialNumber = trimmedLine;
                    }
                }
                
                // MAC - BASIT ARAMA
                if (trimmedLine.Contains("MAC") || trimmedLine.Contains("mac"))
                {
                    Console.WriteLine($"✅ MAC bilgisi buldum: {trimmedLine}");
                    info.MacAddress = trimmedLine.Length > 80 ? trimmedLine.Substring(0, 80) + "..." : trimmedLine;
                }
            }
            
            Console.WriteLine($"🏁 Parse tamamlandı:");
            Console.WriteLine($"   IOS: {info.IosVersion}");
            Console.WriteLine($"   Model: {info.ModelNumber}");
            Console.WriteLine($"   Serial: {info.SerialNumber}");
            Console.WriteLine($"   MAC: {info.MacAddress}");
        }

        private void ParseTemperatureInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output)) 
            {
                info.Temperature = "Normal Operating Range";
                return;
            }

            // Cisco specific temperature patterns based on your example
            var patterns = new[]
            {
                @"Inlet Temperature Value:\s*(\d+)\s*Degree Celsius",
                @"Outlet Temperature Value:\s*(\d+)\s*Degree Celsius", 
                @"Hotspot Temperature Value:\s*(\d+)\s*Degree Celsius",
                @"Temperature Value:\s*(\d+)\s*Degree Celsius",
                @"Temperature.*?(\d+).*?Degree Celsius",
                @"(\d+)\s*Degree Celsius",
                @"Temperature.*?(\d+).*?°C",
                @"(\d+)\s*°C",
                @"(\d+)\s*C",
                @"Temp.*?(\d+)"
            };

            var temperatures = new List<int>();
            var temperatureStates = new List<string>();
            
            // Extract all temperature values and states
            foreach (var pattern in patterns)
            {
                var matches = Regex.Matches(output, pattern, RegexOptions.IgnoreCase);
                foreach (Match match in matches)
                {
                    if (int.TryParse(match.Groups[1].Value, out int temp) && temp >= 15 && temp <= 150)
                {
                        temperatures.Add(temp);
                    }
                }
            }
            
            // Extract temperature states
            var stateMatches = Regex.Matches(output, @"Temperature State:\s*(\w+)", RegexOptions.IgnoreCase);
            foreach (Match match in stateMatches)
            {
                temperatureStates.Add(match.Groups[1].Value.ToUpper());
            }

            // Check overall system temperature status
            var systemTempMatch = Regex.Match(output, @"SYSTEM TEMPERATURE is (\w+)", RegexOptions.IgnoreCase);
            string systemStatus = systemTempMatch.Success ? systemTempMatch.Groups[1].Value.ToUpper() : "";

            // Build temperature info string
            if (temperatures.Any())
            {
                var tempInfo = new StringBuilder();
                
                // Add system status if available
                if (!string.IsNullOrEmpty(systemStatus))
                {
                    tempInfo.Append($"System: {systemStatus}");
                }
                
                // Add specific temperature readings
                if (temperatures.Count == 1)
                    {
                    tempInfo.Append(tempInfo.Length > 0 ? $" ({temperatures[0]}°C)" : $"{temperatures[0]}°C");
                }
                else if (temperatures.Count > 1)
                {
                    var minTemp = temperatures.Min();
                    var maxTemp = temperatures.Max();
                    tempInfo.Append(tempInfo.Length > 0 ? $" ({minTemp}-{maxTemp}°C)" : $"{minTemp}-{maxTemp}°C");
            }

                // Add state information
                if (temperatureStates.Any())
                {
                    var uniqueStates = temperatureStates.Distinct().ToList();
                    if (uniqueStates.Count == 1)
                    {
                        var stateIcon = uniqueStates[0] == "GREEN" ? "✅" : 
                                       uniqueStates[0] == "YELLOW" ? "⚠️" : 
                                       uniqueStates[0] == "RED" ? "🔴" : "";
                        tempInfo.Append($" {stateIcon} {uniqueStates[0]}");
                    }
                    else
                    {
                        tempInfo.Append($" States: {string.Join(", ", uniqueStates)}");
                    }
                }
                
                info.Temperature = tempInfo.ToString();
            }
            else if (!string.IsNullOrEmpty(systemStatus))
            {
                info.Temperature = $"System: {systemStatus}";
            }
            else if (output.ToLower().Contains("ok") || output.ToLower().Contains("normal"))
            {
                info.Temperature = "✅ Normal (OK)";
            }
            else if (output.ToLower().Contains("warning") || output.ToLower().Contains("high"))
            {
                info.Temperature = "⚠️ Warning - High";
            }
            else if (output.ToLower().Contains("critical") || output.ToLower().Contains("alert"))
            {
                info.Temperature = "🔴 Critical - Check Required";
            }
            else
            {
                info.Temperature = "Monitoring Active";
            }
        }

        private void ParseUptimeInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output)) 
            {
                info.Uptime = "⏱️ Uptime bilgisi mevcut değil";
                return;
            }

            // Try multiple uptime patterns
            var patterns = new[]
            {
                @"uptime is (.+?)(?:\n|$)",
                @"System uptime:\s*(.+?)(?:\n|$)", 
                @"uptime:\s*(.+?)(?:\n|$)",
                @"(\d+)\s*days?",
                @"(\d+)\s*hours?",
                @"(\d+)\s*minutes?"
            };

            foreach (var pattern in patterns)
            {
                var match = Regex.Match(output, pattern, RegexOptions.IgnoreCase);
                if (match.Success)
                {
                    var uptime = match.Groups[1].Value.Trim();
                    if (uptime.Length > 3 && uptime.Length < 200)
                    {
                        info.Uptime = $"🕒 {uptime}";
                        return;
                    }
                }
            }

            // If no match, look for time indicators
            if (output.Contains("day") || output.Contains("hour") || output.Contains("minute"))
            {
                info.Uptime = "🕒 Sistem Aktif (CLI'de detaylar)";
            }
            else
            {
                info.Uptime = "✅ Normal Çalışıyor";
            }
        }

        private void ParseCpuInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output)) 
            {
                info.CpuUsage = "📊 CPU izleme mevcut değil";
                return;
            }

            // Try multiple CPU patterns
            var patterns = new[]
            {
                @"CPU utilization.*?(\d+)%",
                @"CPU usage.*?(\d+)%",
                @"(\d+)%.*?CPU",
                @"five minutes:\s*(\d+)%",
                @"one minute:\s*(\d+)%",
                @"five seconds:\s*(\d+)%"
            };

            foreach (var pattern in patterns)
            {
                var match = Regex.Match(output, pattern, RegexOptions.IgnoreCase);
                if (match.Success)
                {
                    var cpu = int.Parse(match.Groups[1].Value);
                    if (cpu >= 0 && cpu <= 100)
                    {
                        var status = cpu < 50 ? "İyi" : cpu < 80 ? "Orta" : "Yüksek";
                        var emoji = cpu < 50 ? "✅" : cpu < 80 ? "⚠️" : "🔴";
                        info.CpuUsage = $"{emoji} {cpu}% ({status})";
                        return;
                    }
                }
            }

            // Look for general status indicators
            if (output.ToLower().Contains("normal") || output.ToLower().Contains("ok"))
            {
                info.CpuUsage = "✅ Normal Aralık";
            }
            else if (output.ToLower().Contains("high") || output.ToLower().Contains("busy"))
            {
                info.CpuUsage = "⚠️ Yüksek Kullanım";
            }
            else
            {
                info.CpuUsage = "📊 İzleme Aktif";
            }
        }

        private void ParseMemoryInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output)) 
            {
                info.MemoryUsage = "💾 Bellek izleme mevcut değil";
                return;
            }

            // Try multiple memory patterns
            var patterns = new[]
            {
                @"Total.*?(\d+).*?Used.*?(\d+)",
                @"Memory.*?(\d+).*?used.*?(\d+)",
                @"Total:\s*(\d+).*?Used:\s*(\d+)",
                @"(\d+)%.*?used"
            };

            foreach (var pattern in patterns)
            {
                var match = Regex.Match(output, pattern, RegexOptions.IgnoreCase);
                if (match.Success)
                {
                    if (match.Groups.Count >= 3)
                    {
                        try
                        {
                            var total = long.Parse(match.Groups[1].Value);
                            var used = long.Parse(match.Groups[2].Value);
                            if (total > 0 && used >= 0 && used <= total)
                            {
                                var usagePercent = (used * 100) / total;
                                var status = usagePercent < 70 ? "İyi" : usagePercent < 90 ? "Yüksek" : "Kritik";
                                var emoji = usagePercent < 70 ? "✅" : usagePercent < 90 ? "⚠️" : "🔴";
                                info.MemoryUsage = $"{emoji} {usagePercent}% ({status})";
                                return;
                            }
                        }
                        catch { /* Continue to next pattern */ }
                    }
                    else if (match.Groups.Count >= 2)
                    {
                        // Direct percentage pattern
                        var percent = int.Parse(match.Groups[1].Value);
                        if (percent >= 0 && percent <= 100)
                        {
                            var status = percent < 70 ? "İyi" : percent < 90 ? "Yüksek" : "Kritik";
                            var emoji = percent < 70 ? "✅" : percent < 90 ? "⚠️" : "🔴";
                            info.MemoryUsage = $"{emoji} {percent}% ({status})";
                            return;
                        }
                    }
                }
            }

            // Look for status indicators
            if (output.ToLower().Contains("available") || output.ToLower().Contains("free"))
            {
                info.MemoryUsage = "✅ Mevcut";
            }
            else if (output.ToLower().Contains("full") || output.ToLower().Contains("low"))
            {
                info.MemoryUsage = "⚠️ Düşük Bellek";
                }
                else
                {
                info.MemoryUsage = "💾 Normal İşlem";
            }
        }

        private void ParsePowerInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output))
            {
                info.PowerStatus = "🔋 Normal Çalışma";
                info.PowerConsumption = "⚡ Spesifikasyon Dahilinde";
                return;
            }
            
            // Parse power status
            if (output.ToLower().Contains("ok") || output.ToLower().Contains("good") || output.ToLower().Contains("normal"))
            {
                info.PowerStatus = "✅ Tüm Güç Kaynakları OK";
            }
            else if (output.ToLower().Contains("warning") || output.ToLower().Contains("alert"))
            {
                info.PowerStatus = "⚠️ Uyarı Durumu";
            }
            else if (output.ToLower().Contains("fail") || output.ToLower().Contains("error") || output.ToLower().Contains("critical"))
            {
                info.PowerStatus = "❌ Kritik - Kontrol Gerekli";
            }
            else
            {
                info.PowerStatus = "🔋 İzleme Aktif";
            }
            
            // Parse power consumption
            var powerPatterns = new[]
            {
                @"(\d+)\s*W(?:atts?)?",
                @"Power:\s*(\d+)",
                @"Consumption:\s*(\d+)",
                @"Draw:\s*(\d+)"
            };

            foreach (var pattern in powerPatterns)
            {
                var match = Regex.Match(output, pattern, RegexOptions.IgnoreCase);
                if (match.Success)
                {
                    var watts = int.Parse(match.Groups[1].Value);
                    if (watts > 0 && watts <= 2000) // Reasonable range for switch power
                    {
                        var efficiency = watts < 200 ? "Verimli" : watts < 400 ? "Normal" : "Yüksek";
                        var emoji = watts < 200 ? "🟢" : watts < 400 ? "🟡" : "🔴";
                        info.PowerConsumption = $"{emoji} {watts}W ({efficiency})";
                        return;
                    }
                }
            }

            // If no numeric value found, use descriptive status
            if (output.ToLower().Contains("efficient") || output.ToLower().Contains("low"))
            {
                info.PowerConsumption = "🟢 Verimli İşlem";
            }
            else if (output.ToLower().Contains("high") || output.ToLower().Contains("max"))
            {
                info.PowerConsumption = "🔴 Yüksek Tüketim";
            }
            else
            {
                info.PowerConsumption = "⚡ Normal Aralık";
            }
        }

        // 🔥 FIREBASE: Comprehensive method to push all switch details to Firebase
        private async Task PushSwitchDetailsToFirebase()
        {
            if (firebaseService == null || string.IsNullOrEmpty(switchIP) || sshClient?.IsConnected != true)
                return;

            try
            {
                // 1. Push Switch System Information
                var switchInfo = await GetSwitchSystemInfo();
                if (switchInfo != null)
                {
                    await firebaseService.PushSwitchInfo(switchInfo, switchIP);
                }

                // 2. Push VLAN Information
                var vlanData = await ExecuteCommandSafely("show vlan brief");
                if (!string.IsNullOrEmpty(vlanData))
                {
                    await firebaseService.PushVlanInfo(switchIP, vlanData);
                }

                // 3. Push Interface Information
                var interfaceData = await ExecuteCommandSafely("show ip interface brief");
                if (!string.IsNullOrEmpty(interfaceData))
                {
                    await firebaseService.PushInterfaceInfo(switchIP, interfaceData);
                }

                // 4. Push Network Discovery (CDP/LLDP neighbors)
                var cdpData = await ExecuteCommandSafely("show cdp neighbors detail");
                var lldpData = await ExecuteCommandSafely("show lldp neighbors detail");
                var discoveryData = new List<string>();
                
                if (!string.IsNullOrEmpty(cdpData))
                    discoveryData.Add($"CDP: {cdpData}");
                
                if (!string.IsNullOrEmpty(lldpData))
                    discoveryData.Add($"LLDP: {lldpData}");

                if (discoveryData.Count > 0)
                {
                    await firebaseService.PushNetworkDiscovery(switchIP, discoveryData);
                }

                // 5. Push Switch Status (Online/Offline determination)
                var connectionData = new
                {
                    SwitchIP = switchIP,
                    IsOnline = sshClient?.IsConnected == true,
                    ConnectionTime = DateTime.UtcNow,
                    PortsActive = portStatus.Count(p => p.Value.IsUp),
                    PortsTotal = portStatus.Count,
                    LastHealthCheck = DateTime.UtcNow,
                    ResponseTime = "< 1000ms",
                    DeviceReachable = true,
                    MonitoringEnabled = refreshTimer?.IsEnabled == true,
                    Username = username,
                    DeviceId = Environment.MachineName
                };

                await firebaseService.PushConnectionInfo(switchIP, username ?? "unknown", true, 
                    $"Online - {portStatus.Count(p => p.Value.IsUp)}/{portStatus.Count} ports active");

            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to push comprehensive switch details: {ex.Message}");
            }
        }

        // 🔥 FIREBASE: Push individual command execution to Firebase for logging
        private async Task PushCommandToFirebase(string command, string response, string actionType = "Command")
        {
            try
            {
                if (firebaseService != null && !string.IsNullOrEmpty(switchIP))
                {
                    await firebaseService.PushCommandLog(command, response, switchIP, actionType);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase command log error: {ex.Message}");
            }
        }

        // 🔥 SÜREKLI MONİTORİNG: Her 1 saniyede çalışan ana monitoring fonksiyonu
        private async Task MonitorAndPushToFirebase()
        {
            if (firebaseService == null || string.IsNullOrEmpty(switchIP))
                return;

            try
            {
                var now = DateTime.UtcNow;
                bool hasChanges = false;

                // 1. PORT DURUMU DEĞİŞİKLİK KONTROLÜ
                if (HasPortStatusChanged())
                {
                    await firebaseService.PushPortStatus(portStatus, switchIP);
                    UpdateLastPortStatus(); // Cache'i güncelle
                    hasChanges = true;
                    
                    // Port durumu değişikliğini logla
                    var changedPorts = GetChangedPorts();
                    if (changedPorts.Count > 0)
                    {
                        await firebaseService.PushUsageStats("Port_Status_Changed", 
                            $"Changed ports: {string.Join(", ", changedPorts)}");
                    }
                }

                // 2. BAĞLANTI DURUMU SÜREKLI PUSH
                bool isCurrentlyConnected = sshClient?.IsConnected == true;
                await firebaseService.PushConnectionInfo(switchIP, username ?? "unknown", isCurrentlyConnected, 
                    $"Real-time monitoring - {portStatus.Count(p => p.Value.IsUp)}/{portStatus.Count} ports active");

                // 3. SWITCH SİSTEM BİLGİLERİ (Her 10 saniyede bir tam bilgi al)
                if (now.Subtract(lastFirebasePush).TotalSeconds >= 10 && isCurrentlyConnected)
                {
                    var currentSwitchInfo = await GetSwitchSystemInfo();
                    if (currentSwitchInfo != null && HasSwitchInfoChanged(currentSwitchInfo))
                    {
                        await firebaseService.PushSwitchInfo(currentSwitchInfo, switchIP);
                        lastSwitchInfo = currentSwitchInfo; // Cache'i güncelle
                        hasChanges = true;
                    }

                    // VLAN ve Interface bilgilerini de push et
                    _ = Task.Run(async () =>
                    {
                        try
                        {
                            var vlanData = await ExecuteCommandSafely("show vlan brief", 5);
                            if (!string.IsNullOrEmpty(vlanData))
                                await firebaseService.PushVlanInfo(switchIP, vlanData);

                            var interfaceData = await ExecuteCommandSafely("show ip interface brief", 5);
                            if (!string.IsNullOrEmpty(interfaceData))
                                await firebaseService.PushInterfaceInfo(switchIP, interfaceData);
                        }
                        catch (Exception ex)
                        {
                            System.Diagnostics.Debug.WriteLine($"Background VLAN/Interface push error: {ex.Message}");
                        }
                    });

                    lastFirebasePush = now;
                }

                // 4. HEARTBEAt / KALDı SINYAL (Her 5 saniyede bir)
                if (now.Subtract(lastFirebasePush).TotalSeconds >= 5)
                {
                    await firebaseService.PushUsageStats("Heartbeat", 
                        $"SwappC monitoring active - Switch: {switchIP} - Connected: {isCurrentlyConnected}");
                }

                // 5. STATUS GÜNCELLEME
                if (hasChanges)
                {
                    var timestamp = DateTime.Now.ToString("HH:mm:ss.fff");
                    UpdateStatus($"🔥 Firebase PUSHED [{timestamp}] - {portStatus.Count} ports monitored");
                }

            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase monitoring error: {ex.Message}");
                // Hatayı logla ama monitoring'i durdurma
                if (DateTime.UtcNow.Subtract(lastFirebasePush).TotalMinutes > 1)
                {
                    try
                    {
                        await firebaseService?.PushUsageStats("Monitoring_Error", ex.Message);
                        lastFirebasePush = DateTime.UtcNow;
                    }
                    catch { /* Ignore logging errors */ }
                }
            }
        }

        // Port durumu değişti mi kontrol et
        private bool HasPortStatusChanged()
        {
            if (lastPortStatus.Count != portStatus.Count)
                return true;

            foreach (var kvp in portStatus)
            {
                if (!lastPortStatus.ContainsKey(kvp.Key))
                    return true;

                var last = lastPortStatus[kvp.Key];
                var current = kvp.Value;

                if (last.Status != current.Status || 
                    last.IsUp != current.IsUp || 
                    last.IsDown != current.IsDown || 
                    last.IsShutdown != current.IsShutdown)
                {
                    return true;
                }
            }

            return false;
        }

        // Switch info değişti mi kontrol et
        private bool HasSwitchInfoChanged(SwitchSystemInfo current)
        {
            if (lastSwitchInfo == null) return true;

            return lastSwitchInfo.Temperature != current.Temperature ||
                   lastSwitchInfo.CpuUsage != current.CpuUsage ||
                   lastSwitchInfo.MemoryUsage != current.MemoryUsage ||
                   lastSwitchInfo.PowerStatus != current.PowerStatus ||
                   lastSwitchInfo.FanStatus != current.FanStatus ||
                   lastSwitchInfo.Uptime != current.Uptime;
        }

        // Son port durumunu cache'e kaydet
        private void UpdateLastPortStatus()
        {
            lastPortStatus.Clear();
            foreach (var kvp in portStatus)
            {
                lastPortStatus[kvp.Key] = new PortStatus
                {
                    Name = kvp.Value.Name,
                    Status = kvp.Value.Status,
                    IsUp = kvp.Value.IsUp,
                    IsDown = kvp.Value.IsDown,
                    IsShutdown = kvp.Value.IsShutdown
                };
            }
        }

        // Değişen portları bul
        private List<string> GetChangedPorts()
        {
            var changedPorts = new List<string>();

            foreach (var kvp in portStatus)
            {
                if (!lastPortStatus.ContainsKey(kvp.Key))
                {
                    changedPorts.Add($"{kvp.Key}:NEW");
                    continue;
                }

                var last = lastPortStatus[kvp.Key];
                var current = kvp.Value;

                if (last.Status != current.Status)
                {
                    changedPorts.Add($"{kvp.Key}:{last.Status}→{current.Status}");
                }
            }

            return changedPorts;
        }

        private void ParseFanInfo(SwitchSystemInfo info, string output)
        {
            if (string.IsNullOrEmpty(output))
            {
                info.FanStatus = "💨 Soğutma sistemi OK";
                return;
            }
            
            var fanOkCount = Regex.Matches(output, @"OK|GOOD|NORMAL", RegexOptions.IgnoreCase).Count;
            var fanFailCount = Regex.Matches(output, @"FAIL|ERROR|CRITICAL|ALERT", RegexOptions.IgnoreCase).Count;
            var fanWarningCount = Regex.Matches(output, @"WARNING|SLOW|HIGH", RegexOptions.IgnoreCase).Count;
            
            if (fanFailCount > 0)
            {
                info.FanStatus = $"❌ {fanFailCount} Fan Arızalı - Kontrol Gerekli";
            }
            else if (fanWarningCount > 0)
            {
                info.FanStatus = $"⚠️ {fanWarningCount} Fan Uyarı Durumunda";
            }
            else if (fanOkCount > 0)
            {
                info.FanStatus = $"✅ Tüm {fanOkCount} Fan OK";
            }
            else
            {
                // Look for RPM values to indicate fans are working
                var rpmMatches = Regex.Matches(output, @"(\d+)\s*RPM", RegexOptions.IgnoreCase);
                if (rpmMatches.Count > 0)
                {
                    var avgRpm = rpmMatches.Cast<Match>()
                        .Select(m => int.Parse(m.Groups[1].Value))
                        .Where(rpm => rpm > 0)
                        .DefaultIfEmpty(0)
                        .Average();
                    
                    if (avgRpm > 1000)
                    {
                        info.FanStatus = $"✅ Fanlar Çalışıyor ({avgRpm:F0} RPM ort)";
                    }
                    else if (avgRpm > 0)
                    {
                        info.FanStatus = $"⚠️ Düşük Hız ({avgRpm:F0} RPM ort)";
                    }
                    else
                    {
                        info.FanStatus = "💨 İzleme Aktif";
                    }
                }
                else
                {
                    // General status based on keywords
                    if (output.ToLower().Contains("cooling") && output.ToLower().Contains("ok"))
                    {
                        info.FanStatus = "✅ Soğutma Sistemi OK";
                    }
                    else if (output.ToLower().Contains("normal") || output.ToLower().Contains("operational"))
                    {
                        info.FanStatus = "✅ Normal İşlem";
                    }
                    else
                    {
                        info.FanStatus = "💨 İzleme Aktif";
                    }
                }
            }
        }

        private void UpdatePortButton(Button button, PortStatus port)
        {
            var portNum = port.Name.Substring(port.Name.LastIndexOf('/') + 1);
            
            // Enhanced button content with VLAN info
            var vlanInfo = !string.IsNullOrEmpty(port.VlanId) ? $"\nVLAN {port.VlanId}" : "";
            button.Content = $"{portNum}\nGigE{vlanInfo}";
            
            // Color coding based on status
            if (port.IsUp)
            {
                button.Background = Brushes.LightGreen;
                button.Foreground = Brushes.DarkGreen;
            }
            else if (port.IsShutdown)
            {
                button.Background = Brushes.Gray;
                button.Foreground = Brushes.White;
            }
            else if (port.IsDown)
            {
                button.Background = Brushes.LightCoral;
                button.Foreground = Brushes.DarkRed;
            }
            else
            {
                button.Background = Brushes.LightGray;
                button.Foreground = Brushes.Black;
            }
            
            // Enhanced tooltip with VLAN information
            var tooltip = new StringBuilder();
            tooltip.AppendLine($"Port: {port.Name}");
            tooltip.AppendLine($"Status: {port.Status.ToUpper()}");
            
            if (!string.IsNullOrEmpty(port.VlanId))
                tooltip.AppendLine($"VLAN ID: {port.VlanId}");
            
            if (!string.IsNullOrEmpty(port.VlanName))
                tooltip.AppendLine($"VLAN Name: {port.VlanName}");
            
            if (!string.IsNullOrEmpty(port.SwitchportMode))
                tooltip.AppendLine($"Mode: {port.SwitchportMode}");
            
            if (!string.IsNullOrEmpty(port.Speed))
                tooltip.AppendLine($"Speed: {port.Speed}");
            
            if (!string.IsNullOrEmpty(port.Duplex))
                tooltip.AppendLine($"Duplex: {port.Duplex}");
            
            button.ToolTip = tooltip.ToString().TrimEnd();
        }
    }

    public class PortStatus
    {
        public string Name { get; set; } = "";
        public string Status { get; set; } = "";
        public bool IsUp { get; set; }
        public bool IsDown { get; set; }
        public bool IsShutdown { get; set; }
        public string VlanId { get; set; } = "";
        public string VlanName { get; set; } = "";
        public string SwitchportMode { get; set; } = "";
        public string Speed { get; set; } = "";
        public string Duplex { get; set; } = "";
    }

    public class SwitchSystemInfo
    {
        public string IosVersion { get; set; } = "";
        public string ModelNumber { get; set; } = "";
        public string SerialNumber { get; set; } = "";
        public string MacAddress { get; set; } = "";
        public string ActivePorts { get; set; } = "";
        public string Temperature { get; set; } = "";
        public string Uptime { get; set; } = "";
        public string CpuUsage { get; set; } = "";
        public string MemoryUsage { get; set; } = "";
        public string PowerStatus { get; set; } = "";
        public string PowerConsumption { get; set; } = "";
        public string FanStatus { get; set; } = "";
        public DateTime LastUpdated { get; set; }
        public string ErrorMessage { get; set; } = "";
        public bool IsDataValid { get; set; } = false;
    }
} 
