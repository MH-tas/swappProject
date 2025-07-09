using System;
using System.Threading.Tasks;
using System.Windows;

namespace SwappC
{
    public partial class SwitchInfoDialog : Window
    {
        private SwitchSystemInfo systemInfo;
        private SwitchPortManager? parentManager;

        public SwitchInfoDialog(SwitchSystemInfo info, SwitchPortManager? parent = null)
        {
            InitializeComponent();
            systemInfo = info;
            parentManager = parent;
            
            // Try to find parent SwitchPortManager for refresh functionality if not provided
            if (parentManager == null && this.Owner is SwitchPortManager manager)
            {
                parentManager = manager;
            }
            
            DisplaySystemInfo();
            UpdateLastUpdateTime();
        }

        private void DisplaySystemInfo()
        {
            if (systemInfo == null)
            {
                ShowError("Switch bilgisi alınamadı - veri eksik");
                return;
            }

            try
            {
                // Basic system information with better Turkish messages
                txtModel.Text = string.IsNullOrEmpty(systemInfo.ModelNumber) ? "🔍 Model bilgisi tespit edilemiyor" : systemInfo.ModelNumber;
                txtSerial.Text = string.IsNullOrEmpty(systemInfo.SerialNumber) ? "🔍 Seri numarası tespit edilemiyor" : systemInfo.SerialNumber;
                txtMac.Text = string.IsNullOrEmpty(systemInfo.MacAddress) ? "🔍 MAC adresi tespit edilemiyor" : systemInfo.MacAddress;
                txtIosVersion.Text = string.IsNullOrEmpty(systemInfo.IosVersion) ? "🔍 IOS versiyonu tespit edilemiyor" : systemInfo.IosVersion;
                
                // Performance metrics with better messages
                txtUptime.Text = string.IsNullOrEmpty(systemInfo.Uptime) ? "📊 Uptime bilgisi alınamıyor" : systemInfo.Uptime;
                txtCpu.Text = string.IsNullOrEmpty(systemInfo.CpuUsage) ? "📊 CPU kullanımı izlenemiyor" : systemInfo.CpuUsage;
                txtMemory.Text = string.IsNullOrEmpty(systemInfo.MemoryUsage) ? "📊 Bellek kullanımı izlenemiyor" : systemInfo.MemoryUsage;
                
                // Environmental information with better messages
                txtTemperature.Text = string.IsNullOrEmpty(systemInfo.Temperature) ? "🌡️ Sıcaklık sensörü okunamıyor" : systemInfo.Temperature;
                txtFanStatus.Text = string.IsNullOrEmpty(systemInfo.FanStatus) ? "💨 Fan durumu kontrol edilemiyor" : systemInfo.FanStatus;
                txtPowerStatus.Text = string.IsNullOrEmpty(systemInfo.PowerStatus) ? "🔋 Güç durumu kontrol edilemiyor" : systemInfo.PowerStatus;
                txtPowerConsumption.Text = string.IsNullOrEmpty(systemInfo.PowerConsumption) ? "⚡ Güç tüketimi ölçülemiyor" : systemInfo.PowerConsumption;

                // Show helpful message if data is not valid
                if (!systemInfo.IsDataValid && string.IsNullOrEmpty(systemInfo.ErrorMessage))
                {
                    ShowError("⚠️ Switch bilgileri eksik - SSH bağlantısı veya komut yanıtları kontrol edilsin. Refresh Data butonuna basarak tekrar deneyin.");
                }
                // Show error message if there's one
                else if (!string.IsNullOrEmpty(systemInfo.ErrorMessage))
                {
                    ShowError(systemInfo.ErrorMessage);
                }
                else
                {
                    HideError();
                }
            }
            catch (Exception ex)
            {
                ShowError($"Switch bilgisi gösterilirken hata: {ex.Message}");
            }
        }

        private void ShowError(string errorMessage)
        {
            errorCard.Visibility = Visibility.Visible;
            txtError.Text = errorMessage;
        }

        private void HideError()
        {
            errorCard.Visibility = Visibility.Collapsed;
        }

        private void UpdateLastUpdateTime()
        {
            if (systemInfo != null && systemInfo.LastUpdated != default(DateTime))
            {
                txtLastUpdate.Text = $"Last Update: {systemInfo.LastUpdated:HH:mm:ss}";
            }
            else
            {
                txtLastUpdate.Text = "Last Update: Just now";
            }
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                this.DialogResult = true;
                this.Close();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"SwitchInfoDialog close error: {ex.Message}");
                // Force close even if there's an error
                try
                {
                    this.Close();
                }
                catch
                {
                    // If even force close fails, just return
                }
            }
        }

        private async void BtnRefresh_Click(object sender, RoutedEventArgs e)
        {
            if (parentManager == null)
            {
                ShowError("❌ Refresh yapılamıyor - parent switch manager mevcut değil. Switch Port Manager'dan bu pencereyi açmanız gerekiyor.");
                return;
            }

            try
            {
                // Disable refresh button and show loading state
                btnRefresh.IsEnabled = false;
                btnRefresh.Content = "🔄 Yenileniyor...";
                txtLastUpdate.Text = "Veriler yenileniyor...";
                HideError();

                // Get fresh system information
                var newSystemInfo = await parentManager.GetSwitchSystemInfo();
                
                if (newSystemInfo != null)
                {
                    systemInfo = newSystemInfo;
                    DisplaySystemInfo();
                    UpdateLastUpdateTime();
                    
                    // Show success message briefly
                    txtLastUpdate.Text = "✅ Veriler başarıyla yenilendi";
                    await Task.Delay(2000);
                    UpdateLastUpdateTime();
                }
                else
                {
                    ShowError("❌ Switch bilgisi alınamadı - null veri döndü");
                }
            }
            catch (Exception ex)
            {
                ShowError($"❌ Refresh hatası: {ex.Message}");
                txtLastUpdate.Text = "❌ Yenileme başarısız";
                System.Diagnostics.Debug.WriteLine($"SwitchInfoDialog refresh error: {ex.Message}");
            }
            finally
            {
                try
                {
                    // Re-enable refresh button
                    btnRefresh.IsEnabled = true;
                    btnRefresh.Content = "🔄 Refresh Data";
                }
                catch (Exception finallyEx)
                {
                    System.Diagnostics.Debug.WriteLine($"SwitchInfoDialog finally block error: {finallyEx.Message}");
                }
            }
        }
    }
} 