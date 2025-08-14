import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

// Force correct backend URL since environment variables aren't loading properly
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://192.168.0.243:8001';
const API = `${BACKEND_URL}/api`;

console.log('Environment check:', {
  REACT_APP_BACKEND_URL: process.env.REACT_APP_BACKEND_URL,
  BACKEND_URL,
  API,
  FORCED_URL: 'http://192.168.0.243:8001'
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

// Comprehensive Invoices/Receipts Module with SOAP Integration
const InvoicesModule = ({ setActiveModule }) => {
  const [invoices, setInvoices] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [patients, setPatients] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [newInvoice, setNewInvoice] = useState({
    patient_id: '',
    description: '',
    items: [{
      description: '',
      quantity: 1,
      unit_price: 0,
      inventory_item_id: null,
      is_service: true
    }],
    notes: '',
    due_days: 30
  });
  const [paymentData, setPaymentData] = useState({
    amount: 0,
    payment_method: 'cash',
    notes: ''
  });

  useEffect(() => {
    fetchInvoices();
    fetchPatients();
    fetchInventory();
  }, []);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data);
    } catch (error) {
      console.error('Failed to fetch invoices:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    }
  };

  const fetchInventory = async () => {
    try {
      const response = await axios.get(`${API}/inventory`);
      setInventory(response.data);
    } catch (error) {
      console.error('Failed to fetch inventory:', error);
    }
  };

  const calculateInvoiceTotal = (items) => {
    return items.reduce((total, item) => total + (item.quantity * item.unit_price), 0).toFixed(2);
  };

  const handleCreateInvoice = async (e) => {
    e.preventDefault();
    try {
      const invoiceData = {
        ...newInvoice,
        total_amount: calculateInvoiceTotal(newInvoice.items),
        status: 'pending',
        issue_date: new Date().toISOString().split('T')[0],
        due_date: new Date(Date.now() + newInvoice.due_days * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      };
      
      const response = await axios.post(`${API}/invoices`, invoiceData);
      setInvoices([response.data, ...invoices]);
      setNewInvoice({
        patient_id: '',
        description: '',
        items: [{
          description: '',
          quantity: 1,
          unit_price: 0,
          inventory_item_id: null,
          is_service: true
        }],
        notes: '',
        due_days: 30
      });
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create invoice:', error);
    }
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    if (!selectedInvoice) return;
    
    try {
      // Process payment
      const response = await axios.post(`${API}/invoices/${selectedInvoice.id}/payment`, paymentData);
      
      // Update invoice status
      const updatedInvoices = invoices.map(inv => 
        inv.id === selectedInvoice.id 
          ? { ...inv, status: 'paid', paid_date: new Date().toISOString().split('T')[0] }
          : inv
      );
      setInvoices(updatedInvoices);
      
      // Deduct inventory for non-service items
      const inventoryUpdates = selectedInvoice.items
        .filter(item => !item.is_service && item.inventory_item_id)
        .map(item => ({
          item_id: item.inventory_item_id,
          quantity_used: item.quantity
        }));
      
      if (inventoryUpdates.length > 0) {
        await axios.post(`${API}/inventory/deduct-batch`, { updates: inventoryUpdates });
      }
      
      setPaymentData({ amount: 0, payment_method: 'cash', notes: '' });
      setShowPaymentForm(false);
      setSelectedInvoice(null);
    } catch (error) {
      console.error('Failed to process payment:', error);
    }
  };

  const addInvoiceItem = () => {
    setNewInvoice({
      ...newInvoice,
      items: [...newInvoice.items, {
        description: '',
        quantity: 1,
        unit_price: 0,
        inventory_item_id: null,
        is_service: true
      }]
    });
  };

  const removeInvoiceItem = (index) => {
    const updatedItems = newInvoice.items.filter((_, i) => i !== index);
    setNewInvoice({ ...newInvoice, items: updatedItems });
  };

  const updateInvoiceItem = (index, field, value) => {
    const updatedItems = newInvoice.items.map((item, i) => 
      i === index ? { ...item, [field]: value } : item
    );
    setNewInvoice({ ...newInvoice, items: updatedItems });
  };

  const generateSOAPInvoice = async (patientId, planItems) => {
    // Generate invoice from SOAP note plan section
    const soapInvoiceItems = planItems.map(planItem => ({
      description: planItem.description,
      quantity: planItem.quantity || 1,
      unit_price: planItem.estimated_cost || 0,
      inventory_item_id: planItem.inventory_item_id || null,
      is_service: !planItem.inventory_item_id
    }));

    setNewInvoice({
      patient_id: patientId,
      description: 'Generated from SOAP Note Plan',
      items: soapInvoiceItems,
      notes: 'Auto-generated from treatment plan',
      due_days: 30
    });
    setShowCreateForm(true);
  };

  const renderOverview = () => {
    const stats = {
      total: invoices.length,
      pending: invoices.filter(inv => inv.status === 'pending').length,
      paid: invoices.filter(inv => inv.status === 'paid').length,
      overdue: invoices.filter(inv => {
        const dueDate = new Date(inv.due_date);
        const today = new Date();
        return inv.status === 'pending' && dueDate < today;
      }).length,
      totalRevenue: invoices
        .filter(inv => inv.status === 'paid')
        .reduce((sum, inv) => sum + parseFloat(inv.total_amount), 0),
      pendingRevenue: invoices
        .filter(inv => inv.status === 'pending')
        .reduce((sum, inv) => sum + parseFloat(inv.total_amount), 0)
    };

    return (
      <div className="space-y-6">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">{stats.total}</div>
            <div className="text-blue-200 text-sm">Total Invoices</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-400">{stats.pending}</div>
            <div className="text-blue-200 text-sm">Pending</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-400">{stats.paid}</div>
            <div className="text-blue-200 text-sm">Paid</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-400">{stats.overdue}</div>
            <div className="text-blue-200 text-sm">Overdue</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-400">${stats.totalRevenue.toFixed(2)}</div>
            <div className="text-blue-200 text-sm">Total Revenue</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-400">${stats.pendingRevenue.toFixed(2)}</div>
            <div className="text-blue-200 text-sm">Pending Revenue</div>
          </div>
        </div>

        {/* Recent Invoices */}
        <div className="bg-white/5 border border-white/10 rounded-lg">
          <div className="p-4 border-b border-white/10">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-white">Recent Invoices</h3>
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + Create Invoice
              </button>
            </div>
          </div>
          
          {loading ? (
            <div className="text-center text-blue-200 py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
              Loading invoices...
            </div>
          ) : (
            <div className="p-4">
              {invoices.length > 0 ? (
                <div className="space-y-4">
                  {invoices.slice(0, 10).map((invoice) => (
                    <div
                      key={invoice.id}
                      className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <div>
                              <div className="text-white font-medium">
                                Invoice #{invoice.invoice_number}
                              </div>
                              <div className="text-blue-200 text-sm">
                                Patient: {invoice.patient_name || 'N/A'}
                              </div>
                            </div>
                          </div>
                          <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                              <div className="text-blue-200 text-xs">Amount</div>
                              <div className="text-white text-sm font-bold">${invoice.total_amount}</div>
                            </div>
                            <div>
                              <div className="text-blue-200 text-xs">Status</div>
                              <div className={`text-sm capitalize ${
                                invoice.status === 'paid' ? 'text-green-400' :
                                invoice.status === 'pending' ? 'text-yellow-400' :
                                'text-red-400'
                              }`}>
                                {invoice.status}
                              </div>
                            </div>
                            <div>
                              <div className="text-blue-200 text-xs">Issue Date</div>
                              <div className="text-white text-sm">{invoice.issue_date}</div>
                            </div>
                            <div>
                              <div className="text-blue-200 text-xs">Due Date</div>
                              <div className="text-white text-sm">{invoice.due_date || 'N/A'}</div>
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => setSelectedInvoice(invoice)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                          >
                            View
                          </button>
                          {invoice.status === 'pending' && (
                            <button
                              onClick={() => {
                                setSelectedInvoice(invoice);
                                setPaymentData({ 
                                  ...paymentData, 
                                  amount: parseFloat(invoice.total_amount) 
                                });
                                setShowPaymentForm(true);
                              }}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                            >
                              Pay
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-blue-200 py-8">
                  No invoices found. Click "Create Invoice" to get started.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderInvoiceDetail = () => {
    if (!selectedInvoice) return null;

    return (
      <div className="space-y-6">
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-2xl font-bold text-white">Invoice #{selectedInvoice.invoice_number}</h3>
              <div className="text-blue-200">Patient: {selectedInvoice.patient_name || 'N/A'}</div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              selectedInvoice.status === 'paid' ? 'bg-green-600 text-white' :
              selectedInvoice.status === 'pending' ? 'bg-yellow-600 text-white' :
              'bg-red-600 text-white'
            }`}>
              {selectedInvoice.status.toUpperCase()}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <div className="text-blue-200 text-sm">Issue Date</div>
              <div className="text-white font-medium">{selectedInvoice.issue_date}</div>
            </div>
            <div>
              <div className="text-blue-200 text-sm">Due Date</div>
              <div className="text-white font-medium">{selectedInvoice.due_date || 'N/A'}</div>
            </div>
            <div>
              <div className="text-blue-200 text-sm">Total Amount</div>
              <div className="text-white font-bold text-xl">${selectedInvoice.total_amount}</div>
            </div>
          </div>

          {/* Invoice Items */}
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <h4 className="text-lg font-medium text-white mb-4">Items & Services</h4>
            <div className="space-y-3">
              {selectedInvoice.items && selectedInvoice.items.map((item, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-white/5 rounded">
                  <div className="flex-1">
                    <div className="text-white font-medium">{item.description}</div>
                    <div className="text-blue-200 text-sm">
                      {item.is_service ? '🔧 Service' : '📦 Product'} • 
                      Qty: {item.quantity} × ${item.unit_price}
                    </div>
                  </div>
                  <div className="text-white font-bold">${(item.quantity * item.unit_price).toFixed(2)}</div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 pt-4 border-t border-white/20">
              <div className="flex justify-between text-xl font-bold text-white">
                <span>Total:</span>
                <span>${selectedInvoice.total_amount}</span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4 mt-6">
            <button
              onClick={() => window.print()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
            >
              🖨️ Print Receipt
            </button>
            {selectedInvoice.status === 'pending' && (
              <button
                onClick={() => {
                  setPaymentData({ 
                    ...paymentData, 
                    amount: parseFloat(selectedInvoice.total_amount) 
                  });
                  setShowPaymentForm(true);
                }}
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg"
              >
                💳 Process Payment
              </button>
            )}
            <button
              onClick={() => setSelectedInvoice(null)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
            >
              Back to List
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderCreateForm = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-screen overflow-y-auto">
        <h3 className="text-lg font-medium text-white mb-6">Create New Invoice</h3>
        <form onSubmit={handleCreateInvoice} className="space-y-6">
          {/* Patient Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
            <select
              required
              value={newInvoice.patient_id}
              onChange={(e) => setNewInvoice({...newInvoice, patient_id: e.target.value})}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="">Select Patient</option>
              {patients.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.name ? patient.name.given?.[0] : ''} {patient.name ? patient.name.family : ''} - {patient.id}
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <input
              type="text"
              required
              value={newInvoice.description}
              onChange={(e) => setNewInvoice({...newInvoice, description: e.target.value})}
              placeholder="Brief description of services/products"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>

          {/* Invoice Items */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <label className="block text-sm font-medium text-gray-300">Items & Services</label>
              <button
                type="button"
                onClick={addInvoiceItem}
                className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
              >
                + Add Item
              </button>
            </div>
            
            <div className="space-y-4">
              {newInvoice.items.map((item, index) => (
                <div key={index} className="bg-gray-700 p-4 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                    <div className="md:col-span-2">
                      <label className="block text-xs text-gray-400 mb-1">Description</label>
                      <input
                        type="text"
                        required
                        value={item.description}
                        onChange={(e) => updateInvoiceItem(index, 'description', e.target.value)}
                        className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Quantity</label>
                      <input
                        type="number"
                        min="1"
                        required
                        value={item.quantity}
                        onChange={(e) => updateInvoiceItem(index, 'quantity', parseInt(e.target.value))}
                        className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Unit Price</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        required
                        value={item.unit_price}
                        onChange={(e) => updateInvoiceItem(index, 'unit_price', parseFloat(e.target.value))}
                        className="w-full px-3 py-2 bg-gray-600 border border-gray-500 rounded text-white text-sm"
                      />
                    </div>
                    <div className="flex items-end">
                      <button
                        type="button"
                        onClick={() => removeInvoiceItem(index)}
                        className="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded text-sm"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  
                  <div className="mt-3 flex items-center space-x-4">
                    <label className="flex items-center text-gray-300 text-sm">
                      <input
                        type="checkbox"
                        checked={item.is_service}
                        onChange={(e) => updateInvoiceItem(index, 'is_service', e.target.checked)}
                        className="mr-2"
                      />
                      Service (no inventory deduction)
                    </label>
                    {!item.is_service && (
                      <select
                        value={item.inventory_item_id || ''}
                        onChange={(e) => updateInvoiceItem(index, 'inventory_item_id', e.target.value)}
                        className="px-3 py-1 bg-gray-600 border border-gray-500 rounded text-white text-sm"
                      >
                        <option value="">Select Inventory Item</option>
                        {inventory.map((invItem) => (
                          <option key={invItem.id} value={invItem.id}>
                            {invItem.name} (Stock: {invItem.current_stock})
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                  
                  <div className="mt-2 text-right">
                    <span className="text-gray-300 text-sm">
                      Subtotal: ${(item.quantity * item.unit_price).toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 text-right">
              <div className="text-xl font-bold text-white">
                Total: ${calculateInvoiceTotal(newInvoice.items)}
              </div>
            </div>
          </div>

          {/* Notes and Due Date */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
              <textarea
                value={newInvoice.notes}
                onChange={(e) => setNewInvoice({...newInvoice, notes: e.target.value})}
                rows={3}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Due Days</label>
              <select
                value={newInvoice.due_days}
                onChange={(e) => setNewInvoice({...newInvoice, due_days: parseInt(e.target.value)})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value={0}>Due Immediately</option>
                <option value={15}>15 Days</option>
                <option value={30}>30 Days</option>
                <option value={60}>60 Days</option>
                <option value={90}>90 Days</option>
              </select>
            </div>
          </div>
          
          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium"
            >
              Create Invoice
            </button>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-3 rounded-lg font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  const renderPaymentForm = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-medium text-white mb-6">
          Process Payment - Invoice #{selectedInvoice?.invoice_number}
        </h3>
        <form onSubmit={handlePayment} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Payment Amount</label>
            <input
              type="number"
              step="0.01"
              min="0"
              required
              value={paymentData.amount}
              onChange={(e) => setPaymentData({...paymentData, amount: parseFloat(e.target.value)})}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Payment Method</label>
            <select
              value={paymentData.payment_method}
              onChange={(e) => setPaymentData({...paymentData, payment_method: e.target.value})}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="cash">Cash</option>
              <option value="card">Credit/Debit Card</option>
              <option value="check">Check</option>
              <option value="bank_transfer">Bank Transfer</option>
              <option value="insurance">Insurance</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
            <textarea
              value={paymentData.notes}
              onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
              rows={3}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>
          
          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 rounded-lg"
            >
              Process Payment
            </button>
            <button
              type="button"
              onClick={() => setShowPaymentForm(false)}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded-lg"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Invoice Management</h2>
        <button
          onClick={() => setActiveModule('dashboard')}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'detail', name: 'Invoice Detail', icon: '📋', disabled: !selectedInvoice }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-400 text-blue-400'
                  : tab.disabled
                  ? 'border-transparent text-gray-500 cursor-not-allowed'
                  : 'border-transparent text-gray-300 hover:text-white'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'detail' && renderInvoiceDetail()}

      {/* Modals */}
      {showCreateForm && renderCreateForm()}
      {showPaymentForm && renderPaymentForm()}
    </div>
  );
};

// Employees Module - Comprehensive Employee Management System
const EmployeesModule = ({ setActiveModule }) => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEmployee, setNewEmployee] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: 'staff',
    department: '',
    hire_date: new Date().toISOString().split('T')[0],
    salary: '',
    employment_type: 'full_time',
    benefits_eligible: true,
    vacation_days_allocated: 15,
    sick_days_allocated: 10
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/employees`);
      setEmployees(response.data);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/employees`, newEmployee);
      setEmployees([...employees, response.data]);
      setNewEmployee({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        role: 'staff',
        department: '',
        hire_date: new Date().toISOString().split('T')[0],
        salary: '',
        employment_type: 'full_time',
        benefits_eligible: true,
        vacation_days_allocated: 15,
        sick_days_allocated: 10
      });
      setShowAddForm(false);
    } catch (error) {
      console.error('Failed to add employee:', error);
    }
  };

  const handleDeleteEmployee = async (employeeId) => {
    if (window.confirm('Are you sure you want to delete this employee?')) {
      try {
        await axios.delete(`${API}/employees/${employeeId}`);
        setEmployees(employees.filter(emp => emp.id !== employeeId));
      } catch (error) {
        console.error('Failed to delete employee:', error);
      }
    }
  };

  const renderEmployeeOverview = () => (
    <div className="space-y-6">
      {/* Employee Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">{employees.length}</div>
          <div className="text-blue-200 text-sm">Total Employees</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">
            {employees.filter(emp => emp.role === 'doctor').length}
          </div>
          <div className="text-blue-200 text-sm">Doctors</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">
            {employees.filter(emp => emp.role === 'nurse').length}
          </div>
          <div className="text-blue-200 text-sm">Nurses</div>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">
            {employees.filter(emp => emp.employment_type === 'full_time').length}
          </div>
          <div className="text-blue-200 text-sm">Full-Time</div>
        </div>
      </div>

      {/* Employee List */}
      <div className="bg-white/5 border border-white/10 rounded-lg">
        <div className="p-4 border-b border-white/10">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-white">Employee Directory</h3>
            <button
              onClick={() => setShowAddForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
            >
              + Add Employee
            </button>
          </div>
        </div>
        
        {loading ? (
          <div className="text-center text-blue-200 py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
            Loading employees...
          </div>
        ) : (
          <div className="p-4">
            {employees.length > 0 ? (
              <div className="space-y-4">
                {employees.map((employee) => (
                  <div
                    key={employee.id}
                    className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                            <span className="text-white font-medium">
                              {employee.first_name?.[0]}{employee.last_name?.[0]}
                            </span>
                          </div>
                          <div>
                            <div className="text-white font-medium">
                              {employee.first_name} {employee.last_name}
                            </div>
                            <div className="text-blue-200 text-sm">ID: {employee.employee_id}</div>
                          </div>
                        </div>
                        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <div className="text-blue-200 text-xs">Role</div>
                            <div className="text-white text-sm capitalize">{employee.role}</div>
                          </div>
                          <div>
                            <div className="text-blue-200 text-xs">Department</div>
                            <div className="text-white text-sm">{employee.department || 'N/A'}</div>
                          </div>
                          <div>
                            <div className="text-blue-200 text-xs">Email</div>
                            <div className="text-white text-sm">{employee.email}</div>
                          </div>
                          <div>
                            <div className="text-blue-200 text-xs">Status</div>
                            <div className="text-green-400 text-sm">Active</div>
                          </div>
                        </div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => setSelectedEmployee(employee)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        >
                          View
                        </button>
                        <button
                          onClick={() => handleDeleteEmployee(employee.id)}
                          className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-blue-200 py-8">
                No employees found. Click "Add Employee" to get started.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  const renderTimeTracking = () => (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Time Clock</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <button className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded-lg font-medium">
              ⏰ Clock In
            </button>
          </div>
          <div>
            <button className="w-full bg-red-600 hover:bg-red-700 text-white py-3 rounded-lg font-medium">
              ⏰ Clock Out
            </button>
          </div>
        </div>
      </div>
      
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Today's Attendance</h3>
        <div className="space-y-3">
          {employees.slice(0, 5).map((employee) => (
            <div key={employee.id} className="flex justify-between items-center py-2">
              <div>
                <div className="text-white">{employee.first_name} {employee.last_name}</div>
                <div className="text-blue-200 text-sm">{employee.role}</div>
              </div>
              <div className="text-right">
                <div className="text-green-400 text-sm">Present</div>
                <div className="text-blue-200 text-xs">8:00 AM - Present</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderPayroll = () => (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Payroll Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">$45,250</div>
            <div className="text-blue-200 text-sm">This Period</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">$542,000</div>
            <div className="text-blue-200 text-sm">YTD Total</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">Next Friday</div>
            <div className="text-blue-200 text-sm">Next Payday</div>
          </div>
        </div>
      </div>
      
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Payroll Actions</h3>
        <div className="flex space-x-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
            Process Payroll
          </button>
          <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">
            Generate Reports
          </button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg">
            Print Checks
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Employee Management</h2>
        <button
          onClick={() => setActiveModule('dashboard')}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '👥' },
            { id: 'timetracking', name: 'Time & Attendance', icon: '⏰' },
            { id: 'payroll', name: 'Payroll', icon: '💰' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeTab === tab.id
                  ? 'border-blue-400 text-blue-400'
                  : 'border-transparent text-gray-300 hover:text-white'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && renderEmployeeOverview()}
      {activeTab === 'timetracking' && renderTimeTracking()}
      {activeTab === 'payroll' && renderPayroll()}

      {/* Add Employee Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
            <h3 className="text-lg font-medium text-white mb-4">Add New Employee</h3>
            <form onSubmit={handleAddEmployee} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">First Name</label>
                  <input
                    type="text"
                    required
                    value={newEmployee.first_name}
                    onChange={(e) => setNewEmployee({...newEmployee, first_name: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Last Name</label>
                  <input
                    type="text"
                    required
                    value={newEmployee.last_name}
                    onChange={(e) => setNewEmployee({...newEmployee, last_name: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={newEmployee.email}
                  onChange={(e) => setNewEmployee({...newEmployee, email: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Phone</label>
                <input
                  type="tel"
                  value={newEmployee.phone}
                  onChange={(e) => setNewEmployee({...newEmployee, phone: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Role</label>
                  <select
                    value={newEmployee.role}
                    onChange={(e) => setNewEmployee({...newEmployee, role: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  >
                    <option value="doctor">Doctor</option>
                    <option value="nurse">Nurse</option>
                    <option value="technician">Technician</option>
                    <option value="admin">Admin</option>
                    <option value="staff">Staff</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Department</label>
                  <input
                    type="text"
                    value={newEmployee.department}
                    onChange={(e) => setNewEmployee({...newEmployee, department: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Hire Date</label>
                  <input
                    type="date"
                    value={newEmployee.hire_date}
                    onChange={(e) => setNewEmployee({...newEmployee, hire_date: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Salary</label>
                  <input
                    type="number"
                    value={newEmployee.salary}
                    onChange={(e) => setNewEmployee({...newEmployee, salary: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
                  />
                </div>
              </div>
              
              <div className="flex space-x-4 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
                >
                  Add Employee
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded-lg"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Employee Detail Modal */}
      {selectedEmployee && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-medium text-white">
                {selectedEmployee.first_name} {selectedEmployee.last_name}
              </h3>
              <button
                onClick={() => setSelectedEmployee(null)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-gray-300 text-sm">Employee ID</div>
                  <div className="text-white">{selectedEmployee.employee_id}</div>
                </div>
                <div>
                  <div className="text-gray-300 text-sm">Role</div>
                  <div className="text-white capitalize">{selectedEmployee.role}</div>
                </div>
                <div>
                  <div className="text-gray-300 text-sm">Department</div>
                  <div className="text-white">{selectedEmployee.department || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-gray-300 text-sm">Email</div>
                  <div className="text-white">{selectedEmployee.email}</div>
                </div>
                <div>
                  <div className="text-gray-300 text-sm">Phone</div>
                  <div className="text-white">{selectedEmployee.phone || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-gray-300 text-sm">Hire Date</div>
                  <div className="text-white">{selectedEmployee.hire_date || 'N/A'}</div>
                </div>
              </div>
              
              <div className="pt-4">
                <button
                  onClick={() => setSelectedEmployee(null)}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Inventory Module
const InventoryModule = ({ setActiveModule }) => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/inventory`);
      setInventory(response.data);
    } catch (error) {
      console.error('Failed to fetch inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Inventory Management</h2>
        <button
          onClick={() => setActiveModule('dashboard')}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>
      
      {loading ? (
        <div className="text-center text-blue-200 py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
          Loading inventory...
        </div>
      ) : (
        <div className="space-y-4">
          {inventory.length > 0 ? (
            inventory.map((item) => (
              <div
                key={item.id}
                className="bg-white/5 border border-white/10 rounded-lg p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">{item.name}</div>
                    <div className="text-blue-200 text-sm">SKU: {item.sku || 'N/A'}</div>
                    <div className="text-blue-300 text-sm">Category: {item.category}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold">Stock: {item.current_stock}</div>
                    <div className="text-blue-300 text-sm">Min: {item.min_stock_level}</div>
                    <div className="text-blue-300 text-sm">Cost: ${item.unit_cost}</div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-blue-200 py-8">
              No inventory items found
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Finance Module
const FinanceModule = ({ setActiveModule }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/financial-transactions`);
      setTransactions(response.data);
    } catch (error) {
      console.error('Failed to fetch transactions:', error);
    } finally {
      setLoading(false);
    }
  };

  const totalIncome = transactions
    .filter(t => t.transaction_type === 'income')
    .reduce((sum, t) => sum + t.amount, 0);

  const totalExpenses = transactions
    .filter(t => t.transaction_type === 'expense')
    .reduce((sum, t) => sum + t.amount, 0);

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Financial Management</h2>
        <button
          onClick={() => setActiveModule('dashboard')}
          className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>
      
      {/* Financial Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-green-600/20 border border-green-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">${totalIncome.toFixed(2)}</div>
          <div className="text-green-200 text-sm">Total Income</div>
        </div>
        <div className="bg-red-600/20 border border-red-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">${totalExpenses.toFixed(2)}</div>
          <div className="text-red-200 text-sm">Total Expenses</div>
        </div>
        <div className="bg-blue-600/20 border border-blue-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">${(totalIncome - totalExpenses).toFixed(2)}</div>
          <div className="text-blue-200 text-sm">Net Income</div>
        </div>
      </div>
      
      {loading ? (
        <div className="text-center text-blue-200 py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
          Loading transactions...
        </div>
      ) : (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-white">Recent Transactions</h3>
          {transactions.length > 0 ? (
            transactions.slice(0, 10).map((transaction) => (
              <div
                key={transaction.id}
                className="bg-white/5 border border-white/10 rounded-lg p-4"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">{transaction.description}</div>
                    <div className="text-blue-200 text-sm">
                      {transaction.transaction_number} | {transaction.transaction_date}
                    </div>
                    <div className="text-blue-300 text-sm capitalize">
                      {transaction.payment_method} | {transaction.category || 'N/A'}
                    </div>
                  </div>
                  <div className={`text-lg font-bold ${
                    transaction.transaction_type === 'income' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {transaction.transaction_type === 'income' ? '+' : '-'}${transaction.amount}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-blue-200 py-8">
              No transactions found
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default App;