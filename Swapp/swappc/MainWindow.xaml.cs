using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using Renci.SshNet;

namespace SwappC
{
    public partial class MainWindow : Window
    {
        private SshClient? sshClient;
        private ShellStream? shellStream;
        private List<string> commandHistory = new List<string>();
        private int historyIndex = -1;
        private string currentHostname = "";
        private CancellationTokenSource? readCancellationTokenSource;
        private bool isDisconnecting = false;
        private FirebaseService? firebaseService;
        private DispatcherTimer? mainAppMonitorTimer; // 🔥 Ana uygulama monitoring timer
        private DateTime lastMainAppPush = DateTime.MinValue;

        public MainWindow()
        {
            InitializeComponent();
            InitializeTerminal();
            InitializeFirebase();
            UpdateStatus("🚀 Ready to connect");
        }

        private async void InitializeFirebase()
        {
            try
            {
                firebaseService = new FirebaseService();
                
                // Log application startup
                await firebaseService.PushUsageStats("Application_Started", $"SwappC started on {Environment.MachineName}");
                
                // 🔥 Ana uygulama için sürekli monitoring başlat
                InitializeMainAppMonitoring();
                
                // Show Firebase status
                UpdateStatus("🔥 Firebase initialized + Real-time monitoring ACTIVE");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase initialization failed: {ex.Message}");
                UpdateStatus("⚠️ Firebase unavailable - Ready to connect");
            }
        }

        // 🔥 Ana uygulama için sürekli monitoring
        private void InitializeMainAppMonitoring()
        {
            mainAppMonitorTimer = new DispatcherTimer();
            mainAppMonitorTimer.Interval = TimeSpan.FromSeconds(1); // HER 1 SANİYE!
            mainAppMonitorTimer.Tick += async (s, e) => await MonitorMainAppToFirebase();
            mainAppMonitorTimer.Start();
        }

        // 🔥 Ana uygulama monitoring fonksiyonu
        private async Task MonitorMainAppToFirebase()
        {
            if (firebaseService == null) return;

            try
            {
                var now = DateTime.UtcNow;

                // 1. BAĞLANTI DURUMU SÜREKLI PUSH (Her 1 saniye)
                if (!string.IsNullOrEmpty(txtHost.Text))
                {
                    bool isConnected = sshClient?.IsConnected == true;
                    await firebaseService.PushConnectionInfo(
                        txtHost.Text, 
                        txtUsername.Text, 
                        isConnected, 
                        isConnected ? $"Active SSH session - Commands: {commandHistory.Count}" : "Disconnected"
                    );

                    // Connection status değişikliği logla
                    if (now.Subtract(lastMainAppPush).TotalSeconds >= 5)
                    {
                        await firebaseService.PushUsageStats("MainApp_Heartbeat", 
                            $"SSH Status: {(isConnected ? "Connected" : "Disconnected")} - Host: {txtHost.Text}");
                        lastMainAppPush = now;
                    }
                }

                // 2. KOMUT AKTİVİTESİ İZLEME (Her 3 saniye)
                if (now.Subtract(lastMainAppPush).TotalSeconds >= 3)
                {
                    var timestamp = DateTime.Now.ToString("HH:mm:ss");
                    UpdateStatus($"🔥 Firebase monitoring LIVE [{timestamp}] - SSH: {(sshClient?.IsConnected == true ? "ON" : "OFF")}");
                }

            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Main app Firebase monitoring error: {ex.Message}");
            }
        }

        private void InitializeTerminal()
        {
            // Set terminal appearance
            txtOutput.Background = new SolidColorBrush(Color.FromRgb(0, 0, 0));
            txtOutput.Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 65));
            txtOutput.FontFamily = new FontFamily("Consolas");
            txtOutput.FontSize = 13;
            
            // Add welcome message
            AppendTerminalText("╔══════════════════════════════════════╗\n", Colors.Cyan);
            AppendTerminalText("║          ⚡ SwappC Terminal          ║\n", Colors.Cyan);
            AppendTerminalText("║     Professional SSH Client v2.0    ║\n", Colors.Cyan);
            AppendTerminalText("╚══════════════════════════════════════╝\n", Colors.Cyan);
            AppendTerminalText("\n");
            AppendTerminalText("💡 Tips:\n", Colors.Yellow);
            AppendTerminalText("  • Use ↑/↓ arrows for command history\n", Colors.Gray);
            AppendTerminalText("  • Press Tab for command completion\n", Colors.Gray);
            AppendTerminalText("  • Ctrl+C to interrupt commands\n", Colors.Gray);
            AppendTerminalText("  • Type 'help' for available commands\n", Colors.Gray);
            AppendTerminalText("\n");
            AppendTerminalText("Please connect to start SSH session...\n", Colors.Orange);
            AppendTerminalText("\n");
            
