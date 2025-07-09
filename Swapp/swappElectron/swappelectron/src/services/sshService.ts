// eslint-disable-next-line @typescript-eslint/no-var-requires
const snmp = require('snmp-native');

export interface SNMPConfig {
  host: string;
  community: string;
  version?: number;
  port?: number;
  timeout?: number;
  retries?: number;
}

export interface SwitchInfo {
  hostname: string;
  model: string;
  version: string;
  uptime: string;
  serialNumber: string;
  temperature: number;
  cpuUsage: number;
  memoryUsage: number;
}

export interface PortInfo {
  name: string;
  description: string;
  status: 'up' | 'down' | 'admin-down';
  speed: string;
  duplex: string;
  vlan: string;
  type: string;
  inputRate: number;
  outputRate: number;
  errors: number;
}

// Cisco SNMP OID'leri
const CISCO_OIDS = {
  // System Information
  sysName: '1.3.6.1.2.1.1.5.0',
  sysDescr: '1.3.6.1.2.1.1.1.0',
  sysUpTime: '1.3.6.1.2.1.1.3.0',
  sysContact: '1.3.6.1.2.1.1.4.0',
  sysLocation: '1.3.6.1.2.1.1.6.0',
  
  // Interface Table
  ifDescr: '1.3.6.1.2.1.2.2.1.2',
  ifType: '1.3.6.1.2.1.2.2.1.3',
  ifMtu: '1.3.6.1.2.1.2.2.1.4',
  ifSpeed: '1.3.6.1.2.1.2.2.1.5',
  ifPhysAddress: '1.3.6.1.2.1.2.2.1.6',
  ifAdminStatus: '1.3.6.1.2.1.2.2.1.7',
  ifOperStatus: '1.3.6.1.2.1.2.2.1.8',
  ifInOctets: '1.3.6.1.2.1.2.2.1.10',
  ifOutOctets: '1.3.6.1.2.1.2.2.1.16',
  ifInErrors: '1.3.6.1.2.1.2.2.1.14',
  ifOutErrors: '1.3.6.1.2.1.2.2.1.20',
  ifAlias: '1.3.6.1.2.1.31.1.1.1.18',
  
  // Cisco Specific
  ciscoModel: '1.3.6.1.4.1.9.3.6.11.0',
  ciscoSerial: '1.3.6.1.4.1.9.3.6.3.0',
  ciscoFlashSize: '1.3.6.1.4.1.9.3.6.12.0',
  
  // CPU Usage
  cpmCPUTotal5sec: '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1',
  cpmCPUTotal1min: '1.3.6.1.4.1.9.9.109.1.1.1.1.5.1',
  cpmCPUTotal5min: '1.3.6.1.4.1.9.9.109.1.1.1.1.6.1',
  
  // Memory Usage
  ciscoMemoryPoolUsed: '1.3.6.1.4.1.9.9.48.1.1.1.5.1',
  ciscoMemoryPoolFree: '1.3.6.1.4.1.9.9.48.1.1.1.6.1',
  
  // Environment (Temperature)
  ciscoEnvMonTemperatureStatusValue: '1.3.6.1.4.1.9.9.13.1.3.1.3.1',
  ciscoEnvMonTemperatureStatusDescr: '1.3.6.1.4.1.9.9.13.1.3.1.2.1',
  
  // VLAN Info
  vtpVlanName: '1.3.6.1.4.1.9.9.46.1.3.1.1.4.1',
  vtpVlanState: '1.3.6.1.4.1.9.9.46.1.3.1.1.2.1'
};

export class CiscoSNMPService {
  private session: any;
  private config: SNMPConfig;
  private connected: boolean = false;

  constructor(config: SNMPConfig) {
    this.config = {
      version: 1,
      port: 161,
      timeout: 10000,
      retries: 3,
      ...config
    };
    
    this.session = new snmp.Session({
      host: this.config.host,
      port: this.config.port,
      community: this.config.community,
      timeout: this.config.timeout,
      retries: this.config.retries
    });
  }

  async connect(): Promise<boolean> {
    try {
      console.log(`SNMP bağlantı testi: ${this.config.host}:${this.config.port}`);
      console.log(`Community: ${this.config.community}`);
      
      // Gerçek SNMP test yerine mock test
      console.log('SNMP Mock Mode - Switch bilgileri simüle ediliyor...');
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      this.connected = true;
      console.log('SNMP Bağlantısı başarılı! (Mock Mode)');
      return true;
      
    } catch (error) {
      console.error('SNMP Bağlantı hatası:', error);
      throw error;
    }
  }

  private getSNMPValue(oid: string): Promise<string> {
    return new Promise((resolve, reject) => {
      console.log(`SNMP GET: ${oid}`);
      
      this.session.get({
        oid: oid
      }, (error: any, varbinds: any[]) => {
        if (error) {
          console.error(`SNMP GET Error for ${oid}:`, error);
          reject(error);
          return;
        }

        if (!varbinds || varbinds.length === 0) {
          reject(new Error(`No data returned for OID ${oid}`));
          return;
        }

        const value = varbinds[0].value;
        console.log(`SNMP GET Result for ${oid}: ${value}`);
        resolve(value.toString());
      });
    });
  }

  private getSNMPTable(baseOid: string): Promise<{[key: string]: string}> {
    return new Promise((resolve, reject) => {
      const table: {[key: string]: string} = {};
      
      console.log(`SNMP WALK: ${baseOid}`);
      
      this.session.getNext({
        oid: baseOid
      }, (error: any, varbinds: any[]) => {
        if (error) {
          console.error(`SNMP WALK Error for ${baseOid}:`, error);
          reject(error);
          return;
        }

        if (varbinds && varbinds.length > 0) {
          varbinds.forEach((vb: any) => {
            table[vb.oid] = vb.value.toString();
          });
        }
        
        resolve(table);
      });
    });
  }

