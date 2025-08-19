{/* Patient Chart Tab */}
        {activeTab === 'details' && selectedPatient && (
          <div className="space-y-6">
            {/* Patient Summary Card */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-white">
                  {getPatientName(selectedPatient)}
                </h3>
                <div className="text-sm text-blue-200">
                  Patient ID: {selectedPatient.id}
                </div>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-blue-200">DOB:</span>
                  <span className="text-white ml-2">{selectedPatient.birth_date || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Gender:</span>
                  <span className="text-white ml-2">{selectedPatient.gender || 'Not specified'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Phone:</span>
                  <span className="text-white ml-2">{getPatientPhone(selectedPatient) || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Email:</span>
                  <span className="text-white ml-2 truncate">{getPatientEmail(selectedPatient) || 'Not provided'}</span>
                </div>
                <div className="md:col-span-2">
                  <span className="text-blue-200">Address:</span>
                  <span className="text-white ml-2">{getPatientAddress(selectedPatient) || 'Not provided'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Status:</span>
                  <span className="text-white ml-2 capitalize">{selectedPatient.status || 'active'}</span>
                </div>
                <div>
                  <span className="text-blue-200">Created:</span>
                  <span className="text-white ml-2">{new Date(selectedPatient.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-3">
                <div className="text-blue-200 text-sm">SOAP Notes</div>
                <div className="text-white text-xl font-bold">{soapNotes.length}</div>
              </div>
              <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3">
                <div className="text-green-200 text-sm">Vital Signs</div>
                <div className="text-white text-xl font-bold">{vitalSigns.length}</div>
              </div>
              <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-3">
                <div className="text-yellow-200 text-sm">Allergies</div>
                <div className="text-white text-xl font-bold">{allergies.length}</div>
              </div>
              <div className="bg-purple-500/20 border border-purple-500/50 rounded-lg p-3">
                <div className="text-purple-200 text-sm">Medications</div>
                <div className="text-white text-xl font-bold">{medications.length}</div>
              </div>
              <div className="bg-indigo-500/20 border border-indigo-500/50 rounded-lg p-3">
                <div className="text-indigo-200 text-sm">Prescriptions</div>
                <div className="text-white text-xl font-bold">{prescriptions.length}</div>
              </div>
            </div>

            {/* SOAP Notes Section */}
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-white">📋 SOAP Notes</h4>
                <button
                  onClick={() => setShowSoapForm(!showSoapForm)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {showSoapForm ? 'Cancel' : 'Add SOAP Note'}
                </button>
              </div>
              
              {/* SOAP Note Form */}
              {showSoapForm && (
                <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-4">
                  <h5 className="text-md font-medium text-white mb-3">
                    {editingSoapNote ? 'Edit SOAP Note' : 'New SOAP Note'}
                  </h5>
                  <form onSubmit={handleSoapSubmit} className="space-y-4">
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Subjective (Patient's complaints and history)</label>
                      <textarea
                        name="subjective"
                        value={soapFormData.subjective}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="What the patient reports, symptoms, history..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Objective (Physical examination findings)</label>
                      <textarea
                        name="objective"
                        value={soapFormData.objective}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Vital signs, physical exam findings, lab results..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Assessment (Diagnosis and clinical impression)</label>
                      <textarea
                        name="assessment"
                        value={soapFormData.assessment}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Diagnosis, clinical impression, differential diagnosis..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Plan (Treatment plan and follow-up)</label>
                      <textarea
                        name="plan"
                        value={soapFormData.plan}
                        onChange={handleSoapInputChange}
                        rows={3}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Treatment plan, medications, follow-up instructions..."
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Provider</label>
                      <input
                        type="text"
                        name="provider"
                        value={soapFormData.provider}
                        onChange={handleSoapInputChange}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Provider name"
                        required
                      />
                    </div>
                    <div className="flex space-x-4">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Saving...' : (editingSoapNote ? 'Update SOAP Note' : 'Save SOAP Note')}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowSoapForm(false);
                          setEditingSoapNote(null);
                          setSoapFormData({
                            subjective: '',
                            objective: '',
                            assessment: '',
                            plan: '',
                            provider: user?.username || 'Dr. Provider'
                          });
                        }}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}
              
              {/* SOAP Notes List */}
              <div className="space-y-3">
                {soapNotes.length > 0 ? (
                  soapNotes.map((note) => (
                    <div key={note.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-white font-medium">
                          SOAP Note - {new Date(note.created_at).toLocaleDateString()}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-blue-300 text-sm">by {note.provider}</span>
                          <button
                            onClick={() => handleEditSoapNote(note)}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors"
                          >
                            Edit
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Subjective:</div>
                          <div className="text-white text-sm">{note.subjective}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Objective:</div>
                          <div className="text-white text-sm">{note.objective}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Assessment:</div>
                          <div className="text-white text-sm">{note.assessment}</div>
                        </div>
                        <div>
                          <div className="text-blue-200 font-medium mb-1">Plan:</div>
                          <div className="text-white text-sm">{note.plan}</div>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center text-blue-200 py-4">
                    <div className="text-2xl mb-2">📝</div>
                    <p>No SOAP notes found for this patient</p>
                    <p className="text-sm mt-1">Click "Add SOAP Note" to create the first note</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Vital Signs Tab */}
        {activeTab === 'vitals' && selectedPatient && (
          <div className="space-y-6">
            <div className="bg-white/5 border border-white/10 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-lg font-medium text-white">📊 Vital Signs</h4>
                <button
                  onClick={() => setShowVitalsForm(!showVitalsForm)}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
                >
                  {showVitalsForm ? 'Cancel' : 'Add Vital Signs'}
                </button>
              </div>

              {/* Vital Signs Form */}
              {showVitalsForm && (
                <div className="bg-white/5 border border-white/10 rounded-lg p-4 mb-4">
                  <h5 className="text-md font-medium text-white mb-3">New Vital Signs</h5>
                  <form onSubmit={handleVitalsSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Temperature (°F)</label>
                        <input
                          type="number"
                          name="temperature"
                          value={vitalsFormData.temperature}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="98.6"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Heart Rate (BPM)</label>
                        <input
                          type="number"
                          name="heart_rate"
                          value={vitalsFormData.heart_rate}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="72"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Systolic BP</label>
                        <input
                          type="number"
                          name="blood_pressure_systolic"
                          value={vitalsFormData.blood_pressure_systolic}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="120"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Diastolic BP</label>
                        <input
                          type="number"
                          name="blood_pressure_diastolic"
                          value={vitalsFormData.blood_pressure_diastolic}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="80"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Respiratory Rate</label>
                        <input
                          type="number"
                          name="respiratory_rate"
                          value={vitalsFormData.respiratory_rate}
                          onChange={handleVitalsInputChange}
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="16"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">O2 Saturation (%)</label>
                        <input
                          type="number"
                          name="oxygen_saturation"
                          value={vitalsFormData.oxygen_saturation}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="98.0"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Weight (lbs)</label>
                        <input
                          type="number"
                          name="weight"
                          value={vitalsFormData.weight}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="150"
                        />
                      </div>
                      <div>
                        <label className="block text-blue-200 text-sm font-medium mb-2">Height (inches)</label>
                        <input
                          type="number"
                          name="height"
                          value={vitalsFormData.height}
                          onChange={handleVitalsInputChange}
                          step="0.1"
                          className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                          placeholder="68"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="block text-blue-200 text-sm font-medium mb-2">Notes</label>
                      <textarea
                        name="notes"
                        value={vitalsFormData.notes}
                        onChange={handleVitalsInputChange}
                        rows={2}
                        className="w-full p-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400"
                        placeholder="Additional notes about vital signs..."
                      />
                    </div>
                    <div className="flex space-x-4">
                      <button
                        type="submit"
                        disabled={loading}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg transition-colors disabled:opacity-50"
                      >
                        {loading ? 'Saving...' : 'Save Vital Signs'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowVitalsForm(false)}
                        className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Vital Signs List */}
              <div className="space-y-3">
                {vitalSigns.length > 0 ? (
                  vitalSigns.map((vitals) => (
                    <div key={vitals.id} className="bg-white/5 border border-white/10 rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div className="text-white font-medium">
                          {new Date(vitals.recorded_at || vitals.created_at).toLocaleDateString()} - {new Date(vitals.recorded_at || vitals.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-blue-200">Temperature:</span>
                          <span className="text-white ml-2">{vitals.temperature}°F</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Heart Rate:</span>
                          <span className="text-white ml-2">{vitals.heart_rate} BPM</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Blood Pressure:</span>
                          <span className="text-white ml-2">{vitals.blood_pressure_systolic}/{vitals.blood_pressure_diastolic}</span>
                        </div>
                        <div>
                          <span className="text-blue-200">O2 Sat:</span>
                          <span className="text-white ml-2">{vitals.oxygen_saturation}%</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Respiratory Rate:</span>
                          <span className="text-white ml-2">{vitals.respiratory_rate}</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Weight:</span>
                          <span className="text-white ml-2">{vitals.weight} lbs</span>
                        </div>
                        <div>
                          <span className="text-blue-200">Height:</span>
                          <span className="text-white ml-2">{vitals.height} in</span>
                        </div>
                        <div>
                          <span className="text-blue-200">BMI:</span>
                          <span className="text-white ml-2">{vitals.weight && vitals.height ? ((vitals.weight / (vitals.height * vitals.height)) * 703).toFixed(1) : 'N/A'}</span>
                        </div>
                      </div>
                      {vitals.notes && (
                        <div className="mt-3 text-sm">
                          <span className="text-blue-200">Notes:</span>
                          <span className="text-white ml-2">{vitals.notes}</span>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center text-blue-200 py-4">
                    <div className="text-2xl mb-2">📊</div>
                    <p>No vital signs recorded for this patient</p>
                    <p className="text-sm mt-1">Click "Add Vital Signs" to record the first measurement</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}