            // Set command input placeholder
            txtCommand.Text = "Connect to SSH to start typing commands...";
            txtCommand.Foreground = new SolidColorBrush(Colors.Gray);
        }

        private async void BtnConnect_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrWhiteSpace(txtHost.Text) || 
                string.IsNullOrWhiteSpace(txtUsername.Text))
            {
                MessageBox.Show("Please enter host and username.", "Missing Information", 
                              MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                btnConnect.IsEnabled = false;
                UpdateStatus("Connecting...");

                var connectionInfo = new ConnectionInfo(
                    txtHost.Text.Trim(),
                    int.Parse(txtPort.Text),
                    txtUsername.Text.Trim(),
                    new PasswordAuthenticationMethod(txtUsername.Text.Trim(), txtPassword.Password)
                );
                
                // Enhanced connection settings for better stability
                connectionInfo.Timeout = TimeSpan.FromSeconds(30);
                connectionInfo.MaxSessions = 10;
                connectionInfo.Encoding = System.Text.Encoding.UTF8;

                sshClient = new SshClient(connectionInfo);
                
                // Set keep-alive to prevent connection drops
                sshClient.KeepAliveInterval = TimeSpan.FromSeconds(10);
                
                await Task.Run(() => sshClient.Connect());

                if (sshClient.IsConnected)
                {
                    // Reset flags
                    isDisconnecting = false;
                    readCancellationTokenSource?.Cancel();
                    readCancellationTokenSource?.Dispose();
                    readCancellationTokenSource = new CancellationTokenSource();
                    
                    // Push connection info to Firebase (NON-BLOCKING)
                    _ = PushConnectionInfoSafely();
                    
                    // Optimized terminal settings for Cisco devices
                    shellStream = sshClient.CreateShellStream("vt100", 160, 50, 1600, 1200, 4096);
                    
                    // Configure Cisco terminal for better command handling
                    await Task.Delay(500); // Wait for shell to initialize
                    
                    // Send terminal length 0 to prevent --More-- prompts
                    await ConfigureCiscoTerminal();
                    
                    // Start reading output in background with cancellation token
                    _ = Task.Run(async () => await ReadShellOutput(readCancellationTokenSource.Token));

                    // Update UI
                    btnConnect.IsEnabled = false;
                    btnDisconnect.IsEnabled = true;
                    txtCommand.IsEnabled = true;
                    btnSend.IsEnabled = true;
                    commandTabControl.IsEnabled = true;
                    
                    // Clear placeholder text and setup terminal
                    txtCommand.Text = "";
                    txtCommand.Foreground = new SolidColorBrush(Colors.Black);
                    
                    currentHostname = txtHost.Text;
                    
                    UpdateStatus($"🔗 Connected to {txtHost.Text}");
                    
                    // Add connection success message with styling
                    ShowConnectionSuccessMessage();
                    
                    // Add some demo commands to history for testing
                    commandHistory.AddRange(new[]
                    {
                        "show version",
                        "show ip interface brief", 
                        "show running-config",
                        "show interfaces status"
                    });
                    
                    // Focus on command input
                    txtCommand.Focus();
                    
                    // Reset status after connection message
                    _ = DelayedStatusUpdate();
                }
            }
            catch (Exception ex)
            {
                HandleConnectionError(ex);
            }
            finally
            {
                if (!sshClient?.IsConnected == true)
                {
                    btnConnect.IsEnabled = true;
                }
            }
        }

        private async Task PushConnectionInfoSafely()
        {
            try
            {
                if (firebaseService != null)
                {
                    await firebaseService.PushConnectionInfo(
                            txtHost.Text, 
                            txtUsername.Text, 
                            true, 
                            $"Connected successfully from {Environment.MachineName}"
                        );
                        
                    await firebaseService.PushUsageStats(
                            "SSH_Connection_Established", 
                            $"Connected to {txtHost.Text} as {txtUsername.Text}"
                        );
                }
                    }
                    catch (Exception fbEx)
                    {
                        System.Diagnostics.Debug.WriteLine($"Firebase connection log failed: {fbEx.Message}");
                    }
        }

        private async Task ConfigureCiscoTerminal()
        {
            try
            {
                if (shellStream != null)
                {
                    var initCommands = new string[]
                    {
                        "terminal length 0\r\n",
                        "terminal width 0\r\n"
                    };
                    
                    foreach (var initCmd in initCommands)
                    {
                        var initBytes = System.Text.Encoding.UTF8.GetBytes(initCmd);
                        shellStream.Write(initBytes, 0, initBytes.Length);
                        shellStream.Flush();
                        await Task.Delay(100);
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Cisco terminal config failed: {ex.Message}");
            }
        }

        private void ShowConnectionSuccessMessage()
        {
            try
            {
                    AppendTerminalText("════════════════════════════════════════\n", Colors.Green);
                    AppendTerminalText($"✅ SSH CONNECTION ESTABLISHED\n", Colors.LightGreen);
                    AppendTerminalText($"🌐 Host: {txtHost.Text}:{txtPort.Text}\n", Colors.Cyan);
                    AppendTerminalText($"👤 User: {txtUsername.Text}\n", Colors.Cyan);
                    AppendTerminalText($"🕒 Time: {DateTime.Now:yyyy-MM-dd HH:mm:ss}\n", Colors.Gray);
                    AppendTerminalText("════════════════════════════════════════\n", Colors.Green);
                    AppendTerminalText("\n");
                    AppendTerminalText("🎯 Terminal ready! You can now execute commands.\n", Colors.Yellow);
                    AppendTerminalText("💡 Try: show version, show ip interface brief, etc.\n", Colors.Gray);
                    AppendTerminalText("\n");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Connection message display failed: {ex.Message}");
            }
        }

        private async Task DelayedStatusUpdate()
        {
            try
                    {
                        await Task.Delay(3000);
                        Dispatcher.Invoke(() => UpdateStatus($"🔗 Connected to {txtHost.Text}"));
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Delayed status update failed: {ex.Message}");
            }
        }

        private void HandleConnectionError(Exception ex)
        {
            try
            {
                string errorMessage = $"Connection failed: {ex.Message}";
                MessageBox.Show(errorMessage, "Connection Error", 
                              MessageBoxButton.OK, MessageBoxImage.Error);
                
                btnConnect.IsEnabled = true;
                UpdateStatus("Connection failed");
                
                // Clean up any partial connections
                CleanupSshResources();
            }
            catch (Exception cleanupEx)
            {
                System.Diagnostics.Debug.WriteLine($"Error cleanup failed: {cleanupEx.Message}");
            }
        }

        private void CleanupSshResources()
        {
            try
            {
                readCancellationTokenSource?.Cancel();
                readCancellationTokenSource?.Dispose();
                readCancellationTokenSource = null;
                
                shellStream?.Close();
                shellStream?.Dispose();
                shellStream = null;
                
                sshClient?.Disconnect();
                sshClient?.Dispose();
                sshClient = null;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"SSH cleanup error: {ex.Message}");
            }
        }

        private void BtnDisconnect_Click(object sender, RoutedEventArgs e)
        {
            DisconnectSsh();
        }

        private void DisconnectSsh()
        {
            try
            {
                // Set disconnecting flag to prevent race conditions
                isDisconnecting = true;
                
                // Cancel background reading task first
                readCancellationTokenSource?.Cancel();
                
                // Add disconnection message with styling
                if (sshClient?.IsConnected == true)
                {
                    AppendTerminalText("════════════════════════════════════════\n", Colors.Red);
                    AppendTerminalText("🔌 SSH CONNECTION TERMINATED\n", Colors.Orange);
                    AppendTerminalText($"🕒 Time: {DateTime.Now:yyyy-MM-dd HH:mm:ss}\n", Colors.Gray);
                    AppendTerminalText("════════════════════════════════════════\n", Colors.Red);
                    AppendTerminalText("\n");
                }
                
                // Wait a moment for background tasks to stop
                Thread.Sleep(100);
                
                // Dispose SSH objects safely
                try
                {
                    shellStream?.Close();
                shellStream?.Dispose();
                    shellStream = null;
                }
                catch (Exception ex)
                {
                    UpdateStatus($"Shell dispose warning: {ex.Message}");
                }
                
                try
                {
                sshClient?.Disconnect();
                sshClient?.Dispose();
                    sshClient = null;
                }
                catch (Exception ex)
                {
                    UpdateStatus($"SSH dispose warning: {ex.Message}");
                }
                
                // Dispose cancellation token
                readCancellationTokenSource?.Dispose();
                readCancellationTokenSource = null;
                
                // Reset UI state
                btnConnect.IsEnabled = true;
                btnDisconnect.IsEnabled = false;
                txtCommand.IsEnabled = false;
                btnSend.IsEnabled = false;
                commandTabControl.IsEnabled = false;
                
                // Reset terminal state
                txtCommand.Text = "Connect to SSH to start typing commands...";
                txtCommand.Foreground = new SolidColorBrush(Colors.Gray);
                currentHostname = "";
                
                UpdateStatus("⭕ Disconnected");
                AppendTerminalText("📱 Terminal is now offline. Connect to SSH to continue.\n", Colors.Orange);
                AppendTerminalText("\n");
            }
            catch (Exception ex)
            {
                UpdateStatus($"❌ Disconnect error: {ex.Message}");
                AppendTerminalText($"⚠️ Disconnect error: {ex.Message}\n", Colors.Red);
            }
        }

        private async void BtnSend_Click(object sender, RoutedEventArgs e)
        {
            try
        {
            await SendCommand();
            }
            catch (Exception ex)
            {
                UpdateStatus($"Send command error: {ex.Message}");
                AppendTerminalText($"❌ Command send failed: {ex.Message}\n", Colors.Red);
            }
        }

        private void TxtCommand_PreviewKeyDown(object sender, KeyEventArgs e)
        {
            // Handle navigation keys in PreviewKeyDown to prevent TextBox from handling them
            switch (e.Key)
            {
                case Key.Up:
                    NavigateCommandHistory(-1);
                    e.Handled = true;
                    break;
                    
                case Key.Down:
                    NavigateCommandHistory(1);
                    e.Handled = true;
                    break;
                    
                case Key.Tab:
                    HandleTabCompletion();
                    e.Handled = true;
                    break;
            }
        }

        private async void TxtCommand_KeyDown(object sender, KeyEventArgs e)
        {
            switch (e.Key)
            {
                case Key.Enter:
                    await SendCommand();
                    break;
                    
                case Key.C when Keyboard.Modifiers == ModifierKeys.Control:
                    SendInterrupt();
                    e.Handled = true;
                    break;
                    
                case Key.L when Keyboard.Modifiers == ModifierKeys.Control:
                    ClearTerminal();
                    e.Handled = true;
                    break;
            }
        }

        private void NavigateCommandHistory(int direction)
        {
            if (commandHistory.Count == 0) 
            {
                AppendTerminalText("📝 No command history available\n", Colors.Yellow);
                return;
            }
            
            if (direction < 0) // Up arrow - go back in history
            {
                if (historyIndex < 0)
                    historyIndex = commandHistory.Count - 1;
                else if (historyIndex > 0)
                    historyIndex--;
            }
            else // Down arrow - go forward in history
            {
                if (historyIndex >= 0 && historyIndex < commandHistory.Count - 1)
                    historyIndex++;
                else
                {
                    historyIndex = -1;
                    txtCommand.Text = "";
                    txtCommand.CaretIndex = 0;
                    return;
                }
            }
            
            if (historyIndex >= 0 && historyIndex < commandHistory.Count)
            {
                txtCommand.Text = commandHistory[historyIndex];
                txtCommand.CaretIndex = txtCommand.Text.Length;
                
                // Visual feedback for history navigation
                UpdateStatus($"📜 History: {historyIndex + 1}/{commandHistory.Count} - {commandHistory[historyIndex]}");
            }
        }

        private void HandleTabCompletion()
        {
            var currentText = txtCommand.Text.Trim();
            if (string.IsNullOrEmpty(currentText)) return;
            
            // Comprehensive Cisco command completion
            var ciscoCommands = new[]
            {
                // Show commands
                "show version", "show running-config", "show startup-config",
                "show ip interface brief", "show interfaces status", "show interfaces",
                "show mac address-table", "show arp", "show ip route",
                "show vlan brief", "show vlan", "show spanning-tree",
                "show etherchannel summary", "show etherchannel",
                "show environment", "show environment temperature", "show environment power",
                "show environment fan", "show inventory", "show processes",
                "show processes cpu", "show memory", "show logging",
                "show users", "show sessions", "show ssh", "show telnet",
                "show clock", "show calendar", "show flash", "show boot",
                "show tech-support", "show cdp neighbors", "show lldp neighbors",
                
                // Configuration commands
                "configure terminal", "config t", "interface", "int",
                "vlan", "ip", "no", "exit", "end", "write", "copy",
                "copy running-config startup-config", "write memory",
                "copy startup-config running-config", "reload", "write erase",
                
                // Interface commands
                "interface gigabitethernet", "interface fastethernet",
                "interface vlan", "interface loopback", "interface serial",
                
                // Network commands
                "ping", "traceroute", "telnet", "ssh", "arp",
                
                // Debug commands
                "debug", "undebug", "undebug all", "terminal monitor",
                
                // Clear commands
                "clear", "clear arp", "clear mac address-table", "clear logging",
                "clear counters", "clear interface"
            };
            
            // Find matches
            var exactMatches = ciscoCommands.Where(cmd => 
                cmd.StartsWith(currentText, StringComparison.OrdinalIgnoreCase)).ToList();
            
            // Also find partial word matches
            var wordMatches = ciscoCommands.Where(cmd => 
                cmd.Split(' ').Any(word => word.StartsWith(currentText, StringComparison.OrdinalIgnoreCase))).ToList();
            
            var allMatches = exactMatches.Union(wordMatches).Distinct().ToList();
            
            if (allMatches.Count == 1)
            {
                txtCommand.Text = allMatches[0];
                txtCommand.CaretIndex = txtCommand.Text.Length;
            }
            else if (allMatches.Count > 1)
            {
                // Find common prefix
                var commonPrefix = FindCommonPrefix(exactMatches.Count > 0 ? exactMatches : allMatches, currentText);
                if (commonPrefix.Length > currentText.Length)
                {
                    txtCommand.Text = commonPrefix;
                    txtCommand.CaretIndex = txtCommand.Text.Length;
                }
                else
                {
                    AppendTerminalText($"\n💡 Available completions for '{currentText}' ({allMatches.Count} matches):\n", Colors.Yellow);
                    
                    // Show exact matches first
                    if (exactMatches.Count > 0)
                    {
                        AppendTerminalText("🎯 Exact matches:\n", Colors.Green);
                        foreach (var match in exactMatches.Take(8))
                        {
                            AppendTerminalText($"  • {match}\n", Colors.Cyan);
                        }
                    }
                    
                    // Show partial matches
                    var remainingMatches = allMatches.Except(exactMatches).Take(10 - exactMatches.Count);
                    if (remainingMatches.Any())
                    {
                        AppendTerminalText("🔍 Contains matches:\n", Colors.Gray);
                        foreach (var match in remainingMatches)
                        {
                            AppendTerminalText($"  • {match}\n", Colors.DarkCyan);
                        }
                    }
                    
                    if (allMatches.Count > 18)
                        AppendTerminalText($"  ... and {allMatches.Count - 18} more matches\n", Colors.Gray);
                    AppendTerminalText("\n");
                }
            }
            else
            {
                AppendTerminalText($"❌ No command completions found for '{currentText}'\n", Colors.Red);
            }
        }

        private string FindCommonPrefix(List<string> commands, string currentText)
        {
            if (commands.Count == 0) return currentText;
            
            var first = commands[0];
            var commonLength = currentText.Length;
            
            for (int i = commonLength; i < first.Length; i++)
            {
                var currentChar = first[i];
                if (!commands.All(cmd => cmd.Length > i && 
                    char.ToLower(cmd[i]) == char.ToLower(currentChar)))
                {
                    break;
                }
                commonLength++;
            }
            
            return first.Substring(0, commonLength);
        }

        private void SendInterrupt()
        {
            if (shellStream != null && shellStream.CanWrite && 
                !isDisconnecting && sshClient?.IsConnected == true)
            {
                try
                {
                    AppendTerminalText("^C\n", Colors.Red);
                    var ctrlCBytes = new byte[] { 0x03 }; // Ctrl+C as byte array
                    shellStream.Write(ctrlCBytes, 0, 1);
                    shellStream.Flush();
                }
                catch (ObjectDisposedException)
                {
                    AppendTerminalText("❌ SSH connection has been closed\n", Colors.Red);
                    DisconnectSsh();
                }
                catch (Exception ex)
                {
                    AppendTerminalText($"❌ Failed to send interrupt: {ex.Message}\n", Colors.Red);
                }
            }
        }

        private void ClearTerminal()
        {
            txtOutput.Clear();
            AppendTerminalText("🧹 Terminal cleared\n", Colors.Yellow);
            if (!string.IsNullOrEmpty(currentHostname))
            {
                AppendTerminalText($"📡 Connected to {currentHostname}\n\n", Colors.Cyan);
            }
        }

        private async Task SendCommand()
        {
            if (shellStream == null || string.IsNullOrWhiteSpace(txtCommand.Text) || 
                isDisconnecting || sshClient?.IsConnected != true)
                return;
                
                var command = txtCommand.Text.Trim();
            
            // Add to command history
            if (!string.IsNullOrEmpty(command))
            {
                // Remove duplicate if exists
                commandHistory.RemoveAll(c => c.Equals(command, StringComparison.OrdinalIgnoreCase));
                commandHistory.Add(command);
                
                // Keep only last 50 commands
                if (commandHistory.Count > 50)
                    commandHistory.RemoveAt(0);
            }
            
            historyIndex = -1; // Reset history navigation
            
            // Display command with prompt styling
            var timestamp = DateTime.Now.ToString("HH:mm:ss");
            AppendTerminalText($"[{timestamp}] ", Colors.Gray);
            AppendTerminalText($"{txtUsername.Text}@{currentHostname}", Colors.Green);
            AppendTerminalText($"$ ", Colors.White);
            AppendTerminalText($"{command}\n", Colors.Yellow);
            
            // Handle built-in commands
            if (HandleBuiltInCommands(command))
            {
                txtCommand.Clear();
                return;
            }
            
            // Send command to SSH safely - ROBUST METHOD FOR CISCO
            try
            {
                if (shellStream != null && shellStream.CanWrite && !isDisconnecting && sshClient?.IsConnected == true)
                {
                    // Method: Single write with proper buffering and timing
                    var fullCommand = command + "\r\n";
                    var commandBytes = System.Text.Encoding.UTF8.GetBytes(fullCommand);
                    
                    // Clear any pending data in stream
                    await Task.Delay(10);
                    
                    // Single atomic write - most reliable for Cisco
                    shellStream.Write(commandBytes, 0, commandBytes.Length);
                    
                    // CRITICAL: Wait before flush to allow buffer to fill
                    await Task.Delay(20);
                    
                    // Force transmission
                    shellStream.Flush();
                    
                    // Additional delay to ensure command is fully sent
                    await Task.Delay(10);
                    
                    // 🔥 FIREBASE: Log command execution
                    _ = Task.Run(async () =>
                    {
                        try
                        {
                            if (firebaseService != null)
                            {
                                await firebaseService.PushCommandLog(command, "Manual command executed", 
                                                                   txtHost.Text, "ManualCommand");
                            }
                        }
                        catch (Exception ex)
                        {
                            System.Diagnostics.Debug.WriteLine($"Firebase manual command log error: {ex.Message}");
                        }
                    });
                }
                else
                {
                    AppendTerminalText("❌ Shell stream is not available for writing\n", Colors.Red);
                }
            }
            catch (ObjectDisposedException)
            {
                AppendTerminalText("❌ SSH connection has been closed\n", Colors.Red);
                DisconnectSsh();
            }
            catch (Exception ex)
            {
                AppendTerminalText($"❌ Error sending command: {ex.Message}\n", Colors.Red);
            }
            
            txtCommand.Clear();
        }

        private bool HandleBuiltInCommands(string command)
        {
            var cmd = command.ToLower().Trim();
            
            switch (cmd)
            {
                case "clear":
                case "cls":
                    ClearTerminal();
                    return true;
                    
                case "help":
                    ShowHelp();
                    return true;
                    
                case "history":
                    ShowCommandHistory();
                    return true;
                    
                case "exit":
                case "quit":
                case "logout":
                    DisconnectSsh();
                    return true;
                    
                default:
                    return false;
            }
        }

        private void ShowHelp()
        {
            AppendTerminalText("╔════════════════════════════════════════╗\n", Colors.Cyan);
            AppendTerminalText("║            📚 Built-in Commands        ║\n", Colors.Cyan);
            AppendTerminalText("╠════════════════════════════════════════╣\n", Colors.Cyan);
            AppendTerminalText("║ help          - Show this help message ║\n", Colors.White);
            AppendTerminalText("║ clear/cls     - Clear terminal screen  ║\n", Colors.White);
            AppendTerminalText("║ history       - Show command history   ║\n", Colors.White);
            AppendTerminalText("║ exit/quit     - Disconnect from SSH    ║\n", Colors.White);
            AppendTerminalText("╠════════════════════════════════════════╣\n", Colors.Cyan);
            AppendTerminalText("║            ⌨️ Keyboard Shortcuts       ║\n", Colors.Cyan);
            AppendTerminalText("╠════════════════════════════════════════╣\n", Colors.Cyan);
            AppendTerminalText("║ ↑/↓           - Navigate history       ║\n", Colors.White);
            AppendTerminalText("║ Tab           - Auto-complete commands  ║\n", Colors.White);
            AppendTerminalText("║ Ctrl+C        - Interrupt command      ║\n", Colors.White);
            AppendTerminalText("║ Ctrl+L        - Clear screen           ║\n", Colors.White);
            AppendTerminalText("╚════════════════════════════════════════╝\n", Colors.Cyan);
            AppendTerminalText("\n");
        }

        private void ShowCommandHistory()
        {
            if (commandHistory.Count == 0)
            {
                AppendTerminalText("📝 Command history is empty.\n", Colors.Yellow);
                return;
            }
            
            AppendTerminalText("📜 Command History:\n", Colors.Cyan);
            AppendTerminalText("═══════════════\n", Colors.Cyan);
            
            for (int i = Math.Max(0, commandHistory.Count - 20); i < commandHistory.Count; i++)
            {
                AppendTerminalText($"{i + 1:D2}. {commandHistory[i]}\n", Colors.Gray);
            }
            
            if (commandHistory.Count > 20)
                AppendTerminalText($"... and {commandHistory.Count - 20} more commands\n", Colors.DarkGray);
                
            AppendTerminalText("\n");
        }

        private async Task ReadShellOutput(CancellationToken cancellationToken)
        {
            if (shellStream == null) return;

            var buffer = new byte[4096]; // Larger buffer for better performance
            var outputBuilder = new StringBuilder();
            
            try
            {
                while (!cancellationToken.IsCancellationRequested && 
                       !isDisconnecting && 
                       shellStream != null && 
                       shellStream.CanRead && 
                       sshClient?.IsConnected == true)
                {
                    try
                    {
                        if (shellStream.DataAvailable)
                {
                    var bytesRead = await shellStream.ReadAsync(buffer, 0, buffer.Length);
                    if (bytesRead > 0)
                    {
                                var chunk = System.Text.Encoding.UTF8.GetString(buffer, 0, bytesRead);
                                outputBuilder.Append(chunk);
                                
                                // Process output when we have a complete line or after a small delay
                                if (chunk.Contains('\n') || outputBuilder.Length > 1000)
                                {
                                    var output = outputBuilder.ToString();
                                    outputBuilder.Clear();
                                    
                                    if (!cancellationToken.IsCancellationRequested && !isDisconnecting)
                                    {
                                        Dispatcher.Invoke(() => AppendOutput(output));
                                    }
                                }
                            }
                        }
                        else
                        {
                            // If no data available, but we have some in buffer, flush it
                            if (outputBuilder.Length > 0)
                            {
                                var output = outputBuilder.ToString();
                                outputBuilder.Clear();
                            
                                if (!cancellationToken.IsCancellationRequested && !isDisconnecting)
                                {
                                    Dispatcher.Invoke(() => AppendOutput(output));
                                }
                            }
                        
                            // Check for cancellation before delay
                            if (cancellationToken.IsCancellationRequested || isDisconnecting)
                                break;
                                
                            await Task.Delay(100, cancellationToken); // Longer delay when no data available
                        }
                    }
                    catch (ObjectDisposedException)
                    {
                        // SSH objects have been disposed, exit gracefully
                        break;
                    }
                    catch (OperationCanceledException)
                    {
                        // Cancellation requested, exit gracefully
                        break;
                    }
                    catch (Exception ex)
                    {
                        if (!cancellationToken.IsCancellationRequested && !isDisconnecting)
                        {
                            Dispatcher.Invoke(() => UpdateStatus($"Read error: {ex.Message}"));
                        }
                        break;
                    }
                }
            }
            catch (OperationCanceledException)
            {
                // Expected when cancellation is requested
            }
            catch (ObjectDisposedException)
            {
                // Expected when SSH objects are disposed
            }
            catch (Exception ex)
            {
                if (!cancellationToken.IsCancellationRequested && !isDisconnecting)
            {
                Dispatcher.Invoke(() => UpdateStatus($"Read error: {ex.Message}"));
                }
            }
            finally
            {
                // Flush any remaining output
                if (outputBuilder.Length > 0 && !cancellationToken.IsCancellationRequested && !isDisconnecting)
                {
                    var output = outputBuilder.ToString();
                    try
                    {
                        Dispatcher.Invoke(() => AppendOutput(output));
                    }
                    catch
                    {
                        // Ignore errors during cleanup
                    }
                }
            }
        }

        private void AppendOutput(string text)
        {
            // Process ANSI escape codes and format text appropriately
            ProcessAndAppendText(text);
            txtOutput.ScrollToEnd();
        }

        private void AppendTerminalText(string text, Color? color = null)
        {
            // TextBox doesn't support multiple colors, so we'll use simple prefixes for message types
            if (color.HasValue)
            {
                var colorIndicator = color.Value.ToString() switch
                {
                    var c when c.Contains("Red") => "[ERR] ",
                    var c when c.Contains("Yellow") => "[WARN] ",
                    var c when c.Contains("Green") || c.Contains("LightGreen") => "[OK] ",
                    var c when c.Contains("Cyan") => "[INFO] ",
                    var c when c.Contains("Gray") || c.Contains("DarkGray") => "[LOG] ",
                    var c when c.Contains("Orange") => "[SYS] ",
                    _ => ""
                };
                
                txtOutput.AppendText(colorIndicator + text);
            }
            else
        {
            txtOutput.AppendText(text);
            }
            
            txtOutput.ScrollToEnd();
        }

        private void ProcessAndAppendText(string text)
        {
            // Remove ANSI escape sequences for cleaner output
            var cleanText = Regex.Replace(text, @"\x1B\[[0-9;]*[a-zA-Z]", "");
            
            // Color code different types of messages
            var lines = cleanText.Split('\n');
            foreach (var line in lines)
            {
                if (string.IsNullOrEmpty(line)) continue;
                
                Color textColor = Colors.LimeGreen; // Default terminal green
                
                // Error messages in red
                if (line.Contains("Error") || line.Contains("error") || line.Contains("failed") || 
                    line.Contains("ERROR") || line.Contains("FAILED") || line.Contains("Invalid"))
                {
                    textColor = Colors.Red;
                }
                // Warning messages in yellow
                else if (line.Contains("Warning") || line.Contains("warning") || line.Contains("WARN"))
                {
                    textColor = Colors.Yellow;
                }
                // Success messages in bright green
                else if (line.Contains("Success") || line.Contains("success") || line.Contains("OK") || 
                         line.Contains("Connected") || line.Contains("enabled"))
                {
                    textColor = Colors.LightGreen;
                }
                // Prompts and important info in cyan
                else if (line.Contains("#") || line.Contains(">") || line.Contains("$"))
                {
                    textColor = Colors.Cyan;
                }
                
                AppendTerminalText(line + "\n", textColor);
            }
        }

        private void UpdateStatus(string message)
        {
            txtStatus.Text = $"Status: {message}";
        }

        private void BtnSwitchManager_Click(object sender, RoutedEventArgs e)
        {
            try
        {
            if (sshClient?.IsConnected != true)
            {
                MessageBox.Show("Please connect to SSH first!", "Not Connected", 
                              MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var switchManager = new SwitchPortManager(sshClient, txtHost.Text, txtUsername.Text, txtPassword.Password);
            switchManager.Show();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"❌ FAILED TO OPEN SWITCH MANAGER\n\nError: {ex.Message}", 
                              "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void BtnSwitchInfo_Click(object sender, RoutedEventArgs e)
        {
            try
        {
                // SSH bağlantı durumunu kontrol et
                if (sshClient?.IsConnected != true)
            {
                MessageBox.Show("❌ SSH BAĞLANTISI YOK\n\nSwitch bilgilerini almak için önce SSH bağlantısı kurmalısınız.", 
                              "SSH Gerekli", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

                // SSH nesnesinin dispose edilip edilmediğini kontrol et
                try
                {
                    var testResult = sshClient.ConnectionInfo?.Host;
                    if (string.IsNullOrEmpty(testResult))
                    {
                        throw new ObjectDisposedException("SSH bağlantısı artık geçerli değil");
                    }
                }
                catch (ObjectDisposedException)
                {
                    MessageBox.Show("❌ SSH BAĞLANTISI GEÇERSİZ\n\nSSH bağlantısı kapatılmış durumda. Lütfen yeniden bağlanın.", 
                                  "Bağlantı Hatası", MessageBoxButton.OK, MessageBoxImage.Error);
                    UpdateStatus("SSH bağlantısı geçersiz - yeniden bağlanın");
                    return;
                }

                btnSwitchInfo.IsEnabled = false;
                btnSwitchInfo.Content = "📊 Yükleniyor...";
                UpdateStatus("Switch bilgileri alınıyor...");

                // Yeni bir SSH bağlantısı ile SwitchPortManager oluştur (güvenli yöntem)
                var tempManager = new SwitchPortManager(sshClient, txtHost.Text, txtUsername.Text, txtPassword.Password);
                var systemInfo = await tempManager.GetSwitchSystemInfo();

                // Switch Info dialogunu göster
                var infoDialog = new SwitchInfoDialog(systemInfo);
                infoDialog.Owner = this;
                infoDialog.ShowDialog();

                UpdateStatus("Switch bilgileri başarıyla yüklendi");
            }
            catch (ObjectDisposedException ex)
            {
                MessageBox.Show($"❌ SSH BAĞLANTISI GEÇERSİZ\n\nSSH bağlantı nesnesi kapatılmış durumda.\n\nHata: {ex.Message}\n\nÇözüm: Disconnect butonuna tıklayıp yeniden bağlanın.", 
                              "Bağlantı Hatası", MessageBoxButton.OK, MessageBoxImage.Error);
                UpdateStatus("SSH bağlantısı geçersiz - yeniden bağlanmalısınız");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"❌ SWITCH BİLGİSİ ALINAMADI\n\nHata: {ex.Message}\n\nÇözüm öneri:\n• Yeniden bağlanmayı deneyin\n• Switch IP adresini kontrol edin", 
                              "Hata", MessageBoxButton.OK, MessageBoxImage.Error);
                UpdateStatus($"Switch bilgisi alma hatası: {ex.Message}");
            }
            finally
            {
                btnSwitchInfo.IsEnabled = true;
                btnSwitchInfo.Content = "ℹ️ Switch Info";
            }
        }

        // Quick Command Event Handlers
        private void BtnQuickCommand_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is string command)
            {
                ExecuteQuickCommand(command);
            }
        }

        private void BtnPingTrace_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is string commandType)
            {
                var targetIP = commandType == "ping" ? txtPingIP.Text.Trim() : txtTraceIP.Text.Trim();
                
                if (string.IsNullOrEmpty(targetIP))
                {
                    AppendTerminalText("❌ Please enter an IP address\n", Colors.Red);
                    return;
                }
                
                var command = $"{commandType} {targetIP}";
                ExecuteQuickCommand(command);
            }
        }

        private async void ExecuteQuickCommand(string command)
        {
            try
            {
                if (sshClient?.IsConnected != true)
            {
                    MessageBox.Show("Please connect to SSH first!", "Not Connected", 
                                  MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
                
                // Add command to input and send it
                txtCommand.Text = command;
                await SendCommand();
                    }
                    catch (Exception ex)
                    {
                UpdateStatus($"Quick command error: {ex.Message}");
                AppendTerminalText($"❌ Quick command failed: {ex.Message}\n", Colors.Red);
            }
        }

        protected override void OnClosed(EventArgs e)
        {
            try
            {
                // 🔥 Ana uygulama monitoring timer'ını durdur
                mainAppMonitorTimer?.Stop();
                mainAppMonitorTimer = null;
                
                // Cancel background tasks
                readCancellationTokenSource?.Cancel();
                
                // Wait a moment for tasks to stop
                Thread.Sleep(200);
                
                // Cleanup SSH resources
                CleanupSshResources();
                
                // Firebase cleanup
                if (firebaseService != null)
                {
                _ = Task.Run(async () =>
                {
                    try
                    {
                            await firebaseService.PushUsageStats("Application_Closed", 
                                $"SwappC closed on {Environment.MachineName}");
                    }
                        catch (Exception fbEx)
                    {
                            System.Diagnostics.Debug.WriteLine($"Firebase app close log failed: {fbEx.Message}");
                    }
                });
                }
                
                base.OnClosed(e);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Window close cleanup error: {ex.Message}");
            base.OnClosed(e);
            }
        }
    }
} 