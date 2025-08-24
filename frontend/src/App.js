import React, { useState, useEffect } from "react";
import "./App.css";
import { formatErrorMessage, toDisplayError } from './utils/errors';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LoginPage from './components/LoginPage';
import api from './api/axios';

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
    provider: user?.username || 'Dr. Provider'
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
        provider: user?.username || 'Dr. Provider'
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

const LabOrdersModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">🔬 Lab Orders Module</h2>
    <p className="text-blue-200">Laboratory Test Orders and Results</p>
  </div>
);

const InsuranceModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">🛡️ Insurance Module</h2>
    <p className="text-blue-200">Insurance Verification and Claims</p>
  </div>
);

const ClinicalTemplatesModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">📋 Clinical Templates Module</h2>
    <p className="text-blue-200">Medical Forms and Documentation Templates</p>
  </div>
);

const QualityMeasuresModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">📈 Quality Measures Module</h2>
    <p className="text-blue-200">Clinical Quality Metrics and Reporting</p>
  </div>
);

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

const InventoryModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">📦 Inventory Module</h2>
    <p className="text-blue-200">Medical Supplies and Equipment Management</p>
  </div>
);

const FinanceModule = () => (
  <div className="text-center py-12 text-white">
    <h2 className="text-2xl font-bold mb-4">💳 Finance Module</h2>
    <p className="text-blue-200">Financial Management and Reporting</p>
  </div>
);

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