  async getSwitchInfo(): Promise<SwitchInfo> {
    try {
      if (!this.connected) {
        throw new Error('SNMP bağlantısı yok');
      }

      console.log('Switch bilgileri alınıyor... (Mock Mode)');

      // Gerçekçi mock data
      return {
        hostname: 'SWAPP-SW',
        model: 'Catalyst 9300-48P',
        version: '16.12.04',
        uptime: '125 days, 14 hours, 23 minutes',
        serialNumber: 'FOC2347L49W',
        temperature: 42,
        cpuUsage: Math.floor(Math.random() * 20) + 5, // 5-25% arası
        memoryUsage: Math.floor(Math.random() * 30) + 40 // 40-70% arası
      };
    } catch (error) {
      console.error('Switch bilgisi alma hatası:', error);
      throw error;
    }
  }

  async getPortStatus(): Promise<PortInfo[]> {
    try {
      if (!this.connected) {
        throw new Error('SNMP bağlantısı yok');
      }

      console.log('Port bilgileri alınıyor... (Mock Mode)');

      const ports: PortInfo[] = [];
      
      // Gerçekçi port konfigürasyonu
      for (let i = 1; i <= 48; i++) {
        const isConnected = Math.random() > 0.4; // %60 bağlı
        const isUplink = i > 44;
        
        ports.push({
          name: `GigabitEthernet1/0/${i}`,
          description: isUplink ? `Uplink-${i-44}` : 
                      i <= 24 ? `Workstation-${i.toString().padStart(2, '0')}` : 
                      `Server-${(i-24).toString().padStart(2, '0')}`,
          status: isConnected ? 'up' : Math.random() > 0.8 ? 'admin-down' : 'down',
          speed: isUplink ? '10Gbps' : '1Gbps',
          duplex: 'full',
          vlan: isUplink ? 'trunk' : i <= 24 ? '100' : '200',
          type: isUplink ? 'SFP+' : 'RJ45',
          inputRate: isConnected ? Math.floor(Math.random() * 800) + 50 : 0,
          outputRate: isConnected ? Math.floor(Math.random() * 600) + 30 : 0,
          errors: Math.floor(Math.random() * 5)
        });
      }

      return ports;
    } catch (error) {
      console.error('Port bilgisi alma hatası:', error);
      throw error;
    }
  }

  async getVlanInfo(): Promise<any[]> {
    try {
      if (!this.connected) {
        throw new Error('SNMP bağlantısı yok');
      }

      console.log('VLAN bilgileri alınıyor... (Mock Mode)');
      
      return [
        { 
          id: '1', 
          name: 'default', 
          status: 'active', 
          ports: ['Gi1/0/45', 'Gi1/0/46', 'Gi1/0/47', 'Gi1/0/48'] 
        },
        { 
          id: '100', 
          name: 'Workstations', 
          status: 'active', 
          ports: Array.from({length: 24}, (_, i) => `Gi1/0/${i+1}`)
        },
        { 
          id: '200', 
          name: 'Servers', 
          status: 'active', 
          ports: Array.from({length: 20}, (_, i) => `Gi1/0/${i+25}`)
        },
        { 
          id: '300', 
          name: 'Management', 
          status: 'active', 
          ports: ['Gi1/0/45'] 
        }
      ];
    } catch (error) {
      console.error('VLAN bilgisi alma hatası:', error);
      return [
        { id: '1', name: 'default', status: 'active', ports: [] },
        { id: '100', name: 'Data', status: 'active', ports: [] },
        { id: '200', name: 'Voice', status: 'active', ports: [] }
      ];
    }
  }

  async getMacAddressTable(): Promise<any[]> {
    try {
      if (!this.connected) {
        throw new Error('SNMP bağlantısı yok');
      }

      console.log('MAC address table alınıyor... (Mock Mode)');
      
      const macTable: any[] = [];
      const companies = ['Dell', 'HP', 'Cisco', 'Apple', 'Lenovo'];
      
      for (let i = 1; i <= 25; i++) {
        const vlan = i <= 12 ? '100' : i <= 20 ? '200' : '300';
        const port = `GigabitEthernet1/0/${i}`;
        const company = companies[Math.floor(Math.random() * companies.length)];
        
        macTable.push({
          vlan: vlan,
          macAddress: this.generateRealisticMac(company),
          type: 'DYNAMIC',
          port: port,
          age: Math.floor(Math.random() * 300) + 1 // 1-300 seconds
        });
      }

      return macTable;
    } catch (error) {
      console.error('MAC address table alma hatası:', error);
      throw error;
    }
  }

  private generateRealisticMac(company: string): string {
    // Gerçekçi MAC adresleri üret
    const ouis: { [key: string]: string } = {
      'Dell': '00:14:22',
      'HP': '00:1f:29', 
      'Cisco': '00:1a:a1',
      'Apple': '00:1f:f3',
      'Lenovo': '00:21:cc'
    };
    
    const oui = ouis[company] || '00:50:56';
    const random1 = Math.floor(Math.random() * 256).toString(16).padStart(2, '0');
    const random2 = Math.floor(Math.random() * 256).toString(16).padStart(2, '0');
    const random3 = Math.floor(Math.random() * 256).toString(16).padStart(2, '0');
    
    return `${oui}:${random1}:${random2}:${random3}`;
  }

  disconnect(): void {
    if (this.session) {
      this.session.close();
    }
    this.connected = false;
    console.log('SNMP bağlantısı kapatıldı (Mock Mode)');
  }
} 