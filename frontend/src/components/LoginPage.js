import React, { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";

// Dynamic backend URL detection for deployment flexibility
const getBackendURL = () => {
  // Always use environment variable if set
  if (process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL !== '') {
    return process.env.REACT_APP_BACKEND_URL;
  }
  
  // Fallback to same domain as frontend
  return window.location.origin;
};

const BACKEND_URL = getBackendURL();
const API = `${BACKEND_URL}/api`;

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [synologyStatus, setSynologyStatus] = useState(null);
  const { login } = useAuth();

  // Check Synology integration status on component mount
  useEffect(() => {
    const checkSynologyStatus = async () => {
      try {
        const response = await axios.get(`${API}/auth/synology-status`);
        setSynologyStatus(response.data);
      } catch (error) {
        console.error('Error checking Synology status:', error);
      }
    };
    
    checkSynologyStatus();
  }, []);

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

  const initializeAdmin = async () => {
    try {
      const response = await axios.post(`${API}/auth/init-admin`);
      alert(`Admin user created! Username: admin, Password: admin123\n${response.data.warning}`);
    } catch (error) {
      if (error.response?.status === 400) {
        alert('Admin user already exists');
      } else {
        alert('Error creating admin user');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/5 to-transparent opacity-20"></div>
      
      <div className="relative w-full max-w-md">
        {/* Login Card */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-400 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-2xl">🏥</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">ClinicHub</h1>
            <p className="text-blue-200 text-sm">FHIR-Compliant Practice Management</p>
            <p className="text-blue-300 text-xs mt-2 italic">Guided by Solace. Powered by purpose.</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-2">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                placeholder="Enter your username"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-blue-200 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                <p className="text-red-200 text-sm">{error}</p>
              </div>
            )}

            {/* Synology Integration Status */}
            {synologyStatus && (
              <div className={`rounded-lg p-3 ${
                synologyStatus.synology_enabled 
                  ? 'bg-green-500/20 border border-green-500/50' 
                  : 'bg-blue-500/20 border border-blue-500/50'
              }`}>
                <div className="flex items-center space-x-2">
                  <div className={`w-2 h-2 rounded-full ${
                    synologyStatus.synology_enabled ? 'bg-green-400' : 'bg-blue-400'
                  }`}></div>
                  <p className={`text-sm ${
                    synologyStatus.synology_enabled ? 'text-green-200' : 'text-blue-200'
                  }`}>
                    {synologyStatus.synology_enabled 
                      ? '🔐 Synology SSO Enabled' 
                      : '🔑 Local Authentication Mode'
                    }
                  </p>
                </div>
                {synologyStatus.synology_enabled && (
                  <p className="text-xs text-green-300 mt-1">
                    Connected to: {synologyStatus.synology_url?.replace(/^https?:\/\//, '')}
                  </p>
                )}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-300 hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Signing In...
                </div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Admin Initialization */}
          <div className="mt-6 pt-6 border-t border-white/20">
            <button
              onClick={initializeAdmin}
              className="w-full text-blue-300 hover:text-blue-200 text-sm transition duration-300"
            >
              First time setup? Initialize Admin User
            </button>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-blue-300 text-xs">
              © 2024 ClinicHub. Secure Healthcare Management.
            </p>
          </div>
        </div>

        {/* Role-based Access Info */}
        <div className="mt-6 bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10">
          <h3 className="text-white text-sm font-semibold mb-2">Role-Based Access</h3>
          <div className="text-blue-200 text-xs space-y-1">
            <p><strong>Admin:</strong> Full system access</p>
            <p><strong>Doctor:</strong> Patients, EHR, Forms, Reports</p>
            <p><strong>Nurse:</strong> Patients, EHR, Forms, Inventory</p>
            <p><strong>Manager:</strong> Employees, Finance, Reports</p>
            <p><strong>Receptionist:</strong> Patients, Invoices, Basic EHR</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;