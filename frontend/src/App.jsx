import React, { useState, useEffect } from 'react';
import Navbar, { Topbar } from './components/Navbar';
import LoginPage from './pages/LoginPage';
import ScanPage from './pages/ScanPage';
import ResultsPage from './pages/ResultsPage';
import RepositoryPage from './pages/RepositoryPage';
import DashboardPage from './pages/DashboardPage';
import { checkHealth } from './services/api';

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('labelsure_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [activeTab, setActiveTab] = useState(() => {
    // Default to scan page in guest mode, or dashboard if already logged in
    try {
      const saved = localStorage.getItem('labelsure_user');
      return saved ? 'dashboard' : 'scan';
    } catch {
      return 'scan';
    }
  });
  const [isConnected, setIsConnected] = useState(false);
  const [healthData, setHealthData] = useState({ connected: false });
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
    try {
      localStorage.setItem('labelsure_user', JSON.stringify(userData));
    } catch (e) {
      console.warn('Could not persist login session:', e);
    }
    // Return to results if currently reviewing a scan, otherwise go to dashboard
    if (scanResult && activeTab === 'results') {
      setActiveTab('results');
    } else {
      setActiveTab('dashboard');
    }
  };

  const handleLogout = () => {
    setUser(null);
    try {
      localStorage.removeItem('labelsure_user');
    } catch (e) {
      console.warn('Could not clear login session:', e);
    }
    setActiveTab('scan');
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
          <LoginPage
            onLoginSuccess={handleLoginSuccess}
            onContinueAsGuest={() => setActiveTab('scan')}
          />
        )}

        {activeTab === 'dashboard' && (
          <DashboardPage
            user={user}
            onViewScanResult={handleViewScanResult}
            onStartScan={() => setActiveTab('scan')}
            onNavigateLogin={() => setActiveTab('login')}
          />
        )}

        {activeTab === 'scan' && (
          <ScanPage
            user={user}
            onScanComplete={handleScanComplete}
            onNavigateLogin={() => setActiveTab('login')}
          />
        )}

        {activeTab === 'results' && (
          <ResultsPage
            user={user}
            scanResult={scanResult}
            onNewScan={() => setActiveTab('scan')}
            onNavigateLogin={() => setActiveTab('login')}
            onScanSaved={(savedScan) => setScanResult(savedScan)}
          />
        )}

        {activeTab === 'repository' && (
          <RepositoryPage
            user={user}
            onViewScanResult={handleViewScanResult}
            externalSearch={searchQuery}
            onNavigateLogin={() => setActiveTab('login')}
            onStartScan={() => setActiveTab('scan')}
          />
        )}
      </main>
    </div>
  );
}
