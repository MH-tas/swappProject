using System.Net;
using Lextm.SharpSnmpLib;
using Lextm.SharpSnmpLib.Messaging;
using System.Windows.Forms.DataVisualization.Charting;

namespace CiscoSNMPMonitor
{
    public partial class MainForm : Form
    {
        private IPEndPoint? endpoint;
        private System.Windows.Forms.Timer? refreshTimer;
        private bool isConnected = false;
        private Dictionary<string, List<double>> trafficHistory = new Dictionary<string, List<double>>();
        private Dictionary<string, long> lastInOctets = new Dictionary<string, long>();
        private Dictionary<string, long> lastOutOctets = new Dictionary<string, long>();

        // SNMP OID'leri
        private static readonly string OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0";
        private static readonly string OID_SYS_UPTIME = "1.3.6.1.2.1.1.3.0";
        private static readonly string OID_SYS_NAME = "1.3.6.1.2.1.1.5.0";
        private static readonly string OID_SYS_LOCATION = "1.3.6.1.2.1.1.6.0";
        private static readonly string OID_SYS_CONTACT = "1.3.6.1.2.1.1.4.0";
        private static readonly string OID_IF_NUMBER = "1.3.6.1.2.1.2.1.0";
        private static readonly string OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2";
        private static readonly string OID_IF_TYPE = "1.3.6.1.2.1.2.2.1.3";
        private static readonly string OID_IF_MTU = "1.3.6.1.2.1.2.2.1.4";
        private static readonly string OID_IF_SPEED = "1.3.6.1.2.1.2.2.1.5";
        private static readonly string OID_IF_PHYS_ADDR = "1.3.6.1.2.1.2.2.1.6";
        private static readonly string OID_IF_ADMIN_STATUS = "1.3.6.1.2.1.2.2.1.7";
        private static readonly string OID_IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8";
        private static readonly string OID_IF_IN_OCTETS = "1.3.6.1.2.1.2.2.1.10";
        private static readonly string OID_IF_OUT_OCTETS = "1.3.6.1.2.1.2.2.1.16";
        private static readonly string OID_IF_IN_ERRORS = "1.3.6.1.2.1.2.2.1.14";
        private static readonly string OID_IF_OUT_ERRORS = "1.3.6.1.2.1.2.2.1.20";
        private static readonly string OID_IF_IN_DISCARDS = "1.3.6.1.2.1.2.2.1.13";
        private static readonly string OID_IF_OUT_DISCARDS = "1.3.6.1.2.1.2.2.1.19";
        private static readonly string OID_CPU_USAGE = "1.3.6.1.4.1.9.9.109.1.1.1.1.5.1";
        private static readonly string OID_MEMORY_USED = "1.3.6.1.4.1.9.9.48.1.1.1.5.1";
        private static readonly string OID_MEMORY_FREE = "1.3.6.1.4.1.9.9.48.1.1.1.6.1";
        private static readonly string OID_TEMPERATURE = "1.3.6.1.4.1.9.9.13.1.3.1.3.1";
        private static readonly string OID_FAN_STATUS = "1.3.6.1.4.1.9.9.13.1.4.1.3";
        private static readonly string OID_POWER_STATUS = "1.3.6.1.4.1.9.9.13.1.5.1.3";

        public MainForm()
        {
            InitializeComponent();
            SetupInterfaceListView();
            SetupEventHandlers();
            SetupCharts();
            interfaceListView.Location = new Point(12, 255);
            interfaceListView.Size = new Size(978, 294);

            // Varsayılan değerleri ayarla
            txtIP.Text = "192.168.20.1";
            txtPort.Text = "161";
            txtCommunity.Text = "swapp";
            autoRefreshCheckBox.Checked = true;
            refreshIntervalNumeric.Value = 5;
        }

