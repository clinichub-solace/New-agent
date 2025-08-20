import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "/api";
const API = `${BACKEND_URL}`;

const SchedulingModule = ({ setActiveModule }) => {
  const [appointments, setAppointments] = useState([]);
  const [providers, setProviders] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [viewMode, setViewMode] = useState('day'); // day, week, month
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchAppointments();
    fetchProviders();
  }, [selectedDate]);

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/appointments`);
      setAppointments(response.data);
    } catch (error) {
      console.error("Error fetching appointments:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`);
      setProviders(response.data);
    } catch (error) {
      console.error("Error fetching providers:", error);
    }
  };

  const formatTime = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return 'bg-green-600';
      case 'pending': return 'bg-yellow-600';
      case 'cancelled': return 'bg-red-600';
      case 'completed': return 'bg-blue-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Appointment Scheduling</h1>
          <p className="text-blue-200">Manage appointments and provider schedules</p>
        </div>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg">
          + New Appointment
        </button>
      </div>

      {/* Calendar Controls */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-3 py-2 bg-white/10 border border-white/30 rounded text-white"
            />
            
            <div className="flex space-x-2">
              {['day', 'week', 'month'].map(mode => (
                <button
                  key={mode}
                  onClick={() => setViewMode(mode)}
                  className={`px-4 py-2 rounded capitalize ${
                    viewMode === mode 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-white/10 text-blue-200 hover:bg-white/20'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          <div className="text-white text-right">
            <p className="text-sm text-blue-200">Selected Date</p>
            <p className="font-semibold">{formatDate(selectedDate)}</p>
          </div>
        </div>

        {/* Appointments List */}
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">
            Appointments ({appointments.length})
          </h3>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-blue-200">Loading appointments...</p>
            </div>
          ) : (
            <div className="space-y-3">
              {appointments.map((appointment) => (
                <div
                  key={appointment.id}
                  className="bg-white/5 rounded-lg border border-white/10 p-4 hover:bg-white/10 transition-all duration-300"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${getStatusColor(appointment.status)}`}></div>
                      <div>
                        <h4 className="text-white font-semibold">
                          {appointment.patient_name || 'Unknown Patient'}
                        </h4>
                        <p className="text-blue-200 text-sm">
                          {formatTime(appointment.appointment_date)} - {appointment.appointment_type}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-white text-sm">
                        {appointment.provider_name || 'No Provider'}
                      </p>
                      <span className={`text-xs px-2 py-1 rounded ${getStatusColor(appointment.status)} text-white`}>
                        {appointment.status || 'Pending'}
                      </span>
                    </div>
                  </div>
                  
                  {appointment.notes && (
                    <div className="mt-3 pt-3 border-t border-white/10">
                      <p className="text-blue-200 text-sm">{appointment.notes}</p>
                    </div>
                  )}
                </div>
              ))}
              
              {appointments.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-blue-200">No appointments scheduled for this date</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Providers Quick View */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Providers ({providers.length})</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className="bg-white/5 rounded-lg border border-white/10 p-4"
            >
              <h4 className="text-white font-semibold">
                {provider.first_name} {provider.last_name}
              </h4>
              <p className="text-blue-200 text-sm">{provider.specialty || 'General Practice'}</p>
              <p className="text-blue-300 text-xs mt-1">
                Status: {provider.status || 'Active'}
              </p>
            </div>
          ))}
          
          {providers.length === 0 && (
            <div className="col-span-3 text-center py-4">
              <p className="text-blue-200">No providers configured</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SchedulingModule;