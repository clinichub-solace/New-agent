import React, { useState, useEffect } from "react";
import axios from "axios";

// Hardcoded API configuration to bypass environment variable issues in deployment
const BACKEND_URL = "/api";
const API = `/api`;

const PatientsModule = ({ setActiveModule }) => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showAddPatient, setShowAddPatient] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error("Error fetching patients:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const formatAge = (birthDate) => {
    if (!birthDate) return 'N/A';
    const today = new Date();
    const birth = new Date(birthDate);
    const age = today.getFullYear() - birth.getFullYear();
    return age;
  };

  if (selectedPatient) {
    return (
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setSelectedPatient(null)}
              className="text-blue-300 hover:text-white flex items-center"
            >
              ← Back to Patients
            </button>
            <div>
              <h2 className="text-2xl font-bold text-white">
                {selectedPatient.name?.[0]?.given?.[0]} {selectedPatient.name?.[0]?.family}
              </h2>
              <p className="text-blue-200">
                DOB: {formatDate(selectedPatient.birth_date)} | 
                Age: {formatAge(selectedPatient.birth_date)} | 
                Gender: {selectedPatient.gender || 'N/A'}
              </p>
            </div>
          </div>
          <div className="flex space-x-3">
            <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
              + New Visit
            </button>
            <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">
              + Vitals
            </button>
          </div>
        </div>

        {/* Patient Details Tabs */}
        <div className="mb-6">
          <div className="flex space-x-4 border-b border-white/20">
            {['overview', 'encounters', 'medications', 'allergies', 'documents'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-2 px-1 text-sm font-medium capitalize ${
                  activeTab === tab 
                    ? 'text-white border-b-2 border-blue-400' 
                    : 'text-blue-200 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="text-white">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold mb-4">Patient Information</h3>
                <div className="space-y-2">
                  <p><span className="text-blue-200">ID:</span> {selectedPatient.id}</p>
                  <p><span className="text-blue-200">Status:</span> {selectedPatient.status || 'Active'}</p>
                  <p><span className="text-blue-200">Gender:</span> {selectedPatient.gender || 'N/A'}</p>
                  <p><span className="text-blue-200">Birth Date:</span> {formatDate(selectedPatient.birth_date)}</p>
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
                <div className="space-y-2">
                  {selectedPatient.telecom?.map((contact, index) => (
                    <p key={index}>
                      <span className="text-blue-200">{contact.use}:</span> {contact.value}
                    </p>
                  ))}
                  {selectedPatient.address?.map((addr, index) => (
                    <div key={index}>
                      <p className="text-blue-200">Address:</p>
                      <p className="ml-2">{addr.line?.[0]}, {addr.city} {addr.state} {addr.postal_code}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          
          {activeTab !== 'overview' && (
            <div className="text-center py-8">
              <p className="text-blue-200">
                {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} functionality coming soon...
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Patient Management</h1>
          <p className="text-blue-200">FHIR-compliant electronic health records</p>
        </div>
        <button
          onClick={() => setShowAddPatient(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg flex items-center space-x-2"
        >
          <span>+ Add Patient</span>
        </button>
      </div>

      {/* Patients List */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Patients ({patients.length})</h2>
        
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            <p className="text-blue-200">Loading patients...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {patients.map((patient) => (
              <div
                key={patient.id}
                onClick={() => setSelectedPatient(patient)}
                className="bg-white/5 rounded-lg border border-white/10 p-4 hover:bg-white/10 cursor-pointer transition-all duration-300"
              >
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-white font-semibold">
                    {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                  </h3>
                  <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                    {patient.gender || 'N/A'}
                  </span>
                </div>
                
                <div className="text-sm text-blue-200 space-y-1">
                  <p>DOB: {formatDate(patient.birth_date)}</p>
                  <p>Age: {formatAge(patient.birth_date)}</p>
                  <p>ID: {patient.id.slice(0, 8)}...</p>
                </div>

                <div className="mt-3 pt-3 border-t border-white/10">
                  <div className="flex justify-between text-xs">
                    <span className="text-blue-300">Status: {patient.status || 'Active'}</span>
                    <span className="text-green-400">Click to view →</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && patients.length === 0 && (
          <div className="text-center py-8">
            <p className="text-blue-200">No patients found</p>
            <button
              onClick={() => setShowAddPatient(true)}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded transition duration-300"
            >
              Add First Patient
            </button>
          </div>
        )}
      </div>

      {/* Add Patient Modal Placeholder */}
      {showAddPatient && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Add New Patient</h3>
            <p className="text-blue-200 mb-4">Patient creation form coming soon...</p>
            <button
              onClick={() => setShowAddPatient(false)}
              className="w-full bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientsModule;