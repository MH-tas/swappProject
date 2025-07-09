import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Card,
  CardContent,
  Box,
  Chip,
  LinearProgress,
  Alert,
  Button,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Dashboard,
  NetworkCheck,
  Router,
  Settings,
  Refresh,
  Menu as MenuIcon,
  Cable,
  Speed,
  BugReport
} from '@mui/icons-material';
import SettingsPanel from './components/SettingsPanel';
import ConnectionDialog from './components/ConnectionDialog';
import SNMPTester from './components/SNMPTester';
import './App.css';

interface SwitchInfo {
  hostname: string;
  model: string;
  version: string;
  uptime: string;
  serialNumber: string;
  temperature: number;
  cpuUsage: number;
  memoryUsage: number;
}

interface PortInfo {
  name: string;
  description: string;
  status: 'up' | 'down' | 'admin-down';
  speed: string;
  duplex: string;
  vlan: string;
  type: string;
}

interface SNMPSettings {
  host: string;
  port: number;
  username: string; // Kullanılmayacak ama interface uyumluluğu için
  password: string; // Community string olarak kullanılacak
  timeout: number;
  autoConnect: boolean;
}

const defaultSettings: SNMPSettings = {
  host: '192.168.20.1',
  port: 161,
  username: 'admin',
  password: 'public',
  timeout: 5000,
  autoConnect: false
};