        private void SetupCharts()
        {
            // CPU Kullanım Grafiği
            cpuChart.Series.Clear();
            var cpuSeries = new Series("CPU");
            cpuSeries.ChartType = SeriesChartType.Line;
            cpuChart.Series.Add(cpuSeries);
            cpuChart.ChartAreas[0].AxisY.Maximum = 100;
            cpuChart.ChartAreas[0].AxisY.Minimum = 0;

            // Bellek Kullanım Grafiği
            memoryChart.Series.Clear();
            var memorySeries = new Series("Memory");
            memorySeries.ChartType = SeriesChartType.Pie;
            memoryChart.Series.Add(memorySeries);

            // Trafik Grafiği
            trafficChart.Series.Clear();
            var inSeries = new Series("In");
            var outSeries = new Series("Out");
            inSeries.ChartType = SeriesChartType.Line;
            outSeries.ChartType = SeriesChartType.Line;
            trafficChart.Series.Add(inSeries);
            trafficChart.Series.Add(outSeries);
        }

        private void SetupEventHandlers()
        {
            btnConnect.Click += BtnConnect_Click;
            btnTest.Click += BtnTest_Click;
            autoRefreshCheckBox.CheckedChanged += AutoRefreshCheckBox_CheckedChanged;
            refreshIntervalNumeric.ValueChanged += RefreshIntervalNumeric_ValueChanged;
            this.FormClosing += MainForm_FormClosing;
        }

        private void SetupInterfaceListView()
        {
            interfaceListView.Columns.Clear();
            interfaceListView.Columns.Add("Port", 50);
            interfaceListView.Columns.Add("Açıklama", 150);
            interfaceListView.Columns.Add("Tip", 80);
            interfaceListView.Columns.Add("Hız", 80);
            interfaceListView.Columns.Add("MAC Adresi", 120);
            interfaceListView.Columns.Add("Admin Durum", 80);
            interfaceListView.Columns.Add("Operasyon Durum", 80);
            interfaceListView.Columns.Add("Gelen Trafik", 100);
            interfaceListView.Columns.Add("Giden Trafik", 100);
            interfaceListView.Columns.Add("Hatalar (In/Out)", 100);
            interfaceListView.Columns.Add("Discards (In/Out)", 100);
        }

        private void SetupRefreshTimer()
        {
            if (refreshTimer != null)
            {
                refreshTimer.Stop();
                refreshTimer.Dispose();
            }

            refreshTimer = new System.Windows.Forms.Timer();
            refreshTimer.Interval = (int)refreshIntervalNumeric.Value * 1000;
            refreshTimer.Tick += async (sender, e) => await RefreshAllData();
        }

