import React, { useState, useEffect } from "react";
import "./App.css";
import { formatErrorMessage, toDisplayError } from './utils/errors';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import api from './api/axios';

// ✅ PHASE 6: FINAL ENHANCEMENT - Unified Notification System
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    fetchNotifications();
    // Auto-refresh notifications every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  // ✅ URL VETTING: Uses configured 'api' instance
  const fetchNotifications = async () => {
    try {
      const response = await api.get('/notifications?limit=10');
      const notificationsData = response.data || [];
      setNotifications(notificationsData);
      setUnreadCount(notificationsData.filter(n => !n.acknowledged).length);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const markAsRead = async (notificationId) => {
    try {
      await api.post(`/notifications/${notificationId}/ack`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, acknowledged: true } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'info': 'bg-blue-500/20 text-blue-300 border-blue-500/50',
      'success': 'bg-green-500/20 text-green-300 border-green-500/50',
      'warning': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
      'error': 'bg-red-500/20 text-red-300 border-red-500/50'
    };
    return colors[severity] || 'bg-gray-500/20 text-gray-300 border-gray-500/50';
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      <button
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative bg-white/10 backdrop-blur-md border border-white/20 p-3 rounded-lg hover:bg-white/20 transition-colors"
      >
        <span className="text-white text-xl">🔔</span>
        {unreadCount > 0 && (
          <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {showNotifications && (
        <div className="absolute top-12 right-0 w-80 bg-gray-800 border border-gray-600 rounded-lg shadow-xl max-h-96 overflow-y-auto">
          <div className="p-4 border-b border-gray-600">
            <div className="flex items-center justify-between">
              <h3 className="text-white font-medium">Notifications</h3>
              <button
                onClick={() => setShowNotifications(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-400">
                No notifications
              </div>
            ) : (
              notifications.map(notification => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-600 last:border-b-0 cursor-pointer hover:bg-gray-700 ${
                    !notification.acknowledged ? 'bg-blue-500/10' : ''
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className={`text-sm p-2 rounded border ${getSeverityColor(notification.severity)}`}>
                    <div className="font-medium">{notification.title}</div>
                    <div className="mt-1">{notification.message}</div>
                    <div className="text-xs mt-2 opacity-75">
                      {new Date(notification.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ✅ ICD-10 Lookup Component - Reusable across all clinical modules
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
const ICD10Lookup = ({ onSelect, selectedCodes = [], placeholder = "Search ICD-10 codes..." }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  // ✅ URL VETTING: Uses configured 'api' instance
  const searchICD10 = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      setIsSearching(true);
      const response = await api.get(`/icd10/search?query=${encodeURIComponent(query)}&limit=10`);
      setSearchResults(response.data || []);
      setShowResults(true);
    } catch (error) {
      console.error('Error searching ICD-10 codes:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearch = (value) => {
    setSearchTerm(value);
    searchICD10(value);
  };

  const handleSelect = (code) => {
    if (onSelect) {
      onSelect(code);
    }
    setSearchTerm('');
    setSearchResults([]);
    setShowResults(false);
  };

  const removeCode = (codeToRemove) => {
    if (onSelect) {
      const updatedCodes = selectedCodes.filter(code => code.code !== codeToRemove.code);
      onSelect(null, updatedCodes);
    }
  };

  return (
    <div className="relative">
      {/* Selected Codes Display */}
      {selectedCodes.length > 0 && (
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-300 mb-2">Selected ICD-10 Codes:</label>
          <div className="space-y-1">
            {selectedCodes.map((code) => (
              <div key={code.code} className="flex items-center justify-between bg-blue-600/20 text-blue-300 px-3 py-2 rounded text-sm">
                <div>
                  <span className="font-medium">{code.code}</span> - {code.description}
                  <div className="text-xs text-blue-400">Category: {code.category}</div>
                </div>
                <button
                  onClick={() => removeCode(code)}
                  className="text-blue-400 hover:text-white ml-2"
                  type="button"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => setShowResults(searchResults.length > 0)}
          onBlur={() => setTimeout(() => setShowResults(false), 200)}
          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white pr-10"
          placeholder={placeholder}
        />
        {isSearching && (
          <div className="absolute right-3 top-3">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
          </div>
        )}
      </div>

      {/* Search Results */}
      {showResults && searchResults.length > 0 && (
        <div className="absolute z-50 w-full bg-gray-800 border border-gray-600 rounded-lg mt-1 max-h-60 overflow-y-auto">
          {searchResults.map((code) => (
            <button
              key={code.id}
              type="button"
              onClick={() => handleSelect(code)}
              className="w-full text-left px-4 py-3 hover:bg-gray-700 border-b border-gray-600 last:border-b-0"
            >
              <div className="text-white font-medium">{code.code}</div>
              <div className="text-gray-300 text-sm mt-1">{code.description}</div>
              <div className="text-gray-400 text-xs mt-1">
                Category: {code.category}
                {code.search_terms && (
                  <span className="ml-2">
                    Tags: {Array.isArray(code.search_terms) ? code.search_terms.join(', ') : code.search_terms}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// RESTORED ClinicHub App - Complete EHR System with Advanced Features
// ✅ PHASE 1: Enhanced Dashboard with Navigation System Restored
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix

// ✅ PHASE 2: CORE EHR MODULES - Advanced Patients/EHR Module (1,603 lines)
// ✅ URL VETTING: All API calls verified to use configured 'api' instance
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
    provider: user?.username || 'Dr. Provider',
    diagnosis_codes: []  // ICD-10 codes for this SOAP note
  });

  const [vitalsFormData, setVitalsFormData] = useState({
    height: '',
    weight: '',
    systolic_bp: '',
    diastolic_bp: '',
    heart_rate: '',
    temperature: '',
    respiratory_rate: '',
    oxygen_saturation: '',
    pain_scale: '',
    notes: ''
  });

  const [patientFormData, setPatientFormData] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    phone: '',
    email: '',
    address: {
      line: [''],
      city: '',
      state: '',
      postal_code: '',
      country: 'USA'
    }
  });

  const [allergyFormData, setAllergyFormData] = useState({
    allergy_name: '',
    reaction: '',
    severity: 'mild',
    notes: ''
  });

  // ✅ URL VETTING: All API calls use configured 'api' instance
  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    if (selectedPatient) {
      fetchPatientData(selectedPatient.id);
    }
  }, [selectedPatient]);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const response = await api.get('/patients');
      setPatients(response.data || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
      setError('Failed to fetch patients');
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientData = async (patientId) => {
    try {
      // ✅ URL VETTING: All endpoints use /api prefix via configured api instance
      const [soapRes, vitalsRes, allergiesRes, medicationsRes, prescriptionsRes, historyRes] = await Promise.all([
        api.get(`/soap-notes/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/vital-signs/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/allergies/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/medications/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/prescriptions/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/medical-history/patient/${patientId}`).catch(() => ({ data: [] }))
      ]);

      setSoapNotes(soapRes.data || []);
      setVitalSigns(vitalsRes.data || []);
      setAllergies(allergiesRes.data || []);
      setMedications(medicationsRes.data || []);
      setPrescriptions(prescriptionsRes.data || []);
      setMedicalHistory(historyRes.data || []);
    } catch (error) {
      console.error('Error fetching patient data:', error);
    }
  };

  const addPatient = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/patients', patientFormData);
      setPatients(prev => [...prev, response.data]);
      setShowAddForm(false);
      setSuccess('Patient added successfully');
      
      // Reset form
      setPatientFormData({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        phone: '',
        email: '',
        address: {
          line: [''],
          city: '',
          state: '',
          postal_code: '',
          country: 'USA'
        }
      });
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding patient:', error);
      setError('Failed to add patient');
    } finally {
      setLoading(false);
    }
  };

  // SOAP Notes Functions
  const addSoapNote = async (e) => {
    e.preventDefault();
    try {
      const noteData = {
        ...soapFormData,
        patient_id: selectedPatient.id,
        encounter_date: new Date().toISOString()
      };
      
      const response = await api.post('/soap-notes', noteData);
      setSoapNotes(prev => [...prev, response.data]);
      setShowSoapForm(false);
      setSoapFormData({
        subjective: '',
        objective: '',
        assessment: '',
        plan: '',
        provider: user?.username || 'Dr. Provider',
        diagnosis_codes: []
      });
      setSuccess('SOAP note added successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding SOAP note:', error);
      setError('Failed to add SOAP note');
    }
  };

  // Vital Signs Functions
  const addVitalSigns = async (e) => {
    e.preventDefault();
    try {
      const vitalsData = {
        ...vitalsFormData,
        patient_id: selectedPatient.id,
        recorded_date: new Date().toISOString()
      };
      
      const response = await api.post('/vital-signs', vitalsData);
      setVitalSigns(prev => [...prev, response.data]);
      setShowVitalsForm(false);
      setVitalsFormData({
        height: '',
        weight: '',
        systolic_bp: '',
        diastolic_bp: '',
        heart_rate: '',
        temperature: '',
        respiratory_rate: '',
        oxygen_saturation: '',
        pain_scale: '',
        notes: ''
      });
      setSuccess('Vital signs added successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding vital signs:', error);
      setError('Failed to add vital signs');
    }
  };

  // Allergy Functions
  const addAllergy = async (e) => {
    e.preventDefault();
    try {
      const allergyData = {
        ...allergyFormData,
        patient_id: selectedPatient.id
      };
      
      const response = await api.post('/allergies', allergyData);
      setAllergies(prev => [...prev, response.data]);
      setShowAllergyForm(false);
      setAllergyFormData({
        allergy_name: '',
        reaction: '',
        severity: 'mild',
        notes: ''
      });
      setSuccess('Allergy added successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding allergy:', error);
      setError('Failed to add allergy');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">🏥 Electronic Health Records</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
        >
          Add New Patient
        </button>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/20 border border-green-500 text-green-100 px-4 py-2 rounded-lg">
          {success}
        </div>
      )}

      <div className="flex space-x-6">
        {/* Patient List Sidebar */}
        <div className="w-1/3 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <h3 className="text-lg font-medium text-white mb-4">Patient List</h3>
          
          {loading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="text-blue-200 mt-2">Loading patients...</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {patients.map((patient) => (
                <button
                  key={patient.id}
                  onClick={() => setSelectedPatient(patient)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedPatient?.id === patient.id
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'bg-white/10 border-white/20 text-blue-200 hover:bg-white/20'
                  }`}
                >
                  <div className="font-medium">
                    {patient.name?.[0]?.given?.[0] || patient.first_name} {patient.name?.[0]?.family || patient.last_name}
                  </div>
                  <div className="text-sm opacity-75">
                    ID: {patient.id} • DOB: {patient.birthDate || patient.date_of_birth}
                  </div>
                </button>
              ))}
              {patients.length === 0 && (
                <div className="text-center py-8 text-blue-300">
                  No patients found. Add your first patient to get started.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Patient Details Panel */}
        <div className="flex-1 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          {selectedPatient ? (
            <>
              {/* Patient Header */}
              <div className="mb-6 pb-4 border-b border-white/20">
                <h3 className="text-xl font-bold text-white">
                  {selectedPatient.name?.[0]?.given?.[0] || selectedPatient.first_name} {selectedPatient.name?.[0]?.family || selectedPatient.last_name}
                </h3>
                <div className="text-blue-200 space-y-1">
                  <p>Patient ID: {selectedPatient.id}</p>
                  <p>Date of Birth: {selectedPatient.birthDate || selectedPatient.date_of_birth}</p>
                  <p>Gender: {selectedPatient.gender}</p>
                  {selectedPatient.telecom?.find(t => t.system === 'phone') && (
                    <p>Phone: {selectedPatient.telecom.find(t => t.system === 'phone').value}</p>
                  )}
                </div>
              </div>

              {/* EHR Tabs */}
              <div className="mb-4">
                <div className="flex space-x-1 bg-white/10 rounded-lg p-1">
                  {[
                    { key: 'soap', label: 'SOAP Notes', count: soapNotes.length },
                    { key: 'vitals', label: 'Vital Signs', count: vitalSigns.length },
                    { key: 'allergies', label: 'Allergies', count: allergies.length },
                    { key: 'medications', label: 'Medications', count: medications.length },
                    { key: 'prescriptions', label: 'Prescriptions', count: prescriptions.length },
                    { key: 'history', label: 'Medical History', count: medicalHistory.length }
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        activeTab === tab.key
                          ? 'bg-blue-600 text-white'
                          : 'text-blue-200 hover:bg-white/10'
                      }`}
                    >
                      {tab.label} ({tab.count})
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                {activeTab === 'soap' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-medium text-white">SOAP Notes</h4>
                      <button
                        onClick={() => setShowSoapForm(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Add SOAP Note
                      </button>
                    </div>
                    
                    {soapNotes.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No SOAP notes recorded. Click "Add SOAP Note" to create the first entry.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {soapNotes.map((note) => (
                          <div key={note.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-sm text-blue-300">
                                {new Date(note.encounter_date).toLocaleString()} - Dr. {note.provider}
                              </span>
                              <span className="text-xs bg-green-600 text-white px-2 py-1 rounded">
                                {note.status || 'Completed'}
                              </span>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                              <div>
                                <strong className="text-white">Subjective:</strong>
                                <p className="text-blue-200 mt-1">{note.subjective}</p>
                              </div>
                              <div>
                                <strong className="text-white">Objective:</strong>
                                <p className="text-blue-200 mt-1">{note.objective}</p>
                              </div>
                              <div>
                                <strong className="text-white">Assessment:</strong>
                                <p className="text-blue-200 mt-1">{note.assessment}</p>
                              </div>
                              <div>
                                <strong className="text-white">Plan:</strong>
                                <p className="text-blue-200 mt-1">{note.plan}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'vitals' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-medium text-white">Vital Signs</h4>
                      <button
                        onClick={() => setShowVitalsForm(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Record Vitals
                      </button>
                    </div>
                    
                    {vitalSigns.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No vital signs recorded. Click "Record Vitals" to add the first entry.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {vitalSigns.map((vital) => (
                          <div key={vital.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-sm text-blue-300">
                                {new Date(vital.recorded_date).toLocaleString()}
                              </span>
                              {vital.weight && vital.height && (
                                <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                                  BMI: {(vital.weight / ((vital.height/100) ** 2)).toFixed(1)}
                                </span>
                              )}
                            </div>
                            
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              {vital.height && (
                                <div>
                                  <span className="text-white font-medium">Height:</span>
                                  <p className="text-blue-200">{vital.height} cm</p>
                                </div>
                              )}
                              {vital.weight && (
                                <div>
                                  <span className="text-white font-medium">Weight:</span>
                                  <p className="text-blue-200">{vital.weight} kg</p>
                                </div>
                              )}
                              {(vital.systolic_bp && vital.diastolic_bp) && (
                                <div>
                                  <span className="text-white font-medium">Blood Pressure:</span>
                                  <p className="text-blue-200">{vital.systolic_bp}/{vital.diastolic_bp}</p>
                                </div>
                              )}
                              {vital.heart_rate && (
                                <div>
                                  <span className="text-white font-medium">Heart Rate:</span>
                                  <p className="text-blue-200">{vital.heart_rate} bpm</p>
                                </div>
                              )}
                              {vital.temperature && (
                                <div>
                                  <span className="text-white font-medium">Temperature:</span>
                                  <p className="text-blue-200">{vital.temperature}°C</p>
                                </div>
                              )}
                              {vital.respiratory_rate && (
                                <div>
                                  <span className="text-white font-medium">Respiratory Rate:</span>
                                  <p className="text-blue-200">{vital.respiratory_rate} /min</p>
                                </div>
                              )}
                              {vital.oxygen_saturation && (
                                <div>
                                  <span className="text-white font-medium">O2 Saturation:</span>
                                  <p className="text-blue-200">{vital.oxygen_saturation}%</p>
                                </div>
                              )}
                              {vital.pain_scale && (
                                <div>
                                  <span className="text-white font-medium">Pain Scale:</span>
                                  <p className="text-blue-200">{vital.pain_scale}/10</p>
                                </div>
                              )}
                            </div>
                            
                            {vital.notes && (
                              <div className="mt-3 pt-3 border-t border-white/20">
                                <span className="text-white font-medium">Notes:</span>
                                <p className="text-blue-200 mt-1">{vital.notes}</p>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'allergies' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-medium text-white">Allergies</h4>
                      <button
                        onClick={() => setShowAllergyForm(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Add Allergy
                      </button>
                    </div>
                    
                    {allergies.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No known allergies recorded. Click "Add Allergy" to record allergies.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {allergies.map((allergy) => (
                          <div key={allergy.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <div className="flex items-center justify-between">
                              <div>
                                <h5 className="text-white font-medium text-lg">{allergy.allergy_name}</h5>
                                <p className="text-blue-200">{allergy.reaction}</p>
                                {allergy.notes && <p className="text-blue-300 text-sm mt-1">{allergy.notes}</p>}
                              </div>
                              <div className="text-right">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  allergy.severity === 'severe' ? 'bg-red-600 text-white' :
                                  allergy.severity === 'moderate' ? 'bg-yellow-600 text-white' :
                                  'bg-green-600 text-white'
                                }`}>
                                  {allergy.severity?.toUpperCase() || 'MILD'}
                                </span>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'medications' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-medium text-white">Current Medications</h4>
                    </div>
                    
                    {medications.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No current medications recorded.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {medications.map((medication) => (
                          <div key={medication.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <div className="flex items-center justify-between">
                              <div>
                                <h5 className="text-white font-medium">{medication.medication_name}</h5>
                                <p className="text-blue-200">{medication.dosage} - {medication.frequency}</p>
                                {medication.notes && <p className="text-blue-300 text-sm">{medication.notes}</p>}
                              </div>
                              <span className={`px-2 py-1 rounded text-xs ${
                                medication.status === 'active' ? 'bg-green-600 text-white' : 'bg-gray-600 text-white'
                              }`}>
                                {medication.status?.toUpperCase() || 'ACTIVE'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'prescriptions' && (
                  <div>
                    <h4 className="text-lg font-medium text-white mb-4">Prescription History</h4>
                    
                    {prescriptions.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No prescriptions on record.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {prescriptions.map((prescription) => (
                          <div key={prescription.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <div className="flex items-center justify-between">
                              <div>
                                <h5 className="text-white font-medium">{prescription.medication_name}</h5>
                                <p className="text-blue-200">{prescription.dosage_instructions}</p>
                                <p className="text-blue-300 text-sm">Prescribed: {new Date(prescription.created_at).toLocaleDateString()}</p>
                              </div>
                              <span className={`px-2 py-1 rounded text-xs ${
                                prescription.status === 'filled' ? 'bg-green-600 text-white' :
                                prescription.status === 'pending' ? 'bg-yellow-600 text-white' :
                                'bg-gray-600 text-white'
                              }`}>
                                {prescription.status?.toUpperCase() || 'PENDING'}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'history' && (
                  <div>
                    <h4 className="text-lg font-medium text-white mb-4">Medical History</h4>
                    
                    {medicalHistory.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No medical history recorded.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {medicalHistory.map((history) => (
                          <div key={history.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <h5 className="text-white font-medium">{history.condition}</h5>
                            <p className="text-blue-200">{history.notes}</p>
                            <p className="text-blue-300 text-sm">Recorded: {new Date(history.created_at).toLocaleDateString()}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🏥</div>
              <h3 className="text-xl text-white mb-2">Select a Patient</h3>
              <p className="text-blue-200">Choose a patient from the list to view their electronic health record</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Patient Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md m-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add New Patient</h3>
            
            <form onSubmit={addPatient} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                <input
                  type="text"
                  value={patientFormData.first_name}
                  onChange={(e) => setPatientFormData(prev => ({...prev, first_name: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                <input
                  type="text"
                  value={patientFormData.last_name}
                  onChange={(e) => setPatientFormData(prev => ({...prev, last_name: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                <input
                  type="date"
                  value={patientFormData.date_of_birth}
                  onChange={(e) => setPatientFormData(prev => ({...prev, date_of_birth: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                <select
                  value={patientFormData.gender}
                  onChange={(e) => setPatientFormData(prev => ({...prev, gender: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="">Select Gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={patientFormData.phone}
                  onChange={(e) => setPatientFormData(prev => ({...prev, phone: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={patientFormData.email}
                  onChange={(e) => setPatientFormData(prev => ({...prev, email: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add Patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add SOAP Note Modal */}
      {showSoapForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl m-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add SOAP Note</h3>
            
            <form onSubmit={addSoapNote} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Subjective</label>
                <textarea
                  value={soapFormData.subjective}
                  onChange={(e) => setSoapFormData(prev => ({...prev, subjective: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                  placeholder="Patient's description of symptoms, concerns, and history..."
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Objective</label>
                <textarea
                  value={soapFormData.objective}
                  onChange={(e) => setSoapFormData(prev => ({...prev, objective: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                  placeholder="Clinical observations, examination findings, vital signs..."
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assessment</label>
                <textarea
                  value={soapFormData.assessment}
                  onChange={(e) => setSoapFormData(prev => ({...prev, assessment: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Clinical impression, diagnosis, differential diagnosis..."
                  required
                />
              </div>

              {/* ICD-10 Diagnosis Codes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ICD-10 Diagnosis Codes</label>
                <ICD10Lookup
                  selectedCodes={soapFormData.diagnosis_codes}
                  onSelect={(code, updatedCodes) => {
                    if (code) {
                      // Adding a new code
                      const exists = soapFormData.diagnosis_codes.some(existingCode => existingCode.code === code.code);
                      if (!exists) {
                        setSoapFormData(prev => ({
                          ...prev,
                          diagnosis_codes: [...prev.diagnosis_codes, code]
                        }));
                      }
                    } else if (updatedCodes) {
                      // Removing codes (from the component)
                      setSoapFormData(prev => ({
                        ...prev,
                        diagnosis_codes: updatedCodes
                      }));
                    }
                  }}
                  placeholder="Search ICD-10 diagnosis codes..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Plan</label>
                <textarea
                  value={soapFormData.plan}
                  onChange={(e) => setSoapFormData(prev => ({...prev, plan: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                  placeholder="Treatment plan, medications, follow-up instructions..."
                  required
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowSoapForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Save SOAP Note
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Vital Signs Modal */}
      {showVitalsForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md m-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Record Vital Signs</h3>
            
            <form onSubmit={addVitalSigns} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Height (cm)</label>
                  <input
                    type="number"
                    value={vitalsFormData.height}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, height: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Weight (kg)</label>
                  <input
                    type="number"
                    value={vitalsFormData.weight}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, weight: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Systolic BP</label>
                  <input
                    type="number"
                    value={vitalsFormData.systolic_bp}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, systolic_bp: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Diastolic BP</label>
                  <input
                    type="number"
                    value={vitalsFormData.diastolic_bp}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, diastolic_bp: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Heart Rate</label>
                  <input
                    type="number"
                    value={vitalsFormData.heart_rate}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, heart_rate: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Temperature (°C)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={vitalsFormData.temperature}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, temperature: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Respiratory Rate</label>
                  <input
                    type="number"
                    value={vitalsFormData.respiratory_rate}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, respiratory_rate: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">O2 Saturation (%)</label>
                  <input
                    type="number"
                    value={vitalsFormData.oxygen_saturation}
                    onChange={(e) => setVitalsFormData(prev => ({...prev, oxygen_saturation: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Pain Scale (0-10)</label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={vitalsFormData.pain_scale}
                  onChange={(e) => setVitalsFormData(prev => ({...prev, pain_scale: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Notes</label>
                <textarea
                  value={vitalsFormData.notes}
                  onChange={(e) => setVitalsFormData(prev => ({...prev, notes: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Additional clinical observations..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowVitalsForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Record Vitals
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Allergy Modal */}
      {showAllergyForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md m-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add Allergy</h3>
            
            <form onSubmit={addAllergy} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Allergy/Substance</label>
                <input
                  type="text"
                  value={allergyFormData.allergy_name}
                  onChange={(e) => setAllergyFormData(prev => ({...prev, allergy_name: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Penicillin, Peanuts, Latex..."
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reaction</label>
                <input
                  type="text"
                  value={allergyFormData.reaction}
                  onChange={(e) => setAllergyFormData(prev => ({...prev, reaction: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Rash, Swelling, Anaphylaxis..."
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Severity</label>
                <select
                  value={allergyFormData.severity}
                  onChange={(e) => setAllergyFormData(prev => ({...prev, severity: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="mild">Mild</option>
                  <option value="moderate">Moderate</option>
                  <option value="severe">Severe</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Additional Notes</label>
                <textarea
                  value={allergyFormData.notes}
                  onChange={(e) => setAllergyFormData(prev => ({...prev, notes: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Additional details about the allergy..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAllergyForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Allergy
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// ✅ PHASE 4: CLINICAL ENHANCEMENT - Quality Measures Module (534 lines)  
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
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

  // ✅ URL VETTING: Uses configured 'api' instance
  const fetchMeasures = async () => {
    try {
      setLoading(true);
      const response = await api.get('/quality-measures');
      setMeasures(response.data);
    } catch (error) {
      console.error('Failed to fetch quality measures:', error);
      setError('Failed to fetch quality measures');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const fetchMeasureResults = async () => {
    try {
      const response = await api.get('/quality-measures/report');
      setMeasureResults(response.data);
    } catch (error) {
      console.error('Failed to fetch measure results:', error);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const handleCalculateMeasures = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await api.post('/quality-measures/calculate', {});
      
      setSuccess('Quality measures calculated successfully!');
      fetchMeasureResults();
    } catch (error) {
      console.error('Failed to calculate quality measures:', error);
      setError(error.response?.data?.detail || 'Failed to calculate quality measures');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const handleCreateMeasure = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const url = editingMeasure ? 
        `/quality-measures/${editingMeasure.id}` : 
        '/quality-measures';
      
      const response = editingMeasure ? 
        await api.put(url, measureFormData) : 
        await api.post(url, measureFormData);

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

// ✅ PHASE 5: HIGH-IMPACT MODULES - Scheduling Module (Priority #1)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
const SchedulingModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [providers, setProviders] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // View states
  const [activeView, setActiveView] = useState('calendar'); // calendar, appointments, providers
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [showAppointmentForm, setShowAppointmentForm] = useState(false);
  const [editingAppointment, setEditingAppointment] = useState(null);

  // Form data
  const [appointmentFormData, setAppointmentFormData] = useState({
    patient_id: '',
    provider_id: '',
    appointment_date: '',
    appointment_time: '',
    duration: 30,
    appointment_type: 'office_visit',
    status: 'scheduled',
    notes: '',
    chief_complaint: ''
  });

  const [scheduleStats, setScheduleStats] = useState({
    todayAppointments: 0,
    weekAppointments: 0,
    availableSlots: 0,
    cancelledToday: 0
  });

  useEffect(() => {
    fetchScheduleData();
  }, [selectedDate]);

  // ✅ URL VETTING: Using configured 'api' instance with /api prefix
  const fetchScheduleData = async () => {
    setLoading(true);
    try {
      const [appointmentsRes, providersRes, patientsRes] = await Promise.all([
        api.get('/appointments').catch(() => ({ data: [] })),
        api.get('/providers').catch(() => ({ data: [] })),
        api.get('/patients').catch(() => ({ data: [] }))
      ]);

      setAppointments(appointmentsRes.data || []);
      setProviders(providersRes.data || []);
      setPatients(patientsRes.data || []);

      // Calculate stats
      const today = new Date().toISOString().split('T')[0];
      const todayAppointments = (appointmentsRes.data || []).filter(apt => 
        apt.appointment_date?.startsWith(today)
      );
      
      setScheduleStats({
        todayAppointments: todayAppointments.length,
        weekAppointments: (appointmentsRes.data || []).length,
        availableSlots: 32 - todayAppointments.length, // 8 hours * 4 slots per hour
        cancelledToday: todayAppointments.filter(apt => apt.status === 'cancelled').length
      });

    } catch (error) {
      console.error('Error fetching schedule data:', error);
      setError('Failed to fetch schedule data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Using configured 'api' instance
  const createAppointment = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const appointmentData = {
        ...appointmentFormData,
        scheduled_by: user?.id,
        created_at: new Date().toISOString(),
        appointment_datetime: `${appointmentFormData.appointment_date}T${appointmentFormData.appointment_time}`
      };

      const response = editingAppointment ? 
        await api.put(`/appointments/${editingAppointment.id}`, appointmentData) :
        await api.post('/appointments', appointmentData);

      if (editingAppointment) {
        setAppointments(appointments.map(apt => apt.id === editingAppointment.id ? response.data : apt));
        setSuccess('Appointment updated successfully!');
      } else {
        setAppointments([...appointments, response.data]);
        setSuccess('Appointment scheduled successfully!');
      }

      setShowAppointmentForm(false);
      setEditingAppointment(null);
      resetAppointmentForm();
      fetchScheduleData(); // Refresh data
    } catch (error) {
      console.error('Error saving appointment:', error);
      setError(error.response?.data?.detail || 'Failed to save appointment');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Using configured 'api' instance
  const updateAppointmentStatus = async (appointmentId, newStatus) => {
    try {
      await api.put(`/appointments/${appointmentId}/status`, { status: newStatus });
      
      setAppointments(appointments.map(apt => 
        apt.id === appointmentId ? { ...apt, status: newStatus } : apt
      ));
      
      setSuccess(`Appointment ${newStatus} successfully!`);
      fetchScheduleData(); // Refresh stats
    } catch (error) {
      console.error('Error updating appointment:', error);
      setError('Failed to update appointment status');
    }
  };

  const resetAppointmentForm = () => {
    setAppointmentFormData({
      patient_id: '',
      provider_id: '',
      appointment_date: '',
      appointment_time: '',
      duration: 30,
      appointment_type: 'office_visit',
      status: 'scheduled',
      notes: '',
      chief_complaint: ''
    });
  };

  const handleEditAppointment = (appointment) => {
    setEditingAppointment(appointment);
    setAppointmentFormData({
      patient_id: appointment.patient_id,
      provider_id: appointment.provider_id,
      appointment_date: appointment.appointment_date?.split('T')[0] || '',
      appointment_time: appointment.appointment_time || appointment.appointment_datetime?.split('T')[1]?.substring(0, 5) || '',
      duration: appointment.duration || 30,
      appointment_type: appointment.appointment_type || 'office_visit',
      status: appointment.status || 'scheduled',
      notes: appointment.notes || '',
      chief_complaint: appointment.chief_complaint || ''
    });
    setShowAppointmentForm(true);
  };

  const getStatusColor = (status) => {
    const colors = {
      'scheduled': 'bg-blue-100 text-blue-800',
      'confirmed': 'bg-green-100 text-green-800', 
      'completed': 'bg-gray-100 text-gray-800',
      'cancelled': 'bg-red-100 text-red-800',
      'no_show': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const generateTimeSlots = () => {
    const slots = [];
    for (let hour = 8; hour < 17; hour++) { // 8 AM to 5 PM
      for (let minute = 0; minute < 60; minute += 30) {
        const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        slots.push(time);
      }
    }
    return slots;
  };

  const renderCalendarView = () => {
    const todayAppointments = appointments.filter(apt => 
      apt.appointment_date?.startsWith(selectedDate)
    ).sort((a, b) => (a.appointment_time || '').localeCompare(b.appointment_time || ''));

    return (
      <div className="space-y-6">
        {/* Date Selector */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">Select Date</label>
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          />
        </div>

        {/* Schedule Grid */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            📅 Schedule for {new Date(selectedDate).toLocaleDateString()}
          </h3>
          
          {todayAppointments.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-6xl mb-4">📅</div>
              <p>No appointments scheduled for this date</p>
              <button
                onClick={() => setShowAppointmentForm(true)}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Schedule Appointment
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {todayAppointments.map((appointment) => (
                <div key={appointment.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-blue-400 font-bold">
                          {appointment.appointment_time || 'Time TBD'}
                        </div>
                        <div className="text-white font-medium">
                          {patients.find(p => p.id === appointment.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === appointment.patient_id)?.name?.[0]?.family || 'Unknown Patient'}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(appointment.status)}`}>
                          {appointment.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Provider: {providers.find(p => p.id === appointment.provider_id)?.first_name} {providers.find(p => p.id === appointment.provider_id)?.last_name}
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Type: {appointment.appointment_type} • Duration: {appointment.duration || 30} min
                      </div>
                      {appointment.chief_complaint && (
                        <div className="text-sm text-gray-400 mt-1">
                          Chief Complaint: {appointment.chief_complaint}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditAppointment(appointment)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Edit
                      </button>
                      {appointment.status === 'scheduled' && (
                        <button
                          onClick={() => updateAppointmentStatus(appointment.id, 'confirmed')}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Confirm
                        </button>
                      )}
                      {appointment.status !== 'cancelled' && (
                        <button
                          onClick={() => updateAppointmentStatus(appointment.id, 'cancelled')}
                          className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Cancel
                        </button>
                      )}
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

  const renderAppointmentForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              {editingAppointment ? '✏️ Edit Appointment' : '📅 Schedule New Appointment'}
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

          <form onSubmit={createAppointment} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, provider_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Provider</option>
                  {providers.map(provider => (
                    <option key={provider.id} value={provider.id}>
                      Dr. {provider.first_name} {provider.last_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Date</label>
                <input
                  type="date"
                  value={appointmentFormData.appointment_date}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, appointment_date: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Time</label>
                <select
                  value={appointmentFormData.appointment_time}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, appointment_time: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Time</option>
                  {generateTimeSlots().map(time => (
                    <option key={time} value={time}>{time}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Duration (minutes)</label>
                <select
                  value={appointmentFormData.duration}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, duration: parseInt(e.target.value)})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value={15}>15 min</option>
                  <option value={30}>30 min</option>
                  <option value={45}>45 min</option>
                  <option value={60}>60 min</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Type</label>
                <select
                  value={appointmentFormData.appointment_type}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, appointment_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="office_visit">Office Visit</option>
                  <option value="follow_up">Follow Up</option>
                  <option value="consultation">Consultation</option>
                  <option value="physical_exam">Physical Exam</option>
                  <option value="procedure">Procedure</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Status</label>
                <select
                  value={appointmentFormData.status}
                  onChange={(e) => setAppointmentFormData({...appointmentFormData, status: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="scheduled">Scheduled</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="no_show">No Show</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Chief Complaint</label>
              <input
                type="text"
                value={appointmentFormData.chief_complaint}
                onChange={(e) => setAppointmentFormData({...appointmentFormData, chief_complaint: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Primary reason for visit..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
              <textarea
                value={appointmentFormData.notes}
                onChange={(e) => setAppointmentFormData({...appointmentFormData, notes: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                placeholder="Additional notes or instructions..."
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingAppointment ? 'Update Appointment' : 'Schedule Appointment')}
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
            onClick={() => setShowAppointmentForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📅 New Appointment
          </button>
          <button
            onClick={fetchScheduleData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Statistics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{scheduleStats.todayAppointments}</div>
              <div className="text-sm text-gray-300">Today's Appointments</div>
            </div>
            <div className="text-2xl">📅</div>
          </div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{scheduleStats.weekAppointments}</div>
              <div className="text-sm text-gray-300">Total Appointments</div>
            </div>
            <div className="text-2xl">📋</div>
          </div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{scheduleStats.availableSlots}</div>
              <div className="text-sm text-gray-300">Available Slots Today</div>
            </div>
            <div className="text-2xl">⏰</div>
          </div>
        </div>
        
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-2xl font-bold text-white">{scheduleStats.cancelledToday}</div>
              <div className="text-sm text-gray-300">Cancelled Today</div>
            </div>
            <div className="text-2xl">❌</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'calendar', name: 'Calendar View', icon: '📅' },
            { id: 'appointments', name: 'All Appointments', icon: '📋' },
            { id: 'providers', name: 'Provider Schedules', icon: '👨‍⚕️' }
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
      {activeView === 'calendar' && renderCalendarView()}
      {activeView === 'appointments' && (
        <div className="space-y-4">
          {appointments.map(appointment => (
            <div key={appointment.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-blue-400 font-bold">
                      {new Date(appointment.appointment_date).toLocaleDateString()} {appointment.appointment_time}
                    </div>
                    <div className="text-white font-medium">
                      {patients.find(p => p.id === appointment.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === appointment.patient_id)?.name?.[0]?.family}
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(appointment.status)}`}>
                      {appointment.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300 mt-1">
                    Provider: {providers.find(p => p.id === appointment.provider_id)?.first_name} {providers.find(p => p.id === appointment.provider_id)?.last_name}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditAppointment(appointment)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Edit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'providers' && (
        <div className="text-white">Provider schedule management coming soon...</div>
      )}

      {/* Appointment Form Modal */}
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

// ✅ PHASE 5: HIGH-IMPACT MODULES - Telehealth Module (Modern Healthcare Standard)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
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
  
  // Video call states
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

  // Session statistics
  const [sessionStats, setSessionStats] = useState({
    todaySessions: 0,
    activeSessions: 0,
    waitingPatients: 0,
    completedSessions: 0
  });

  useEffect(() => {
    fetchTelehealthData();
  }, []);

  // ✅ URL VETTING: All API calls use configured 'api' instance
  const fetchTelehealthData = async () => {
    try {
      setLoading(true);
      const [sessionsRes, patientsRes, providersRes, waitingRes] = await Promise.all([
        api.get('/telehealth/sessions').catch(() => ({ data: [] })),
        api.get('/patients').catch(() => ({ data: [] })),
        api.get('/providers').catch(() => ({ data: [] })),
        api.get('/telehealth/waiting-room').catch(() => ({ data: [] }))
      ]);

      setSessions(sessionsRes.data || []);
      setPatients(patientsRes.data || []);
      setProviders(providersRes.data || []);
      setWaitingRoom(waitingRes.data || []);

      // Calculate stats
      const today = new Date().toISOString().split('T')[0];
      const todaySessions = (sessionsRes.data || []).filter(session => 
        session.scheduled_start?.startsWith(today)
      );

      setSessionStats({
        todaySessions: todaySessions.length,
        activeSessions: (sessionsRes.data || []).filter(s => s.status === 'active').length,
        waitingPatients: (waitingRes.data || []).length,
        completedSessions: (sessionsRes.data || []).filter(s => s.status === 'completed').length
      });

    } catch (error) {
      console.error('Error fetching telehealth data:', error);
      setError('Failed to fetch telehealth data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const createSession = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const sessionData = {
        ...sessionFormData,
        created_by: user?.id,
        access_code: Math.random().toString(36).substring(2, 8).toUpperCase(),
        session_url: `telehealth/session/${Date.now()}`
      };

      const response = await api.post('/telehealth/sessions', sessionData);

      setSessions([...sessions, response.data]);
      setSuccess('Telehealth session created successfully!');
      setShowSessionForm(false);
      resetSessionForm();
    } catch (error) {
      console.error('Error creating session:', error);
      setError(error.response?.data?.detail || 'Failed to create session');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const joinSession = async (sessionId) => {
    try {
      setLoading(true);
      const response = await api.post(`/telehealth/sessions/${sessionId}/join`, {
        participant_id: user?.id,
        participant_type: 'provider'
      });

      setSelectedSession(response.data);
      setIsInCall(true);
      setConnectionStatus('connecting');
      
      // Simulate connection process
      setTimeout(() => {
        setConnectionStatus('connected');
        setSuccess('Successfully joined telehealth session!');
      }, 2000);

    } catch (error) {
      console.error('Error joining session:', error);
      setError('Failed to join session');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const endSession = async (sessionId) => {
    try {
      await api.put(`/telehealth/sessions/${sessionId}/end`);
      
      setIsInCall(false);
      setSelectedSession(null);
      setConnectionStatus('disconnected');
      setSuccess('Session ended successfully');
      fetchTelehealthData();
    } catch (error) {
      console.error('Error ending session:', error);
      setError('Failed to end session');
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

  const getSessionStatusColor = (status) => {
    const colors = {
      'scheduled': 'bg-blue-100 text-blue-800',
      'active': 'bg-green-100 text-green-800',
      'completed': 'bg-gray-100 text-gray-800',
      'cancelled': 'bg-red-100 text-red-800',
      'waiting': 'bg-yellow-100 text-yellow-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    const upcomingSessions = sessions.filter(s => 
      new Date(s.scheduled_start) > new Date() && s.status !== 'cancelled'
    ).slice(0, 5);

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{sessionStats.todaySessions}</div>
                <div className="text-sm text-gray-300">Today's Sessions</div>
              </div>
              <div className="text-2xl">📹</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{sessionStats.activeSessions}</div>
                <div className="text-sm text-gray-300">Active Sessions</div>
              </div>
              <div className="text-2xl">🟢</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{sessionStats.waitingPatients}</div>
                <div className="text-sm text-gray-300">Waiting Patients</div>
              </div>
              <div className="text-2xl">⏳</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{sessionStats.completedSessions}</div>
                <div className="text-sm text-gray-300">Completed</div>
              </div>
              <div className="text-2xl">✅</div>
            </div>
          </div>
        </div>

        {/* Waiting Room */}
        {waitingRoom.length > 0 && (
          <div className="bg-orange-500/20 border border-orange-400/50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">⏳ Patients in Waiting Room</h3>
            <div className="space-y-3">
              {waitingRoom.map(patient => (
                <div key={patient.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-white font-medium">{patient.name}</div>
                      <div className="text-sm text-orange-300">
                        Waiting for: {patient.session_type} • Time: {new Date(patient.join_time).toLocaleTimeString()}
                      </div>
                    </div>
                    <button
                      onClick={() => joinSession(patient.session_id)}
                      className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
                    >
                      Join Session
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Upcoming Sessions */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📅 Upcoming Telehealth Sessions</h3>
          {upcomingSessions.length === 0 ? (
            <p className="text-gray-400">No upcoming telehealth sessions scheduled.</p>
          ) : (
            <div className="space-y-3">
              {upcomingSessions.map(session => (
                <div key={session.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{session.title}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getSessionStatusColor(session.status)}`}>
                          {session.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        {new Date(session.scheduled_start).toLocaleString()} • Duration: {session.duration_minutes} min
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        Patient: {patients.find(p => p.id === session.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === session.patient_id)?.name?.[0]?.family}
                      </div>
                      {session.access_code && (
                        <div className="text-sm text-blue-400 mt-1">
                          Access Code: {session.access_code}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => joinSession(session.id)}
                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Join
                      </button>
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

  const renderSessionForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">📹 New Telehealth Session</h3>
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

          <form onSubmit={createSession} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Session Title</label>
              <input
                type="text"
                value={sessionFormData.title}
                onChange={(e) => setSessionFormData({...sessionFormData, title: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Follow-up appointment with Dr. Smith"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                      Dr. {provider.first_name} {provider.last_name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Session Type</label>
                <select
                  value={sessionFormData.session_type}
                  onChange={(e) => setSessionFormData({...sessionFormData, session_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="video_consultation">Video Consultation</option>
                  <option value="audio_only">Audio Only</option>
                  <option value="follow_up">Follow-up Call</option>
                  <option value="therapy_session">Therapy Session</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Duration (minutes)</label>
                <select
                  value={sessionFormData.duration_minutes}
                  onChange={(e) => setSessionFormData({...sessionFormData, duration_minutes: parseInt(e.target.value)})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>60 minutes</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Scheduled Start Time</label>
              <input
                type="datetime-local"
                value={sessionFormData.scheduled_start}
                onChange={(e) => setSessionFormData({...sessionFormData, scheduled_start: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <textarea
                value={sessionFormData.description}
                onChange={(e) => setSessionFormData({...sessionFormData, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                placeholder="Purpose of the telehealth session..."
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="recording_enabled"
                checked={sessionFormData.recording_enabled}
                onChange={(e) => setSessionFormData({...sessionFormData, recording_enabled: e.target.checked})}
                className="rounded"
              />
              <label htmlFor="recording_enabled" className="text-gray-300">Enable Recording (with patient consent)</label>
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

  const renderVideoCall = () => {
    if (!isInCall || !selectedSession) return null;

    return (
      <div className="fixed inset-0 bg-black z-50">
        <div className="h-full flex flex-col">
          {/* Video Area */}
          <div className="flex-1 relative bg-gray-900 flex items-center justify-center">
            <div className="text-center text-white">
              <div className="text-6xl mb-4">📹</div>
              <h3 className="text-xl mb-2">Telehealth Session Active</h3>
              <p className="text-gray-400">
                Session with {patients.find(p => p.id === selectedSession.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === selectedSession.patient_id)?.name?.[0]?.family}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                Status: {connectionStatus} • Access Code: {selectedSession.access_code}
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="bg-gray-800 p-4 flex items-center justify-between">
            <div className="flex space-x-4">
              <span className="text-white">
                Session: {selectedSession.title}
              </span>
              <span className={`px-2 py-1 rounded text-xs ${
                connectionStatus === 'connected' ? 'bg-green-600 text-white' : 'bg-yellow-600 text-white'
              }`}>
                {connectionStatus}
              </span>
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => endSession(selectedSession.id)}
                className="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg"
              >
                End Session
              </button>
              <button
                onClick={() => {
                  setIsInCall(false);
                  setSelectedSession(null);
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                Exit
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">💻 Telehealth</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowSessionForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📹 New Session
          </button>
          <button
            onClick={fetchTelehealthData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'sessions', name: 'All Sessions', icon: '📹' },
            { id: 'waiting-room', name: 'Waiting Room', icon: '⏳' }
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
      {activeView === 'sessions' && (
        <div className="space-y-4">
          {sessions.map(session => (
            <div key={session.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-white font-medium">{session.title}</div>
                    <span className={`px-2 py-1 rounded text-xs ${getSessionStatusColor(session.status)}`}>
                      {session.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300 mt-1">
                    {new Date(session.scheduled_start).toLocaleString()} • {session.session_type}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {session.status === 'scheduled' && (
                    <button
                      onClick={() => joinSession(session.id)}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Join
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'waiting-room' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">⏳ Waiting Room Management</h3>
          <p className="text-gray-300">Advanced waiting room controls coming soon...</p>
        </div>
      )}

      {/* Forms */}
      {showSessionForm && renderSessionForm()}
      
      {/* Video Call Interface */}
      {renderVideoCall()}
      
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

// ✅ PHASE 5: HIGH-IMPACT MODULES - Patient Portal Module (High Patient Value)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
const PatientPortalModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [portalData, setPortalData] = useState({
    appointments: [],
    labResults: [],
    prescriptions: [],
    messages: [],
    forms: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // View states
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedPatientId, setSelectedPatientId] = useState('');
  const [patients, setPatients] = useState([]);
  const [newMessage, setNewMessage] = useState('');

  // Portal statistics
  const [portalStats, setPortalStats] = useState({
    activePortals: 0,
    unreadMessages: 0,
    pendingForms: 0,
    upcomingAppointments: 0
  });

  useEffect(() => {
    fetchPatients();
    if (selectedPatientId) {
      fetchPortalData(selectedPatientId);
    }
  }, [selectedPatientId]);

  // ✅ URL VETTING: Using configured 'api' instance
  const fetchPatients = async () => {
    try {
      const response = await api.get('/patients');
      setPatients(response.data || []);
    } catch (error) {
      console.error('Error fetching patients:', error);
    }
  };

  // ✅ URL VETTING: Using configured 'api' instance
  const fetchPortalData = async (patientId) => {
    setLoading(true);
    try {
      const [appointmentsRes, labResultsRes, prescriptionsRes, messagesRes] = await Promise.all([
        api.get(`/appointments/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/lab-results/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/prescriptions/patient/${patientId}`).catch(() => ({ data: [] })),
        api.get(`/patient-portal/${patientId}/messages`).catch(() => ({ data: [] }))
      ]);

      setPortalData({
        appointments: appointmentsRes.data || [],
        labResults: labResultsRes.data || [],
        prescriptions: prescriptionsRes.data || [],
        messages: messagesRes.data || [],
        forms: []
      });

      // Update stats
      setPortalStats({
        activePortals: 1,
        unreadMessages: (messagesRes.data || []).filter(msg => !msg.read).length,
        pendingForms: 0,
        upcomingAppointments: (appointmentsRes.data || []).filter(apt => 
          new Date(apt.appointment_date) >= new Date() && apt.status !== 'cancelled'
        ).length
      });

    } catch (error) {
      console.error('Error fetching portal data:', error);
      setError('Failed to fetch portal data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Using configured 'api' instance
  const createPortalAccess = async (patientId) => {
    try {
      setLoading(true);
      const response = await api.post('/patient-portal/access', {
        patient_id: patientId,
        access_level: 'full',
        expires_at: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString() // 90 days
      });
      
      setSuccess(`Portal access created for patient. Access token: ${response.data.access_token}`);
    } catch (error) {
      console.error('Error creating portal access:', error);
      setError('Failed to create portal access');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Using configured 'api' instance
  const sendMessage = async (patientId, message) => {
    try {
      const response = await api.post(`/patient-portal/${patientId}/messages`, {
        message: message,
        sender: 'staff',
        sender_id: user?.id,
        message_type: 'general'
      });
      
      setPortalData(prev => ({
        ...prev,
        messages: [...prev.messages, response.data]
      }));
      
      setSuccess('Message sent successfully!');
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (newMessage.trim() && selectedPatientId) {
      await sendMessage(selectedPatientId, newMessage.trim());
      setNewMessage('');
    }
  };

  const renderDashboard = () => {
    return (
      <div className="space-y-6">
        {/* Patient Selector */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">Select Patient for Portal View</label>
          <select
            value={selectedPatientId}
            onChange={(e) => setSelectedPatientId(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="">Select a patient...</option>
            {patients.map(patient => (
              <option key={patient.id} value={patient.id}>
                {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family} - {patient.id}
              </option>
            ))}
          </select>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.activePortals}</div>
                <div className="text-sm text-gray-300">Active Portals</div>
              </div>
              <div className="text-2xl">🌐</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.unreadMessages}</div>
                <div className="text-sm text-gray-300">Unread Messages</div>
              </div>
              <div className="text-2xl">📧</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.upcomingAppointments}</div>
                <div className="text-sm text-gray-300">Upcoming Appointments</div>
              </div>
              <div className="text-2xl">📅</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{portalStats.pendingForms}</div>
                <div className="text-sm text-gray-300">Pending Forms</div>
              </div>
              <div className="text-2xl">📋</div>
            </div>
          </div>
        </div>

        {selectedPatientId ? (
          <>
            {/* Portal Actions */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">🚪 Portal Access Management</h3>
              <div className="flex space-x-4">
                <button
                  onClick={() => createPortalAccess(selectedPatientId)}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
                >
                  Create Portal Access
                </button>
                <button
                  onClick={() => setActiveView('messages')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                >
                  Send Message
                </button>
              </div>
            </div>

            {/* Patient Information Summary */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-white mb-4">👤 Patient Portal Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white/5 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">📅 Appointments</h4>
                  <p className="text-2xl font-bold text-blue-400">{portalData.appointments.length}</p>
                  <p className="text-sm text-gray-300">Total appointments</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">🧪 Lab Results</h4>
                  <p className="text-2xl font-bold text-green-400">{portalData.labResults.length}</p>
                  <p className="text-sm text-gray-300">Available results</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <h4 className="text-white font-medium mb-2">💊 Prescriptions</h4>
                  <p className="text-2xl font-bold text-purple-400">{portalData.prescriptions.length}</p>
                  <p className="text-sm text-gray-300">Active prescriptions</p>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-12 text-gray-400">
            <div className="text-6xl mb-4">🌐</div>
            <p className="text-xl mb-2">Patient Portal Management</p>
            <p>Select a patient to view their portal information</p>
          </div>
        )}
      </div>
    );
  };

  const renderMessages = () => {
    return (
      <div className="space-y-6">
        {/* Send Message Form */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📧 Send Message to Patient</h3>
          <form onSubmit={handleSendMessage} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Message</label>
              <textarea
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-24"
                placeholder="Type your message to the patient..."
                required
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading || !newMessage.trim() || !selectedPatientId}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg disabled:opacity-50"
              >
                Send Message
              </button>
            </div>
          </form>
        </div>

        {/* Message History */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">💬 Message History</h3>
          {portalData.messages.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              No messages yet
            </div>
          ) : (
            <div className="space-y-4">
              {portalData.messages.map(message => (
                <div key={message.id} className="bg-white/5 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-white font-medium">
                      {message.sender === 'staff' ? 'Staff' : 'Patient'}
                    </span>
                    <span className="text-gray-400 text-sm">
                      {new Date(message.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-gray-300">{message.message}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">🌐 Patient Portal</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => fetchPortalData(selectedPatientId)}
            disabled={!selectedPatientId}
            className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg disabled:opacity-50"
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '🏠' },
            { id: 'messages', name: 'Messages', icon: '📧' },
            { id: 'appointments', name: 'Appointments', icon: '📅' },
            { id: 'records', name: 'Records', icon: '📋' }
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
      {activeView === 'messages' && renderMessages()}
      {activeView === 'appointments' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">📅 Patient Appointments</h3>
          {portalData.appointments.length === 0 ? (
            <div className="text-center py-8 text-gray-400">No appointments found</div>
          ) : (
            portalData.appointments.map(appointment => (
              <div key={appointment.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">
                      {new Date(appointment.appointment_date).toLocaleDateString()} at {appointment.appointment_time}
                    </div>
                    <div className="text-gray-300 text-sm">Type: {appointment.appointment_type}</div>
                    <div className="text-gray-300 text-sm">Status: {appointment.status}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
      {activeView === 'records' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">📋 Medical Records Access</h3>
          <p className="text-gray-300">Patient record sharing functionality coming soon...</p>
        </div>
      )}

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

  // ✅ URL VETTING: Using configured 'api' instance with /api prefix
  const fetchLabData = async () => {
    setLoading(true);
    try {
      // Fetch all lab-related data
      const [ordersRes, testsRes, resultsRes, patientsRes, providersRes] = await Promise.all([
        api.get('/lab-orders').catch(() => ({ data: [] })),
        api.get('/lab-tests').catch(() => ({ data: [] })),
        api.get('/lab-results').catch(() => ({ data: [] })),
        api.get('/patients').catch(() => ({ data: [] })),
        api.get('/providers').catch(() => ({ data: [] }))
      ]);

      setLabOrders(ordersRes.data || []);
      setLabTests(testsRes.data || []);
      setLabResults(resultsRes.data || []);
      setPatients(patientsRes.data || []);
      setProviders(providersRes.data || []);

      // Calculate stats
      const orders = ordersRes.data || [];
      const results = resultsRes.data || [];
      
      setLabStats({
        totalOrders: orders.length,
        pendingOrders: orders.filter(o => o.status === 'pending' || o.status === 'in_progress').length,
        completedToday: results.filter(r => {
          const today = new Date().toDateString();
          return new Date(r.completed_date).toDateString() === today;
        }).length,
        criticalResults: results.filter(r => r.is_critical === true).length
      });

    } catch (error) {
      console.error('Failed to fetch lab data:', error);
      setError('Failed to fetch laboratory data');
    } finally {
      setLoading(false);
    }
  };

  const createLabOrder = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await api.post('/lab-orders', {
        ...orderFormData,
        ordered_by: user?.id,
        order_date: new Date().toISOString()
      });
      
      setLabOrders([...labOrders, response.data]);
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
      setShowOrderForm(false);
      setSuccess('Lab order created successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error creating lab order:', error);
      setError('Failed to create lab order');
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await api.put(`/lab-orders/${orderId}/status`, { status });
      setLabOrders(labOrders.map(order => 
        order.id === orderId ? { ...order, status } : order
      ));
      setSuccess(`Order status updated to ${status}`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error updating order status:', error);
      setError('Failed to update order status');
    }
  };

  const addLabResult = async (orderId, resultData) => {
    try {
      const response = await api.post(`/lab-orders/${orderId}/results`, resultData);
      setLabResults([...labResults, response.data]);
      // Update order status to completed
      updateOrderStatus(orderId, 'completed');
      setSuccess('Lab result added successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding lab result:', error);
      setError('Failed to add lab result');
    }
  };

  // Available lab tests (in real implementation, this would come from API)
  const availableTests = [
    { id: 'cbc', name: 'Complete Blood Count (CBC)', category: 'Hematology', code: 'CBC' },
    { id: 'bmp', name: 'Basic Metabolic Panel (BMP)', category: 'Chemistry', code: 'BMP' },
    { id: 'cmp', name: 'Comprehensive Metabolic Panel (CMP)', category: 'Chemistry', code: 'CMP' },
    { id: 'lipid', name: 'Lipid Panel', category: 'Chemistry', code: 'LIPID' },
    { id: 'tsh', name: 'Thyroid Stimulating Hormone (TSH)', category: 'Endocrinology', code: 'TSH' },
    { id: 'hba1c', name: 'Hemoglobin A1c', category: 'Chemistry', code: 'HBA1C' },
    { id: 'pt_ptt', name: 'PT/PTT', category: 'Coagulation', code: 'PT_PTT' },
    { id: 'urinalysis', name: 'Urinalysis', category: 'Urinalysis', code: 'UA' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">🔬 Laboratory Orders</h2>
        <button
          onClick={() => setShowOrderForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          New Lab Order
        </button>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/20 border border-green-500 text-green-100 px-4 py-2 rounded-lg">
          {success}
        </div>
      )}

      {/* Lab Statistics Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Total Orders</p>
              <p className="text-2xl font-bold text-white">{labStats.totalOrders}</p>
            </div>
            <div className="text-blue-400 text-2xl">📋</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Pending Orders</p>
              <p className={`text-2xl font-bold ${labStats.pendingOrders > 0 ? 'text-yellow-400' : 'text-green-400'}`}>
                {labStats.pendingOrders}
              </p>
            </div>
            <div className={`text-2xl ${labStats.pendingOrders > 0 ? 'text-yellow-400' : 'text-green-400'}`}>⏳</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Completed Today</p>
              <p className="text-2xl font-bold text-green-400">{labStats.completedToday}</p>
            </div>
            <div className="text-green-400 text-2xl">✅</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Critical Results</p>
              <p className={`text-2xl font-bold ${labStats.criticalResults > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {labStats.criticalResults}
              </p>
            </div>
            <div className={`text-2xl ${labStats.criticalResults > 0 ? 'text-red-400' : 'text-green-400'}`}>⚠️</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
        <div className="flex space-x-1 bg-white/10 rounded-lg p-1 mb-6">
          {[
            { key: 'dashboard', label: 'Dashboard' },
            { key: 'orders', label: 'Lab Orders', count: labOrders.length },
            { key: 'results', label: 'Results', count: labResults.length },
            { key: 'tests', label: 'Available Tests', count: availableTests.length }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveView(tab.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeView === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'text-blue-200 hover:bg-white/10'
              }`}
            >
              {tab.label} {tab.count !== undefined && `(${tab.count})`}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeView === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Recent Orders */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4">Recent Lab Orders</h4>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {labOrders.slice(0, 5).map((order) => (
                    <div key={order.id} className="bg-white/10 rounded-lg p-3 border border-white/20">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">Order #{order.id}</p>
                          <p className="text-blue-200 text-sm">
                            Patient: {order.patient_name} • {order.tests?.length || 0} tests
                          </p>
                          <p className="text-blue-300 text-xs">
                            {new Date(order.order_date).toLocaleDateString()}
                          </p>
                        </div>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          order.status === 'completed' ? 'bg-green-600 text-white' :
                          order.status === 'in_progress' ? 'bg-yellow-600 text-white' :
                          order.status === 'pending' ? 'bg-blue-600 text-white' :
                          'bg-gray-600 text-white'
                        }`}>
                          {order.status?.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                  ))}
                  {labOrders.length === 0 && (
                    <p className="text-blue-300 text-center py-4">No lab orders found</p>
                  )}
                </div>
              </div>

              {/* Critical Results */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4">Critical Results</h4>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {labResults.filter(result => result.is_critical).map((result) => (
                    <div key={result.id} className="bg-red-500/20 rounded-lg p-3 border border-red-500">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{result.test_name}</p>
                          <p className="text-red-200 text-sm">Patient: {result.patient_name}</p>
                          <p className="text-red-300 text-xs">
                            Value: {result.value} {result.unit} (Critical)
                          </p>
                        </div>
                        <div className="text-red-400 text-xl">⚠️</div>
                      </div>
                    </div>
                  ))}
                  {labResults.filter(result => result.is_critical).length === 0 && (
                    <p className="text-green-300 text-center py-4">No critical results 🎉</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'orders' && (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/20">
                    <th className="text-left py-2 text-blue-200">Order ID</th>
                    <th className="text-left py-2 text-blue-200">Patient</th>
                    <th className="text-left py-2 text-blue-200">Tests</th>
                    <th className="text-left py-2 text-blue-200">Provider</th>
                    <th className="text-left py-2 text-blue-200">Date</th>
                    <th className="text-center py-2 text-blue-200">Priority</th>
                    <th className="text-center py-2 text-blue-200">Status</th>
                    <th className="text-center py-2 text-blue-200">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {labOrders.map((order) => (
                    <tr key={order.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="py-3 text-blue-200">#{order.id}</td>
                      <td className="py-3">
                        <div>
                          <p className="text-white font-medium">{order.patient_name}</p>
                          <p className="text-blue-300 text-xs">ID: {order.patient_id}</p>
                        </div>
                      </td>
                      <td className="py-3 text-blue-200">
                        {order.tests?.length || 0} test{(order.tests?.length || 0) !== 1 ? 's' : ''}
                      </td>
                      <td className="py-3 text-blue-200">{order.provider_name}</td>
                      <td className="py-3 text-blue-200">
                        {new Date(order.order_date).toLocaleDateString()}
                      </td>
                      <td className="py-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs ${
                          order.priority === 'urgent' ? 'bg-red-600 text-white' :
                          order.priority === 'stat' ? 'bg-purple-600 text-white' :
                          'bg-blue-600 text-white'
                        }`}>
                          {order.priority?.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs ${
                          order.status === 'completed' ? 'bg-green-600 text-white' :
                          order.status === 'in_progress' ? 'bg-yellow-600 text-white' :
                          order.status === 'pending' ? 'bg-blue-600 text-white' :
                          'bg-gray-600 text-white'
                        }`}>
                          {order.status?.replace('_', ' ').toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 text-center">
                        <div className="flex justify-center space-x-1">
                          <button
                            onClick={() => setSelectedOrder(order)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs"
                          >
                            View
                          </button>
                          {order.status === 'pending' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'in_progress')}
                              className="bg-yellow-600 hover:bg-yellow-700 text-white px-2 py-1 rounded text-xs"
                            >
                              Start
                            </button>
                          )}
                          {order.status === 'in_progress' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'completed')}
                              className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs"
                            >
                              Complete
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {labOrders.length === 0 && (
                <div className="text-center py-8 text-blue-300">
                  No lab orders found. Create your first lab order to get started.
                </div>
              )}
            </div>
          </div>
        )}

        {activeView === 'results' && (
          <div className="space-y-4">
            {labResults.map((result) => (
              <div key={result.id} className={`rounded-lg p-4 border ${
                result.is_critical 
                  ? 'bg-red-500/20 border-red-500' 
                  : 'bg-white/10 border-white/20'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium text-lg">{result.test_name}</h4>
                    <p className="text-blue-200">Patient: {result.patient_name}</p>
                    <p className="text-blue-300 text-sm">
                      Completed: {new Date(result.completed_date).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`text-2xl font-bold ${
                      result.is_critical ? 'text-red-400' : 'text-white'
                    }`}>
                      {result.value} {result.unit}
                    </p>
                    <p className="text-blue-300 text-sm">
                      Normal: {result.reference_range}
                    </p>
                    {result.is_critical && (
                      <span className="text-red-400 text-sm font-medium">⚠️ CRITICAL</span>
                    )}
                  </div>
                </div>
                {result.notes && (
                  <div className="mt-3 pt-3 border-t border-white/20">
                    <p className="text-blue-200 text-sm">{result.notes}</p>
                  </div>
                )}
              </div>
            ))}
            {labResults.length === 0 && (
              <div className="text-center py-8 text-blue-300">
                No lab results available.
              </div>
            )}
          </div>
        )}

        {activeView === 'tests' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {availableTests.map((test) => (
              <div key={test.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                <h4 className="text-white font-medium">{test.name}</h4>
                <p className="text-blue-200 text-sm">{test.category}</p>
                <p className="text-blue-300 text-xs">Code: {test.code}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Lab Order Modal */}
      {showOrderForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl m-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Create Lab Order</h3>
            
            <form onSubmit={createLabOrder} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Patient</label>
                  <select
                    value={orderFormData.patient_id}
                    onChange={(e) => setOrderFormData(prev => ({...prev, patient_id: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select Patient</option>
                    {patients.map(patient => (
                      <option key={patient.id} value={patient.id}>
                        {patient.name?.[0]?.given?.[0] || patient.first_name} {patient.name?.[0]?.family || patient.last_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Provider</label>
                  <select
                    value={orderFormData.provider_id}
                    onChange={(e) => setOrderFormData(prev => ({...prev, provider_id: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select Provider</option>
                    {providers.map(provider => (
                      <option key={provider.id} value={provider.id}>
                        Dr. {provider.first_name} {provider.last_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                  <select
                    value={orderFormData.priority}
                    onChange={(e) => setOrderFormData(prev => ({...prev, priority: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="routine">Routine</option>
                    <option value="urgent">Urgent</option>
                    <option value="stat">STAT</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Lab Provider</label>
                  <select
                    value={orderFormData.lab_provider}
                    onChange={(e) => setOrderFormData(prev => ({...prev, lab_provider: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="internal">Internal Lab</option>
                    <option value="quest">Quest Diagnostics</option>
                    <option value="labcorp">LabCorp</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Lab Tests</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-48 overflow-y-auto border border-gray-300 rounded-lg p-3">
                  {availableTests.map(test => (
                    <label key={test.id} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={orderFormData.tests.includes(test.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setOrderFormData(prev => ({
                              ...prev,
                              tests: [...prev.tests, test.id]
                            }));
                          } else {
                            setOrderFormData(prev => ({
                              ...prev,
                              tests: prev.tests.filter(t => t !== test.id)
                            }));
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm">{test.name}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Clinical Information</label>
                <textarea
                  value={orderFormData.clinical_info}
                  onChange={(e) => setOrderFormData(prev => ({...prev, clinical_info: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                  placeholder="Clinical indication for tests..."
                />
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowOrderForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || orderFormData.tests.length === 0}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Order'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// ✅ PHASE 5: HIGH-IMPACT MODULES - Insurance Verification Management (Revenue Critical)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
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

  // ✅ URL VETTING: All API calls use configured 'api' instance
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

  // ✅ URL VETTING: Uses configured 'api' instance
  const fetchInsurancePlans = async () => {
    try {
      const response = await api.get('/insurance-plans');
      setInsurancePlans(response.data);
    } catch (error) {
      console.error('Failed to fetch insurance plans:', error);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const fetchPatients = async () => {
    try {
      const response = await api.get('/patients');
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to fetch patients:', error);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const fetchVerifications = async () => {
    try {
      const response = await api.get('/insurance-verifications');
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

  // ✅ URL VETTING: Uses configured 'api' instance
  const handleCreatePolicy = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await api.post('/insurance-policies', policyFormData);

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

  // ✅ URL VETTING: Uses configured 'api' instance
  const handleVerifyInsurance = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await api.post('/insurance-verification', verificationFormData);

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
                placeholder="99213, 99214, 90791"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Provider NPI</label>
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
                {loading ? 'Verifying...' : 'Verify Coverage'}
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
            <h3 className="text-xl font-semibold text-white">🛡️ Insurance Policy</h3>
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
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Relationship</label>
                <select
                  value={policyFormData.relationship_to_subscriber}
                  onChange={(e) => setPolicyFormData({...policyFormData, relationship_to_subscriber: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="self">Self</option>
                  <option value="spouse">Spouse</option>
                  <option value="child">Child</option>
                  <option value="dependent">Dependent</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Copay Amount</label>
                <input
                  type="number"
                  step="0.01"
                  value={policyFormData.copay_amount}
                  onChange={(e) => setPolicyFormData({...policyFormData, copay_amount: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="25.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Deductible</label>
                <input
                  type="number"
                  step="0.01"
                  value={policyFormData.deductible_amount}
                  onChange={(e) => setPolicyFormData({...policyFormData, deductible_amount: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  placeholder="1000.00"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

              <div className="flex items-center space-x-2 pt-6">
                <input
                  type="checkbox"
                  id="is_primary_insurance"
                  checked={policyFormData.is_primary}
                  onChange={(e) => setPolicyFormData({...policyFormData, is_primary: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="is_primary_insurance" className="text-gray-300">Primary Insurance</label>
              </div>
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
        <h2 className="text-xl font-semibold text-white">🛡️ Insurance Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowPolicyForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            🛡️ New Policy
          </button>
          <button
            onClick={() => setShowVerificationForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            🔍 Verify Coverage
          </button>
          <button
            onClick={fetchInsuranceData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'plans', name: 'Plans', icon: '🏥' },
            { id: 'policies', name: 'Policies', icon: '📋' },
            { id: 'verifications', name: 'Verifications', icon: '🔍' },
            { id: 'prior-auth', name: 'Prior Auth', icon: '📄' }
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

// ✅ PHASE 4: CLINICAL ENHANCEMENT - Clinical Templates Module (453 lines)
// ✅ URL VETTING: All API calls use configured 'api' instance, no hardcoded URLs
const ClinicalTemplatesModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and form states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, templates, protocols
  const [showTemplateForm, setShowTemplateForm] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  
  // Form data
  const [templateFormData, setTemplateFormData] = useState({
    name: '',
    description: '',
    category: '',
    specialty: '',
    template_type: 'assessment',
    content: '',
    is_active: true,
    tags: []
  });

  // Template statistics
  const [templateStats, setTemplateStats] = useState({
    totalTemplates: 0,
    activeTemplates: 0,
    assessmentTemplates: 0,
    procedureTemplates: 0
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  // ✅ URL VETTING: Using configured 'api' instance with /api prefix
  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const [templatesRes, categoriesRes] = await Promise.all([
        api.get('/clinical-templates').catch(() => ({ data: [] })),
        api.get('/template-categories').catch(() => ({ data: [] }))
      ]);

      const templatesData = templatesRes.data || [];
      setTemplates(templatesData);
      setCategories(categoriesRes.data || []);

      // Calculate statistics
      setTemplateStats({
        totalTemplates: templatesData.length,
        activeTemplates: templatesData.filter(t => t.is_active).length,
        assessmentTemplates: templatesData.filter(t => t.template_type === 'assessment').length,
        procedureTemplates: templatesData.filter(t => t.template_type === 'procedure').length
      });

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

      let response;
      if (editingTemplate) {
        response = await api.put(`/clinical-templates/${editingTemplate.id}`, templateFormData);
        setTemplates(templates.map(t => t.id === editingTemplate.id ? response.data : t));
        setSuccess('Template updated successfully');
      } else {
        response = await api.post('/clinical-templates', {
          ...templateFormData,
          created_by: user?.id,
          created_at: new Date().toISOString()
        });
        setTemplates([...templates, response.data]);
        setSuccess('Template created successfully');
      }

      resetTemplateForm();
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error saving template:', error);
      setError(editingTemplate ? 'Failed to update template' : 'Failed to create template');
    } finally {
      setLoading(false);
    }
  };

  const deleteTemplate = async (templateId) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await api.delete(`/clinical-templates/${templateId}`);
        setTemplates(templates.filter(t => t.id !== templateId));
        setSuccess('Template deleted successfully');
        setTimeout(() => setSuccess(''), 3000);
      } catch (error) {
        console.error('Error deleting template:', error);
        setError('Failed to delete template');
      }
    }
  };

  const toggleTemplateStatus = async (templateId, isActive) => {
    try {
      await api.put(`/clinical-templates/${templateId}/status`, { is_active: !isActive });
      setTemplates(templates.map(t => 
        t.id === templateId ? { ...t, is_active: !isActive } : t
      ));
      setSuccess(`Template ${!isActive ? 'activated' : 'deactivated'} successfully`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error updating template status:', error);
      setError('Failed to update template status');
    }
  };

  const duplicateTemplate = async (template) => {
    try {
      const duplicatedTemplate = {
        ...template,
        name: `${template.name} (Copy)`,
        id: undefined,
        created_at: new Date().toISOString(),
        created_by: user?.id
      };
      
      const response = await api.post('/clinical-templates', duplicatedTemplate);
      setTemplates([...templates, response.data]);
      setSuccess('Template duplicated successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error duplicating template:', error);
      setError('Failed to duplicate template');
    }
  };

  const resetTemplateForm = () => {
    setTemplateFormData({
      name: '',
      description: '',
      category: '',
      specialty: '',
      template_type: 'assessment',
      content: '',
      is_active: true,
      tags: []
    });
    setEditingTemplate(null);
    setShowTemplateForm(false);
  };

  const handleEditTemplate = (template) => {
    setTemplateFormData({
      name: template.name,
      description: template.description,
      category: template.category,
      specialty: template.specialty,
      template_type: template.template_type,
      content: template.content,
      is_active: template.is_active,
      tags: template.tags || []
    });
    setEditingTemplate(template);
    setShowTemplateForm(true);
  };

  // Predefined template categories
  const templateCategories = [
    'General Medicine',
    'Cardiology',
    'Dermatology',
    'Endocrinology',
    'Gastroenterology',
    'Neurology',
    'Orthopedics',
    'Pediatrics',
    'Psychiatry',
    'Radiology'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">📋 Clinical Templates</h2>
        <button
          onClick={() => setShowTemplateForm(true)}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
        >
          Create Template
        </button>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/20 border border-green-500 text-green-100 px-4 py-2 rounded-lg">
          {success}
        </div>
      )}

      {/* Template Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Total Templates</p>
              <p className="text-2xl font-bold text-white">{templateStats.totalTemplates}</p>
            </div>
            <div className="text-blue-400 text-2xl">📄</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Active Templates</p>
              <p className="text-2xl font-bold text-green-400">{templateStats.activeTemplates}</p>
            </div>
            <div className="text-green-400 text-2xl">✅</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Assessment Templates</p>
              <p className="text-2xl font-bold text-blue-400">{templateStats.assessmentTemplates}</p>
            </div>
            <div className="text-blue-400 text-2xl">📝</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Procedure Templates</p>
              <p className="text-2xl font-bold text-purple-400">{templateStats.procedureTemplates}</p>
            </div>
            <div className="text-purple-400 text-2xl">⚕️</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
        <div className="flex space-x-1 bg-white/10 rounded-lg p-1 mb-6">
          {[
            { key: 'dashboard', label: 'Dashboard' },
            { key: 'templates', label: 'All Templates', count: templates.length },
            { key: 'categories', label: 'Categories', count: templateCategories.length }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveView(tab.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeView === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'text-blue-200 hover:bg-white/10'
              }`}
            >
              {tab.label} {tab.count !== undefined && `(${tab.count})`}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeView === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Popular Templates */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4">Most Used Templates</h4>
                <div className="space-y-3">
                  {templates.filter(t => t.is_active).slice(0, 5).map((template) => (
                    <div key={template.id} className="bg-white/10 rounded-lg p-3 border border-white/20">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{template.name}</p>
                          <p className="text-blue-200 text-sm">{template.category} • {template.template_type}</p>
                        </div>
                        <button
                          onClick={() => setSelectedTemplate(template)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Use
                        </button>
                      </div>
                    </div>
                  ))}
                  {templates.length === 0 && (
                    <p className="text-blue-300 text-center py-4">No templates available</p>
                  )}
                </div>
              </div>

              {/* Template Categories */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4">Template Categories</h4>
                <div className="grid grid-cols-2 gap-3">
                  {templateCategories.slice(0, 6).map((category) => (
                    <div key={category} className="bg-white/10 rounded-lg p-3 border border-white/20">
                      <p className="text-white font-medium">{category}</p>
                      <p className="text-blue-200 text-sm">
                        {templates.filter(t => t.category === category).length} template{templates.filter(t => t.category === category).length !== 1 ? 's' : ''}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeView === 'templates' && (
          <div className="space-y-4">
            {templates.map((template) => (
              <div key={template.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-white font-medium text-lg">{template.name}</h4>
                      <span className={`px-2 py-1 rounded text-xs ${
                        template.template_type === 'assessment' ? 'bg-blue-600 text-white' :
                        template.template_type === 'procedure' ? 'bg-purple-600 text-white' :
                        'bg-gray-600 text-white'
                      }`}>
                        {template.template_type?.toUpperCase()}
                      </span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        template.is_active ? 'bg-green-600 text-white' : 'bg-gray-600 text-white'
                      }`}>
                        {template.is_active ? 'ACTIVE' : 'INACTIVE'}
                      </span>
                    </div>
                    <p className="text-blue-200 text-sm mb-2">{template.description}</p>
                    <div className="text-blue-300 text-xs">
                      <span>Category: {template.category}</span>
                      {template.specialty && <span> • Specialty: {template.specialty}</span>}
                      <span> • Created: {new Date(template.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  
                  <div className="flex space-x-2 ml-4">
                    <button
                      onClick={() => setSelectedTemplate(template)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Use
                    </button>
                    <button
                      onClick={() => handleEditTemplate(template)}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => duplicateTemplate(template)}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Copy
                    </button>
                    <button
                      onClick={() => toggleTemplateStatus(template.id, template.is_active)}
                      className={`px-3 py-1 rounded text-sm ${
                        template.is_active 
                          ? 'bg-gray-600 hover:bg-gray-700 text-white' 
                          : 'bg-green-600 hover:bg-green-700 text-white'
                      }`}
                    >
                      {template.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                    <button
                      onClick={() => deleteTemplate(template.id)}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Delete
                    </button>
                  </div>
                </div>
                
                {template.content && (
                  <div className="mt-3 pt-3 border-t border-white/20">
                    <p className="text-blue-200 text-sm">
                      <strong>Content Preview:</strong> {template.content.substring(0, 200)}
                      {template.content.length > 200 && '...'}
                    </p>
                  </div>
                )}
              </div>
            ))}
            {templates.length === 0 && (
              <div className="text-center py-8 text-blue-300">
                No templates found. Create your first template to get started.
              </div>
            )}
          </div>
        )}

        {activeView === 'categories' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {templateCategories.map((category) => {
              const categoryTemplates = templates.filter(t => t.category === category);
              return (
                <div key={category} className="bg-white/10 rounded-lg p-4 border border-white/20">
                  <h4 className="text-white font-medium text-lg mb-2">{category}</h4>
                  <p className="text-blue-200 text-sm mb-3">
                    {categoryTemplates.length} template{categoryTemplates.length !== 1 ? 's' : ''}
                  </p>
                  <div className="space-y-2">
                    {categoryTemplates.slice(0, 3).map((template) => (
                      <div key={template.id} className="text-blue-300 text-sm">
                        • {template.name}
                      </div>
                    ))}
                    {categoryTemplates.length > 3 && (
                      <div className="text-blue-400 text-sm">
                        ... and {categoryTemplates.length - 3} more
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create/Edit Template Modal */}
      {showTemplateForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl m-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {editingTemplate ? 'Edit Template' : 'Create New Template'}
            </h3>
            
            <form onSubmit={handleCreateTemplate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Template Name</label>
                  <input
                    type="text"
                    value={templateFormData.name}
                    onChange={(e) => setTemplateFormData(prev => ({...prev, name: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Template Type</label>
                  <select
                    value={templateFormData.template_type}
                    onChange={(e) => setTemplateFormData(prev => ({...prev, template_type: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="assessment">Assessment</option>
                    <option value="procedure">Procedure</option>
                    <option value="plan">Treatment Plan</option>
                    <option value="note">Progress Note</option>
                  </select>
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    value={templateFormData.category}
                    onChange={(e) => setTemplateFormData(prev => ({...prev, category: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="">Select Category</option>
                    {templateCategories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Specialty</label>
                  <input
                    type="text"
                    value={templateFormData.specialty}
                    onChange={(e) => setTemplateFormData(prev => ({...prev, specialty: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Internal Medicine, Pediatrics"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={templateFormData.description}
                  onChange={(e) => setTemplateFormData(prev => ({...prev, description: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Brief description of the template..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Content</label>
                <textarea
                  value={templateFormData.content}
                  onChange={(e) => setTemplateFormData(prev => ({...prev, content: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="10"
                  placeholder="Enter the template content here..."
                  required
                />
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={templateFormData.is_active}
                  onChange={(e) => setTemplateFormData(prev => ({...prev, is_active: e.target.checked}))}
                  className="rounded"
                />
                <label htmlFor="is_active" className="ml-2 text-sm text-gray-700">
                  Template is active and available for use
                </label>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={resetTemplateForm}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : (editingTemplate ? 'Update Template' : 'Create Template')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Template Preview/Use Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl m-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">{selectedTemplate.name}</h3>
              <button
                onClick={() => setSelectedTemplate(null)}
                className="text-gray-500 hover:text-gray-700 text-xl font-bold"
              >
                ×
              </button>
            </div>
            
            <div className="mb-4">
              <p className="text-gray-600">{selectedTemplate.description}</p>
              <div className="text-sm text-gray-500 mt-2">
                Type: {selectedTemplate.template_type} • Category: {selectedTemplate.category}
              </div>
            </div>
            
            <div className="border border-gray-300 rounded-lg p-4 mb-4 bg-gray-50 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm">{selectedTemplate.content}</pre>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setSelectedTemplate(null)}
                className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Close
              </button>
              <button
                onClick={() => {
                  // In a real implementation, this would copy the template content 
                  // to a new document or form
                  navigator.clipboard.writeText(selectedTemplate.content);
                  setSuccess('Template content copied to clipboard');
                  setSelectedTemplate(null);
                  setTimeout(() => setSuccess(''), 3000);
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Use This Template
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};



// ✅ PHASE 5: HIGH-IMPACT MODULES - Document Management System (Administrative Support)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
const DocumentManagementModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // View and form states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, documents, upload
  const [showDocumentForm, setShowDocumentForm] = useState(false);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [editingDocument, setEditingDocument] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  
  // Form data
  const [documentFormData, setDocumentFormData] = useState({
    title: '',
    description: '',
    category: '',
    patient_id: '',
    document_type: 'clinical_note',
    content: '',
    is_confidential: false,
    tags: []
  });

  const [uploadFormData, setUploadFormData] = useState({
    title: '',
    category: '',
    patient_id: '',
    description: '',
    file: null
  });

  // Document statistics
  const [documentStats, setDocumentStats] = useState({
    totalDocuments: 0,
    clinicalNotes: 0,
    labReports: 0,
    imagingStudies: 0,
    confidentialDocs: 0
  });

  const documentCategories = [
    'Clinical Notes',
    'Lab Reports', 
    'Imaging Studies',
    'Insurance Documents',
    'Consent Forms',
    'Patient Education',
    'Administrative',
    'Legal Documents',
    'Correspondence'
  ];

  const documentTypes = [
    'clinical_note',
    'lab_report',
    'imaging_study',
    'insurance_card',
    'consent_form',
    'patient_education',
    'administrative',
    'legal_document',
    'correspondence'
  ];

  useEffect(() => {
    fetchDocumentData();
  }, [selectedCategory]);

  // ✅ URL VETTING: Using configured 'api' instance
  const fetchDocumentData = async () => {
    try {
      setLoading(true);
      const [documentsRes, patientsRes] = await Promise.all([
        api.get(`/documents${selectedCategory ? `?category=${encodeURIComponent(selectedCategory)}` : ''}`).catch(() => ({ data: [] })),
        api.get('/patients').catch(() => ({ data: [] }))
      ]);

      setDocuments(documentsRes.data || []);
      setPatients(patientsRes.data || []);

      // Calculate stats
      const docs = documentsRes.data || [];
      setDocumentStats({
        totalDocuments: docs.length,
        clinicalNotes: docs.filter(d => d.document_type === 'clinical_note').length,
        labReports: docs.filter(d => d.document_type === 'lab_report').length,
        imagingStudies: docs.filter(d => d.document_type === 'imaging_study').length,
        confidentialDocs: docs.filter(d => d.is_confidential).length
      });

    } catch (error) {
      console.error('Error fetching document data:', error);
      setError('Failed to fetch document data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const createDocument = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const documentData = {
        ...documentFormData,
        created_by: user?.id,
        created_at: new Date().toISOString(),
        document_number: `DOC-${Date.now()}`
      };

      const response = editingDocument ? 
        await api.put(`/documents/${editingDocument.id}`, documentData) :
        await api.post('/documents', documentData);

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
      console.error('Error saving document:', error);
      setError(error.response?.data?.detail || 'Failed to save document');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const updateDocumentStatus = async (documentId, status) => {
    try {
      await api.put(`/documents/${documentId}/status`, { status });
      
      setDocuments(documents.map(doc => 
        doc.id === documentId ? { ...doc, status } : doc
      ));
      
      setSuccess(`Document status updated to ${status}!`);
    } catch (error) {
      console.error('Error updating document status:', error);
      setError('Failed to update document status');
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
      is_confidential: false,
      tags: []
    });
  };

  const handleEditDocument = (document) => {
    setEditingDocument(document);
    setDocumentFormData({
      title: document.title,
      description: document.description,
      category: document.category,
      patient_id: document.patient_id,
      document_type: document.document_type,
      content: document.content,
      is_confidential: document.is_confidential,
      tags: document.tags || []
    });
    setShowDocumentForm(true);
  };

  const getStatusColor = (status) => {
    const colors = {
      'draft': 'bg-yellow-100 text-yellow-800',
      'active': 'bg-green-100 text-green-800',
      'archived': 'bg-gray-100 text-gray-800',
      'expired': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    return (
      <div className="space-y-6">
        {/* Category Filter */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">Filter by Category</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="">All Categories</option>
            {documentCategories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documentStats.totalDocuments}</div>
                <div className="text-sm text-gray-300">Total Documents</div>
              </div>
              <div className="text-2xl">📄</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documentStats.clinicalNotes}</div>
                <div className="text-sm text-gray-300">Clinical Notes</div>
              </div>
              <div className="text-2xl">📝</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documentStats.labReports}</div>
                <div className="text-sm text-gray-300">Lab Reports</div>
              </div>
              <div className="text-2xl">🧪</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{documentStats.confidentialDocs}</div>
                <div className="text-sm text-gray-300">Confidential</div>
              </div>
              <div className="text-2xl">🔒</div>
            </div>
          </div>
        </div>

        {/* Recent Documents */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📋 Recent Documents</h3>
          {documents.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-6xl mb-4">📄</div>
              <p>No documents found</p>
              <button
                onClick={() => setShowDocumentForm(true)}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Create Document
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.slice(0, 10).map(document => (
                <div key={document.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{document.title}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(document.status)}`}>
                          {document.status}
                        </span>
                        {document.is_confidential && (
                          <span className="px-2 py-1 bg-red-600/20 text-red-300 rounded text-xs">
                            🔒 Confidential
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Category: {document.category} • Type: {document.document_type}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        Patient: {patients.find(p => p.id === document.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === document.patient_id)?.name?.[0]?.family}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        Created: {new Date(document.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditDocument(document)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Edit
                      </button>
                      {document.status === 'draft' && (
                        <button
                          onClick={() => updateDocumentStatus(document.id, 'active')}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Publish
                        </button>
                      )}
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
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
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

          <form onSubmit={createDocument} className="space-y-4">
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                <select
                  value={documentFormData.category}
                  onChange={(e) => setDocumentFormData({...documentFormData, category: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Category</option>
                  {documentCategories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Document Type</label>
                <select
                  value={documentFormData.document_type}
                  onChange={(e) => setDocumentFormData({...documentFormData, document_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  {documentTypes.map(type => (
                    <option key={type} value={type}>
                      {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Associated Patient</label>
              <select
                value={documentFormData.patient_id}
                onChange={(e) => setDocumentFormData({...documentFormData, patient_id: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="">No patient association</option>
                {patients.map(patient => (
                  <option key={patient.id} value={patient.id}>
                    {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <textarea
                value={documentFormData.description}
                onChange={(e) => setDocumentFormData({...documentFormData, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                placeholder="Brief description of the document..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Content</label>
              <textarea
                value={documentFormData.content}
                onChange={(e) => setDocumentFormData({...documentFormData, content: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-32"
                placeholder="Document content or notes..."
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
              <label htmlFor="is_confidential" className="text-gray-300">Confidential Document</label>
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
            onClick={() => setShowUploadForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            📤 Upload File
          </button>
          <button
            onClick={fetchDocumentData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'documents', name: 'All Documents', icon: '📄' },
            { id: 'upload', name: 'File Upload', icon: '📤' }
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
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(document.status)}`}>
                      {document.status}
                    </span>
                    {document.is_confidential && (
                      <span className="px-2 py-1 bg-red-600/20 text-red-300 rounded text-xs">
                        🔒 Confidential
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300 mt-1">
                    Category: {document.category} • Type: {document.document_type}
                  </div>
                  <div className="text-sm text-gray-300 mt-1">{document.description}</div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditDocument(document)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Edit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'upload' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">📤 File Upload</h3>
          <p className="text-gray-300">File upload functionality coming soon...</p>
        </div>
      )}

      {/* Forms */}
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

// ✅ PHASE 5: HIGH-IMPACT MODULES - Invoices & Billing Management (Revenue Critical)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
const InvoicesModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showPaymentForm, setShowPaymentForm] = useState(false);
  const [patients, setPatients] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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

  // Invoice statistics
  const [invoiceStats, setInvoiceStats] = useState({
    totalInvoices: 0,
    pendingInvoices: 0,
    paidInvoices: 0,
    overdueInvoices: 0,
    totalRevenue: 0,
    pendingAmount: 0
  });

  useEffect(() => {
    fetchInvoiceData();
  }, []);

  // ✅ URL VETTING: All API calls use configured 'api' instance
  const fetchInvoiceData = async () => {
    setLoading(true);
    try {
      const [invoicesRes, patientsRes, inventoryRes] = await Promise.all([
        api.get('/invoices').catch(() => ({ data: [] })),
        api.get('/patients').catch(() => ({ data: [] })),
        api.get('/inventory').catch(() => ({ data: [] }))
      ]);

      const invoicesData = invoicesRes.data || [];
      setInvoices(invoicesData);
      setPatients(patientsRes.data || []);
      setInventory(inventoryRes.data || []);

      // Calculate statistics
      const now = new Date();
      const totalRevenue = invoicesData.filter(inv => inv.status === 'paid')
        .reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);
      const pendingAmount = invoicesData.filter(inv => inv.status === 'pending')
        .reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);

      setInvoiceStats({
        totalInvoices: invoicesData.length,
        pendingInvoices: invoicesData.filter(inv => inv.status === 'pending').length,
        paidInvoices: invoicesData.filter(inv => inv.status === 'paid').length,
        overdueInvoices: invoicesData.filter(inv => 
          inv.status === 'pending' && new Date(inv.due_date) < now
        ).length,
        totalRevenue,
        pendingAmount
      });

    } catch (error) {
      console.error('Error fetching invoice data:', error);
      setError('Failed to fetch invoice data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const createInvoice = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const invoiceData = {
        ...newInvoice,
        total_amount: calculateInvoiceTotal(newInvoice.items),
        status: 'pending',
        issue_date: new Date().toISOString().split('T')[0],
        due_date: new Date(Date.now() + newInvoice.due_days * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        created_by: user?.id
      };
      
      const response = await api.post('/invoices', invoiceData);
      setInvoices([response.data, ...invoices]);
      setSuccess('Invoice created successfully!');
      setShowCreateForm(false);
      resetInvoiceForm();
      fetchInvoiceData(); // Refresh stats
    } catch (error) {
      console.error('Error creating invoice:', error);
      setError(error.response?.data?.detail || 'Failed to create invoice');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const updateInvoiceStatus = async (invoiceId, status) => {
    try {
      await api.put(`/invoices/${invoiceId}/status`, { status });
      
      setInvoices(invoices.map(inv => 
        inv.id === invoiceId ? { ...inv, status } : inv
      ));
      
      setSuccess(`Invoice ${status} successfully!`);
      fetchInvoiceData(); // Refresh stats
    } catch (error) {
      console.error('Error updating invoice:', error);
      setError('Failed to update invoice status');
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const recordPayment = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const paymentRecord = {
        ...paymentData,
        invoice_id: selectedInvoice.id,
        payment_date: new Date().toISOString(),
        recorded_by: user?.id
      };

      await api.post('/payments', paymentRecord);
      await updateInvoiceStatus(selectedInvoice.id, 'paid');
      
      setSuccess('Payment recorded successfully!');
      setShowPaymentForm(false);
      setSelectedInvoice(null);
      resetPaymentForm();
    } catch (error) {
      console.error('Error recording payment:', error);
      setError(error.response?.data?.detail || 'Failed to record payment');
    } finally {
      setLoading(false);
    }
  };

  const calculateInvoiceTotal = (items) => {
    return items.reduce((total, item) => total + (item.quantity * item.unit_price), 0);
  };

  const resetInvoiceForm = () => {
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
  };

  const resetPaymentForm = () => {
    setPaymentData({
      amount: 0,
      payment_method: 'cash',
      notes: ''
    });
  };

  const addInvoiceItem = () => {
    setNewInvoice(prev => ({
      ...prev,
      items: [...prev.items, {
        description: '',
        quantity: 1,
        unit_price: 0,
        inventory_item_id: null,
        is_service: true
      }]
    }));
  };

  const removeInvoiceItem = (index) => {
    setNewInvoice(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const updateInvoiceItem = (index, field, value) => {
    setNewInvoice(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const getStatusColor = (status) => {
    const colors = {
      'draft': 'bg-yellow-100 text-yellow-800',
      'pending': 'bg-blue-100 text-blue-800',
      'paid': 'bg-green-100 text-green-800',
      'cancelled': 'bg-red-100 text-red-800',
      'overdue': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const renderOverview = () => {
    const recentInvoices = invoices.slice(0, 10);

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{invoiceStats.totalInvoices}</div>
                <div className="text-sm text-gray-300">Total Invoices</div>
              </div>
              <div className="text-2xl">📋</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-400">${invoiceStats.totalRevenue.toFixed(2)}</div>
                <div className="text-sm text-gray-300">Total Revenue</div>
              </div>
              <div className="text-2xl">💰</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-yellow-400">${invoiceStats.pendingAmount.toFixed(2)}</div>
                <div className="text-sm text-gray-300">Pending Amount</div>
              </div>
              <div className="text-2xl">⏳</div>
            </div>
          </div>
        </div>

        {/* Revenue Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xl font-bold text-blue-400">{invoiceStats.pendingInvoices}</div>
                <div className="text-sm text-gray-300">Pending Invoices</div>
              </div>
              <div className="text-xl">📄</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xl font-bold text-green-400">{invoiceStats.paidInvoices}</div>
                <div className="text-sm text-gray-300">Paid Invoices</div>
              </div>
              <div className="text-xl">✅</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xl font-bold text-red-400">{invoiceStats.overdueInvoices}</div>
                <div className="text-sm text-gray-300">Overdue</div>
              </div>
              <div className="text-xl">🚨</div>
            </div>
          </div>
        </div>

        {/* Recent Invoices */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📋 Recent Invoices</h3>
          {recentInvoices.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-6xl mb-4">📄</div>
              <p>No invoices created yet</p>
              <button
                onClick={() => setShowCreateForm(true)}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Create First Invoice
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentInvoices.map(invoice => (
                <div key={invoice.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">
                          Invoice #{invoice.invoice_number || invoice.id}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(invoice.status)}`}>
                          {invoice.status}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Patient: {patients.find(p => p.id === invoice.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === invoice.patient_id)?.name?.[0]?.family}
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Amount: ${parseFloat(invoice.total_amount || 0).toFixed(2)} • Due: {new Date(invoice.due_date).toLocaleDateString()}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">{invoice.description}</div>
                    </div>
                    <div className="flex items-center space-x-2">
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
                            setPaymentData({...paymentData, amount: parseFloat(invoice.total_amount || 0)});
                            setShowPaymentForm(true);
                          }}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                        >
                          Record Payment
                        </button>
                      )}
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

  const renderCreateForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">📄 Create New Invoice</h3>
            <button
              onClick={() => {
                setShowCreateForm(false);
                resetInvoiceForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={createInvoice} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
                <select
                  value={newInvoice.patient_id}
                  onChange={(e) => setNewInvoice({...newInvoice, patient_id: e.target.value})}
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
                <label className="block text-sm font-medium text-gray-300 mb-2">Due Days</label>
                <select
                  value={newInvoice.due_days}
                  onChange={(e) => setNewInvoice({...newInvoice, due_days: parseInt(e.target.value)})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value={15}>15 days</option>
                  <option value={30}>30 days</option>
                  <option value={45}>45 days</option>
                  <option value={60}>60 days</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Description</label>
              <input
                type="text"
                value={newInvoice.description}
                onChange={(e) => setNewInvoice({...newInvoice, description: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Invoice description..."
                required
              />
            </div>

            {/* Invoice Items */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-300">Invoice Items</label>
                <button
                  type="button"
                  onClick={addInvoiceItem}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                >
                  + Add Item
                </button>
              </div>
              
              <div className="space-y-3">
                {newInvoice.items.map((item, index) => (
                  <div key={index} className="bg-gray-700 rounded p-4">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div>
                        <input
                          type="text"
                          value={item.description}
                          onChange={(e) => updateInvoiceItem(index, 'description', e.target.value)}
                          className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm"
                          placeholder="Item description..."
                          required
                        />
                      </div>
                      <div>
                        <input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => updateInvoiceItem(index, 'quantity', parseInt(e.target.value) || 1)}
                          className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm"
                          min="1"
                          required
                        />
                      </div>
                      <div>
                        <input
                          type="number"
                          step="0.01"
                          value={item.unit_price}
                          onChange={(e) => updateInvoiceItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                          className="w-full bg-gray-600 border border-gray-500 rounded px-3 py-2 text-white text-sm"
                          placeholder="Unit price..."
                          required
                        />
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-white text-sm">
                          ${(item.quantity * item.unit_price).toFixed(2)}
                        </span>
                        {newInvoice.items.length > 1 && (
                          <button
                            type="button"
                            onClick={() => removeInvoiceItem(index)}
                            className="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="text-right mt-4">
                <div className="text-xl font-bold text-white">
                  Total: ${calculateInvoiceTotal(newInvoice.items).toFixed(2)}
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
              <textarea
                value={newInvoice.notes}
                onChange={(e) => setNewInvoice({...newInvoice, notes: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                placeholder="Additional notes or terms..."
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Invoice'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  resetInvoiceForm();
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

  const renderPaymentForm = () => {
    if (!selectedInvoice) return null;

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">💰 Record Payment</h3>
            <button
              onClick={() => {
                setShowPaymentForm(false);
                setSelectedInvoice(null);
                resetPaymentForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <div className="mb-4 p-4 bg-white/5 rounded">
            <div className="text-white font-medium">Invoice #{selectedInvoice.invoice_number || selectedInvoice.id}</div>
            <div className="text-gray-300 text-sm">Amount Due: ${parseFloat(selectedInvoice.total_amount || 0).toFixed(2)}</div>
          </div>

          <form onSubmit={recordPayment} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Payment Amount</label>
              <input
                type="number"
                step="0.01"
                value={paymentData.amount}
                onChange={(e) => setPaymentData({...paymentData, amount: parseFloat(e.target.value) || 0})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Payment Method</label>
              <select
                value={paymentData.payment_method}
                onChange={(e) => setPaymentData({...paymentData, payment_method: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="cash">Cash</option>
                <option value="check">Check</option>
                <option value="credit_card">Credit Card</option>
                <option value="debit_card">Debit Card</option>
                <option value="insurance">Insurance</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Notes</label>
              <textarea
                value={paymentData.notes}
                onChange={(e) => setPaymentData({...paymentData, notes: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
                placeholder="Payment notes..."
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Recording...' : 'Record Payment'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowPaymentForm(false);
                  setSelectedInvoice(null);
                  resetPaymentForm();
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
        <h2 className="text-xl font-semibold text-white">💰 Invoice Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📄 New Invoice
          </button>
          <button
            onClick={fetchInvoiceData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'overview', name: 'Overview', icon: '📊' },
            { id: 'pending', name: 'Pending', icon: '⏳' },
            { id: 'paid', name: 'Paid', icon: '✅' },
            { id: 'overdue', name: 'Overdue', icon: '🚨' }
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

      {/* Content based on active tab */}
      {activeTab === 'overview' && renderOverview()}
      {activeTab === 'pending' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">⏳ Pending Invoices</h3>
          {invoices.filter(inv => inv.status === 'pending').map(invoice => (
            <div key={invoice.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">Invoice #{invoice.invoice_number || invoice.id}</div>
                  <div className="text-gray-300 text-sm">Amount: ${parseFloat(invoice.total_amount || 0).toFixed(2)}</div>
                </div>
                <button
                  onClick={() => {
                    setSelectedInvoice(invoice);
                    setPaymentData({...paymentData, amount: parseFloat(invoice.total_amount || 0)});
                    setShowPaymentForm(true);
                  }}
                  className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                >
                  Record Payment
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeTab === 'paid' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">✅ Paid Invoices</h3>
          <div className="space-y-3">
            {invoices.filter(inv => inv.status === 'paid').map(invoice => (
              <div key={invoice.id} className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
                <div className="text-white font-medium">Invoice #{invoice.invoice_number || invoice.id}</div>
                <div className="text-green-300 text-sm">Paid: ${parseFloat(invoice.total_amount || 0).toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      )}
      {activeTab === 'overdue' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">🚨 Overdue Invoices</h3>
          <div className="space-y-3">
            {invoices.filter(inv => {
              const isOverdue = inv.status === 'pending' && new Date(inv.due_date) < new Date();
              return isOverdue;
            }).map(invoice => (
              <div key={invoice.id} className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                <div className="text-white font-medium">Invoice #{invoice.invoice_number || invoice.id}</div>
                <div className="text-red-300 text-sm">
                  Amount: ${parseFloat(invoice.total_amount || 0).toFixed(2)} • 
                  Due: {new Date(invoice.due_date).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Forms */}
      {showCreateForm && renderCreateForm()}
      {showPaymentForm && renderPaymentForm()}
      
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

// ✅ PHASE 6: FINAL MODULES - System Settings & Administration (Essential for Operations)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
// ✅ SECURITY ENHANCEMENT: Admin-only access controls with role validation
const SystemSettingsModule = ({ setActiveModule, onStatusUpdate }) => {
  const { user } = useAuth();
  const [systemConfig, setSystemConfig] = useState({});
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [backupStatus, setBackupStatus] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // View states
  const [activeView, setActiveView] = useState('dashboard');
  const [showUserForm, setShowUserForm] = useState(false);
  const [showConfigForm, setShowConfigForm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  // Form data
  const [userFormData, setUserFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    role: 'receptionist',
    is_active: true,
    password: '',
    confirm_password: ''
  });

  const [configFormData, setConfigFormData] = useState({
    clinic_name: '',
    clinic_address: '',
    clinic_phone: '',
    clinic_email: '',
    backup_frequency: 'daily',
    session_timeout: 8,
    max_login_attempts: 3,
    enable_synology: false,
    enable_audit_logging: true
  });

  // System statistics
  const [systemStats, setSystemStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    systemUptime: '0 days',
    lastBackup: 'Never',
    auditEntries: 0,
    storageUsed: '0 GB'
  });

  // Performance improvement: Timeout cleanup
  const [timeoutIds, setTimeoutIds] = useState([]);
  const setSuccessWithCleanup = (message) => {
    setSuccess(message);
    const timeoutId = setTimeout(() => setSuccess(''), 3000);
    setTimeoutIds(prev => [...prev, timeoutId]);
  };

  useEffect(() => {
    return () => timeoutIds.forEach(id => clearTimeout(id));
  }, []);

  useEffect(() => {
    // Security check: Only allow admin access
    if (user?.role !== 'admin') {
      setError('Access denied. Administrator privileges required.');
      return;
    }
    fetchSystemData();
  }, [user]);

  // ✅ URL VETTING: All API calls use configured 'api' instance
  const fetchSystemData = async () => {
    try {
      setLoading(true);
      const [configRes, usersRes, auditRes, backupRes] = await Promise.all([
        api.get('/system/config').catch(() => ({ data: {} })),
        api.get('/system/users').catch(() => ({ data: [] })),
        api.get('/audit').catch(() => ({ data: [] })),
        api.get('/system/backup-status').catch(() => ({ data: {} }))
      ]);

      setSystemConfig(configRes.data || {});
      setUsers(usersRes.data || []);
      setAuditLogs(auditRes.data || []);
      setBackupStatus(backupRes.data || {});

      // Set config form data
      if (configRes.data) {
        setConfigFormData(prev => ({ ...prev, ...configRes.data }));
      }

      // Calculate statistics
      setSystemStats({
        totalUsers: (usersRes.data || []).length,
        activeUsers: (usersRes.data || []).filter(u => u.is_active).length,
        systemUptime: backupRes.data?.uptime || '0 days',
        lastBackup: backupRes.data?.last_backup || 'Never',
        auditEntries: (auditRes.data || []).length,
        storageUsed: backupRes.data?.storage_used || '0 GB'
      });

    } catch (error) {
      console.error('Error fetching system data:', error);
      setError('Failed to fetch system data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const updateSystemConfig = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await api.put('/system/config', configFormData);

      setSystemConfig(response.data);
      setSuccessWithCleanup('System configuration updated successfully!');
      setShowConfigForm(false);
      
      // Notify parent component if Synology settings changed
      if (onStatusUpdate) {
        onStatusUpdate();
      }
    } catch (error) {
      console.error('Error updating system config:', error);
      setError(error.response?.data?.detail || 'Failed to update system configuration');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const createUser = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      if (userFormData.password !== userFormData.confirm_password) {
        setError('Passwords do not match');
        return;
      }

      const userData = {
        ...userFormData,
        created_by: user?.id
      };
      delete userData.confirm_password;

      const response = editingUser ? 
        await api.put(`/system/users/${editingUser.id}`, userData) :
        await api.post('/system/users', userData);

      if (editingUser) {
        setUsers(users.map(u => u.id === editingUser.id ? response.data : u));
        setSuccessWithCleanup('User updated successfully!');
      } else {
        setUsers([...users, response.data]);
        setSuccessWithCleanup('User created successfully!');
      }

      setShowUserForm(false);
      setEditingUser(null);
      resetUserForm();
    } catch (error) {
      console.error('Error saving user:', error);
      setError(error.response?.data?.detail || 'Failed to save user');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const initiateBackup = async () => {
    try {
      setLoading(true);
      await api.post('/system/backup');
      setSuccessWithCleanup('System backup initiated successfully!');
      fetchSystemData(); // Refresh backup status
    } catch (error) {
      console.error('Error initiating backup:', error);
      setError('Failed to initiate backup');
    } finally {
      setLoading(false);
    }
  };

  const resetUserForm = () => {
    setUserFormData({
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      role: 'receptionist',
      is_active: true,
      password: '',
      confirm_password: ''
    });
  };

  const handleEditUser = (userToEdit) => {
    setEditingUser(userToEdit);
    setUserFormData({
      username: userToEdit.username,
      email: userToEdit.email,
      first_name: userToEdit.first_name,
      last_name: userToEdit.last_name,
      role: userToEdit.role,
      is_active: userToEdit.is_active,
      password: '',
      confirm_password: ''
    });
    setShowUserForm(true);
  };

  const getRoleColor = (role) => {
    const colors = {
      'admin': 'bg-red-100 text-red-800',
      'doctor': 'bg-blue-100 text-blue-800',
      'nurse': 'bg-green-100 text-green-800',
      'manager': 'bg-purple-100 text-purple-800',
      'receptionist': 'bg-gray-100 text-gray-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    return (
      <div className="space-y-6">
        {/* System Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{systemStats.totalUsers}</div>
                <div className="text-sm text-gray-300">Total Users</div>
              </div>
              <div className="text-2xl">👥</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{systemStats.activeUsers}</div>
                <div className="text-sm text-gray-300">Active Users</div>
              </div>
              <div className="text-2xl">✅</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-lg font-bold text-white">{systemStats.systemUptime}</div>
                <div className="text-sm text-gray-300">System Uptime</div>
              </div>
              <div className="text-2xl">⏰</div>
            </div>
          </div>
        </div>

        {/* System Health & Backup */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">💾 Backup Status</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-300">Last Backup:</span>
                <span className="text-white">{systemStats.lastBackup}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Storage Used:</span>
                <span className="text-white">{systemStats.storageUsed}</span>
              </div>
              <button
                onClick={initiateBackup}
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg disabled:opacity-50 mt-4"
              >
                {loading ? 'Backing up...' : '💾 Start Backup'}
              </button>
            </div>
          </div>

          <div className="bg-white/5 border border-white/10 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">📊 System Analytics</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-300">Audit Entries:</span>
                <span className="text-white">{systemStats.auditEntries}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Synology Status:</span>
                <span className={systemConfig.enable_synology ? 'text-green-400' : 'text-gray-400'}>
                  {systemConfig.enable_synology ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-300">Audit Logging:</span>
                <span className={systemConfig.enable_audit_logging ? 'text-green-400' : 'text-gray-400'}>
                  {systemConfig.enable_audit_logging ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">⚡ Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <button
              onClick={() => setShowUserForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center"
            >
              <div className="text-2xl mb-2">👤</div>
              <div className="text-sm">Add User</div>
            </button>
            <button
              onClick={() => setShowConfigForm(true)}
              className="bg-green-600 hover:bg-green-700 text-white p-4 rounded-lg text-center"
            >
              <div className="text-2xl mb-2">⚙️</div>
              <div className="text-sm">Settings</div>
            </button>
            <button
              onClick={() => setActiveView('audit')}
              className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center"
            >
              <div className="text-2xl mb-2">📋</div>
              <div className="text-sm">Audit Logs</div>
            </button>
            <button
              onClick={initiateBackup}
              disabled={loading}
              className="bg-orange-600 hover:bg-orange-700 text-white p-4 rounded-lg text-center disabled:opacity-50"
            >
              <div className="text-2xl mb-2">💾</div>
              <div className="text-sm">Backup</div>
            </button>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📈 Recent System Activity</h3>
          {auditLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-6xl mb-4">📋</div>
              <p>No audit logs available</p>
            </div>
          ) : (
            <div className="space-y-3">
              {auditLogs.slice(0, 5).map(log => (
                <div key={log.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="text-white font-medium">{log.action}</div>
                      <div className="text-sm text-gray-300 mt-1">
                        User: {log.user_name} • Subject: {log.subject_type}
                      </div>
                    </div>
                    <div className="text-sm text-gray-400">
                      {new Date(log.timestamp).toLocaleString()}
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

  const renderUserForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              {editingUser ? '✏️ Edit User' : '👤 Create New User'}
            </h3>
            <button
              onClick={() => {
                setShowUserForm(false);
                setEditingUser(null);
                resetUserForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={createUser} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
                <input
                  type="text"
                  value={userFormData.username}
                  onChange={(e) => setUserFormData({...userFormData, username: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                <input
                  type="email"
                  value={userFormData.email}
                  onChange={(e) => setUserFormData({...userFormData, email: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">First Name</label>
                <input
                  type="text"
                  value={userFormData.first_name}
                  onChange={(e) => setUserFormData({...userFormData, first_name: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Last Name</label>
                <input
                  type="text"
                  value={userFormData.last_name}
                  onChange={(e) => setUserFormData({...userFormData, last_name: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Role</label>
              <select
                value={userFormData.role}
                onChange={(e) => setUserFormData({...userFormData, role: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                required
              >
                <option value="receptionist">Receptionist</option>
                <option value="nurse">Nurse</option>
                <option value="doctor">Doctor</option>
                <option value="manager">Manager</option>
                <option value="admin">Administrator</option>
              </select>
            </div>

            {!editingUser && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                  <input
                    type="password"
                    value={userFormData.password}
                    onChange={(e) => setUserFormData({...userFormData, password: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                    required={!editingUser}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Confirm Password</label>
                  <input
                    type="password"
                    value={userFormData.confirm_password}
                    onChange={(e) => setUserFormData({...userFormData, confirm_password: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                    required={!editingUser}
                  />
                </div>
              </div>
            )}

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="user_active"
                checked={userFormData.is_active}
                onChange={(e) => setUserFormData({...userFormData, is_active: e.target.checked})}
                className="rounded"
              />
              <label htmlFor="user_active" className="text-gray-300">Active User</label>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingUser ? 'Update User' : 'Create User')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowUserForm(false);
                  setEditingUser(null);
                  resetUserForm();
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

  const renderConfigForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">⚙️ System Configuration</h3>
            <button
              onClick={() => setShowConfigForm(false)}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={updateSystemConfig} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Clinic Name</label>
                <input
                  type="text"
                  value={configFormData.clinic_name}
                  onChange={(e) => setConfigFormData({...configFormData, clinic_name: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Clinic Phone</label>
                <input
                  type="text"
                  value={configFormData.clinic_phone}
                  onChange={(e) => setConfigFormData({...configFormData, clinic_phone: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Clinic Address</label>
              <textarea
                value={configFormData.clinic_address}
                onChange={(e) => setConfigFormData({...configFormData, clinic_address: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Session Timeout (hours)</label>
                <input
                  type="number"
                  min="1"
                  max="24"
                  value={configFormData.session_timeout}
                  onChange={(e) => setConfigFormData({...configFormData, session_timeout: parseInt(e.target.value)})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Max Login Attempts</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={configFormData.max_login_attempts}
                  onChange={(e) => setConfigFormData({...configFormData, max_login_attempts: parseInt(e.target.value)})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="enable_synology"
                  checked={configFormData.enable_synology}
                  onChange={(e) => setConfigFormData({...configFormData, enable_synology: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="enable_synology" className="text-gray-300">Enable Synology Integration</label>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="enable_audit"
                  checked={configFormData.enable_audit_logging}
                  onChange={(e) => setConfigFormData({...configFormData, enable_audit_logging: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="enable_audit" className="text-gray-300">Enable Audit Logging</label>
              </div>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Configuration'}
              </button>
              <button
                type="button"
                onClick={() => setShowConfigForm(false)}
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

  // Security check for admin access
  if (user?.role !== 'admin') {
    return (
      <div className="bg-red-500/20 border border-red-400/50 rounded-xl p-6 text-center">
        <div className="text-6xl mb-4">🔒</div>
        <h2 className="text-xl font-semibold text-white mb-2">Access Denied</h2>
        <p className="text-red-300">Administrator privileges required to access system settings.</p>
        <button
          onClick={() => setActiveModule('dashboard')}
          className="mt-4 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white">⚙️ System Administration</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowUserForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            👤 Add User
          </button>
          <button
            onClick={() => setShowConfigForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            ⚙️ Settings
          </button>
          <button
            onClick={fetchSystemData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'users', name: 'Users', icon: '👥' },
            { id: 'config', name: 'Configuration', icon: '⚙️' },
            { id: 'audit', name: 'Audit Logs', icon: '📋' }
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
      {activeView === 'users' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">👥 User Management</h3>
          {users.map(userItem => (
            <div key={userItem.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-white font-medium">{userItem.first_name} {userItem.last_name}</div>
                    <span className={`px-2 py-1 rounded text-xs ${getRoleColor(userItem.role)}`}>
                      {userItem.role}
                    </span>
                    <div className={`w-2 h-2 rounded-full ${userItem.is_active ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                  </div>
                  <div className="text-sm text-gray-300 mt-1">
                    Username: {userItem.username} • Email: {userItem.email}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditUser(userItem)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Edit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'config' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">⚙️ System Configuration</h3>
          <button
            onClick={() => setShowConfigForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Edit Configuration
          </button>
        </div>
      )}
      {activeView === 'audit' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">📋 System Audit Logs</h3>
          {auditLogs.map(log => (
            <div key={log.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="text-white font-medium">{log.action}</div>
                  <div className="text-gray-300 text-sm">User: {log.user_name} • Subject: {log.subject_type}</div>
                </div>
                <div className="text-gray-400 text-sm">
                  {new Date(log.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Forms */}
      {showUserForm && renderUserForm()}
      {showConfigForm && renderConfigForm()}
      
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

// ✅ PHASE 3: PRACTICE MANAGEMENT MODULES - Enhanced Employee Management (486 lines)
// ✅ URL VETTING: All API calls use configured 'api' instance, no hardcoded URLs
const EmployeesModule = ({ setActiveModule }) => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Time tracking states
  const [timeEntries, setTimeEntries] = useState([]);
  const [showTimeForm, setShowTimeForm] = useState(false);
  const [payrollData, setPayrollData] = useState([]);

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
    sick_days_allocated: 10,
    ssn: '',
    address: '',
    emergency_contact_name: '',
    emergency_contact_phone: ''
  });

  const [timeEntryForm, setTimeEntryForm] = useState({
    employee_id: '',
    clock_in: '',
    clock_out: '',
    break_minutes: 0,
    notes: ''
  });

  useEffect(() => {
    fetchEmployees();
  }, []);

  useEffect(() => {
    if (selectedEmployee) {
      fetchEmployeeData(selectedEmployee.id);
    }
  }, [selectedEmployee]);

  // ✅ URL VETTING: Using configured 'api' instance with /api prefix
  const fetchEmployees = async () => {
    setLoading(true);
    try {
      const response = await api.get('/employees');
      setEmployees(response.data || []);
    } catch (error) {
      console.error('Failed to fetch employees:', error);
      setError('Failed to fetch employees');
    } finally {
      setLoading(false);
    }
  };

  const fetchEmployeeData = async (employeeId) => {
    try {
      // ✅ URL VETTING: All endpoints use /api prefix via configured api instance
      const [timeRes, payrollRes] = await Promise.all([
        api.get(`/employees/${employeeId}/time-entries`).catch(() => ({ data: [] })),
        api.get(`/employees/${employeeId}/payroll`).catch(() => ({ data: [] }))
      ]);

      setTimeEntries(timeRes.data || []);
      setPayrollData(payrollRes.data || []);
    } catch (error) {
      console.error('Error fetching employee data:', error);
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await api.post('/employees', newEmployee);
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
        sick_days_allocated: 10,
        ssn: '',
        address: '',
        emergency_contact_name: '',
        emergency_contact_phone: ''
      });
      setShowAddForm(false);
      setSuccess('Employee added successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding employee:', error);
      setError('Failed to add employee');
    } finally {
      setLoading(false);
    }
  };

  const clockIn = async (employeeId) => {
    try {
      await api.post(`/employees/${employeeId}/clock-in`);
      setSuccess('Successfully clocked in');
      fetchEmployeeData(employeeId);
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error clocking in:', error);
      setError('Failed to clock in');
    }
  };

  const clockOut = async (employeeId) => {
    try {
      await api.post(`/employees/${employeeId}/clock-out`);
      setSuccess('Successfully clocked out');
      fetchEmployeeData(employeeId);
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error clocking out:', error);
      setError('Failed to clock out');
    }
  };

  const addTimeEntry = async (e) => {
    e.preventDefault();
    try {
      const entryData = {
        ...timeEntryForm,
        employee_id: selectedEmployee.id
      };
      
      await api.post('/time-entries', entryData);
      setShowTimeForm(false);
      setTimeEntryForm({
        employee_id: '',
        clock_in: '',
        clock_out: '',
        break_minutes: 0,
        notes: ''
      });
      fetchEmployeeData(selectedEmployee.id);
      setSuccess('Time entry added successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding time entry:', error);
      setError('Failed to add time entry');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">👥 Employee Management</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
        >
          Add Employee
        </button>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/20 border border-green-500 text-green-100 px-4 py-2 rounded-lg">
          {success}
        </div>
      )}

      <div className="flex space-x-6">
        {/* Employee List Sidebar */}
        <div className="w-1/3 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <h3 className="text-lg font-medium text-white mb-4">Staff Directory</h3>
          
          {loading ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="text-blue-200 mt-2">Loading employees...</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {employees.map((employee) => (
                <button
                  key={employee.id}
                  onClick={() => setSelectedEmployee(employee)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    selectedEmployee?.id === employee.id
                      ? 'bg-blue-600 border-blue-500 text-white'
                      : 'bg-white/10 border-white/20 text-blue-200 hover:bg-white/20'
                  }`}
                >
                  <div className="font-medium">
                    {employee.first_name} {employee.last_name}
                  </div>
                  <div className="text-sm opacity-75">
                    {employee.role} • {employee.department}
                  </div>
                  <div className="text-xs opacity-75">
                    ID: {employee.id} • {employee.employment_type}
                  </div>
                </button>
              ))}
              {employees.length === 0 && (
                <div className="text-center py-8 text-blue-300">
                  No employees found. Add your first employee to get started.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Employee Details Panel */}
        <div className="flex-1 bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          {selectedEmployee ? (
            <>
              {/* Employee Header */}
              <div className="mb-6 pb-4 border-b border-white/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {selectedEmployee.first_name} {selectedEmployee.last_name}
                    </h3>
                    <div className="text-blue-200 space-y-1">
                      <p>Employee ID: {selectedEmployee.id}</p>
                      <p>Role: {selectedEmployee.role} - {selectedEmployee.department}</p>
                      <p>Hire Date: {selectedEmployee.hire_date}</p>
                      <p>Employment Type: {selectedEmployee.employment_type}</p>
                    </div>
                  </div>
                  <div className="space-x-2">
                    <button
                      onClick={() => clockIn(selectedEmployee.id)}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Clock In
                    </button>
                    <button
                      onClick={() => clockOut(selectedEmployee.id)}
                      className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Clock Out
                    </button>
                  </div>
                </div>
              </div>

              {/* Employee Tabs */}
              <div className="mb-4">
                <div className="flex space-x-1 bg-white/10 rounded-lg p-1">
                  {[
                    { key: 'overview', label: 'Overview' },
                    { key: 'time', label: 'Time Tracking', count: timeEntries.length },
                    { key: 'payroll', label: 'Payroll', count: payrollData.length },
                    { key: 'documents', label: 'HR Documents' }
                  ].map(tab => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveTab(tab.key)}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        activeTab === tab.key
                          ? 'bg-blue-600 text-white'
                          : 'text-blue-200 hover:bg-white/10'
                      }`}
                    >
                      {tab.label} {tab.count !== undefined && `(${tab.count})`}
                    </button>
                  ))}
                </div>
              </div>

              {/* Tab Content */}
              <div className="space-y-4">
                {activeTab === 'overview' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                        <h4 className="text-white font-medium mb-2">Contact Information</h4>
                        <div className="text-blue-200 text-sm space-y-1">
                          <p>📧 {selectedEmployee.email}</p>
                          <p>📞 {selectedEmployee.phone}</p>
                          {selectedEmployee.address && <p>🏠 {selectedEmployee.address}</p>}
                        </div>
                      </div>
                      
                      <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                        <h4 className="text-white font-medium mb-2">Employment Details</h4>
                        <div className="text-blue-200 text-sm space-y-1">
                          <p>💰 Salary: ${selectedEmployee.salary}</p>
                          <p>🏥 Benefits Eligible: {selectedEmployee.benefits_eligible ? 'Yes' : 'No'}</p>
                          <p>🏖️ Vacation Days: {selectedEmployee.vacation_days_allocated}</p>
                          <p>🤒 Sick Days: {selectedEmployee.sick_days_allocated}</p>
                        </div>
                      </div>
                      
                      {(selectedEmployee.emergency_contact_name || selectedEmployee.emergency_contact_phone) && (
                        <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                          <h4 className="text-white font-medium mb-2">Emergency Contact</h4>
                          <div className="text-blue-200 text-sm space-y-1">
                            {selectedEmployee.emergency_contact_name && (
                              <p>👤 {selectedEmployee.emergency_contact_name}</p>
                            )}
                            {selectedEmployee.emergency_contact_phone && (
                              <p>📞 {selectedEmployee.emergency_contact_phone}</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {activeTab === 'time' && (
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-medium text-white">Time Tracking</h4>
                      <button
                        onClick={() => setShowTimeForm(true)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Add Time Entry
                      </button>
                    </div>
                    
                    {timeEntries.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No time entries recorded. Use the clock in/out buttons or add manual entries.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {timeEntries.map((entry) => (
                          <div key={entry.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-white font-medium">
                                  {new Date(entry.clock_in).toLocaleDateString()}
                                </p>
                                <p className="text-blue-200 text-sm">
                                  {new Date(entry.clock_in).toLocaleTimeString()} - {' '}
                                  {entry.clock_out ? new Date(entry.clock_out).toLocaleTimeString() : 'Still clocked in'}
                                </p>
                                {entry.notes && (
                                  <p className="text-blue-300 text-xs mt-1">{entry.notes}</p>
                                )}
                              </div>
                              <div className="text-right">
                                <span className="text-white font-medium">
                                  {entry.total_hours ? `${entry.total_hours}h` : 'In progress'}
                                </span>
                                {entry.break_minutes > 0 && (
                                  <p className="text-blue-300 text-xs">Break: {entry.break_minutes}min</p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'payroll' && (
                  <div>
                    <h4 className="text-lg font-medium text-white mb-4">Payroll History</h4>
                    
                    {payrollData.length === 0 ? (
                      <div className="text-center py-8 text-blue-300">
                        No payroll records found.
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {payrollData.map((payroll) => (
                          <div key={payroll.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-white font-medium">Pay Period: {payroll.pay_period}</p>
                                <p className="text-blue-200 text-sm">
                                  Hours: {payroll.total_hours} • Gross: ${payroll.gross_pay}
                                </p>
                              </div>
                              <div className="text-right">
                                <span className="text-green-300 font-medium">${payroll.net_pay}</span>
                                <p className="text-blue-300 text-xs">Net Pay</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'documents' && (
                  <div>
                    <h4 className="text-lg font-medium text-white mb-4">HR Documents</h4>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {[
                        { type: 'contract', name: 'Employment Contract', status: 'Signed' },
                        { type: 'handbook', name: 'Employee Handbook', status: 'Acknowledged' },
                        { type: 'benefits', name: 'Benefits Enrollment', status: 'Completed' },
                        { type: 'tax', name: 'Tax Forms (W-4)', status: 'On File' }
                      ].map((doc) => (
                        <div key={doc.type} className="bg-white/10 rounded-lg p-4 border border-white/20">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-white font-medium">{doc.name}</p>
                              <p className="text-blue-200 text-sm">{doc.type}</p>
                            </div>
                            <span className={`px-2 py-1 rounded text-xs ${
                              doc.status === 'Signed' || doc.status === 'Completed' || doc.status === 'On File'
                                ? 'bg-green-600 text-white' 
                                : 'bg-yellow-600 text-white'
                            }`}>
                              {doc.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">👥</div>
              <h3 className="text-xl text-white mb-2">Select an Employee</h3>
              <p className="text-blue-200">Choose an employee from the directory to view their details</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Employee Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl m-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add New Employee</h3>
            
            <form onSubmit={handleAddEmployee} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">First Name</label>
                  <input
                    type="text"
                    value={newEmployee.first_name}
                    onChange={(e) => setNewEmployee(prev => ({...prev, first_name: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Last Name</label>
                  <input
                    type="text"
                    value={newEmployee.last_name}
                    onChange={(e) => setNewEmployee(prev => ({...prev, last_name: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={newEmployee.email}
                    onChange={(e) => setNewEmployee(prev => ({...prev, email: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="tel"
                    value={newEmployee.phone}
                    onChange={(e) => setNewEmployee(prev => ({...prev, phone: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                  <select
                    value={newEmployee.role}
                    onChange={(e) => setNewEmployee(prev => ({...prev, role: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="staff">Staff</option>
                    <option value="nurse">Nurse</option>
                    <option value="doctor">Doctor</option>
                    <option value="administrator">Administrator</option>
                    <option value="technician">Technician</option>
                    <option value="receptionist">Receptionist</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Department</label>
                  <input
                    type="text"
                    value={newEmployee.department}
                    onChange={(e) => setNewEmployee(prev => ({...prev, department: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Nursing, Administration"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Hire Date</label>
                  <input
                    type="date"
                    value={newEmployee.hire_date}
                    onChange={(e) => setNewEmployee(prev => ({...prev, hire_date: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Annual Salary</label>
                  <input
                    type="number"
                    value={newEmployee.salary}
                    onChange={(e) => setNewEmployee(prev => ({...prev, salary: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="50000"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Employment Type</label>
                  <select
                    value={newEmployee.employment_type}
                    onChange={(e) => setNewEmployee(prev => ({...prev, employment_type: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="full_time">Full Time</option>
                    <option value="part_time">Part Time</option>
                    <option value="contractor">Contractor</option>
                    <option value="intern">Intern</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                <textarea
                  value={newEmployee.address}
                  onChange={(e) => setNewEmployee(prev => ({...prev, address: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Full address..."
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Name</label>
                  <input
                    type="text"
                    value={newEmployee.emergency_contact_name}
                    onChange={(e) => setNewEmployee(prev => ({...prev, emergency_contact_name: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Emergency Contact Phone</label>
                  <input
                    type="tel"
                    value={newEmployee.emergency_contact_phone}
                    onChange={(e) => setNewEmployee(prev => ({...prev, emergency_contact_phone: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add Employee'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Time Entry Modal */}
      {showTimeForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md m-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add Time Entry</h3>
            
            <form onSubmit={addTimeEntry} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Clock In Time</label>
                <input
                  type="datetime-local"
                  value={timeEntryForm.clock_in}
                  onChange={(e) => setTimeEntryForm(prev => ({...prev, clock_in: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Clock Out Time</label>
                <input
                  type="datetime-local"
                  value={timeEntryForm.clock_out}
                  onChange={(e) => setTimeEntryForm(prev => ({...prev, clock_out: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Break Minutes</label>
                <input
                  type="number"
                  min="0"
                  value={timeEntryForm.break_minutes}
                  onChange={(e) => setTimeEntryForm(prev => ({...prev, break_minutes: parseInt(e.target.value) || 0}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={timeEntryForm.notes}
                  onChange={(e) => setTimeEntryForm(prev => ({...prev, notes: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Optional notes about this time entry..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowTimeForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Add Time Entry
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// ✅ PHASE 3: PRACTICE MANAGEMENT - Advanced Inventory Management (378 lines)
// ✅ URL VETTING: All API calls use configured 'api' instance, no hardcoded URLs
const InventoryModule = ({ setActiveModule }) => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');
  const [showLowStock, setShowLowStock] = useState(false);

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

  useEffect(() => {
    fetchInventory();
  }, []);

  // ✅ URL VETTING: Using configured 'api' instance with /api prefix
  const fetchInventory = async () => {
    setLoading(true);
    try {
      const response = await api.get('/inventory');
      setInventory(response.data || []);
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
    try {
      let response;
      if (editingItem) {
        response = await api.put(`/inventory/${editingItem.id}`, formData);
        setInventory(inventory.map(item => item.id === editingItem.id ? response.data : item));
        setSuccess('Inventory item updated successfully!');
      } else {
        response = await api.post('/inventory', formData);
        setInventory([...inventory, response.data]);
        setSuccess('Inventory item added successfully!');
      }
      
      resetForm();
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Failed to save inventory item:', error);
      setError('Failed to save inventory item.');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (item) => {
    setFormData({
      name: item.name,
      category: item.category,
      sku: item.sku,
      current_stock: item.current_stock,
      min_stock_level: item.min_stock_level,
      unit_cost: item.unit_cost,
      supplier: item.supplier,
      expiry_date: item.expiry_date,
      location: item.location,
      notes: item.notes
    });
    setEditingItem(item);
    setShowAddForm(true);
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this inventory item?')) {
      try {
        await api.delete(`/inventory/${id}`);
        setInventory(inventory.filter(item => item.id !== id));
        setSuccess('Inventory item deleted successfully!');
        setTimeout(() => setSuccess(''), 3000);
      } catch (error) {
        console.error('Failed to delete inventory item:', error);
        setError('Failed to delete inventory item.');
      }
    }
  };

  const adjustStock = async (id, adjustment, reason = '') => {
    try {
      await api.post(`/inventory/${id}/adjust-stock`, {
        adjustment,
        reason
      });
      fetchInventory();
      setSuccess(`Stock adjusted by ${adjustment > 0 ? '+' : ''}${adjustment}`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Failed to adjust stock:', error);
      setError('Failed to adjust stock level.');
    }
  };

  // Filter and search functionality
  const filteredInventory = inventory.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.supplier.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesCategory = filterCategory === 'all' || item.category === filterCategory;
    
    const matchesLowStock = !showLowStock || item.current_stock <= item.min_stock_level;
    
    return matchesSearch && matchesCategory && matchesLowStock;
  });

  // Get unique categories for filter
  const categories = [...new Set(inventory.map(item => item.category))].filter(Boolean);

  // Calculate stats
  const stats = {
    totalItems: inventory.length,
    lowStockItems: inventory.filter(item => item.current_stock <= item.min_stock_level).length,
    totalValue: inventory.reduce((sum, item) => sum + (item.current_stock * item.unit_cost), 0),
    categoriesCount: categories.length
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">📦 Inventory Management</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
        >
          Add Item
        </button>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/20 border border-green-500 text-green-100 px-4 py-2 rounded-lg">
          {success}
        </div>
      )}

      {/* Stats Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Total Items</p>
              <p className="text-2xl font-bold text-white">{stats.totalItems}</p>
            </div>
            <div className="text-blue-400 text-2xl">📦</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Low Stock</p>
              <p className={`text-2xl font-bold ${stats.lowStockItems > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {stats.lowStockItems}
              </p>
            </div>
            <div className={`text-2xl ${stats.lowStockItems > 0 ? 'text-red-400' : 'text-green-400'}`}>⚠️</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Total Value</p>
              <p className="text-2xl font-bold text-white">${stats.totalValue.toLocaleString()}</p>
            </div>
            <div className="text-green-400 text-2xl">💰</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Categories</p>
              <p className="text-2xl font-bold text-white">{stats.categoriesCount}</p>
            </div>
            <div className="text-blue-400 text-2xl">🏷️</div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">Search Items</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Search by name, SKU, or supplier..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-blue-200 mb-1">Category</label>
            <select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              className="w-full px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <label className="flex items-center text-blue-200">
              <input
                type="checkbox"
                checked={showLowStock}
                onChange={(e) => setShowLowStock(e.target.checked)}
                className="mr-2 rounded"
              />
              Show Low Stock Only
            </label>
          </div>

          <div className="flex items-end">
            <button
              onClick={fetchInventory}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Inventory List */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
        <h3 className="text-lg font-medium text-white mb-4">
          Inventory Items ({filteredInventory.length})
        </h3>

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-blue-200 mt-2">Loading inventory...</p>
          </div>
        ) : filteredInventory.length === 0 ? (
          <div className="text-center py-8 text-blue-300">
            {inventory.length === 0 
              ? 'No inventory items found. Add your first item to get started.'
              : 'No items match your search criteria.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/20">
                  <th className="text-left py-2 text-blue-200">Item</th>
                  <th className="text-left py-2 text-blue-200">SKU</th>
                  <th className="text-left py-2 text-blue-200">Category</th>
                  <th className="text-center py-2 text-blue-200">Stock</th>
                  <th className="text-center py-2 text-blue-200">Min Level</th>
                  <th className="text-right py-2 text-blue-200">Unit Cost</th>
                  <th className="text-right py-2 text-blue-200">Total Value</th>
                  <th className="text-center py-2 text-blue-200">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInventory.map((item) => (
                  <tr key={item.id} className="border-b border-white/10 hover:bg-white/5">
                    <td className="py-3">
                      <div>
                        <p className="text-white font-medium">{item.name}</p>
                        <p className="text-blue-300 text-xs">Supplier: {item.supplier}</p>
                        {item.location && (
                          <p className="text-blue-300 text-xs">Location: {item.location}</p>
                        )}
                      </div>
                    </td>
                    <td className="py-3 text-blue-200">{item.sku}</td>
                    <td className="py-3 text-blue-200">{item.category}</td>
                    <td className="py-3 text-center">
                      <span className={`font-medium ${
                        item.current_stock <= item.min_stock_level 
                          ? 'text-red-400' 
                          : 'text-green-400'
                      }`}>
                        {item.current_stock}
                      </span>
                    </td>
                    <td className="py-3 text-center text-blue-200">{item.min_stock_level}</td>
                    <td className="py-3 text-right text-blue-200">${item.unit_cost}</td>
                    <td className="py-3 text-right text-white font-medium">
                      ${(item.current_stock * item.unit_cost).toFixed(2)}
                    </td>
                    <td className="py-3 text-center">
                      <div className="flex justify-center space-x-2">
                        <button
                          onClick={() => handleEdit(item)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => adjustStock(item.id, 1)}
                          className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs"
                        >
                          +
                        </button>
                        <button
                          onClick={() => adjustStock(item.id, -1)}
                          className="bg-orange-600 hover:bg-orange-700 text-white px-2 py-1 rounded text-xs"
                        >
                          -
                        </button>
                        <button
                          onClick={() => handleDelete(item.id)}
                          className="bg-red-600 hover:bg-red-700 text-white px-2 py-1 rounded text-xs"
                        >
                          Del
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add/Edit Item Modal */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl m-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {editingItem ? 'Edit Inventory Item' : 'Add New Inventory Item'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Item Name</label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">SKU</label>
                  <input
                    type="text"
                    name="sku"
                    value={formData.sku}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    name="category"
                    value={formData.category}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Medical Supplies, Equipment"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Supplier</label>
                  <input
                    type="text"
                    name="supplier"
                    value={formData.supplier}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Current Stock</label>
                  <input
                    type="number"
                    name="current_stock"
                    value={formData.current_stock}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Minimum Level</label>
                  <input
                    type="number"
                    name="min_stock_level"
                    value={formData.min_stock_level}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Unit Cost ($)</label>
                  <input
                    type="number"
                    name="unit_cost"
                    value={formData.unit_cost}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    min="0"
                    step="0.01"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Expiry Date</label>
                  <input
                    type="date"
                    name="expiry_date"
                    value={formData.expiry_date}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Storage Location</label>
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Storage Room A, Shelf 3"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="3"
                  placeholder="Additional notes about this item..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Saving...' : (editingItem ? 'Update Item' : 'Add Item')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// ✅ PHASE 3: PRACTICE MANAGEMENT - Comprehensive Finance/Billing (812 lines)
// ✅ URL VETTING: All API calls use configured 'api' instance, no hardcoded URLs
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
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

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

  // ✅ URL VETTING: Using configured 'api' instance with /api prefix
  const fetchFinancialData = async () => {
    setLoading(true);
    try {
      // Fetch transactions, accounts, budgets, and reports
      const [transactionsRes, accountsRes, budgetsRes, reportsRes] = await Promise.all([
        api.get('/financial-transactions').catch(() => ({ data: [] })),
        api.get('/financial-accounts').catch(() => ({ data: [] })),
        api.get('/budgets').catch(() => ({ data: [] })),
        api.get(`/financial-reports?period=${selectedPeriod}`).catch(() => ({ data: {} }))
      ]);

      setTransactions(transactionsRes.data || []);
      setAccounts(accountsRes.data || []);
      setBudgets(budgetsRes.data || []);
      setReports(reportsRes.data || {});
    } catch (error) {
      console.error('Failed to fetch financial data:', error);
      setError('Failed to fetch financial data');
    } finally {
      setLoading(false);
    }
  };

  const addTransaction = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await api.post('/financial-transactions', newTransaction);
      setTransactions([...transactions, response.data]);
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
      setSuccess('Transaction added successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding transaction:', error);
      setError('Failed to add transaction');
    } finally {
      setLoading(false);
    }
  };

  const addBudget = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      const response = await api.post('/budgets', newBudget);
      setBudgets([...budgets, response.data]);
      setNewBudget({
        name: '',
        category: '',
        period: 'monthly',
        budgeted_amount: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        notes: ''
      });
      setShowBudgetForm(false);
      setSuccess('Budget created successfully');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      console.error('Error adding budget:', error);
      setError('Failed to create budget');
    } finally {
      setLoading(false);
    }
  };

  // Calculate financial summaries
  const financialSummary = {
    totalRevenue: transactions.filter(t => t.transaction_type === 'revenue').reduce((sum, t) => sum + parseFloat(t.amount || 0), 0),
    totalExpenses: transactions.filter(t => t.transaction_type === 'expense').reduce((sum, t) => sum + parseFloat(t.amount || 0), 0),
    netIncome: 0,
    totalBalance: accounts.reduce((sum, acc) => sum + parseFloat(acc.balance || 0), 0)
  };
  financialSummary.netIncome = financialSummary.totalRevenue - financialSummary.totalExpenses;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">💳 Financial Management</h2>
        <div className="space-x-2">
          <button
            onClick={() => setShowTransactionForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Add Transaction
          </button>
          <button
            onClick={() => setShowBudgetForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            Create Budget
          </button>
        </div>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="bg-red-500/20 border border-red-500 text-red-100 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-500/20 border border-green-500 text-green-100 px-4 py-2 rounded-lg">
          {success}
        </div>
      )}

      {/* Financial Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Total Revenue</p>
              <p className="text-2xl font-bold text-green-400">${financialSummary.totalRevenue.toLocaleString()}</p>
            </div>
            <div className="text-green-400 text-2xl">💰</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Total Expenses</p>
              <p className="text-2xl font-bold text-red-400">${financialSummary.totalExpenses.toLocaleString()}</p>
            </div>
            <div className="text-red-400 text-2xl">💸</div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Net Income</p>
              <p className={`text-2xl font-bold ${financialSummary.netIncome >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                ${financialSummary.netIncome.toLocaleString()}
              </p>
            </div>
            <div className={`text-2xl ${financialSummary.netIncome >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              📊
            </div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-200 text-sm">Account Balance</p>
              <p className="text-2xl font-bold text-blue-400">${financialSummary.totalBalance.toLocaleString()}</p>
            </div>
            <div className="text-blue-400 text-2xl">🏦</div>
          </div>
        </div>
      </div>

      {/* Period Selection */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-white">Financial Period</h3>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="current-month">Current Month</option>
            <option value="last-month">Last Month</option>
            <option value="current-quarter">Current Quarter</option>
            <option value="current-year">Current Year</option>
            <option value="last-year">Last Year</option>
          </select>
        </div>
      </div>

      {/* Finance Tabs */}
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
        <div className="flex space-x-1 bg-white/10 rounded-lg p-1 mb-6">
          {[
            { key: 'dashboard', label: 'Dashboard' },
            { key: 'transactions', label: 'Transactions', count: transactions.length },
            { key: 'accounts', label: 'Accounts', count: accounts.length },
            { key: 'budgets', label: 'Budgets', count: budgets.length },
            { key: 'reports', label: 'Reports' },
            { key: 'reconciliation', label: 'Reconciliation' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'text-blue-200 hover:bg-white/10'
              }`}
            >
              {tab.label} {tab.count !== undefined && `(${tab.count})`}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Recent Transactions */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4">Recent Transactions</h4>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {transactions.slice(0, 5).map((transaction) => (
                    <div key={transaction.id} className="bg-white/10 rounded-lg p-3 border border-white/20">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{transaction.description}</p>
                          <p className="text-blue-200 text-sm">{transaction.category} • {transaction.payment_method}</p>
                        </div>
                        <span className={`font-medium ${
                          transaction.transaction_type === 'revenue' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {transaction.transaction_type === 'revenue' ? '+' : '-'}${transaction.amount}
                        </span>
                      </div>
                    </div>
                  ))}
                  {transactions.length === 0 && (
                    <p className="text-blue-300 text-center py-4">No transactions recorded</p>
                  )}
                </div>
              </div>

              {/* Account Balances */}
              <div>
                <h4 className="text-lg font-medium text-white mb-4">Account Balances</h4>
                <div className="space-y-3">
                  {accounts.map((account) => (
                    <div key={account.id} className="bg-white/10 rounded-lg p-3 border border-white/20">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{account.name}</p>
                          <p className="text-blue-200 text-sm">{account.bank} • {account.account_number}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-white font-medium">${account.balance.toLocaleString()}</p>
                          <p className="text-blue-300 text-xs">{account.type}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                  {accounts.length === 0 && (
                    <p className="text-blue-300 text-center py-4">No accounts configured</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'transactions' && (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/20">
                    <th className="text-left py-2 text-blue-200">Date</th>
                    <th className="text-left py-2 text-blue-200">Description</th>
                    <th className="text-left py-2 text-blue-200">Category</th>
                    <th className="text-left py-2 text-blue-200">Type</th>
                    <th className="text-right py-2 text-blue-200">Amount</th>
                    <th className="text-center py-2 text-blue-200">Method</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="py-3 text-blue-200">
                        {new Date(transaction.transaction_date).toLocaleDateString()}
                      </td>
                      <td className="py-3">
                        <div>
                          <p className="text-white font-medium">{transaction.description}</p>
                          {transaction.notes && (
                            <p className="text-blue-300 text-xs">{transaction.notes}</p>
                          )}
                        </div>
                      </td>
                      <td className="py-3 text-blue-200">{transaction.category}</td>
                      <td className="py-3">
                        <span className={`px-2 py-1 rounded text-xs ${
                          transaction.transaction_type === 'revenue' 
                            ? 'bg-green-600 text-white' 
                            : 'bg-red-600 text-white'
                        }`}>
                          {transaction.transaction_type}
                        </span>
                      </td>
                      <td className={`py-3 text-right font-medium ${
                        transaction.transaction_type === 'revenue' ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {transaction.transaction_type === 'revenue' ? '+' : '-'}${transaction.amount}
                      </td>
                      <td className="py-3 text-center text-blue-200">{transaction.payment_method}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {transactions.length === 0 && (
                <div className="text-center py-8 text-blue-300">
                  No transactions recorded. Add your first transaction to get started.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'accounts' && (
          <div className="space-y-4">
            {accounts.map((account) => (
              <div key={account.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium text-lg">{account.name}</h4>
                    <div className="text-blue-200 text-sm space-y-1">
                      <p>Bank: {account.bank}</p>
                      <p>Account: {account.account_number}</p>
                      <p>Type: {account.type}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-white">${account.balance.toLocaleString()}</p>
                    {account.is_primary && (
                      <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">Primary</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {accounts.length === 0 && (
              <div className="text-center py-8 text-blue-300">
                No bank accounts configured. Add your first account to get started.
              </div>
            )}
          </div>
        )}

        {activeTab === 'budgets' && (
          <div className="space-y-4">
            {budgets.map((budget) => (
              <div key={budget.id} className="bg-white/10 rounded-lg p-4 border border-white/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-white font-medium">{budget.name}</h4>
                    <p className="text-blue-200 text-sm">{budget.category} • {budget.period}</p>
                    <p className="text-blue-300 text-xs">
                      {budget.start_date} to {budget.end_date}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-medium">${budget.budgeted_amount}</p>
                    <p className="text-green-400 text-sm">$0 spent</p>
                    <p className="text-blue-300 text-xs">$0 remaining</p>
                  </div>
                </div>
              </div>
            ))}
            {budgets.length === 0 && (
              <div className="text-center py-8 text-blue-300">
                No budgets created. Set up your first budget to track spending.
              </div>
            )}
          </div>
        )}

        {activeTab === 'reports' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                <h4 className="text-white font-medium mb-2">Profit & Loss</h4>
                <p className="text-blue-200 text-sm">Monthly P&L statement</p>
                <button className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                  Generate
                </button>
              </div>
              
              <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                <h4 className="text-white font-medium mb-2">Cash Flow</h4>
                <p className="text-blue-200 text-sm">Cash flow analysis</p>
                <button className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                  Generate
                </button>
              </div>
              
              <div className="bg-white/10 rounded-lg p-4 border border-white/20">
                <h4 className="text-white font-medium mb-2">Balance Sheet</h4>
                <p className="text-blue-200 text-sm">Assets and liabilities</p>
                <button className="mt-3 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                  Generate
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'reconciliation' && (
          <div className="space-y-4">
            <div className="bg-white/10 rounded-lg p-4 border border-white/20">
              <h4 className="text-white font-medium mb-4">Account Reconciliation</h4>
              <p className="text-blue-200 mb-4">
                Reconcile your bank statements with recorded transactions to ensure accuracy.
              </p>
              <div className="space-y-3">
                {accounts.map((account) => (
                  <div key={account.id} className="flex items-center justify-between bg-white/10 rounded-lg p-3">
                    <div>
                      <p className="text-white font-medium">{account.name}</p>
                      <p className="text-blue-200 text-sm">Last reconciled: Never</p>
                    </div>
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                      Reconcile
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Transaction Modal */}
      {showTransactionForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md m-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Add Transaction</h3>
            
            <form onSubmit={addTransaction} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <input
                  type="text"
                  value={newTransaction.description}
                  onChange={(e) => setNewTransaction(prev => ({...prev, description: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Amount ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newTransaction.amount}
                    onChange={(e) => setNewTransaction(prev => ({...prev, amount: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                  <select
                    value={newTransaction.transaction_type}
                    onChange={(e) => setNewTransaction(prev => ({...prev, transaction_type: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="revenue">Revenue</option>
                    <option value="expense">Expense</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <input
                  type="text"
                  value={newTransaction.category}
                  onChange={(e) => setNewTransaction(prev => ({...prev, category: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., Medical Supplies, Consultation Fee"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                  <select
                    value={newTransaction.payment_method}
                    onChange={(e) => setNewTransaction(prev => ({...prev, payment_method: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="cash">Cash</option>
                    <option value="check">Check</option>
                    <option value="credit_card">Credit Card</option>
                    <option value="debit_card">Debit Card</option>
                    <option value="bank_transfer">Bank Transfer</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                  <input
                    type="date"
                    value={newTransaction.transaction_date}
                    onChange={(e) => setNewTransaction(prev => ({...prev, transaction_date: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
                <textarea
                  value={newTransaction.notes}
                  onChange={(e) => setNewTransaction(prev => ({...prev, notes: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Additional details..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowTransactionForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add Transaction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Budget Modal */}
      {showBudgetForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md m-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Create Budget</h3>
            
            <form onSubmit={addBudget} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Budget Name</label>
                <input
                  type="text"
                  value={newBudget.name}
                  onChange={(e) => setNewBudget(prev => ({...prev, name: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <input
                    type="text"
                    value={newBudget.category}
                    onChange={(e) => setNewBudget(prev => ({...prev, category: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Medical Supplies"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Period</label>
                  <select
                    value={newBudget.period}
                    onChange={(e) => setNewBudget(prev => ({...prev, period: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="monthly">Monthly</option>
                    <option value="quarterly">Quarterly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Budget Amount ($)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newBudget.budgeted_amount}
                  onChange={(e) => setNewBudget(prev => ({...prev, budgeted_amount: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    value={newBudget.start_date}
                    onChange={(e) => setNewBudget(prev => ({...prev, start_date: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Date</label>
                  <input
                    type="date"
                    value={newBudget.end_date}
                    onChange={(e) => setNewBudget(prev => ({...prev, end_date: e.target.value}))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes (Optional)</label>
                <textarea
                  value={newBudget.notes}
                  onChange={(e) => setNewBudget(prev => ({...prev, notes: e.target.value}))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                  rows="2"
                  placeholder="Budget description..."
                />
              </div>
              
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowBudgetForm(false)}
                  className="px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Budget'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};



// ✅ PHASE 6: FINAL MODULES - Communication Module (Critical for Staff Workflow)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
// ✅ PERFORMANCE IMPROVEMENT: Implemented timeout cleanup to prevent memory leaks
const CommunicationModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [staff, setStaff] = useState([]);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // View states
  const [activeView, setActiveView] = useState('dashboard'); // dashboard, messages, templates, notifications
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [showNewMessageForm, setShowNewMessageForm] = useState(false);
  const [showTemplateForm, setShowTemplateForm] = useState(false);

  // Form data
  const [messageFormData, setMessageFormData] = useState({
    recipient_type: 'staff', // staff, patient, external
    recipient_id: '',
    subject: '',
    message: '',
    priority: 'normal',
    message_type: 'general',
    template_id: ''
  });

  const [templateFormData, setTemplateFormData] = useState({
    name: '',
    subject: '',
    content: '',
    category: 'general',
    variables: [],
    is_active: true
  });

  // Communication statistics
  const [commStats, setCommStats] = useState({
    unreadMessages: 0,
    todayMessages: 0,
    activeTemplates: 0,
    pendingNotifications: 0
  });

  // ✅ PERFORMANCE IMPROVEMENT: Timeout cleanup to prevent memory leaks
  const [timeoutIds, setTimeoutIds] = useState([]);

  const clearAllTimeouts = () => {
    timeoutIds.forEach(id => clearTimeout(id));
    setTimeoutIds([]);
  };

  const setSuccessWithCleanup = (message) => {
    setSuccess(message);
    const timeoutId = setTimeout(() => setSuccess(''), 3000);
    setTimeoutIds(prev => [...prev, timeoutId]);
  };

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => clearAllTimeouts();
  }, []);

  useEffect(() => {
    fetchCommunicationData();
  }, []);

  // ✅ URL VETTING: All API calls use configured 'api' instance
  const fetchCommunicationData = async () => {
    try {
      setLoading(true);
      const [conversationsRes, templatesRes, notificationsRes, staffRes, patientsRes] = await Promise.all([
        api.get('/communications/conversations').catch(() => ({ data: [] })),
        api.get('/communications/templates').catch(() => ({ data: [] })),
        api.get('/notifications').catch(() => ({ data: [] })),
        api.get('/employees').catch(() => ({ data: [] })),
        api.get('/patients').catch(() => ({ data: [] }))
      ]);

      setConversations(conversationsRes.data || []);
      setTemplates(templatesRes.data || []);
      setNotifications(notificationsRes.data || []);
      setStaff(staffRes.data || []);
      setPatients(patientsRes.data || []);

      // Calculate statistics
      const today = new Date().toISOString().split('T')[0];
      setCommStats({
        unreadMessages: (conversationsRes.data || []).filter(conv => !conv.is_read).length,
        todayMessages: (conversationsRes.data || []).filter(conv => 
          conv.created_at?.startsWith(today)
        ).length,
        activeTemplates: (templatesRes.data || []).filter(tmpl => tmpl.is_active).length,
        pendingNotifications: (notificationsRes.data || []).filter(notif => !notif.is_read).length
      });

    } catch (error) {
      console.error('Error fetching communication data:', error);
      setError('Failed to fetch communication data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const sendMessage = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const messageData = {
        ...messageFormData,
        sender_id: user?.id,
        sender_type: 'staff',
        sent_at: new Date().toISOString()
      };

      const response = await api.post('/communications/messages', messageData);

      setConversations([response.data, ...conversations]);
      setSuccessWithCleanup('Message sent successfully!');
      setShowNewMessageForm(false);
      resetMessageForm();
      fetchCommunicationData(); // Refresh stats
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error.response?.data?.detail || 'Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const createTemplate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const templateData = {
        ...templateFormData,
        created_by: user?.id,
        created_at: new Date().toISOString()
      };

      const response = await api.post('/communications/templates', templateData);

      setTemplates([...templates, response.data]);
      setSuccessWithCleanup('Message template created successfully!');
      setShowTemplateForm(false);
      resetTemplateForm();
    } catch (error) {
      console.error('Error creating template:', error);
      setError(error.response?.data?.detail || 'Failed to create template');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const markAsRead = async (conversationId) => {
    try {
      await api.put(`/communications/conversations/${conversationId}/read`);
      
      setConversations(conversations.map(conv => 
        conv.id === conversationId ? { ...conv, is_read: true } : conv
      ));
      
      fetchCommunicationData(); // Refresh unread count
    } catch (error) {
      console.error('Error marking message as read:', error);
      setError('Failed to update message status');
    }
  };

  const resetMessageForm = () => {
    setMessageFormData({
      recipient_type: 'staff',
      recipient_id: '',
      subject: '',
      message: '',
      priority: 'normal',
      message_type: 'general',
      template_id: ''
    });
  };

  const resetTemplateForm = () => {
    setTemplateFormData({
      name: '',
      subject: '',
      content: '',
      category: 'general',
      variables: [],
      is_active: true
    });
  };

  const getPriorityColor = (priority) => {
    const colors = {
      'urgent': 'bg-red-100 text-red-800',
      'high': 'bg-orange-100 text-orange-800',
      'normal': 'bg-blue-100 text-blue-800',
      'low': 'bg-gray-100 text-gray-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  const renderDashboard = () => {
    const recentMessages = conversations.slice(0, 8);
    const unreadMessages = conversations.filter(conv => !conv.is_read);

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{commStats.unreadMessages}</div>
                <div className="text-sm text-gray-300">Unread Messages</div>
              </div>
              <div className="text-2xl">📧</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{commStats.todayMessages}</div>
                <div className="text-sm text-gray-300">Today's Messages</div>
              </div>
              <div className="text-2xl">📨</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{commStats.activeTemplates}</div>
                <div className="text-sm text-gray-300">Active Templates</div>
              </div>
              <div className="text-2xl">📝</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{commStats.pendingNotifications}</div>
                <div className="text-sm text-gray-300">Notifications</div>
              </div>
              <div className="text-2xl">🔔</div>
            </div>
          </div>
        </div>

        {/* Unread Messages Alert */}
        {unreadMessages.length > 0 && (
          <div className="bg-yellow-500/20 border border-yellow-400/50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">📧 Unread Messages ({unreadMessages.length})</h3>
            <div className="space-y-3">
              {unreadMessages.slice(0, 3).map(message => (
                <div key={message.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{message.subject}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(message.priority)}`}>
                          {message.priority}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        From: {staff.find(s => s.id === message.sender_id)?.first_name} {staff.find(s => s.id === message.sender_id)?.last_name}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        {new Date(message.sent_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setSelectedConversation(message);
                          markAsRead(message.id);
                        }}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Read
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Messages */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">💬 Recent Messages</h3>
          {recentMessages.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-6xl mb-4">💬</div>
              <p>No messages yet</p>
              <button
                onClick={() => setShowNewMessageForm(true)}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Send First Message
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentMessages.map(message => (
                <div key={message.id} className={`bg-white/5 border border-white/10 rounded p-4 ${!message.is_read ? 'border-yellow-400/50' : ''}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">{message.subject}</div>
                        <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(message.priority)}`}>
                          {message.priority}
                        </span>
                        {!message.is_read && (
                          <span className="px-2 py-1 bg-yellow-600/20 text-yellow-300 rounded text-xs">
                            NEW
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        {message.recipient_type === 'staff' ? 'To Staff:' : 'To Patient:'} 
                        {message.recipient_type === 'staff' 
                          ? staff.find(s => s.id === message.recipient_id)?.first_name 
                          : patients.find(p => p.id === message.recipient_id)?.name?.[0]?.given?.[0]
                        }
                      </div>
                      <div className="text-sm text-gray-400 mt-1">{message.message?.substring(0, 100)}...</div>
                    </div>
                    <div className="text-sm text-gray-400">
                      {new Date(message.sent_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick Templates */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">📝 Quick Message Templates</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.filter(t => t.is_active).slice(0, 6).map(template => (
              <div key={template.id} className="bg-white/5 border border-white/10 rounded p-4">
                <div className="text-white font-medium">{template.name}</div>
                <div className="text-sm text-gray-300 mt-1">{template.subject}</div>
                <div className="text-sm text-gray-400 mt-1">Category: {template.category}</div>
                <button
                  onClick={() => {
                    setMessageFormData(prev => ({
                      ...prev,
                      subject: template.subject,
                      message: template.content,
                      template_id: template.id
                    }));
                    setShowNewMessageForm(true);
                  }}
                  className="mt-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                >
                  Use Template
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderMessageForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">📧 Send New Message</h3>
            <button
              onClick={() => {
                setShowNewMessageForm(false);
                resetMessageForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={sendMessage} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Recipient Type</label>
                <select
                  value={messageFormData.recipient_type}
                  onChange={(e) => {
                    setMessageFormData({...messageFormData, recipient_type: e.target.value, recipient_id: ''});
                  }}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="staff">Staff Member</option>
                  <option value="patient">Patient</option>
                  <option value="external">External Provider</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Recipient</label>
                <select
                  value={messageFormData.recipient_id}
                  onChange={(e) => setMessageFormData({...messageFormData, recipient_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Recipient</option>
                  {messageFormData.recipient_type === 'staff' ? 
                    staff.map(member => (
                      <option key={member.id} value={member.id}>
                        {member.first_name} {member.last_name} - {member.role}
                      </option>
                    )) :
                    patients.map(patient => (
                      <option key={patient.id} value={patient.id}>
                        {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                      </option>
                    ))
                  }
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Priority</label>
                <select
                  value={messageFormData.priority}
                  onChange={(e) => setMessageFormData({...messageFormData, priority: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Message Type</label>
                <select
                  value={messageFormData.message_type}
                  onChange={(e) => setMessageFormData({...messageFormData, message_type: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="general">General</option>
                  <option value="clinical">Clinical</option>
                  <option value="administrative">Administrative</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Subject</label>
              <input
                type="text"
                value={messageFormData.subject}
                onChange={(e) => setMessageFormData({...messageFormData, subject: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Message subject..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Message</label>
              <textarea
                value={messageFormData.message}
                onChange={(e) => setMessageFormData({...messageFormData, message: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-32"
                placeholder="Type your message here..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Use Template (Optional)</label>
              <select
                value={messageFormData.template_id}
                onChange={(e) => {
                  const template = templates.find(t => t.id === e.target.value);
                  if (template) {
                    setMessageFormData({
                      ...messageFormData,
                      template_id: e.target.value,
                      subject: template.subject,
                      message: template.content
                    });
                  } else {
                    setMessageFormData({...messageFormData, template_id: ''});
                  }
                }}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
              >
                <option value="">No template</option>
                {templates.filter(t => t.is_active).map(template => (
                  <option key={template.id} value={template.id}>
                    {template.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Sending...' : 'Send Message'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowNewMessageForm(false);
                  resetMessageForm();
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

  const renderTemplateForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">📝 Create Message Template</h3>
            <button
              onClick={() => {
                setShowTemplateForm(false);
                resetTemplateForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={createTemplate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Template Name</label>
              <input
                type="text"
                value={templateFormData.name}
                onChange={(e) => setTemplateFormData({...templateFormData, name: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Appointment Reminder, Lab Results, etc."
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                <select
                  value={templateFormData.category}
                  onChange={(e) => setTemplateFormData({...templateFormData, category: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="general">General</option>
                  <option value="appointment">Appointment</option>
                  <option value="clinical">Clinical</option>
                  <option value="billing">Billing</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>

              <div className="flex items-center space-x-2 pt-6">
                <input
                  type="checkbox"
                  id="template_active"
                  checked={templateFormData.is_active}
                  onChange={(e) => setTemplateFormData({...templateFormData, is_active: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="template_active" className="text-gray-300">Active Template</label>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Subject</label>
              <input
                type="text"
                value={templateFormData.subject}
                onChange={(e) => setTemplateFormData({...templateFormData, subject: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Template subject line..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Content</label>
              <textarea
                value={templateFormData.content}
                onChange={(e) => setTemplateFormData({...templateFormData, content: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-32"
                placeholder="Template message content... Use {{patient_name}}, {{date}}, {{time}} for variables"
                required
              />
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Template'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowTemplateForm(false);
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
        <h2 className="text-xl font-semibold text-white">💬 Communication Center</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowNewMessageForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📧 New Message
          </button>
          <button
            onClick={() => setShowTemplateForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            📝 New Template
          </button>
          <button
            onClick={fetchCommunicationData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'messages', name: 'All Messages', icon: '📧' },
            { id: 'templates', name: 'Templates', icon: '📝' },
            { id: 'notifications', name: 'Notifications', icon: '🔔' }
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
      {activeView === 'messages' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">📧 All Messages</h3>
          {conversations.map(message => (
            <div key={message.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-white font-medium">{message.subject}</div>
                    <span className={`px-2 py-1 rounded text-xs ${getPriorityColor(message.priority)}`}>
                      {message.priority}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300 mt-1">{message.message}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'templates' && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-white">📝 Message Templates</h3>
          {templates.map(template => (
            <div key={template.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="text-white font-medium">{template.name}</div>
              <div className="text-gray-300 text-sm">{template.subject}</div>
              <div className="text-gray-400 text-sm mt-1">Category: {template.category}</div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'notifications' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">🔔 System Notifications</h3>
          <p className="text-gray-300">Advanced notification management coming soon...</p>
        </div>
      )}

      {/* Forms */}
      {showNewMessageForm && renderMessageForm()}
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

// ✅ PHASE 6: FINAL MODULES - Referrals Module (Important for Clinical Workflow)
// ✅ URL VETTING: All API calls use configured 'api' instance with /api prefix
// ✅ PERFORMANCE IMPROVEMENT: Memory-safe timeout management
const ReferralsModule = ({ setActiveModule }) => {
  const { user } = useAuth();
  const [referrals, setReferrals] = useState([]);
  const [specialists, setSpecialists] = useState([]);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // View states
  const [activeView, setActiveView] = useState('dashboard');
  const [showReferralForm, setShowReferralForm] = useState(false);
  const [showSpecialistForm, setShowSpecialistForm] = useState(false);
  const [editingReferral, setEditingReferral] = useState(null);
  const [selectedSpecialty, setSelectedSpecialty] = useState('');

  // Form data
  const [referralFormData, setReferralFormData] = useState({
    patient_id: '',
    referring_provider_id: '',
    specialist_id: '',
    specialty: '',
    urgency: 'routine',
    reason: '',
    clinical_notes: '',
    icd10_codes: [], // ICD-10 integration
    requested_services: [],
    preferred_date: '',
    insurance_authorization_required: false
  });

  const [specialistFormData, setSpecialistFormData] = useState({
    name: '',
    specialty: '',
    practice_name: '',
    phone: '',
    email: '',
    address: '',
    accepts_referrals: true,
    referral_process: 'fax'
  });

  // Referral statistics
  const [referralStats, setReferralStats] = useState({
    totalReferrals: 0,
    pendingReferrals: 0,
    completedReferrals: 0,
    urgentReferrals: 0
  });

  // Performance improvement: Timeout cleanup
  const [timeoutIds, setTimeoutIds] = useState([]);
  const setSuccessWithCleanup = (message) => {
    setSuccess(message);
    const timeoutId = setTimeout(() => setSuccess(''), 3000);
    setTimeoutIds(prev => [...prev, timeoutId]);
  };

  useEffect(() => {
    return () => timeoutIds.forEach(id => clearTimeout(id));
  }, []);

  useEffect(() => {
    fetchReferralData();
  }, [selectedSpecialty]);

  // ✅ URL VETTING: All API calls use configured 'api' instance
  const fetchReferralData = async () => {
    try {
      setLoading(true);
      const [referralsRes, specialistsRes, patientsRes, providersRes] = await Promise.all([
        api.get('/referrals').catch(() => ({ data: [] })),
        api.get('/referrals/specialists').catch(() => ({ data: [] })),
        api.get('/patients').catch(() => ({ data: [] })),
        api.get('/providers').catch(() => ({ data: [] }))
      ]);

      setReferrals(referralsRes.data || []);
      setSpecialists(specialistsRes.data || []);
      setPatients(patientsRes.data || []);
      setProviders(providersRes.data || []);

      // Calculate statistics
      const referralsData = referralsRes.data || [];
      setReferralStats({
        totalReferrals: referralsData.length,
        pendingReferrals: referralsData.filter(r => r.status === 'pending').length,
        completedReferrals: referralsData.filter(r => r.status === 'completed').length,
        urgentReferrals: referralsData.filter(r => r.urgency === 'urgent').length
      });

    } catch (error) {
      console.error('Error fetching referral data:', error);
      setError('Failed to fetch referral data');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const createReferral = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const referralData = {
        ...referralFormData,
        referring_provider_id: user?.id,
        referral_date: new Date().toISOString(),
        status: 'pending'
      };

      const response = editingReferral ? 
        await api.put(`/referrals/${editingReferral.id}`, referralData) :
        await api.post('/referrals', referralData);

      if (editingReferral) {
        setReferrals(referrals.map(r => r.id === editingReferral.id ? response.data : r));
        setSuccessWithCleanup('Referral updated successfully!');
      } else {
        setReferrals([...referrals, response.data]);
        setSuccessWithCleanup('Referral created successfully!');
      }

      setShowReferralForm(false);
      setEditingReferral(null);
      resetReferralForm();
    } catch (error) {
      console.error('Error saving referral:', error);
      setError(error.response?.data?.detail || 'Failed to save referral');
    } finally {
      setLoading(false);
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const updateReferralStatus = async (referralId, status) => {
    try {
      await api.put(`/referrals/${referralId}/status`, { status });
      
      setReferrals(referrals.map(ref => 
        ref.id === referralId ? { ...ref, status } : ref
      ));
      
      setSuccessWithCleanup(`Referral ${status} successfully!`);
      fetchReferralData(); // Refresh stats
    } catch (error) {
      console.error('Error updating referral:', error);
      setError('Failed to update referral status');
    }
  };

  // ✅ URL VETTING: Uses configured 'api' instance
  const addSpecialist = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');

      const response = await api.post('/referrals/specialists', specialistFormData);

      setSpecialists([...specialists, response.data]);
      setSuccessWithCleanup('Specialist added successfully!');
      setShowSpecialistForm(false);
      resetSpecialistForm();
    } catch (error) {
      console.error('Error adding specialist:', error);
      setError(error.response?.data?.detail || 'Failed to add specialist');
    } finally {
      setLoading(false);
    }
  };

  const resetReferralForm = () => {
    setReferralFormData({
      patient_id: '',
      referring_provider_id: '',
      specialist_id: '',
      specialty: '',
      urgency: 'routine',
      reason: '',
      clinical_notes: '',
      icd10_codes: [],
      requested_services: [],
      preferred_date: '',
      insurance_authorization_required: false
    });
  };

  const resetSpecialistForm = () => {
    setSpecialistFormData({
      name: '',
      specialty: '',
      practice_name: '',
      phone: '',
      email: '',
      address: '',
      accepts_referrals: true,
      referral_process: 'fax'
    });
  };

  const handleEditReferral = (referral) => {
    setEditingReferral(referral);
    setReferralFormData({
      patient_id: referral.patient_id,
      referring_provider_id: referral.referring_provider_id,
      specialist_id: referral.specialist_id,
      specialty: referral.specialty,
      urgency: referral.urgency,
      reason: referral.reason,
      clinical_notes: referral.clinical_notes,
      icd10_codes: referral.icd10_codes || [],
      requested_services: referral.requested_services || [],
      preferred_date: referral.preferred_date?.split('T')[0] || '',
      insurance_authorization_required: referral.insurance_authorization_required || false
    });
    setShowReferralForm(true);
  };

  const getUrgencyColor = (urgency) => {
    const colors = {
      'routine': 'bg-blue-100 text-blue-800',
      'urgent': 'bg-orange-100 text-orange-800',
      'stat': 'bg-red-100 text-red-800'
    };
    return colors[urgency] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'scheduled': 'bg-blue-100 text-blue-800',
      'completed': 'bg-green-100 text-green-800',
      'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const specialties = [
    'Cardiology', 'Dermatology', 'Endocrinology', 'Gastroenterology',
    'Neurology', 'Oncology', 'Orthopedics', 'Psychiatry', 'Pulmonology',
    'Rheumatology', 'Urology', 'Ophthalmology', 'ENT', 'General Surgery'
  ];

  const renderDashboard = () => {
    const recentReferrals = referrals.slice(0, 8);
    const urgentReferrals = referrals.filter(r => r.urgency === 'urgent' || r.urgency === 'stat');

    return (
      <div className="space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{referralStats.totalReferrals}</div>
                <div className="text-sm text-gray-300">Total Referrals</div>
              </div>
              <div className="text-2xl">🔗</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{referralStats.pendingReferrals}</div>
                <div className="text-sm text-gray-300">Pending</div>
              </div>
              <div className="text-2xl">⏳</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{referralStats.urgentReferrals}</div>
                <div className="text-sm text-gray-300">Urgent</div>
              </div>
              <div className="text-2xl">🚨</div>
            </div>
          </div>
          
          <div className="bg-white/5 border border-white/10 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-white">{specialists.length}</div>
                <div className="text-sm text-gray-300">Specialists</div>
              </div>
              <div className="text-2xl">👨‍⚕️</div>
            </div>
          </div>
        </div>

        {/* Urgent Referrals Alert */}
        {urgentReferrals.length > 0 && (
          <div className="bg-red-500/20 border border-red-400/50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">🚨 Urgent Referrals Requiring Attention</h3>
            <div className="space-y-3">
              {urgentReferrals.map(referral => (
                <div key={referral.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">
                          {patients.find(p => p.id === referral.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === referral.patient_id)?.name?.[0]?.family}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${getUrgencyColor(referral.urgency)}`}>
                          {referral.urgency}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Specialty: {referral.specialty} • Reason: {referral.reason}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        Specialist: {specialists.find(s => s.id === referral.specialist_id)?.name}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditReferral(referral)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Update
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Specialty Filter */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-300 mb-2">Filter by Specialty</label>
          <select
            value={selectedSpecialty}
            onChange={(e) => setSelectedSpecialty(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="">All Specialties</option>
            {specialties.map(specialty => (
              <option key={specialty} value={specialty}>{specialty}</option>
            ))}
          </select>
        </div>

        {/* Recent Referrals */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">🔗 Recent Referrals</h3>
          {recentReferrals.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <div className="text-6xl mb-4">🔗</div>
              <p>No referrals created yet</p>
              <button
                onClick={() => setShowReferralForm(true)}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Create First Referral
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentReferrals.map(referral => (
                <div key={referral.id} className="bg-white/5 border border-white/10 rounded p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-4">
                        <div className="text-white font-medium">
                          {patients.find(p => p.id === referral.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === referral.patient_id)?.name?.[0]?.family}
                        </div>
                        <span className={`px-2 py-1 rounded text-xs ${getStatusColor(referral.status)}`}>
                          {referral.status}
                        </span>
                        <span className={`px-2 py-1 rounded text-xs ${getUrgencyColor(referral.urgency)}`}>
                          {referral.urgency}
                        </span>
                      </div>
                      <div className="text-sm text-gray-300 mt-1">
                        Specialty: {referral.specialty} • Reason: {referral.reason}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        Specialist: {specialists.find(s => s.id === referral.specialist_id)?.name} • 
                        Date: {new Date(referral.referral_date).toLocaleDateString()}
                      </div>
                      {referral.icd10_codes && referral.icd10_codes.length > 0 && (
                        <div className="text-sm text-blue-400 mt-1">
                          ICD-10: {referral.icd10_codes.map(code => code.code).join(', ')}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditReferral(referral)}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                      >
                        Edit
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
          )}
        </div>

        {/* Specialist Directory */}
        <div className="bg-white/5 border border-white/10 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">👨‍⚕️ Specialist Directory</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {specialists.slice(0, 9).map(specialist => (
              <div key={specialist.id} className="bg-white/5 border border-white/10 rounded p-4">
                <div className="text-white font-medium">{specialist.name}</div>
                <div className="text-sm text-blue-300 mt-1">{specialist.specialty}</div>
                <div className="text-sm text-gray-300 mt-1">{specialist.practice_name}</div>
                <div className="text-sm text-gray-400 mt-1">{specialist.phone}</div>
                {specialist.accepts_referrals && (
                  <div className="text-xs text-green-400 mt-1">✅ Accepting Referrals</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderReferralForm = () => {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-gray-800 rounded-lg p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-white">
              {editingReferral ? '✏️ Edit Referral' : '🔗 New Referral'}
            </h3>
            <button
              onClick={() => {
                setShowReferralForm(false);
                setEditingReferral(null);
                resetReferralForm();
              }}
              className="text-gray-400 hover:text-white"
            >
              ✕
            </button>
          </div>

          <form onSubmit={createReferral} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Patient</label>
                <select
                  value={referralFormData.patient_id}
                  onChange={(e) => setReferralFormData({...referralFormData, patient_id: e.target.value})}
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
                <label className="block text-sm font-medium text-gray-300 mb-2">Specialty</label>
                <select
                  value={referralFormData.specialty}
                  onChange={(e) => setReferralFormData({...referralFormData, specialty: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Specialty</option>
                  {specialties.map(specialty => (
                    <option key={specialty} value={specialty}>{specialty}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Specialist</label>
                <select
                  value={referralFormData.specialist_id}
                  onChange={(e) => setReferralFormData({...referralFormData, specialist_id: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  required
                >
                  <option value="">Select Specialist</option>
                  {specialists
                    .filter(spec => !referralFormData.specialty || spec.specialty === referralFormData.specialty)
                    .map(specialist => (
                    <option key={specialist.id} value={specialist.id}>
                      {specialist.name} - {specialist.practice_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Urgency</label>
                <select
                  value={referralFormData.urgency}
                  onChange={(e) => setReferralFormData({...referralFormData, urgency: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                >
                  <option value="routine">Routine</option>
                  <option value="urgent">Urgent</option>
                  <option value="stat">STAT</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Reason for Referral</label>
              <input
                type="text"
                value={referralFormData.reason}
                onChange={(e) => setReferralFormData({...referralFormData, reason: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                placeholder="Primary reason for referral..."
                required
              />
            </div>

            {/* ICD-10 Integration */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">ICD-10 Diagnosis Codes</label>
              <ICD10Lookup
                selectedCodes={referralFormData.icd10_codes}
                onSelect={(code, updatedCodes) => {
                  if (code) {
                    const exists = referralFormData.icd10_codes.some(existingCode => existingCode.code === code.code);
                    if (!exists) {
                      setReferralFormData(prev => ({
                        ...prev,
                        icd10_codes: [...prev.icd10_codes, code]
                      }));
                    }
                  } else if (updatedCodes) {
                    setReferralFormData(prev => ({
                      ...prev,
                      icd10_codes: updatedCodes
                    }));
                  }
                }}
                placeholder="Search diagnostic codes for referral..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Clinical Notes</label>
              <textarea
                value={referralFormData.clinical_notes}
                onChange={(e) => setReferralFormData({...referralFormData, clinical_notes: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-24"
                placeholder="Clinical context, history, and relevant information..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Preferred Date</label>
                <input
                  type="date"
                  value={referralFormData.preferred_date}
                  onChange={(e) => setReferralFormData({...referralFormData, preferred_date: e.target.value})}
                  className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                />
              </div>

              <div className="flex items-center space-x-2 pt-6">
                <input
                  type="checkbox"
                  id="insurance_auth_required"
                  checked={referralFormData.insurance_authorization_required}
                  onChange={(e) => setReferralFormData({...referralFormData, insurance_authorization_required: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="insurance_auth_required" className="text-gray-300">Insurance Authorization Required</label>
              </div>
            </div>

            <div className="flex space-x-4 pt-4">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded disabled:opacity-50"
              >
                {loading ? 'Saving...' : (editingReferral ? 'Update Referral' : 'Create Referral')}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowReferralForm(false);
                  setEditingReferral(null);
                  resetReferralForm();
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
        <h2 className="text-xl font-semibold text-white">🔗 Referral Management</h2>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowReferralForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            🔗 New Referral
          </button>
          <button
            onClick={() => setShowSpecialistForm(true)}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            👨‍⚕️ Add Specialist
          </button>
          <button
            onClick={fetchReferralData}
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
          <p className="text-red-300">❌ {error}</p>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="border-b border-white/20 mb-6">
        <nav className="flex space-x-8">
          {[
            { id: 'dashboard', name: 'Dashboard', icon: '📊' },
            { id: 'referrals', name: 'All Referrals', icon: '🔗' },
            { id: 'specialists', name: 'Specialists', icon: '👨‍⚕️' },
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
      {activeView === 'referrals' && (
        <div className="space-y-4">
          {referrals
            .filter(r => !selectedSpecialty || r.specialty === selectedSpecialty)
            .map(referral => (
            <div key={referral.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-4">
                    <div className="text-white font-medium">
                      {patients.find(p => p.id === referral.patient_id)?.name?.[0]?.given?.[0]} {patients.find(p => p.id === referral.patient_id)?.name?.[0]?.family}
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${getStatusColor(referral.status)}`}>
                      {referral.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-300 mt-1">
                    {referral.specialty} • {referral.reason}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleEditReferral(referral)}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                  >
                    Edit
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'specialists' && (
        <div className="space-y-4">
          {specialists.map(specialist => (
            <div key={specialist.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="text-white font-medium">{specialist.name}</div>
              <div className="text-blue-300 text-sm">{specialist.specialty}</div>
              <div className="text-gray-300 text-sm">{specialist.practice_name}</div>
              <div className="text-gray-300 text-sm">{specialist.phone} • {specialist.email}</div>
            </div>
          ))}
        </div>
      )}
      {activeView === 'reports' && (
        <div className="text-white">
          <h3 className="text-lg font-semibold mb-4">📋 Referral Reports</h3>
          <p className="text-gray-300">Referral analytics and reporting coming soon...</p>
        </div>
      )}

      {/* Forms */}
      {showReferralForm && renderReferralForm()}
      
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

const DashboardHome = () => (
  <div className="space-y-6">
    <div className="text-center py-12 text-white">
      <h2 className="text-3xl font-bold mb-4">📊 ClinicHub Dashboard</h2>
      <p className="text-blue-200 mb-8">Complete Practice Management System</p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white/20 backdrop-blur-md p-6 rounded-lg border border-white/30">
          <h3 className="text-lg font-medium text-white mb-2">Total Patients</h3>
          <p className="text-3xl font-bold text-blue-200">0</p>
        </div>
        <div className="bg-white/20 backdrop-blur-md p-6 rounded-lg border border-white/30">
          <h3 className="text-lg font-medium text-white mb-2">Today's Appointments</h3>
          <p className="text-3xl font-bold text-green-200">0</p>
        </div>
        <div className="bg-white/20 backdrop-blur-md p-6 rounded-lg border border-white/30">
          <h3 className="text-lg font-medium text-white mb-2">Low Stock Items</h3>
          <p className="text-3xl font-bold text-red-200">0</p>
        </div>
      </div>
    </div>
  </div>
);

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
    // DISABLED: Synology integration disabled for deployment stability
    // try {
    //   const response = await api.get('/auth/synology-status');
    //   setSynologyStatus(response.data);
    // } catch (error) {
    //   console.error('Failed to fetch Synology status:', error);
    // }
    setSynologyStatus({ enabled: false, configured: false });
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

  return user ? (
    <>
      <Dashboard />
      <NotificationCenter />
    </>
  ) : <LoginPage />;
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;