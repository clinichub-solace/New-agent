import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

// Force correct backend URL since environment variables aren't loading properly
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

// Add axios timeout to prevent hanging requests
axios.defaults.timeout = 10000; // 10 second timeout

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
      case 'scheduling':
        return <SchedulingModule setActiveModule={setActiveModule} />;
      case 'telehealth':
        return <TelehealthModule setActiveModule={setActiveModule} />;
      case 'patient-portal':
        return <PatientPortalModule setActiveModule={setActiveModule} />;
      case 'lab-orders':
        return <LabOrdersModule setActiveModule={setActiveModule} />;
      case 'insurance':
        return <InsuranceModule setActiveModule={setActiveModule} />;
      case 'clinical-templates':
        return <ClinicalTemplatesModule setActiveModule={setActiveModule} />;
      case 'quality-measures':
        return <QualityMeasuresModule setActiveModule={setActiveModule} />;
      case 'documents':
        return <DocumentManagementModule setActiveModule={setActiveModule} />;
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
      case 'referrals':
        return <ReferralsModule setActiveModule={setActiveModule} />;
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

// Patients Module (FHIR-Compliant EHR)
const PatientsModule = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('patients');
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // EHR Data states
  const [soapNotes, setSoapNotes] = useState([]);
  const [vitalSigns, setVitalSigns] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [medications, setMedications] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [medicalHistory, setMedicalHistory] = useState([]);

  // Form states
  const [showSoapForm, setShowSoapForm] = useState(false);
  const [showVitalsForm, setShowVitalsForm] = useState(false);
  const [showAllergyForm, setShowAllergyForm] = useState(false);
  const [showMedicationForm, setShowMedicationForm] = useState(false);
  const [showPrescriptionForm, setShowPrescriptionForm] = useState(false);
  const [showHistoryForm, setShowHistoryForm] = useState(false);

  // Editing states
  const [editingSoapNote, setEditingSoapNote] = useState(null);
  const [editingVitals, setEditingVitals] = useState(null);
  const [editingAllergy, setEditingAllergy] = useState(null);

  // Form data states
  const [soapFormData, setSoapFormData] = useState({
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
    provider: user?.username || 'Dr. Provider'
  });

  const [vitalsFormData, setVitalsFormData] = useState({
    temperature: '',
    blood_pressure_systolic: '',
    blood_pressure_diastolic: '',
    heart_rate: '',
    respiratory_rate: '',
    oxygen_saturation: '',
    weight: '',
    height: '',
    notes: ''
  });

  const [allergyFormData, setAllergyFormData] = useState({
    allergen: '',
    reaction: '',
    severity: 'mild',
    onset_date: '',
    notes: ''
  });

  const [medicationFormData, setMedicationFormData] = useState({
    name: '',
    dosage: '',
    frequency: '',
    route: 'oral',
    start_date: '',
    end_date: '',
    prescribing_physician: user?.username || 'Dr. Provider',
    instructions: ''
  });

  const [prescriptionFormData, setPrescriptionFormData] = useState({
    medication_name: '',
    dosage: '',
    quantity: '',
    frequency: '',
    duration: '',
    instructions: '',
    refills: 0
  });

  const [historyFormData, setHistoryFormData] = useState({
    condition: '',
    diagnosis_date: '',
    status: 'active',
    notes: ''
  });

  // Form state for adding new patient
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    gender: '',
    address_line1: '',
    city: '',
    state: '',
    zip_code: ''
  });

  useEffect(() => {
    if (activeTab === 'patients') {
      fetchPatients();
    }
  }, [activeTab]);

  useEffect(() => {
    if (selectedPatient && activeTab === 'details') {
      fetchAllPatientData(selectedPatient.id);
    }
  }, [selectedPatient, activeTab]);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
      setError('');
    } catch (error) {
      console.error('Failed to fetch patients:', error);
      setError('Failed to fetch patients. Please try again.');
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllPatientData = async (patientId) => {
    try {
      const [soapResponse, vitalsResponse, allergiesResponse, medicationsResponse, prescriptionsResponse] = await Promise.all([
        axios.get(`${API}/soap-notes/patient/${patientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/vital-signs/patient/${patientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/allergies/patient/${patientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/medications/patient/${patientId}`).catch(() => ({ data: [] })),
        axios.get(`${API}/patients/${patientId}/prescriptions`).catch(() => ({ data: [] }))
      ]);

      setSoapNotes(soapResponse.data);
      setVitalSigns(vitalsResponse.data);
      setAllergies(allergiesResponse.data);
      setMedications(medicationsResponse.data);
      setPrescriptions(prescriptionsResponse.data);
    } catch (error) {
      console.error('Failed to fetch patient data:', error);
    }
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    setActiveTab('details');
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSoapInputChange = (e) => {
    const { name, value } = e.target;
    setSoapFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleVitalsInputChange = (e) => {
    const { name, value } = e.target;
    setVitalsFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleAllergyInputChange = (e) => {
    const { name, value } = e.target;
    setAllergyFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleMedicationInputChange = (e) => {
    const { name, value } = e.target;
    setMedicationFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePrescriptionInputChange = (e) => {
    const { name, value } = e.target;
    setPrescriptionFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post(`${API}/patients`, formData);
      setSuccess('Patient added successfully!');
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        date_of_birth: '',
        gender: '',
        address_line1: '',
        city: '',
        state: '',
        zip_code: ''
      });
      setShowAddForm(false);
      fetchPatients(); // Refresh the patient list
    } catch (error) {
      console.error('Failed to add patient:', error);
      setError(error.response?.data?.detail || 'Failed to add patient. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // SOAP Notes Submit
  const handleSoapSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // First create an encounter if needed
      const encounterData = {
        patient_id: selectedPatient.id,
        encounter_type: 'office_visit',
        scheduled_date: new Date().toISOString(),
        provider: soapFormData.provider,
        chief_complaint: 'SOAP note documentation',
        reason_for_visit: 'Clinical documentation'
      };

      const encounterResponse = await axios.post(`${API}/encounters`, encounterData);
      const encounterId = encounterResponse.data.id;

      // Create SOAP note
      const soapData = {
        encounter_id: encounterId,
        patient_id: selectedPatient.id,
        ...soapFormData
      };

      let response;
      if (editingSoapNote) {
        response = await axios.put(`${API}/soap-notes/${editingSoapNote.id}`, soapData);
        setSuccess('SOAP note updated successfully!');
      } else {
        response = await axios.post(`${API}/soap-notes`, soapData);
        setSuccess('SOAP note added successfully!');
      }

      setSoapFormData({
        subjective: '',
        objective: '',
        assessment: '',
        plan: '',
        provider: user?.username || 'Dr. Provider'
      });
      setShowSoapForm(false);
      setEditingSoapNote(null);
      fetchAllPatientData(selectedPatient.id); // Refresh data
    } catch (error) {
      console.error('Failed to save SOAP note:', error);
      setError(error.response?.data?.detail || 'Failed to save SOAP note. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Vitals Submit
  const handleVitalsSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const vitalsData = {
        patient_id: selectedPatient.id,
        ...vitalsFormData,
        temperature: parseFloat(vitalsFormData.temperature) || 0,
        blood_pressure_systolic: parseInt(vitalsFormData.blood_pressure_systolic) || 0,
        blood_pressure_diastolic: parseInt(vitalsFormData.blood_pressure_diastolic) || 0,
        heart_rate: parseInt(vitalsFormData.heart_rate) || 0,
        respiratory_rate: parseInt(vitalsFormData.respiratory_rate) || 0,
        oxygen_saturation: parseFloat(vitalsFormData.oxygen_saturation) || 0,
        weight: parseFloat(vitalsFormData.weight) || 0,
        height: parseFloat(vitalsFormData.height) || 0
      };

      await axios.post(`${API}/vital-signs`, vitalsData);
      setSuccess('Vital signs added successfully!');
      
      setVitalsFormData({
        temperature: '',
        blood_pressure_systolic: '',
        blood_pressure_diastolic: '',
        heart_rate: '',
        respiratory_rate: '',
        oxygen_saturation: '',
        weight: '',
        height: '',
        notes: ''
      });
      setShowVitalsForm(false);
      fetchAllPatientData(selectedPatient.id);
    } catch (error) {
      console.error('Failed to save vital signs:', error);
      setError(error.response?.data?.detail || 'Failed to save vital signs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Allergy Submit
  const handleAllergySubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const allergyData = {
        patient_id: selectedPatient.id,
        ...allergyFormData
      };

      await axios.post(`${API}/allergies`, allergyData);
      setSuccess('Allergy added successfully!');
      
      setAllergyFormData({
        allergen: '',
        reaction: '',
        severity: 'mild',
        onset_date: '',
        notes: ''
      });
      setShowAllergyForm(false);
      fetchAllPatientData(selectedPatient.id);
    } catch (error) {
      console.error('Failed to save allergy:', error);
      setError(error.response?.data?.detail || 'Failed to save allergy. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Medication Submit
  const handleMedicationSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const medicationData = {
        patient_id: selectedPatient.id,
        ...medicationFormData
      };

      await axios.post(`${API}/medications`, medicationData);
      setSuccess('Medication added successfully!');
      
      setMedicationFormData({
        name: '',
        dosage: '',
        frequency: '',
        route: 'oral',
        start_date: '',
        end_date: '',
        prescribing_physician: user?.username || 'Dr. Provider',
        instructions: ''
      });
      setShowMedicationForm(false);
      fetchAllPatientData(selectedPatient.id);
    } catch (error) {
      console.error('Failed to save medication:', error);
      setError(error.response?.data?.detail || 'Failed to save medication. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Prescription Submit  
  const handlePrescriptionSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const prescriptionData = {
        patient_id: selectedPatient.id,
        ...prescriptionFormData,
        quantity: parseInt(prescriptionFormData.quantity) || 0,
        refills: parseInt(prescriptionFormData.refills) || 0
      };

      await axios.post(`${API}/prescriptions`, prescriptionData);
      setSuccess('Prescription created successfully!');
      
      setPrescriptionFormData({
        medication_name: '',
        dosage: '',
        quantity: '',
        frequency: '',
        duration: '',
        instructions: '',
        refills: 0
      });
      setShowPrescriptionForm(false);
      fetchAllPatientData(selectedPatient.id);
    } catch (error) {
      console.error('Failed to save prescription:', error);
      setError(error.response?.data?.detail || 'Failed to save prescription. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEditSoapNote = (soapNote) => {
    setSoapFormData({
      subjective: soapNote.subjective || '',
      objective: soapNote.objective || '',
      assessment: soapNote.assessment || '',
      plan: soapNote.plan || '',
      provider: soapNote.provider || user?.username || 'Dr. Provider'
    });
    setEditingSoapNote(soapNote);
    setShowSoapForm(true);
  };

  const getPatientName = (patient) => {
    if (patient.name && patient.name.length > 0) {
      const name = patient.name[0];
      const firstName = name.given && name.given.length > 0 ? name.given[0] : '';
      const lastName = name.family || '';
      return `${firstName} ${lastName}`;
    }
    return 'Unknown Patient';
  };

  const getPatientPhone = (patient) => {
    if (patient.telecom && patient.telecom.length > 0) {
      const phoneContact = patient.telecom.find(t => t.system === 'phone');
      return phoneContact ? phoneContact.value : '';
    }
    return '';
  };

  const getPatientEmail = (patient) => {
    if (patient.telecom && patient.telecom.length > 0) {
      const emailContact = patient.telecom.find(t => t.system === 'email');
      return emailContact ? emailContact.value : '';
    }
    return '';
  };

  const getPatientAddress = (patient) => {
    if (patient.address && patient.address.length > 0) {
      const addr = patient.address[0];
      const line = addr.line && addr.line.length > 0 ? addr.line[0] : '';
      const city = addr.city || '';
      const state = addr.state || '';
      const postal = addr.postal_code || '';
      return `${line}, ${city}, ${state} ${postal}`.replace(/^, |, $/, '');
    }
    return '';
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Comprehensive EHR System</h2>
        
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          {showAddForm ? 'Cancel' : 'Add Patient'}
        </button>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3 mb-4">
          <p className="text-green-200 text-sm">{success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-4">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Add Patient Form */}
      {showAddForm && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-white mb-4">Add New Patient</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">First Name *</label>
                <input
                  type="text"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter first name"
                  required
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Last Name *</label>
                <input
                  type="text"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter last name"
                  required
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter email address"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Phone</label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter phone number"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Date of Birth</label>
                <input
                  type="date"
                  name="date_of_birth"
                  value={formData.date_of_birth}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Gender</label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                  <option value="unknown">Unknown</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="block text-blue-200 text-sm font-medium mb-2">Address</label>
                <input
                  type="text"
                  name="address_line1"
                  value={formData.address_line1}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter street address"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">City</label>
                <input
                  type="text"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter city"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">State</label>
                <input
                  type="text"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter state"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">ZIP Code</label>
                <input
                  type="text"
                  name="zip_code"
                  value={formData.zip_code}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter ZIP code"
                />
              </div>
            </div>
            
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Patient'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
      
      <div className="space-y-4">
        {/* Tab Navigation */}
        <div className="flex space-x-2 flex-wrap">
          <button
            onClick={() => setActiveTab('patients')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'patients' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
          >
            Patient List ({patients.length})
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
            🏥 Patient Chart
          </button>
          <button
            onClick={() => setActiveTab('vitals')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'vitals' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
            disabled={!selectedPatient}
          >
            📊 Vital Signs
          </button>
          <button
            onClick={() => setActiveTab('medications')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'medications' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
            disabled={!selectedPatient}
          >
            💊 Medications
          </button>
          <button
            onClick={() => setActiveTab('allergies')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'allergies' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
            disabled={!selectedPatient}
          >
            ⚠️ Allergies
          </button>
          <button
            onClick={() => setActiveTab('prescriptions')}
            className={`px-4 py-2 rounded-lg transition-colors ${
              activeTab === 'prescriptions' 
                ? 'bg-blue-600 text-white' 
                : 'text-blue-200 hover:bg-white/10'
            }`}
            disabled={!selectedPatient}
          >
            📝 Prescriptions
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
                            {getPatientName(patient)}
                          </div>
                          <div className="text-blue-200 text-sm">
                            DOB: {patient.birth_date || 'Not provided'} | {patient.gender || 'Not specified'}
                          </div>
                        </div>
                        <div className="text-blue-300 text-sm">
                          {getPatientPhone(patient)}
                        </div>
                      </div>
                      <div className="text-blue-300 text-sm mt-2">
                        {getPatientAddress(patient) || 'No address provided'}
                      </div>
                    </div>
                  ))}
                </div>
                
                {patients.length === 0 && !loading && (
                  <div className="text-center text-blue-200 py-8">
                    <div className="text-4xl mb-4">👥</div>
                    <p className="text-lg">No patients found</p>
                    <p className="text-sm mt-2">Click "Add Patient" to get started</p>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Patient Chart Tab */}
        {activeTab === 'details' && selectedPatient && (
          <div className="space-y-6">
            {/* Patient Summary Card */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">
                  {getPatientName(selectedPatient)}
                </h3>
                <div className="text-sm text-blue-200">
                  Patient ID: {selectedPatient.id}
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-blue-200">DOB:</span>
                  <span className="text-white ml-2">{selectedPatient.birth_date || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Gender:</span>
                  <span className="text-white ml-2">{selectedPatient.gender || 'Not specified'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Phone:</span>
                  <span className="text-white ml-2">{getPatientPhone(selectedPatient) || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Email:</span>
                  <span className="text-white ml-2 truncate">{getPatientEmail(selectedPatient) || 'Not provided'}</span>
                </div>
                <div className="md:col-span-2">
                  <span className="text-blue-200">Address:</span>
                  <span className="text-white ml-2">{getPatientAddress(selectedPatient) || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Status:</span>
                  <span className="text-white ml-2 capitalize">{selectedPatient.status || 'active'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Created:</span>
                  <span className="text-white ml-2">{new Date(selectedPatient.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-3">
                <div className="text-blue-200 text-sm">SOAP Notes</div>
                <div className="text-white text-xl font-bold">{soapNotes.length}</div>
              </div>
              <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3">
                <div className="text-green-200 text-sm">Vital Signs</div>
                <div className="text-white text-xl font-bold">{vitalSigns.length}</div>
              </div>
              <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3">
                <div className="text-yellow-200 text-sm">Allergies</div>
                <div className="text-white text-xl font-bold">{allergies.length}</div>
              </div>
              <div className="bg-purple-500/20 border border-purple-500/50 rounded-lg p-3">
                <div className="text-purple-200 text-sm">Medications</div>
                <div className="text-white text-xl font-bold">{medications.length}</div>
              </div>
              <div className="bg-indigo-500/20 border border-indigo-500/50 rounded-lg p-3">
                <div className="text-indigo-200 text-sm">Prescriptions</div>  
                <div className="text-white text-xl font-bold">{prescriptions.length}</div>
              </div>
            </div>

            {/* SOAP Notes Section */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-white">📋 SOAP Notes</h4>
                <button
                  onClick={() => setShowSoapForm(!showSoapForm)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {showSoapForm ? 'Cancel' : 'Add SOAP Note'}
                </button>
              </div>
              
              {/* SOAP Note Form */}
              {showSoapForm && (
                <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-4">
                  <h5 className="text-md font-medium text-white mb-3">
                    {editingSoapNote ? 'Edit SOAP Note' : 'New SOAP Note'}
                  </h5>
                  <form onSubmit={handleSoapSubmit} className="space-y-4">
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Subjective (Patient's complaints and history)</label>
                      <textarea
                        name="subjective"
                        value={soapFormData.subjective}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="What the patient reports, symptoms, history..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Objective (Physical examination findings)</label>
                      <textarea
                        name="objective"
                        value={soapFormData.objective}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Vital signs, physical exam findings, lab results..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Assessment (Diagnosis and clinical impression)</label>
                      <textarea
                        name="assessment"
                        value={soapFormData.assessment}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Diagnosis, clinical impression, differential diagnosis..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Plan (Treatment plan and follow-up)</label>
                      <textarea
                        name="plan"
                        value={soapFormData.plan}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Treatment plan, medications, follow-up instructions..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Provider</label>
                      <input
                        type="text"
                        name="provider"
                        value={soapFormData.provider}
                        onChange={handleSoapInputChange}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Provider name"
                        required
                      />
                    </div>
                    <div className="flex space-x-4">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Saving...' : (editingSoapNote ? 'Update SOAP Note' : 'Save SOAP Note')}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowSoapForm(false);
                          setEditingSoapNote(null);
                          setSoapFormData({
                            subjective: '',
                            objective: '',
                            assessment: '',
                            plan: '',
                            provider: user?.username || 'Dr. Provider'
                          });
                        }}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}
              
              {/* SOAP Notes List */}
              <div className="space-y-3">
                {soapNotes.length > 0 ? (
                  soapNotes.map((note) => (
                    <div key={note.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-white font-medium">
                          SOAP Note - {new Date(note.created_at).toLocaleDateString()}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-blue-300 text-sm">by {note.provider}</span>
                          <button
                            onClick={() => handleEditSoapNote(note)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Subjective:</div>
                          <div className="text-white text-sm">{note.subjective}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Objective:</div>
                          <div className="text-white text-sm">{note.objective}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Assessment:</div>
                          <div className="text-white text-sm">{note.assessment}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Plan:</div>
                          <div className="text-white text-sm">{note.plan}</div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-blue-200 py-4">
                    <div className="text-2xl mb-2">📝</div>
                    <p>No SOAP notes found for this patient</p>
                    <p className="text-sm mt-1">Click "Add SOAP Note" to create the first note</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Vital Signs Tab */}
        {activeTab === 'vitals' && selectedPatient && (
          <div className="space-y-6">
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-white">📊 Vital Signs</h4>
                <button
                  onClick={() => setShowVitalsForm(!showVitalsForm)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {showVitalsForm ? 'Cancel' : 'Add Vital Signs'}
                </button>
              </div>

              {/* Vital Signs Form */}
              {showVitalsForm && (
                <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-4">
                  <h5 className="text-md font-medium text-white mb-3">New Vital Signs</h5>
                  <form onSubmit={handleVitalsSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Temperature (°F)</label>
                        <input
                          type="number"
                          name="temperature"
                          value={vitalsFormData.temperature}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="98.6"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Heart Rate (BPM)</label>
                        <input
                          type="number"
                          name="heart_rate"
                          value={vitalsFormData.heart_rate}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="72"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Systolic BP</label>
                        <input
                          type="number"
                          name="blood_pressure_systolic"
                          value={vitalsFormData.blood_pressure_systolic}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="120"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Diastolic BP</label>
                        <input
                          type="number"
                          name="blood_pressure_diastolic"
                          value={vitalsFormData.blood_pressure_diastolic}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="80"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Respiratory Rate</label>
                        <input
                          type="number"
                          name="respiratory_rate"
                          value={vitalsFormData.respiratory_rate}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="16"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">O2 Saturation (%)</label>
                        <input
                          type="number"
                          name="oxygen_saturation"
                          value={vitalsFormData.oxygen_saturation}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="98.0"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Weight (lbs)</label>
                        <input
                          type="number"
                          name="weight"
                          value={vitalsFormData.weight}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="150"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Height (inches)</label>
                        <input
                          type="number"
                          name="height"
                          value={vitalsFormData.height}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="68"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Notes</label>
                      <textarea
                        name="notes"
                        value={vitalsFormData.notes}
                        onChange={handleVitalsInputChange}
                        rows={2}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Additional notes about vital signs..."
                      />
                    </div>
                    <div className="flex space-x-4">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Saving...' : 'Save Vital Signs'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowVitalsForm(false)}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Vital Signs List */}
              <div className="space-y-3">
                {vitalSigns.length > 0 ? (
                  vitalSigns.map((vitals) => (
                    <div key={vitals.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div className="text-white font-medium">
                          {new Date(vitals.recorded_at || vitals.created_at).toLocaleDateString()} - {new Date(vitals.recorded_at || vitals.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-blue-200">Temperature:</span>
                          <span className="text-white ml-2">{vitals.temperature}°F</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Heart Rate:</span>
                          <span className="text-white ml-2">{vitals.heart_rate} BPM</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Blood Pressure:</span>
                          <span className="text-white ml-2">{vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic}</span>
                        </div>
                        <div>
                          <span className="text-blue-200">O2 Sat:</span>
                          <span className="text-white ml-2">{vitals.oxygen_saturation}%</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Respiratory Rate:</span>
                          <span className="text-white ml-2">{vitals.respiratory_rate}</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Weight:</span>
                          <span className="text-white ml-2">{vitals.weight} lbs</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Height:</span>
                          <span className="text-white ml-2">{vitals.height} in</span>
                        </div>
                        <div>
                          <span className="text-blue-200">BMI:</span>
                          <span className="text-white ml-2">{vitals.weight && vitals.height ? ((vitals.weight / (vitals.height * vitals.height)) * 703).toFixed(1) : 'N/A'}</span>
                        </div>
                      </div>
                      {vitals.notes && (
                        <div className="mt-3 text-sm">
                          <span className="text-blue-200">Notes:</span>
                          <span className="text-white ml-2">{vitals.notes}</span>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center text-blue-200 py-4">
                    <div className="text-2xl mb-2">📊</div>
                    <p>No vital signs recorded for this patient</p>
                    <p className="text-sm mt-1">Click "Add Vital Signs" to record the first measurement</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Additional tabs would be rendered here */}
        {(activeTab === 'medications' || activeTab === 'allergies' || activeTab === 'prescriptions') && selectedPatient && (
          <div className="text-center text-blue-200 py-8">
            <div className="text-4xl mb-4">🚧</div>
            <p className="text-lg">{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Module</p>
            <p className="text-sm mt-2">This tab is being developed with comprehensive functionality</p>
            <p className="text-xs mt-4 text-blue-300">Backend APIs are ready - Frontend interface coming soon</p>
          </div>
        )}

        {/* Patient Details & SOAP Notes Tab */}
        {activeTab === 'details' && selectedPatient && (
          <div className="space-y-6">
            {/* Patient Info */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">
                  {getPatientName(selectedPatient)}
                </h3>
                <div className="text-sm text-blue-200">
                  Patient ID: {selectedPatient.id}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-200">Date of Birth:</span>
                  <span className="text-white ml-2">{selectedPatient.birth_date || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Gender:</span>
                  <span className="text-white ml-2">{selectedPatient.gender || 'Not specified'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Phone:</span>
                  <span className="text-white ml-2">{getPatientPhone(selectedPatient) || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Email:</span>
                  <span className="text-white ml-2">{getPatientEmail(selectedPatient) || 'Not provided'}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-blue-200">Address:</span>
                  <span className="text-white ml-2">{getPatientAddress(selectedPatient) || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Status:</span>
                  <span className="text-white ml-2 capitalize">{selectedPatient.status || 'active'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Created:</span>
                  <span className="text-white ml-2">{new Date(selectedPatient.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* SOAP Notes Section */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-white">📋 SOAP Notes</h4>
                <button
                  onClick={() => setShowSoapForm(!showSoapForm)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {showSoapForm ? 'Cancel' : 'Add SOAP Note'}
                </button>
              </div>
              
              {/* SOAP Note Form */}
              {showSoapForm && (
                <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-4">
                  <h5 className="text-md font-medium text-white mb-3">
                    {editingSoapNote ? 'Edit SOAP Note' : 'New SOAP Note'}
                  </h5>
                  <form onSubmit={handleSoapSubmit} className="space-y-4">
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Subjective (Patient's complaints and history)</label>
                      <textarea
                        name="subjective"
                        value={soapFormData.subjective}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="What the patient reports, symptoms, history..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Objective (Physical examination findings)</label>
                      <textarea
                        name="objective"
                        value={soapFormData.objective}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Vital signs, physical exam findings, lab results..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Assessment (Diagnosis and clinical impression)</label>
                      <textarea
                        name="assessment"
                        value={soapFormData.assessment}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Diagnosis, clinical impression, differential diagnosis..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Plan (Treatment plan and follow-up)</label>
                      <textarea
                        name="plan"
                        value={soapFormData.plan}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Treatment plan, medications, follow-up instructions..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Provider</label>
                      <input
                        type="text"
                        name="provider"
                        value={soapFormData.provider}
                        onChange={handleSoapInputChange}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Provider name"
                        required
                      />
                    </div>
                    <div className="flex space-x-4">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Saving...' : (editingSoapNote ? 'Update SOAP Note' : 'Save SOAP Note')}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowSoapForm(false);
                          setEditingSoapNote(null);
                          setSoapFormData({
                            subjective: '',
                            objective: '',
                            assessment: '',
                            plan: '',
                            provider: user?.username || 'Dr. Provider'
                          });
                        }}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}
              
              {/* SOAP Notes List */}
              <div className="space-y-3">
                {soapNotes.length > 0 ? (
                  soapNotes.map((note) => (
                    <div key={note.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-white font-medium">
                          SOAP Note - {new Date(note.created_at).toLocaleDateString()}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-blue-300 text-sm">by {note.provider}</span>
                          <button
                            onClick={() => handleEditSoapNote(note)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Subjective:</div>
                          <div className="text-white text-sm">{note.subjective}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Objective:</div>
                          <div className="text-white text-sm">{note.objective}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Assessment:</div>
                          <div className="text-white text-sm">{note.assessment}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Plan:</div>
                          <div className="text-white text-sm">{note.plan}</div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-blue-200 py-4">
                    <div className="text-2xl mb-2">📝</div>
                    <p>No SOAP notes found for this patient</p>
                    <p className="text-sm mt-1">Click "Add SOAP Note" to create the first note</p>
                  </div>
                )}
              </div>
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

// Comprehensive Referrals Management Module
const ReferralsModule = ({ setActiveModule }) => {
  const [referrals, setReferrals] = useState([]);
  const [specialists, setSpecialists] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedReferral, setSelectedReferral] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showSpecialistForm, setShowSpecialistForm] = useState(false);
  const [newReferral, setNewReferral] = useState({
    patient_id: '',
    specialist_id: '',
    reason: '',
    urgency: 'routine',
    clinical_notes: '',
    requested_services: '',
    insurance_authorization_required: false,
    preferred_appointment_date: '',
    patient_symptoms: '',
    relevant_history: '',
    current_medications: '',
    diagnostic_results: ''
  });
  const [newSpecialist, setNewSpecialist] = useState({
    name: '',
    specialty: '',
    practice_name: '',
    phone: '',
    email: '',
    address: '',
    fax: '',
    accepts_new_patients: true,
    insurance_networks: '',
    notes: ''
  });

  useEffect(() => {
    fetchReferrals();
    fetchSpecialists();
    fetchPatients();
  }, []);

  const fetchReferrals = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/referrals`);
      setReferrals(response.data);
    } catch (error) {
      console.error('Failed to fetch referrals:', error);
      // Mock data for demo
      setReferrals([
        {
          id: '1',
          referral_number: 'REF-2024-001',
          patient_name: 'John Doe',
          patient_id: 'P001',
          specialist_name: 'Dr. Sarah Johnson',
          specialist_id: 'S001', 
          specialty: 'Cardiology',
          reason: 'Chest pain evaluation',
          status: 'pending',
          urgency: 'urgent',
          date_created: '2024-01-15',
          appointment_date: '2024-01-25',
          insurance_status: 'approved'
        },
        {
          id: '2',
          referral_number: 'REF-2024-002',
          patient_name: 'Jane Smith',
          patient_id: 'P002',
          specialist_name: 'Dr. Michael Chen',
          specialist_id: 'S002',
          specialty: 'Orthopedics',
          reason: 'Knee pain - possible arthritis',
          status: 'scheduled',
          urgency: 'routine',
          date_created: '2024-01-10',
          appointment_date: '2024-02-01',
          insurance_status: 'pending'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSpecialists = async () => {
    try {
      const response = await axios.get(`${API}/specialists`);
      setSpecialists(response.data);
    } catch (error) {
      console.error('Failed to fetch specialists:', error);
      // Mock data for demo
      setSpecialists([
        {
          id: 'S001',
          name: 'Dr. Sarah Johnson',
          specialty: 'Cardiology',
          practice_name: 'Heart Care Associates',
          phone: '(555) 123-4567',
          email: 'sarah@heartcare.com',
          address: '123 Medical Plaza, Suite 200',
          accepts_new_patients: true,
          rating: 4.8,
          years_experience: 15
        },
        {
          id: 'S002',
          name: 'Dr. Michael Chen',
          specialty: 'Orthopedics',
          practice_name: 'Bone & Joint Clinic',
          phone: '(555) 234-5678',
          email: 'mchen@boneclinic.com',
          address: '456 Healthcare Blvd, Floor 3',
          accepts_new_patients: true,
          rating: 4.9,
          years_experience: 12
        },
        {
          id: 'S003',
          name: 'Dr. Emily Rodriguez',
          specialty: 'Dermatology',
          practice_name: 'Skin Health Center',
          phone: '(555) 345-6789',
          email: 'erodriguez@skinhealth.com',
          address: '789 Wellness Ave, Building A',
          accepts_new_patients: false,
          rating: 4.7,
          years_experience: 18
        }
      ]);
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

  const handleCreateReferral = async (e) => {
    e.preventDefault();
    try {
      const referralData = {
        ...newReferral,
        referral_number: `REF-${new Date().getFullYear()}-${String(referrals.length + 1).padStart(3, '0')}`,
        date_created: new Date().toISOString().split('T')[0],
        status: 'pending'
      };
      
      const response = await axios.post(`${API}/referrals`, referralData);
      setReferrals([response.data, ...referrals]);
      setNewReferral({
        patient_id: '',
        specialist_id: '',
        reason: '',
        urgency: 'routine',
        clinical_notes: '',
        requested_services: '',
        insurance_authorization_required: false,
        preferred_appointment_date: '',
        patient_symptoms: '',
        relevant_history: '',
        current_medications: '',
        diagnostic_results: ''
      });
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create referral:', error);
    }
  };

  const handleCreateSpecialist = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/specialists`, newSpecialist);
      setSpecialists([response.data, ...specialists]);
      setNewSpecialist({
        name: '',
        specialty: '',
        practice_name: '',
        phone: '',
        email: '',
        address: '',
        fax: '',
        accepts_new_patients: true,
        insurance_networks: '',
        notes: ''
      });
      setShowSpecialistForm(false);
    } catch (error) {
      console.error('Failed to create specialist:', error);
    }
  };

  const updateReferralStatus = async (referralId, newStatus) => {
    try {
      await axios.put(`${API}/referrals/${referralId}/status`, { status: newStatus });
      setReferrals(referrals.map(ref => 
        ref.id === referralId ? { ...ref, status: newStatus } : ref
      ));
    } catch (error) {
      console.error('Failed to update referral status:', error);
    }
  };

  const renderOverview = () => {
    const stats = {
      total: referrals.length,
      pending: referrals.filter(ref => ref.status === 'pending').length,
      scheduled: referrals.filter(ref => ref.status === 'scheduled').length,
      completed: referrals.filter(ref => ref.status === 'completed').length,
      urgent: referrals.filter(ref => ref.urgency === 'urgent').length,
      activeSpecialists: specialists.filter(spec => spec.accepts_new_patients).length
    };

    return (
      <div className="space-y-6">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-white">{stats.total}</div>
            <div className="text-blue-200 text-sm">Total Referrals</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-yellow-400">{stats.pending}</div>
            <div className="text-blue-200 text-sm">Pending</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-400">{stats.scheduled}</div>
            <div className="text-blue-200 text-sm">Scheduled</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-green-400">{stats.completed}</div>
            <div className="text-blue-200 text-sm">Completed</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-red-400">{stats.urgent}</div>
            <div className="text-blue-200 text-sm">Urgent</div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="text-2xl font-bold text-purple-400">{stats.activeSpecialists}</div>
            <div className="text-blue-200 text-sm">Active Specialists</div>
          </div>
        </div>

        {/* Recent Referrals */}
        <div className="bg-white/5 border border-white/10 rounded-lg">
          <div className="p-4 border-b border-white/10">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-white">Recent Referrals</h3>
              <button
                onClick={() => setShowCreateForm(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + Create Referral
              </button>
            </div>
          </div>
          
          {loading ? (
            <div className="text-center text-blue-200 py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
              Loading referrals...
            </div>
          ) : (
            <div className="p-4">
              {referrals.length > 0 ? (
                <div className="space-y-4">
                  {referrals.map((referral) => (
                    <div
                      key={referral.id}
                      className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <div>
                              <div className="text-white font-medium">
                                {referral.referral_number}
                              </div>
                              <div className="text-blue-200 text-sm">
                                {referral.patient_name} → {referral.specialist_name}
                              </div>
                            </div>
                          </div>
                          <div className="mt-3 grid grid-cols-2 md:grid-cols-5 gap-4">
                            <div>
                              <div className="text-blue-200 text-xs">Specialty</div>
                              <div className="text-white text-sm">{referral.specialty}</div>
                            </div>
                            <div>
                              <div className="text-blue-200 text-xs">Reason</div>
                              <div className="text-white text-sm">{referral.reason}</div>
                            </div>
                            <div>
                              <div className="text-blue-200 text-xs">Status</div>
                              <div className={`text-sm capitalize ${
                                referral.status === 'completed' ? 'text-green-400' :
                                referral.status === 'scheduled' ? 'text-blue-400' :
                                referral.status === 'pending' ? 'text-yellow-400' :
                                'text-red-400'
                              }`}>
                                {referral.status}
                              </div>
                            </div>
                            <div>
                              <div className="text-blue-200 text-xs">Urgency</div>
                              <div className={`text-sm capitalize ${
                                referral.urgency === 'urgent' ? 'text-red-400' :
                                referral.urgency === 'stat' ? 'text-red-500' :
                                'text-white'
                              }`}>
                                {referral.urgency}
                              </div>
                            </div>
                            <div>
                              <div className="text-blue-200 text-xs">Appointment</div>
                              <div className="text-white text-sm">{referral.appointment_date || 'Not scheduled'}</div>
                            </div>
                          </div>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => setSelectedReferral(referral)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                          >
                            View
                          </button>
                          {referral.status === 'pending' && (
                            <button
                              onClick={() => updateReferralStatus(referral.id, 'scheduled')}
                              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                            >
                              Schedule
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-blue-200 py-8">
                  No referrals found. Click "Create Referral" to get started.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderSpecialistNetwork = () => (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-lg">
        <div className="p-4 border-b border-white/10">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-white">Specialist Network</h3>
            <button
              onClick={() => setShowSpecialistForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
            >
              + Add Specialist
            </button>
          </div>
        </div>
        
        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {specialists.map((specialist) => (
              <div
                key={specialist.id}
                className="bg-white/5 border border-white/10 rounded-lg p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <div className="text-white font-medium">{specialist.name}</div>
                    <div className="text-blue-200 text-sm">{specialist.specialty}</div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs ${
                    specialist.accepts_new_patients 
                      ? 'bg-green-600 text-white' 
                      : 'bg-red-600 text-white'
                  }`}>
                    {specialist.accepts_new_patients ? 'Accepting' : 'Full'}
                  </div>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <div className="text-blue-200">Practice</div>
                    <div className="text-white">{specialist.practice_name}</div>
                  </div>
                  <div>
                    <div className="text-blue-200">Phone</div>
                    <div className="text-white">{specialist.phone}</div>
                  </div>
                  <div>
                    <div className="text-blue-200">Email</div>
                    <div className="text-white">{specialist.email}</div>
                  </div>
                  {specialist.rating && (
                    <div>
                      <div className="text-blue-200">Rating</div>
                      <div className="text-yellow-400">{'★'.repeat(Math.floor(specialist.rating))} {specialist.rating}</div>
                    </div>
                  )}
                </div>
                
                <div className="mt-4 flex space-x-2">
                  <button
                    onClick={() => {
                      setNewReferral({...newReferral, specialist_id: specialist.id});
                      setShowCreateForm(true);
                    }}
                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Refer Patient
                  </button>
                  <button className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm">
                    Contact
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderReferralDetail = () => {
    if (!selectedReferral) return null;

    return (
      <div className="space-y-6">
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-2xl font-bold text-white">{selectedReferral.referral_number}</h3>
              <div className="text-blue-200">{selectedReferral.patient_name} → {selectedReferral.specialist_name}</div>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              selectedReferral.status === 'completed' ? 'bg-green-600 text-white' :
              selectedReferral.status === 'scheduled' ? 'bg-blue-600 text-white' :
              selectedReferral.status === 'pending' ? 'bg-yellow-600 text-white' :
              'bg-red-600 text-white'
            }`}>
              {selectedReferral.status.toUpperCase()}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div>
              <div className="text-blue-200 text-sm">Specialty</div>
              <div className="text-white font-medium">{selectedReferral.specialty}</div>
            </div>
            <div>
              <div className="text-blue-200 text-sm">Urgency</div>
              <div className={`font-medium ${
                selectedReferral.urgency === 'urgent' ? 'text-red-400' :
                selectedReferral.urgency === 'stat' ? 'text-red-500' :
                'text-white'
              }`}>
                {selectedReferral.urgency.toUpperCase()}
              </div>
            </div>
            <div>
              <div className="text-blue-200 text-sm">Date Created</div>
              <div className="text-white font-medium">{selectedReferral.date_created}</div>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-6">
            <h4 className="text-lg font-medium text-white mb-3">Referral Details</h4>
            <div className="space-y-3">
              <div>
                <div className="text-blue-200 text-sm">Reason for Referral</div>
                <div className="text-white">{selectedReferral.reason}</div>
              </div>
              {selectedReferral.appointment_date && (
                <div>
                  <div className="text-blue-200 text-sm">Appointment Date</div>
                  <div className="text-white">{selectedReferral.appointment_date}</div>
                </div>
              )}
              <div>
                <div className="text-blue-200 text-sm">Insurance Status</div>
                <div className={`capitalize ${
                  selectedReferral.insurance_status === 'approved' ? 'text-green-400' :
                  selectedReferral.insurance_status === 'pending' ? 'text-yellow-400' :
                  'text-red-400'
                }`}>
                  {selectedReferral.insurance_status}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button
              onClick={() => window.print()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
            >
              🖨️ Print Referral Letter
            </button>
            <button
              onClick={() => updateReferralStatus(selectedReferral.id, 'completed')}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg"
            >
              ✅ Mark Complete
            </button>
            <button
              onClick={() => setSelectedReferral(null)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
            >
              Back to List
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderCreateReferralForm = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-screen overflow-y-auto">
        <h3 className="text-lg font-medium text-white mb-6">Create New Referral</h3>
        <form onSubmit={handleCreateReferral} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Patient Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
              <select
                required
                value={newReferral.patient_id}
                onChange={(e) => setNewReferral({...newReferral, patient_id: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="">Select Patient</option>
                {patients.map((patient) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.name ? `${patient.name.given?.[0]} ${patient.name.family}` : `Patient ${patient.id}`}
                  </option>
                ))}
              </select>
            </div>

            {/* Specialist Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Specialist</label>
              <select
                required
                value={newReferral.specialist_id}
                onChange={(e) => setNewReferral({...newReferral, specialist_id: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="">Select Specialist</option>
                {specialists.filter(s => s.accepts_new_patients).map((specialist) => (
                  <option key={specialist.id} value={specialist.id}>
                    {specialist.name} - {specialist.specialty}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Urgency */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Urgency</label>
              <select
                value={newReferral.urgency}
                onChange={(e) => setNewReferral({...newReferral, urgency: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="routine">Routine</option>
                <option value="urgent">Urgent</option>
                <option value="stat">STAT</option>
              </select>
            </div>

            {/* Preferred Date */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Preferred Appointment Date</label>
              <input
                type="date"
                value={newReferral.preferred_appointment_date}
                onChange={(e) => setNewReferral({...newReferral, preferred_appointment_date: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          </div>

          {/* Reason for Referral */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Reason for Referral</label>
            <input
              type="text"
              required
              value={newReferral.reason}
              onChange={(e) => setNewReferral({...newReferral, reason: e.target.value})}
              placeholder="Brief description of why patient needs specialist care"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>

          {/* Clinical Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Clinical Notes</label>
            <textarea
              value={newReferral.clinical_notes}
              onChange={(e) => setNewReferral({...newReferral, clinical_notes: e.target.value})}
              rows={4}
              placeholder="Detailed clinical information for the specialist"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Patient Symptoms */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Patient Symptoms</label>
              <textarea
                value={newReferral.patient_symptoms}
                onChange={(e) => setNewReferral({...newReferral, patient_symptoms: e.target.value})}
                rows={3}
                placeholder="Current symptoms and duration"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>

            {/* Relevant History */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Relevant History</label>
              <textarea
                value={newReferral.relevant_history}
                onChange={(e) => setNewReferral({...newReferral, relevant_history: e.target.value})}
                rows={3}
                placeholder="Relevant medical history"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          </div>

          {/* Current Medications */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Current Medications</label>
            <textarea
              value={newReferral.current_medications}
              onChange={(e) => setNewReferral({...newReferral, current_medications: e.target.value})}
              rows={3}
              placeholder="List current medications and dosages"
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>

          {/* Insurance Authorization */}
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="auth_required"
              checked={newReferral.insurance_authorization_required}
              onChange={(e) => setNewReferral({...newReferral, insurance_authorization_required: e.target.checked})}
              className="w-4 h-4"
            />
            <label htmlFor="auth_required" className="text-gray-300">
              Insurance authorization required
            </label>
          </div>
          
          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium"
            >
              Create Referral
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

  const renderAddSpecialistForm = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
        <h3 className="text-lg font-medium text-white mb-6">Add New Specialist</h3>
        <form onSubmit={handleCreateSpecialist} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={newSpecialist.name}
                onChange={(e) => setNewSpecialist({...newSpecialist, name: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Specialty</label>
              <input
                type="text"
                required
                value={newSpecialist.specialty}
                onChange={(e) => setNewSpecialist({...newSpecialist, specialty: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Practice Name</label>
            <input
              type="text"
              value={newSpecialist.practice_name}
              onChange={(e) => setNewSpecialist({...newSpecialist, practice_name: e.target.value})}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Phone</label>
              <input
                type="tel"
                required
                value={newSpecialist.phone}
                onChange={(e) => setNewSpecialist({...newSpecialist, phone: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
              <input
                type="email"
                value={newSpecialist.email}
                onChange={(e) => setNewSpecialist({...newSpecialist, email: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Address</label>
            <textarea
              value={newSpecialist.address}
              onChange={(e) => setNewSpecialist({...newSpecialist, address: e.target.value})}
              rows={2}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>
          
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="accepts_new"
              checked={newSpecialist.accepts_new_patients}
              onChange={(e) => setNewSpecialist({...newSpecialist, accepts_new_patients: e.target.checked})}
              className="w-4 h-4"
            />
            <label htmlFor="accepts_new" className="text-gray-300">
              Currently accepting new patients
            </label>
          </div>
          
          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
            >
              Add Specialist
            </button>
            <button
              type="button"
              onClick={() => setShowSpecialistForm(false)}
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
        <h2 className="text-xl font-semibold text-white">Referral Management</h2>
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
            { id: 'specialists', name: 'Specialist Network', icon: '👨‍⚕️' },
            { id: 'detail', name: 'Referral Detail', icon: '📋', disabled: !selectedReferral }
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
      {activeTab === 'specialists' && renderSpecialistNetwork()}
      {activeTab === 'detail' && renderReferralDetail()}

      {/* Modals */}
      {showCreateForm && renderCreateReferralForm()}
      {showSpecialistForm && renderAddSpecialistForm()}
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
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    sku: '',
    current_stock: 0,
    min_stock_level: 0,
    unit_cost: 0,
    supplier: '',
    expiry_date: '',
    location: '',
    notes: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/inventory`);
      setInventory(response.data);
      setError('');
    } catch (error) {
      console.error('Failed to fetch inventory:', error);
      setError('Failed to fetch inventory items.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name.includes('stock') || name === 'unit_cost' ? Number(value) : value
    }));
  };

  const resetForm = () => {
    setFormData({
      name: '',
      category: '',
      sku: '',
      current_stock: 0,
      min_stock_level: 0,
      unit_cost: 0,
      supplier: '',
      expiry_date: '',
      location: '',
      notes: ''
    });
    setEditingItem(null);
    setShowAddForm(false);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      let response;
      if (editingItem) {
        // Update existing item
        response = await axios.put(`${API}/inventory/${editingItem.id}`, formData);
        setSuccess('Inventory item updated successfully!');
      } else {
        // Create new item
        response = await axios.post(`${API}/inventory`, formData);
        setSuccess('Inventory item added successfully!');
      }
      
      resetForm();
      fetchInventory(); // Refresh the list
    } catch (error) {
      console.error('Failed to save inventory item:', error);
      setError(error.response?.data?.detail || 'Failed to save inventory item. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (item) => {
    setFormData({
      name: item.name || '',
      category: item.category || '',
      sku: item.sku || '',
      current_stock: item.current_stock || 0,
      min_stock_level: item.min_stock_level || 0,
      unit_cost: item.unit_cost || 0,
      supplier: item.supplier || '',
      expiry_date: item.expiry_date || '',
      location: item.location || '',
      notes: item.notes || ''
    });
    setEditingItem(item);
    setShowAddForm(true);
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">Inventory Management</h2>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            {showAddForm ? 'Cancel' : 'Add Item'}
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3 mb-4">
          <p className="text-green-200 text-sm">{success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-4">
          <p className="text-red-200 text-sm">{error}</p>
        </div>
      )}

      {/* Add/Edit Item Form */}
      {showAddForm && (
        <div className="bg-white/5 border border-white/10 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-medium text-white mb-4">
            {editingItem ? 'Edit Inventory Item' : 'Add New Inventory Item'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Item Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter item name"
                  required
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Category *</label>
                <select
                  name="category"
                  value={formData.category}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-400"
                  required
                >
                  <option value="">Select category</option>
                  <option value="medications">Medications</option>
                  <option value="supplies">Medical Supplies</option>
                  <option value="equipment">Equipment</option>
                  <option value="disposables">Disposables</option>
                  <option value="office">Office Supplies</option>
                  <option value="lab">Lab Supplies</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">SKU</label>
                <input
                  type="text"
                  name="sku"
                  value={formData.sku}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter SKU"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Current Stock</label>
                <input
                  type="number"
                  name="current_stock"
                  value={formData.current_stock}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter current stock"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Minimum Stock Level</label>
                <input
                  type="number"
                  name="min_stock_level"
                  value={formData.min_stock_level}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter minimum stock level"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Unit Cost ($)</label>
                <input
                  type="number"
                  name="unit_cost"
                  value={formData.unit_cost}
                  onChange={handleInputChange}
                  step="0.01"
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter unit cost"
                  min="0"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Supplier</label>
                <input
                  type="text"
                  name="supplier"
                  value={formData.supplier}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter supplier name"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Expiry Date</label>
                <input
                  type="date"
                  name="expiry_date"
                  value={formData.expiry_date}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                />
              </div>
              <div>
                <label className="block text-blue-200 text-sm font-medium mb-2">Location</label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter storage location"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-blue-200 text-sm font-medium mb-2">Notes</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                  placeholder="Enter any additional notes"
                />
              </div>
            </div>
            
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingItem ? 'Update Item' : 'Add Item')}
              </button>
              <button
                type="button"
                onClick={resetForm}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
      
      {/* Inventory List */}
      <div className="space-y-4">
        <h3 className="text-lg font-medium text-white">Current Inventory ({inventory.length} items)</h3>
        
        {loading && !showAddForm ? (
          <div className="text-center text-blue-200 py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
            Loading inventory...
          </div>
        ) : (
          <div className="space-y-3">
            {inventory.length > 0 ? (
              inventory.map((item) => (
                <div
                  key={item.id}
                  className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <div className="text-white font-medium text-lg">{item.name}</div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          item.current_stock <= item.min_stock_level 
                            ? 'bg-red-600/20 text-red-200 border border-red-600/50' 
                            : 'bg-green-600/20 text-green-200 border border-green-600/50'
                        }`}>
                          {item.current_stock <= item.min_stock_level ? 'Low Stock' : 'In Stock'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2 text-sm">
                        <div>
                          <span className="text-blue-200">SKU:</span>
                          <span className="text-white ml-2">{item.sku || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Category:</span>
                          <span className="text-white ml-2 capitalize">{item.category}</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Supplier:</span>
                          <span className="text-white ml-2">{item.supplier || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Location:</span>
                          <span className="text-white ml-2">{item.location || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-right">
                        <div className="text-white font-bold text-lg">Stock: {item.current_stock}</div>
                        <div className="text-blue-300 text-sm">Min: {item.min_stock_level}</div>
                        <div className="text-blue-300 text-sm">Cost: ${item.unit_cost}</div>
                      </div>
                      <button
                        onClick={() => handleEdit(item)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-colors"
                      >
                        Edit
                      </button>
                    </div>
                  </div>
                  {item.notes && (
                    <div className="mt-2 text-blue-300 text-sm">
                      <span className="text-blue-200">Notes:</span> {item.notes}
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center text-blue-200 py-8">
                <div className="text-4xl mb-4">📦</div>
                <p className="text-lg">No inventory items found</p>
                <p className="text-sm mt-2">Click "Add Item" to get started</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Comprehensive Finance Module - Enterprise Financial Management System
const FinanceModule = ({ setActiveModule }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [transactions, setTransactions] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [budgets, setBudgets] = useState([]);
  const [reports, setReports] = useState({});
  const [loading, setLoading] = useState(false);
  const [showTransactionForm, setShowTransactionForm] = useState(false);
  const [showBudgetForm, setShowBudgetForm] = useState(false);
  const [showReconciliation, setShowReconciliation] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('current-month');
  const [newTransaction, setNewTransaction] = useState({
    description: '',
    amount: '',
    transaction_type: 'expense',
    category: '',
    account_id: '',
    payment_method: 'cash',
    transaction_date: new Date().toISOString().split('T')[0],
    notes: ''
  });
  const [newBudget, setNewBudget] = useState({
    name: '',
    category: '',
    period: 'monthly',
    budgeted_amount: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    notes: ''
  });

  useEffect(() => {
    fetchFinancialData();
  }, [selectedPeriod]);

  const fetchFinancialData = async () => {
    setLoading(true);
    try {
      // Fetch transactions
      const transactionsResponse = await axios.get(`${API}/financial-transactions`);
      setTransactions(transactionsResponse.data || []);

      // Mock comprehensive financial data for demo
      setAccounts([
        {
          id: '1',
          name: 'Operating Account',
          type: 'checking',
          balance: 125000.50,
          bank: 'Chase Bank',
          account_number: '****1234',
          is_primary: true
        },
        {
          id: '2', 
          name: 'Savings Account',
          type: 'savings',
          balance: 75000.00,
          bank: 'Wells Fargo',
          account_number: '****5678',
          is_primary: false
        },
        {
          id: '3',
          name: 'Payroll Account',
          type: 'checking',
          balance: 45000.25,
          bank: 'Bank of America',
          account_number: '****9012',
          is_primary: false
        }
      ]);

      setBudgets([
        {
          id: '1',
          name: 'Medical Supplies',
          category: 'supplies',
          budgeted_amount: 15000,
          actual_amount: 12500,
          period: 'monthly',
          variance: -2500,
          percentage: 83.3
        },
        {
          id: '2',
          name: 'Staff Salaries',
          category: 'payroll',
          budgeted_amount: 85000,
          actual_amount: 87200,
          period: 'monthly',
          variance: 2200,
          percentage: 102.6
        },
        {
          id: '3',
          name: 'Office Rent',
          category: 'facilities',
          budgeted_amount: 8000,
          actual_amount: 8000,
          period: 'monthly',
          variance: 0,
          percentage: 100.0
        },
        {
          id: '4',
          name: 'Marketing',
          category: 'marketing',
          budgeted_amount: 5000,
          actual_amount: 3200,
          period: 'monthly',
          variance: -1800,
          percentage: 64.0
        }
      ]);

      // Calculate financial reports
      const income = transactionsResponse.data
        ?.filter(t => t.transaction_type === 'income')
        .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0) || 0;
      
      const expenses = transactionsResponse.data
        ?.filter(t => t.transaction_type === 'expense')
        .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0) || 0;

      setReports({
        profitLoss: {
          revenue: income + 145000, // Add mock revenue
          totalRevenue: income + 145000,
          expenses: expenses + 95000, // Add mock expenses
          totalExpenses: expenses + 95000,
          netIncome: (income + 145000) - (expenses + 95000),
          grossMargin: 0.65,
          netMargin: 0.28
        },
        balanceSheet: {
          assets: {
            cash: 245250.75,
            accountsReceivable: 32500.00,
            inventory: 18750.25,
            equipment: 125000.00,
            total: 421500.00
          },
          liabilities: {
            accountsPayable: 15200.00,
            payroll: 23500.00,
            loans: 75000.00,
            total: 113700.00
          },
          equity: 307800.00
        },
        cashFlow: {
          operatingActivities: 42500.00,
          investingActivities: -15000.00,
          financingActivities: -8000.00,
          netCashFlow: 19500.00,
          beginningCash: 225750.75,
          endingCash: 245250.75
        },
        kpis: {
          patientVisits: 2150,
          avgRevenuePerVisit: 128.50,
          collectionRate: 94.2,
          operatingMargin: 31.5,
          daysInAR: 28,
          costPerPatient: 84.30
        }
      });

    } catch (error) {
      console.error('Failed to fetch financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTransaction = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post(`${API}/financial-transactions`, newTransaction);
      setTransactions([response.data, ...transactions]);
      setNewTransaction({
        description: '',
        amount: '',
        transaction_type: 'expense',
        category: '',
        account_id: '',
        payment_method: 'cash',
        transaction_date: new Date().toISOString().split('T')[0],
        notes: ''
      });
      setShowTransactionForm(false);
      fetchFinancialData(); // Refresh data
    } catch (error) {
      console.error('Failed to create transaction:', error);
    }
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        <div className="bg-green-600/20 border border-green-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">${reports.profitLoss?.totalRevenue?.toLocaleString() || '0'}</div>
          <div className="text-green-200 text-sm">Total Revenue</div>
          <div className="text-green-300 text-xs">↗ +12.5% vs last month</div>
        </div>
        <div className="bg-red-600/20 border border-red-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">${reports.profitLoss?.totalExpenses?.toLocaleString() || '0'}</div>
          <div className="text-red-200 text-sm">Total Expenses</div>
          <div className="text-red-300 text-xs">↗ +5.2% vs last month</div>
        </div>
        <div className="bg-blue-600/20 border border-blue-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">${reports.profitLoss?.netIncome?.toLocaleString() || '0'}</div>
          <div className="text-blue-200 text-sm">Net Income</div>
          <div className="text-green-300 text-xs">↗ +18.7% vs last month</div>
        </div>
        <div className="bg-purple-600/20 border border-purple-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">{reports.kpis?.operatingMargin || '0'}%</div>
          <div className="text-purple-200 text-sm">Operating Margin</div>
          <div className="text-green-300 text-xs">↗ +2.1% vs last month</div>
        </div>
        <div className="bg-yellow-600/20 border border-yellow-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">{reports.kpis?.collectionRate || '0'}%</div>
          <div className="text-yellow-200 text-sm">Collection Rate</div>
          <div className="text-green-300 text-xs">↗ +1.8% vs last month</div>
        </div>
        <div className="bg-teal-600/20 border border-teal-400/50 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">${reports.kpis?.avgRevenuePerVisit?.toFixed(2) || '0'}</div>
          <div className="text-teal-200 text-sm">Avg Revenue/Visit</div>
          <div className="text-green-300 text-xs">↗ +3.4% vs last month</div>
        </div>
      </div>

      {/* Charts and Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trend Chart */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Revenue Trend (Last 6 Months)</h3>
          <div className="h-48 flex items-end space-x-2">
            {[125000, 132000, 128000, 145000, 142000, 155000].map((amount, index) => (
              <div key={index} className="flex-1 bg-green-500 rounded-t" style={{height: `${(amount/155000)*100}%`}}>
                <div className="text-xs text-center text-white mt-1">${(amount/1000).toFixed(0)}K</div>
              </div>
            ))}
          </div>
          <div className="flex justify-between text-xs text-blue-200 mt-2">
            <span>Jul</span><span>Aug</span><span>Sep</span><span>Oct</span><span>Nov</span><span>Dec</span>
          </div>
        </div>

        {/* Expense Breakdown */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-medium text-white mb-4">Expense Breakdown</h3>
          <div className="space-y-3">
            {[
              {name: 'Payroll', amount: 87200, percentage: 45, color: 'bg-red-500'},
              {name: 'Medical Supplies', amount: 25000, percentage: 26, color: 'bg-orange-500'},
              {name: 'Facilities', amount: 15000, percentage: 16, color: 'bg-yellow-500'},
              {name: 'Insurance', amount: 8000, percentage: 8, color: 'bg-purple-500'},
              {name: 'Other', amount: 5000, percentage: 5, color: 'bg-gray-500'}
            ].map((expense, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${expense.color}`}></div>
                  <span className="text-white">{expense.name}</span>
                </div>
                <div className="text-right">
                  <div className="text-white font-medium">${expense.amount.toLocaleString()}</div>
                  <div className="text-blue-200 text-sm">{expense.percentage}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Account Balances */}
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-white">Account Balances</h3>
          <button
            onClick={() => setShowReconciliation(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
          >
            Reconcile Accounts
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {accounts.map((account) => (
            <div key={account.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="text-white font-medium">{account.name}</div>
                  <div className="text-blue-200 text-sm">{account.bank} {account.account_number}</div>
                </div>
                {account.is_primary && (
                  <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded">Primary</span>
                )}
              </div>
              <div className="text-2xl font-bold text-white">${account.balance.toLocaleString()}</div>
              <div className="text-blue-200 text-sm capitalize">{account.type} Account</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderProfitLoss = () => (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-medium text-white">Profit & Loss Statement</h3>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
          >
            <option value="current-month">Current Month</option>
            <option value="last-month">Last Month</option>
            <option value="quarter">This Quarter</option>
            <option value="year">This Year</option>
          </select>
        </div>

        <div className="space-y-6">
          {/* Revenue Section */}
          <div>
            <h4 className="text-white font-medium mb-3">Revenue</h4>
            <div className="space-y-2 pl-4">
              <div className="flex justify-between">
                <span className="text-blue-200">Patient Services</span>
                <span className="text-white">$125,000.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Insurance Reimbursements</span>
                <span className="text-white">$85,500.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Cash Payments</span>
                <span className="text-white">$28,750.00</span>
              </div>
              <div className="flex justify-between border-t border-white/20 pt-2">
                <span className="text-white font-medium">Total Revenue</span>
                <span className="text-white font-bold">${reports.profitLoss?.totalRevenue?.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Expenses Section */}
          <div>
            <h4 className="text-white font-medium mb-3">Expenses</h4>
            <div className="space-y-2 pl-4">
              <div className="flex justify-between">
                <span className="text-blue-200">Salaries & Benefits</span>
                <span className="text-white">$87,200.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Medical Supplies</span>
                <span className="text-white">$25,000.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Rent & Utilities</span>
                <span className="text-white">$15,000.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Insurance</span>
                <span className="text-white">$8,000.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Equipment Depreciation</span>
                <span className="text-white">$5,500.00</span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-200">Other Operating Expenses</span>
                <span className="text-white">$12,300.00</span>
              </div>
              <div className="flex justify-between border-t border-white/20 pt-2">
                <span className="text-white font-medium">Total Expenses</span>
                <span className="text-white font-bold">${reports.profitLoss?.totalExpenses?.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Net Income */}
          <div className="bg-green-600/20 border border-green-400/50 rounded-lg p-4">
            <div className="flex justify-between items-center">
              <span className="text-white font-medium text-lg">Net Income</span>
              <span className="text-green-400 font-bold text-xl">${reports.profitLoss?.netIncome?.toLocaleString()}</span>
            </div>
            <div className="mt-2 text-sm">
              <div className="flex justify-between text-green-200">
                <span>Gross Margin: {(reports.profitLoss?.grossMargin * 100)?.toFixed(1)}%</span>
                <span>Net Margin: {(reports.profitLoss?.netMargin * 100)?.toFixed(1)}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderBalanceSheet = () => (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-6">Balance Sheet</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Assets */}
          <div>
            <h4 className="text-white font-medium mb-4">Assets</h4>
            <div className="space-y-3">
              <div>
                <div className="text-blue-200 text-sm mb-1">Current Assets</div>
                <div className="pl-4 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Cash & Cash Equivalents</span>
                    <span className="text-white">${reports.balanceSheet?.assets?.cash?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Accounts Receivable</span>
                    <span className="text-white">${reports.balanceSheet?.assets?.accountsReceivable?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Inventory</span>
                    <span className="text-white">${reports.balanceSheet?.assets?.inventory?.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <div className="text-blue-200 text-sm mb-1">Fixed Assets</div>
                <div className="pl-4 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Equipment (Net)</span>
                    <span className="text-white">${reports.balanceSheet?.assets?.equipment?.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-between border-t border-white/20 pt-2 font-medium">
                <span className="text-white">Total Assets</span>
                <span className="text-white">${reports.balanceSheet?.assets?.total?.toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Liabilities & Equity */}
          <div>
            <h4 className="text-white font-medium mb-4">Liabilities & Equity</h4>
            <div className="space-y-3">
              <div>
                <div className="text-blue-200 text-sm mb-1">Current Liabilities</div>
                <div className="pl-4 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Accounts Payable</span>
                    <span className="text-white">${reports.balanceSheet?.liabilities?.accountsPayable?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-300">Accrued Payroll</span>
                    <span className="text-white">${reports.balanceSheet?.liabilities?.payroll?.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <div className="text-blue-200 text-sm mb-1">Long-term Liabilities</div>
                <div className="pl-4 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Equipment Loans</span>
                    <span className="text-white">${reports.balanceSheet?.liabilities?.loans?.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-between border-t border-white/20 pt-2">
                <span className="text-white font-medium">Total Liabilities</span>
                <span className="text-white">${reports.balanceSheet?.liabilities?.total?.toLocaleString()}</span>
              </div>
              
              <div className="mt-4">
                <div className="text-blue-200 text-sm mb-1">Equity</div>
                <div className="pl-4">
                  <div className="flex justify-between">
                    <span className="text-gray-300">Owner's Equity</span>
                    <span className="text-white">${reports.balanceSheet?.equity?.toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-between border-t border-white/20 pt-2 font-medium">
                <span className="text-white">Total Liabilities & Equity</span>
                <span className="text-white">${(reports.balanceSheet?.liabilities?.total + reports.balanceSheet?.equity)?.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderBudgetManagement = () => (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-lg">
        <div className="p-4 border-b border-white/10">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-white">Budget Management</h3>
            <button
              onClick={() => setShowBudgetForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
            >
              + Create Budget
            </button>
          </div>
        </div>
        
        <div className="p-4">
          <div className="space-y-4">
            {budgets.map((budget) => (
              <div key={budget.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="text-white font-medium">{budget.name}</div>
                    <div className="text-blue-200 text-sm capitalize">{budget.category} • {budget.period}</div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    budget.percentage <= 100 ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
                  }`}>
                    {budget.percentage}%
                  </div>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-300">Budget: ${budget.budgeted_amount.toLocaleString()}</span>
                    <span className="text-gray-300">Actual: ${budget.actual_amount.toLocaleString()}</span>
                  </div>
                  
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        budget.percentage <= 100 ? 'bg-green-500' : 'bg-red-500'
                      }`}
                      style={{width: `${Math.min(budget.percentage, 100)}%`}}
                    ></div>
                  </div>
                  
                  <div className="flex justify-between text-sm">
                    <span className={`${
                      budget.variance < 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      Variance: ${Math.abs(budget.variance).toLocaleString()} {budget.variance < 0 ? 'Under' : 'Over'}
                    </span>
                    <span className="text-blue-200">{budget.percentage.toFixed(1)}% of budget used</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderTransactions = () => (
    <div className="space-y-6">
      <div className="bg-white/5 border border-white/10 rounded-lg">
        <div className="p-4 border-b border-white/10">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-white">Transaction History</h3>
            <button
              onClick={() => setShowTransactionForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
            >
              + Add Transaction
            </button>
          </div>
        </div>
        
        <div className="p-4">
          {loading ? (
            <div className="text-center text-blue-200 py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400 mx-auto mb-4"></div>
              Loading transactions...
            </div>
          ) : (
            <div className="space-y-3">
              {transactions.length > 0 ? (
                transactions.map((transaction) => (
                  <div key={transaction.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="text-white font-medium">{transaction.description}</div>
                        <div className="text-blue-200 text-sm">
                          #{transaction.transaction_number} • {transaction.transaction_date}
                        </div>
                        <div className="text-blue-300 text-sm">
                          {transaction.payment_method} • {transaction.category || 'Uncategorized'}
                        </div>
                        {transaction.notes && (
                          <div className="text-gray-400 text-sm mt-1">{transaction.notes}</div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-bold ${
                          transaction.transaction_type === 'income' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {transaction.transaction_type === 'income' ? '+' : '-'}${parseFloat(transaction.amount || 0).toFixed(2)}
                        </div>
                        <div className="text-blue-200 text-sm capitalize">{transaction.transaction_type}</div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-blue-200 py-8">
                  No transactions found. Click "Add Transaction" to get started.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderTransactionForm = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
        <h3 className="text-lg font-medium text-white mb-6">Add New Transaction</h3>
        <form onSubmit={handleCreateTransaction} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
              <input
                type="text"
                required
                value={newTransaction.description}
                onChange={(e) => setNewTransaction({...newTransaction, description: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Amount</label>
              <input
                type="number"
                step="0.01"
                required
                value={newTransaction.amount}
                onChange={(e) => setNewTransaction({...newTransaction, amount: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Type</label>
              <select
                value={newTransaction.transaction_type}
                onChange={(e) => setNewTransaction({...newTransaction, transaction_type: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="income">Income</option>
                <option value="expense">Expense</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Category</label>
              <select
                value={newTransaction.category}
                onChange={(e) => setNewTransaction({...newTransaction, category: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="">Select Category</option>
                <option value="patient_services">Patient Services</option>
                <option value="insurance">Insurance Reimbursement</option>
                <option value="supplies">Medical Supplies</option>
                <option value="payroll">Payroll</option>
                <option value="rent">Rent & Utilities</option>
                <option value="equipment">Equipment</option>
                <option value="marketing">Marketing</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Payment Method</label>
              <select
                value={newTransaction.payment_method}
                onChange={(e) => setNewTransaction({...newTransaction, payment_method: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              >
                <option value="cash">Cash</option>
                <option value="check">Check</option>
                <option value="credit_card">Credit Card</option>
                <option value="bank_transfer">Bank Transfer</option>
                <option value="ach">ACH</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">Date</label>
              <input
                type="date"
                value={newTransaction.transaction_date}
                onChange={(e) => setNewTransaction({...newTransaction, transaction_date: e.target.value})}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Account</label>
            <select
              value={newTransaction.account_id}
              onChange={(e) => setNewTransaction({...newTransaction, account_id: e.target.value})}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            >
              <option value="">Select Account</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name} ({account.bank})
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Notes</label>
            <textarea
              value={newTransaction.notes}
              onChange={(e) => setNewTransaction({...newTransaction, notes: e.target.value})}
              rows={3}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white"
            />
          </div>
          
          <div className="flex space-x-4 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg"
            >
              Add Transaction
            </button>
            <button
              type="button"
              onClick={() => setShowTransactionForm(false)}
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
        <h2 className="text-xl font-semibold text-white">Financial Management</h2>
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
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'profitloss', name: 'P&L Statement', icon: '📈' },
            { id: 'balancesheet', name: 'Balance Sheet', icon: '⚖️' },
            { id: 'budgets', name: 'Budget Management', icon: '🎯' },
            { id: 'transactions', name: 'Transactions', icon: '💳' }
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
      {activeTab === 'dashboard' && renderDashboard()}
      {activeTab === 'profitloss' && renderProfitLoss()}
      {activeTab === 'balancesheet' && renderBalanceSheet()}
      {activeTab === 'budgets' && renderBudgetManagement()}
      {activeTab === 'transactions' && renderTransactions()}

      {/* Modals */}
      {showTransactionForm && renderTransactionForm()}
    </div>
  );
};

// Comprehensive Appointment Scheduling Module
const SchedulingModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [providers, setProviders] = useState([]);
  const [patients, setPatients] = useState([]);
  const [waitingList, setWaitingList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and navigation states
  const [activeView, setActiveView] = useState('calendar'); // calendar, appointments, waiting-list, providers
  const [calendarView, setCalendarView] = useState('week'); // day, week, month
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [selectedProvider, setSelectedProvider] = useState('');
  
  // Form states
  const [showAppointmentForm, setShowAppointmentForm] = useState(false);
  const [showRecurringForm, setShowRecurringForm] = useState(false);
  const [showWaitingListForm, setShowWaitingListForm] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);
  
  // Form data
  const [appointmentFormData, setAppointmentFormData] = useState({
    patient_id: '',
    provider_id: '',
    appointment_date: new Date().toISOString().split('T')[0],
    start_time: '09:00',
    duration_minutes: 30,
    appointment_type: 'consultation',
    title: '',
    description: '',
    notes: ''
  });
  
  const [recurringFormData, setRecurringFormData] = useState({
    recurrence_type: 'weekly',
    recurrence_interval: 1,
    recurrence_end_date: '',
    max_occurrences: 12
  });
  
  const [waitingListFormData, setWaitingListFormData] = useState({
    patient_id: '',
    provider_id: '',
    preferred_date: new Date().toISOString().split('T')[0],
    preferred_time_start: '09:00',
    preferred_time_end: '17:00',
    appointment_type: 'consultation',
    priority: 1,
    duration_minutes: 30,
    reason: '',
    notes: ''
  });
  
  // Available time slots
  const [availableSlots, setAvailableSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState(null);

  useEffect(() => {
    fetchAppointments();
    fetchProviders();
    fetchPatients();
    fetchWaitingList();
  }, []);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/appointments`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setAppointments(response.data);
    } catch (error) {
      console.error('Failed to fetch appointments:', error);
      setError('Failed to fetch appointments');
    } finally {
      setLoading(false);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    }
  };

  const fetchWaitingList = async () => {
    try {
      const response = await axios.get(`${API}/waiting-list`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setWaitingList(response.data);
    } catch (error) {
      console.error('Failed to fetch waiting list:', error);
    }
  };

  const fetchAvailableSlots = async (providerId, date, duration = 30) => {
    try {
      const response = await axios.get(`${API}/appointments/available-slots`, {
        params: { provider_id: providerId, date, duration_minutes: duration },
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setAvailableSlots(response.data.available_slots || []);
    } catch (error) {
      console.error('Failed to fetch available slots:', error);
      setAvailableSlots([]);
    }
  };

  const handleCreateAppointment = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      
      // Get patient and provider names
      const patient = patients.find(p => p.id === appointmentFormData.patient_id);
      const provider = providers.find(p => p.id === appointmentFormData.provider_id);
      
      const appointmentData = {
        ...appointmentFormData,
        patient_name: `${patient?.name?.[0]?.given?.[0] || ''} ${patient?.name?.[0]?.family || ''}`.trim(),
        provider_name: provider?.name || '',
        scheduled_by: user.username
      };

      const response = await axios.post(`${API}/appointments`, appointmentData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setAppointments([...appointments, response.data]);
      setSuccess('Appointment created successfully!');
      setShowAppointmentForm(false);
      resetAppointmentForm();
      fetchAppointments();
    } catch (error) {
      console.error('Failed to create appointment:', error);
      setError(error.response?.data?.detail || 'Failed to create appointment');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateRecurringAppointment = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      
      const patient = patients.find(p => p.id === appointmentFormData.patient_id);
      const provider = providers.find(p => p.id === appointmentFormData.provider_id);
      
      const recurringData = {
        appointment: {
          ...appointmentFormData,
          patient_name: `${patient?.name?.[0]?.given?.[0] || ''} ${patient?.name?.[0]?.family || ''}`.trim(),
          provider_name: provider?.name || '',
          scheduled_by: user.username
        },
        ...recurringFormData
      };

      const response = await axios.post(`${API}/appointments/recurring`, recurringData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setSuccess(`Created ${response.data.total_appointments} recurring appointments successfully!`);
      setShowRecurringForm(false);
      resetAppointmentForm();
      fetchAppointments();
    } catch (error) {
      console.error('Failed to create recurring appointments:', error);
      setError(error.response?.data?.detail || 'Failed to create recurring appointments');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToWaitingList = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${API}/waiting-list`, waitingListFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setWaitingList([...waitingList, response.data]);
      setSuccess('Added to waiting list successfully!');
      setShowWaitingListForm(false);
      resetWaitingListForm();
    } catch (error) {
      console.error('Failed to add to waiting list:', error);
      setError(error.response?.data?.detail || 'Failed to add to waiting list');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAppointmentStatus = async (appointmentId, status) => {
    try {
      const response = await axios.put(`${API}/appointments/${appointmentId}/status`, 
        { status }, 
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      
      setAppointments(appointments.map(apt => 
        apt.id === appointmentId ? { ...apt, status } : apt
      ));
      setSuccess('Appointment status updated successfully!');
    } catch (error) {
      console.error('Failed to update appointment status:', error);
      setError('Failed to update appointment status');
    }
  };

  const resetAppointmentForm = () => {
    setAppointmentFormData({
      patient_id: '',
      provider_id: '',
      appointment_date: new Date().toISOString().split('T')[0],
      start_time: '09:00',
      duration_minutes: 30,
      appointment_type: 'consultation',
      title: '',
      description: '',
      notes: ''
    });
    setAvailableSlots([]);
    setSelectedSlot(null);
  };

  const resetWaitingListForm = () => {
    setWaitingListFormData({
      patient_id: '',
      provider_id: '',
      preferred_date: new Date().toISOString().split('T')[0],
      preferred_time_start: '09:00',
      preferred_time_end: '17:00',
      appointment_type: 'consultation',
      priority: 1,
      duration_minutes: 30,
      reason: '',
      notes: ''
    });
  };

  // Calendar view helpers
  const getWeekDates = (date) => {
    const week = [];
    const startDate = new Date(date);
    const day = startDate.getDay();
    const diff = startDate.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
    startDate.setDate(diff);

    for (let i = 0; i < 7; i++) {
      const currentDate = new Date(startDate);
      currentDate.setDate(startDate.getDate() + i);
      week.push(currentDate);
    }
    return week;
  };

  const getAppointmentsForDate = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    return appointments.filter(apt => apt.appointment_date === dateStr);
  };

  const formatTime = (time) => {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      'scheduled': 'bg-blue-100 text-blue-800',
      'confirmed': 'bg-green-100 text-green-800',
      'checked_in': 'bg-yellow-100 text-yellow-800',
      'in_progress': 'bg-purple-100 text-purple-800',
      'completed': 'bg-gray-100 text-gray-800',
      'cancelled': 'bg-red-100 text-red-800',
      'no_show': 'bg-orange-100 text-orange-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderCalendarView = () => {
    if (calendarView === 'week') {
      const weekDates = getWeekDates(selectedDate);
      
      return (
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="grid grid-cols-8 gap-4">
            {/* Time column */}
            <div className="text-sm font-medium text-gray-300">
              <div className="h-12"></div> {/* Header spacer */}
              {Array.from({ length: 12 }, (_, i) => (
                <div key={i} className="h-16 border-b border-white/10 flex items-center">
                  {formatTime(`${8 + i}:00`)}
                </div>
              ))}
            </div>
            
            {/* Day columns */}
            {weekDates.map((date, dayIndex) => (
              <div key={dayIndex} className="min-h-0">
                <div className="h-12 flex flex-col items-center justify-center border-b border-white/10">
                  <div className="text-sm font-medium text-white">
                    {date.toLocaleDateString('en-US', { weekday: 'short' })}
                  </div>
                  <div className="text-lg text-gray-300">
                    {date.getDate()}
                  </div>
                </div>
                
                {/* Appointments for this day */}
                <div className="relative">
                  {Array.from({ length: 12 }, (_, i) => (
                    <div key={i} className="h-16 border-b border-white/10 relative">
                      {getAppointmentsForDate(date)
                        .filter(apt => {
                          const aptHour = parseInt(apt.start_time.split(':')[0]);
                          return aptHour === 8 + i;
                        })
                        .map(appointment => (
                          <div
                            key={appointment.id}
                            className="absolute inset-x-1 bg-blue-500/20 border border-blue-400/50 rounded p-1 cursor-pointer hover:bg-blue-500/30 transition-colors"
                            style={{ 
                              height: `${(appointment.duration_minutes / 60) * 64}px`,
                              top: `${(parseInt(appointment.start_time.split(':')[1]) / 60) * 64}px`
                            }}
                            onClick={() => setEditingAppointment(appointment)}
                          >
                            <div className="text-xs text-white font-medium truncate">
                              {appointment.patient_name}
                            </div>
                            <div className="text-xs text-blue-200 truncate">
                              {formatTime(appointment.start_time)}
                            </div>
                            <div className="text-xs text-blue-200 truncate">
                              {appointment.title || appointment.appointment_type}
                            </div>
                          </div>
                        ))}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }
    
    return <div className="text-white">Other calendar views coming soon...</div>;
  };

  const renderAppointmentsList = () => {
    const today = new Date().toISOString().split('T')[0];
    const todayAppointments = appointments.filter(apt => apt.appointment_date === today);
    const upcomingAppointments = appointments.filter(apt => apt.appointment_date > today).slice(0, 10);
    
    return (
      <div className="space-y-6">
        {/* Today's Appointments */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Today's Appointments</h3>
          {todayAppointments.length === 0 ? (
            <p className="text-gray-400">No appointments scheduled for today.</p>
          ) : (
            <div className="space-y-3">
              {todayAppointments.map(appointment => (
                <div key={appointment.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{appointment.patient_name}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(appointment.status)}`}>
                          {appointment.status.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        {formatTime(appointment.start_time)} - {appointment.provider_name} - {appointment.appointment_type}
                      </div>
                      {appointment.notes && (
                        <div className="text-sm text-gray-400 mt-1">{appointment.notes}</div>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      {appointment.status === 'scheduled' && (
                        <button
                          onClick={() => handleUpdateAppointmentStatus(appointment.id, 'confirmed')}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Confirm
                        </button>
                      )}
                      {appointment.status === 'confirmed' && (
                        <button
                          onClick={() => handleUpdateAppointmentStatus(appointment.id, 'checked_in')}
                          className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Check In
                        </button>
                      )}
                      {appointment.status === 'checked_in' && (
                        <button
                          onClick={() => handleUpdateAppointmentStatus(appointment.id, 'completed')}
                          className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Complete
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming Appointments */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Upcoming Appointments</h3>
          {upcomingAppointments.length === 0 ? (
            <p className="text-gray-400">No upcoming appointments.</p>
          ) : (
            <div className="space-y-3">
              {upcomingAppointments.map(appointment => (
                <div key={appointment.id} className="bg-white/5 border border-white/10 rounded p-4 flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">{appointment.patient_name}</div>
                    <div className="text-sm text-gray-300">
                      {new Date(appointment.appointment_date).toLocaleDateString()} at {formatTime(appointment.start_time)} - {appointment.provider_name}
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(appointment.status)}`}>
                    {appointment.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderWaitingList = () => {
    const activeEntries = waitingList.filter(entry => entry.is_active);
    
    return (
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Waiting List</h3>
        {activeEntries.length === 0 ? (
          <p className="text-gray-400">No patients on waiting list.</p>
        ) : (
          <div className="space-y-3">
            {activeEntries
              .sort((a, b) => b.priority - a.priority || new Date(a.created_at) - new Date(b.created_at))
              .map(entry => (
                <div key={entry.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{entry.patient_name}</div>
                        <span className={`px-2 py-1 rounded text-xs ${
                          entry.priority === 4 ? 'bg-red-100 text-red-800' :
                          entry.priority === 3 ? 'bg-orange-100 text-orange-800' :
                          entry.priority === 2 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          Priority {entry.priority}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        {entry.provider_name} - {entry.appointment_type} - {new Date(entry.preferred_date).toLocaleDateString()}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">{entry.reason}</div>
                    </div>
                    <button
                      onClick={() => {
                        setAppointmentFormData({
                          ...appointmentFormData,
                          patient_id: entry.patient_id,
                          provider_id: entry.provider_id,
                          appointment_type: entry.appointment_type,
                          duration_minutes: entry.duration_minutes,
                          title: entry.reason
                        });
                        setShowAppointmentForm(true);
                      }}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Schedule
                    </button>
                  </div>
                </div>
              ))}
          </div>
        )}
      </div>
    );
  };

  const renderAppointmentForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              {editingAppointment ? 'Edit Appointment' : 'New Appointment'}
            </h3>
            <button
              onClick={() => {
                setShowAppointmentForm(false);
                setEditingAppointment(null);
                resetAppointmentForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreateAppointment} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
                <select
                  value={appointmentFormData.patient_id}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, patient_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Provider</label>
                <select
                  value={appointmentFormData.provider_id}
                  onChange={(e) => {
                    setAppointmentFormData({...appointmentFormData, provider_id: e.target.value});
                    if (e.target.value && appointmentFormData.appointment_date) {
                      fetchAvailableSlots(e.target.value, appointmentFormData.appointment_date, appointmentFormData.duration_minutes);
                    }
                  }}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Provider</option>
                  {providers.map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Date</label>
                <input
                  type="date"
                  value={appointmentFormData.appointment_date}
                  onChange={(e) => {
                    setAppointmentFormData({...appointmentFormData, appointment_date: e.target.value});
                    if (appointmentFormData.provider_id && e.target.value) {
                      fetchAvailableSlots(appointmentFormData.provider_id, e.target.value, appointmentFormData.duration_minutes);
                    }
                  }}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Start Time</label>
                <input
                  type="time"
                  value={appointmentFormData.start_time}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, start_time: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Duration (min)</label>
                <select
                  value={appointmentFormData.duration_minutes}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, duration_minutes: parseInt(e.target.value)})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={90}>1.5 hours</option>
                  <option value={120}>2 hours</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Appointment Type</label>
                <select
                  value={appointmentFormData.appointment_type}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, appointment_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="consultation">Consultation</option>
                  <option value="follow_up">Follow Up</option>
                  <option value="annual_physical">Annual Physical</option>
                  <option value="vaccination">Vaccination</option>
                  <option value="procedure">Procedure</option>
                  <option value="therapy">Therapy</option>
                  <option value="emergency">Emergency</option>
                  <option value="telemedicine">Telemedicine</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Title</label>
                <input
                  type="text"
                  value={appointmentFormData.title}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, title: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="Appointment title"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <textarea
                value={appointmentFormData.description}
                onChange={(e) => setAppointmentFormData({...appointmentFormData, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                rows={3}
                placeholder="Appointment description"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
              <textarea
                value={appointmentFormData.notes}
                onChange={(e) => setAppointmentFormData({...appointmentFormData, notes: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                rows={2}
                placeholder="Additional notes"
              />
            </div>

            {availableSlots.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Available Time Slots</label>
                <div className="grid grid-cols-4 gap-2 max-h-40 overflow-y-auto">
                  {availableSlots.map((slot, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        setAppointmentFormData({...appointmentFormData, start_time: slot.start_time});
                        setSelectedSlot(slot);
                      }}
                      className={`p-2 rounded text-sm ${
                        slot.is_available 
                          ? selectedSlot?.start_time === slot.start_time
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-600 hover:bg-gray-500 text-white'
                          : 'bg-red-600/20 text-red-400 cursor-not-allowed'
                      }`}
                      disabled={!slot.is_available}
                    >
                      {formatTime(slot.start_time)}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Creating...' : editingAppointment ? 'Update Appointment' : 'Create Appointment'}
              </button>
              <button
                type="button"
                onClick={() => setShowRecurringForm(true)}
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded"
              >
                Create Recurring
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowAppointmentForm(false);
                  setEditingAppointment(null);
                  resetAppointmentForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">📅 Appointment Scheduling</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowWaitingListForm(true)}
            className="bg-orange-600 hover:bg-orange-700 text-white px-4 py-2 rounded-lg"
          >
            Add to Waiting List
          </button>
          <button
            onClick={() => setShowAppointmentForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            New Appointment
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'calendar', name: 'Calendar View', icon: '📅' },
            { id: 'appointments', name: 'Appointments', icon: '📋' },
            { id: 'waiting-list', name: 'Waiting List', icon: '⏰' },
            { id: 'providers', name: 'Providers', icon: '👨‍⚕️' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeView === tab.id
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

      {/* Calendar Controls */}
      {activeView === 'calendar' && (
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getTime() - 7 * 24 * 60 * 60 * 1000))}
              className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded"
            >
              ← Previous Week
            </button>
            <div className="text-white font-medium">
              {selectedDate.toLocaleDateString('en-US', { 
                month: 'long', 
                year: 'numeric',
                day: 'numeric'
              })}
            </div>
            <button
              onClick={() => setSelectedDate(new Date(selectedDate.getTime() + 7 * 24 * 60 * 60 * 1000))}
              className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded"
            >
              Next Week →
            </button>
            <button
              onClick={() => setSelectedDate(new Date())}
              className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded"
            >
              Today
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white text-sm"
            >
              <option value="">All Providers</option>
              {providers.map(provider => (
                <option key={provider.id} value={provider.id}>
                  {provider.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Content based on active view */}
      {activeView === 'calendar' && renderCalendarView()}
      {activeView === 'appointments' && renderAppointmentsList()}
      {activeView === 'waiting-list' && renderWaitingList()}
      {activeView === 'providers' && (
        <div className="text-white">Provider management coming soon...</div>
      )}

      {/* Forms */}
      {showAppointmentForm && renderAppointmentForm()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Comprehensive Telehealth Module with Video Conferencing
const TelehealthModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);
  const [waitingRoom, setWaitingRoom] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and navigation states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, sessions, waiting-room, video-call
  const [selectedSession, setSelectedSession] = useState(null);
  const [isInCall, setIsInCall] = useState(false);
  
  // Form states
  const [showSessionForm, setShowSessionForm] = useState(false);
  const [showConvertForm, setShowConvertForm] = useState(false);
  
  // Video call states
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  
  // Form data
  const [sessionFormData, setSessionFormData] = useState({
    patient_id: '',
    provider_id: '',
    session_type: 'video_consultation',
    title: '',
    description: '',
    scheduled_start: new Date().toISOString().slice(0, 16),
    duration_minutes: 30,
    recording_enabled: false,
    access_code: ''
  });

  useEffect(() => {
    fetchSessions();
    fetchPatients();
    fetchProviders();
    fetchWaitingRoom();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/telehealth/sessions`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setSessions(response.data);
    } catch (error) {
      console.error('Failed to fetch telehealth sessions:', error);
      setError('Failed to fetch telehealth sessions');
    } finally {
      setLoading(false);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    }
  };

  const fetchWaitingRoom = async () => {
    try {
      const response = await axios.get(`${API}/telehealth/waiting-room`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setWaitingRoom(response.data);
    } catch (error) {
      console.error('Failed to fetch waiting room:', error);
    }
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${API}/telehealth/sessions`, sessionFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setSessions([...sessions, response.data]);
      setSuccess('Telehealth session created successfully!');
      setShowSessionForm(false);
      resetSessionForm();
      fetchSessions();
    } catch (error) {
      console.error('Failed to create telehealth session:', error);
      setError(error.response?.data?.detail || 'Failed to create telehealth session');
    } finally {
      setLoading(false);
    }
  };

  const handleStartSession = async (sessionId) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/telehealth/sessions/${sessionId}/start`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      setSuccess('Telehealth session started successfully!');
      setSelectedSession(sessions.find(s => s.id === sessionId));
      setActiveView('video-call');
      await initializeVideoCall();
      fetchSessions();
    } catch (error) {
      console.error('Failed to start telehealth session:', error);
      setError(error.response?.data?.detail || 'Failed to start telehealth session');
    } finally {
      setLoading(false);
    }
  };

  const handleEndSession = async (sessionId, sessionNotes = '') => {
    try {
      setLoading(true);
      const sessionSummary = {
        session_notes: sessionNotes,
        provider_notes: `Session completed by ${user.username}`,
        technical_issues: []
      };

      await axios.post(`${API}/telehealth/sessions/${sessionId}/end`, sessionSummary, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setSuccess('Telehealth session ended successfully!');
      setIsInCall(false);
      setActiveView('dashboard');
      await cleanupVideoCall();
      fetchSessions();
    } catch (error) {
      console.error('Failed to end telehealth session:', error);
      setError(error.response?.data?.detail || 'Failed to end telehealth session');
    } finally {
      setLoading(false);
    }
  };

  const initializeVideoCall = async () => {
    try {
      // Get user media (camera and microphone)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      setLocalStream(stream);
      setIsInCall(true);
      setConnectionStatus('connected');
      
      // In a production system, this would initialize WebRTC peer connection
      // and handle signaling through the backend WebSocket/SignalR
      
    } catch (error) {
      console.error('Failed to initialize video call:', error);
      setError('Failed to access camera/microphone. Please check permissions.');
    }
  };

  const cleanupVideoCall = async () => {
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
      setLocalStream(null);
    }
    if (remoteStream) {
      remoteStream.getTracks().forEach(track => track.stop());
      setRemoteStream(null);
    }
    setIsInCall(false);
    setConnectionStatus('disconnected');
  };

  const toggleVideo = () => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsVideoEnabled(videoTrack.enabled);
      }
    }
  };

  const toggleAudio = () => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsAudioEnabled(audioTrack.enabled);
      }
    }
  };

  const handleScreenShare = async () => {
    try {
      if (!isScreenSharing) {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
        setIsScreenSharing(true);
        // In production, replace video track in peer connection
      } else {
        setIsScreenSharing(false);
        // Switch back to camera
        await initializeVideoCall();
      }
    } catch (error) {
      console.error('Screen sharing failed:', error);
      setError('Screen sharing failed');
    }
  };

  const sendChatMessage = async () => {
    if (!newMessage.trim() || !selectedSession) return;
    
    try {
      const messageData = {
        message: newMessage.trim(),
        sender_type: 'provider',
        message_type: 'text'
      };

      await axios.post(`${API}/telehealth/sessions/${selectedSession.id}/chat`, messageData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setChatMessages([...chatMessages, {
        id: Date.now(),
        sender_name: user.username,
        message: newMessage.trim(),
        timestamp: new Date(),
        sender_type: 'provider'
      }]);
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send chat message:', error);
    }
  };

  const resetSessionForm = () => {
    setSessionFormData({
      patient_id: '',
      provider_id: '',
      session_type: 'video_consultation',
      title: '',
      description: '',
      scheduled_start: new Date().toISOString().slice(0, 16),
      duration_minutes: 30,
      recording_enabled: false,
      access_code: ''
    });
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      'scheduled': 'bg-blue-100 text-blue-800',
      'waiting': 'bg-yellow-100 text-yellow-800',
      'in_progress': 'bg-green-100 text-green-800',
      'completed': 'bg-gray-100 text-gray-800',
      'cancelled': 'bg-red-100 text-red-800',
      'no_show': 'bg-orange-100 text-orange-800',
      'technical_issues': 'bg-purple-100 text-purple-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    const todaySessions = sessions.filter(session => 
      new Date(session.scheduled_start).toDateString() === new Date().toDateString()
    );
    const upcomingSessions = sessions.filter(session => 
      new Date(session.scheduled_start) > new Date()
    ).slice(0, 5);

    return (
      <div className="space-y-6">
        {/* Today's Sessions */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📅 Today's Telehealth Sessions</h3>
          {todaySessions.length === 0 ? (
            <p className="text-gray-400">No telehealth sessions scheduled for today.</p>
          ) : (
            <div className="space-y-3">
              {todaySessions.map(session => (
                <div key={session.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{session.patient_name}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(session.status)}`}>
                          {session.status.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        {formatDateTime(session.scheduled_start)} - {session.provider_name}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">{session.title}</div>
                    </div>
                    <div className="flex space-x-2">
                      {session.status === 'scheduled' && (
                        <button
                          onClick={() => handleStartSession(session.id)}
                          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
                        >
                          🎥 Start Session
                        </button>
                      )}
                      {session.status === 'in_progress' && (
                        <button
                          onClick={() => {
                            setSelectedSession(session);
                            setActiveView('video-call');
                          }}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                        >
                          💻 Join Session
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{todaySessions.length}</div>
                <div className="text-sm text-gray-300">Today's Sessions</div>
              </div>
              <div className="text-2xl">📅</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">
                  {sessions.filter(s => s.status === 'in_progress').length}
                </div>
                <div className="text-sm text-gray-300">Active Sessions</div>
              </div>
              <div className="text-2xl">🔴</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{waitingRoom.length}</div>
                <div className="text-sm text-gray-300">Waiting Room</div>
              </div>
              <div className="text-2xl">⏰</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">
                  {sessions.filter(s => s.status === 'completed' && 
                    new Date(s.actual_end).toDateString() === new Date().toDateString()).length}
                </div>
                <div className="text-sm text-gray-300">Completed Today</div>
              </div>
              <div className="text-2xl">✅</div>
            </div>
          </div>
        </div>

        {/* Upcoming Sessions */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">🔮 Upcoming Sessions</h3>
          {upcomingSessions.length === 0 ? (
            <p className="text-gray-400">No upcoming telehealth sessions.</p>
          ) : (
            <div className="space-y-3">
              {upcomingSessions.map(session => (
                <div key={session.id} className="bg-white/5 border border-white/10 rounded p-4 flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">{session.patient_name}</div>
                    <div className="text-sm text-gray-300">
                      {formatDateTime(session.scheduled_start)} - {session.session_type}
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs ${getStatusColor(session.status)}`}>
                    {session.status.replace('_', ' ')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderVideoCall = () => {
    if (!selectedSession) return null;

    return (
      <div className="bg-gray-900 rounded-lg p-4 h-screen">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between mb-4">
            <div className="text-white">
              <h3 className="text-lg font-semibold">{selectedSession.title}</h3>
              <p className="text-sm text-gray-300">
                {selectedSession.patient_name} - {selectedSession.provider_name}
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <span className={`px-3 py-1 rounded text-sm ${
                connectionStatus === 'connected' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
              }`}>
                {connectionStatus === 'connected' ? '🟢 Connected' : '🔴 Disconnected'}
              </span>
            </div>
          </div>

          {/* Video Area */}
          <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Main Video */}
            <div className="lg:col-span-2 bg-gray-800 rounded-lg relative">
              <div className="aspect-video bg-gray-700 rounded-lg flex items-center justify-center">
                {localStream ? (
                  <video
                    ref={(video) => {
                      if (video && localStream) {
                        video.srcObject = localStream;
                      }
                    }}
                    autoPlay
                    muted
                    className="w-full h-full object-cover rounded-lg"
                  />
                ) : (
                  <div className="text-center text-gray-400">
                    <div className="text-4xl mb-2">📹</div>
                    <p>Camera not available</p>
                  </div>
                )}
              </div>
              
              {/* Video Controls */}
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex space-x-4">
                <button
                  onClick={toggleAudio}
                  className={`p-3 rounded-full ${
                    isAudioEnabled 
                      ? 'bg-gray-600 hover:bg-gray-700 text-white' 
                      : 'bg-red-600 hover:bg-red-700 text-white'
                  }`}
                >
                  {isAudioEnabled ? '🎤' : '🔇'}
                </button>
                
                <button
                  onClick={toggleVideo}
                  className={`p-3 rounded-full ${
                    isVideoEnabled 
                      ? 'bg-gray-600 hover:bg-gray-700 text-white' 
                      : 'bg-red-600 hover:bg-red-700 text-white'
                  }`}
                >
                  {isVideoEnabled ? '📹' : '📷'}
                </button>
                
                <button
                  onClick={handleScreenShare}
                  className={`p-3 rounded-full ${
                    isScreenSharing 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                      : 'bg-gray-600 hover:bg-gray-700 text-white'
                  }`}
                >
                  🖥️
                </button>
                
                <button
                  onClick={() => handleEndSession(selectedSession.id)}
                  className="p-3 rounded-full bg-red-600 hover:bg-red-700 text-white"
                >
                  📞
                </button>
              </div>
            </div>

            {/* Chat Panel */}
            <div className="bg-white/5 border border-white/10 rounded-lg flex flex-col">
              <div className="p-4 border-b border-white/10">
                <h4 className="text-white font-medium">💬 Session Chat</h4>
              </div>
              
              <div className="flex-1 p-4 overflow-y-auto space-y-3">
                {chatMessages.map(message => (
                  <div key={message.id} className="text-sm">
                    <div className="text-gray-300 font-medium">{message.sender_name}</div>
                    <div className="text-white">{message.message}</div>
                    <div className="text-xs text-gray-400">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="p-4 border-t border-white/10">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                    placeholder="Type a message..."
                    className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
                  />
                  <button
                    onClick={sendChatMessage}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded text-sm"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSessionForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">🎥 New Telehealth Session</h3>
            <button
              onClick={() => {
                setShowSessionForm(false);
                resetSessionForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreateSession} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
                <select
                  value={sessionFormData.patient_id}
                  onChange={(e) => setSessionFormData({...sessionFormData, patient_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Provider</label>
                <select
                  value={sessionFormData.provider_id}
                  onChange={(e) => setSessionFormData({...sessionFormData, provider_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Provider</option>
                  {providers.map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Session Type</label>
                <select
                  value={sessionFormData.session_type}
                  onChange={(e) => setSessionFormData({...sessionFormData, session_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="video_consultation">Video Consultation</option>
                  <option value="audio_only">Audio Only</option>
                  <option value="follow_up">Follow Up</option>
                  <option value="therapy_session">Therapy Session</option>
                  <option value="group_session">Group Session</option>
                  <option value="emergency_consult">Emergency Consult</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Duration (minutes)</label>
                <select
                  value={sessionFormData.duration_minutes}
                  onChange={(e) => setSessionFormData({...sessionFormData, duration_minutes: parseInt(e.target.value)})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={90}>1.5 hours</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Scheduled Start</label>
              <input
                type="datetime-local"
                value={sessionFormData.scheduled_start}
                onChange={(e) => setSessionFormData({...sessionFormData, scheduled_start: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Title</label>
              <input
                type="text"
                value={sessionFormData.title}
                onChange={(e) => setSessionFormData({...sessionFormData, title: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Session title"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <textarea
                value={sessionFormData.description}
                onChange={(e) => setSessionFormData({...sessionFormData, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                rows={3}
                placeholder="Session description"
              />
            </div>

            <div className="flex items-center space-x-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={sessionFormData.recording_enabled}
                  onChange={(e) => setSessionFormData({...sessionFormData, recording_enabled: e.target.checked})}
                  className="rounded"
                />
                <span className="text-gray-300">Enable Recording</span>
              </label>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Session'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowSessionForm(false);
                  resetSessionForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">💻 Telehealth System</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowSessionForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            🎥 New Session
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      {activeView !== 'video-call' && (
        <div className="border-b border-white/20 mb-6">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', name: 'Dashboard', icon: '📊' },
              { id: 'sessions', name: 'All Sessions', icon: '📋' },
              { id: 'waiting-room', name: 'Waiting Room', icon: '⏰' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveView(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                  activeView === tab.id
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
      )}

      {/* Content based on active view */}
      {activeView === 'dashboard' && renderDashboard()}
      {activeView === 'sessions' && (
        <div className="text-white">Sessions list view coming soon...</div>
      )}
      {activeView === 'waiting-room' && (
        <div className="text-white">Waiting room management coming soon...</div>
      )}
      {activeView === 'video-call' && renderVideoCall()}

      {/* Forms */}
      {showSessionForm && renderSessionForm()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Comprehensive Lab Orders Management Module
const LabOrdersModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [labOrders, setLabOrders] = useState([]);
  const [labTests, setLabTests] = useState([]);
  const [labResults, setLabResults] = useState([]);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and navigation states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, orders, tests, results
  const [selectedOrder, setSelectedOrder] = useState(null);
  
  // Form states
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [showResultsModal, setShowResultsModal] = useState(false);
  
  // Form data
  const [orderFormData, setOrderFormData] = useState({
    patient_id: '',
    provider_id: '',
    tests: [],
    priority: 'routine',
    clinical_info: '',
    diagnosis_codes: [],
    lab_provider: 'internal',
    encounter_id: ''
  });
  
  // Stats data
  const [labStats, setLabStats] = useState({
    totalOrders: 0,
    pendingOrders: 0,
    completedToday: 0,
    criticalResults: 0
  });

  useEffect(() => {
    fetchLabData();
  }, []);

  const fetchLabData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchLabOrders(),
        fetchLabTests(),
        fetchPatients(),
        fetchProviders(),
        fetchLabResults()
      ]);
    } catch (error) {
      console.error('Failed to fetch lab data:', error);
      setError('Failed to fetch lab data');
    } finally {
      setLoading(false);
    }
  };

  const fetchLabOrders = async () => {
    try {
      const response = await axios.get(`${API}/lab-orders`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setLabOrders(response.data);
      
      // Update stats
      const today = new Date().toDateString();
      setLabStats(prev => ({
        ...prev,
        totalOrders: response.data.length,
        pendingOrders: response.data.filter(order => 
          ['draft', 'ordered', 'collected', 'processing'].includes(order.status)
        ).length,
        completedToday: response.data.filter(order => 
          order.completed_date && new Date(order.completed_date).toDateString() === today
        ).length
      }));
      
    } catch (error) {
      console.error('Failed to fetch lab orders:', error);
    }
  };

  const fetchLabTests = async () => {
    try {
      const response = await axios.get(`${API}/lab-tests`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setLabTests(response.data);
    } catch (error) {
      console.error('Failed to fetch lab tests:', error);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    }
  };

  const fetchLabResults = async () => {
    try {
      const response = await axios.get(`${API}/lab-results`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setLabResults(response.data);
      
      // Update critical results count
      const criticalCount = response.data.filter(result => result.critical_value).length;
      setLabStats(prev => ({ ...prev, criticalResults: criticalCount }));
      
    } catch (error) {
      console.error('Failed to fetch lab results:', error);
    }
  };

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${API}/lab-orders`, orderFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setLabOrders([...labOrders, response.data]);
      setSuccess('Lab order created successfully!');
      setShowOrderForm(false);
      resetOrderForm();
      fetchLabOrders();
    } catch (error) {
      console.error('Failed to create lab order:', error);
      setError(error.response?.data?.detail || 'Failed to create lab order');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitOrder = async (orderId) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/lab-orders/${orderId}/submit`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      setSuccess('Lab order submitted to external lab successfully!');
      fetchLabOrders();
    } catch (error) {
      console.error('Failed to submit lab order:', error);
      setError(error.response?.data?.detail || 'Failed to submit lab order');
    } finally {
      setLoading(false);
    }
  };

  const handleRetrieveResults = async (orderId) => {
    try {
      setLoading(true);
      const response = await axios.post(`${API}/lab-orders/${orderId}/results`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      setSuccess('Lab results retrieved successfully!');
      fetchLabOrders();
      fetchLabResults();
    } catch (error) {
      console.error('Failed to retrieve lab results:', error);
      setError(error.response?.data?.detail || 'Failed to retrieve lab results');
    } finally {
      setLoading(false);
    }
  };

  const resetOrderForm = () => {
    setOrderFormData({
      patient_id: '',
      provider_id: '',
      tests: [],
      priority: 'routine',
      clinical_info: '',
      diagnosis_codes: [],
      lab_provider: 'internal',
      encounter_id: ''
    });
  };

  const addTestToOrder = (test) => {
    const newTest = {
      test_id: test.id,
      test_code: test.test_code,
      test_name: test.test_name,
      quantity: 1,
      specimen_type: test.specimen_type,
      fasting_required: test.fasting_required,
      priority: orderFormData.priority
    };
    
    setOrderFormData({
      ...orderFormData,
      tests: [...orderFormData.tests, newTest]
    });
  };

  const removeTestFromOrder = (testIndex) => {
    setOrderFormData({
      ...orderFormData,
      tests: orderFormData.tests.filter((_, index) => index !== testIndex)
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      'draft': 'bg-gray-100 text-gray-800',
      'ordered': 'bg-blue-100 text-blue-800',
      'collected': 'bg-yellow-100 text-yellow-800',
      'processing': 'bg-purple-100 text-purple-800',
      'completed': 'bg-green-100 text-green-800',
      'resulted': 'bg-green-100 text-green-800',
      'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'routine': 'bg-blue-100 text-blue-800',
      'urgent': 'bg-orange-100 text-orange-800',
      'stat': 'bg-red-100 text-red-800',
      'asap': 'bg-red-100 text-red-800'
    };
    return colors[priority] || 'bg-blue-100 text-blue-800';
  };

  const renderDashboard = () => {
    const todayOrders = labOrders.filter(order => 
      new Date(order.created_at).toDateString() === new Date().toDateString()
    );

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{labStats.totalOrders}</div>
                <div className="text-sm text-gray-300">Total Orders</div>
              </div>
              <div className="text-2xl">🧪</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{labStats.pendingOrders}</div>
                <div className="text-sm text-gray-300">Pending Orders</div>
              </div>
              <div className="text-2xl">⏳</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{labStats.completedToday}</div>
                <div className="text-sm text-gray-300">Completed Today</div>
              </div>
              <div className="text-2xl">✅</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{labStats.criticalResults}</div>
                <div className="text-sm text-gray-300">Critical Results</div>
              </div>
              <div className="text-2xl">🚨</div>
            </div>
          </div>
        </div>

        {/* Today's Orders */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📋 Today's Lab Orders</h3>
          {todayOrders.length === 0 ? (
            <p className="text-gray-400">No lab orders created today.</p>
          ) : (
            <div className="space-y-3">
              {todayOrders.map(order => (
                <div key={order.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{order.order_number}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(order.status)}`}>
                          {order.status}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(order.priority)}`}>
                          {order.priority}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        {order.patient_name} - {order.tests.length} test(s)
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        Provider: {order.provider_name}
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      {order.status === 'draft' && (
                        <button
                          onClick={() => handleSubmitOrder(order.id)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Submit Order
                        </button>
                      )}
                      {order.status === 'ordered' && (
                        <button
                          onClick={() => handleRetrieveResults(order.id)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Check Results
                        </button>
                      )}
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available Lab Tests */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">🔬 Available Lab Tests</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {labTests.slice(0, 6).map(test => (
              <div key={test.id} className="bg-white/5 border border-white/10 rounded p-4">
                <div className="text-white font-medium">{test.test_name}</div>
                <div className="text-sm text-gray-300 mt-1">Code: {test.test_code}</div>
                <div className="text-sm text-gray-400 mt-1">Category: {test.category}</div>
                <div className="text-sm text-gray-400 mt-1">
                  Turnaround: {test.turnaround_time_hours}h
                </div>
                {test.fasting_required && (
                  <div className="text-xs text-yellow-400 mt-1">⚠️ Fasting Required</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderOrderForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">🧪 New Lab Order</h3>
            <button
              onClick={() => {
                setShowOrderForm(false);
                resetOrderForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreateOrder} className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
                <select
                  value={orderFormData.patient_id}
                  onChange={(e) => setOrderFormData({...orderFormData, patient_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Provider</label>
                <select
                  value={orderFormData.provider_id}
                  onChange={(e) => setOrderFormData({...orderFormData, provider_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Provider</option>
                  {providers.map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
                <select
                  value={orderFormData.priority}
                  onChange={(e) => setOrderFormData({...orderFormData, priority: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="routine">Routine</option>
                  <option value="urgent">Urgent</option>
                  <option value="stat">STAT</option>
                  <option value="asap">ASAP</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Lab Provider</label>
                <select
                  value={orderFormData.lab_provider}
                  onChange={(e) => setOrderFormData({...orderFormData, lab_provider: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="internal">Internal Lab</option>
                  <option value="labcorp">LabCorp</option>
                  <option value="quest">Quest Diagnostics</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Selected Tests */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Selected Tests</label>
              {orderFormData.tests.length === 0 ? (
                <p className="text-gray-400 text-sm">No tests selected</p>
              ) : (
                <div className="space-y-2 mb-4">
                  {orderFormData.tests.map((test, index) => (
                    <div key={index} className="bg-white/5 border border-white/10 rounded p-3 flex items-center justify-between">
                      <div>
                        <div className="text-white font-medium">{test.test_name}</div>
                        <div className="text-sm text-gray-300">
                          Code: {test.test_code} | Specimen: {test.specimen_type}
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeTestFromOrder(index)}
                        className="text-red-400 hover:text-red-300"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Available Tests to Add */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Add Tests</label>
              <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
                {labTests.map(test => (
                  <button
                    key={test.id}
                    type="button"
                    onClick={() => addTestToOrder(test)}
                    disabled={orderFormData.tests.some(t => t.test_id === test.id)}
                    className="bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 disabled:opacity-50 text-white p-2 rounded text-sm text-left"
                  >
                    <div className="font-medium">{test.test_name}</div>
                    <div className="text-xs text-gray-300">{test.test_code}</div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Clinical Information</label>
              <textarea
                value={orderFormData.clinical_info}
                onChange={(e) => setOrderFormData({...orderFormData, clinical_info: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                rows={3}
                placeholder="Clinical notes, symptoms, diagnosis..."
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading || orderFormData.tests.length === 0}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Lab Order'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowOrderForm(false);
                  resetOrderForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">🧪 Lab Orders Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowOrderForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            🧪 New Lab Order
          </button>
          <button
            onClick={() => fetchLabData()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'orders', name: 'All Orders', icon: '📋' },
            { id: 'tests', name: 'Lab Tests', icon: '🔬' },
            { id: 'results', name: 'Results', icon: '📄' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeView === tab.id
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

      {/* Content based on active view */}
      {activeView === 'dashboard' && renderDashboard()}
      {activeView === 'orders' && (
        <div className="text-white">All orders list view coming soon...</div>
      )}
      {activeView === 'tests' && (
        <div className="text-white">Lab tests catalog view coming soon...</div>
      )}
      {activeView === 'results' && (
        <div className="text-white">Lab results view coming soon...</div>
      )}

      {/* Forms */}
      {showOrderForm && renderOrderForm()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Comprehensive Insurance Verification Management Module
const PatientPortalModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [portalUsers, setPortalUsers] = useState([]);
  const [appointmentRequests, setAppointmentRequests] = useState([]);
  const [patientMessages, setPatientMessages] = useState([]);
  const [refillRequests, setRefillRequests] = useState([]);
  const [portalActivities, setPortalActivities] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and navigation states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, users, requests, messages, analytics
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRequest, setSelectedRequest] = useState(null);
  
  // Form states
  const [showUserDetails, setShowUserDetails] = useState(false);
  const [showMessageReply, setShowMessageReply] = useState(false);
  const [replyMessage, setReplyMessage] = useState('');
  
  // Analytics data
  const [portalStats, setPortalStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    newRegistrations: 0,
    pendingRequests: 0,
    messagesUnread: 0
  });

  useEffect(() => {
    fetchPortalData();
  }, []);

  const fetchPortalData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchPortalUsers(),
        fetchAppointmentRequests(),
        fetchPatientMessages(),
        fetchRefillRequests(),
        fetchPortalActivities()
      ]);
    } catch (error) {
      console.error('Failed to fetch portal data:', error);
      setError('Failed to fetch portal data');
    } finally {
      setLoading(false);
    }
  };

  const fetchPortalUsers = async () => {
    try {
      // Since we don't have a direct endpoint for portal users list,
      // we'll create a comprehensive view from existing data
      const response = await axios.get(`${API}/patients`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      // Mock portal user data based on patients
      const mockPortalUsers = response.data.slice(0, 10).map(patient => ({
        id: `portal_${patient.id}`,
        patient_id: patient.id,
        patient_name: `${patient.name?.[0]?.given?.[0] || ''} ${patient.name?.[0]?.family || ''}`.trim(),
        email: patient.telecom?.find(t => t.system === 'email')?.value || 'Not provided',
        username: `patient_${patient.id.slice(-4)}`,
        is_active: true,
        is_verified: Math.random() > 0.2, // 80% verified
        last_login: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        created_at: patient.created_at
      }));
      
      setPortalUsers(mockPortalUsers);
      
      // Update stats
      setPortalStats(prev => ({
        ...prev,
        totalUsers: mockPortalUsers.length,
        activeUsers: mockPortalUsers.filter(u => u.is_active).length,
        newRegistrations: mockPortalUsers.filter(u => 
          new Date(u.created_at) > new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
        ).length
      }));
      
    } catch (error) {
      console.error('Failed to fetch portal users:', error);
    }
  };

  const fetchAppointmentRequests = async () => {
    try {
      // Mock appointment requests data
      const mockRequests = [
        {
          id: 'req_001',
          patient_name: 'Sarah Johnson',
          appointment_type: 'Annual Physical',
          preferred_date: '2024-01-20',
          preferred_time: '10:00',
          reason: 'Annual checkup and preventive care',
          urgency: 'routine',
          status: 'pending',
          created_at: new Date().toISOString()
        },
        {
          id: 'req_002',
          patient_name: 'Michael Chen',
          appointment_type: 'Follow-up',
          preferred_date: '2024-01-22',
          preferred_time: '14:30',
          reason: 'Follow-up for blood pressure monitoring',
          urgency: 'routine',
          status: 'approved',
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
        }
      ];
      
      setAppointmentRequests(mockRequests);
      
      setPortalStats(prev => ({
        ...prev,
        pendingRequests: mockRequests.filter(r => r.status === 'pending').length
      }));
      
    } catch (error) {
      console.error('Failed to fetch appointment requests:', error);
    }
  };

  const fetchPatientMessages = async () => {
    try {
      // Mock patient messages data
      const mockMessages = [
        {
          id: 'msg_001',
          patient_name: 'Emma Wilson',
          subject: 'Question about lab results',
          message: 'I received my lab results but have some questions about the cholesterol levels.',
          message_type: 'general',
          priority: 'normal',
          status: 'unread',
          created_at: new Date().toISOString()
        },
        {
          id: 'msg_002',
          patient_name: 'David Brown',
          subject: 'Prescription refill needed',
          message: 'My blood pressure medication is running low, can I get a refill?',
          message_type: 'prescription',
          priority: 'normal',
          status: 'read',
          created_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString()
        },
        {
          id: 'msg_003',
          patient_name: 'Lisa Garcia',
          subject: 'Urgent: Side effects from medication',
          message: 'I\'m experiencing some concerning side effects from the new medication.',
          message_type: 'urgent',
          priority: 'high',
          status: 'unread',
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
        }
      ];
      
      setPatientMessages(mockMessages);
      
      setPortalStats(prev => ({
        ...prev,
        messagesUnread: mockMessages.filter(m => m.status === 'unread').length
      }));
      
    } catch (error) {
      console.error('Failed to fetch patient messages:', error);
    }
  };

  const fetchRefillRequests = async () => {
    try {
      // Mock refill requests data
      const mockRefills = [
        {
          id: 'refill_001',
          patient_name: 'Robert Taylor',
          medication_name: 'Lisinopril 10mg',
          quantity_requested: 90,
          pharmacy_name: 'CVS Pharmacy',
          status: 'pending',
          urgency: 'routine',
          created_at: new Date().toISOString()
        }
      ];
      
      setRefillRequests(mockRefills);
      
    } catch (error) {
      console.error('Failed to fetch refill requests:', error);
    }
  };

  const fetchPortalActivities = async () => {
    try {
      // Mock activity data
      const mockActivities = [
        {
          id: 'act_001',
          patient_name: 'Various Patients',
          activity_type: 'login',
          description: '15 patient logins in the last hour',
          created_at: new Date().toISOString()
        },
        {
          id: 'act_002',
          patient_name: 'Sarah Johnson',
          activity_type: 'appointment_request',
          description: 'New appointment request submitted',
          created_at: new Date(Date.now() - 30 * 60 * 1000).toISOString()
        }
      ];
      
      setPortalActivities(mockActivities);
      
    } catch (error) {
      console.error('Failed to fetch portal activities:', error);
    }
  };

  const handleApproveRequest = async (requestId) => {
    try {
      setLoading(true);
      
      // Update request status
      setAppointmentRequests(prev => 
        prev.map(req => 
          req.id === requestId 
            ? { ...req, status: 'approved', processed_at: new Date().toISOString() }
            : req
        )
      );
      
      setSuccess('Appointment request approved successfully!');
      
    } catch (error) {
      console.error('Failed to approve request:', error);
      setError('Failed to approve appointment request');
    } finally {
      setLoading(false);
    }
  };

  const handleReplyToMessage = async (messageId) => {
    try {
      setLoading(true);
      
      // Mark message as replied
      setPatientMessages(prev => 
        prev.map(msg => 
          msg.id === messageId 
            ? { ...msg, status: 'replied', replied_at: new Date().toISOString() }
            : msg
        )
      );
      
      setSuccess('Reply sent successfully!');
      setShowMessageReply(false);
      setReplyMessage('');
      
    } catch (error) {
      console.error('Failed to send reply:', error);
      setError('Failed to send reply');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'low': 'bg-gray-100 text-gray-800',
      'normal': 'bg-blue-100 text-blue-800',
      'high': 'bg-orange-100 text-orange-800',
      'urgent': 'bg-red-100 text-red-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'approved': 'bg-green-100 text-green-800',
      'denied': 'bg-red-100 text-red-800',
      'unread': 'bg-red-100 text-red-800',
      'read': 'bg-blue-100 text-blue-800',
      'replied': 'bg-green-100 text-green-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.totalUsers}</div>
                <div className="text-sm text-gray-300">Total Users</div>
              </div>
              <div className="text-2xl">👥</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.activeUsers}</div>
                <div className="text-sm text-gray-300">Active Users</div>
              </div>
              <div className="text-2xl">🟢</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.pendingRequests}</div>
                <div className="text-sm text-gray-300">Pending Requests</div>
              </div>
              <div className="text-2xl">📋</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.messagesUnread}</div>
                <div className="text-sm text-gray-300">Unread Messages</div>
              </div>
              <div className="text-2xl">📧</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.newRegistrations}</div>
                <div className="text-sm text-gray-300">New This Month</div>
              </div>
              <div className="text-2xl">🆕</div>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pending Appointment Requests */}
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">📋 Pending Appointment Requests</h3>
            {appointmentRequests.filter(req => req.status === 'pending').length === 0 ? (
              <p className="text-gray-400">No pending appointment requests.</p>
            ) : (
              <div className="space-y-3">
                {appointmentRequests.filter(req => req.status === 'pending').map(request => (
                  <div key={request.id} className="bg-white/5 border border-white/10 rounded p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="text-white font-medium">{request.patient_name}</div>
                        <div className="text-sm text-gray-300">
                          {request.appointment_type} - {request.preferred_date} at {request.preferred_time}
                        </div>
                        <div className="text-sm text-gray-400 mt-1">{request.reason}</div>
                      </div>
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApproveRequest(request.id)}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => setSelectedRequest(request)}
                          className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm"
                        >
                          View
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Unread Messages */}
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">📧 Unread Messages</h3>
            {patientMessages.filter(msg => msg.status === 'unread').length === 0 ? (
              <p className="text-gray-400">No unread messages.</p>
            ) : (
              <div className="space-y-3">
                {patientMessages.filter(msg => msg.status === 'unread').map(message => (
                  <div key={message.id} className="bg-white/5 border border-white/10 rounded p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <div className="text-white font-medium">{message.patient_name}</div>
                          <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(message.priority)}`}>
                            {message.priority}
                          </span>
                        </div>
                        <div className="text-sm text-gray-300 mt-1">{message.subject}</div>
                        <div className="text-sm text-gray-400 mt-1 truncate">{message.message}</div>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedUser(message);
                          setShowMessageReply(true);
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Reply
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Portal Activity */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📊 Recent Portal Activity</h3>
          <div className="space-y-3">
            {portalActivities.slice(0, 5).map(activity => (
              <div key={activity.id} className="flex items-center justify-between py-2 border-b border-white/10 last:border-b-0">
                <div className="flex items-center space-x-3">
                  <div className="text-xl">
                    {activity.activity_type === 'login' ? '🔐' : 
                     activity.activity_type === 'appointment_request' ? '📅' : 
                     activity.activity_type === 'message_sent' ? '📧' : '📋'}
                  </div>
                  <div>
                    <div className="text-white text-sm">{activity.description}</div>
                    <div className="text-xs text-gray-400">
                      {new Date(activity.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderUserManagement = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">👥 Portal Users</h3>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/20">
                  <th className="text-left text-white font-medium pb-3">Patient Name</th>
                  <th className="text-left text-white font-medium pb-3">Username</th>
                  <th className="text-left text-white font-medium pb-3">Email</th>
                  <th className="text-left text-white font-medium pb-3">Status</th>
                  <th className="text-left text-white font-medium pb-3">Last Login</th>
                  <th className="text-left text-white font-medium pb-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {portalUsers.map(user => (
                  <tr key={user.id} className="border-b border-white/10">
                    <td className="text-white py-3">{user.patient_name}</td>
                    <td className="text-gray-300 py-3">{user.username}</td>
                    <td className="text-gray-300 py-3">{user.email}</td>
                    <td className="py-3">
                      <div className="flex items-center space-x-2">
                        <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                        {user.is_verified && (
                          <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                            Verified
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="text-gray-300 py-3 text-sm">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => setSelectedUser(user)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderMessageReplyModal = () => {
    if (!showMessageReply || !selectedUser) return null;

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">Reply to Message</h3>
            <button
              onClick={() => {
                setShowMessageReply(false);
                setReplyMessage('');
                setSelectedUser(null);
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="mb-4">
            <div className="bg-white/5 border border-white/10 rounded p-4">
              <div className="text-white font-medium mb-2">Original Message from {selectedUser.patient_name || 'Patient'}</div>
              <div className="text-gray-300 text-sm">{selectedUser.subject}</div>
              <div className="text-gray-400 text-sm mt-2">{selectedUser.message}</div>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">Your Reply</label>
            <textarea
              value={replyMessage}
              onChange={(e) => setReplyMessage(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              rows={6}
              placeholder="Type your reply..."
              required
            />
          </div>

          <div className="flex space-x-4">
            <button
              onClick={() => handleReplyToMessage(selectedUser.id)}
              disabled={loading || !replyMessage.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
            >
              {loading ? 'Sending...' : 'Send Reply'}
            </button>
            <button
              onClick={() => {
                setShowMessageReply(false);
                setReplyMessage('');
                setSelectedUser(null);
              }}
              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">🌐 Patient Portal Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => fetchPortalData()}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'users', name: 'Portal Users', icon: '👥' },
            { id: 'requests', name: 'Requests', icon: '📋' },
            { id: 'messages', name: 'Messages', icon: '📧' },
            { id: 'analytics', name: 'Analytics', icon: '📈' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeView === tab.id
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

      {/* Content based on active view */}
      {activeView === 'dashboard' && renderDashboard()}
      {activeView === 'users' && renderUserManagement()}
      {activeView === 'requests' && (
        <div className="text-white">Appointment requests management view coming soon...</div>
      )}
      {activeView === 'messages' && (
        <div className="text-white">Message management view coming soon...</div>
      )}
      {activeView === 'analytics' && (
        <div className="text-white">Portal analytics view coming soon...</div>
      )}

      {/* Modals */}
      {renderMessageReplyModal()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Comprehensive Insurance Verification Management Module
const InsuranceModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [insurancePlans, setInsurancePlans] = useState([]);
  const [insurancePolicies, setInsurancePolicies] = useState([]);
  const [verifications, setVerifications] = useState([]);
  const [priorAuths, setPriorAuths] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and navigation states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, plans, policies, verifications, prior-auth
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  
  // Form states
  const [showPolicyForm, setShowPolicyForm] = useState(false);
  const [showVerificationForm, setShowVerificationForm] = useState(false);
  const [showPriorAuthForm, setShowPriorAuthForm] = useState(false);
  
  // Form data
  const [policyFormData, setPolicyFormData] = useState({
    patient_id: '',
    insurance_plan_id: '',
    policy_number: '',
    group_number: '',
    subscriber_id: '',
    subscriber_name: '',
    relationship_to_subscriber: 'self',
    effective_date: new Date().toISOString().split('T')[0],
    is_primary: true,
    copay_amount: '',
    deductible_amount: ''
  });
  
  const [verificationFormData, setVerificationFormData] = useState({
    patient_id: '',
    insurance_policy_id: '',
    service_codes: ['99213'], // Default office visit
    provider_npi: ''
  });
  
  // Stats data
  const [insuranceStats, setInsuranceStats] = useState({
    totalPolicies: 0,
    verifiedToday: 0,
    pendingVerifications: 0,
    activeAuthorizations: 0
  });

  useEffect(() => {
    fetchInsuranceData();
  }, []);

  const fetchInsuranceData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchInsurancePlans(),
        fetchPatients(),
        fetchVerifications()
      ]);
    } catch (error) {
      console.error('Failed to fetch insurance data:', error);
      setError('Failed to fetch insurance data');
    } finally {
      setLoading(false);
    }
  };

  const fetchInsurancePlans = async () => {
    try {
      const response = await axios.get(`${API}/insurance-plans`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setInsurancePlans(response.data);
    } catch (error) {
      console.error('Failed to fetch insurance plans:', error);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    }
  };

  const fetchVerifications = async () => {
    try {
      const response = await axios.get(`${API}/insurance-verifications`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setVerifications(response.data);
      
      // Update stats
      const today = new Date().toDateString();
      setInsuranceStats(prev => ({
        ...prev,
        verifiedToday: response.data.filter(v => 
          new Date(v.verification_date).toDateString() === today
        ).length,
        pendingVerifications: response.data.filter(v => v.status === 'pending').length
      }));
      
    } catch (error) {
      console.error('Failed to fetch verifications:', error);
    }
  };

  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${API}/insurance-policies`, policyFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setInsurancePolicies([...insurancePolicies, response.data]);
      setSuccess('Insurance policy created successfully!');
      setShowPolicyForm(false);
      resetPolicyForm();
    } catch (error) {
      console.error('Failed to create insurance policy:', error);
      setError(error.response?.data?.detail || 'Failed to create insurance policy');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyInsurance = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await axios.post(`${API}/insurance-verification`, verificationFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setSuccess('Insurance verification completed successfully!');
      setShowVerificationForm(false);
      resetVerificationForm();
      fetchVerifications();
    } catch (error) {
      console.error('Failed to verify insurance:', error);
      setError(error.response?.data?.detail || 'Failed to verify insurance');
    } finally {
      setLoading(false);
    }
  };

  const resetPolicyForm = () => {
    setPolicyFormData({
      patient_id: '',
      insurance_plan_id: '',
      policy_number: '',
      group_number: '',
      subscriber_id: '',
      subscriber_name: '',
      relationship_to_subscriber: 'self',
      effective_date: new Date().toISOString().split('T')[0],
      is_primary: true,
      copay_amount: '',
      deductible_amount: ''
    });
  };

  const resetVerificationForm = () => {
    setVerificationFormData({
      patient_id: '',
      insurance_policy_id: '',
      service_codes: ['99213'],
      provider_npi: ''
    });
  };

  const getVerificationStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'verified': 'bg-green-100 text-green-800',
      'denied': 'bg-red-100 text-red-800',
      'expired': 'bg-gray-100 text-gray-800',
      'requires_auth': 'bg-orange-100 text-orange-800',
      'error': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    const recentVerifications = verifications.slice(0, 5);

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{insurancePlans.length}</div>
                <div className="text-sm text-gray-300">Insurance Plans</div>
              </div>
              <div className="text-2xl">🏥</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{insuranceStats.verifiedToday}</div>
                <div className="text-sm text-gray-300">Verified Today</div>
              </div>
              <div className="text-2xl">✅</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{insuranceStats.pendingVerifications}</div>
                <div className="text-sm text-gray-300">Pending Verifications</div>
              </div>
              <div className="text-2xl">⏳</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{insuranceStats.activeAuthorizations}</div>
                <div className="text-sm text-gray-300">Active Prior Auths</div>
              </div>
              <div className="text-2xl">📋</div>
            </div>
          </div>
        </div>

        {/* Recent Verifications */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">🔍 Recent Insurance Verifications</h3>
          {recentVerifications.length === 0 ? (
            <p className="text-gray-400">No recent insurance verifications.</p>
          ) : (
            <div className="space-y-3">
              {recentVerifications.map(verification => (
                <div key={verification.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">
                          Patient ID: {verification.patient_id}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${getVerificationStatusColor(verification.status)}`}>
                          {verification.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Service Codes: {verification.service_codes?.join(', ') || 'N/A'}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        {verification.is_covered !== null && (
                          <span className={verification.is_covered ? 'text-green-400' : 'text-red-400'}>
                            {verification.is_covered ? '✅ Covered' : '❌ Not Covered'}
                          </span>
                        )}
                        {verification.copay_amount && (
                          <span className="ml-4">Copay: ${verification.copay_amount}</span>
                        )}
                      </div>
                    </div>
                    <div className="text-sm text-gray-400">
                      {new Date(verification.verification_date).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Available Insurance Plans */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">🏥 Insurance Plans</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {insurancePlans.slice(0, 6).map(plan => (
              <div key={plan.id} className="bg-white/5 border border-white/10 rounded p-4">
                <div className="text-white font-medium">{plan.insurance_company}</div>
                <div className="text-sm text-gray-300 mt-1">{plan.plan_name}</div>
                <div className="text-sm text-gray-400 mt-1">Type: {plan.plan_type}</div>
                <div className="text-sm text-gray-400 mt-1">Network: {plan.network_type}</div>
                {plan.requires_referrals && (
                  <div className="text-xs text-yellow-400 mt-1">⚠️ Requires Referrals</div>
                )}
                {plan.requires_prior_auth && (
                  <div className="text-xs text-orange-400 mt-1">📋 Prior Auth Required</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderVerificationForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">🔍 Insurance Verification</h3>
            <button
              onClick={() => {
                setShowVerificationForm(false);
                resetVerificationForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleVerifyInsurance} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
              <select
                value={verificationFormData.patient_id}
                onChange={(e) => setVerificationFormData({...verificationFormData, patient_id: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                required
              >
                <option value="">Select Patient</option>
                {patients.map(patient => (
                  <option key={patient.id} value={patient.id}>
                    {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Service Codes (CPT)</label>
              <input
                type="text"
                value={verificationFormData.service_codes.join(', ')}
                onChange={(e) => setVerificationFormData({
                  ...verificationFormData, 
                  service_codes: e.target.value.split(',').map(code => code.trim())
                })}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="99213, 99214, 80048"
                required
              />
              <p className="text-xs text-gray-400 mt-1">Enter CPT codes separated by commas</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Provider NPI (Optional)</label>
              <input
                type="text"
                value={verificationFormData.provider_npi}
                onChange={(e) => setVerificationFormData({...verificationFormData, provider_npi: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="1234567890"
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Verifying...' : 'Verify Insurance'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowVerificationForm(false);
                  resetVerificationForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const renderPolicyForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">🏥 New Insurance Policy</h3>
            <button
              onClick={() => {
                setShowPolicyForm(false);
                resetPolicyForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreatePolicy} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
                <select
                  value={policyFormData.patient_id}
                  onChange={(e) => setPolicyFormData({...policyFormData, patient_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Insurance Plan</label>
                <select
                  value={policyFormData.insurance_plan_id}
                  onChange={(e) => setPolicyFormData({...policyFormData, insurance_plan_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Insurance Plan</option>
                  {insurancePlans.map(plan => (
                    <option key={plan.id} value={plan.id}>
                      {plan.insurance_company} - {plan.plan_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Policy Number</label>
                <input
                  type="text"
                  value={policyFormData.policy_number}
                  onChange={(e) => setPolicyFormData({...policyFormData, policy_number: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Group Number</label>
                <input
                  type="text"
                  value={policyFormData.group_number}
                  onChange={(e) => setPolicyFormData({...policyFormData, group_number: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Subscriber ID</label>
                <input
                  type="text"
                  value={policyFormData.subscriber_id}
                  onChange={(e) => setPolicyFormData({...policyFormData, subscriber_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Subscriber Name</label>
                <input
                  type="text"
                  value={policyFormData.subscriber_name}
                  onChange={(e) => setPolicyFormData({...policyFormData, subscriber_name: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Relationship to Subscriber</label>
                <select
                  value={policyFormData.relationship_to_subscriber}
                  onChange={(e) => setPolicyFormData({...policyFormData, relationship_to_subscriber: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="self">Self</option>
                  <option value="spouse">Spouse</option>
                  <option value="child">Child</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Effective Date</label>
                <input
                  type="date"
                  value={policyFormData.effective_date}
                  onChange={(e) => setPolicyFormData({...policyFormData, effective_date: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Copay Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={policyFormData.copay_amount}
                  onChange={(e) => setPolicyFormData({...policyFormData, copay_amount: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Deductible Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={policyFormData.deductible_amount}
                  onChange={(e) => setPolicyFormData({...policyFormData, deductible_amount: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_primary"
                checked={policyFormData.is_primary}
                onChange={(e) => setPolicyFormData({...policyFormData, is_primary: e.target.checked})}
                className="rounded"
              />
              <label htmlFor="is_primary" className="text-gray-300">Primary Insurance</label>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Policy'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowPolicyForm(false);
                  resetPolicyForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">💳 Insurance Verification</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowPolicyForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            🏥 New Policy
          </button>
          <button
            onClick={() => setShowVerificationForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            🔍 Verify Insurance
          </button>
          <button
            onClick={() => fetchInsuranceData()}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'plans', name: 'Insurance Plans', icon: '🏥' },
            { id: 'policies', name: 'Patient Policies', icon: '📋' },
            { id: 'verifications', name: 'Verifications', icon: '🔍' },
            { id: 'prior-auth', name: 'Prior Authorization', icon: '📄' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeView === tab.id
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

      {/* Content based on active view */}
      {activeView === 'dashboard' && renderDashboard()}
      {activeView === 'plans' && (
        <div className="text-white">Insurance plans management view coming soon...</div>
      )}
      {activeView === 'policies' && (
        <div className="text-white">Patient policies management view coming soon...</div>
      )}
      {activeView === 'verifications' && (
        <div className="text-white">Verifications history view coming soon...</div>
      )}
      {activeView === 'prior-auth' && (
        <div className="text-white">Prior authorization management view coming soon...</div>
      )}

      {/* Forms */}
      {showPolicyForm && renderPolicyForm()}
      {showVerificationForm && renderVerificationForm()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Clinical Templates Management Module
const ClinicalTemplatesModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and form states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, templates, protocols
  const [showTemplateForm, setShowTemplateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  
  // Form data
  const [templateFormData, setTemplateFormData] = useState({
    name: '',
    description: '',
    category: '',
    specialty: '',
    template_type: 'assessment',
    content: '',
    is_active: true
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/clinical-templates`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch clinical templates:', error);
      setError('Failed to fetch clinical templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const url = editingTemplate ? 
        `${API}/clinical-templates/${editingTemplate.id}` : 
        `${API}/clinical-templates`;
      
      const method = editingTemplate ? 'put' : 'post';
      
      const response = await axios[method](url, templateFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (editingTemplate) {
        setTemplates(templates.map(t => t.id === editingTemplate.id ? response.data : t));
        setSuccess('Clinical template updated successfully!');
      } else {
        setTemplates([...templates, response.data]);
        setSuccess('Clinical template created successfully!');
      }
      
      setShowTemplateForm(false);
      setEditingTemplate(null);
      resetTemplateForm();
    } catch (error) {
      console.error('Failed to save clinical template:', error);
      setError(error.response?.data?.detail || 'Failed to save clinical template');
    } finally {
      setLoading(false);
    }
  };

  const handleEditTemplate = (template) => {
    setEditingTemplate(template);
    setTemplateFormData({
      name: template.name,
      description: template.description,
      category: template.category,
      specialty: template.specialty,
      template_type: template.template_type,
      content: template.content,
      is_active: template.is_active
    });
    setShowTemplateForm(true);
  };

  const resetTemplateForm = () => {
    setTemplateFormData({
      name: '',
      description: '',
      category: '',
      specialty: '',
      template_type: 'assessment',
      content: '',
      is_active: true
    });
  };

  const renderDashboard = () => {
    const templatesByType = templates.reduce((acc, template) => {
      acc[template.template_type] = (acc[template.template_type] || 0) + 1;
      return acc;
    }, {});

    const recentTemplates = templates.slice(0, 5);

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{templates.length}</div>
                <div className="text-sm text-gray-300">Total Templates</div>
              </div>
              <div className="text-2xl">📝</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{templatesByType.assessment || 0}</div>
                <div className="text-sm text-gray-300">Assessment Templates</div>
              </div>
              <div className="text-2xl">🔍</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{templatesByType.treatment || 0}</div>
                <div className="text-sm text-gray-300">Treatment Plans</div>
              </div>
              <div className="text-2xl">💊</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{templatesByType.protocol || 0}</div>
                <div className="text-sm text-gray-300">Protocols</div>
              </div>
              <div className="text-2xl">📋</div>
            </div>
          </div>
        </div>

        {/* Recent Templates */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📝 Recent Clinical Templates</h3>
          {recentTemplates.length === 0 ? (
            <p className="text-gray-400">No clinical templates created yet.</p>
          ) : (
            <div className="space-y-3">
              {recentTemplates.map(template => (
                <div key={template.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{template.name}</div>
                        <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded text-xs">
                          {template.template_type}
                        </span>
                        {template.specialty && (
                          <span className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs">
                            {template.specialty}
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-300 mt-1">{template.description}</div>
                      <div className="text-sm text-gray-400 mt-1">Category: {template.category}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditTemplate(template)}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        Edit
                      </button>
                      <div className={`w-2 h-2 rounded-full ${template.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderTemplateForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              {editingTemplate ? '✏️ Edit Clinical Template' : '📝 New Clinical Template'}
            </h3>
            <button
              onClick={() => {
                setShowTemplateForm(false);
                setEditingTemplate(null);
                resetTemplateForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreateTemplate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Template Name</label>
                <input
                  type="text"
                  value={templateFormData.name}
                  onChange={(e) => setTemplateFormData({...templateFormData, name: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Template Type</label>
                <select
                  value={templateFormData.template_type}
                  onChange={(e) => setTemplateFormData({...templateFormData, template_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="assessment">Assessment</option>
                  <option value="treatment">Treatment Plan</option>
                  <option value="protocol">Clinical Protocol</option>
                  <option value="documentation">Documentation</option>
                  <option value="form">Form Template</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                <input
                  type="text"
                  value={templateFormData.category}
                  onChange={(e) => setTemplateFormData({...templateFormData, category: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="e.g., SOAP Notes, Intake Forms"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Specialty</label>
                <input
                  type="text"
                  value={templateFormData.specialty}
                  onChange={(e) => setTemplateFormData({...templateFormData, specialty: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="e.g., Cardiology, Family Medicine"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <input
                type="text"
                value={templateFormData.description}
                onChange={(e) => setTemplateFormData({...templateFormData, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Brief description of the template"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Template Content</label>
              <textarea
                value={templateFormData.content}
                onChange={(e) => setTemplateFormData({...templateFormData, content: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-64"
                placeholder="Enter the template content here..."
                required
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active"
                checked={templateFormData.is_active}
                onChange={(e) => setTemplateFormData({...templateFormData, is_active: e.target.checked})}
                className="rounded"
              />
              <label htmlFor="is_active" className="text-gray-300">Active Template</label>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingTemplate ? 'Update Template' : 'Create Template')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowTemplateForm(false);
                  setEditingTemplate(null);
                  resetTemplateForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">📝 Clinical Templates</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowTemplateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📝 New Template
          </button>
          <button
            onClick={() => fetchTemplates()}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'templates', name: 'All Templates', icon: '📝' },
            { id: 'protocols', name: 'Protocols', icon: '📋' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeView === tab.id
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

      {/* Content based on active view */}
      {activeView === 'dashboard' && renderDashboard()}
      {activeView === 'templates' && (
        <div className="space-y-4">
          {templates.map(template => (
            <div key={template.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-white font-medium">{template.name}</div>
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded text-xs">
                      {template.template_type}
                    </span>
                    {template.specialty && (
                      <span className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs">
                        {template.specialty}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300 mt-1">{template.description}</div>
                  <div className="text-sm text-gray-400 mt-1">Category: {template.category}</div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditTemplate(template)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Edit
                  </button>
                  <div className={`w-2 h-2 rounded-full ${template.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'protocols' && (
        <div className="text-white">Clinical protocols view coming soon...</div>
      )}

      {/* Template Form Modal */}
      {showTemplateForm && renderTemplateForm()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Quality Measures Management Module
const QualityMeasuresModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [measures, setMeasures] = useState([]);
  const [measureResults, setMeasureResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and form states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, measures, reports
  const [showMeasureForm, setShowMeasureForm] = useState(false);
  const [editingMeasure, setEditingMeasure] = useState(null);
  
  // Form data
  const [measureFormData, setMeasureFormData] = useState({
    name: '',
    description: '',
    category: '',
    measure_type: 'outcome',
    calculation_method: '',
    target_value: '',
    target_operator: 'gte',
    is_active: true
  });

  useEffect(() => {
    fetchMeasures();
    fetchMeasureResults();
  }, []);

  const fetchMeasures = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/quality-measures`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setMeasures(response.data);
    } catch (error) {
      console.error('Failed to fetch quality measures:', error);
      setError('Failed to fetch quality measures');
    } finally {
      setLoading(false);
    }
  };

  const fetchMeasureResults = async () => {
    try {
      const response = await axios.get(`${API}/quality-measures/report`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setMeasureResults(response.data);
    } catch (error) {
      console.error('Failed to fetch measure results:', error);
    }
  };

  const handleCalculateMeasures = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await axios.post(`${API}/quality-measures/calculate`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      setSuccess('Quality measures calculated successfully!');
      fetchMeasureResults();
    } catch (error) {
      console.error('Failed to calculate quality measures:', error);
      setError(error.response?.data?.detail || 'Failed to calculate quality measures');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMeasure = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const url = editingMeasure ? 
        `${API}/quality-measures/${editingMeasure.id}` : 
        `${API}/quality-measures`;
      
      const method = editingMeasure ? 'put' : 'post';
      
      const response = await axios[method](url, measureFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (editingMeasure) {
        setMeasures(measures.map(m => m.id === editingMeasure.id ? response.data : m));
        setSuccess('Quality measure updated successfully!');
      } else {
        setMeasures([...measures, response.data]);
        setSuccess('Quality measure created successfully!');
      }
      
      setShowMeasureForm(false);
      setEditingMeasure(null);
      resetMeasureForm();
    } catch (error) {
      console.error('Failed to save quality measure:', error);
      setError(error.response?.data?.detail || 'Failed to save quality measure');
    } finally {
      setLoading(false);
    }
  };

  const handleEditMeasure = (measure) => {
    setEditingMeasure(measure);
    setMeasureFormData({
      name: measure.name,
      description: measure.description,
      category: measure.category,
      measure_type: measure.measure_type,
      calculation_method: measure.calculation_method,
      target_value: measure.target_value,
      target_operator: measure.target_operator,
      is_active: measure.is_active
    });
    setShowMeasureForm(true);
  };

  const resetMeasureForm = () => {
    setMeasureFormData({
      name: '',
      description: '',
      category: '',
      measure_type: 'outcome',
      calculation_method: '',
      target_value: '',
      target_operator: 'gte',
      is_active: true
    });
  };

  const getMeasureStatusColor = (status) => {
    const colors = {
      'met': 'bg-green-100 text-green-800',
      'not_met': 'bg-red-100 text-red-800',
      'improving': 'bg-yellow-100 text-yellow-800',
      'declining': 'bg-orange-100 text-orange-800',
      'stable': 'bg-blue-100 text-blue-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    const measuresByType = measures.reduce((acc, measure) => {
      acc[measure.measure_type] = (acc[measure.measure_type] || 0) + 1;
      return acc;
    }, {});

    const recentResults = measureResults.slice(0, 5);

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{measures.length}</div>
                <div className="text-sm text-gray-300">Total Measures</div>
              </div>
              <div className="text-2xl">📈</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{measuresByType.outcome || 0}</div>
                <div className="text-sm text-gray-300">Outcome Measures</div>
              </div>
              <div className="text-2xl">🎯</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{measuresByType.process || 0}</div>
                <div className="text-sm text-gray-300">Process Measures</div>
              </div>
              <div className="text-2xl">⚙️</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{measuresByType.structure || 0}</div>
                <div className="text-sm text-gray-300">Structure Measures</div>
              </div>
              <div className="text-2xl">🏗️</div>
            </div>
          </div>
        </div>

        {/* Recent Results */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">📊 Recent Quality Measure Results</h3>
            <button
              onClick={handleCalculateMeasures}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
            >
              🔄 Calculate Measures
            </button>
          </div>
          {recentResults.length === 0 ? (
            <p className="text-gray-400">No quality measure results available. Click "Calculate Measures" to generate results.</p>
          ) : (
            <div className="space-y-3">
              {recentResults.map(result => (
                <div key={result.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{result.measure_name}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getMeasureStatusColor(result.status)}`}>
                          {result.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Current Value: {result.current_value} | Target: {result.target_value}
                      </div>
                      {result.improvement_percentage && (
                        <div className="text-sm text-gray-400 mt-1">
                          Improvement: {result.improvement_percentage}%
                        </div>
                      )}
                    </div>
                    <div className="text-sm text-gray-400">
                      {new Date(result.calculation_date).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Measures */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📈 Active Quality Measures</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {measures.filter(m => m.is_active).slice(0, 6).map(measure => (
              <div key={measure.id} className="bg-white/5 border border-white/10 rounded p-4">
                <div className="text-white font-medium">{measure.name}</div>
                <div className="text-sm text-gray-300 mt-1">{measure.description}</div>
                <div className="text-sm text-gray-400 mt-1">Type: {measure.measure_type}</div>
                <div className="text-sm text-gray-400 mt-1">Category: {measure.category}</div>
                {measure.target_value && (
                  <div className="text-xs text-blue-400 mt-1">Target: {measure.target_operator} {measure.target_value}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderMeasureForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              {editingMeasure ? '✏️ Edit Quality Measure' : '📈 New Quality Measure'}
            </h3>
            <button
              onClick={() => {
                setShowMeasureForm(false);
                setEditingMeasure(null);
                resetMeasureForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreateMeasure} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Measure Name</label>
              <input
                type="text"
                value={measureFormData.name}
                onChange={(e) => setMeasureFormData({...measureFormData, name: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <textarea
                value={measureFormData.description}
                onChange={(e) => setMeasureFormData({...measureFormData, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                placeholder="Describe what this measure evaluates"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Measure Type</label>
                <select
                  value={measureFormData.measure_type}
                  onChange={(e) => setMeasureFormData({...measureFormData, measure_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="outcome">Outcome</option>
                  <option value="process">Process</option>
                  <option value="structure">Structure</option>
                  <option value="patient_experience">Patient Experience</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                <input
                  type="text"
                  value={measureFormData.category}
                  onChange={(e) => setMeasureFormData({...measureFormData, category: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="e.g., Diabetes Care, Preventive Care"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Calculation Method</label>
              <textarea
                value={measureFormData.calculation_method}
                onChange={(e) => setMeasureFormData({...measureFormData, calculation_method: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                placeholder="Describe how this measure is calculated"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Target Operator</label>
                <select
                  value={measureFormData.target_operator}
                  onChange={(e) => setMeasureFormData({...measureFormData, target_operator: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="gte">Greater than or equal (≥)</option>
                  <option value="lte">Less than or equal (≤)</option>
                  <option value="eq">Equal to (=)</option>
                  <option value="gt">Greater than (&gt;)</option>
                  <option value="lt">Less than (&lt;)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Target Value</label>
                <input
                  type="text"
                  value={measureFormData.target_value}
                  onChange={(e) => setMeasureFormData({...measureFormData, target_value: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="e.g., 85%, 120, 7.0"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_active_measure"
                checked={measureFormData.is_active}
                onChange={(e) => setMeasureFormData({...measureFormData, is_active: e.target.checked})}
                className="rounded"
              />
              <label htmlFor="is_active_measure" className="text-gray-300">Active Measure</label>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingMeasure ? 'Update Measure' : 'Create Measure')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowMeasureForm(false);
                  setEditingMeasure(null);
                  resetMeasureForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">📈 Quality Measures</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowMeasureForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📈 New Measure
          </button>
          <button
            onClick={() => fetchMeasures()}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'measures', name: 'All Measures', icon: '📈' },
            { id: 'reports', name: 'Reports', icon: '📋' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeView === tab.id
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

      {/* Content based on active view */}
      {activeView === 'dashboard' && renderDashboard()}
      {activeView === 'measures' && (
        <div className="space-y-4">
          {measures.map(measure => (
            <div key={measure.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-white font-medium">{measure.name}</div>
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded text-xs">
                      {measure.measure_type}
                    </span>
                    {measure.category && (
                      <span className="px-2 py-1 bg-purple-600/20 text-purple-300 rounded text-xs">
                        {measure.category}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300 mt-1">{measure.description}</div>
                  <div className="text-sm text-gray-400 mt-1">
                    Target: {measure.target_operator} {measure.target_value}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditMeasure(measure)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Edit
                  </button>
                  <div className={`w-2 h-2 rounded-full ${measure.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'reports' && (
        <div className="text-white">Quality measure reports view coming soon...</div>
      )}

      {/* Measure Form Modal */}
      {showMeasureForm && renderMeasureForm()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

// Document Management Module
const DocumentManagementModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and form states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, documents, upload
  const [showDocumentForm, setShowDocumentForm] = useState(false);
  const [editingDocument, setEditingDocument] = useState(null);
  
  // Form data
  const [documentFormData, setDocumentFormData] = useState({
    title: '',
    description: '',
    category: '',
    patient_id: '',
    document_type: 'clinical_note',
    content: '',
    is_confidential: false
  });

  const [uploadFormData, setUploadFormData] = useState({
    title: '',
    category: '',
    patient_id: '',
    description: ''
  });

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/documents`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setDocuments(response.data);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      setError('Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateDocument = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const url = editingDocument ? 
        `${API}/documents/${editingDocument.id}` : 
        `${API}/documents`;
      
      const method = editingDocument ? 'put' : 'post';
      
      const response = await axios[method](url, documentFormData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      if (editingDocument) {
        setDocuments(documents.map(d => d.id === editingDocument.id ? response.data : d));
        setSuccess('Document updated successfully!');
      } else {
        setDocuments([...documents, response.data]);
        setSuccess('Document created successfully!');
      }
      
      setShowDocumentForm(false);
      setEditingDocument(null);
      resetDocumentForm();
    } catch (error) {
      console.error('Failed to save document:', error);
      setError(error.response?.data?.detail || 'Failed to save document');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDocument = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      // Create a document record first
      const documentData = {
        ...uploadFormData,
        document_type: 'uploaded_file',
        content: 'File uploaded',
        file_path: `/uploads/documents/${uploadFormData.title.replace(/\s+/g, '_')}.pdf`
      };

      const response = await axios.post(`${API}/documents/upload`, documentData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });

      setDocuments([...documents, response.data]);
      setSuccess('Document uploaded successfully!');
      resetUploadForm();
      setActiveView('documents');
    } catch (error) {
      console.error('Failed to upload document:', error);
      setError(error.response?.data?.detail || 'Failed to upload document');
    } finally {
      setLoading(false);
    }
  };

  const handleEditDocument = (document) => {
    setEditingDocument(document);
    setDocumentFormData({
      title: document.title,
      description: document.description,
      category: document.category,
      patient_id: document.patient_id || '',
      document_type: document.document_type,
      content: document.content,
      is_confidential: document.is_confidential
    });
    setShowDocumentForm(true);
  };

  const handleUpdateDocumentStatus = async (documentId, newStatus) => {
    try {
      setLoading(true);
      const response = await axios.put(`${API}/documents/${documentId}/status`, 
        { status: newStatus }, 
        { headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } }
      );
      
      setDocuments(documents.map(d => d.id === documentId ? response.data : d));
      setSuccess(`Document status updated to ${newStatus}!`);
    } catch (error) {
      console.error('Failed to update document status:', error);
      setError(error.response?.data?.detail || 'Failed to update document status');
    } finally {
      setLoading(false);
    }
  };

  const resetDocumentForm = () => {
    setDocumentFormData({
      title: '',
      description: '',
      category: '',
      patient_id: '',
      document_type: 'clinical_note',
      content: '',
      is_confidential: false
    });
  };

  const resetUploadForm = () => {
    setUploadFormData({
      title: '',
      category: '',
      patient_id: '',
      description: ''
    });
  };

  const getDocumentStatusColor = (status) => {
    const colors = {
      'draft': 'bg-yellow-100 text-yellow-800',
      'active': 'bg-green-100 text-green-800',
      'archived': 'bg-gray-100 text-gray-800',
      'pending_approval': 'bg-blue-100 text-blue-800',
      'approved': 'bg-green-100 text-green-800',
      'rejected': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    const documentsByType = documents.reduce((acc, doc) => {
      acc[doc.document_type] = (acc[doc.document_type] || 0) + 1;
      return acc;
    }, {});

    const recentDocuments = documents.slice(0, 5);

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documents.length}</div>
                <div className="text-sm text-gray-300">Total Documents</div>
              </div>
              <div className="text-2xl">📄</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documentsByType.clinical_note || 0}</div>
                <div className="text-sm text-gray-300">Clinical Notes</div>
              </div>
              <div className="text-2xl">📝</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documentsByType.uploaded_file || 0}</div>
                <div className="text-sm text-gray-300">Uploaded Files</div>
              </div>
              <div className="text-2xl">📎</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documents.filter(d => d.is_confidential).length}</div>
                <div className="text-sm text-gray-300">Confidential</div>
              </div>
              <div className="text-2xl">🔒</div>
            </div>
          </div>
        </div>

        {/* Recent Documents */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📄 Recent Documents</h3>
          {recentDocuments.length === 0 ? (
            <p className="text-gray-400">No documents available.</p>
          ) : (
            <div className="space-y-3">
              {recentDocuments.map(document => (
                <div key={document.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{document.title}</div>
                        <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded text-xs">
                          {document.document_type}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${getDocumentStatusColor(document.status)}`}>
                          {document.status}
                        </span>
                        {document.is_confidential && (
                          <span className="px-2 py-1 bg-red-600/20 text-red-300 rounded text-xs">
                            🔒 Confidential
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-300 mt-1">{document.description}</div>
                      <div className="text-sm text-gray-400 mt-1">Category: {document.category}</div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditDocument(document)}
                        className="text-blue-400 hover:text-blue-300 text-sm"
                      >
                        Edit
                      </button>
                      <div className="text-sm text-gray-400">
                        {new Date(document.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDocumentForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              {editingDocument ? '✏️ Edit Document' : '📄 New Document'}
            </h3>
            <button
              onClick={() => {
                setShowDocumentForm(false);
                setEditingDocument(null);
                resetDocumentForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreateDocument} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Document Title</label>
                <input
                  type="text"
                  value={documentFormData.title}
                  onChange={(e) => setDocumentFormData({...documentFormData, title: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Document Type</label>
                <select
                  value={documentFormData.document_type}
                  onChange={(e) => setDocumentFormData({...documentFormData, document_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="clinical_note">Clinical Note</option>
                  <option value="lab_result">Lab Result</option>
                  <option value="imaging_report">Imaging Report</option>
                  <option value="consultation_report">Consultation Report</option>
                  <option value="discharge_summary">Discharge Summary</option>
                  <option value="uploaded_file">Uploaded File</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                <input
                  type="text"
                  value={documentFormData.category}
                  onChange={(e) => setDocumentFormData({...documentFormData, category: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="e.g., Cardiology, Lab Reports"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Patient ID (Optional)</label>
                <input
                  type="text"
                  value={documentFormData.patient_id}
                  onChange={(e) => setDocumentFormData({...documentFormData, patient_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="Link to patient record"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <input
                type="text"
                value={documentFormData.description}
                onChange={(e) => setDocumentFormData({...documentFormData, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Brief description of the document"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Document Content</label>
              <textarea
                value={documentFormData.content}
                onChange={(e) => setDocumentFormData({...documentFormData, content: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-64"
                placeholder="Enter the document content here..."
                required
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="is_confidential"
                checked={documentFormData.is_confidential}
                onChange={(e) => setDocumentFormData({...documentFormData, is_confidential: e.target.checked})}
                className="rounded"
              />
              <label htmlFor="is_confidential" className="text-gray-300">Mark as Confidential</label>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingDocument ? 'Update Document' : 'Create Document')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowDocumentForm(false);
                  setEditingDocument(null);
                  resetDocumentForm();
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const renderUploadForm = () => {
    return (
      <div className="bg-white/5 border border-white/10 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">📎 Upload Document</h3>
        
        <form onSubmit={handleUploadDocument} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Document Title</label>
              <input
                type="text"
                value={uploadFormData.title}
                onChange={(e) => setUploadFormData({...uploadFormData, title: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
              <input
                type="text"
                value={uploadFormData.category}
                onChange={(e) => setUploadFormData({...uploadFormData, category: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="e.g., Lab Reports, Imaging"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Patient ID (Optional)</label>
            <input
              type="text"
              value={uploadFormData.patient_id}
              onChange={(e) => setUploadFormData({...uploadFormData, patient_id: e.target.value})}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              placeholder="Link to patient record"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
            <textarea
              value={uploadFormData.description}
              onChange={(e) => setUploadFormData({...uploadFormData, description: e.target.value})}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
              placeholder="Brief description of the document"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">File Upload</label>
            <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center">
              <div className="text-gray-400 mb-2">📎 Click to upload or drag and drop</div>
              <div className="text-sm text-gray-500">PDF, DOC, DOCX, JPG, PNG (max 10MB)</div>
              <input
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              />
            </div>
          </div>

          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
            >
              {loading ? 'Uploading...' : 'Upload Document'}
            </button>
            <button
              type="button"
              onClick={() => resetUploadForm()}
              className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded"
            >
              Clear Form
            </button>
          </div>
        </form>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">📄 Document Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowDocumentForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📄 New Document
          </button>
          <button
            onClick={() => fetchDocuments()}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            🔄 Refresh
          </button>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="bg-green-500/20 border border-green-400/50 rounded-lg p-4 mb-6">
          <p className="text-green-300">✅ {success}</p>
        </div>
      )}
      
      {error && (
        <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-4 mb-6">
          <p className="text-red-300">❌ {typeof error === 'object' ? JSON.stringify(error) : error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'documents', name: 'All Documents', icon: '📄' },
            { id: 'upload', name: 'Upload', icon: '📎' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                activeView === tab.id
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

      {/* Content based on active view */}
      {activeView === 'dashboard' && renderDashboard()}
      {activeView === 'documents' && (
        <div className="space-y-4">
          {documents.map(document => (
            <div key={document.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-white font-medium">{document.title}</div>
                    <span className="px-2 py-1 bg-blue-600/20 text-blue-300 rounded text-xs">
                      {document.document_type}
                    </span>
                    <span className={`px-2 py-1 rounded text-xs ${getDocumentStatusColor(document.status)}`}>
                      {document.status}
                    </span>
                    {document.is_confidential && (
                      <span className="px-2 py-1 bg-red-600/20 text-red-300 rounded text-xs">
                        🔒 Confidential
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300 mt-1">{document.description}</div>
                  <div className="text-sm text-gray-400 mt-1">Category: {document.category}</div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditDocument(document)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Edit
                  </button>
                  <select
                    value={document.status}
                    onChange={(e) => handleUpdateDocumentStatus(document.id, e.target.value)}
                    className="bg-gray-600 text-white px-2 py-1 rounded text-xs"
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="archived">Archived</option>
                    <option value="pending_approval">Pending Approval</option>
                    <option value="approved">Approved</option>
                  </select>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'upload' && renderUploadForm()}

      {/* Document Form Modal */}
      {showDocumentForm && renderDocumentForm()}
      
      {/* Loading */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-40">
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-white">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;