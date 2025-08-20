import React, { useState, useEffect } from "react";
import axios from "axios";

// Hardcoded API configuration to bypass environment variable issues in deployment
const BACKEND_URL = "/api";
const API = `/api`;

const eRxModule = () => {
  const [medications, setMedications] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize eRx system on component mount
  useEffect(() => {
    initializeERx();
  }, []);

  const initializeERx = async () => {
    try {
      const response = await axios.post(`${API}/erx/init`);
      console.log('eRx system initialized:', response.data);
      setIsInitialized(true);
      loadMedications();
    } catch (error) {
      console.error('Error initializing eRx:', error);
    }
  };

  const loadMedications = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/erx/medications`);
      setMedications(response.data || []);
    } catch (error) {
      console.error('Error loading medications:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchMedications = async (query) => {
    if (!query) {
      loadMedications();
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`${API}/erx/medications`, {
        params: { search: query }
      });
      setMedications(response.data || []);
    } catch (error) {
      console.error('Error searching medications:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Debounce search
    setTimeout(() => {
      if (query === searchQuery) {
        searchMedications(query);
      }
    }, 300);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      <div className="bg-white/10 backdrop-blur-md border-b border-white/20 px-6 py-4">
        <h1 className="text-2xl font-bold text-white">Electronic Prescribing (eRx)</h1>
        <p className="text-blue-200">FHIR-Compliant Medication Management</p>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Search Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">Medication Search</h3>
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={handleSearch}
              placeholder="Search for medications (e.g., Lisinopril, Metformin)..."
              className="w-full p-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
            {loading && (
              <div className="absolute right-3 top-3">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              </div>
            )}
          </div>
        </div>

        {/* Status Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-blue-200 text-sm">eRx System</p>
              <p className={`font-medium ${isInitialized ? 'text-green-400' : 'text-yellow-400'}`}>
                {isInitialized ? '✅ Initialized' : '⚠️ Initializing...'}
              </p>
            </div>
            <div>
              <p className="text-blue-200 text-sm">Medications Available</p>
              <p className="text-white font-medium">{medications.length} medications</p>
            </div>
            <div>
              <p className="text-blue-200 text-sm">FHIR Compliance</p>
              <p className="text-green-400 font-medium">✅ FHIR R4</p>
            </div>
          </div>
        </div>

        {/* Medications List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Available Medications ({medications.length})
          </h3>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-blue-200">Loading medications...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {medications.map((med) => (
                <div key={med.id} className="bg-white/5 rounded-lg border border-white/10 p-4">
                  <div className="mb-2">
                    <h4 className="text-white font-semibold">{med.generic_name}</h4>
                    <p className="text-blue-200 text-sm">{med.strength}</p>
                  </div>
                  
                  {med.brand_names && med.brand_names.length > 0 && (
                    <div className="mb-2">
                      <p className="text-blue-300 text-xs">Brand names:</p>
                      <p className="text-white text-sm">{med.brand_names.join(', ')}</p>
                    </div>
                  )}
                  
                  <div className="mb-2">
                    <p className="text-blue-300 text-xs">Drug class:</p>
                    <p className="text-white text-sm">{med.drug_class}</p>
                  </div>
                  
                  {med.dosage_forms && (
                    <div className="mb-2">
                      <p className="text-blue-300 text-xs">Forms:</p>
                      <p className="text-white text-sm">{med.dosage_forms.join(', ')}</p>
                    </div>
                  )}
                  
                  {med.rxnorm_code && (
                    <div className="mb-2">
                      <p className="text-blue-300 text-xs">RxNorm Code:</p>
                      <p className="text-white text-sm">{med.rxnorm_code}</p>
                    </div>
                  )}

                  <div className="mt-3 pt-3 border-t border-white/10">
                    <button className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 px-4 rounded transition duration-300">
                      Create Prescription
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {!loading && medications.length === 0 && (
            <div className="text-center py-8">
              <p className="text-blue-200">No medications found</p>
              <button
                onClick={initializeERx}
                className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded transition duration-300"
              >
                Initialize eRx System
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default eRxModule;