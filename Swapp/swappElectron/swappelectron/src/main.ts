const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { CiscoSNMPService } = require('./services/sshService');

const isDev = process.env.NODE_ENV === 'development';

// SNMP Servisi
let snmpService: any = null;

// IPC Event Handlers
ipcMain.handle('ssh-connect', async (event: any, config: any) => {
  try {
    // SSH config'i SNMP config'e çevir
    const snmpConfig = {
      host: config.host,
      community: config.password || 'public', // Password'u community string olarak kullan
      port: 161,
      timeout: 10000,
      retries: 3
    };
    
    console.log('SNMP Config:', snmpConfig);
    
    snmpService = new CiscoSNMPService(snmpConfig);
    await snmpService.connect();
    return { success: true, message: 'SNMP Bağlantı başarılı' };
  } catch (error: any) {
    console.error('SNMP Error:', error);
    return { success: false, message: error.message };
  }
});

ipcMain.handle('get-switch-info', async () => {
  try {
    if (!snmpService) {
      throw new Error('SNMP bağlantısı yok');
    }
    const info = await snmpService.getSwitchInfo();
    return { success: true, data: info };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
});

ipcMain.handle('get-port-status', async () => {
  try {
    if (!snmpService) {
      throw new Error('SNMP bağlantısı yok');
    }
    const ports = await snmpService.getPortStatus();
    return { success: true, data: ports };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
});

ipcMain.handle('get-vlan-info', async () => {
  try {
    if (!snmpService) {
      throw new Error('SNMP bağlantısı yok');
    }
    const vlans = await snmpService.getVlanInfo();
    return { success: true, data: vlans };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
});

ipcMain.handle('get-mac-table', async () => {
  try {
    if (!snmpService) {
      throw new Error('SNMP bağlantısı yok');
    }
    const macTable = await snmpService.getMacAddressTable();
    return { success: true, data: macTable };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
});

ipcMain.handle('execute-command', async (event: any, command: any) => {
  try {
    // SNMP'de direktkomut yok, sadece OID sorguları var
    return { success: false, message: 'SNMP üzerinden komut çalıştırma desteklenmiyor' };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
});

ipcMain.handle('ssh-disconnect', async () => {
  try {
    if (snmpService) {
      snmpService.disconnect();
      snmpService = null;
    }
    return { success: true, message: 'SNMP Bağlantı kesildi' };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
});

function createWindow(): void {
  // Ana pencereyi oluştur
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, '../public/vite.svg'), // İkon ekle
    show: false, // Hazır olana kadar gizle
    titleBarStyle: 'default',
    resizable: true,
    minimizable: true,
    maximizable: true,
    closable: true
  });

  // Development modunda Vite dev server'ı yükle, production'da build edilmiş dosyaları
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    // DevTools'u aç (development modunda)
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Pencere hazır olduğunda göster
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  // Pencere kapatıldığında null yap
  mainWindow.on('closed', () => {
    // Dereference the window object
  });
}

// Bu metod Electron'un başlatılmaya hazır olduğunda çağrılır
app.whenReady().then(createWindow);

// Tüm pencereler kapatıldığında uygulamayı kapat (macOS hariç)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // macOS'ta dock icon'a tıklandığında pencere açık değilse yeni pencere oluştur
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
}); 