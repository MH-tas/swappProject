const { contextBridge, ipcRenderer } = require('electron');

// Bu dosyayı TypeScript modülü yapmak için
export {};

// Güvenli API'leri renderer process'e expose et
contextBridge.exposeInMainWorld('electronAPI', {
  // SSH Bağlantı API'leri
  connectSSH: (config: any) => ipcRenderer.invoke('ssh-connect', config),
  disconnectSSH: () => ipcRenderer.invoke('ssh-disconnect'),
  
  // Switch Bilgi API'leri
  getSwitchInfo: () => ipcRenderer.invoke('get-switch-info'),
  getPortStatus: () => ipcRenderer.invoke('get-port-status'),
  getVlanInfo: () => ipcRenderer.invoke('get-vlan-info'),
  getMacTable: () => ipcRenderer.invoke('get-mac-table'),
  
  // Genel Komut Çalıştırma
  executeCommand: (command: string) => ipcRenderer.invoke('execute-command', command),
  
  // Event listeners
  onSwitchStatusChange: (callback: (status: boolean) => void) => {
    ipcRenderer.on('switch-status-changed', (_event: any, status: any) => callback(status));
  },
  
  // Cleanup
  removeAllListeners: (channel: string) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

// Type definitions for window object
declare global {
  interface Window {
    electronAPI: {
      connectSSH: (config: any) => Promise<any>;
      disconnectSSH: () => Promise<any>;
      getSwitchInfo: () => Promise<any>;
      getPortStatus: () => Promise<any>;
      getVlanInfo: () => Promise<any>;
      getMacTable: () => Promise<any>;
      executeCommand: (command: string) => Promise<any>;
      onSwitchStatusChange: (callback: (status: boolean) => void) => void;
      removeAllListeners: (channel: string) => void;
    };
  }
} 