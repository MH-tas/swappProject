import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  IconButton,
  Alert,
  InputAdornment,
  Chip
} from '@mui/material';
import {
  Close as CloseIcon,
  Visibility,
  VisibilityOff,
  Wifi,
  Router as RouterIcon
} from '@mui/icons-material';

interface ConnectionDialogProps {
  open: boolean;
  onClose: () => void;
  onConnect: (connectionData: ConnectionData) => Promise<void>;
  defaultValues?: ConnectionData;
  isConnecting?: boolean;
}

interface ConnectionData {
  host: string;
  port: number;
  username: string;
  password: string; // Community string olarak kullanılacak
}

const defaultConnectionData: ConnectionData = {
  host: '192.168.20.1',
  port: 161,
  username: 'admin', // Kullanılmayacak ama interface uyumluluğu için
  password: 'public' // Bu community string olarak kullanılacak
};

const ConnectionDialog: React.FC<ConnectionDialogProps> = ({
  open,
  onClose,
  onConnect,
  defaultValues = defaultConnectionData,
  isConnecting = false
}) => {
  const [formData, setFormData] = useState<ConnectionData>(defaultValues);
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form açıldığında default değerleri yükle
  useEffect(() => {
    if (open) {
      setFormData(defaultValues);
      setErrors({});
      setIsSubmitting(false);
    }
  }, [open, defaultValues]);

  const handleInputChange = (field: keyof ConnectionData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = field === 'port' 
      ? parseInt(event.target.value) || 161
      : event.target.value;
    
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));

    // Hatayı temizle
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: ''
      }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.host.trim()) {
      newErrors.host = 'IP adresi/hostname gerekli';
    } else if (!/^(\d{1,3}\.){3}\d{1,3}$/.test(formData.host) && 
               !/^[a-zA-Z0-9.-]+$/.test(formData.host)) {
      newErrors.host = 'Geçerli bir IP adresi veya hostname girin';
    }

    if (!formData.port || formData.port < 1 || formData.port > 65535) {
      newErrors.port = 'Port 1-65535 arasında olmalıdır';
    }

    if (!formData.password.trim()) {
      newErrors.password = 'SNMP Community string gerekli';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleConnect = async () => {
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onConnect(formData);
      // Başarılı bağlantıda dialog'u kapat
      onClose();
    } catch (error) {
      console.error('SNMP Bağlantı hatası:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !isSubmitting) {
      handleConnect();
    }
  };

  const resetToDefaults = () => {
    setFormData(defaultConnectionData);
    setErrors({});
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        backgroundColor: '#1976d2',
        color: 'white',
        pb: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <RouterIcon />
          <Typography variant="h6">
            Cisco Switch SNMP Bağlantısı
          </Typography>
        </Box>
        <IconButton 
          onClick={onClose}
          sx={{ color: 'white' }}
          disabled={isSubmitting || isConnecting}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ pt: 3 }}>
        <Box sx={{ mb: 2 }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2">
              Cisco switch'inize SNMP ile bağlanmak için bilgileri girin. 
              SNMP v2c protokolü kullanılır.
            </Typography>
          </Alert>
        </Box>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          {/* IP ve Port */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ flex: '2 1 300px', minWidth: 250 }}>
              <TextField
                fullWidth
                label="IP Adresi / Hostname"
                value={formData.host}
                onChange={handleInputChange('host')}
                onKeyPress={handleKeyPress}
                error={!!errors.host}
                helperText={errors.host || 'Switch\'in IP adresi veya hostname\'i'}
                placeholder="192.168.20.1"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Wifi color="action" />
                    </InputAdornment>
                  )
                }}
              />
            </Box>

            <Box sx={{ flex: '1 1 150px', minWidth: 120 }}>
              <TextField
                fullWidth
                label="SNMP Port"
                type="number"
                value={formData.port}
                onChange={handleInputChange('port')}
                onKeyPress={handleKeyPress}
                error={!!errors.port}
                helperText={errors.port || 'SNMP portu (161)'}
                placeholder="161"
                inputProps={{ min: 1, max: 65535 }}
              />
            </Box>
          </Box>

          {/* Community String */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
              <TextField
                fullWidth
                label="SNMP Community String"
                type={showPassword ? 'text' : 'password'}
                value={formData.password}
                onChange={handleInputChange('password')}
                onKeyPress={handleKeyPress}
                error={!!errors.password}
                helperText={errors.password || 'SNMP community string (public/private)'}
                placeholder="public"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                        tabIndex={-1}
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
              />
            </Box>

            <Box sx={{ flex: '1 1 200px', minWidth: 200 }}>
              <Alert severity="success" sx={{ mt: 1 }}>
                <Typography variant="caption">
                  <strong>Cisco Konfigürasyonu:</strong><br/>
                  <code>snmp-server community {formData.password} RO</code>
                </Typography>
              </Alert>
            </Box>
          </Box>

          {/* Bağlantı Bilgisi */}
          <Box sx={{ 
            p: 2, 
            backgroundColor: '#f5f5f5', 
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                SNMP Bağlantı: <strong>{formData.host}:{formData.port}</strong>
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Community: {formData.password}
              </Typography>
            </Box>
            <Chip 
              label="SNMP v2c" 
              size="small" 
              color="success" 
              variant="outlined"
            />
          </Box>
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 1 }}>
        <Button 
          onClick={resetToDefaults}
          disabled={isSubmitting || isConnecting}
          color="inherit"
        >
          Varsayılan Değerler
        </Button>
        
        <Button 
          onClick={onClose}
          disabled={isSubmitting || isConnecting}
          color="inherit"
        >
          İptal
        </Button>
        
        <Button 
          onClick={handleConnect}
          variant="contained"
          disabled={isSubmitting || isConnecting}
          sx={{ minWidth: 120 }}
        >
          {isSubmitting || isConnecting ? 'SNMP Bağlanıyor...' : 'SNMP Bağlan'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConnectionDialog; 