function App() {
  const [switchInfo, setSwitchInfo] = useState<SwitchInfo | null>(null);
  const [ports, setPorts] = useState<PortInfo[]>([]);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentView, setCurrentView] = useState('dashboard');
  const [snmpSettings, setSNMPSettings] = useState<SNMPSettings>(defaultSettings);
  const [connectionDialogOpen, setConnectionDialogOpen] = useState(false);

  // Local storage'dan ayarları yükle
  useEffect(() => {
    const savedSettings = localStorage.getItem('sshSettings'); // Eski key'i koruyoruz uyumluluk için
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSNMPSettings({ ...defaultSettings, ...parsed });
      } catch (error) {
        console.error('Ayar yükleme hatası:', error);
      }
    }
  }, []);

  // Auto-connect
  useEffect(() => {
    if (snmpSettings.autoConnect && !connected) {
      connectToSwitch();
    }
  }, [snmpSettings.autoConnect]);

  const connectToSwitch = async (connectionData?: any) => {
    setLoading(true);
    
    // Dialog'dan gelen veri varsa kullan, yoksa mevcut ayarları kullan
    const configToUse = connectionData || snmpSettings;
    
    try {
      // Electron API üzerinden SNMP bağlantısı
      if (window.electronAPI) {
        const connectResult = await window.electronAPI.connectSSH(configToUse);
        
        if (connectResult.success) {
          // Bağlantı bilgilerini güncelle
          if (connectionData) {
            setSNMPSettings({
              ...snmpSettings,
              host: connectionData.host,
              port: connectionData.port,
              username: connectionData.username,
              password: connectionData.password
            });
          }

          // Switch bilgilerini al
          const switchResult = await window.electronAPI.getSwitchInfo();
          if (switchResult.success) {
            setSwitchInfo(switchResult.data);
          }

          // Port bilgilerini al
          const portsResult = await window.electronAPI.getPortStatus();
          if (portsResult.success) {
            setPorts(portsResult.data);
          }

          setConnected(true);
        } else {
          throw new Error(connectResult.message);
        }
      } else {
        // Fallback: Web tarayıcısında çalışıyorsa mock data
        console.warn('Electron API bulunamadı, mock data kullanılıyor');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        setSwitchInfo({
          hostname: 'SWAPP-9300-01',
          model: 'Catalyst 9300-48P',
          version: '16.12.04',
          uptime: '15 days, 3 hours, 45 minutes',
          serialNumber: 'FCW2140L0GH',
          temperature: 45,
          cpuUsage: 12,
          memoryUsage: 34
        });

        const mockPorts: PortInfo[] = [];
        for (let i = 1; i <= 48; i++) {
          mockPorts.push({
            name: `GigabitEthernet1/0/${i}`,
            description: i <= 24 ? `Workstation-${i}` : `Server-${i-24}`,
            status: Math.random() > 0.3 ? 'up' : 'down',
            speed: i > 44 ? '10Gbps' : '1Gbps',
            duplex: 'full',
            vlan: i <= 24 ? '100' : '200',
            type: i > 44 ? 'SFP+' : 'RJ45'
          });
        }
        setPorts(mockPorts);
        setConnected(true);
      }
    } catch (error: any) {
      console.error('SNMP Bağlantı hatası:', error);
      alert(`SNMP Bağlantı hatası: ${error.message || error}`);
    } finally {
      setLoading(false);
    }
  };

  const disconnectFromSwitch = async () => {
    if (window.electronAPI) {
      await window.electronAPI.disconnectSSH();
    }
    setConnected(false);
    setSwitchInfo(null);
    setPorts([]);
  };

  const refreshData = () => {
    if (connected) {
      connectToSwitch();
    }
  };

  const handleSettingsChange = async (newSettings: SNMPSettings) => {
    setSNMPSettings(newSettings);
    
    // Eğer bağlantı varsa ve ayarlar değiştiyse, yeniden bağlan
    if (connected) {
      await disconnectFromSwitch();
      setTimeout(() => {
        setSNMPSettings(newSettings);
        connectToSwitch();
      }, 1000);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'up': return 'success';
      case 'down': return 'error';
      case 'admin-down': return 'warning';
      default: return 'default';
    }
  };

  const renderDashboard = () => (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* System Info Cards */}
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
        <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Switch Bilgileri
              </Typography>
              {switchInfo && (
                <Box>
                  <Typography variant="body2">Model: {switchInfo.model}</Typography>
                  <Typography variant="body2">Hostname: {switchInfo.hostname}</Typography>
                  <Typography variant="body2">Version: {switchInfo.version}</Typography>
                  <Typography variant="body2">Uptime: {switchInfo.uptime}</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                CPU Kullanımı
              </Typography>
              {switchInfo && (
                <Box>
                  <Typography variant="body2">{switchInfo.cpuUsage}%</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={switchInfo.cpuUsage} 
                    color={switchInfo.cpuUsage > 80 ? 'error' : 'primary'}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Memory Kullanımı
              </Typography>
              {switchInfo && (
                <Box>
                  <Typography variant="body2">{switchInfo.memoryUsage}%</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={switchInfo.memoryUsage} 
                    color={switchInfo.memoryUsage > 80 ? 'error' : 'primary'}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: '1 1 300px', minWidth: 250 }}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Sıcaklık
              </Typography>
              {switchInfo && (
                <Box>
                  <Typography variant="body2">{switchInfo.temperature}°C</Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(switchInfo.temperature / 80) * 100} 
                    color={switchInfo.temperature > 60 ? 'error' : 'primary'}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Port Status Summary */}
      <Card elevation={3}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Port Durumu Özeti
          </Typography>
          <Box display="flex" gap={2} flexWrap="wrap">
            <Chip 
              label={`Aktif: ${ports.filter(p => p.status === 'up').length}`} 
              color="success" 
              variant="outlined"
            />
            <Chip 
              label={`Pasif: ${ports.filter(p => p.status === 'down').length}`} 
              color="error" 
              variant="outlined"
            />
            <Chip 
              label={`Admin Down: ${ports.filter(p => p.status === 'admin-down').length}`} 
              color="warning" 
              variant="outlined"
            />
            <Chip 
              label={`Toplam: ${ports.length}`} 
              color="primary" 
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>
    </Box>
  );

  const renderPorts = () => (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Port Detayları
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
          {ports.map((port, index) => (
            <Box key={index} sx={{ flex: '1 1 300px', minWidth: 250, maxWidth: 350 }}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>
                    {port.name}
                  </Typography>
                  <Chip 
                    label={port.status.toUpperCase()} 
                    color={getStatusColor(port.status)} 
                    size="small"
                    sx={{ mb: 1 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    {port.description}
                  </Typography>
                  <Typography variant="body2">
                    Speed: {port.speed}
                  </Typography>
                  <Typography variant="body2">
                    VLAN: {port.vlan}
                  </Typography>
                  <Typography variant="body2">
                    Type: {port.type}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );

  const menuItems = [
    { text: 'Dashboard', icon: <Dashboard />, id: 'dashboard' },
    { text: 'Port Status', icon: <Cable />, id: 'ports' },
    { text: 'Performance', icon: <Speed />, id: 'performance' },
    { text: 'Network', icon: <NetworkCheck />, id: 'network' },
    { text: 'Settings', icon: <Settings />, id: 'settings' },
    { text: 'SNMP Test', icon: <BugReport />, id: 'snmp-test' }
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ backgroundColor: '#1976d2' }}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={() => setDrawerOpen(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Router sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            SWAPP - Cisco 9300 SNMP Management ({snmpSettings.host}:{snmpSettings.port})
          </Typography>
          <Chip 
            label={connected ? 'Connected (SNMP)' : 'Disconnected'} 
            color={connected ? 'success' : 'error'} 
            variant="outlined"
            sx={{ color: 'white', borderColor: 'white', mr: 2 }}
          />
          {connected ? (
            <Button 
              color="inherit" 
              onClick={disconnectFromSwitch}
              sx={{ mr: 1 }}
            >
              Disconnect
            </Button>
          ) : (
            <Button 
              color="inherit" 
              onClick={() => setConnectionDialogOpen(true)} 
              disabled={loading}
              sx={{ mr: 1 }}
            >
              Connect
            </Button>
          )}
          <IconButton color="inherit" onClick={refreshData} disabled={loading || !connected}>
            <Refresh />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 250 }}>
          <List>
            <ListItem>
              <Typography variant="h6">Menu</Typography>
            </ListItem>
            <Divider />
            {menuItems.map((item) => (
              <ListItemButton 
                key={item.id}
                onClick={() => {
                  setCurrentView(item.id);
                  setDrawerOpen(false);
                }}
                selected={currentView === item.id}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            ))}
          </List>
        </Box>
      </Drawer>

      <Container maxWidth="xl" sx={{ mt: 3, mb: 3 }}>
        {loading && <LinearProgress sx={{ mb: 2 }} />}
        
        {!connected && !loading && currentView !== 'settings' && currentView !== 'snmp-test' && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            Switch SNMP bağlantısı yok. 
            <Button onClick={() => setConnectionDialogOpen(true)} sx={{ ml: 2 }}>
              SNMP Bağlan ({snmpSettings.host}:{snmpSettings.port})
            </Button>
          </Alert>
        )}

        {currentView === 'dashboard' && renderDashboard()}
        {currentView === 'ports' && renderPorts()}
        {currentView === 'performance' && (
          <Typography variant="h6">Performance Monitoring - Coming Soon</Typography>
        )}
        {currentView === 'network' && (
          <Typography variant="h6">Network Topology - Coming Soon</Typography>
        )}
        {currentView === 'settings' && (
          <SettingsPanel 
            currentSettings={snmpSettings}
            onSettingsChange={handleSettingsChange}
          />
        )}
        {currentView === 'snmp-test' && (
          <SNMPTester />
        )}
      </Container>

      {/* Connection Dialog */}
      <ConnectionDialog
        open={connectionDialogOpen}
        onClose={() => setConnectionDialogOpen(false)}
        onConnect={connectToSwitch}
        defaultValues={{
          host: snmpSettings.host,
          port: snmpSettings.port,
          username: snmpSettings.username,
          password: snmpSettings.password
        }}
        isConnecting={loading}
      />
    </Box>
  );
}

export default App;
