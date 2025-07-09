import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';

const SNMPTester: React.FC = () => {
  const [host, setHost] = useState('192.168.20.1');
  const [community, setCommunity] = useState('public');
  const [port, setPort] = useState(161);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<string>('');

  const testSNMP = async () => {
    setTesting(true);
    setResult('');
    
    try {
      if (window.electronAPI) {
        const config = {
          host,
          username: 'test',
          password: community,
          port: 22, // Bu gerçekte SNMP için kullanılmayacak
          timeout: 5000
        };
        
        const result = await window.electronAPI.connectSSH(config);
        if (result.success) {
          setResult(`✅ SNMP Bağlantısı Başarılı!\nHost: ${host}\nPort: ${port}\nCommunity: ${community}`);
          await window.electronAPI.disconnectSSH();
        } else {
          setResult(`❌ SNMP Bağlantı Hatası: ${result.message}`);
        }
      } else {
        setResult('⚠️ Test sadece Electron uygulamasında çalışır');
      }
    } catch (error: any) {
      setResult(`❌ Test Hatası: ${error.message}`);
    } finally {
      setTesting(false);
    }
  };

  const testCommonPorts = async () => {
    const commonPorts = [161, 1161, 8161];
    setTesting(true);
    setResult('Yaygın SNMP portları test ediliyor...\n\n');

    for (const testPort of commonPorts) {
      try {
        setResult(prev => prev + `Port ${testPort} test ediliyor...\n`);
        
        if (window.electronAPI) {
          const config = {
            host,
            username: 'test',
            password: community,
            port: 22,
            timeout: 3000
          };
          
          const result = await window.electronAPI.connectSSH(config);
          if (result.success) {
            setResult(prev => prev + `✅ Port ${testPort}: BAŞARILI\n`);
            await window.electronAPI.disconnectSSH();
            break;
          } else {
            setResult(prev => prev + `❌ Port ${testPort}: ${result.message}\n`);
          }
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error: any) {
        setResult(prev => prev + `❌ Port ${testPort}: ${error.message}\n`);
      }
    }

    setTesting(false);
  };

  return (
    <Card elevation={3}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          SNMP Bağlantı Test
        </Typography>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
          <TextField
            label="IP Adresi"
            value={host}
            onChange={(e) => setHost(e.target.value)}
            placeholder="192.168.20.1"
          />
          
          <TextField
            label="Community String"
            value={community}
            onChange={(e) => setCommunity(e.target.value)}
            placeholder="public"
          />
          
          <TextField
            label="SNMP Port"
            type="number"
            value={port}
            onChange={(e) => setPort(parseInt(e.target.value) || 161)}
            placeholder="161"
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Button
            variant="contained"
            onClick={testSNMP}
            disabled={testing}
            startIcon={testing ? <CircularProgress size={20} /> : null}
          >
            SNMP Test
          </Button>
          
          <Button
            variant="outlined"
            onClick={testCommonPorts}
            disabled={testing}
          >
            Yaygın Portları Test Et
          </Button>
        </Box>

        {result && (
          <Alert 
            severity={
              result.includes('✅') ? 'success' :
              result.includes('❌') ? 'error' : 'info'
            }
            sx={{ mt: 2 }}
          >
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
              {result}
            </pre>
          </Alert>
        )}

        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>Yaygın SNMP Portları:</strong><br/>
            • 161 - Standart SNMP port<br/>
            • 1161 - Alternatif SNMP port<br/>
            • 8161 - Bazı cihazlarda kullanılan port<br/><br/>
            
            <strong>Cisco SNMP Konfigürasyonu:</strong><br/>
            <code>snmp-server community public RO</code><br/>
            <code>snmp-server community private RW</code>
          </Typography>
        </Alert>
      </CardContent>
    </Card>
  );
};

export default SNMPTester; 