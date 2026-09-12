import React, { useState, useEffect } from 'react';
import Navbar, { Topbar } from './components/Navbar';
import LoginPage from './pages/LoginPage';
import ScanPage from './pages/ScanPage';
import ResultsPage from './pages/ResultsPage';
import RepositoryPage from './pages/RepositoryPage';
import DashboardPage from './pages/DashboardPage';
import { checkHealth } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard'); // Default to dashboard/home view
  const [isConnected, setIsConnected] = useState(false);
  const [healthData, setHealthData] = useState({ connected: false });
  const [user, setUser] = useState({ username: 'Inspector Alpha', role: 'Legal Metrology Inspector' });
  const [scanResult, setScanResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

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
    setActiveTab('dashboard');
  };

  const handleLogout = () => {
    setUser(null);
    setActiveTab('login');
  };

  return (
    <div className="shell-container">
      {/* Sidebar Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isConnected={isConnected}
        healthData={healthData}
        scanResult={scanResult}
        user={user}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="main">
        <Topbar
          user={user}
          onLogout={handleLogout}
          setActiveTab={setActiveTab}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
        />

        {activeTab === 'login' && (
          <LoginPage onLoginSuccess={handleLoginSuccess} />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage
            onViewScanResult={handleViewScanResult}
            onStartScan={() => setActiveTab('scan')}
          />
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
          <RepositoryPage
            onViewScanResult={handleViewScanResult}
            externalSearch={searchQuery}
          />
        )}
      </main>
    </div>
  );
}
