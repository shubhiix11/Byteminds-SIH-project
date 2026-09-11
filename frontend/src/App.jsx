import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import LoginPage from './pages/LoginPage';
import ScanPage from './pages/ScanPage';
import ResultsPage from './pages/ResultsPage';
import RepositoryPage from './pages/RepositoryPage';
import DashboardPage from './pages/DashboardPage';
import { checkHealth } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('scan'); // 'scan' | 'results' | 'repository' | 'dashboard' | 'login'
  const [isConnected, setIsConnected] = useState(false);
  const [healthData, setHealthData] = useState({ connected: false });
  const [user, setUser] = useState({ username: 'Inspector Alpha', role: 'Inspector' });
  const [scanResult, setScanResult] = useState(null);

  useEffect(() => {
    let isMounted = true;
    const verifyBackend = async () => {
      const data = await checkHealth();
      if (isMounted) {
        setIsConnected(Boolean(data && data.connected));
        setHealthData(data || { connected: false });
      }
    };

    verifyBackend();
    const interval = setInterval(verifyBackend, 10000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleScanComplete = (result) => {
    setScanResult(result);
    setActiveTab('results');
  };

  const handleViewScanResult = (result) => {
    setScanResult(result);
    setActiveTab('results');
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setActiveTab('scan');
  };

  const handleLogout = () => {
    setUser(null);
    setActiveTab('login');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isConnected={isConnected}
        healthData={healthData}
        scanResult={scanResult}
        user={user}
        onLogout={handleLogout}
      />

      <main style={{ flex: 1, paddingBottom: '3rem' }}>
        {activeTab === 'login' && (
          <LoginPage onLoginSuccess={handleLoginSuccess} />
        )}

        {activeTab === 'scan' && (
          <ScanPage onScanComplete={handleScanComplete} />
        )}

        {activeTab === 'results' && (
          <ResultsPage
            scanResult={scanResult}
            onNewScan={() => setActiveTab('scan')}
          />
        )}

        {activeTab === 'repository' && (
          <RepositoryPage onViewScanResult={handleViewScanResult} />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage onViewScanResult={handleViewScanResult} />
        )}
      </main>

      <footer style={{
        textAlign: 'center',
        padding: '1.5rem',
        borderTop: '1px solid var(--border-color)',
        color: 'var(--text-dim)',
        fontSize: '0.8rem'
      }}>
        LabelSure &copy; {new Date().getFullYear()} • Legal Metrology Packaged Commodity AI Compliance & Enforcement Platform
      </footer>
    </div>
  );
}