        private async void BtnConnect_Click(object sender, EventArgs e)
        {
            try
            {
                if (!isConnected)
                {
                    btnConnect.Enabled = false;
                    btnConnect.Text = "Bağlanıyor...";
                    await Connect();
                    btnConnect.Text = "BAĞLANTIYI KES";
                    btnConnect.BackColor = Color.FromArgb(255, 68, 68);
                }
                else
                {
                    Disconnect();
                    btnConnect.Text = "BAĞLAN";
                    btnConnect.BackColor = Color.FromArgb(0, 122, 204);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Bağlantı hatası: {ex.Message}", "Hata", MessageBoxButtons.OK, MessageBoxIcon.Error);
                Disconnect();
            }
            finally
            {
                btnConnect.Enabled = true;
            }
        }

        private async void BtnTest_Click(object sender, EventArgs e)
        {
            btnTest.Enabled = false;
            btnTest.Text = "Test Ediliyor...";
            
            try
            {
                var testEndpoint = new IPEndPoint(IPAddress.Parse(txtIP.Text), int.Parse(txtPort.Text));
                var result = await Messenger.GetAsync(VersionCode.V2,
                    testEndpoint,
                    new OctetString(txtCommunity.Text),
                    new List<Variable> { new Variable(new ObjectIdentifier(OID_SYS_NAME)) });

                MessageBox.Show($"Bağlantı başarılı!\nCihaz adı: {result[0].Data}", "Test Başarılı", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Bağlantı hatası: {ex.Message}", "Test Başarısız", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                btnTest.Enabled = true;
                btnTest.Text = "BAĞLANTIYI TEST ET";
            }
        }

        private async Task Connect()
        {
            try
            {
                endpoint = new IPEndPoint(IPAddress.Parse(txtIP.Text), int.Parse(txtPort.Text));
                await RefreshAllData();
                
                isConnected = true;
                EnableControls(false);
                SetupRefreshTimer();

                if (autoRefreshCheckBox.Checked && refreshTimer != null)
                {
                    refreshTimer.Start();
                }
            }
            catch (Exception ex)
            {
                throw new Exception($"Bağlantı kurulamadı: {ex.Message}");
            }
        }

        private void Disconnect()
        {
            if (refreshTimer != null)
            {
                refreshTimer.Stop();
                refreshTimer.Dispose();
                refreshTimer = null;
            }

            isConnected = false;
            endpoint = null;
            EnableControls(true);
            ClearData();
        }

        private void EnableControls(bool enable)
        {
            txtIP.Enabled = enable;
            txtPort.Enabled = enable;
            txtCommunity.Enabled = enable;
            btnTest.Enabled = enable;
        }

        private void ClearData()
        {
            systemNameLabel.Text = "Switch Adı";
            systemDescTextBox.Text = "";
            interfaceListView.Items.Clear();
            statusStrip.Items["statusLabel"].Text = "Bağlantı kesildi";
            uptimeLabel.Text = "Uptime: -";
            locationLabel.Text = "Konum: -";
            contactLabel.Text = "İletişim: -";
            cpuChart.Series[0].Points.Clear();
            memoryChart.Series[0].Points.Clear();
            trafficChart.Series[0].Points.Clear();
            trafficChart.Series[1].Points.Clear();
            temperatureLabel.Text = "Sıcaklık: -";
            fanStatusLabel.Text = "Fan Durumu: -";
            powerStatusLabel.Text = "Güç Durumu: -";
        }

        private async Task RefreshAllData()
        {
            if (endpoint == null) return;

            try
            {
                await GetSystemInfo();
                await GetInterfaceInfo();
                await GetSystemMetrics();
                statusStrip.Items["statusLabel"].Text = "Son Güncelleme: " + DateTime.Now.ToString("HH:mm:ss");
            }
            catch (Exception ex)
            {
                statusStrip.Items["statusLabel"].Text = $"Hata: {ex.Message}";
            }
        }

        private async Task GetSystemInfo()
        {
            if (endpoint == null) return;

            try
            {
                var tasks = new[]
                {
                    GetSnmpValue(OID_SYS_DESCR),
                    GetSnmpValue(OID_SYS_NAME),
                    GetSnmpValue(OID_SYS_UPTIME),
                    GetSnmpValue(OID_SYS_LOCATION),
                    GetSnmpValue(OID_SYS_CONTACT)
                };

                var results = await Task.WhenAll(tasks);

                systemNameLabel.Text = $"Switch Adı: {results[1]}";
                systemDescTextBox.Text = results[0];
                uptimeLabel.Text = $"Uptime: {results[2]}";
                locationLabel.Text = $"Konum: {results[3]}";
                contactLabel.Text = $"İletişim: {results[4]}";
            }
            catch (Exception ex)
            {
                statusStrip.Items["statusLabel"].Text = $"Sistem bilgisi alınamadı: {ex.Message}";
            }
        }

        private async Task GetSystemMetrics()
        {
            if (endpoint == null) return;

            try
            {
                var tasks = new[]
                {
                    GetSnmpValue(OID_CPU_USAGE),
                    GetSnmpValue(OID_MEMORY_USED),
                    GetSnmpValue(OID_MEMORY_FREE),
                    GetSnmpValue(OID_TEMPERATURE),
                    GetSnmpValue(OID_FAN_STATUS),
                    GetSnmpValue(OID_POWER_STATUS)
                };

                var results = await Task.WhenAll(tasks);

                // CPU Kullanımı
                if (int.TryParse(results[0], out int cpuUsage))
                {
                    UpdateCpuChart(cpuUsage);
                }

                // Bellek Kullanımı
                if (long.TryParse(results[1], out long memUsed) && long.TryParse(results[2], out long memFree))
                {
                    UpdateMemoryChart(memUsed, memFree);
                }

                // Sıcaklık
                temperatureLabel.Text = $"Sıcaklık: {results[3]}°C";

                // Fan Durumu
                fanStatusLabel.Text = $"Fan Durumu: {(results[4] == "1" ? "Normal" : "Kritik")}";

                // Güç Durumu
                powerStatusLabel.Text = $"Güç Durumu: {(results[5] == "1" ? "Normal" : "Kritik")}";
            }
            catch (Exception ex)
            {
                statusStrip.Items["statusLabel"].Text = $"Sistem metrikleri alınamadı: {ex.Message}";
            }
        }

        private void UpdateCpuChart(int cpuUsage)
        {
            var series = cpuChart.Series[0];
            series.Points.AddY(cpuUsage);
            if (series.Points.Count > 30)
                series.Points.RemoveAt(0);
        }

        private void UpdateMemoryChart(long used, long free)
        {
            var series = memoryChart.Series[0];
            series.Points.Clear();
            series.Points.AddXY("Kullanılan", used);
            series.Points.AddXY("Boş", free);
        }

        private async Task GetInterfaceInfo()
        {
            if (endpoint == null) return;

            try
            {
                interfaceListView.Items.Clear();
                for (int i = 1; i <= 48; i++)
                {
                    try
                    {
                        var tasks = new[]
                        {
                            GetSnmpValue($"{OID_IF_DESCR}.{i}"),
                            GetSnmpValue($"{OID_IF_TYPE}.{i}"),
                            GetSnmpValue($"{OID_IF_SPEED}.{i}"),
                            GetSnmpValue($"{OID_IF_PHYS_ADDR}.{i}"),
                            GetSnmpValue($"{OID_IF_ADMIN_STATUS}.{i}"),
                            GetSnmpValue($"{OID_IF_OPER_STATUS}.{i}"),
                            GetSnmpValue($"{OID_IF_IN_OCTETS}.{i}"),
                            GetSnmpValue($"{OID_IF_OUT_OCTETS}.{i}"),
                            GetSnmpValue($"{OID_IF_IN_ERRORS}.{i}"),
                            GetSnmpValue($"{OID_IF_OUT_ERRORS}.{i}"),
                            GetSnmpValue($"{OID_IF_IN_DISCARDS}.{i}"),
                            GetSnmpValue($"{OID_IF_OUT_DISCARDS}.{i}")
                        };

                        var results = await Task.WhenAll(tasks);

                        string adminStatus = results[4] == "1" ? "Up" : "Down";
                        string operStatus = results[5] == "1" ? "Up" : "Down";
                        string speed = FormatSpeed(results[2]);

                        // Trafik hesaplama
                        if (long.TryParse(results[6], out long inOctets) && long.TryParse(results[7], out long outOctets))
                        {
                            string portKey = $"Port{i}";
                            string inTraffic = "0";
                            string outTraffic = "0";
                            long inDiff = 0;
                            long outDiff = 0;

                            if (lastInOctets.ContainsKey(portKey) && lastOutOctets.ContainsKey(portKey))
                            {
                                inDiff = inOctets - lastInOctets[portKey];
                                outDiff = outOctets - lastOutOctets[portKey];
                                
                                if (refreshTimer != null)
                                {
                                    inTraffic = FormatSpeed($"{inDiff / refreshTimer.Interval * 1000 * 8}"); // bps
                                    outTraffic = FormatSpeed($"{outDiff / refreshTimer.Interval * 1000 * 8}"); // bps
                                }

                                if (!trafficHistory.ContainsKey(portKey))
                                    trafficHistory[portKey] = new List<double>();

                                trafficHistory[portKey].Add(inDiff);
                                if (trafficHistory[portKey].Count > 30)
                                    trafficHistory[portKey].RemoveAt(0);
                            }

                            lastInOctets[portKey] = inOctets;
                            lastOutOctets[portKey] = outOctets;

                            var item = new ListViewItem(new[]
                            {
                                i.ToString(),
                                results[0],
                                GetInterfaceType(results[1]),
                                speed,
                                FormatMacAddress(results[3]),
                                adminStatus,
                                operStatus,
                                inTraffic + "/s",
                                outTraffic + "/s",
                                $"{results[8]}/{results[9]}",
                                $"{results[10]}/{results[11]}"
                            });

                            if (operStatus == "Up")
                                item.BackColor = Color.LightGreen;
                            else if (adminStatus == "Down")
                                item.BackColor = Color.LightGray;
                            else
                                item.BackColor = Color.LightPink;

                            interfaceListView.Items.Add(item);

                            // Trafik grafiğini güncelle
                            if (i == 1) // Sadece ilk port için grafik göster
                            {
                                UpdateTrafficChart(inDiff, outDiff);
                            }
                        }
                    }
                    catch
                    {
                        continue;
                    }
                }
            }
            catch (Exception ex)
            {
                statusStrip.Items["statusLabel"].Text = $"Interface bilgisi alınamadı: {ex.Message}";
            }
        }

        private void UpdateTrafficChart(long inTraffic, long outTraffic)
        {
            var inSeries = trafficChart.Series[0];
            var outSeries = trafficChart.Series[1];

            inSeries.Points.AddY(inTraffic);
            outSeries.Points.AddY(outTraffic);

            if (inSeries.Points.Count > 30)
            {
                inSeries.Points.RemoveAt(0);
                outSeries.Points.RemoveAt(0);
            }
        }

        private async Task<string> GetSnmpValue(string oid)
        {
            if (endpoint == null) return string.Empty;

            try
            {
                var result = await Messenger.GetAsync(VersionCode.V2,
                    endpoint,
                    new OctetString(txtCommunity.Text),
                    new List<Variable> { new Variable(new ObjectIdentifier(oid)) });

                return result[0].Data.ToString();
            }
            catch
            {
                return string.Empty;
            }
        }

        private string GetInterfaceType(string type)
        {
            switch (type)
            {
                case "1": return "Other";
                case "6": return "Ethernet";
                case "24": return "Loopback";
                case "53": return "Virtual PPP";
                case "131": return "Tunnel";
                case "135": return "L2 VLAN";
                case "136": return "L3 VLAN";
                default: return $"Type {type}";
            }
        }

        private string FormatMacAddress(string mac)
        {
            if (string.IsNullOrEmpty(mac)) return "";
            try
            {
                byte[] bytes = Convert.FromHexString(mac);
                return BitConverter.ToString(bytes).Replace("-", ":");
            }
            catch
            {
                return mac;
            }
        }

        private string FormatSpeed(string speedStr)
        {
            if (long.TryParse(speedStr, out long speed))
            {
                if (speed >= 1000000000) return $"{speed / 1000000000}G";
                if (speed >= 1000000) return $"{speed / 1000000}M";
                if (speed >= 1000) return $"{speed / 1000}K";
                return $"{speed}";
            }
            return speedStr;
        }

        private void AutoRefreshCheckBox_CheckedChanged(object sender, EventArgs e)
        {
            refreshIntervalNumeric.Enabled = autoRefreshCheckBox.Checked;
            if (isConnected && refreshTimer != null)
            {
                if (autoRefreshCheckBox.Checked)
                    refreshTimer.Start();
                else
                    refreshTimer.Stop();
            }
        }

        private void RefreshIntervalNumeric_ValueChanged(object sender, EventArgs e)
        {
            if (isConnected)
                SetupRefreshTimer();
        }

        private void MainForm_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (refreshTimer != null)
            {
                refreshTimer.Stop();
                refreshTimer.Dispose();
            }
        }
    }
} 