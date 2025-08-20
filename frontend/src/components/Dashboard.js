import React, { useState, useEffect } from "react";
import axios from "axios";
import { useAuth } from "../contexts/AuthContext";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "/api";
const API = `${BACKEND_URL}`;

const Dashboard = ({ setActiveModule }) => {
  const { user, logout, hasPermission } = useAuth();
  const [quickStats, setQuickStats] = useState({});

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const [erxResponse, dailyResponse, queueResponse, paymentsResponse] = await Promise.allSettled([
        axios.get(`${API}/dashboard/erx-patients`),
        axios.get(`${API}/dashboard/daily-log`),
        axios.get(`${API}/dashboard/patient-queue`),
        axios.get(`${API}/dashboard/pending-payments`)
      ]);

      setQuickStats({
        erx_patients_today: erxResponse.value?.data?.length || 0,
        daily_revenue: dailyResponse.value?.data?.total_revenue || 0,
        patients_in_queue: queueResponse.value?.data?.length || 0,
        pending_amount: paymentsResponse.value?.data?.total_overdue || 0
      });
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      setQuickStats({
        erx_patients_today: 0,
        daily_revenue: 0,
        patients_in_queue: 0,
        pending_amount: 0
      });
    }
  };

  const handleCardClick = (moduleKey) => {
    setActiveModule(moduleKey);
  };

  const modules = [
    { name: "Patients/EHR", key: "patients", icon: "👥", color: "bg-blue-500", permission: "patients:read", description: "Patient records & encounters" },
    { name: "Smart Forms", key: "forms", icon: "📋", color: "bg-green-500", permission: "forms:read", description: "FHIR-compliant forms" },
    { name: "Inventory", key: "inventory", icon: "📦", color: "bg-orange-500", permission: "inventory:read", description: "Medical supplies tracking" },
    { name: "Invoices", key: "invoices", icon: "🧾", color: "bg-purple-500", permission: "invoices:read", description: "Billing & payments" },
    { name: "Lab Orders", key: "lab-orders", icon: "🧪", color: "bg-teal-600", permission: "lab:read", description: "Laboratory integration" },
    { name: "Insurance", key: "insurance", icon: "🏥", color: "bg-cyan-600", permission: "insurance:read", description: "Verification & prior auth" },
    { name: "Employees", key: "employees", icon: "👨‍⚕️", color: "bg-indigo-500", permission: "employees:read", description: "Staff management" },
    { name: "Finance", key: "finance", icon: "💰", color: "bg-green-600", permission: "finance:read", description: "Financial reporting" },
    { name: "Scheduling", key: "scheduling", icon: "📅", color: "bg-blue-600", permission: "scheduling:read", description: "Appointment management" },
    { name: "Communications", key: "communications", icon: "📨", color: "bg-teal-500", permission: "communications:read", description: "Patient messaging" },
    { name: "Referrals", key: "referrals", icon: "🔄", color: "bg-red-500", permission: "referrals:read", description: "Provider network" },
    { name: "Clinical Templates", key: "clinical-templates", icon: "📋", color: "bg-green-700", permission: "templates:read", description: "Disease protocols" },
    { name: "Quality Measures", key: "quality-measures", icon: "📊", color: "bg-blue-700", permission: "quality:read", description: "Performance analytics" },
    { name: "Patient Portal", key: "patient-portal-mgmt", icon: "🚪", color: "bg-purple-600", permission: "portal:read", description: "Portal management" },
    { name: "Documents", key: "documents", icon: "📄", color: "bg-gray-600", permission: "documents:read", description: "Document workflows" },
    { name: "Telehealth", key: "telehealth", icon: "📹", color: "bg-pink-600", permission: "telehealth:read", description: "Virtual consultations" },
    { name: "System Settings", key: "system-settings", icon: "⚙️", color: "bg-slate-700", permission: "admin", description: "System configuration" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-400 to-purple-500 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-xl">🏥</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">ClinicHub Dashboard</h1>
                <p className="text-blue-200 text-sm">FHIR-Compliant Practice Management</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => window.open('/patient-portal', '_blank')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
              >
                Patient Portal
              </button>
              <div className="text-right">
                <p className="text-white font-semibold">
                  {user?.first_name} {user?.last_name}
                </p>
                <div className="flex items-center space-x-2">
                  <p className="text-blue-200 text-sm capitalize">{user?.role}</p>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    user?.auth_source === 'synology' 
                      ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                      : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                  }`}>
                    {user?.auth_source === 'synology' ? '🔐 Synology' : '🔑 Local'}
                  </span>
                </div>
              </div>
              <button
                onClick={logout}
                className="bg-red-500/20 hover:bg-red-500/30 text-red-200 hover:text-white px-4 py-2 rounded-lg transition-colors duration-200 border border-red-500/30"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Quick Stats - Clinic Operations */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div 
            onClick={() => handleCardClick('erx-patients')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm">eRx Dashboard</p>
                <p className="text-3xl font-bold text-white">{quickStats.erx_patients_today || 0}</p>
                <p className="text-purple-300 text-xs">Patients Today</p>
              </div>
              <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">💊</span>
              </div>
            </div>
          </div>

          <div 
            onClick={() => handleCardClick('daily-log')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm">Daily Revenue</p>
                <p className="text-3xl font-bold text-white">${quickStats.daily_revenue?.toFixed(0) || 0}</p>
                <p className="text-green-300 text-xs">Today's Total</p>
              </div>
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">📊</span>
              </div>
            </div>
          </div>

          <div 
            onClick={() => handleCardClick('patient-queue')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm">Patient Queue</p>
                <p className="text-3xl font-bold text-white">{quickStats.patients_in_queue || 0}</p>
                <p className="text-blue-300 text-xs">In Clinic Now</p>
              </div>
              <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">🏥</span>
              </div>
            </div>
          </div>

          <div 
            onClick={() => handleCardClick('pending-payments')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-200 text-sm">Pending</p>
                <p className="text-3xl font-bold text-white">${quickStats.pending_amount?.toFixed(0) || 0}</p>
                <p className="text-red-300 text-xs">Outstanding</p>
              </div>
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">💳</span>
              </div>
            </div>
          </div>
        </div>

        {/* Module Cards */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-white mb-6">Practice Management Modules</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {modules.filter(module => hasPermission(module.permission)).map((module) => (
              <div
                key={module.key}
                onClick={() => handleCardClick(module.key)}
                className={`${module.color} rounded-xl p-6 cursor-pointer hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 hover:scale-105`}
              >
                <div className="flex items-start justify-between mb-4">
                  <span className="text-4xl">{module.icon}</span>
                  <div className="bg-white/20 w-3 h-3 rounded-full"></div>
                </div>
                <h3 className="text-white font-bold text-lg mb-1">{module.name}</h3>
                <p className="text-white/80 text-sm">{module.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-blue-200 text-sm">Backend Services</p>
              <p className="text-green-400 font-medium">✅ Operational</p>
            </div>
            <div>
              <p className="text-blue-200 text-sm">Database</p>
              <p className="text-green-400 font-medium">✅ Connected</p>
            </div>
            <div>
              <p className="text-blue-200 text-sm">eRx System</p>
              <p className="text-green-400 font-medium">✅ FHIR Compliant</p>
            </div>
            <div>
              <p className="text-blue-200 text-sm">User Permissions</p>
              <p className="text-white font-medium">{user?.permissions?.length || 0} permissions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;