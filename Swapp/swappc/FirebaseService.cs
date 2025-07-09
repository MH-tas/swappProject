using Firebase.Database;
using Firebase.Database.Query;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace SwappC
{
    public class FirebaseService
    {
        private readonly FirebaseClient firebaseClient;
        private readonly string deviceId;

        public FirebaseService()
        {
            // Firebase config
            var firebaseConfig = new FirebaseOptions
            {
                AuthTokenAsyncFactory = () => Task.FromResult("")
            };

            firebaseClient = new FirebaseClient(
                "https://swapp-b5339-default-rtdb.europe-west1.firebasedatabase.app/",
                firebaseConfig
            );

            // Unique device identifier
            deviceId = Environment.MachineName + "_" + DateTime.Now.ToString("yyyyMMdd");
        }

        // Push Switch Information to Firebase
        public async Task<bool> PushSwitchInfo(SwitchSystemInfo switchInfo, string switchIP)
        {
            try
            {
                var switchData = new
                {
                    DeviceId = deviceId,
                    SwitchIP = switchIP,
                    ModelNumber = switchInfo.ModelNumber,
                    SerialNumber = switchInfo.SerialNumber,
                    MacAddress = switchInfo.MacAddress,
                    IosVersion = switchInfo.IosVersion,
                    Uptime = switchInfo.Uptime,
                    CpuUsage = switchInfo.CpuUsage,
                    MemoryUsage = switchInfo.MemoryUsage,
                    Temperature = switchInfo.Temperature,
                    FanStatus = switchInfo.FanStatus,
                    PowerStatus = switchInfo.PowerStatus,
                    PowerConsumption = switchInfo.PowerConsumption,
                    LastUpdated = switchInfo.LastUpdated,
                    ErrorMessage = switchInfo.ErrorMessage,
                    Timestamp = DateTime.UtcNow,
                    Category = "SwitchInfo"
                };

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("SystemInfo")
                    .PutAsync(switchData);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Switch Info Push Error: {ex.Message}");
                return false;
            }
        }

        // Push Port Status Information to Firebase
        public async Task<bool> PushPortStatus(Dictionary<string, PortStatus> portStatusDict, string switchIP)
        {
            try
            {
                var portsData = new Dictionary<string, object>();

                foreach (var kvp in portStatusDict)
                {
                    var portData = new
                    {
                        PortName = kvp.Value.Name,
                        Status = kvp.Value.Status,
                        IsUp = kvp.Value.IsUp,
                        IsDown = kvp.Value.IsDown,
                        IsShutdown = kvp.Value.IsShutdown,
                        LastUpdated = DateTime.UtcNow,
                        DeviceId = deviceId,
                        Category = "PortStatus"
                    };

                    portsData[kvp.Key.Replace("/", "_")] = portData;
                }

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("Ports")
                    .PutAsync(portsData);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Port Status Push Error: {ex.Message}");
                return false;
            }
        }

        // Push Command Execution Log to Firebase
        public async Task<bool> PushCommandLog(string command, string response, string switchIP, string actionType = "Command")
        {
            try
            {
                var logData = new
                {
                    DeviceId = deviceId,
                    SwitchIP = switchIP,
                    Command = command,
                    Response = response?.Length > 1000 ? response.Substring(0, 1000) + "..." : response,
                    ActionType = actionType,
                    Timestamp = DateTime.UtcNow,
                    Category = "CommandLog"
                };

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("CommandHistory")
                    .PostAsync(logData);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Command Log Push Error: {ex.Message}");
                return false;
            }
        }

        // Push Connection Information to Firebase
        public async Task<bool> PushConnectionInfo(string switchIP, string username, bool isConnected, string connectionDetails = "")
        {
            try
            {
                var connectionData = new
                {
                    DeviceId = deviceId,
                    SwitchIP = switchIP,
                    Username = username,
                    IsConnected = isConnected,
                    ConnectionDetails = connectionDetails,
                    LastConnectionAttempt = DateTime.UtcNow,
                    Category = "Connection"
                };

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("ConnectionInfo")
                    .PutAsync(connectionData);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Connection Info Push Error: {ex.Message}");
                return false;
            }
        }

        // Push Network Discovery Information to Firebase
        public async Task<bool> PushNetworkDiscovery(string switchIP, List<string> networkData)
        {
            try
            {
                var discoveryData = new
                {
                    DeviceId = deviceId,
                    SwitchIP = switchIP,
                    DiscoveredNetworks = networkData,
                    DiscoveryTimestamp = DateTime.UtcNow,
                    Category = "NetworkDiscovery"
                };

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("NetworkDiscovery")
                    .PutAsync(discoveryData);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Network Discovery Push Error: {ex.Message}");
                return false;
            }
        }

        // Push Application Usage Statistics to Firebase
        public async Task<bool> PushUsageStats(string action, string details = "")
        {
            try
            {
                var usageData = new
                {
                    DeviceId = deviceId,
                    Action = action,
                    Details = details,
                    Timestamp = DateTime.UtcNow,
                    Category = "AppUsage"
                };

                await firebaseClient
                    .Child("ApplicationUsage")
                    .Child(deviceId)
                    .PostAsync(usageData);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Usage Stats Push Error: {ex.Message}");
                return false;
            }
        }

        // Push VLAN Information to Firebase
        public async Task<bool> PushVlanInfo(string switchIP, string vlanData)
        {
            try
            {
                var vlanInfo = new
                {
                    DeviceId = deviceId,
                    SwitchIP = switchIP,
                    VlanData = vlanData,
                    LastUpdated = DateTime.UtcNow,
                    Category = "VlanInfo"
                };

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("VlanInfo")
                    .PutAsync(vlanInfo);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase VLAN Info Push Error: {ex.Message}");
                return false;
            }
        }

        // Push Interface Information to Firebase
        public async Task<bool> PushInterfaceInfo(string switchIP, string interfaceData)
        {
            try
            {
                var interfaceInfo = new
                {
                    DeviceId = deviceId,
                    SwitchIP = switchIP,
                    InterfaceData = interfaceData,
                    LastUpdated = DateTime.UtcNow,
                    Category = "InterfaceInfo"
                };

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("InterfaceInfo")
                    .PutAsync(interfaceInfo);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Interface Info Push Error: {ex.Message}");
                return false;
            }
        }

        // Retrieve data from Firebase (if needed)
        public async Task<T?> GetData<T>(string path)
        {
            try
            {
                var data = await firebaseClient
                    .Child(path)
                    .OnceSingleAsync<T>();

                return data;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Get Data Error: {ex.Message}");
                return default(T);
            }
        }

        // 📱 PHONE COMMAND SİSTEMİ - Firebase'den komutları getir
        public async Task<List<dynamic>?> GetPortCommands(string switchIP)
        {
            try
            {
                Console.WriteLine($"🔥 === FIREBASE KOMUT ÇEKİMİ BAŞLADI ===");
                Console.WriteLine($"🔥 Switch IP: {switchIP}");
                
                var commands = new List<dynamic>();
                
                // Path'i oluştur
                string firebasePath = $"NetworkDevices/Switches/{switchIP.Replace(".", "_")}/PortCommands";
                Console.WriteLine($"🔥 Firebase Path: {firebasePath}");
                
                // Firebase'den PortCommands al
                var firebaseCommands = await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("PortCommands")
                    .OnceAsync<object>();

                Console.WriteLine($"🔥 Firebase Response: {firebaseCommands?.Count ?? 0} komut bulundu");

                if (firebaseCommands != null && firebaseCommands.Count > 0)
                {
                    foreach (var item in firebaseCommands)
                    {
                        Console.WriteLine($"🔥 RAW Firebase Item Key: {item.Key}");
                        Console.WriteLine($"🔥 RAW Firebase Item Object: {JsonConvert.SerializeObject(item.Object, Formatting.Indented)}");
                        
                        // Komut verisini parse et
                        var commandJson = JsonConvert.SerializeObject(item.Object);
                        var commandData = JsonConvert.DeserializeObject<dynamic>(commandJson);
                        
                        // Key'i ekle (silmek için gerekli)
                        commandData.Key = item.Key;
                        
                        Console.WriteLine($"🔥 Parsed Command Data: {JsonConvert.SerializeObject(commandData, Formatting.Indented)}");
                        
                        commands.Add(commandData);
                    }
                }
                else
                {
                    Console.WriteLine($"🔥 ❌ Firebase'de komut bulunamadı veya null response");
                }

                Console.WriteLine($"🔥 TOPLAM {commands.Count} komut döndürülüyor");
                Console.WriteLine($"🔥 === FIREBASE KOMUT ÇEKİMİ BİTTİ ===");
                
                return commands;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"🔥 ❌ FIREBASE KOMUT ÇEKİM HATASI: {ex.Message}");
                Console.WriteLine($"🔥 Stack Trace: {ex.StackTrace}");
                System.Diagnostics.Debug.WriteLine($"Firebase Get Port Commands Error: {ex.Message}");
                return null;
            }
        }

        // 📱 PHONE COMMAND SİSTEMİ - İşlenen komutu Firebase'den sil
        public async Task<bool> DeleteProcessedCommand(string switchIP, string commandKey)
        {
            try
            {
                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("PortCommands")
                    .Child(commandKey)
                    .DeleteAsync();

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Delete Command Error: {ex.Message}");
                return false;
            }
        }

        // 📱 PHONE COMMAND SİSTEMİ - Komut işleme logunu Firebase'e gönder
        public async Task<bool> PushCommandProcessLog(string switchIP, string portName, string command, string result, bool success)
        {
            try
            {
                var logData = new
                {
                    DeviceId = deviceId,
                    SwitchIP = switchIP,
                    PortName = portName,
                    Command = command,
                    Result = result,
                    Success = success,
                    ProcessedAt = DateTime.UtcNow,
                    Category = "PhoneCommandLog"
                };

                await firebaseClient
                    .Child("NetworkDevices")
                    .Child("Switches")
                    .Child(switchIP.Replace(".", "_"))
                    .Child("CommandProcessLog")
                    .PostAsync(logData);

                return true;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Firebase Command Process Log Error: {ex.Message}");
                return false;
            }
        }

        // Dispose method
        public void Dispose()
        {
            firebaseClient?.Dispose();
        }
    }
} 