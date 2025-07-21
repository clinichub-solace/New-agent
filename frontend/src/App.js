import React, { useState } from "react";
import "./App.css";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import LoginPage from "./components/LoginPage";
import Dashboard from "./components/Dashboard";
import AppHeader from "./components/AppHeader";
import ProtectedRoute from "./components/ProtectedRoute";
import ERxModule from "./components/eRxModule";

// Import Module Components
import PatientsModule from "./components/modules/PatientsModule";
import SchedulingModule from "./components/modules/SchedulingModule";

// Loading Component
const LoadingScreen = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
    <div className="text-white text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
      <p>Loading ClinicHub...</p>
    </div>
  </div>
);

// Main App Component with Module Routing
function AppContent() {
  const { user, loading } = useAuth();
  const [activeModule, setActiveModule] = useState('dashboard');

  if (loading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <LoginPage />;
  }

  // Module Routing
  const renderModule = () => {
    switch (activeModule) {
      case 'patients':
        return (
          <ProtectedRoute permission="patients:read">
            <AppHeader setActiveModule={setActiveModule}>
              <PatientsModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'scheduling':
        return (
          <ProtectedRoute permission="scheduling:read">
            <AppHeader setActiveModule={setActiveModule}>
              <SchedulingModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'erx':
        return (
          <ProtectedRoute permission="patients:read">
            <AppHeader setActiveModule={setActiveModule}>
              <ERxModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );

      // Placeholder modules - will be implemented next
      case 'forms':
        return (
          <ProtectedRoute permission="forms:read">
            <AppHeader setActiveModule={setActiveModule}>
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">SmartForms Module</h2>
                <p className="text-blue-200">FHIR-compliant form builder coming soon...</p>
              </div>
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'inventory':
        return (
          <ProtectedRoute permission="inventory:read">
            <AppHeader setActiveModule={setActiveModule}>
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Inventory Management</h2>
                <p className="text-blue-200">Medical supplies tracking coming soon...</p>
              </div>
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'invoices':
        return (
          <ProtectedRoute permission="invoices:read">
            <AppHeader setActiveModule={setActiveModule}>
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Invoice Management</h2>
                <p className="text-blue-200">Billing and payments coming soon...</p>
              </div>
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'lab-orders':
        return (
          <ProtectedRoute permission="lab:read">
            <AppHeader setActiveModule={setActiveModule}>
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Lab Integration</h2>
                <p className="text-blue-200">Laboratory orders and results coming soon...</p>
              </div>
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'insurance':
        return (
          <ProtectedRoute permission="insurance:read">
            <AppHeader setActiveModule={setActiveModule}>
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Insurance Verification</h2>
                <p className="text-blue-200">Eligibility and prior authorization coming soon...</p>
              </div>
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'employees':
        return (
          <ProtectedRoute permission="employees:read">
            <AppHeader setActiveModule={setActiveModule}>
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Employee Management</h2>
                <p className="text-blue-200">Staff management and payroll coming soon...</p>
              </div>
            </AppHeader>
          </ProtectedRoute>
        );
      
      case 'finance':
        return (
          <ProtectedRoute permission="finance:read">
            <AppHeader setActiveModule={setActiveModule}>
              <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-8 text-center">
                <h2 className="text-2xl font-bold text-white mb-4">Financial Reports</h2>
                <p className="text-blue-200">Practice analytics and reporting coming soon...</p>
              </div>
            </AppHeader>
          </ProtectedRoute>
        );

      // Add more modules as needed...
      
      default:
        return <Dashboard setActiveModule={setActiveModule} />;
    }
  };

  return renderModule();
}

// Main App Wrapper
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;