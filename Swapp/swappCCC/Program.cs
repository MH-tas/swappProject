using System;
using System.Net;
using Lextm.SharpSnmpLib;
using Lextm.SharpSnmpLib.Messaging;
using System.Windows.Forms;

namespace CiscoSNMPMonitor
{
    internal static class Program
    {
        /// <summary>
        ///  The main entry point for the application.
        /// </summary>
        [STAThread]
        static void Main()
        {
            ApplicationConfiguration.Initialize();
            Application.Run(new MainForm());
        }
    }
}

class Program
{
    static async Task Main(string[] args)
    {
        Console.WriteLine("Cisco Catalyst 9300 SNMP Monitor");
        Console.WriteLine("--------------------------------");

        // SNMP configuration
        string ipAddress = "192.168.20.1";
        string community = "swapp";
        int port = 161;

        try
        {
            IPEndPoint endpoint = new IPEndPoint(IPAddress.Parse(ipAddress), port);
            Console.WriteLine($"Bağlantı: {ipAddress} (Community: {community})");

            while (true)
            {
                Console.WriteLine("\nİşlem seçin:");
                Console.WriteLine("1. Sistem Bilgisi Al");
                Console.WriteLine("2. Uptime Bilgisi Al");
                Console.WriteLine("3. Interface Listesi");
                Console.WriteLine("4. Çıkış");
                Console.Write("Seçiminiz: ");

                string? choice = Console.ReadLine();

                switch (choice)
                {
                    case "1":
                        await GetSystemInfo(endpoint, community);
                        break;
                    case "2":
                        await GetSystemUptime(endpoint, community);
                        break;
                    case "3":
                        await GetInterfaceInfo(endpoint, community);
                        break;
                    case "4":
                        return;
                    default:
                        Console.WriteLine("Geçersiz seçim!");
                        break;
                }

                Console.WriteLine("\nDevam etmek için bir tuşa basın...");
                Console.ReadKey();
                Console.Clear();
                Console.WriteLine("Cisco Catalyst 9300 SNMP Monitor");
                Console.WriteLine("--------------------------------");
                Console.WriteLine($"Bağlantı: {ipAddress} (Community: {community})");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Hata: {ex.Message}");
            Console.WriteLine("Programı kapatmak için bir tuşa basın...");
            Console.ReadKey();
        }
    }

    static async Task GetSystemInfo(IPEndPoint endpoint, string community)
    {
        try
        {
            var result = await Messenger.GetAsync(VersionCode.V2,
                endpoint,
                new OctetString(community),
                new List<Variable> { new Variable(new ObjectIdentifier("1.3.6.1.2.1.1.1.0")) });

            Console.WriteLine($"\nSistem Bilgisi: {result[0].Data}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Sistem bilgisi alınırken hata: {ex.Message}");
        }
    }

    static async Task GetSystemUptime(IPEndPoint endpoint, string community)
    {
        try
        {
            var result = await Messenger.GetAsync(VersionCode.V2,
                endpoint,
                new OctetString(community),
                new List<Variable> { new Variable(new ObjectIdentifier("1.3.6.1.2.1.1.3.0")) });

            Console.WriteLine($"\nSistem Çalışma Süresi: {result[0].Data}");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Uptime bilgisi alınırken hata: {ex.Message}");
        }
    }

    static async Task GetInterfaceInfo(IPEndPoint endpoint, string community)
    {
        try
        {
            var result = await Messenger.GetAsync(VersionCode.V2,
                endpoint,
                new OctetString(community),
                new List<Variable> { new Variable(new ObjectIdentifier("1.3.6.1.2.1.2.1.0")) });

            Console.WriteLine($"\nToplam Interface Sayısı: {result[0].Data}");

            // Interface durumlarını al
            for (int i = 1; i <= 24; i++) // İlk 24 port için
            {
                try
                {
                    var ifDescr = await Messenger.GetAsync(VersionCode.V2,
                        endpoint,
                        new OctetString(community),
                        new List<Variable> { new Variable(new ObjectIdentifier($"1.3.6.1.2.1.2.2.1.2.{i}")) });

                    var ifStatus = await Messenger.GetAsync(VersionCode.V2,
                        endpoint,
                        new OctetString(community),
                        new List<Variable> { new Variable(new ObjectIdentifier($"1.3.6.1.2.1.2.2.1.7.{i}")) });

                    string status = ifStatus[0].Data.ToString() == "1" ? "Aktif" : "Pasif";
                    Console.WriteLine($"Port {i}: {ifDescr[0].Data} - {status}");
                }
                catch
                {
                    // Port bilgisi alınamazsa devam et
                    continue;
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Interface bilgisi alınırken hata: {ex.Message}");
        }
    }
} 