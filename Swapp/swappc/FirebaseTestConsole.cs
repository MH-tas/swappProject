using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SwappC
{
    // Firebase Database Test Console - Firebase veritabanının yapısını test etmek için
    public class FirebaseTestConsole
    {
        public static async Task TestFirebaseIntegration()
        {
            Console.WriteLine("🔥 Firebase Database Test Started...");
            Console.WriteLine("=====================================");

            var firebaseService = new FirebaseService();

            try
            {
                // 1. Test Switch Information Push
                Console.WriteLine("1. Testing Switch Info Push...");
                var testSwitchInfo = new SwitchSystemInfo
                {
                    IosVersion = "Cisco IOS XE Software, Version 16.12.04",
                    ModelNumber = "Catalyst 2960-48TT-L",
                    SerialNumber = "FCW1234A5BC",
                    MacAddress = "00:1A:2B:3C:4D:5E",
                    Temperature = "45°C (Normal)",
                    Uptime = "1 week, 3 days, 12 hours, 45 minutes",
                    CpuUsage = "15% (Good)",
                    MemoryUsage = "45% (Normal)",
                    PowerStatus = "✅ All Power Supplies OK",
                    PowerConsumption = "180W (Efficient)",
                    FanStatus = "✅ All 3 Fan(s) OK",
                    LastUpdated = DateTime.UtcNow,
                    ErrorMessage = ""
                };

                bool switchInfoResult = await firebaseService.PushSwitchInfo(testSwitchInfo, "192.168.1.100");
                Console.WriteLine($"   Switch Info Push: {(switchInfoResult ? "✅ SUCCESS" : "❌ FAILED")}");

                // 2. Test Port Status Push
                Console.WriteLine("2. Testing Port Status Push...");
                var testPortStatus = new Dictionary<string, PortStatus>
                {
                    ["Gi1/0/1"] = new PortStatus { Name = "Gi1/0/1", Status = "connected", IsUp = true, IsDown = false, IsShutdown = false },
                    ["Gi1/0/2"] = new PortStatus { Name = "Gi1/0/2", Status = "notconnect", IsUp = false, IsDown = true, IsShutdown = false },
                    ["Gi1/0/3"] = new PortStatus { Name = "Gi1/0/3", Status = "disabled", IsUp = false, IsDown = false, IsShutdown = true },
                    ["Gi1/0/4"] = new PortStatus { Name = "Gi1/0/4", Status = "connected", IsUp = true, IsDown = false, IsShutdown = false }
                };

                bool portStatusResult = await firebaseService.PushPortStatus(testPortStatus, "192.168.1.100");
                Console.WriteLine($"   Port Status Push: {(portStatusResult ? "✅ SUCCESS" : "❌ FAILED")}");

                // 3. Test VLAN Information Push
                Console.WriteLine("3. Testing VLAN Info Push...");
                string testVlanData = @"
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Gi1/0/1, Gi1/0/5, Gi1/0/6, Gi1/0/7
10   MANAGEMENT                       active    Gi1/0/2, Gi1/0/3
20   GUEST_NETWORK                    active    Gi1/0/4
100  SERVERS                          active    Gi1/0/48
";

                bool vlanResult = await firebaseService.PushVlanInfo("192.168.1.100", testVlanData);
                Console.WriteLine($"   VLAN Info Push: {(vlanResult ? "✅ SUCCESS" : "❌ FAILED")}");

                // 4. Test Interface Information Push
                Console.WriteLine("4. Testing Interface Info Push...");
                string testInterfaceData = @"
Interface              IP-Address      OK? Method Status                Protocol
GigabitEthernet1/0/1   unassigned      YES unset  up                    up      
GigabitEthernet1/0/2   unassigned      YES unset  down                  down    
GigabitEthernet1/0/3   unassigned      YES unset  administratively down down    
Vlan1                  192.168.1.100   YES NVRAM  up                    up      
Vlan10                 10.0.10.1       YES NVRAM  up                    up      
";

                bool interfaceResult = await firebaseService.PushInterfaceInfo("192.168.1.100", testInterfaceData);
                Console.WriteLine($"   Interface Info Push: {(interfaceResult ? "✅ SUCCESS" : "❌ FAILED")}");

                // 5. Test Connection Information Push
                Console.WriteLine("5. Testing Connection Info Push...");
                bool connectionResult = await firebaseService.PushConnectionInfo("192.168.1.100", "admin", true, 
                    "Online - 24/48 ports active - Test connection");
                Console.WriteLine($"   Connection Info Push: {(connectionResult ? "✅ SUCCESS" : "❌ FAILED")}");

                // 6. Test Command Log Push
                Console.WriteLine("6. Testing Command Log Push...");
                bool commandResult = await firebaseService.PushCommandLog("show version", 
                    "Cisco IOS Software, C2960 Software...", "192.168.1.100", "TestCommand");
                Console.WriteLine($"   Command Log Push: {(commandResult ? "✅ SUCCESS" : "❌ FAILED")}");

                // 7. Test Network Discovery Push
                Console.WriteLine("7. Testing Network Discovery Push...");
                var discoveryData = new List<string>
                {
                    "CDP: Device ID: Router-01, Platform: cisco ISR4331, Capabilities: Router",
                    "LLDP: System Name: Switch-02, System Description: Cisco Catalyst 2960"
                };
                bool discoveryResult = await firebaseService.PushNetworkDiscovery("192.168.1.100", discoveryData);
                Console.WriteLine($"   Network Discovery Push: {(discoveryResult ? "✅ SUCCESS" : "❌ FAILED")}");

                // 8. Test Usage Statistics Push
                Console.WriteLine("8. Testing Usage Stats Push...");
                bool usageResult = await firebaseService.PushUsageStats("Firebase_Test_Completed", 
                    "Firebase database test completed successfully");
                Console.WriteLine($"   Usage Stats Push: {(usageResult ? "✅ SUCCESS" : "❌ FAILED")}");

                Console.WriteLine("\n🎉 Firebase Database Test Completed!");
                Console.WriteLine("=====================================");
                Console.WriteLine("📊 Database Structure Created:");
                Console.WriteLine("   📁 NetworkDevices/");
                Console.WriteLine("      📁 Switches/");
                Console.WriteLine("         📁 192_168_1_100/");
                Console.WriteLine("            📄 SystemInfo");
                Console.WriteLine("            📄 Ports/");
                Console.WriteLine("            📄 VlanInfo");
                Console.WriteLine("            📄 InterfaceInfo");
                Console.WriteLine("            📄 ConnectionInfo");
                Console.WriteLine("            📄 CommandHistory/");
                Console.WriteLine("            📄 NetworkDiscovery");
                Console.WriteLine("   📁 ApplicationUsage/");
                Console.WriteLine("      📁 {DeviceId}/");
                Console.WriteLine("         📄 {Usage Logs}");
                
            }
            catch (Exception ex)
            {
                Console.WriteLine($"❌ Firebase Test Failed: {ex.Message}");
                Console.WriteLine($"Stack Trace: {ex.StackTrace}");
            }
            finally
            {
                firebaseService?.Dispose();
            }
        }

        // Firebase Database Kategorize Edilmiş Yapı Açıklaması
        public static void ShowDatabaseStructure()
        {
            Console.WriteLine("🔥 Firebase Realtime Database - SwappC Yapısı");
            Console.WriteLine("==============================================");
            Console.WriteLine();
            Console.WriteLine("📊 VERİTABANI YAPISI:");
            Console.WriteLine();
            Console.WriteLine("📁 NetworkDevices/");
            Console.WriteLine("  📁 Switches/");
            Console.WriteLine("    📁 {SwitchIP_Replaced}/           # IP adresindeki noktalar _ ile değiştirilir");
            Console.WriteLine("      📄 SystemInfo/                 # Switch sistem bilgileri");
            Console.WriteLine("        - IosVersion                 # IOS versiyonu");
            Console.WriteLine("        - ModelNumber                # Model numarası");
            Console.WriteLine("        - SerialNumber               # Seri numarası");
            Console.WriteLine("        - MacAddress                 # MAC adresi");
            Console.WriteLine("        - Temperature                # Sıcaklık bilgisi");
            Console.WriteLine("        - Uptime                     # Çalışma süresi");
            Console.WriteLine("        - CpuUsage                   # CPU kullanımı");
            Console.WriteLine("        - MemoryUsage                # Bellek kullanımı");
            Console.WriteLine("        - PowerStatus                # Güç durumu");
            Console.WriteLine("        - FanStatus                  # Fan durumu");
            Console.WriteLine("        - LastUpdated                # Son güncelleme");
            Console.WriteLine();
            Console.WriteLine("      📁 Ports/                     # Port durumları");
            Console.WriteLine("        📄 Gi1_0_1/                 # Her port için ayrı kayıt");
            Console.WriteLine("          - PortName                 # Port adı");
            Console.WriteLine("          - Status                   # connected/notconnect/disabled");
            Console.WriteLine("          - IsUp                     # Açık mı?");
            Console.WriteLine("          - IsDown                   # Kapalı mı?");
            Console.WriteLine("          - IsShutdown               # Devre dışı mı?");
            Console.WriteLine("          - LastUpdated              # Son güncelleme");
            Console.WriteLine();
            Console.WriteLine("      📄 VlanInfo/                  # VLAN bilgileri");
            Console.WriteLine("        - VlanData                  # show vlan brief çıktısı");
            Console.WriteLine("        - LastUpdated               # Son güncelleme");
            Console.WriteLine();
            Console.WriteLine("      📄 InterfaceInfo/             # Interface bilgileri");
            Console.WriteLine("        - InterfaceData             # show ip interface brief çıktısı");
            Console.WriteLine("        - LastUpdated               # Son güncelleme");
            Console.WriteLine();
            Console.WriteLine("      📄 ConnectionInfo/            # Bağlantı bilgileri");
            Console.WriteLine("        - IsConnected               # Bağlı mı?");
            Console.WriteLine("        - Username                  # Kullanıcı adı");
            Console.WriteLine("        - ConnectionDetails         # Bağlantı detayları");
            Console.WriteLine("        - LastConnectionAttempt     # Son bağlantı denemesi");
            Console.WriteLine();
            Console.WriteLine("      📁 CommandHistory/            # Komut geçmişi");
            Console.WriteLine("        📄 {CommandId}/             # Her komut için unique ID");
            Console.WriteLine("          - Command                 # Çalıştırılan komut");
            Console.WriteLine("          - Response                # Komut yanıtı");
            Console.WriteLine("          - ActionType              # ManualCommand/QuickCommand/Port_Enable vb.");
            Console.WriteLine("          - Timestamp               # Komut zamanı");
            Console.WriteLine();
            Console.WriteLine("      📄 NetworkDiscovery/          # Ağ keşif bilgileri");
            Console.WriteLine("        - DiscoveredNetworks        # CDP/LLDP komşu bilgileri");
            Console.WriteLine("        - DiscoveryTimestamp        # Keşif zamanı");
            Console.WriteLine();
            Console.WriteLine("📁 ApplicationUsage/               # Uygulama kullanım istatistikleri");
            Console.WriteLine("  📁 {DeviceId}/                   # Cihaz ID (MachineName_Date)");
            Console.WriteLine("    📄 {UsageId}/                  # Her aktivite için unique ID");
            Console.WriteLine("      - Action                     # Yapılan işlem");
            Console.WriteLine("      - Details                    # İşlem detayları");
            Console.WriteLine("      - Timestamp                  # İşlem zamanı");
            Console.WriteLine();
            Console.WriteLine("🎯 ANAHTAR ÖZELLİKLER:");
            Console.WriteLine("  ✅ Switch'lerin online/offline durumu");
            Console.WriteLine("  ✅ Port durumları (açık/kapalı/devre dışı)");
            Console.WriteLine("  ✅ VLAN konfigürasyonları");
            Console.WriteLine("  ✅ Interface IP bilgileri");
            Console.WriteLine("  ✅ Sistem performans metrikleri");
            Console.WriteLine("  ✅ Komut geçmişi ve aktivite logları");
            Console.WriteLine("  ✅ Ağ keşif bilgileri (CDP/LLDP)");
            Console.WriteLine("  ✅ Uygulama kullanım istatistikleri");
        }
    }
} 