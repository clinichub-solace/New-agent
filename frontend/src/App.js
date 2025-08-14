import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

console.log('Environment check:', {
  REACT_APP_BACKEND_URL: process.env.REACT_APP_BACKEND_URL,
  BACKEND_URL,
  API
});

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Token validation failed:', error);
      localStorage.removeItem('token');
      setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      console.log('Making login request to:', `${API}/auth/login`);
      console.log('Request payload:', { username, password });
      
      const response = await axios.post(`${API}/auth/login`, { username, password });
      console.log('Login response:', response.data);
      
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || 'Login failed. Please try again.' 
      };
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post(`${API}/auth/logout`);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Page Component
const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(username, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="bg-white/10 backdrop-blur-md p-8 rounded-xl border border-white/20 shadow-2xl w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">ClinicHub</h1>
          <p className="text-blue-200">Practice Management System</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-blue-200 text-sm font-medium mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Enter your username"
              required
            />
          </div>

          <div>
            <label className="block text-blue-200 text-sm font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>

          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}
        </form>

        <div className="mt-6 text-center">
          <p className="text-blue-300 text-sm">
            Default: admin / admin123
          </p>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeModule, setActiveModule] = useState('dashboard');
  const [synologyStatus, setSynologyStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSynologyStatus();
  }, []);

  const fetchSynologyStatus = async () => {
    try {
      const response = await axios.get(`${API}/auth/synology-status`);
      setSynologyStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch Synology status:', error);
    }
  };

  const renderContent = () => {
    switch (activeModule) {
      case 'patients':
        return <PatientsModule />;
      case 'invoices':
        return <InvoicesModule setActiveModule={setActiveModule} />;
      case 'system-settings':
        return <SystemSettingsModule onStatusUpdate={fetchSynologyStatus} />;
      case 'employees':
        return <EmployeesModule setActiveModule={setActiveModule} />;
      case 'inventory':
        return <InventoryModule setActiveModule={setActiveModule} />;
      case 'finance':
        return <FinanceModule setActiveModule={setActiveModule} />;
      case 'communication':
        return <CommunicationModule />;
      default:
        return <DashboardHome setActiveModule={setActiveModule} />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">ClinicHub Dashboard</h1>
            <p className="text-blue-200">Welcome back, {user?.first_name || user?.username}!</p>
          </div>
          <div className="flex items-center space-x-4">
            {synologyStatus && (
              <div className="text-sm text-blue-200">
                Synology: {synologyStatus.enabled ? 'Enabled' : 'Disabled'}
              </div>
            )}
            <button
              onClick={logout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex space-x-6">
          {/* Sidebar Navigation */}
          <div className="w-64 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
            <nav className="space-y-2">
              <button
                onClick={() => setActiveModule('dashboard')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'dashboard' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveModule('patients')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'patients' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                Patients/EHR
              </button>
              <button
                onClick={() => setActiveModule('system-settings')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'system-settings' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                System Settings
              </button>
              <button
                onClick={() => setActiveModule('medical-databases')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'medical-databases' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                Medical Databases
              </button>
              <button
                onClick={() => setActiveModule('communication')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'communication' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                Communication
              </button>
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

// Dashboard Home Component - Comprehensive Practice Management System
const DashboardHome = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    patients: 0,
    dailyRevenue: 0,
    patientCare: 0,
    pendingIssues: 0
  });
  
  useEffect(() => {
    // This would fetch real stats from the backend
    setStats({
      patients: 0,
      dailyRevenue: 0,
      patientCare: 0,
      pendingIssues: 0
    });
  }, []);
  
  const practiceModules = [
    {
      id: 'patients-ehr',
      title: 'Patients/EHR',
      description: 'Patient records & encounters',
      icon: '👥',
      color: 'bg-blue-600/20 border-blue-400/50',
      onClick: () => setActiveModule('patients')
    },
    {
      id: 'smart-forms',
      title: 'Smart Forms',
      description: 'FHIR-compliant forms',
      icon: '📋',
      color: 'bg-green-600/20 border-green-400/50',
      onClick: () => setActiveModule('forms')
    },
    {
      id: 'inventory',
      title: 'Inventory',
      description: 'Medical supplies tracking',
      icon: '📦',
      color: 'bg-purple-600/20 border-purple-400/50',
      onClick: () => setActiveModule('inventory')
    },
    {
      id: 'invoices',
      title: 'Invoices',
      description: 'Billing & payments',
      icon: '💰',
      color: 'bg-yellow-600/20 border-yellow-400/50',
      onClick: () => setActiveModule('invoices')
    },
    {
      id: 'lab-orders',
      title: 'Lab Orders',
      description: 'Laboratory integration',
      icon: '🧪',
      color: 'bg-red-600/20 border-red-400/50',
      onClick: () => setActiveModule('lab-orders')
    },
    {
      id: 'insurance',
      title: 'Insurance',
      description: 'Verification & prior auth',
      icon: '🛡️',
      color: 'bg-indigo-600/20 border-indigo-400/50',
      onClick: () => setActiveModule('insurance')
    },
    {
      id: 'employees',
      title: 'Employees',
      description: 'Staff management',
      icon: '👨‍⚕️',
      color: 'bg-teal-600/20 border-teal-400/50',
      onClick: () => setActiveModule('employees')
    },
    {
      id: 'finance',
      title: 'Finance',
      description: 'Financial reporting',
      icon: '📊',
      color: 'bg-orange-600/20 border-orange-400/50',
      onClick: () => setActiveModule('finance')
    },
    {
      id: 'scheduling',
      title: 'Scheduling',
      description: 'Appointment management',
      icon: '📅',
      color: 'bg-pink-600/20 border-pink-400/50',
      onClick: () => setActiveModule('scheduling')
    },
    {
      id: 'communications',
      title: 'Communications',
      description: 'Patient messaging',
      icon: '💬',
      color: 'bg-cyan-600/20 border-cyan-400/50',
      onClick: () => setActiveModule('communication')
    },
    {
      id: 'referrals',
      title: 'Referrals',
      description: 'Provider network',
      icon: '🔗',
      color: 'bg-violet-600/20 border-violet-400/50',
      onClick: () => setActiveModule('referrals')
    },
    {
      id: 'clinical-templates',
      title: 'Clinical Templates',
      description: 'Clinical protocols',
      icon: '📝',
      color: 'bg-lime-600/20 border-lime-400/50',
      onClick: () => setActiveModule('clinical-templates')
    },
    {
      id: 'quality-measures',
      title: 'Quality Measures',
      description: 'Performance analytics',
      icon: '📈',
      color: 'bg-emerald-600/20 border-emerald-400/50',
      onClick: () => setActiveModule('quality-measures')
    },
    {
      id: 'patient-portal',
      title: 'Patient Portal',
      description: 'Portal management',
      icon: '🌐',
      color: 'bg-sky-600/20 border-sky-400/50',
      onClick: () => setActiveModule('patient-portal')
    },
    {
      id: 'documents',
      title: 'Documents',
      description: 'Document workflows',
      icon: '📄',
      color: 'bg-amber-600/20 border-amber-400/50',
      onClick: () => setActiveModule('documents')
    },
    {
      id: 'telehealth',
      title: 'Telehealth',
      description: 'Virtual consultations',
      icon: '💻',
      color: 'bg-rose-600/20 border-rose-400/50',
      onClick: () => setActiveModule('telehealth')
    },
    {
      id: 'system-settings',
      title: 'System Settings',
      description: 'System configuration',
      icon: '⚙️',
      color: 'bg-slate-600/20 border-slate-400/50',
      onClick: () => setActiveModule('system-settings')
    }
  ];
  
  return (
    <div className="space-y-6">
      {/* Dashboard Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-white">{stats.patients}</h3>
              <p className="text-blue-200 text-sm">Patients</p>
            </div>
            <div className="text-3xl">👥</div>
          </div>
        </div>
        
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-white">${stats.dailyRevenue}</h3>
              <p className="text-blue-200 text-sm">Daily Revenue</p>
            </div>
            <div className="text-3xl">💰</div>
          </div>
        </div>
        
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-white">{stats.patientCare}</h3>
              <p className="text-blue-200 text-sm">Patient Care</p>
            </div>
            <div className="text-3xl">⚕️</div>
          </div>
        </div>
        
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-2xl font-bold text-white">${stats.pendingIssues}</h3>
              <p className="text-blue-200 text-sm">Pending Issues</p>
            </div>
            <div className="text-3xl">⚠️</div>
          </div>
        </div>
      </div>

      {/* Practice Management Modules */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
        <h3 className="text-xl font-bold text-white mb-6">Practice Management Modules</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {practiceModules.map((module) => (
            <div
              key={module.id}
              onClick={module.onClick}
              className={`${module.color} backdrop-blur-md rounded-lg border p-4 hover:bg-white/20 transition-all cursor-pointer`}
            >
              <div className="flex items-center space-x-3">
                <div className="text-2xl">{module.icon}</div>
                <div>
                  <h4 className="text-white font-semibold text-sm">{module.title}</h4>
                  <p className="text-blue-200 text-xs">{module.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p className="text-blue-200 text-sm">Authentication Source</p>
            <p className="text-white font-medium">{user?.auth_source || 'Local'}</p>
          </div>
          <div>
            <p className="text-blue-200 text-sm">User Role</p>
            <p className="text-white font-medium">{user?.role || 'Admin'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// System Settings Module
const SystemSettingsModule = ({ onStatusUpdate }) => {
  const [synologyConfig, setSynologyConfig] = useState({
    auth_url: '',
    session_name: 'ClinicHub',
    verify_ssl: true
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleConfigUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await axios.post(`${API}/auth/synology-config`, synologyConfig);
      setMessage('Synology configuration updated successfully!');
      onStatusUpdate();
    } catch (error) {
      setMessage(`Error: ${error.response?.data?.detail || 'Failed to update configuration'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <h2 className="text-xl font-semibold text-white mb-6">System Settings</h2>
      
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-white mb-4">Synology SSO Configuration</h3>
          <form onSubmit={handleConfigUpdate} className="space-y-4">
            <div>
              <label className="block text-blue-200 text-sm font-medium mb-2">
                Synology DSM URL
              </label>
              <input
                type="url"
                value={synologyConfig.auth_url}
                onChange={(e) => setSynologyConfig({...synologyConfig, auth_url: e.target.value})}
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="https://your-synology-nas.example.com:5001"
                required
              />
            </div>
            
            <div>
              <label className="block text-blue-200 text-sm font-medium mb-2">
                Session Name
              </label>
              <input
                type="text"
                value={synologyConfig.session_name}
                onChange={(e) => setSynologyConfig({...synologyConfig, session_name: e.target.value})}
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="ClinicHub"
                required
              />
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                checked={synologyConfig.verify_ssl}
                onChange={(e) => setSynologyConfig({...synologyConfig, verify_ssl: e.target.checked})}
                className="mr-2"
              />
              <label className="text-blue-200 text-sm">Verify SSL Certificate</label>
            </div>
            
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
            >
              {loading ? 'Updating...' : 'Update Configuration'}
            </button>
          </form>
          
          {message && (
            <div className={`mt-4 p-3 rounded-lg ${
              message.includes('Error') ? 'bg-red-500/20 border border-red-500/50' : 'bg-green-500/20 border border-green-500/50'
            }`}>
              <p className={`text-sm ${message.includes('Error') ? 'text-red-200' : 'text-green-200'}`}>
                {message}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Medical Databases Module
const MedicalDatabasesModule = () => {
  const [activeTab, setActiveTab] = useState('icd10');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchDatabase = async (query, type) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    try {
      const endpoint = type === 'icd10' ? '/icd10/search' : '/comprehensive-medications/search';
      const response = await axios.get(`${API}${endpoint}?query=${encodeURIComponent(query)}`);
      setSearchResults(response.data);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Debounce search
    const timeoutId = setTimeout(() => {
      searchDatabase(query, activeTab);
    }, 300);

    return () => clearTimeout(timeoutId);
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <h2 className="text-xl font-semibold text-white mb-6">Medical Databases</h2>
      
      <div className="space-y-4">
        {/* Tab Navigation */}
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('icd10')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'icd10' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            ICD-10 Codes
          </button>
          <button
            onClick={() => setActiveTab('medications')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'medications' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            Medications
          </button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={handleSearch}
            className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
            placeholder={`Search ${activeTab === 'icd10' ? 'ICD-10 codes' : 'medications'}...`}
          />
          {loading && (
            <div className="absolute right-3 top-3">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
            </div>
          )}
        </div>

        {/* Search Results */}
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {searchResults.map((item, index) => (
            <div
              key={index}
              className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
            >
              {activeTab === 'icd10' ? (
                <div>
                  <div className="text-white font-medium">{item.code}</div>
                  <div className="text-blue-200 text-sm">{item.description}</div>
                </div>
              ) : (
                <div>
                  <div className="text-white font-medium">{item.generic_name}</div>
                  {item.brand_names && item.brand_names.length > 0 && (
                    <div className="text-blue-200 text-sm">Brand: {item.brand_names.join(', ')}</div>
                  )}
                  <div className="text-blue-300 text-sm">Class: {item.drug_class}</div>
                  {item.indication && (
                    <div className="text-blue-300 text-sm">Indication: {item.indication}</div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {searchQuery && searchResults.length === 0 && !loading && (
          <div className="text-center text-blue-200 py-8">
            No results found for "{searchQuery}"
          </div>
        )}
      </div>
    </div>
  );
};

// Communication Module
const CommunicationModule = () => {
  const [activeTab, setActiveTab] = useState('email');
  const [emailData, setEmailData] = useState({
    to: '',
    subject: '',
    body: ''
  });
  const [faxData, setFaxData] = useState({
    to: '',
    document: null
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [commStatus, setCommStatus] = useState(null);

  useEffect(() => {
    fetchCommunicationStatus();
  }, []);

  const fetchCommunicationStatus = async () => {
    try {
      const response = await axios.get(`${API}/communication/status`);
      setCommStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch communication status:', error);
    }
  };

  const sendEmail = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const response = await axios.post(`${API}/communication/send-email`, emailData);
      if (response.data.success) {
        setMessage(`✅ ${response.data.message}`);
        setEmailData({ to: '', subject: '', body: '' });
      } else {
        setMessage(`❌ ${response.data.message}`);
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || 'Failed to send email'}`);
    } finally {
      setLoading(false);
    }
  };

  const sendFax = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const faxPayload = {
        to: faxData.to,
        document: faxData.document?.name || 'uploaded_document.pdf',
        cover_page: true
      };

      const response = await axios.post(`${API}/communication/send-fax`, faxPayload);
      if (response.data.success) {
        setMessage(`✅ ${response.data.message}`);
        setFaxData({ to: '', document: null });
      } else {
        setMessage(`❌ ${response.data.message}`);
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || 'Failed to send fax'}`);
    } finally {
      setLoading(false);
    }
  };

  const initiateCall = async (fromNumber, toNumber) => {
    setLoading(true);
    setMessage('');

    try {
      const callPayload = {
        from_number: fromNumber,
        to_number: toNumber,
        call_type: 'outbound'
      };

      const response = await axios.post(`${API}/communication/voip-call`, callPayload);
      if (response.data.success) {
        setMessage(`✅ ${response.data.message}`);
      } else {
        setMessage(`❌ ${response.data.message}`);
      }
    } catch (error) {
      setMessage(`❌ Error: ${error.response?.data?.detail || 'Failed to initiate call'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Communication Gateway</h2>
        
        {/* Communication Status Indicator */}
        {commStatus && (
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              commStatus.gateway_connected ? 'bg-green-400' : 'bg-yellow-400'
            }`}></div>
            <span className="text-sm text-blue-200">
              Gateway: {commStatus.gateway_connected ? 'Connected' : 'Simulated'}
            </span>
          </div>
        )}
      </div>
      
      <div className="space-y-4">
        {/* Tab Navigation */}
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('email')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'email' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            Email
          </button>
          <button
            onClick={() => setActiveTab('fax')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'fax' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            Fax
          </button>
          <button
            onClick={() => setActiveTab('voip')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'voip' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            VoIP
          </button>
          <button
            onClick={() => setActiveTab('status')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'status' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            Status
          </button>
        </div>

        {/* Email Tab */}
        {activeTab === 'email' && (
          <form onSubmit={sendEmail} className="space-y-4">
            <div>
              <label className="block text-blue-200 text-sm font-medium mb-2">To</label>
              <input
                type="email"
                value={emailData.to}
                onChange={(e) => setEmailData({...emailData, to: e.target.value})}
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="recipient@example.com"
                required
              />
            </div>
            <div>
              <label className="block text-blue-200 text-sm font-medium mb-2">Subject</label>
              <input
                type="text"
                value={emailData.subject}
                onChange={(e) => setEmailData({...emailData, subject: e.target.value})}
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Email subject"
                required
              />
            </div>
            <div>
              <label className="block text-blue-200 text-sm font-medium mb-2">Message</label>
              <textarea
                value={emailData.body}
                onChange={(e) => setEmailData({...emailData, body: e.target.value})}
                rows="4"
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="Email message"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send Email'}
            </button>
          </form>
        )}

        {/* Fax Tab */}
        {activeTab === 'fax' && (
          <form onSubmit={sendFax} className="space-y-4">
            <div>
              <label className="block text-blue-200 text-sm font-medium mb-2">Fax Number</label>
              <input
                type="tel"
                value={faxData.to}
                onChange={(e) => setFaxData({...faxData, to: e.target.value})}
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                placeholder="+1234567890"
                required
              />
            </div>
            <div>
              <label className="block text-blue-200 text-sm font-medium mb-2">Document</label>
              <input
                type="file"
                onChange={(e) => setFaxData({...faxData, document: e.target.files[0]})}
                className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                accept=".pdf,.doc,.docx"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send Fax'}
            </button>
          </form>
        )}

        {/* VoIP Tab */}
        {activeTab === 'voip' && (
          <div className="space-y-4">
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Quick Dial</h3>
              <div className="grid grid-cols-2 gap-4">
                <button
                  onClick={() => initiateCall('clinic-main', '911')}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
                  disabled={loading}
                >
                  Emergency (911)
                </button>
                <button
                  onClick={() => initiateCall('clinic-main', '+1234567890')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                  disabled={loading}
                >
                  Sample Call
                </button>
              </div>
            </div>
            
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="text-white font-medium mb-2">VoIP Features</h3>
              <ul className="text-blue-200 text-sm space-y-1">
                <li>• Outbound calling</li>
                <li>• Call logging and recording</li>
                <li>• Patient communication tracking</li>
                <li>• Integration with clinic workflows</li>
              </ul>
            </div>
          </div>
        )}

        {/* Status Tab */}
        {activeTab === 'status' && commStatus && (
          <div className="space-y-4">
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Gateway Status</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-200">Connection:</span>
                  <span className={`ml-2 ${commStatus.gateway_connected ? 'text-green-400' : 'text-yellow-400'}`}>
                    {commStatus.gateway_connected ? 'Connected' : 'Simulated Mode'}
                  </span>
                </div>
                <div>
                  <span className="text-blue-200">Gateway URL:</span>
                  <span className="text-white ml-2 text-xs">{commStatus.gateway_url}</span>
                </div>
              </div>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="text-white font-medium mb-4">Services Status</h3>
              <div className="space-y-3">
                {Object.entries(commStatus.services).map(([service, info]) => (
                  <div key={service} className="flex items-center justify-between">
                    <div>
                      <span className="text-white capitalize">{service}</span>
                      <span className="text-blue-300 text-sm ml-2">({info.description})</span>
                    </div>
                    <span className={`text-sm px-2 py-1 rounded ${
                      info.status === 'available' ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
                    }`}>
                      {info.status}
                    </span>
                  </div>
                ))}
              </div>
              
              {!commStatus.gateway_connected && (
                <div className="mt-4 p-3 bg-yellow-500/20 border border-yellow-500/50 rounded-lg">
                  <p className="text-yellow-200 text-sm">
                    📝 {commStatus.note}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {message && (
          <div className={`p-3 rounded-lg ${
            message.includes('✅') ? 'bg-green-500/20 border border-green-500/50' : 'bg-red-500/20 border border-red-500/50'
          }`}>
            <p className={`text-sm ${message.includes('✅') ? 'text-green-200' : 'text-red-200'}`}>
              {message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// Patients Module (OpenEMR Integration)
const PatientsModule = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('patients');
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [encounters, setEncounters] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [openemrStatus, setOpenemrStatus] = useState(null);

  useEffect(() => {
    fetchOpenEMRStatus();
    if (activeTab === 'patients') {
      fetchPatients();
    }
  }, [activeTab]);

  const fetchOpenEMRStatus = async () => {
    try {
      const response = await axios.get(`${API}/openemr/status`);
      setOpenemrStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch OpenEMR status:', error);
    }
  };

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/openemr/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientDetails = async (patientId) => {
    setLoading(true);
    try {
      const [encountersRes, prescriptionsRes] = await Promise.all([
        axios.get(`${API}/openemr/patients/${patientId}/encounters`),
        axios.get(`${API}/openemr/patients/${patientId}/prescriptions`)
      ]);
      
      setEncounters(encountersRes.data);
      setPrescriptions(prescriptionsRes.data);
    } catch (error) {
      console.error('Failed to fetch patient details:', error);
      setEncounters([]);
      setPrescriptions([]);
    } finally {
      setLoading(false);
    }
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    fetchPatientDetails(patient.id);
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Patients/EHR (OpenEMR Integration)</h2>
        
        {/* OpenEMR Status Indicator */}
        {openemrStatus && (
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              openemrStatus.status === 'connected' ? 'bg-green-400' : 'bg-red-400'
            }`}></div>
            <span className="text-sm text-blue-200">
              OpenEMR: {openemrStatus.status}
            </span>
          </div>
        )}
      </div>
      
      <div className="space-y-4">
        {/* Tab Navigation */}
        <div className="flex space-x-2">
          <button
            onClick={() => setActiveTab('patients')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'patients' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            Patient List
          </button>
          <button
            onClick={() => setActiveTab('details')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'details' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
            disabled={!selectedPatient}
          >
            Patient Details
          </button>
        </div>

        {/* Patient List Tab */}
        {activeTab === 'patients' && (
          <div className="space-y-2">
            {loading ? (
              <div className="text-center text-blue-200 py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
                Loading patients...
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 gap-3">
                  {patients.map((patient) => (
                    <div
                      key={patient.id}
                      onClick={() => handlePatientSelect(patient)}
                      className={`bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors cursor-pointer ${
                        selectedPatient?.id === patient.id ? 'bg-blue-600/20 border-blue-400/50' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-white font-medium">
                            {patient.fname} {patient.lname}
                          </div>
                          <div className="text-blue-200 text-sm">
                            DOB: {patient.DOB} | {patient.sex}
                          </div>
                        </div>
                        <div className="text-blue-300 text-sm">
                          {patient.phone_home}
                        </div>
                      </div>
                      <div className="text-blue-300 text-sm mt-2">
                        {patient.street}, {patient.city}, {patient.state} {patient.postal_code}
                      </div>
                    </div>
                  ))}
                </div>
                
                {patients.length === 0 && !loading && (
                  <div className="text-center text-blue-200 py-8">
                    No patients found in OpenEMR
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Patient Details Tab */}
        {activeTab === 'details' && selectedPatient && (
          <div className="space-y-6">
            {/* Patient Info */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h3 className="text-lg font-medium text-white mb-4">
                {selectedPatient.fname} {selectedPatient.lname}
              </h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-200">Date of Birth:</span>
                  <span className="text-white ml-2">{selectedPatient.DOB}</span>
                </div>
                <div>
                  <span className="text-blue-200">Gender:</span>
                  <span className="text-white ml-2">{selectedPatient.sex}</span>
                </div>
                <div>
                  <span className="text-blue-200">Phone:</span>
                  <span className="text-white ml-2">{selectedPatient.phone_home}</span>
                </div>
                <div>
                  <span className="text-blue-200">Patient ID:</span>
                  <span className="text-white ml-2">{selectedPatient.id}</span>
                </div>
              </div>
            </div>

            {/* Encounters */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h4 className="text-lg font-medium text-white mb-3">Recent Encounters</h4>
              {loading ? (
                <div className="text-blue-200 text-sm">Loading encounters...</div>
              ) : encounters.length > 0 ? (
                <div className="space-y-2">
                  {encounters.map((encounter) => (
                    <div key={encounter.id} className="bg-white/5 rounded-lg p-3">
                      <div className="text-white font-medium">{encounter.reason}</div>
                      <div className="text-blue-200 text-sm">
                        {encounter.date} | Provider: {encounter.provider}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-blue-200 text-sm">No encounters found</div>
              )}
            </div>

            {/* Prescriptions */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <h4 className="text-lg font-medium text-white mb-3">Current Prescriptions</h4>
              {loading ? (
                <div className="text-blue-200 text-sm">Loading prescriptions...</div>
              ) : prescriptions.length > 0 ? (
                <div className="space-y-2">
                  {prescriptions.map((prescription) => (
                    <div key={prescription.id} className="bg-white/5 rounded-lg p-3">
                      <div className="text-white font-medium">{prescription.drug}</div>
                      <div className="text-blue-200 text-sm">
                        {prescription.directions}
                      </div>
                      <div className="text-blue-300 text-sm">
                        Qty: {prescription.quantity} | Refills: {prescription.refills}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-blue-200 text-sm">No prescriptions found</div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

function AppContent() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
          <p>Loading ClinicHub...</p>
        </div>
      </div>
    );
  }

  return user ? <Dashboard /> : <LoginPage />;
}

export default App;