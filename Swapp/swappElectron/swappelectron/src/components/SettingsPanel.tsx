import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  Grid,
  Divider,
  Alert,
  Chip,
  FormControlLabel,
  Switch
} from '@mui/material';
import {
  Save as SaveIcon,
  Restore as RestoreIcon,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';

interface SNMPSettings {
  host: string;
  port: number;
  username: string;
  password: string; // Bu artık community string olarak kullanılacak
  timeout: number;
  autoConnect: boolean;
}

interface SettingsPanelProps {
  onSettingsChange: (settings: SNMPSettings) => void;
  currentSettings: SNMPSettings;
}

const defaultSettings: SNMPSettings = {
  host: '192.168.20.1',
  port: 161,
  username: 'admin', // Kullanılmayacak ama interface uyumluluğu için
  password: 'public', // Community string
  timeout: 5000,
  autoConnect: false
};

const SettingsPanel: React.FC<SettingsPanelProps> = ({ 
  onSettingsChange, 
  currentSettings 
}) => {
  const [settings, setSettings] = useState<SNMPSettings>(currentSettings);
  const [showCommunity, setShowCommunity] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string>('');

  useEffect(() => {
    const changed = JSON.stringify(settings) !== JSON.stringify(currentSettings);
    setHasChanges(changed);
  }, [settings, currentSettings]);

  const handleInputChange = (field: keyof SNMPSettings) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = event.target.type === 'number' 
      ? parseInt(event.target.value) || 0
      : event.target.value;
    
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSwitchChange = (field: keyof SNMPSettings) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setSettings(prev => ({
      ...prev,
      [field]: event.target.checked
    }));
  };

  const handleSave = () => {
    // Validasyonlar
    if (!settings.host.trim()) {
      setSaveMessage('Host adresi boş olamaz');
      return;
    }
    if (settings.port < 1 || settings.port > 65535) {
      setSaveMessage('Port 1-65535 arasında olmalıdır');
      return;
    }
    if (!settings.password.trim()) {
      setSaveMessage('SNMP Community string boş olamaz');
      return;
    }

    // Ayarları kaydet
    onSettingsChange(settings);
    setSaveMessage('Ayarlar başarıyla kaydedildi!');
    setTimeout(() => setSaveMessage(''), 3000);

    // Local storage'a kaydet
    localStorage.setItem('sshSettings', JSON.stringify(settings));
  };

  const handleRestore = () => {
    setSettings(defaultSettings);
    setSaveMessage('Varsayılan ayarlar geri yüklendi');
    setTimeout(() => setSaveMessage(''), 3000);
  };

  const testConnection = async () => {
    if (window.electronAPI) {
      try {
        setSaveMessage('SNMP bağlantı test ediliyor...');
        const result = await window.electronAPI.connectSSH(settings);
        if (result.success) {
          setSaveMessage('✅ SNMP Bağlantısı başarılı!');
          await window.electronAPI.disconnectSSH();
        } else {
          setSaveMessage(`❌ SNMP Bağlantı hatası: ${result.message}`);
        }
      } catch (error: any) {
        setSaveMessage(`❌ Test hatası: ${error.message}`);
      }
      setTimeout(() => setSaveMessage(''), 5000);
    } else {
      setSaveMessage('⚠️ Test sadece Electron uygulamasında çalışır');
      setTimeout(() => setSaveMessage(''), 3000);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Card elevation={3}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" component="h2" sx={{ flexGrow: 1 }}>
              SNMP Bağlantı Ayarları
            </Typography>
            {hasChanges && (
              <Chip label="Değişiklikler var" color="warning" size="small" />
            )}
          </Box>

          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            {/* Ana Bağlantı Bilgileri */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                SNMP Bağlantı Bilgileri
              </Typography>
            </Grid>

            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Host/IP Adresi"
                value={settings.host}
                onChange={handleInputChange('host')}
                placeholder="192.168.20.1"
                helperText="Switch'in IP adresi"
              />
            </Grid>

            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="SNMP Port"
                type="number"
                value={settings.port}
                onChange={handleInputChange('port')}
                placeholder="161"
                helperText="SNMP portu (varsayılan: 161)"
                inputProps={{ min: 1, max: 65535 }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="SNMP Community String"
                type={showCommunity ? 'text' : 'password'}
                value={settings.password}
                onChange={handleInputChange('password')}
                placeholder="public"
                helperText="SNMP community string (varsayılan: public)"
                InputProps={{
                  endAdornment: (
                    <Button
                      onClick={() => setShowCommunity(!showCommunity)}
                      sx={{ minWidth: 'auto', p: 1 }}
                    >
                      {showCommunity ? <VisibilityOff /> : <Visibility />}
                    </Button>
                  )
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Alert severity="info" sx={{ mt: 1 }}>
                <Typography variant="caption">
                  SNMP v2c kullanılır. Community string'i switch konfigürasyonundaki ile eşleşmelidir.
                </Typography>
              </Alert>
            </Grid>

            {/* Gelişmiş Ayarlar */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Gelişmiş Ayarlar
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Bağlantı Timeout (ms)"
                type="number"
                value={settings.timeout}
                onChange={handleInputChange('timeout')}
                placeholder="5000"
                helperText="SNMP zaman aşımı süresi"
                inputProps={{ min: 1000, max: 30000 }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoConnect}
                    onChange={handleSwitchChange('autoConnect')}
                  />
                }
                label="Uygulama açılışında otomatik bağlan"
              />
            </Grid>

            {/* Butonlar */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSave}
                  disabled={!hasChanges}
                  color="primary"
                >
                  Kaydet
                </Button>

                <Button
                  variant="outlined"
                  onClick={testConnection}
                  color="info"
                >
                  SNMP Bağlantıyı Test Et
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<RestoreIcon />}
                  onClick={handleRestore}
                  color="warning"
                >
                  Varsayılan Ayarlar
                </Button>
              </Box>
            </Grid>

            {/* Mesaj Alanı */}
            {saveMessage && (
              <Grid item xs={12}>
                <Alert 
                  severity={
                    saveMessage.includes('✅') ? 'success' :
                    saveMessage.includes('❌') ? 'error' :
                    saveMessage.includes('⚠️') ? 'warning' : 'info'
                  }
                >
                  {saveMessage}
                </Alert>
              </Grid>
            )}

            {/* SNMP Bilgi Kutusu */}
            <Grid item xs={12}>
              <Alert severity="info">
                <Typography variant="body2">
                  <strong>SNMP Hakkında:</strong> Bu uygulama artık SNMP protokolü kullanıyor. 
                  Cisco cihazınızda SNMP'nin etkin olduğundan ve doğru community string'in konfigüre edildiğinden emin olun.
                  <br />
                  <strong>Örnek Cisco Konfigürasyonu:</strong> <code>snmp-server community public RO</code>
                </Typography>
              </Alert>
            </Grid>

            {/* SNMP OID Bilgileri */}
            <Grid item xs={12}>
              <Alert severity="success">
                <Typography variant="body2">
                  <strong>Desteklenen Cisco OID'ler:</strong>
                  <br />• System Information (sysName, sysDescr, sysUpTime)
                  <br />• Interface Statistics (ifTable, ifXTable)
                  <br />• CPU Usage (cpmCPUTotal5sec)
                  <br />• Memory Usage (ciscoMemoryPool)
                  <br />• Temperature (ciscoEnvMon)
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SettingsPanel; 