import React from "react";
import { useAuth } from "../contexts/AuthContext";

const AppHeader = ({ children, setActiveModule }) => {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setActiveModule && setActiveModule('dashboard')}
              className="text-blue-300 hover:text-white flex items-center space-x-2 transition duration-300"
            >
              <span className="text-2xl">🏥</span>
              <div>
                <h1 className="text-xl font-bold text-white">ClinicHub</h1>
                <p className="text-xs text-blue-200">Practice Management</p>
              </div>
            </button>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="text-right">
              <p className="text-white font-medium">{user?.first_name} {user?.last_name}</p>
              <p className="text-blue-200 text-sm">{user?.role} • {user?.auth_source}</p>
            </div>
            <button
              onClick={logout}
              className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition duration-300"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {children}
      </div>
    </div>
  );
};

export default AppHeader;