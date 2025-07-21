import React from "react";
import "./App.css";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import LoginPage from "./components/LoginPage";
import ERxModule from "./components/eRxModule";

// Loading Component
const LoadingScreen = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
    <div className="text-white text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
      <p>Loading ClinicHub...</p>
    </div>
  </div>
);

// Dashboard Component with Module Navigation
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [activeModule, setActiveModule] = React.useState(null);

  // Handle module navigation
  const handleModuleClick = (module) => {
    setActiveModule(module);
  };

  const handleBackToDashboard = () => {
    setActiveModule(null);
  };

  // If a module is active, render it
  if (activeModule === 'erx') {
    return (
      <div>
        <div className="bg-white/10 backdrop-blur-md border-b border-white/20 px-6 py-4">
          <button
            onClick={handleBackToDashboard}
            className="text-blue-300 hover:text-white mb-2 flex items-center"
          >
            ← Back to Dashboard
          </button>
        </div>
        <ERxModule />
      </div>
    );
  }

  // Default dashboard view
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">ClinicHub Dashboard</h1>
            <p className="text-blue-200">Welcome back, {user?.first_name}!</p>
          </div>
          <button
            onClick={logout}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div 
            onClick={() => handleModuleClick('patients')}
            className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 hover:bg-white/20 cursor-pointer transition-all duration-300"
          >
            <h3 className="text-lg font-semibold text-white mb-2">Patients/EHR</h3>
            <p className="text-blue-200 text-sm">Manage patient records and encounters</p>
          </div>
          
          <div 
            onClick={() => handleModuleClick('erx')}
            className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 hover:bg-white/20 cursor-pointer transition-all duration-300"
          >
            <h3 className="text-lg font-semibold text-white mb-2">eRx Module</h3>
            <p className="text-blue-200 text-sm">Electronic prescribing system</p>
            <div className="mt-2 text-green-400 text-xs">✅ FHIR Compliant</div>
          </div>
          
          <div 
            onClick={() => handleModuleClick('appointments')}
            className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 hover:bg-white/20 cursor-pointer transition-all duration-300"
          >
            <h3 className="text-lg font-semibold text-white mb-2">Appointments</h3>
            <p className="text-blue-200 text-sm">Schedule and manage appointments</p>
          </div>
          
          <div 
            onClick={() => handleModuleClick('settings')}
            className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 hover:bg-white/20 cursor-pointer transition-all duration-300"
          >
            <h3 className="text-lg font-semibold text-white mb-2">System Settings</h3>
            <p className="text-blue-200 text-sm">Configure Synology integration</p>
          </div>
          
          <div 
            onClick={() => handleModuleClick('medical-db')}
            className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 hover:bg-white/20 cursor-pointer transition-all duration-300"
          >
            <h3 className="text-lg font-semibold text-white mb-2">Medical Databases</h3>
            <p className="text-blue-200 text-sm">Search ICD-10 codes and medications</p>
          </div>
          
          <div 
            onClick={() => handleModuleClick('reports')}
            className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 hover:bg-white/20 cursor-pointer transition-all duration-300"
          >
            <h3 className="text-lg font-semibold text-white mb-2">Reports</h3>
            <p className="text-blue-200 text-sm">Generate practice analytics</p>
          </div>
        </div>

        <div className="mt-8 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-blue-200 text-sm">Authentication Source</p>
              <p className="text-white font-medium">{user?.auth_source || 'Local'}</p>
            </div>
            <div>
              <p className="text-blue-200 text-sm">User Role</p>
              <p className="text-white font-medium">{user?.role || 'User'}</p>
            </div>
            <div>
              <p className="text-blue-200 text-sm">Backend Status</p>
              <p className="text-green-400 font-medium">✅ Operational</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Content
const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return <LoadingScreen />;
  }

  return user ? <Dashboard /> : <LoginPage />;
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;