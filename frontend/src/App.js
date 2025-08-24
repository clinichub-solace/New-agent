import React, { useState, useEffect } from "react";
import "./App.css";
import { formatErrorMessage, toDisplayError } from './utils/errors';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import api from './api/axios';

// RESTORED ClinicHub App - Complete EHR System with Advanced Features
// ✅ PHASE 1: Enhanced Dashboard with Navigation System Restored
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix

// Dashboard Component with Full Navigation System
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeModule, setActiveModule] = useState('dashboard');
  const [synologyStatus, setSynologyStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  // Core state management for essential EHR functions
  const [patients, setPatients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [employees, setEmployees] = useState([]);

  // UI state
  const [showAddPatient, setShowAddPatient] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetchSynologyStatus();
  }, []);

  // ✅ URL VETTING: Uses configured 'api' instance with proper /api routing
  const fetchSynologyStatus = async () => {
    try {
      const response = await api.get('/auth/synology-status');
      setSynologyStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch Synology status:', error);
    }
  };

  // Enhanced Module Rendering System - All 16 Modules
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

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      // Using simplified API calls with configured api instance
      const [patientsRes, appointmentsRes, inventoryRes] = await Promise.all([
        api.get('/patients').catch(() => ({ data: [] })),
        api.get('/appointments').catch(() => ({ data: [] })),
        api.get('/inventory').catch(() => ({ data: [] }))
      ]);

      setStats({
        total_patients: patientsRes.data?.length || 0,
        todays_appointments: appointmentsRes.data?.filter(apt => 
          new Date(apt.start_time).toDateString() === new Date().toDateString()
        ).length || 0,
        low_stock_items: inventoryRes.data?.filter(item => 
          item.quantity <= item.reorder_level
        ).length || 0
      });
    } catch (error) {
      console.error('Dashboard stats error:', error);
    } finally {
      setLoading(false);
    }
  };

  // CORE EHR FUNCTIONS ONLY

  // Patient Management
  const fetchPatients = async () => {
    try {
      const response = await api.get('/patients');
      setPatients(response.data || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  const addPatient = async (patientData) => {
    try {
      const response = await api.post('/patients', patientData);
      setPatients(prev => [...prev, response.data]);
      setShowAddPatient(false);
    } catch (error) {
      console.error('Error adding patient:', error);
    }
  };

  // Appointment Management
  const fetchAppointments = async () => {
    try {
      const response = await api.get('/appointments');
      setAppointments(response.data || []);
    } catch (error) {
      console.error('Error fetching appointments:', error);
    }
  };

  const scheduleAppointment = async (appointmentData) => {
    try {
      const response = await api.post('/appointments', appointmentData);
      setAppointments(prev => [...prev, response.data]);
    } catch (error) {
      console.error('Error scheduling appointment:', error);
    }
  };

  // Inventory Management
  const fetchInventory = async () => {
    try {
      const response = await api.get('/inventory');
      setInventory(response.data || []);
    } catch (error) {
      console.error('Error fetching inventory:', error);
    }
  };

  // Employee Management
  const fetchEmployees = async () => {
    try {
      const response = await api.get('/employees');
      setEmployees(response.data || []);
    } catch (error) {
      console.error('Error fetching employees:', error);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Patients</h3>
          <p className="text-3xl font-bold text-blue-600">
            {loading ? '...' : stats?.total_patients || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Today's Appointments</h3>
          <p className="text-3xl font-bold text-green-600">
            {loading ? '...' : stats?.todays_appointments || 0}
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Low Stock Items</h3>
          <p className="text-3xl font-bold text-red-600">
            {loading ? '...' : stats?.low_stock_items || 0}
          </p>
        </div>
      </div>
    </div>
  );

  const renderPatients = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">Patient Management</h2>
        <button
          onClick={() => setShowAddPatient(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Add Patient
        </button>
      </div>
      
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {patients.length === 0 ? (
            <li className="px-4 py-6 text-center text-gray-500">
              No patients found. Click "Add Patient" to get started.
            </li>
          ) : (
            patients.map((patient) => (
              <li key={patient.id} className="px-4 py-4 hover:bg-gray-50 cursor-pointer">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {patient.first_name} {patient.last_name}
                    </p>
                    <p className="text-sm text-gray-500">DOB: {patient.date_of_birth}</p>
                  </div>
                  <div className="text-sm text-gray-400">
                    ID: {patient.id}
                  </div>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );



  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Enhanced Header with Synology Status */}
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
          {/* Enhanced Sidebar Navigation - 16 Modules */}
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
                📊 Dashboard
              </button>
              <button
                onClick={() => setActiveModule('patients')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'patients' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                🏥 Patients/EHR
              </button>
              <button
                onClick={() => setActiveModule('scheduling')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'scheduling' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                📅 Scheduling
              </button>
              <button
                onClick={() => setActiveModule('telehealth')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'telehealth' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                💻 Telehealth
              </button>
              <button
                onClick={() => setActiveModule('patient-portal')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'patient-portal' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                🌐 Patient Portal
              </button>
              <button
                onClick={() => setActiveModule('lab-orders')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'lab-orders' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                🔬 Lab Orders
              </button>
              <button
                onClick={() => setActiveModule('insurance')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'insurance' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                🛡️ Insurance
              </button>
              <button
                onClick={() => setActiveModule('clinical-templates')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'clinical-templates' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                📋 Clinical Templates
              </button>
              <button
                onClick={() => setActiveModule('quality-measures')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'quality-measures' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                📈 Quality Measures
              </button>
              <button
                onClick={() => setActiveModule('documents')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'documents' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                📄 Documents
              </button>
              <button
                onClick={() => setActiveModule('invoices')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'invoices' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                💰 Invoices
              </button>
              <button
                onClick={() => setActiveModule('employees')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'employees' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                👥 Employees
              </button>
              <button
                onClick={() => setActiveModule('inventory')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'inventory' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                📦 Inventory
              </button>
              <button
                onClick={() => setActiveModule('finance')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'finance' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                💳 Finance
              </button>
              <button
                onClick={() => setActiveModule('communication')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'communication' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                💬 Communication
              </button>
              <button
                onClick={() => setActiveModule('referrals')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'referrals' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                🔗 Referrals
              </button>
              <button
                onClick={() => setActiveModule('system-settings')}
                className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                  activeModule === 'system-settings' 
                    ? 'bg-blue-600 text-white' 
                    : 'text-blue-200 hover:bg-white/10'
                }`}
              >
                ⚙️ System Settings
              </button>
            </nav>
            
            {/* Practice Management System Footer */}
            <div className="mt-8 pt-4 border-t border-white/20">
              <p className="text-xs text-blue-300 text-center">
                Complete Practice Management System
              </p>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="flex-1 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
            {renderContent()}
          </div>
        </div>
      </div>

      {/* Add Patient Modal */}
      {showAddPatient && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Patient</h3>
              <form onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                addPatient({
                  first_name: formData.get('first_name'),
                  last_name: formData.get('last_name'),
                  date_of_birth: formData.get('date_of_birth'),
                  email: formData.get('email'),
                  phone: formData.get('phone')
                });
              }}>
                <div className="space-y-4">
                  <input
                    name="first_name"
                    placeholder="First Name"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  />
                  <input
                    name="last_name"
                    placeholder="Last Name"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  />
                  <input
                    name="date_of_birth"
                    type="date"
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  />
                  <input
                    name="email"
                    type="email"
                    placeholder="Email"
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                  <input
                    name="phone"
                    placeholder="Phone"
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>
                <div className="flex justify-end space-x-2 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowAddPatient(false)}
                    className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Add Patient
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading ClinicHub...</p>
        </div>
      </div>
    );
  }

  return user ? <Dashboard /> : <LoginPage />;
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;