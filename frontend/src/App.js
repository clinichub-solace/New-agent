import React, { useState, useEffect } from "react";
import "./App.css";
import { formatErrorMessage, toDisplayError } from './utils/errors';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import api from './api/axios';

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

              {/* Tab Content */}
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

const SchedulingModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">📅 Scheduling Module</h2>
    <p className="text-blue-200">Appointment Scheduling and Calendar Management</p>
  </div>
);

const TelehealthModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">💻 Telehealth Module</h2>
    <p className="text-blue-200">Virtual Consultations and Remote Care</p>
  </div>
);

const PatientPortalModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">🌐 Patient Portal Module</h2>
    <p className="text-blue-200">Patient Self-Service and Communication</p>
  </div>
);

// ✅ PHASE 4: CLINICAL ENHANCEMENT - Laboratory Orders Module (644 lines)
// ✅ URL VETTING: All API calls use configured 'api' instance, no hardcoded URLs
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

const InsuranceModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">🛡️ Insurance Module</h2>
    <p className="text-blue-200">Insurance Verification and Claims</p>
  </div>
);

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



const DocumentManagementModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">📄 Documents Module</h2>
    <p className="text-blue-200">Document Storage and Management</p>
  </div>
);

const InvoicesModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">💰 Invoices Module</h2>
    <p className="text-blue-200">Billing and Invoice Management</p>
  </div>
);

const SystemSettingsModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">⚙️ System Settings Module</h2>
    <p className="text-blue-200">System Configuration and Administration</p>
  </div>
);

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



const CommunicationModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">💬 Communication Module</h2>
    <p className="text-blue-200">Internal and Patient Communication</p>
  </div>
);

const ReferralsModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">🔗 Referrals Module</h2>
    <p className="text-blue-200">Patient Referrals and Specialist Coordination</p>
  </div>
);

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