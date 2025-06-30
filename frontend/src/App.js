import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Components
const Dashboard = ({ setActiveModule }) => {
  const [stats, setStats] = useState({});
  const [recentPatients, setRecentPatients] = useState([]);
  const [recentInvoices, setRecentInvoices] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data.stats);
      setRecentPatients(response.data.recent_patients);
      setRecentInvoices(response.data.recent_invoices);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    }
  };

  const modules = [
    { name: "Patients/EHR", key: "patients", icon: "👥", color: "bg-blue-500" },
    { name: "Smart Forms", key: "forms", icon: "📋", color: "bg-green-500" },
    { name: "Invoices", key: "invoices", icon: "🧾", color: "bg-purple-500" },
    { name: "Inventory", key: "inventory", icon: "📦", color: "bg-orange-500" },
    { name: "Employees", key: "employees", icon: "👨‍⚕️", color: "bg-indigo-500" },
    { name: "Reports", key: "reports", icon: "📊", color: "bg-pink-500" }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Header */}
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-400 to-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">🏥</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">ClinicHub</h1>
                <p className="text-blue-200 text-sm">AI-Powered Practice Management</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-white font-semibold">Dr. Sarah Chen</p>
              <p className="text-blue-200 text-sm">Healthcare Admin</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm">Total Patients</p>
                <p className="text-3xl font-bold text-white">{stats.total_patients || 0}</p>
              </div>
              <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">👥</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm">Total Invoices</p>
                <p className="text-3xl font-bold text-white">{stats.total_invoices || 0}</p>
              </div>
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">🧾</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-200 text-sm">Pending Invoices</p>
                <p className="text-3xl font-bold text-white">{stats.pending_invoices || 0}</p>
              </div>
              <div className="w-12 h-12 bg-yellow-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">⏳</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-200 text-sm">Low Stock Items</p>
                <p className="text-3xl font-bold text-white">{stats.low_stock_items || 0}</p>
              </div>
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">⚠️</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm">Total Staff</p>
                <p className="text-3xl font-bold text-white">{stats.total_employees || 0}</p>
              </div>
              <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">👨‍⚕️</span>
              </div>
            </div>
          </div>
        </div>

        {/* Module Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {modules.map((module) => (
            <div
              key={module.key}
              onClick={() => setActiveModule(module.key)}
              className="bg-white/10 backdrop-blur-md rounded-xl p-8 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
            >
              <div className="text-center">
                <div className={`w-16 h-16 ${module.color} rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <span className="text-white text-2xl">{module.icon}</span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">{module.name}</h3>
                <p className="text-blue-200 text-sm">Manage your {module.name.toLowerCase()}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-4">Recent Patients</h3>
            <div className="space-y-3">
              {recentPatients.map((patient) => (
                <div key={patient.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div>
                    <p className="text-white font-medium">
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </p>
                    <p className="text-blue-200 text-sm">
                      {new Date(patient.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full">
                    {patient.status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-xl font-semibold text-white mb-4">Recent Invoices</h3>
            <div className="space-y-3">
              {recentInvoices.map((invoice) => (
                <div key={invoice.id} className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                  <div>
                    <p className="text-white font-medium">{invoice.invoice_number}</p>
                    <p className="text-blue-200 text-sm">
                      ${invoice.total_amount?.toFixed(2)}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-white text-xs rounded-full ${
                    invoice.status === 'paid' ? 'bg-green-500' : 
                    invoice.status === 'sent' ? 'bg-blue-500' : 'bg-gray-500'
                  }`}>
                    {invoice.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PatientsModule = ({ setActiveModule }) => {
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [formData, setFormData] = useState({
    first_name: '', last_name: '', email: '', phone: '', 
    date_of_birth: '', gender: '', address_line1: '', city: '', state: '', zip_code: ''
  });

  // EHR Data States
  const [patientSummary, setPatientSummary] = useState(null);
  const [encounters, setEncounters] = useState([]);
  const [showEncounterForm, setShowEncounterForm] = useState(false);
  const [showVitalsForm, setShowVitalsForm] = useState(false);
  const [showAllergyForm, setShowAllergyForm] = useState(false);
  const [showMedicationForm, setShowMedicationForm] = useState(false);
  const [showSOAPForm, setShowSOAPForm] = useState(false);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error("Error fetching patients:", error);
    }
  };

  const fetchPatientSummary = async (patientId) => {
    try {
      const response = await axios.get(`${API}/patients/${patientId}/summary`);
      setPatientSummary(response.data);
    } catch (error) {
      console.error("Error fetching patient summary:", error);
    }
  };

  const handlePatientSelect = (patient) => {
    setSelectedPatient(patient);
    fetchPatientSummary(patient.id);
    setActiveTab('overview');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/patients`, formData);
      setShowForm(false);
      setFormData({
        first_name: '', last_name: '', email: '', phone: '', 
        date_of_birth: '', gender: '', address_line1: '', city: '', state: '', zip_code: ''
      });
      fetchPatients();
    } catch (error) {
      console.error("Error creating patient:", error);
    }
  };

  // New Encounter Form
  const EncounterForm = () => {
    const [encounterData, setEncounterData] = useState({
      encounter_type: 'follow_up',
      scheduled_date: '',
      provider: 'Dr. Sarah Chen',
      location: 'Main Office',
      chief_complaint: '',
      reason_for_visit: ''
    });

    const handleEncounterSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/encounters`, {
          ...encounterData,
          patient_id: selectedPatient.id
        });
        setShowEncounterForm(false);
        fetchPatientSummary(selectedPatient.id);
      } catch (error) {
        console.error("Error creating encounter:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4">
          <h3 className="text-xl font-bold mb-4">New Encounter</h3>
          <form onSubmit={handleEncounterSubmit} className="space-y-4">
            <select
              value={encounterData.encounter_type}
              onChange={(e) => setEncounterData({...encounterData, encounter_type: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            >
              <option value="annual_physical">Annual Physical</option>
              <option value="follow_up">Follow-up</option>
              <option value="acute_care">Acute Care</option>
              <option value="preventive_care">Preventive Care</option>
              <option value="emergency">Emergency</option>
              <option value="consultation">Consultation</option>
            </select>
            <input
              type="datetime-local"
              value={encounterData.scheduled_date}
              onChange={(e) => setEncounterData({...encounterData, scheduled_date: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
            <input
              type="text"
              placeholder="Provider"
              value={encounterData.provider}
              onChange={(e) => setEncounterData({...encounterData, provider: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            />
            <textarea
              placeholder="Chief Complaint"
              value={encounterData.chief_complaint}
              onChange={(e) => setEncounterData({...encounterData, chief_complaint: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              rows="3"
            />
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowEncounterForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-500 text-white rounded-lg"
              >
                Create Encounter
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Vitals Form
  const VitalsForm = () => {
    const [vitalsData, setVitalsData] = useState({
      height: '', weight: '', systolic_bp: '', diastolic_bp: '',
      heart_rate: '', temperature: '', oxygen_saturation: '', pain_scale: '',
      recorded_by: 'Nurse Smith'
    });

    const handleVitalsSubmit = async (e) => {
      e.preventDefault();
      try {
        const data = {
          ...vitalsData,
          patient_id: selectedPatient.id,
          height: vitalsData.height ? parseFloat(vitalsData.height) : null,
          weight: vitalsData.weight ? parseFloat(vitalsData.weight) : null,
          systolic_bp: vitalsData.systolic_bp ? parseInt(vitalsData.systolic_bp) : null,
          diastolic_bp: vitalsData.diastolic_bp ? parseInt(vitalsData.diastolic_bp) : null,
          heart_rate: vitalsData.heart_rate ? parseInt(vitalsData.heart_rate) : null,
          temperature: vitalsData.temperature ? parseFloat(vitalsData.temperature) : null,
          oxygen_saturation: vitalsData.oxygen_saturation ? parseInt(vitalsData.oxygen_saturation) : null,
          pain_scale: vitalsData.pain_scale ? parseInt(vitalsData.pain_scale) : null,
        };
        
        await axios.post(`${API}/vital-signs`, data);
        setShowVitalsForm(false);
        fetchPatientSummary(selectedPatient.id);
      } catch (error) {
        console.error("Error recording vitals:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-bold mb-4">Record Vital Signs</h3>
          <form onSubmit={handleVitalsSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <input
                type="number"
                step="0.1"
                placeholder="Height (cm)"
                value={vitalsData.height}
                onChange={(e) => setVitalsData({...vitalsData, height: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                step="0.1"
                placeholder="Weight (kg)"
                value={vitalsData.weight}
                onChange={(e) => setVitalsData({...vitalsData, weight: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                placeholder="Systolic BP"
                value={vitalsData.systolic_bp}
                onChange={(e) => setVitalsData({...vitalsData, systolic_bp: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                placeholder="Diastolic BP"
                value={vitalsData.diastolic_bp}
                onChange={(e) => setVitalsData({...vitalsData, diastolic_bp: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                placeholder="Heart Rate (bpm)"
                value={vitalsData.heart_rate}
                onChange={(e) => setVitalsData({...vitalsData, heart_rate: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                step="0.1"
                placeholder="Temperature (°C)"
                value={vitalsData.temperature}
                onChange={(e) => setVitalsData({...vitalsData, temperature: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                placeholder="O2 Saturation (%)"
                value={vitalsData.oxygen_saturation}
                onChange={(e) => setVitalsData({...vitalsData, oxygen_saturation: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <select
                value={vitalsData.pain_scale}
                onChange={(e) => setVitalsData({...vitalsData, pain_scale: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="">Pain Scale (0-10)</option>
                {[0,1,2,3,4,5,6,7,8,9,10].map(n => (
                  <option key={n} value={n}>{n} - {n === 0 ? 'No Pain' : n <= 3 ? 'Mild' : n <= 6 ? 'Moderate' : 'Severe'}</option>
                ))}
              </select>
            </div>
            <input
              type="text"
              placeholder="Recorded by"
              value={vitalsData.recorded_by}
              onChange={(e) => setVitalsData({...vitalsData, recorded_by: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            />
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowVitalsForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-green-500 text-white rounded-lg"
              >
                Record Vitals
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  if (selectedPatient) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Patient Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setSelectedPatient(null)}
                className="text-blue-200 hover:text-white"
              >
                ← Back to Patients
              </button>
              <div>
                <h1 className="text-3xl font-bold text-white">
                  {selectedPatient.name?.[0]?.given?.[0]} {selectedPatient.name?.[0]?.family}
                </h1>
                <p className="text-blue-200">
                  DOB: {selectedPatient.birth_date ? new Date(selectedPatient.birth_date).toLocaleDateString() : 'N/A'} |
                  Gender: {selectedPatient.gender || 'N/A'} |
                  Status: {selectedPatient.status}
                </p>
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowEncounterForm(true)}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
              >
                + New Visit
              </button>
              <button
                onClick={() => setShowVitalsForm(true)}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg"
              >
                + Vitals
              </button>
            </div>
          </div>

          {/* EHR Tabs */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
            <div className="border-b border-white/20">
              <nav className="flex space-x-8 px-6">
                {['overview', 'encounters', 'medications', 'allergies', 'history'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`py-4 px-2 border-b-2 font-medium text-sm capitalize ${
                      activeTab === tab
                        ? 'border-blue-400 text-blue-400'
                        : 'border-transparent text-blue-200 hover:text-white'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'overview' && patientSummary && (
                <div className="space-y-6">
                  {/* Recent Vitals */}
                  {patientSummary.recent_vitals?.length > 0 && (
                    <div className="bg-white/5 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-white mb-3">Latest Vital Signs</h3>
                      <div className="grid grid-cols-4 gap-4">
                        {patientSummary.recent_vitals[0].systolic_bp && (
                          <div className="text-center">
                            <p className="text-blue-200 text-sm">Blood Pressure</p>
                            <p className="text-white font-semibold">
                              {patientSummary.recent_vitals[0].systolic_bp}/{patientSummary.recent_vitals[0].diastolic_bp}
                            </p>
                          </div>
                        )}
                        {patientSummary.recent_vitals[0].heart_rate && (
                          <div className="text-center">
                            <p className="text-blue-200 text-sm">Heart Rate</p>
                            <p className="text-white font-semibold">{patientSummary.recent_vitals[0].heart_rate} bpm</p>
                          </div>
                        )}
                        {patientSummary.recent_vitals[0].temperature && (
                          <div className="text-center">
                            <p className="text-blue-200 text-sm">Temperature</p>
                            <p className="text-white font-semibold">{patientSummary.recent_vitals[0].temperature}°C</p>
                          </div>
                        )}
                        {patientSummary.recent_vitals[0].weight && (
                          <div className="text-center">
                            <p className="text-blue-200 text-sm">Weight</p>
                            <p className="text-white font-semibold">{patientSummary.recent_vitals[0].weight} kg</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Active Medications */}
                  <div className="bg-white/5 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-white mb-3">Active Medications</h3>
                    {patientSummary.active_medications?.length > 0 ? (
                      <div className="space-y-2">
                        {patientSummary.active_medications.map((med) => (
                          <div key={med.id} className="flex justify-between items-center">
                            <div>
                              <p className="text-white font-medium">{med.medication_name}</p>
                              <p className="text-blue-200 text-sm">{med.dosage} - {med.frequency}</p>
                            </div>
                            <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full">
                              {med.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-blue-200">No active medications</p>
                    )}
                  </div>

                  {/* Allergies */}
                  <div className="bg-white/5 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-white mb-3">Allergies</h3>
                    {patientSummary.allergies?.length > 0 ? (
                      <div className="space-y-2">
                        {patientSummary.allergies.map((allergy) => (
                          <div key={allergy.id} className="flex justify-between items-center">
                            <div>
                              <p className="text-white font-medium">{allergy.allergen}</p>
                              <p className="text-blue-200 text-sm">{allergy.reaction}</p>
                            </div>
                            <span className={`px-2 py-1 text-white text-xs rounded-full ${
                              allergy.severity === 'severe' || allergy.severity === 'life_threatening'
                                ? 'bg-red-500' : 'bg-yellow-500'
                            }`}>
                              {allergy.severity}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-blue-200">No known allergies</p>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'encounters' && patientSummary && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-white">Recent Encounters</h3>
                  {patientSummary.recent_encounters?.map((encounter) => (
                    <div key={encounter.id} className="bg-white/5 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-white font-medium">{encounter.encounter_number}</p>
                          <p className="text-blue-200 capitalize">{encounter.encounter_type.replace('_', ' ')}</p>
                          <p className="text-blue-200 text-sm">
                            {new Date(encounter.scheduled_date).toLocaleDateString()} - {encounter.provider}
                          </p>
                          {encounter.chief_complaint && (
                            <p className="text-blue-200 text-sm mt-1">CC: {encounter.chief_complaint}</p>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-white text-xs rounded-full ${
                          encounter.status === 'completed' ? 'bg-green-500' : 
                          encounter.status === 'in_progress' ? 'bg-blue-500' : 'bg-gray-500'
                        }`}>
                          {encounter.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Forms */}
        {showEncounterForm && <EncounterForm />}
        {showVitalsForm && <VitalsForm />}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-200 hover:text-white"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Patients & EHR</h1>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg font-medium"
          >
            + Add Patient
          </button>
        </div>

        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-6">Add New Patient</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Form fields remain the same */}
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="text"
                    placeholder="First Name *"
                    value={formData.first_name}
                    onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                  <input
                    type="text"
                    placeholder="Last Name *"
                    value={formData.last_name}
                    onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="email"
                    placeholder="Email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="tel"
                    placeholder="Phone"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="date"
                    placeholder="Date of Birth"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({...formData, date_of_birth: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({...formData, gender: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select Gender</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <input
                  type="text"
                  placeholder="Address"
                  value={formData.address_line1}
                  onChange={(e) => setFormData({...formData, address_line1: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <div className="grid grid-cols-3 gap-4">
                  <input
                    type="text"
                    placeholder="City"
                    value={formData.city}
                    onChange={(e) => setFormData({...formData, city: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="State"
                    value={formData.state}
                    onChange={(e) => setFormData({...formData, state: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="ZIP Code"
                    value={formData.zip_code}
                    onChange={(e) => setFormData({...formData, zip_code: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="flex justify-end space-x-4 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                  >
                    Add Patient
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="bg-white/10 backdrop-blur-md rounded-xl overflow-hidden border border-white/20">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/20">
                <tr>
                  <th className="text-left p-4 text-white font-semibold">Name</th>
                  <th className="text-left p-4 text-white font-semibold">Contact</th>
                  <th className="text-left p-4 text-white font-semibold">DOB</th>
                  <th className="text-left p-4 text-white font-semibold">Gender</th>
                  <th className="text-left p-4 text-white font-semibold">Status</th>
                  <th className="text-left p-4 text-white font-semibold">Added</th>
                  <th className="text-left p-4 text-white font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr key={patient.id} className="border-b border-white/10 hover:bg-white/5">
                    <td className="p-4 text-white">
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </td>
                    <td className="p-4 text-blue-200">
                      {patient.telecom?.find(t => t.system === 'email')?.value || 'N/A'}
                    </td>
                    <td className="p-4 text-blue-200">
                      {patient.birth_date ? new Date(patient.birth_date).toLocalDateString() : 'N/A'}
                    </td>
                    <td className="p-4 text-blue-200 capitalize">
                      {patient.gender || 'N/A'}
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-1 bg-green-500 text-white text-xs rounded-full">
                        {patient.status}
                      </span>
                    </td>
                    <td className="p-4 text-blue-200">
                      {new Date(patient.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => handlePatientSelect(patient)}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                      >
                        View EHR
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

const InvoicesModule = ({ setActiveModule }) => {
  const [invoices, setInvoices] = useState([]);
  const [patients, setPatients] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    patient_id: '', items: [{ description: '', quantity: 1, unit_price: 0, total: 0 }],
    tax_rate: 0.08, due_days: 30, notes: ''
  });

  useEffect(() => {
    fetchInvoices();
    fetchPatients();
  }, []);

  const fetchInvoices = async () => {
    try {
      const response = await axios.get(`${API}/invoices`);
      setInvoices(response.data);
    } catch (error) {
      console.error("Error fetching invoices:", error);
    }
  };

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error("Error fetching patients:", error);
    }
  };

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { description: '', quantity: 1, unit_price: 0, total: 0 }]
    });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    
    if (field === 'quantity' || field === 'unit_price') {
      newItems[index].total = newItems[index].quantity * newItems[index].unit_price;
    }
    
    setFormData({ ...formData, items: newItems });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/invoices`, formData);
      setShowForm(false);
      setFormData({
        patient_id: '', items: [{ description: '', quantity: 1, unit_price: 0, total: 0 }],
        tax_rate: 0.08, due_days: 30, notes: ''
      });
      fetchInvoices();
    } catch (error) {
      console.error("Error creating invoice:", error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-200 hover:text-white"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Invoices & Billing</h1>
          </div>
          <button
            onClick={() => setShowForm(true)}
            className="bg-purple-500 hover:bg-purple-600 text-white px-6 py-2 rounded-lg font-medium"
          >
            + Create Invoice
          </button>
        </div>

        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <h2 className="text-2xl font-bold mb-6">Create Invoice</h2>
              <form onSubmit={handleSubmit} className="space-y-6">
                <select
                  value={formData.patient_id}
                  onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>

                <div>
                  <h3 className="text-lg font-semibold mb-3">Invoice Items</h3>
                  {formData.items.map((item, index) => (
                    <div key={index} className="grid grid-cols-4 gap-4 mb-3">
                      <input
                        type="text"
                        placeholder="Description"
                        value={item.description}
                        onChange={(e) => updateItem(index, 'description', e.target.value)}
                        className="col-span-2 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                      <input
                        type="number"
                        placeholder="Qty"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                        className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                      <input
                        type="number"
                        step="0.01"
                        placeholder="Unit Price"
                        value={item.unit_price}
                        onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                        className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addItem}
                    className="text-purple-500 hover:text-purple-600 font-medium"
                  >
                    + Add Item
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Tax Rate (0.08 = 8%)"
                    value={formData.tax_rate}
                    onChange={(e) => setFormData({...formData, tax_rate: parseFloat(e.target.value) || 0})}
                    className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                  <input
                    type="number"
                    placeholder="Due Days"
                    value={formData.due_days}
                    onChange={(e) => setFormData({...formData, due_days: parseInt(e.target.value) || 30})}
                    className="p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <textarea
                  placeholder="Notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                  rows="3"
                />

                <div className="flex justify-end space-x-4 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
                  >
                    Create Invoice
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        <div className="bg-white/10 backdrop-blur-md rounded-xl overflow-hidden border border-white/20">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/20">
                <tr>
                  <th className="text-left p-4 text-white font-semibold">Invoice #</th>
                  <th className="text-left p-4 text-white font-semibold">Patient</th>
                  <th className="text-left p-4 text-white font-semibold">Amount</th>
                  <th className="text-left p-4 text-white font-semibold">Status</th>
                  <th className="text-left p-4 text-white font-semibold">Issue Date</th>
                  <th className="text-left p-4 text-white font-semibold">Due Date</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="border-b border-white/10 hover:bg-white/5">
                    <td className="p-4 text-white font-medium">{invoice.invoice_number}</td>
                    <td className="p-4 text-blue-200">Patient ID: {invoice.patient_id.slice(0, 8)}...</td>
                    <td className="p-4 text-white">${invoice.total_amount?.toFixed(2)}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-white text-xs rounded-full ${
                        invoice.status === 'paid' ? 'bg-green-500' : 
                        invoice.status === 'sent' ? 'bg-blue-500' : 'bg-gray-500'
                      }`}>
                        {invoice.status}
                      </span>
                    </td>
                    <td className="p-4 text-blue-200">
                      {new Date(invoice.issue_date).toLocaleDateString()}
                    </td>
                    <td className="p-4 text-blue-200">
                      {invoice.due_date ? new Date(invoice.due_date).toLocaleDateString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [activeModule, setActiveModule] = useState('dashboard');

  const renderModule = () => {
    switch (activeModule) {
      case 'patients':
        return <PatientsModule setActiveModule={setActiveModule} />;
      case 'invoices':
        return <InvoicesModule setActiveModule={setActiveModule} />;
      default:
        return <Dashboard setActiveModule={setActiveModule} />;
    }
  };

  return (
    <div className="App">
      {renderModule()}
    </div>
  );
}

export default App;