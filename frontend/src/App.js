import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      // Verify token and get user info
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Token invalid, logging out:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { username, password });
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const hasPermission = (permission) => {
    if (!user) return false;
    if (user.role === 'admin') return true; // Admin has all permissions
    return user.permissions?.includes(permission) || false;
  };

  const value = {
    user,
    login,
    logout,
    hasPermission,
    loading,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Page Component
const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(username, password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const initializeAdmin = async () => {
    try {
      const response = await axios.post(`${API}/auth/init-admin`);
      alert(`Admin user created! Username: admin, Password: admin123\n${response.data.warning}`);
    } catch (error) {
      if (error.response?.status === 400) {
        alert('Admin user already exists');
      } else {
        alert('Error creating admin user');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/5 to-transparent opacity-20"></div>
      
      <div className="relative w-full max-w-md">
        {/* Login Card */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-400 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-2xl">🏥</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">ClinicHub</h1>
            <p className="text-blue-200 text-sm">FHIR-Compliant Practice Management</p>
            <p className="text-blue-300 text-xs mt-2 italic">Guided by Solace. Powered by purpose.</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-blue-200 mb-2">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                placeholder="Enter your username"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-blue-200 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                placeholder="Enter your password"
                required
              />
            </div>

            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3">
                <p className="text-red-200 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold py-3 px-4 rounded-lg transition duration-300 hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Signing In...
                </div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Admin Initialization */}
          <div className="mt-6 pt-6 border-t border-white/20">
            <button
              onClick={initializeAdmin}
              className="w-full text-blue-300 hover:text-blue-200 text-sm transition duration-300"
            >
              First time setup? Initialize Admin User
            </button>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-blue-300 text-xs">
              © 2024 ClinicHub. Secure Healthcare Management.
            </p>
          </div>
        </div>

        {/* Role-based Access Info */}
        <div className="mt-6 bg-white/5 backdrop-blur-sm rounded-lg p-4 border border-white/10">
          <h3 className="text-white text-sm font-semibold mb-2">Role-Based Access</h3>
          <div className="text-blue-200 text-xs space-y-1">
            <p><strong>Admin:</strong> Full system access</p>
            <p><strong>Doctor:</strong> Patients, EHR, Forms, Reports</p>
            <p><strong>Nurse:</strong> Patients, EHR, Forms, Inventory</p>
            <p><strong>Manager:</strong> Employees, Finance, Reports</p>
            <p><strong>Receptionist:</strong> Patients, Invoices, Basic EHR</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, permission }) => {
  const { user, hasPermission, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading ClinicHub...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  if (permission && !hasPermission(permission)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 border border-white/20 text-center">
          <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white text-2xl">🚫</span>
          </div>
          <h2 className="text-2xl font-bold text-white mb-4">Access Denied</h2>
          <p className="text-blue-200 mb-6">
            You don't have permission to access this resource.
            <br />
            Required permission: <code className="bg-white/20 px-2 py-1 rounded">{permission}</code>
          </p>
          <p className="text-blue-300 text-sm">
            Your role: <strong>{user.role}</strong>
          </p>
        </div>
      </div>
    );
  }

  return children;
};

// Enhanced Header with User Info and Logout
const AppHeader = ({ children }) => {
  const { user, logout } = useAuth();

  return (
    <>
      {React.cloneElement(children, {
        user,
        onLogout: logout
      })}
    </>
  );
};

// Helper function to safely format dates
const formatDate = (dateValue) => {
  if (!dateValue) return 'N/A';
  try {
    const date = new Date(dateValue);
    if (isNaN(date.getTime())) return 'N/A';
    return date.toLocaleDateString();
  } catch (error) {
    return 'N/A';
  }
};

// Components

// Comprehensive Finance Management Module
const FinanceModule = ({ setActiveModule }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [vendors, setVendors] = useState([]);
  const [checks, setChecks] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [vendorInvoices, setVendorInvoices] = useState([]);
  const [dailySummary, setDailySummary] = useState(null);
  const [showVendorForm, setShowVendorForm] = useState(false);
  const [showCheckForm, setShowCheckForm] = useState(false);
  const [showTransactionForm, setShowTransactionForm] = useState(false);
  const [showInvoiceForm, setShowInvoiceForm] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    fetchFinanceData();
  }, []);

  const fetchFinanceData = async () => {
    try {
      const [vendorsRes, checksRes, transactionsRes, invoicesRes] = await Promise.all([
        axios.get(`${API}/vendors`),
        axios.get(`${API}/checks`),
        axios.get(`${API}/financial-transactions`),
        axios.get(`${API}/vendor-invoices`)
      ]);
      
      setVendors(vendorsRes.data);
      setChecks(checksRes.data);
      setTransactions(transactionsRes.data);
      setVendorInvoices(invoicesRes.data);
      
      // Get today's summary
      const today = new Date().toISOString().split('T')[0];
      await fetchDailySummary(today);
    } catch (error) {
      console.error("Error fetching finance data:", error);
    }
  };

  const fetchDailySummary = async (date) => {
    try {
      const response = await axios.get(`${API}/financial-summary/${date}`);
      setDailySummary(response.data);
    } catch (error) {
      console.error("Error fetching daily summary:", error);
    }
  };

  // Vendor Form Component
  const VendorForm = () => {
    const [formData, setFormData] = useState({
      company_name: '', contact_person: '', email: '', phone: '',
      address_line1: '', city: '', state: '', zip_code: '',
      tax_id: '', payment_terms: 'Net 30', preferred_payment_method: 'check'
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/vendors`, formData);
        setShowVendorForm(false);
        setFormData({
          company_name: '', contact_person: '', email: '', phone: '',
          address_line1: '', city: '', state: '', zip_code: '',
          tax_id: '', payment_terms: 'Net 30', preferred_payment_method: 'check'
        });
        fetchFinanceData();
      } catch (error) {
        console.error("Error creating vendor:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-bold mb-4">Add New Vendor</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Company Name *"
                value={formData.company_name}
                onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
              <input
                type="text"
                placeholder="Contact Person"
                value={formData.contact_person}
                onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="tel"
                placeholder="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
            </div>
            <input
              type="text"
              placeholder="Address *"
              value={formData.address_line1}
              onChange={(e) => setFormData({...formData, address_line1: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
            <div className="grid grid-cols-3 gap-4">
              <input
                type="text"
                placeholder="City *"
                value={formData.city}
                onChange={(e) => setFormData({...formData, city: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
              <input
                type="text"
                placeholder="State *"
                value={formData.state}
                onChange={(e) => setFormData({...formData, state: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
              <input
                type="text"
                placeholder="ZIP Code *"
                value={formData.zip_code}
                onChange={(e) => setFormData({...formData, zip_code: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Tax ID/EIN"
                value={formData.tax_id}
                onChange={(e) => setFormData({...formData, tax_id: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <select
                value={formData.payment_terms}
                onChange={(e) => setFormData({...formData, payment_terms: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="Net 30">Net 30</option>
                <option value="Net 15">Net 15</option>
                <option value="Net 7">Net 7</option>
                <option value="COD">Cash on Delivery</option>
                <option value="Immediate">Immediate</option>
              </select>
            </div>
            <div className="flex justify-end space-x-4 pt-4">
              <button
                type="button"
                onClick={() => setShowVendorForm(false)}
                className="px-6 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-green-500 text-white rounded-lg"
              >
                Add Vendor
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Check Form Component
  const CheckForm = () => {
    const [formData, setFormData] = useState({
      payee_type: 'vendor', payee_id: '', payee_name: '', amount: '',
      memo: '', expense_category: 'office_supplies', check_date: new Date().toISOString().split('T')[0]
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/checks`, {
          ...formData,
          amount: parseFloat(formData.amount),
          created_by: 'Admin'
        });
        setShowCheckForm(false);
        setFormData({
          payee_type: 'vendor', payee_id: '', payee_name: '', amount: '',
          memo: '', expense_category: 'office_supplies', check_date: new Date().toISOString().split('T')[0]
        });
        fetchFinanceData();
      } catch (error) {
        console.error("Error creating check:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4">
          <h3 className="text-xl font-bold mb-4">Create Check</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <select
                value={formData.payee_type}
                onChange={(e) => setFormData({...formData, payee_type: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="vendor">Vendor</option>
                <option value="employee">Employee</option>
                <option value="other">Other</option>
              </select>
              {formData.payee_type === 'vendor' && (
                <select
                  value={formData.payee_id}
                  onChange={(e) => {
                    const vendor = vendors.find(v => v.id === e.target.value);
                    setFormData({
                      ...formData, 
                      payee_id: e.target.value,
                      payee_name: vendor ? vendor.company_name : ''
                    });
                  }}
                  className="p-3 border border-gray-300 rounded-lg"
                >
                  <option value="">Select Vendor</option>
                  {vendors.map(vendor => (
                    <option key={vendor.id} value={vendor.id}>{vendor.company_name}</option>
                  ))}
                </select>
              )}
              {formData.payee_type !== 'vendor' && (
                <input
                  type="text"
                  placeholder="Payee Name *"
                  value={formData.payee_name}
                  onChange={(e) => setFormData({...formData, payee_name: e.target.value})}
                  className="p-3 border border-gray-300 rounded-lg"
                  required
                />
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="number"
                step="0.01"
                placeholder="Amount *"
                value={formData.amount}
                onChange={(e) => setFormData({...formData, amount: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
              <input
                type="date"
                value={formData.check_date}
                onChange={(e) => setFormData({...formData, check_date: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            <select
              value={formData.expense_category}
              onChange={(e) => setFormData({...formData, expense_category: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            >
              <option value="payroll">Payroll</option>
              <option value="rent">Rent</option>
              <option value="utilities">Utilities</option>
              <option value="medical_supplies">Medical Supplies</option>
              <option value="insurance">Insurance</option>
              <option value="marketing">Marketing</option>
              <option value="maintenance">Maintenance</option>
              <option value="professional_fees">Professional Fees</option>
              <option value="office_supplies">Office Supplies</option>
              <option value="other_expense">Other Expense</option>
            </select>
            <input
              type="text"
              placeholder="Memo/Description"
              value={formData.memo}
              onChange={(e) => setFormData({...formData, memo: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            />
            <div className="flex justify-end space-x-4 pt-4">
              <button
                type="button"
                onClick={() => setShowCheckForm(false)}
                className="px-6 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-500 text-white rounded-lg"
              >
                Create Check
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Transaction Form Component
  const TransactionForm = () => {
    const [formData, setFormData] = useState({
      transaction_type: 'income', amount: '', payment_method: 'cash',
      description: '', category: 'patient_payment', transaction_date: new Date().toISOString().split('T')[0]
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/financial-transactions`, {
          ...formData,
          amount: parseFloat(formData.amount),
          created_by: 'Admin'
        });
        setShowTransactionForm(false);
        setFormData({
          transaction_type: 'income', amount: '', payment_method: 'cash',
          description: '', category: 'patient_payment', transaction_date: new Date().toISOString().split('T')[0]
        });
        fetchFinanceData();
        fetchDailySummary(formData.transaction_date);
      } catch (error) {
        console.error("Error creating transaction:", error);
      }
    };

    const incomeCategories = [
      'patient_payment', 'insurance_payment', 'consultation_fee', 
      'procedure_fee', 'medication_sale', 'other_income'
    ];

    const expenseCategories = [
      'payroll', 'rent', 'utilities', 'medical_supplies', 'insurance',
      'marketing', 'maintenance', 'professional_fees', 'office_supplies', 'other_expense'
    ];

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4">
          <h3 className="text-xl font-bold mb-4">Add Transaction</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <select
                value={formData.transaction_type}
                onChange={(e) => setFormData({
                  ...formData, 
                  transaction_type: e.target.value,
                  category: e.target.value === 'income' ? 'patient_payment' : 'office_supplies'
                })}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="income">Income</option>
                <option value="expense">Expense</option>
              </select>
              <select
                value={formData.payment_method}
                onChange={(e) => setFormData({...formData, payment_method: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="cash">Cash</option>
                <option value="credit_card">Credit Card</option>
                <option value="debit_card">Debit Card</option>
                <option value="check">Check</option>
                <option value="bank_transfer">Bank Transfer</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="number"
                step="0.01"
                placeholder="Amount *"
                value={formData.amount}
                onChange={(e) => setFormData({...formData, amount: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
              <input
                type="date"
                value={formData.transaction_date}
                onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            <select
              value={formData.category}
              onChange={(e) => setFormData({...formData, category: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            >
              {(formData.transaction_type === 'income' ? incomeCategories : expenseCategories).map(cat => (
                <option key={cat} value={cat}>
                  {cat.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
            <input
              type="text"
              placeholder="Description *"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
            <div className="flex justify-end space-x-4 pt-4">
              <button
                type="button"
                onClick={() => setShowTransactionForm(false)}
                className="px-6 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-green-500 text-white rounded-lg"
              >
                Add Transaction
              </button>
            </div>
          </form>
        </div>
      </div>
    );
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
            <h1 className="text-3xl font-bold text-white">Finance Management</h1>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowTransactionForm(true)}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg"
            >
              + Transaction
            </button>
            <button
              onClick={() => setShowCheckForm(true)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg"
            >
              + Write Check
            </button>
            <button
              onClick={() => setShowVendorForm(true)}
              className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
            >
              + Add Vendor
            </button>
          </div>
        </div>

        {/* Finance Tabs */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="border-b border-white/20">
            <nav className="flex space-x-8 px-6">
              {['dashboard', 'transactions', 'checks', 'vendors', 'invoices', 'reports'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-2 border-b-2 font-medium text-sm capitalize ${
                    activeTab === tab
                      ? 'border-green-400 text-green-400'
                      : 'border-transparent text-blue-200 hover:text-white'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'dashboard' && (
              <div className="space-y-6">
                {/* Daily Summary */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Today's Summary</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-blue-200">Income:</span>
                        <span className="text-green-400 font-medium">
                          ${dailySummary?.total_income?.toFixed(2) || '0.00'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-200">Expenses:</span>
                        <span className="text-red-400 font-medium">
                          ${dailySummary?.total_expenses?.toFixed(2) || '0.00'}
                        </span>
                      </div>
                      <div className="border-t border-white/20 pt-2">
                        <div className="flex justify-between">
                          <span className="text-white font-medium">Net:</span>
                          <span className={`font-bold ${
                            (dailySummary?.net_amount || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            ${dailySummary?.net_amount?.toFixed(2) || '0.00'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Quick Stats</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-blue-200">Vendors:</span>
                        <span className="text-white">{vendors.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-200">Unpaid Bills:</span>
                        <span className="text-yellow-400">{vendorInvoices.filter(inv => inv.payment_status === 'unpaid').length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-200">Pending Checks:</span>
                        <span className="text-orange-400">{checks.filter(check => check.status === 'draft').length}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Payment Methods Today</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-blue-200">Cash:</span>
                        <span className="text-white">${dailySummary?.cash_income?.toFixed(2) || '0.00'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-200">Credit Card:</span>
                        <span className="text-white">${dailySummary?.credit_card_income?.toFixed(2) || '0.00'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-200">Checks:</span>
                        <span className="text-white">${dailySummary?.check_income?.toFixed(2) || '0.00'}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Transaction Count</h3>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-blue-200">Income:</span>
                        <span className="text-green-400">{dailySummary?.income_transaction_count || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-blue-200">Expenses:</span>
                        <span className="text-red-400">{dailySummary?.expense_transaction_count || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recent Transactions */}
                <div className="bg-white/5 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-white mb-4">Recent Transactions</h3>
                  <div className="space-y-3">
                    {transactions.slice(0, 5).map((transaction) => (
                      <div key={transaction.id} className="flex items-center justify-between p-3 bg-white/10 rounded-lg">
                        <div>
                          <p className="text-white font-medium">{transaction.description}</p>
                          <p className="text-blue-200 text-sm">
                            {formatDate(transaction.transaction_date)} • {transaction.payment_method.replace('_', ' ')}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`font-bold ${
                            transaction.transaction_type === 'income' ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {transaction.transaction_type === 'income' ? '+' : '-'}${transaction.amount.toFixed(2)}
                          </p>
                          <p className="text-blue-200 text-sm capitalize">
                            {transaction.category?.replace('_', ' ')}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Forms */}
      {showVendorForm && <VendorForm />}
      {showCheckForm && <CheckForm />}
      {showTransactionForm && <TransactionForm />}
    </div>
  );
};
const Dashboard = ({ setActiveModule, user, onLogout }) => {
  const [stats, setStats] = useState({});
  const [recentPatients, setRecentPatients] = useState([]);
  const [recentInvoices, setRecentInvoices] = useState([]);
  
  // New dashboard data states
  const [erxPatients, setErxPatients] = useState([]);
  const [dailyLog, setDailyLog] = useState([]);
  const [patientQueue, setPatientQueue] = useState([]);
  const [pendingPayments, setPendingPayments] = useState([]);
  const [quickStats, setQuickStats] = useState({
    erx_patients_today: 0,
    daily_revenue: 0,
    patients_in_queue: 0,
    pending_payments_total: 0
  });

  useEffect(() => {
    fetchDashboardData();
    fetchQuickStats();
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

  const fetchQuickStats = async () => {
    try {
      // Fetch quick stats for the new dashboard cards
      const [erxResponse, dailyResponse, queueResponse, paymentsResponse] = await Promise.all([
        axios.get(`${API}/dashboard/erx-patients`),
        axios.get(`${API}/dashboard/daily-log`),
        axios.get(`${API}/dashboard/patient-queue`),
        axios.get(`${API}/dashboard/pending-payments`)
      ]);

      setQuickStats({
        erx_patients_today: erxResponse.data.total_scheduled,
        daily_revenue: dailyResponse.data.summary.total_revenue,
        patients_in_queue: queueResponse.data.summary.total_patients,
        pending_payments_total: paymentsResponse.data.summary.total_outstanding_amount
      });
    } catch (error) {
      console.error("Error fetching quick stats:", error);
    }
  };

  const handleCardClick = (cardType) => {
    setActiveModule(cardType);
  };

  const modules = [
    { name: "Patients/EHR", key: "patients", icon: "👥", color: "bg-blue-500", permission: "patients:read" },
    { name: "Smart Forms", key: "forms", icon: "📋", color: "bg-green-500", permission: "forms:read" },
    { name: "Inventory", key: "inventory", icon: "📦", color: "bg-orange-500", permission: "inventory:read" },
    { name: "Invoices", key: "invoices", icon: "🧾", color: "bg-purple-500", permission: "invoices:read" },
    { name: "Employees", key: "employees", icon: "👨‍⚕️", color: "bg-indigo-500", permission: "employees:read" },
    { name: "Finance", key: "finance", icon: "💰", color: "bg-green-600", permission: "finance:read" },
    { name: "Scheduling", key: "scheduling", icon: "📅", color: "bg-blue-600", permission: "scheduling:read" },
    { name: "Communications", key: "communications", icon: "📨", color: "bg-teal-500", permission: "communications:read" }
  ];

  const { hasPermission } = useAuth();

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
                <p className="text-blue-200 text-sm">FHIR-Compliant Practice Management</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-white font-semibold">
                  {user?.first_name} {user?.last_name}
                </p>
                <p className="text-blue-200 text-sm capitalize">{user?.role}</p>
              </div>
              {user?.profile_picture && (
                <img 
                  src={`data:image/jpeg;base64,${user.profile_picture}`}
                  alt="Profile"
                  className="w-10 h-10 rounded-full object-cover"
                />
              )}
              <button
                onClick={onLogout}
                className="bg-red-500/20 hover:bg-red-500/30 text-red-200 hover:text-white px-4 py-2 rounded-lg transition-colors duration-200 border border-red-500/30"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* New Clinic Operations Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div 
            onClick={() => handleCardClick('erx-patients')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm">eRx</p>
                <p className="text-3xl font-bold text-white">{quickStats.erx_patients_today || 0}</p>
                <p className="text-purple-300 text-xs">Patients Today</p>
              </div>
              <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">💊</span>
              </div>
            </div>
          </div>

          <div 
            onClick={() => handleCardClick('daily-log')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm">Daily Total</p>
                <p className="text-3xl font-bold text-white">${quickStats.daily_revenue?.toFixed(0) || 0}</p>
                <p className="text-green-300 text-xs">Revenue Today</p>
              </div>
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">📊</span>
              </div>
            </div>
          </div>

          <div 
            onClick={() => handleCardClick('patient-queue')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm">Patient Queue</p>
                <p className="text-3xl font-bold text-white">{quickStats.patients_in_queue || 0}</p>
                <p className="text-blue-300 text-xs">In Clinic Now</p>
              </div>
              <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">🏥</span>
              </div>
            </div>
          </div>

          <div 
            onClick={() => handleCardClick('pending-payments')}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 cursor-pointer hover:bg-white/20 transition-all duration-300 transform hover:-translate-y-1"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-200 text-sm">Pending Payments</p>
                <p className="text-3xl font-bold text-white">${quickStats.pending_payments_total?.toFixed(0) || 0}</p>
                <p className="text-yellow-300 text-xs">Outstanding</p>
              </div>
              <div className="w-12 h-12 bg-yellow-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">💰</span>
              </div>
            </div>
          </div>
        </div>

        {/* Module Grid with Permission Checks */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {modules.map((module) => {
            const hasAccess = hasPermission(module.permission);
            return (
              <div
                key={module.key}
                onClick={() => hasAccess && setActiveModule(module.key)}
                className={`bg-white/10 backdrop-blur-md rounded-xl p-8 border border-white/20 transition-all duration-300 ${
                  hasAccess 
                    ? 'cursor-pointer hover:bg-white/20 transform hover:-translate-y-1' 
                    : 'opacity-50 cursor-not-allowed'
                }`}
              >
                <div className="text-center">
                  <div className={`w-16 h-16 ${module.color} rounded-full flex items-center justify-center mx-auto mb-4 ${
                    !hasAccess && 'grayscale'
                  }`}>
                    <span className="text-white text-2xl">{module.icon}</span>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-2">{module.name}</h3>
                  <p className="text-blue-200 text-sm">
                    {hasAccess ? `Manage your ${module.name.toLowerCase()}` : 'Access restricted'}
                  </p>
                  {!hasAccess && (
                    <p className="text-red-300 text-xs mt-1">
                      Required: {module.permission}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* Recent Activity - Removed Encounters Section */}
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
                      {formatDate(patient.created_at)}
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
                      {invoice.auto_generated && <span className="ml-2 text-xs text-green-400">(Auto)</span>}
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
  const [activeTab, setActiveTab] = useState('overview');
  const [patientSummary, setPatientSummary] = useState(null);
  const [showPatientForm, setShowPatientForm] = useState(false);
  const [showEncounterForm, setShowEncounterForm] = useState(false);
  const [showVitalsForm, setShowVitalsForm] = useState(false);
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);
  const [showPrescriptionForm, setShowPrescriptionForm] = useState(false);
  const [showSmartFormSelector, setShowSmartFormSelector] = useState(false);
  
  // eRx States
  const [medications, setMedications] = useState([]);
  const [medicationSearch, setMedicationSearch] = useState('');
  const [selectedMedication, setSelectedMedication] = useState(null);
  const [prescriptions, setPrescriptions] = useState([]);
  
  // Smart Forms States
  const [availableForms, setAvailableForms] = useState([]);
  const [selectedForm, setSelectedForm] = useState(null);
  const [formSubmissions, setFormSubmissions] = useState([]);

  // Prescription Management Functions
  const activatePrescription = async (prescriptionId) => {
    try {
      await axios.put(`${API}/prescriptions/${prescriptionId}/status`, null, {
        params: { status: 'active' }
      });
      fetchPatientSummary(selectedPatient.id);
    } catch (error) {
      console.error("Error activating prescription:", error);
      alert('Error activating prescription. Please try again.');
    }
  };

  const updatePrescriptionStatus = async (prescriptionId, status) => {
    try {
      await axios.put(`${API}/prescriptions/${prescriptionId}/status`, null, {
        params: { status }
      });
      fetchPatientSummary(selectedPatient.id);
    } catch (error) {
      console.error("Error updating prescription status:", error);
      alert('Error updating prescription status. Please try again.');
    }
  };

  const checkPrescriptionInteractions = async (prescriptionId) => {
    try {
      const response = await axios.get(`${API}/prescriptions/${prescriptionId}/interactions`);
      const interactions = response.data.interactions;
      
      if (interactions.length > 0) {
        let alertMessage = "Drug Interactions Found:\n\n";
        interactions.forEach(interaction => {
          alertMessage += `• ${interaction.message}\n`;
          if (interaction.management) {
            alertMessage += `  Management: ${interaction.management}\n`;
          }
        });
        alert(alertMessage);
      } else {
        alert("No drug interactions found for this prescription.");
      }
    } catch (error) {
      console.error("Error checking interactions:", error);
      alert('Error checking drug interactions. Please try again.');
    }
  };

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

  // Document Management Functions
  const viewDocument = (doc) => {
    // Create a blob from base64 data and open in new window
    const byteCharacters = atob(doc.file_data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: `application/${doc.file_extension}` });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
  };

  const deleteDocument = async (documentId) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await axios.delete(`${API}/documents/${documentId}`);
        fetchPatientSummary(selectedPatient.id);
      } catch (error) {
        console.error("Error deleting document:", error);
      }
    }
  };

  // Document Upload Form
  const DocumentUploadForm = () => {
    const [documentData, setDocumentData] = useState({
      document_name: '',
      document_type: 'lab_result',
      notes: '',
      uploaded_by: 'Dr. Sarah Chen'
    });
    const [selectedFile, setSelectedFile] = useState(null);

    const handleFileSelect = (e) => {
      const file = e.target.files[0];
      if (file) {
        setSelectedFile(file);
        setDocumentData({
          ...documentData,
          document_name: file.name.split('.')[0]
        });
      }
    };

    const handleDocumentSubmit = async (e) => {
      e.preventDefault();
      if (!selectedFile) {
        alert('Please select a file to upload');
        return;
      }

      try {
        // Convert file to base64
        const reader = new FileReader();
        reader.onload = async () => {
          const base64Data = reader.result.split(',')[1]; // Remove data:*/*;base64, prefix
          
          const uploadData = {
            ...documentData,
            patient_id: selectedPatient.id,
            file_data: base64Data,
            file_extension: selectedFile.name.split('.').pop().toLowerCase(),
            file_size: selectedFile.size
          };

          await axios.post(`${API}/patients/${selectedPatient.id}/documents`, uploadData);
          setShowDocumentUpload(false);
          setSelectedFile(null);
          setDocumentData({
            document_name: '',
            document_type: 'lab_result',
            notes: '',
            uploaded_by: 'Dr. Sarah Chen'
          });
          fetchPatientSummary(selectedPatient.id);
        };
        reader.readAsDataURL(selectedFile);
      } catch (error) {
        console.error("Error uploading document:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4">
          <h3 className="text-xl font-bold mb-4">Upload Patient Document</h3>
          <form onSubmit={handleDocumentSubmit} className="space-y-4">
            <input
              type="text"
              placeholder="Document Name"
              value={documentData.document_name}
              onChange={(e) => setDocumentData({...documentData, document_name: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
            <select
              value={documentData.document_type}
              onChange={(e) => setDocumentData({...documentData, document_type: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            >
              <option value="lab_result">Lab Result</option>
              <option value="imaging">Imaging/X-Ray</option>
              <option value="insurance">Insurance Document</option>
              <option value="consent_form">Consent Form</option>
              <option value="referral">Referral</option>
              <option value="discharge_summary">Discharge Summary</option>
              <option value="other">Other</option>
            </select>
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              onChange={handleFileSelect}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
            {selectedFile && (
              <div className="p-3 bg-gray-100 rounded-lg">
                <p className="text-sm text-gray-600">
                  Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </p>
              </div>
            )}
            <textarea
              placeholder="Notes (optional)"
              value={documentData.notes}
              onChange={(e) => setDocumentData({...documentData, notes: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              rows="3"
            />
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowDocumentUpload(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-500 text-white rounded-lg"
              >
                Upload Document
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // eRx Prescription Form Component
  const PrescriptionForm = () => {
    const [prescriptionData, setPrescriptionData] = useState({
      medication_id: '',
      prescriber_name: 'Dr. Sarah Chen',
      dosage_text: '',
      dose_quantity: '',
      dose_unit: 'mg',
      frequency: 'BID',
      route: 'oral',
      quantity: '',
      days_supply: 30,
      refills: 0,
      indication: '',
      special_instructions: '',
      generic_substitution_allowed: true
    });

    const [drugSearchResults, setDrugSearchResults] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [safetyAlerts, setSafetyAlerts] = useState([]);
    const [showAlerts, setShowAlerts] = useState(false);

    const searchMedications = async (query) => {
      if (query.length < 2) {
        setDrugSearchResults([]);
        return;
      }
      
      try {
        const response = await axios.get(`${API}/medications`, {
          params: { search: query, limit: 10 }
        });
        setDrugSearchResults(response.data);
      } catch (error) {
        console.error("Error searching medications:", error);
      }
    };

    const selectMedication = async (medication) => {
      setSelectedMedication(medication);
      setPrescriptionData({
        ...prescriptionData,
        medication_id: medication.id
      });
      setSearchQuery(medication.generic_name);
      setDrugSearchResults([]);
      
      // Check for allergies and interactions
      await checkSafetyAlerts(medication.id);
    };

    const checkSafetyAlerts = async (medicationId) => {
      try {
        // This would call an endpoint that checks allergies and interactions
        // For now, we'll simulate it
        const alerts = [];
        
        // Check allergies
        if (patientSummary.allergies?.some(allergy => 
          allergy.allergen.toLowerCase().includes(selectedMedication?.generic_name.toLowerCase())
        )) {
          alerts.push({
            type: 'allergy',
            severity: 'major',
            message: 'Patient has documented allergy to this medication'
          });
        }
        
        setSafetyAlerts(alerts);
        setShowAlerts(alerts.length > 0);
      } catch (error) {
        console.error("Error checking safety alerts:", error);
      }
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      
      if (!selectedMedication) {
        alert('Please select a medication');
        return;
      }

      try {
        const submitData = {
          ...prescriptionData,
          patient_id: selectedPatient.id,
          prescriber_id: 'user123', // This should come from current user
          dose_quantity: parseFloat(prescriptionData.dose_quantity),
          quantity: parseFloat(prescriptionData.quantity),
          days_supply: parseInt(prescriptionData.days_supply),
          refills: parseInt(prescriptionData.refills),
          created_by: 'Dr. Sarah Chen'
        };

        await axios.post(`${API}/prescriptions`, submitData);
        setShowPrescriptionForm(false);
        fetchPatientSummary(selectedPatient.id);
        
        // Reset form
        setPrescriptionData({
          medication_id: '',
          prescriber_name: 'Dr. Sarah Chen',
          dosage_text: '',
          dose_quantity: '',
          dose_unit: 'mg',
          frequency: 'BID',
          route: 'oral',
          quantity: '',
          days_supply: 30,
          refills: 0,
          indication: '',
          special_instructions: '',
          generic_substitution_allowed: true
        });
        setSelectedMedication(null);
        setSearchQuery('');
        setSafetyAlerts([]);
        
      } catch (error) {
        console.error("Error creating prescription:", error);
        alert('Error creating prescription. Please try again.');
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-8">
            <h3 className="text-2xl font-bold mb-6">New Electronic Prescription</h3>
            
            {/* Safety Alerts */}
            {showAlerts && safetyAlerts.length > 0 && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <h4 className="font-semibold text-red-800 mb-2">⚠️ Safety Alerts</h4>
                {safetyAlerts.map((alert, index) => (
                  <div key={index} className="text-red-700 text-sm mb-1">
                    <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                      alert.severity === 'major' ? 'bg-red-500' : 
                      alert.severity === 'moderate' ? 'bg-orange-500' : 'bg-yellow-500'
                    }`}></span>
                    {alert.message}
                  </div>
                ))}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Medication Search */}
              <div>
                <label className="block text-sm font-medium mb-2">Search Medication *</label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      searchMedications(e.target.value);
                    }}
                    placeholder="Type medication name..."
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                  
                  {drugSearchResults.length > 0 && (
                    <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                      {drugSearchResults.map((med) => (
                        <div
                          key={med.id}
                          onClick={() => selectMedication(med)}
                          className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100"
                        >
                          <div className="font-medium">{med.generic_name}</div>
                          <div className="text-sm text-gray-600">
                            {med.brand_names?.join(', ')} | {med.strength} | {med.dosage_forms?.join(', ')}
                          </div>
                          <div className="text-xs text-gray-500 capitalize">
                            {med.drug_class?.replace('_', ' ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                
                {selectedMedication && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                    <div className="font-medium text-blue-900">{selectedMedication.generic_name}</div>
                    <div className="text-sm text-blue-700">
                      Strength: {selectedMedication.strength} | Forms: {selectedMedication.dosage_forms?.join(', ')}
                    </div>
                  </div>
                )}
              </div>

              {/* Dosage Information */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Dose Quantity *</label>
                  <input
                    type="number"
                    step="0.1"
                    value={prescriptionData.dose_quantity}
                    onChange={(e) => setPrescriptionData({...prescriptionData, dose_quantity: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Unit</label>
                  <select
                    value={prescriptionData.dose_unit}
                    onChange={(e) => setPrescriptionData({...prescriptionData, dose_unit: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  >
                    <option value="mg">mg</option>
                    <option value="g">g</option>
                    <option value="mcg">mcg</option>
                    <option value="ml">ml</option>
                    <option value="units">units</option>
                    <option value="tablets">tablets</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Frequency *</label>
                  <select
                    value={prescriptionData.frequency}
                    onChange={(e) => setPrescriptionData({...prescriptionData, frequency: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="QD">Once Daily (QD)</option>
                    <option value="BID">Twice Daily (BID)</option>
                    <option value="TID">Three Times Daily (TID)</option>
                    <option value="QID">Four Times Daily (QID)</option>
                    <option value="Q6H">Every 6 Hours</option>
                    <option value="Q8H">Every 8 Hours</option>
                    <option value="Q12H">Every 12 Hours</option>
                    <option value="PRN">As Needed (PRN)</option>
                  </select>
                </div>
              </div>

              {/* Route and Instructions */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Route</label>
                  <select
                    value={prescriptionData.route}
                    onChange={(e) => setPrescriptionData({...prescriptionData, route: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  >
                    <option value="oral">Oral</option>
                    <option value="IV">Intravenous (IV)</option>
                    <option value="IM">Intramuscular (IM)</option>
                    <option value="topical">Topical</option>
                    <option value="sublingual">Sublingual</option>
                    <option value="rectal">Rectal</option>
                    <option value="nasal">Nasal</option>
                    <option value="ophthalmic">Ophthalmic</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Dosage Instructions *</label>
                  <input
                    type="text"
                    value={prescriptionData.dosage_text}
                    onChange={(e) => setPrescriptionData({...prescriptionData, dosage_text: e.target.value})}
                    placeholder="e.g., Take 1 tablet by mouth twice daily"
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
              </div>

              {/* Prescription Details */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Quantity *</label>
                  <input
                    type="number"
                    value={prescriptionData.quantity}
                    onChange={(e) => setPrescriptionData({...prescriptionData, quantity: e.target.value})}
                    placeholder="e.g., 30"
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Days Supply *</label>
                  <input
                    type="number"
                    value={prescriptionData.days_supply}
                    onChange={(e) => setPrescriptionData({...prescriptionData, days_supply: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Refills</label>
                  <select
                    value={prescriptionData.refills}
                    onChange={(e) => setPrescriptionData({...prescriptionData, refills: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  >
                    {[0,1,2,3,4,5].map(num => (
                      <option key={num} value={num}>{num}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Clinical Information */}
              <div>
                <label className="block text-sm font-medium mb-2">Indication/Reason for Prescription *</label>
                <input
                  type="text"
                  value={prescriptionData.indication}
                  onChange={(e) => setPrescriptionData({...prescriptionData, indication: e.target.value})}
                  placeholder="e.g., Hypertension, Diabetes, Infection"
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Special Instructions</label>
                <textarea
                  value={prescriptionData.special_instructions}
                  onChange={(e) => setPrescriptionData({...prescriptionData, special_instructions: e.target.value})}
                  placeholder="Additional instructions for patient or pharmacist..."
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  rows="3"
                />
              </div>

              {/* Generic Substitution */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="generic_substitution"
                  checked={prescriptionData.generic_substitution_allowed}
                  onChange={(e) => setPrescriptionData({...prescriptionData, generic_substitution_allowed: e.target.checked})}
                  className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                />
                <label htmlFor="generic_substitution" className="ml-2 text-sm font-medium">
                  Allow generic substitution
                </label>
              </div>

              {/* Form Actions */}
              <div className="flex justify-end space-x-4 pt-6 border-t">
                <button
                  type="button"
                  onClick={() => setShowPrescriptionForm(false)}
                  className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600"
                >
                  Create Prescription
                </button>
              </div>
            </form>
          </div>
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
                  DOB: {formatDate(selectedPatient.birth_date)} |
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
                {['overview', 'encounters', 'prescriptions', 'forms', 'documents', 'medications', 'allergies', 'history'].map((tab) => (
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
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">Patient Encounters</h3>
                    <button
                      onClick={() => setShowEncounterForm(true)}
                      className="bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + New Encounter
                    </button>
                  </div>
                  {patientSummary.recent_encounters?.map((encounter) => (
                    <div key={encounter.id} className="bg-white/5 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <p className="text-white font-medium">{encounter.encounter_number}</p>
                            <span className={`px-2 py-1 text-white text-xs rounded-full ${
                              encounter.status === 'completed' ? 'bg-green-500' : 
                              encounter.status === 'in_progress' ? 'bg-blue-500' : 'bg-gray-500'
                            }`}>
                              {encounter.status}
                            </span>
                          </div>
                          <p className="text-blue-200 capitalize">{encounter.encounter_type?.replace('_', ' ')}</p>
                          <p className="text-blue-200 text-sm">
                            {formatDate(encounter.scheduled_date)} - {encounter.provider}
                          </p>
                          {encounter.chief_complaint && (
                            <p className="text-blue-200 text-sm mt-1">CC: {encounter.chief_complaint}</p>
                          )}
                        </div>
                        <div className="flex space-x-2">
                          <button className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                            View Details
                          </button>
                          {encounter.status !== 'completed' && (
                            <button className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm">
                              Complete
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'documents' && patientSummary && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">Patient Documents</h3>
                    <button
                      onClick={() => setShowDocumentUpload(true)}
                      className="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + Upload Document
                    </button>
                  </div>
                  {patientSummary.documents?.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {patientSummary.documents.map((doc) => (
                        <div key={doc.id} className="bg-white/5 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-white font-medium">{doc.document_name}</p>
                              <p className="text-blue-200 text-sm capitalize">{doc.document_type.replace('_', ' ')}</p>
                              <p className="text-blue-200 text-xs">
                                Uploaded: {formatDate(doc.upload_date)} by {doc.uploaded_by}
                              </p>
                              <p className="text-blue-200 text-xs">
                                Size: {(doc.file_size / 1024).toFixed(1)} KB | Type: {doc.file_extension.toUpperCase()}
                              </p>
                            </div>
                            <div className="flex space-x-2">
                              <button 
                                onClick={() => viewDocument(doc)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                              >
                                View
                              </button>
                              <button 
                                onClick={() => deleteDocument(doc.id)}
                                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-blue-200">No documents uploaded yet</p>
                  )}
                </div>
              )}

              {activeTab === 'prescriptions' && patientSummary && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">eRx - Electronic Prescriptions</h3>
                    <button
                      onClick={() => setShowPrescriptionForm(true)}
                      className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + New Prescription
                    </button>
                  </div>
                  
                  {/* Safety Alerts */}
                  {patientSummary.prescription_alerts?.length > 0 && (
                    <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                      <h4 className="text-red-200 font-semibold mb-2">⚠️ Safety Alerts</h4>
                      {patientSummary.prescription_alerts.map((alert, index) => (
                        <div key={index} className="text-red-200 text-sm mb-1">
                          • {alert.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Current Prescriptions */}
                  {patientSummary.prescriptions?.length > 0 ? (
                    <div className="space-y-3">
                      {patientSummary.prescriptions.map((prescription) => (
                        <div key={prescription.id} className="bg-white/5 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <p className="text-white font-medium text-lg">
                                  {prescription.medication_display}
                                </p>
                                <span className={`px-2 py-1 text-white text-xs rounded-full ${
                                  prescription.status === 'active' ? 'bg-green-500' :
                                  prescription.status === 'draft' ? 'bg-yellow-500' :
                                  prescription.status === 'cancelled' ? 'bg-red-500' : 'bg-gray-500'
                                }`}>
                                  {prescription.status}
                                </span>
                                <span className="text-purple-300 text-sm font-mono">
                                  {prescription.prescription_number}
                                </span>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                                <div>
                                  <p className="text-blue-200 text-sm">Dosage</p>
                                  <p className="text-white">
                                    {prescription.dosage_instruction?.[0]?.text || 'Not specified'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Quantity</p>
                                  <p className="text-white">{prescription.quantity || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Days Supply</p>
                                  <p className="text-white">{prescription.days_supply || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Refills</p>
                                  <p className="text-white">{prescription.refills}</p>
                                </div>
                              </div>
                              
                              <div className="flex items-center space-x-4 text-sm">
                                <p className="text-blue-200">
                                  Prescribed: {formatDate(prescription.authored_on)}
                                </p>
                                <p className="text-blue-200">
                                  By: {prescription.prescriber_name}
                                </p>
                                {prescription.reason_code?.[0]?.text && (
                                  <p className="text-blue-200">
                                    For: {prescription.reason_code[0].text}
                                  </p>
                                )}
                              </div>

                              {/* Safety Alerts for this prescription */}
                              {(prescription.allergy_alerts?.length > 0 || prescription.interaction_alerts?.length > 0) && (
                                <div className="mt-3 p-3 bg-yellow-500/20 rounded-lg">
                                  <p className="text-yellow-200 font-semibold text-sm mb-2">Safety Alerts:</p>
                                  {prescription.allergy_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                  {prescription.interaction_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-4">
                              {prescription.status === 'draft' && (
                                <button
                                  onClick={() => activatePrescription(prescription.id)}
                                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Activate
                                </button>
                              )}
                              {prescription.status === 'active' && (
                                <button
                                  onClick={() => updatePrescriptionStatus(prescription.id, 'on-hold')}
                                  className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Hold
                                </button>
                              )}
                              <button
                                onClick={() => checkPrescriptionInteractions(prescription.id)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Check Interactions
                              </button>
                              <button
                                onClick={() => updatePrescriptionStatus(prescription.id, 'cancelled')}
                                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-purple-300 text-2xl">💊</span>
                      </div>
                      <p className="text-blue-200">No prescriptions found</p>
                      <p className="text-blue-300 text-sm">Click "New Prescription" to create the first prescription</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'prescriptions' && patientSummary && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">eRx - Electronic Prescriptions</h3>
                    <button
                      onClick={() => setShowPrescriptionForm(true)}
                      className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + New Prescription
                    </button>
                  </div>
                  
                  {/* Safety Alerts */}
                  {patientSummary.prescription_alerts?.length > 0 && (
                    <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                      <h4 className="text-red-200 font-semibold mb-2">⚠️ Safety Alerts</h4>
                      {patientSummary.prescription_alerts.map((alert, index) => (
                        <div key={index} className="text-red-200 text-sm mb-1">
                          • {alert.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Current Prescriptions */}
                  {patientSummary.prescriptions?.length > 0 ? (
                    <div className="space-y-3">
                      {patientSummary.prescriptions.map((prescription) => (
                        <div key={prescription.id} className="bg-white/5 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <p className="text-white font-medium text-lg">
                                  {prescription.medication_display}
                                </p>
                                <span className={`px-2 py-1 text-white text-xs rounded-full ${
                                  prescription.status === 'active' ? 'bg-green-500' :
                                  prescription.status === 'draft' ? 'bg-yellow-500' :
                                  prescription.status === 'cancelled' ? 'bg-red-500' : 'bg-gray-500'
                                }`}>
                                  {prescription.status}
                                </span>
                                <span className="text-purple-300 text-sm font-mono">
                                  {prescription.prescription_number}
                                </span>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                                <div>
                                  <p className="text-blue-200 text-sm">Dosage</p>
                                  <p className="text-white">
                                    {prescription.dosage_instruction?.[0]?.text || 'Not specified'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Quantity</p>
                                  <p className="text-white">{prescription.quantity || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Days Supply</p>
                                  <p className="text-white">{prescription.days_supply || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Refills</p>
                                  <p className="text-white">{prescription.refills}</p>
                                </div>
                              </div>
                              
                              <div className="flex items-center space-x-4 text-sm">
                                <p className="text-blue-200">
                                  Prescribed: {formatDate(prescription.authored_on)}
                                </p>
                                <p className="text-blue-200">
                                  By: {prescription.prescriber_name}
                                </p>
                                {prescription.reason_code?.[0]?.text && (
                                  <p className="text-blue-200">
                                    For: {prescription.reason_code[0].text}
                                  </p>
                                )}
                              </div>

                              {/* Safety Alerts for this prescription */}
                              {(prescription.allergy_alerts?.length > 0 || prescription.interaction_alerts?.length > 0) && (
                                <div className="mt-3 p-3 bg-yellow-500/20 rounded-lg">
                                  <p className="text-yellow-200 font-semibold text-sm mb-2">Safety Alerts:</p>
                                  {prescription.allergy_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                  {prescription.interaction_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-4">
                              {prescription.status === 'draft' && (
                                <button
                                  onClick={() => activatePrescription(prescription.id)}
                                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Activate
                                </button>
                              )}
                              {prescription.status === 'active' && (
                                <button
                                  onClick={() => updatePrescriptionStatus(prescription.id, 'on-hold')}
                                  className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Hold
                                </button>
                              )}
                              <button
                                onClick={() => checkPrescriptionInteractions(prescription.id)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Check Interactions
                              </button>
                              <button
                                onClick={() => updatePrescriptionStatus(prescription.id, 'cancelled')}
                                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-purple-300 text-2xl">💊</span>
                      </div>
                      <p className="text-blue-200">No prescriptions found</p>
                      <p className="text-blue-300 text-sm">Click "New Prescription" to create the first prescription</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'prescriptions' && patientSummary && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">eRx - Electronic Prescriptions</h3>
                    <button
                      onClick={() => setShowPrescriptionForm(true)}
                      className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + New Prescription
                    </button>
                  </div>
                  
                  {/* Safety Alerts */}
                  {patientSummary.prescription_alerts?.length > 0 && (
                    <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                      <h4 className="text-red-200 font-semibold mb-2">⚠️ Safety Alerts</h4>
                      {patientSummary.prescription_alerts.map((alert, index) => (
                        <div key={index} className="text-red-200 text-sm mb-1">
                          • {alert.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Current Prescriptions */}
                  {patientSummary.prescriptions?.length > 0 ? (
                    <div className="space-y-3">
                      {patientSummary.prescriptions.map((prescription) => (
                        <div key={prescription.id} className="bg-white/5 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <p className="text-white font-medium text-lg">
                                  {prescription.medication_display}
                                </p>
                                <span className={`px-2 py-1 text-white text-xs rounded-full ${
                                  prescription.status === 'active' ? 'bg-green-500' :
                                  prescription.status === 'draft' ? 'bg-yellow-500' :
                                  prescription.status === 'cancelled' ? 'bg-red-500' : 'bg-gray-500'
                                }`}>
                                  {prescription.status}
                                </span>
                                <span className="text-purple-300 text-sm font-mono">
                                  {prescription.prescription_number}
                                </span>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                                <div>
                                  <p className="text-blue-200 text-sm">Dosage</p>
                                  <p className="text-white">
                                    {prescription.dosage_instruction?.[0]?.text || 'Not specified'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Quantity</p>
                                  <p className="text-white">{prescription.quantity || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Days Supply</p>
                                  <p className="text-white">{prescription.days_supply || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Refills</p>
                                  <p className="text-white">{prescription.refills}</p>
                                </div>
                              </div>
                              
                              <div className="flex items-center space-x-4 text-sm">
                                <p className="text-blue-200">
                                  Prescribed: {formatDate(prescription.authored_on)}
                                </p>
                                <p className="text-blue-200">
                                  By: {prescription.prescriber_name}
                                </p>
                                {prescription.reason_code?.[0]?.text && (
                                  <p className="text-blue-200">
                                    For: {prescription.reason_code[0].text}
                                  </p>
                                )}
                              </div>

                              {/* Safety Alerts for this prescription */}
                              {(prescription.allergy_alerts?.length > 0 || prescription.interaction_alerts?.length > 0) && (
                                <div className="mt-3 p-3 bg-yellow-500/20 rounded-lg">
                                  <p className="text-yellow-200 font-semibold text-sm mb-2">Safety Alerts:</p>
                                  {prescription.allergy_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                  {prescription.interaction_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-4">
                              {prescription.status === 'draft' && (
                                <button
                                  onClick={() => activatePrescription(prescription.id)}
                                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Activate
                                </button>
                              )}
                              {prescription.status === 'active' && (
                                <button
                                  onClick={() => updatePrescriptionStatus(prescription.id, 'on-hold')}
                                  className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Hold
                                </button>
                              )}
                              <button
                                onClick={() => checkPrescriptionInteractions(prescription.id)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Check Interactions
                              </button>
                              <button
                                onClick={() => updatePrescriptionStatus(prescription.id, 'cancelled')}
                                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-purple-300 text-2xl">💊</span>
                      </div>
                      <p className="text-blue-200">No prescriptions found</p>
                      <p className="text-blue-300 text-sm">Click "New Prescription" to create the first prescription</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'prescriptions' && patientSummary && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">eRx - Electronic Prescriptions</h3>
                    <button
                      onClick={() => setShowPrescriptionForm(true)}
                      className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + New Prescription
                    </button>
                  </div>
                  
                  {/* Safety Alerts */}
                  {patientSummary.prescription_alerts?.length > 0 && (
                    <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4">
                      <h4 className="text-red-200 font-semibold mb-2">⚠️ Safety Alerts</h4>
                      {patientSummary.prescription_alerts.map((alert, index) => (
                        <div key={index} className="text-red-200 text-sm mb-1">
                          • {alert.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Current Prescriptions */}
                  {patientSummary.prescriptions?.length > 0 ? (
                    <div className="space-y-3">
                      {patientSummary.prescriptions.map((prescription) => (
                        <div key={prescription.id} className="bg-white/5 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <p className="text-white font-medium text-lg">
                                  {prescription.medication_display}
                                </p>
                                <span className={`px-2 py-1 text-white text-xs rounded-full ${
                                  prescription.status === 'active' ? 'bg-green-500' :
                                  prescription.status === 'draft' ? 'bg-yellow-500' :
                                  prescription.status === 'cancelled' ? 'bg-red-500' : 'bg-gray-500'
                                }`}>
                                  {prescription.status}
                                </span>
                                <span className="text-purple-300 text-sm font-mono">
                                  {prescription.prescription_number}
                                </span>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                                <div>
                                  <p className="text-blue-200 text-sm">Dosage</p>
                                  <p className="text-white">
                                    {prescription.dosage_instruction?.[0]?.text || 'Not specified'}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Quantity</p>
                                  <p className="text-white">{prescription.quantity || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Days Supply</p>
                                  <p className="text-white">{prescription.days_supply || 'Not specified'}</p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Refills</p>
                                  <p className="text-white">{prescription.refills}</p>
                                </div>
                              </div>
                              
                              <div className="flex items-center space-x-4 text-sm">
                                <p className="text-blue-200">
                                  Prescribed: {formatDate(prescription.authored_on)}
                                </p>
                                <p className="text-blue-200">
                                  By: {prescription.prescriber_name}
                                </p>
                                {prescription.reason_code?.[0]?.text && (
                                  <p className="text-blue-200">
                                    For: {prescription.reason_code[0].text}
                                  </p>
                                )}
                              </div>

                              {/* Safety Alerts for this prescription */}
                              {(prescription.allergy_alerts?.length > 0 || prescription.interaction_alerts?.length > 0) && (
                                <div className="mt-3 p-3 bg-yellow-500/20 rounded-lg">
                                  <p className="text-yellow-200 font-semibold text-sm mb-2">Safety Alerts:</p>
                                  {prescription.allergy_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                  {prescription.interaction_alerts?.map((alert, idx) => (
                                    <p key={idx} className="text-yellow-200 text-sm">• {alert.message}</p>
                                  ))}
                                </div>
                              )}
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-4">
                              {prescription.status === 'draft' && (
                                <button
                                  onClick={() => activatePrescription(prescription.id)}
                                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Activate
                                </button>
                              )}
                              {prescription.status === 'active' && (
                                <button
                                  onClick={() => updatePrescriptionStatus(prescription.id, 'on-hold')}
                                  className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Hold
                                </button>
                              )}
                              <button
                                onClick={() => checkPrescriptionInteractions(prescription.id)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Check Interactions
                              </button>
                              <button
                                onClick={() => updatePrescriptionStatus(prescription.id, 'cancelled')}
                                className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-purple-300 text-2xl">💊</span>
                      </div>
                      <p className="text-blue-200">No prescriptions found</p>
                      <p className="text-blue-300 text-sm">Click "New Prescription" to create the first prescription</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'forms' && patientSummary && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">Patient Forms</h3>
                    <button
                      onClick={() => setShowSmartFormSelector(true)}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + Fill Out Form
                    </button>
                  </div>
                  
                  {/* Form Submissions History */}
                  {patientSummary.form_submissions?.length > 0 ? (
                    <div className="space-y-3">
                      {patientSummary.form_submissions.map((submission) => (
                        <div key={submission.id} className="bg-white/5 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <p className="text-white font-medium text-lg">
                                  {submission.form_title}
                                </p>
                                <span className={`px-2 py-1 text-white text-xs rounded-full ${
                                  submission.status === 'completed' ? 'bg-green-500' :
                                  submission.status === 'reviewed' ? 'bg-blue-500' : 'bg-yellow-500'
                                }`}>
                                  {submission.status}
                                </span>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-3">
                                <div>
                                  <p className="text-blue-200 text-sm">Submitted</p>
                                  <p className="text-white">
                                    {formatDate(submission.submitted_at)}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Submitted By</p>
                                  <p className="text-white">{submission.submitted_by}</p>
                                </div>
                                {submission.encounter_id && (
                                  <div>
                                    <p className="text-blue-200 text-sm">Encounter</p>
                                    <p className="text-white">Linked</p>
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-4">
                              <button
                                onClick={() => viewFormSubmission(submission.id)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                              >
                                View
                              </button>
                              {submission.fhir_data && (
                                <button
                                  onClick={() => exportToFHIR(submission.id)}
                                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Export FHIR
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-blue-300 text-2xl">📋</span>
                      </div>
                      <p className="text-blue-200">No forms submitted yet</p>
                      <p className="text-blue-300 text-sm">Click "Fill Out Form" to start with a medical form</p>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'forms' && patientSummary && (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">Patient Forms</h3>
                    <button
                      onClick={() => setShowSmartFormSelector(true)}
                      className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm"
                    >
                      + Fill Out Form
                    </button>
                  </div>
                  
                  {/* Form Submissions History */}
                  {patientSummary.form_submissions?.length > 0 ? (
                    <div className="space-y-3">
                      {patientSummary.form_submissions.map((submission) => (
                        <div key={submission.id} className="bg-white/5 rounded-lg p-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <p className="text-white font-medium text-lg">
                                  {submission.form_title}
                                </p>
                                <span className={`px-2 py-1 text-white text-xs rounded-full ${
                                  submission.status === 'completed' ? 'bg-green-500' :
                                  submission.status === 'reviewed' ? 'bg-blue-500' : 'bg-yellow-500'
                                }`}>
                                  {submission.status}
                                </span>
                              </div>
                              
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-3">
                                <div>
                                  <p className="text-blue-200 text-sm">Submitted</p>
                                  <p className="text-white">
                                    {formatDate(submission.submitted_at)}
                                  </p>
                                </div>
                                <div>
                                  <p className="text-blue-200 text-sm">Submitted By</p>
                                  <p className="text-white">{submission.submitted_by}</p>
                                </div>
                                {submission.encounter_id && (
                                  <div>
                                    <p className="text-blue-200 text-sm">Encounter</p>
                                    <p className="text-white">Linked</p>
                                  </div>
                                )}
                              </div>
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-4">
                              <button
                                onClick={() => viewFormSubmission(submission.id)}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                              >
                                View
                              </button>
                              {submission.fhir_data && (
                                <button
                                  onClick={() => exportToFHIR(submission.id)}
                                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                                >
                                  Export FHIR
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-blue-300 text-2xl">📋</span>
                      </div>
                      <p className="text-blue-200">No forms submitted yet</p>
                      <p className="text-blue-300 text-sm">Click "Fill Out Form" to start with a medical form</p>
                    </div>
                  )}
                </div>
              )}

              {/* Keep existing medications, allergies, history tabs */}
              {activeTab === 'medications' && patientSummary && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-white">All Medications</h3>
                  {patientSummary.active_medications?.map((med) => (
                    <div key={med.id} className="bg-white/5 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-white font-medium">{med.medication_name}</p>
                          <p className="text-blue-200">{med.dosage} - {med.frequency} - {med.route}</p>
                          <p className="text-blue-200 text-sm">Prescribed by: {med.prescribing_physician}</p>
                          <p className="text-blue-200 text-sm">Indication: {med.indication}</p>
                          <p className="text-blue-200 text-sm">Start Date: {formatDate(med.start_date)}</p>
                        </div>
                        <span className={`px-2 py-1 text-white text-xs rounded-full ${
                          med.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                        }`}>
                          {med.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'allergies' && patientSummary && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-white">All Allergies</h3>
                  {patientSummary.allergies?.map((allergy) => (
                    <div key={allergy.id} className="bg-white/5 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-white font-medium">{allergy.allergen}</p>
                          <p className="text-blue-200">Reaction: {allergy.reaction}</p>
                          <p className="text-blue-200 text-sm">Onset: {formatDate(allergy.onset_date)}</p>
                          <p className="text-blue-200 text-sm">Documented by: {allergy.created_by}</p>
                          {allergy.notes && <p className="text-blue-200 text-sm">Notes: {allergy.notes}</p>}
                        </div>
                        <span className={`px-2 py-1 text-white text-xs rounded-full ${
                          allergy.severity === 'severe' || allergy.severity === 'life_threatening'
                            ? 'bg-red-500' : allergy.severity === 'moderate' ? 'bg-orange-500' : 'bg-yellow-500'
                        }`}>
                          {allergy.severity}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'history' && patientSummary && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-white">Medical History</h3>
                  {patientSummary.medical_history?.map((history) => (
                    <div key={history.id} className="bg-white/5 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-white font-medium">{history.condition}</p>
                          {history.icd10_code && <p className="text-blue-200">ICD-10: {history.icd10_code}</p>}
                          <p className="text-blue-200 text-sm">Diagnosed: {formatDate(history.diagnosis_date)}</p>
                          <p className="text-blue-200 text-sm">Diagnosed by: {history.diagnosed_by}</p>
                          {history.notes && <p className="text-blue-200 text-sm">Notes: {history.notes}</p>}
                        </div>
                        <span className={`px-2 py-1 text-white text-xs rounded-full ${
                          history.status === 'active' ? 'bg-red-500' : 
                          history.status === 'resolved' ? 'bg-green-500' : 'bg-blue-500'
                        }`}>
                          {history.status}
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
        {showDocumentUpload && <DocumentUploadForm />}
        {showPrescriptionForm && <PrescriptionForm />}
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

        {showPatientForm && (
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
                      {formatDate(patient.birth_date)}
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
                      {formatDate(patient.created_at)}
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
                      {formatDate(invoice.issue_date)}
                    </td>
                    <td className="p-4 text-blue-200">
                      {formatDate(invoice.due_date)}
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

// Comprehensive Inventory Module
const InventoryModule = ({ setActiveModule }) => {
  const [inventory, setInventory] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [showItemForm, setShowItemForm] = useState(false);
  const [showTransactionForm, setShowTransactionForm] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [activeTab, setActiveTab] = useState('items');
  const [lowStockItems, setLowStockItems] = useState([]);

  useEffect(() => {
    fetchInventory();
    fetchTransactions();
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await axios.get(`${API}/inventory`);
      setInventory(response.data);
      
      // Calculate low stock items
      const lowStock = response.data.filter(item => 
        item.current_stock <= item.min_stock_level && item.current_stock > 0
      );
      setLowStockItems(lowStock);
    } catch (error) {
      console.error("Error fetching inventory:", error);
    }
  };

  const fetchTransactions = async () => {
    try {
      // This would need a new endpoint to get all transactions
      // For now, we'll use empty array
      setTransactions([]);
    } catch (error) {
      console.error("Error fetching transactions:", error);
    }
  };

  const ItemForm = () => {
    const [itemData, setItemData] = useState({
      name: '', category: 'medical_supply', sku: '', current_stock: 0,
      min_stock_level: 10, unit_cost: 0, supplier: '', location: '', notes: ''
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/inventory`, {
          ...itemData,
          current_stock: parseInt(itemData.current_stock),
          min_stock_level: parseInt(itemData.min_stock_level),
          unit_cost: parseFloat(itemData.unit_cost)
        });
        setShowItemForm(false);
        setItemData({
          name: '', category: 'medical_supply', sku: '', current_stock: 0,
          min_stock_level: 10, unit_cost: 0, supplier: '', location: '', notes: ''
        });
        fetchInventory();
      } catch (error) {
        console.error("Error creating item:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-bold mb-4">Add Inventory Item</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              placeholder="Item Name *"
              value={itemData.name}
              onChange={(e) => setItemData({...itemData, name: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
            <div className="grid grid-cols-2 gap-4">
              <select
                value={itemData.category}
                onChange={(e) => setItemData({...itemData, category: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="medical_supply">Medical Supply</option>
                <option value="medication">Medication</option>
                <option value="injectable">Injectable</option>
                <option value="lab_supply">Lab Supply</option>
                <option value="equipment">Equipment</option>
                <option value="office_supply">Office Supply</option>
              </select>
              <input
                type="text"
                placeholder="SKU/Code"
                value={itemData.sku}
                onChange={(e) => setItemData({...itemData, sku: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <input
                type="number"
                placeholder="Current Stock"
                value={itemData.current_stock}
                onChange={(e) => setItemData({...itemData, current_stock: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                placeholder="Min Stock Level"
                value={itemData.min_stock_level}
                onChange={(e) => setItemData({...itemData, min_stock_level: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                step="0.01"
                placeholder="Unit Cost"
                value={itemData.unit_cost}
                onChange={(e) => setItemData({...itemData, unit_cost: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="Supplier"
                value={itemData.supplier}
                onChange={(e) => setItemData({...itemData, supplier: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="text"
                placeholder="Location"
                value={itemData.location}
                onChange={(e) => setItemData({...itemData, location: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
            </div>
            <textarea
              placeholder="Notes"
              value={itemData.notes}
              onChange={(e) => setItemData({...itemData, notes: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              rows="3"
            />
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowItemForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-orange-500 text-white rounded-lg"
              >
                Add Item
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  const TransactionForm = () => {
    const [transactionData, setTransactionData] = useState({
      transaction_type: 'in', quantity: 1, notes: '', created_by: 'Admin'
    });

    const handleTransactionSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/inventory/${selectedItem.id}/transaction`, {
          ...transactionData,
          quantity: parseInt(transactionData.quantity)
        });
        setShowTransactionForm(false);
        setSelectedItem(null);
        setTransactionData({
          transaction_type: 'in', quantity: 1, notes: '', created_by: 'Admin'
        });
        fetchInventory();
      } catch (error) {
        console.error("Error creating transaction:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-lg w-full mx-4">
          <h3 className="text-xl font-bold mb-4">
            Inventory Transaction: {selectedItem?.name}
          </h3>
          <form onSubmit={handleTransactionSubmit} className="space-y-4">
            <select
              value={transactionData.transaction_type}
              onChange={(e) => setTransactionData({...transactionData, transaction_type: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            >
              <option value="in">Stock In (Add)</option>
              <option value="out">Stock Out (Remove)</option>
              <option value="adjustment">Adjustment</option>
            </select>
            <input
              type="number"
              placeholder="Quantity"
              value={transactionData.quantity}
              onChange={(e) => setTransactionData({...transactionData, quantity: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
            <textarea
              placeholder="Notes/Reason"
              value={transactionData.notes}
              onChange={(e) => setTransactionData({...transactionData, notes: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              rows="3"
            />
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => setShowTransactionForm(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-green-500 text-white rounded-lg"
              >
                Process Transaction
              </button>
            </div>
          </form>
        </div>
      </div>
    );
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
            <h1 className="text-3xl font-bold text-white">Medical Inventory</h1>
          </div>
          <button
            onClick={() => setShowItemForm(true)}
            className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-2 rounded-lg font-medium"
          >
            + Add Item
          </button>
        </div>

        {/* Alerts for Low Stock */}
        {lowStockItems.length > 0 && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-xl p-4 mb-6">
            <h3 className="text-red-200 font-semibold mb-2">⚠️ Low Stock Alert</h3>
            <p className="text-red-200 text-sm">
              {lowStockItems.length} item(s) are running low on stock. Please reorder soon.
            </p>
          </div>
        )}

        {/* Inventory Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm">Total Items</p>
                <p className="text-3xl font-bold text-white">{inventory.length}</p>
              </div>
              <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">📦</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-200 text-sm">Low Stock</p>
                <p className="text-3xl font-bold text-white">{lowStockItems.length}</p>
              </div>
              <div className="w-12 h-12 bg-red-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">⚠️</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm">Total Value</p>
                <p className="text-3xl font-bold text-white">
                  ${inventory.reduce((total, item) => total + (item.current_stock * item.unit_cost), 0).toFixed(0)}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">💰</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm">Categories</p>
                <p className="text-3xl font-bold text-white">
                  {[...new Set(inventory.map(item => item.category))].length}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">📋</span>
              </div>
            </div>
          </div>
        </div>

        {/* Inventory Table */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl overflow-hidden border border-white/20">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/20">
                <tr>
                  <th className="text-left p-4 text-white font-semibold">Item Name</th>
                  <th className="text-left p-4 text-white font-semibold">Category</th>
                  <th className="text-left p-4 text-white font-semibold">SKU</th>
                  <th className="text-left p-4 text-white font-semibold">Current Stock</th>
                  <th className="text-left p-4 text-white font-semibold">Min Level</th>
                  <th className="text-left p-4 text-white font-semibold">Unit Cost</th>
                  <th className="text-left p-4 text-white font-semibold">Status</th>
                  <th className="text-left p-4 text-white font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {inventory.map((item) => (
                  <tr key={item.id} className="border-b border-white/10 hover:bg-white/5">
                    <td className="p-4 text-white font-medium">{item.name}</td>
                    <td className="p-4 text-blue-200 capitalize">{item.category?.replace('_', ' ')}</td>
                    <td className="p-4 text-blue-200">{item.sku || 'N/A'}</td>
                    <td className="p-4 text-white">{item.current_stock}</td>
                    <td className="p-4 text-blue-200">{item.min_stock_level}</td>
                    <td className="p-4 text-white">${item.unit_cost?.toFixed(2)}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-white text-xs rounded-full ${
                        item.current_stock === 0 ? 'bg-red-500' :
                        item.current_stock <= item.min_stock_level ? 'bg-yellow-500' : 'bg-green-500'
                      }`}>
                        {item.current_stock === 0 ? 'Out of Stock' :
                         item.current_stock <= item.min_stock_level ? 'Low Stock' : 'In Stock'}
                      </span>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => {
                          setSelectedItem(item);
                          setShowTransactionForm(true);
                        }}
                        className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm mr-2"
                      >
                        Transaction
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Forms */}
      {showItemForm && <ItemForm />}
      {showTransactionForm && <TransactionForm />}
    </div>
  );
};
const SmartFormsModule = ({ setActiveModule }) => {
  const [forms, setForms] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [selectedForm, setSelectedForm] = useState(null);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [showFormBuilder, setShowFormBuilder] = useState(false);
  const [showFormSubmission, setShowFormSubmission] = useState(false);
  const [showSubmissionViewer, setShowSubmissionViewer] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [activeTab, setActiveTab] = useState('forms');
  const [formFields, setFormFields] = useState([]);
  const [formTitle, setFormTitle] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formCategory, setFormCategory] = useState('custom');
  const [submissionData, setSubmissionData] = useState({});
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patients, setPatients] = useState([]);

  useEffect(() => {
    fetchForms();
    fetchTemplates();
    fetchPatients();
  }, []);

  const fetchForms = async () => {
    try {
      const response = await axios.get(`${API}/forms`, {
        params: { is_template: false }
      });
      setForms(response.data);
    } catch (error) {
      console.error("Error fetching forms:", error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/forms`, {
        params: { is_template: true }
      });
      setTemplates(response.data);
    } catch (error) {
      console.error("Error fetching templates:", error);
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

  const fetchSubmissions = async (formId = null) => {
    try {
      let url = `${API}/form-submissions`;
      if (formId) {
        url = `${API}/forms/${formId}/submissions`;
      }
      const response = await axios.get(url);
      setSubmissions(response.data);
    } catch (error) {
      console.error("Error fetching submissions:", error);
    }
  };

  const initializeTemplates = async () => {
    try {
      await axios.post(`${API}/forms/templates/init`);
      fetchTemplates();
      alert('Medical form templates initialized successfully!');
    } catch (error) {
      console.error("Error initializing templates:", error);
      alert('Error initializing templates. They may already exist.');
    }
  };

  const createFormFromTemplate = async (templateId, title, description) => {
    try {
      await axios.post(`${API}/forms/from-template/${templateId}`, {
        title,
        description
      });
      fetchForms();
      setShowTemplateSelector(false);
    } catch (error) {
      console.error("Error creating form from template:", error);
    }
  };

  const addField = (type) => {
    const newField = {
      id: Date.now().toString(),
      type,
      label: `${type.charAt(0).toUpperCase() + type.slice(1)} Field`,
      placeholder: '',
      required: false,
      options: type === 'select' ? ['Option 1', 'Option 2'] : [],
      smart_tag: '',
      validation_rules: {},
      order: formFields.length
    };
    setFormFields([...formFields, newField]);
  };

  const updateField = (fieldId, updates) => {
    setFormFields(formFields.map(field => 
      field.id === fieldId ? { ...field, ...updates } : field
    ));
  };

  const removeField = (fieldId) => {
    setFormFields(formFields.filter(field => field.id !== fieldId));
  };

  const saveForm = async () => {
    try {
      const formData = {
        title: formTitle,
        description: formDescription,
        category: formCategory,
        fields: formFields.map((field, index) => ({ ...field, order: index })),
        status: 'active',
        is_template: false
      };
      
      await axios.post(`${API}/forms`, formData);
      setShowFormBuilder(false);
      resetForm();
      fetchForms();
    } catch (error) {
      console.error("Error saving form:", error);
    }
  };

  const resetForm = () => {
    setFormTitle('');
    setFormDescription('');
    setFormCategory('custom');
    setFormFields([]);
  };

  const submitForm = async () => {
    if (!selectedPatient) {
      alert('Please select a patient');
      return;
    }

    try {
      await axios.post(`${API}/forms/${selectedForm.id}/submit`, submissionData, {
        params: {
          patient_id: selectedPatient.id
        }
      });
      
      setShowFormSubmission(false);
      setSubmissionData({});
      setSelectedForm(null);
      setSelectedPatient(null);
      alert('Form submitted successfully!');
    } catch (error) {
      console.error("Error submitting form:", error);
      alert('Error submitting form. Please try again.');
    }
  };

  const handleSubmissionInputChange = (fieldId, value) => {
    setSubmissionData({
      ...submissionData,
      [fieldId]: value
    });
  };

  const deleteForm = async (formId) => {
    if (window.confirm('Are you sure you want to delete this form?')) {
      try {
        await axios.delete(`${API}/forms/${formId}`);
        fetchForms();
      } catch (error) {
        console.error("Error deleting form:", error);
      }
    }
  };

  const smartTags = [
    '{patient_name}', '{patient_dob}', '{patient_gender}', '{patient_phone}',
    '{patient_address}', '{current_date}', '{current_time}', '{current_datetime}',
    '{provider_name}', '{clinic_name}', '{encounter_date}', '{chief_complaint}'
  ];

  const fieldTypes = [
    { type: 'text', label: 'Text Input', icon: '📝' },
    { type: 'textarea', label: 'Text Area', icon: '📄' },
    { type: 'number', label: 'Number', icon: '🔢' },
    { type: 'date', label: 'Date', icon: '📅' },
    { type: 'select', label: 'Dropdown', icon: '📋' },
    { type: 'checkbox', label: 'Checkbox', icon: '☑️' },
    { type: 'signature', label: 'Signature', icon: '✍️' },
    { type: 'file', label: 'File Upload', icon: '📎' }
  ];

  const categories = [
    { value: 'custom', label: 'Custom' },
    { value: 'intake', label: 'Patient Intake' },
    { value: 'vitals', label: 'Vital Signs' },
    { value: 'assessment', label: 'Assessment' },
    { value: 'discharge', label: 'Discharge' }
  ];

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
            <h1 className="text-3xl font-bold text-white">Smart Forms</h1>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowTemplateSelector(true)}
              className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg font-medium"
            >
              📋 Use Template
            </button>
            <button
              onClick={initializeTemplates}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium"
            >
              🏥 Init Medical Templates
            </button>
            <button
              onClick={() => setShowFormBuilder(true)}
              className="bg-green-500 hover:bg-green-600 text-white px-6 py-2 rounded-lg font-medium"
            >
              + Create Form
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-6 mb-8">
          {['forms', 'templates', 'submissions'].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === 'submissions') fetchSubmissions();
              }}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === tab
                  ? 'bg-white/20 text-white'
                  : 'text-blue-200 hover:text-white hover:bg-white/10'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Forms Tab */}
        {activeTab === 'forms' && (
          <div className="bg-white/10 backdrop-blur-md rounded-xl overflow-hidden border border-white/20">
            <div className="p-6 border-b border-white/20">
              <h2 className="text-xl font-bold text-white">Active Forms</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5 border-b border-white/20">
                  <tr>
                    <th className="text-left p-4 text-white font-semibold">Form Title</th>
                    <th className="text-left p-4 text-white font-semibold">Category</th>
                    <th className="text-left p-4 text-white font-semibold">Fields</th>
                    <th className="text-left p-4 text-white font-semibold">Status</th>
                    <th className="text-left p-4 text-white font-semibold">Created</th>
                    <th className="text-left p-4 text-white font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {forms.map((form) => (
                    <tr key={form.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="p-4 text-white font-medium">{form.title}</td>
                      <td className="p-4 text-blue-200 capitalize">{form.category?.replace('_', ' ')}</td>
                      <td className="p-4 text-blue-200">{form.fields?.length || 0} fields</td>
                      <td className="p-4">
                        <span className={`px-2 py-1 text-white text-xs rounded-full ${
                          form.status === 'active' ? 'bg-green-500' : 'bg-gray-500'
                        }`}>
                          {form.status}
                        </span>
                      </td>
                      <td className="p-4 text-blue-200">
                        {formatDate(form.created_at)}
                      </td>
                      <td className="p-4 space-x-2">
                        <button 
                          onClick={() => {
                            setSelectedForm(form);
                            setShowFormSubmission(true);
                          }}
                          className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded text-sm"
                        >
                          Fill Out
                        </button>
                        <button 
                          onClick={() => {
                            fetchSubmissions(form.id);
                            setSelectedForm(form);
                            setActiveTab('submissions');
                          }}
                          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                        >
                          Responses
                        </button>
                        <button 
                          onClick={() => deleteForm(form.id)}
                          className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <div className="bg-white/10 backdrop-blur-md rounded-xl overflow-hidden border border-white/20">
            <div className="p-6 border-b border-white/20">
              <h2 className="text-xl font-bold text-white">Medical Form Templates</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5 border-b border-white/20">
                  <tr>
                    <th className="text-left p-4 text-white font-semibold">Template Name</th>
                    <th className="text-left p-4 text-white font-semibold">Category</th>
                    <th className="text-left p-4 text-white font-semibold">Description</th>
                    <th className="text-left p-4 text-white font-semibold">Fields</th>
                    <th className="text-left p-4 text-white font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {templates.map((template) => (
                    <tr key={template.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="p-4 text-white font-medium">{template.title}</td>
                      <td className="p-4 text-blue-200 capitalize">{template.category?.replace('_', ' ')}</td>
                      <td className="p-4 text-blue-200">{template.description}</td>
                      <td className="p-4 text-blue-200">{template.fields?.length || 0} fields</td>
                      <td className="p-4">
                        <button 
                          onClick={() => {
                            const title = prompt('Enter form title:', template.title);
                            const description = prompt('Enter description (optional):', template.description);
                            if (title) {
                              createFormFromTemplate(template.id, title, description);
                            }
                          }}
                          className="bg-purple-500 hover:bg-purple-600 text-white px-3 py-1 rounded text-sm"
                        >
                          Use Template
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Submissions Tab */}
        {activeTab === 'submissions' && (
          <div className="bg-white/10 backdrop-blur-md rounded-xl overflow-hidden border border-white/20">
            <div className="p-6 border-b border-white/20">
              <h2 className="text-xl font-bold text-white">
                Form Submissions {selectedForm && `- ${selectedForm.title}`}
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5 border-b border-white/20">
                  <tr>
                    <th className="text-left p-4 text-white font-semibold">Form</th>
                    <th className="text-left p-4 text-white font-semibold">Patient</th>
                    <th className="text-left p-4 text-white font-semibold">Submitted</th>
                    <th className="text-left p-4 text-white font-semibold">Status</th>
                    <th className="text-left p-4 text-white font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((submission) => (
                    <tr key={submission.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="p-4 text-white font-medium">{submission.form_title}</td>
                      <td className="p-4 text-blue-200">{submission.patient_name}</td>
                      <td className="p-4 text-blue-200">
                        {formatDate(submission.submitted_at)}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 text-white text-xs rounded-full ${
                          submission.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'
                        }`}>
                          {submission.status}
                        </span>
                      </td>
                      <td className="p-4">
                        <button 
                          onClick={() => {
                            setSelectedSubmission(submission);
                            setShowSubmissionViewer(true);
                          }}
                          className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Enhanced Form Builder Modal */}
        {showFormBuilder && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-8">
                <h2 className="text-2xl font-bold mb-6">Smart Form Builder</h2>
                
                {/* Form Details */}
                <div className="mb-6 space-y-4">
                  <input
                    type="text"
                    placeholder="Form Title"
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg text-lg font-semibold"
                  />
                  <textarea
                    placeholder="Form Description"
                    value={formDescription}
                    onChange={(e) => setFormDescription(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    rows="3"
                  />
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  >
                    {categories.map((cat) => (
                      <option key={cat.value} value={cat.value}>{cat.label}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-3 gap-6">
                  {/* Field Types Panel */}
                  <div className="col-span-1">
                    <h3 className="text-lg font-semibold mb-4">Field Types</h3>
                    <div className="space-y-2">
                      {fieldTypes.map((fieldType) => (
                        <button
                          key={fieldType.type}
                          onClick={() => addField(fieldType.type)}
                          className="w-full p-3 bg-gray-100 hover:bg-gray-200 rounded-lg text-left flex items-center space-x-3"
                        >
                          <span className="text-xl">{fieldType.icon}</span>
                          <span>{fieldType.label}</span>
                        </button>
                      ))}
                    </div>

                    <div className="mt-6">
                      <h4 className="font-semibold mb-2">Smart Tags</h4>
                      <div className="space-y-1 max-h-48 overflow-y-auto">
                        {smartTags.map((tag) => (
                          <div 
                            key={tag} 
                            className="text-sm text-blue-600 font-mono cursor-pointer hover:bg-blue-50 p-1 rounded"
                            onClick={() => navigator.clipboard.writeText(tag)}
                            title="Click to copy"
                          >
                            {tag}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Enhanced Form Builder */}
                  <div className="col-span-2">
                    <h3 className="text-lg font-semibold mb-4">Form Preview</h3>
                    <div className="border border-gray-300 rounded-lg p-6 min-h-96 bg-gray-50">
                      {formFields.length === 0 ? (
                        <div className="text-center text-gray-500 py-12">
                          <p>Add field types from the left to build your form</p>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {formFields.map((field, index) => (
                            <div key={field.id} className="bg-white p-4 rounded-lg border">
                              <div className="flex justify-between items-start mb-3">
                                <input
                                  type="text"
                                  value={field.label}
                                  onChange={(e) => updateField(field.id, { label: e.target.value })}
                                  className="font-semibold text-lg border-b border-gray-300 bg-transparent flex-1 mr-4"
                                />
                                <button
                                  onClick={() => removeField(field.id)}
                                  className="text-red-500 hover:text-red-700"
                                >
                                  ✕
                                </button>
                              </div>
                              
                              <div className="grid grid-cols-2 gap-4 mb-3">
                                <input
                                  type="text"
                                  placeholder="Placeholder text"
                                  value={field.placeholder}
                                  onChange={(e) => updateField(field.id, { placeholder: e.target.value })}
                                  className="p-2 border border-gray-300 rounded"
                                />
                                <input
                                  type="text"
                                  placeholder="Smart tag (e.g., {patient_name})"
                                  value={field.smart_tag}
                                  onChange={(e) => updateField(field.id, { smart_tag: e.target.value })}
                                  className="p-2 border border-gray-300 rounded font-mono text-sm"
                                />
                              </div>

                              <div className="flex items-center space-x-4 mb-3">
                                <label className="flex items-center">
                                  <input
                                    type="checkbox"
                                    checked={field.required}
                                    onChange={(e) => updateField(field.id, { required: e.target.checked })}
                                    className="mr-2"
                                  />
                                  Required
                                </label>
                                
                                {field.type === 'select' && (
                                  <input
                                    type="text"
                                    placeholder="Options (comma-separated)"
                                    value={field.options.join(', ')}
                                    onChange={(e) => updateField(field.id, { 
                                      options: e.target.value.split(',').map(opt => opt.trim()).filter(opt => opt)
                                    })}
                                    className="p-2 border border-gray-300 rounded flex-1"
                                  />
                                )}
                                
                                {field.type === 'number' && (
                                  <div className="flex space-x-2">
                                    <input
                                      type="number"
                                      placeholder="Min"
                                      onChange={(e) => updateField(field.id, { 
                                        validation_rules: { ...field.validation_rules, min: e.target.value }
                                      })}
                                      className="p-2 border border-gray-300 rounded w-20"
                                    />
                                    <input
                                      type="number"
                                      placeholder="Max"
                                      onChange={(e) => updateField(field.id, { 
                                        validation_rules: { ...field.validation_rules, max: e.target.value }
                                      })}
                                      className="p-2 border border-gray-300 rounded w-20"
                                    />
                                  </div>
                                )}
                              </div>

                              {/* Enhanced Field Preview */}
                              <div className="mt-4 p-3 bg-gray-50 rounded">
                                <label className="block text-sm font-medium mb-1">
                                  {field.label} {field.required && <span className="text-red-500">*</span>}
                                </label>
                                {field.type === 'textarea' ? (
                                  <textarea
                                    placeholder={field.placeholder || field.smart_tag}
                                    className="w-full p-2 border border-gray-300 rounded"
                                    rows="3"
                                    disabled
                                  />
                                ) : field.type === 'select' ? (
                                  <select className="w-full p-2 border border-gray-300 rounded" disabled>
                                    <option>Select an option</option>
                                    {field.options.map((option, idx) => (
                                      <option key={idx} value={option}>{option}</option>
                                    ))}
                                  </select>
                                ) : field.type === 'checkbox' ? (
                                  <div className="flex items-center">
                                    <input type="checkbox" disabled className="mr-2" />
                                    <span>{field.placeholder || 'Checkbox option'}</span>
                                  </div>
                                ) : field.type === 'signature' ? (
                                  <div className="w-full h-24 border-2 border-dashed border-gray-300 rounded flex items-center justify-center text-gray-500">
                                    Signature Area
                                  </div>
                                ) : field.type === 'file' ? (
                                  <div className="w-full p-4 border-2 border-dashed border-gray-300 rounded flex items-center justify-center text-gray-500">
                                    📎 File Upload Area
                                  </div>
                                ) : (
                                  <input
                                    type={field.type}
                                    placeholder={field.placeholder || field.smart_tag}
                                    className="w-full p-2 border border-gray-300 rounded"
                                    min={field.validation_rules?.min}
                                    max={field.validation_rules?.max}
                                    disabled
                                  />
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-4 mt-6 pt-6 border-t">
                  <button
                    onClick={() => {
                      setShowFormBuilder(false);
                      resetForm();
                    }}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={saveForm}
                    disabled={!formTitle || formFields.length === 0}
                    className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50"
                  >
                    Save Form
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Form Submission Modal */}
        {showFormSubmission && selectedForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-8">
                <h2 className="text-2xl font-bold mb-6">{selectedForm.title}</h2>
                {selectedForm.description && (
                  <p className="text-gray-600 mb-6">{selectedForm.description}</p>
                )}

                {/* Patient Selection */}
                <div className="mb-6">
                  <label className="block text-sm font-medium mb-2">Select Patient *</label>
                  <select
                    value={selectedPatient?.id || ''}
                    onChange={(e) => {
                      const patient = patients.find(p => p.id === e.target.value);
                      setSelectedPatient(patient);
                    }}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Choose a patient...</option>
                    {patients.map((patient) => (
                      <option key={patient.id} value={patient.id}>
                        {patient.name[0].given[0]} {patient.name[0].family} - {patient.birth_date}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Form Fields */}
                <div className="space-y-6">
                  {selectedForm.fields
                    ?.sort((a, b) => (a.order || 0) - (b.order || 0))
                    .map((field) => (
                    <div key={field.id}>
                      <label className="block text-sm font-medium mb-2">
                        {field.label} {field.required && <span className="text-red-500">*</span>}
                      </label>
                      
                      {field.type === 'textarea' ? (
                        <textarea
                          placeholder={field.placeholder || field.smart_tag}
                          value={submissionData[field.id] || ''}
                          onChange={(e) => handleSubmissionInputChange(field.id, e.target.value)}
                          className="w-full p-3 border border-gray-300 rounded-lg"
                          rows="4"
                          required={field.required}
                        />
                      ) : field.type === 'select' ? (
                        <select
                          value={submissionData[field.id] || ''}
                          onChange={(e) => handleSubmissionInputChange(field.id, e.target.value)}
                          className="w-full p-3 border border-gray-300 rounded-lg"
                          required={field.required}
                        >
                          <option value="">Select an option</option>
                          {field.options?.map((option, idx) => (
                            <option key={idx} value={option}>{option}</option>
                          ))}
                        </select>
                      ) : field.type === 'checkbox' ? (
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={submissionData[field.id] || false}
                            onChange={(e) => handleSubmissionInputChange(field.id, e.target.checked)}
                            className="mr-3 w-4 h-4"
                          />
                          <span>{field.placeholder || 'Check if applicable'}</span>
                        </div>
                      ) : field.type === 'signature' ? (
                        <div className="w-full h-32 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center text-gray-500">
                          <span>✍️ Signature capture would be implemented here</span>
                        </div>
                      ) : field.type === 'file' ? (
                        <input
                          type="file"
                          onChange={(e) => {
                            // File handling would be implemented here
                            console.log('File selected:', e.target.files[0]);
                          }}
                          className="w-full p-3 border border-gray-300 rounded-lg"
                        />
                      ) : (
                        <input
                          type={field.type}
                          placeholder={field.placeholder || field.smart_tag}
                          value={submissionData[field.id] || ''}
                          onChange={(e) => handleSubmissionInputChange(field.id, e.target.value)}
                          className="w-full p-3 border border-gray-300 rounded-lg"
                          min={field.validation_rules?.min}
                          max={field.validation_rules?.max}
                          required={field.required}
                        />
                      )}
                    </div>
                  ))}
                </div>

                <div className="flex justify-end space-x-4 mt-8 pt-6 border-t">
                  <button
                    onClick={() => {
                      setShowFormSubmission(false);
                      setSubmissionData({});
                      setSelectedForm(null);
                      setSelectedPatient(null);
                    }}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={submitForm}
                    disabled={!selectedPatient}
                    className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
                  >
                    Submit Form
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Submission Viewer Modal */}
        {showSubmissionViewer && selectedSubmission && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-8">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold">{selectedSubmission.form_title}</h2>
                    <p className="text-gray-600">
                      Submitted by {selectedSubmission.submitted_by} on {formatDate(selectedSubmission.submitted_at)}
                    </p>
                    <p className="text-gray-600">
                      Patient: {selectedSubmission.patient_name}
                    </p>
                  </div>
                  <span className={`px-3 py-1 text-white text-sm rounded-full ${
                    selectedSubmission.status === 'completed' ? 'bg-green-500' : 'bg-yellow-500'
                  }`}>
                    {selectedSubmission.status}
                  </span>
                </div>

                {/* Submission Data */}
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Form Responses</h3>
                    <div className="bg-gray-50 rounded-lg p-6">
                      {Object.entries(selectedSubmission.data || {}).map(([key, value]) => (
                        <div key={key} className="mb-4 last:mb-0">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </label>
                          <div className="text-gray-900">
                            {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Processed Data with Smart Tags */}
                  {selectedSubmission.processed_data && Object.keys(selectedSubmission.processed_data).length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">Processed Data (Smart Tags Applied)</h3>
                      <div className="bg-blue-50 rounded-lg p-6">
                        {Object.entries(selectedSubmission.processed_data).map(([key, value]) => (
                          <div key={key} className="mb-4 last:mb-0">
                            <label className="block text-sm font-medium text-blue-700 mb-1">
                              {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </label>
                            <div className="text-blue-900">
                              {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* FHIR Data */}
                  {selectedSubmission.fhir_data && (
                    <div>
                      <h3 className="text-lg font-semibold mb-4">FHIR Data</h3>
                      <div className="bg-green-50 rounded-lg p-6">
                        <pre className="text-sm text-green-800 overflow-x-auto">
                          {JSON.stringify(selectedSubmission.fhir_data, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end mt-8 pt-6 border-t">
                  <button
                    onClick={() => {
                      setShowSubmissionViewer(false);
                      setSelectedSubmission(null);
                    }}
                    className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Template Selector Modal */}
        {showTemplateSelector && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-8">
                <h2 className="text-2xl font-bold mb-6">Choose a Medical Form Template</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {templates.map((template) => (
                    <div key={template.id} className="border border-gray-300 rounded-lg p-6 hover:border-blue-500 transition-colors">
                      <h3 className="text-lg font-semibold mb-2">{template.title}</h3>
                      <p className="text-gray-600 mb-4">{template.description}</p>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-500 capitalize">
                          {template.category?.replace('_', ' ')} • {template.fields?.length || 0} fields
                        </span>
                        <button
                          onClick={() => {
                            const title = prompt('Enter form title:', template.title);
                            const description = prompt('Enter description (optional):', template.description);
                            if (title) {
                              createFormFromTemplate(template.id, title, description);
                            }
                          }}
                          className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
                        >
                          Use Template
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-end mt-8 pt-6 border-t">
                  <button
                    onClick={() => setShowTemplateSelector(false)}
                    className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Forms List - Remove this section since it's now in the tabs */}
      </div>
    </div>
  );
};

// Comprehensive Employee Management Module
const EmployeeModule = ({ setActiveModule }) => {
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [showEmployeeForm, setShowEmployeeForm] = useState(false);
  const [showDocumentForm, setShowDocumentForm] = useState(false);
  const [showTimeEntry, setShowTimeEntry] = useState(false);
  const [showScheduleForm, setShowScheduleForm] = useState(false);
  const [employeeDashboard, setEmployeeDashboard] = useState(null);

  useEffect(() => {
    fetchEmployees();
  }, []);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(`${API}/enhanced-employees`);
      setEmployees(response.data);
    } catch (error) {
      console.error("Error fetching employees:", error);
    }
  };

  const fetchEmployeeDashboard = async (employeeId) => {
    try {
      const response = await axios.get(`${API}/employees/${employeeId}/dashboard`);
      setEmployeeDashboard(response.data);
    } catch (error) {
      console.error("Error fetching employee dashboard:", error);
    }
  };

  const handleEmployeeSelect = (employee) => {
    setSelectedEmployee(employee);
    fetchEmployeeDashboard(employee.id);
    setActiveTab('overview');
  };

  // Employee Creation Form
  const EmployeeForm = () => {
    const [formData, setFormData] = useState({
      first_name: '', last_name: '', email: '', phone: '',
      role: 'nurse', department: '', hire_date: '',
      salary: '', hourly_rate: '', employment_type: 'full_time'
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const submitData = {
          ...formData,
          salary: formData.salary ? parseFloat(formData.salary) : null,
          hourly_rate: formData.hourly_rate ? parseFloat(formData.hourly_rate) : null
        };
        await axios.post(`${API}/enhanced-employees`, submitData);
        setShowEmployeeForm(false);
        setFormData({
          first_name: '', last_name: '', email: '', phone: '',
          role: 'nurse', department: '', hire_date: '',
          salary: '', hourly_rate: '', employment_type: 'full_time'
        });
        fetchEmployees();
      } catch (error) {
        console.error("Error creating employee:", error);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-bold mb-4">Add New Employee</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <input
                type="text"
                placeholder="First Name *"
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
              <input
                type="text"
                placeholder="Last Name *"
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <input
                type="email"
                placeholder="Email *"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
              <input
                type="tel"
                placeholder="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <select
                value={formData.role}
                onChange={(e) => setFormData({...formData, role: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="doctor">Doctor</option>
                <option value="nurse">Nurse</option>
                <option value="admin">Admin</option>
                <option value="receptionist">Receptionist</option>
                <option value="technician">Technician</option>
              </select>
              <input
                type="text"
                placeholder="Department"
                value={formData.department}
                onChange={(e) => setFormData({...formData, department: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="date"
                placeholder="Hire Date *"
                value={formData.hire_date}
                onChange={(e) => setFormData({...formData, hire_date: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
                required
              />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <input
                type="number"
                step="0.01"
                placeholder="Annual Salary"
                value={formData.salary}
                onChange={(e) => setFormData({...formData, salary: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <input
                type="number"
                step="0.01"
                placeholder="Hourly Rate"
                value={formData.hourly_rate}
                onChange={(e) => setFormData({...formData, hourly_rate: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              />
              <select
                value={formData.employment_type}
                onChange={(e) => setFormData({...formData, employment_type: e.target.value})}
                className="p-3 border border-gray-300 rounded-lg"
              >
                <option value="full_time">Full Time</option>
                <option value="part_time">Part Time</option>
                <option value="contract">Contract</option>
              </select>
            </div>
            <div className="flex justify-end space-x-4 pt-4">
              <button
                type="button"
                onClick={() => setShowEmployeeForm(false)}
                className="px-6 py-2 border border-gray-300 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-6 py-2 bg-indigo-500 text-white rounded-lg"
              >
                Add Employee
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Time Clock Component
  const TimeClock = ({ employee }) => {
    const [currentStatus, setCurrentStatus] = useState('not_clocked_in');
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
      if (employee) {
        fetchCurrentStatus();
      }
    }, [employee]);

    const fetchCurrentStatus = async () => {
      try {
        const response = await axios.get(`${API}/time-entries/employee/${employee.id}/current-status`);
        setCurrentStatus(response.data.status);
      } catch (error) {
        console.error("Error fetching status:", error);
      }
    };

    const clockAction = async (action) => {
      setIsLoading(true);
      try {
        await axios.post(`${API}/time-entries`, {
          employee_id: employee.id,
          entry_type: action,
          location: 'Main Office'
        });
        fetchCurrentStatus();
        fetchEmployeeDashboard(employee.id);
      } catch (error) {
        console.error("Error with clock action:", error);
      }
      setIsLoading(false);
    };

    const getStatusColor = () => {
      switch (currentStatus) {
        case 'clocked_in': return 'bg-green-500';
        case 'on_break': return 'bg-yellow-500';
        case 'clocked_out': return 'bg-gray-500';
        default: return 'bg-red-500';
      }
    };

    const getStatusText = () => {
      switch (currentStatus) {
        case 'clocked_in': return 'Clocked In';
        case 'on_break': return 'On Break';
        case 'clocked_out': return 'Clocked Out';
        default: return 'Not Clocked In';
      }
    };

    return (
      <div className="bg-white/5 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Time Clock</h3>
        <div className="text-center">
          <div className={`w-20 h-20 ${getStatusColor()} rounded-full flex items-center justify-center mx-auto mb-4`}>
            <span className="text-white text-2xl">⏰</span>
          </div>
          <p className="text-white text-lg font-medium mb-4">{getStatusText()}</p>
          <div className="grid grid-cols-2 gap-3">
            {currentStatus === 'not_clocked_in' || currentStatus === 'clocked_out' ? (
              <button
                onClick={() => clockAction('clock_in')}
                disabled={isLoading}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                Clock In
              </button>
            ) : (
              <button
                onClick={() => clockAction('clock_out')}
                disabled={isLoading}
                className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                Clock Out
              </button>
            )}
            
            {currentStatus === 'clocked_in' ? (
              <button
                onClick={() => clockAction('break_start')}
                disabled={isLoading}
                className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                Start Break
              </button>
            ) : currentStatus === 'on_break' ? (
              <button
                onClick={() => clockAction('break_end')}
                disabled={isLoading}
                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50"
              >
                End Break
              </button>
            ) : (
              <div></div>
            )}
          </div>
        </div>
      </div>
    );
  };

  if (selectedEmployee) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Employee Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setSelectedEmployee(null)}
                className="text-blue-200 hover:text-white"
              >
                ← Back to Employees
              </button>
              <div className="flex items-center space-x-4">
                {selectedEmployee.profile_picture && (
                  <img 
                    src={`data:image/jpeg;base64,${selectedEmployee.profile_picture}`}
                    alt="Profile"
                    className="w-16 h-16 rounded-full object-cover"
                  />
                )}
                <div>
                  <h1 className="text-3xl font-bold text-white">
                    {selectedEmployee.first_name} {selectedEmployee.last_name}
                  </h1>
                  <p className="text-blue-200">
                    {selectedEmployee.role} • {selectedEmployee.department} • {selectedEmployee.employee_id}
                  </p>
                </div>
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowDocumentForm(true)}
                className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
              >
                + Create Document
              </button>
              <button
                onClick={() => setShowScheduleForm(true)}
                className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg"
              >
                + Schedule Shift
              </button>
            </div>
          </div>

          {/* Employee Tabs */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
            <div className="border-b border-white/20">
              <nav className="flex space-x-8 px-6">
                {['overview', 'profile', 'documents', 'schedule', 'timesheet', 'payroll'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`py-4 px-2 border-b-2 font-medium text-sm capitalize ${
                      activeTab === tab
                        ? 'border-indigo-400 text-indigo-400'
                        : 'border-transparent text-blue-200 hover:text-white'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </nav>
            </div>

            <div className="p-6">
              {activeTab === 'overview' && employeeDashboard && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Time Clock */}
                    <TimeClock employee={selectedEmployee} />

                    {/* Quick Stats */}
                    <div className="bg-white/5 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">This Week</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-blue-200">Hours Worked:</span>
                          <span className="text-white font-medium">
                            {employeeDashboard.week_hours?.total_hours || 0}h
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-blue-200">Regular Hours:</span>
                          <span className="text-white font-medium">
                            {employeeDashboard.week_hours?.regular_hours || 0}h
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-blue-200">Overtime Hours:</span>
                          <span className="text-white font-medium">
                            {employeeDashboard.week_hours?.overtime_hours || 0}h
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-blue-200">Vacation Days Left:</span>
                          <span className="text-white font-medium">
                            {selectedEmployee.vacation_days_allocated - selectedEmployee.vacation_days_used}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Upcoming Shifts */}
                  <div className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Upcoming Shifts</h3>
                    {employeeDashboard.upcoming_shifts?.length > 0 ? (
                      <div className="space-y-3">
                        {employeeDashboard.upcoming_shifts.map((shift) => (
                          <div key={shift.id} className="flex items-center justify-between p-3 bg-white/10 rounded-lg">
                            <div>
                              <p className="text-white font-medium">
                                {formatDate(shift.shift_date)}
                              </p>
                              <p className="text-blue-200 text-sm">
                                {new Date(shift.start_time).toLocaleTimeString()} - {new Date(shift.end_time).toLocaleTimeString()}
                              </p>
                            </div>
                            <span className={`px-2 py-1 text-white text-xs rounded-full ${
                              shift.status === 'completed' ? 'bg-green-500' : 
                              shift.status === 'in_progress' ? 'bg-blue-500' : 'bg-gray-500'
                            }`}>
                              {shift.status}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-blue-200">No upcoming shifts scheduled</p>
                    )}
                  </div>

                  {/* Pending Documents */}
                  <div className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Pending Documents</h3>
                    {employeeDashboard.pending_documents?.length > 0 ? (
                      <div className="space-y-3">
                        {employeeDashboard.pending_documents.map((doc) => (
                          <div key={doc.id} className="flex items-center justify-between p-3 bg-white/10 rounded-lg">
                            <div>
                              <p className="text-white font-medium">{doc.title}</p>
                              <p className="text-blue-200 text-sm capitalize">
                                {doc.document_type.replace('_', ' ')}
                              </p>
                            </div>
                            <span className="px-2 py-1 bg-yellow-500 text-white text-xs rounded-full">
                              {doc.status.replace('_', ' ')}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-blue-200">No pending documents</p>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'profile' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Personal Information */}
                    <div className="bg-white/5 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Personal Information</h3>
                      <div className="space-y-3">
                        <div>
                          <label className="text-blue-200 text-sm">Full Name</label>
                          <p className="text-white">{selectedEmployee.first_name} {selectedEmployee.last_name}</p>
                        </div>
                        <div>
                          <label className="text-blue-200 text-sm">Email</label>
                          <p className="text-white">{selectedEmployee.email}</p>
                        </div>
                        <div>
                          <label className="text-blue-200 text-sm">Phone</label>
                          <p className="text-white">{selectedEmployee.phone || 'N/A'}</p>
                        </div>
                        <div>
                          <label className="text-blue-200 text-sm">Date of Birth</label>
                          <p className="text-white">{formatDate(selectedEmployee.date_of_birth)}</p>
                        </div>
                      </div>
                    </div>

                    {/* Employment Details */}
                    <div className="bg-white/5 rounded-lg p-6">
                      <h3 className="text-lg font-semibold text-white mb-4">Employment Details</h3>
                      <div className="space-y-3">
                        <div>
                          <label className="text-blue-200 text-sm">Employee ID</label>
                          <p className="text-white">{selectedEmployee.employee_id}</p>
                        </div>
                        <div>
                          <label className="text-blue-200 text-sm">Role</label>
                          <p className="text-white capitalize">{selectedEmployee.role}</p>
                        </div>
                        <div>
                          <label className="text-blue-200 text-sm">Department</label>
                          <p className="text-white">{selectedEmployee.department || 'N/A'}</p>
                        </div>
                        <div>
                          <label className="text-blue-200 text-sm">Hire Date</label>
                          <p className="text-white">{formatDate(selectedEmployee.hire_date)}</p>
                        </div>
                        <div>
                          <label className="text-blue-200 text-sm">Employment Type</label>
                          <p className="text-white capitalize">{selectedEmployee.employment_type?.replace('_', ' ')}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Emergency Contact */}
                  <div className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-lg font-semibold text-white mb-4">Emergency Contact</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div>
                        <label className="text-blue-200 text-sm">Name</label>
                        <p className="text-white">{selectedEmployee.emergency_contact_name || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-blue-200 text-sm">Phone</label>
                        <p className="text-white">{selectedEmployee.emergency_contact_phone || 'N/A'}</p>
                      </div>
                      <div>
                        <label className="text-blue-200 text-sm">Relationship</label>
                        <p className="text-white">{selectedEmployee.emergency_contact_relationship || 'N/A'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Add other tabs content here - documents, schedule, timesheet, payroll */}
            </div>
          </div>
        </div>

        {/* Forms */}
        {showDocumentForm && <div>Document Form Placeholder</div>}
        {showScheduleForm && <div>Schedule Form Placeholder</div>}
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
            <h1 className="text-3xl font-bold text-white">Employee Management</h1>
          </div>
          <button
            onClick={() => setShowEmployeeForm(true)}
            className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-2 rounded-lg font-medium"
          >
            + Add Employee
          </button>
        </div>

        {/* Employee Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-200 text-sm">Total Employees</p>
                <p className="text-3xl font-bold text-white">{employees.length}</p>
              </div>
              <div className="w-12 h-12 bg-indigo-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">👨‍⚕️</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-200 text-sm">Active Today</p>
                <p className="text-3xl font-bold text-white">
                  {employees.filter(emp => emp.is_active).length}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">✅</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-200 text-sm">Departments</p>
                <p className="text-3xl font-bold text-white">
                  {[...new Set(employees.map(emp => emp.department).filter(Boolean))].length}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">🏢</span>
              </div>
            </div>
          </div>

          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-yellow-200 text-sm">New This Month</p>
                <p className="text-3xl font-bold text-white">
                  {employees.filter(emp => {
                    const hireDate = new Date(emp.hire_date);
                    const thisMonth = new Date();
                    return hireDate.getMonth() === thisMonth.getMonth() && 
                           hireDate.getFullYear() === thisMonth.getFullYear();
                  }).length}
                </p>
              </div>
              <div className="w-12 h-12 bg-yellow-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">🆕</span>
              </div>
            </div>
          </div>
        </div>

        {/* Employee List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl overflow-hidden border border-white/20">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/20">
                <tr>
                  <th className="text-left p-4 text-white font-semibold">Employee</th>
                  <th className="text-left p-4 text-white font-semibold">Role</th>
                  <th className="text-left p-4 text-white font-semibold">Department</th>
                  <th className="text-left p-4 text-white font-semibold">Hire Date</th>
                  <th className="text-left p-4 text-white font-semibold">Employment</th>
                  <th className="text-left p-4 text-white font-semibold">Status</th>
                  <th className="text-left p-4 text-white font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((employee) => (
                  <tr key={employee.id} className="border-b border-white/10 hover:bg-white/5">
                    <td className="p-4">
                      <div className="flex items-center space-x-3">
                        {employee.profile_picture ? (
                          <img 
                            src={`data:image/jpeg;base64,${employee.profile_picture}`}
                            alt="Profile"
                            className="w-10 h-10 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center">
                            <span className="text-white font-medium">
                              {employee.first_name.charAt(0)}{employee.last_name.charAt(0)}
                            </span>
                          </div>
                        )}
                        <div>
                          <p className="text-white font-medium">
                            {employee.first_name} {employee.last_name}
                          </p>
                          <p className="text-blue-200 text-sm">{employee.employee_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 text-blue-200 capitalize">{employee.role}</td>
                    <td className="p-4 text-blue-200">{employee.department || 'N/A'}</td>
                    <td className="p-4 text-blue-200">{formatDate(employee.hire_date)}</td>
                    <td className="p-4 text-blue-200 capitalize">
                      {employee.employment_type?.replace('_', ' ')}
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-white text-xs rounded-full ${
                        employee.is_active ? 'bg-green-500' : 'bg-red-500'
                      }`}>
                        {employee.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="p-4">
                      <button
                        onClick={() => handleEmployeeSelect(employee)}
                        className="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-1 rounded text-sm"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Forms */}
      {showEmployeeForm && <EmployeeForm />}
    </div>
  );
};

// Scheduling Module
const SchedulingModule = ({ setActiveModule }) => {
  const [appointments, setAppointments] = useState([]);
  const [providers, setProviders] = useState([]);
  const [patients, setPatients] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [calendarView, setCalendarView] = useState('week');
  const [showAppointmentForm, setShowAppointmentForm] = useState(false);
  const [showProviderForm, setShowProviderForm] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [calendarData, setCalendarData] = useState({});
  const [activeTab, setActiveTab] = useState('calendar');

  useEffect(() => {
    fetchProviders();
    fetchPatients();
    fetchCalendarData();
  }, [selectedDate, calendarView]);

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`);
      setProviders(response.data);
    } catch (error) {
      console.error("Error fetching providers:", error);
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

  const fetchCalendarData = async () => {
    try {
      const response = await axios.get(`${API}/appointments/calendar`, {
        params: {
          date: selectedDate,
          view: calendarView
        }
      });
      setCalendarData(response.data);
    } catch (error) {
      console.error("Error fetching calendar:", error);
    }
  };

  const createAppointment = async (appointmentData) => {
    try {
      await axios.post(`${API}/appointments`, appointmentData);
      setShowAppointmentForm(false);
      fetchCalendarData();
    } catch (error) {
      console.error("Error creating appointment:", error);
      alert('Error creating appointment: ' + (error.response?.data?.detail || 'Unknown error'));
    }
  };

  const updateAppointmentStatus = async (appointmentId, status) => {
    try {
      await axios.put(`${API}/appointments/${appointmentId}/status`, null, {
        params: { status }
      });
      fetchCalendarData();
    } catch (error) {
      console.error("Error updating appointment:", error);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      scheduled: 'bg-blue-500',
      confirmed: 'bg-green-500',
      arrived: 'bg-yellow-500',
      in_progress: 'bg-purple-500',
      completed: 'bg-gray-500',
      cancelled: 'bg-red-500',
      no_show: 'bg-red-700'
    };
    return colors[status] || 'bg-gray-400';
  };

  const AppointmentForm = () => {
    const [formData, setFormData] = useState({
      patient_id: '',
      provider_id: '',
      appointment_date: selectedDate,
      start_time: '09:00',
      end_time: '09:30',
      appointment_type: 'consultation',
      reason: '',
      notes: '',
      location: 'Main Office',
      room: ''
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      createAppointment(formData);
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <h2 className="text-xl font-bold mb-4">Schedule New Appointment</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Patient *</label>
                  <select
                    value={formData.patient_id}
                    onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Select Patient</option>
                    {patients.map((patient) => (
                      <option key={patient.id} value={patient.id}>
                        {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Provider *</label>
                  <select
                    value={formData.provider_id}
                    onChange={(e) => setFormData({...formData, provider_id: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  >
                    <option value="">Select Provider</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {provider.title} {provider.first_name} {provider.last_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Date *</label>
                  <input
                    type="date"
                    value={formData.appointment_date}
                    onChange={(e) => setFormData({...formData, appointment_date: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Start Time *</label>
                  <input
                    type="time"
                    value={formData.start_time}
                    onChange={(e) => setFormData({...formData, start_time: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">End Time *</label>
                  <input
                    type="time"
                    value={formData.end_time}
                    onChange={(e) => setFormData({...formData, end_time: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Appointment Type</label>
                  <select
                    value={formData.appointment_type}
                    onChange={(e) => setFormData({...formData, appointment_type: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  >
                    <option value="consultation">Consultation</option>
                    <option value="follow_up">Follow Up</option>
                    <option value="procedure">Procedure</option>
                    <option value="urgent">Urgent</option>
                    <option value="physical_exam">Physical Exam</option>
                    <option value="vaccination">Vaccination</option>
                    <option value="lab_work">Lab Work</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Location</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({...formData, location: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    placeholder="Main Office"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Reason for Visit *</label>
                <input
                  type="text"
                  value={formData.reason}
                  onChange={(e) => setFormData({...formData, reason: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  placeholder="Brief description of visit reason"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  rows="3"
                  placeholder="Additional notes or instructions"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowAppointmentForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  Schedule Appointment
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-200 hover:text-white"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Scheduling</h1>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowProviderForm(true)}
              className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
            >
              + Add Provider
            </button>
            <button
              onClick={() => setShowAppointmentForm(true)}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg"
            >
              + Schedule Appointment
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-6 mb-8">
          {['calendar', 'appointments', 'providers'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === tab
                  ? 'bg-white/20 text-white'
                  : 'text-blue-200 hover:text-white hover:bg-white/10'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Calendar Tab */}
        {activeTab === 'calendar' && (
          <div className="space-y-6">
            {/* Calendar Controls */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
              <div className="flex justify-between items-center">
                <div className="flex space-x-4">
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="p-2 rounded-lg border border-gray-300"
                  />
                  <select
                    value={calendarView}
                    onChange={(e) => setCalendarView(e.target.value)}
                    className="p-2 rounded-lg border border-gray-300"
                  >
                    <option value="day">Day View</option>
                    <option value="week">Week View</option>
                    <option value="month">Month View</option>
                  </select>
                </div>
                <div className="text-white">
                  {calendarData.date_range?.from} to {calendarData.date_range?.to}
                </div>
              </div>
            </div>

            {/* Calendar Grid */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 overflow-hidden">
              <div className="p-6">
                <h2 className="text-xl font-bold text-white mb-4">
                  {calendarView.charAt(0).toUpperCase() + calendarView.slice(1)} View
                </h2>
                {Object.keys(calendarData.calendar_data || {}).length > 0 ? (
                  <div className="space-y-6">
                    {Object.entries(calendarData.calendar_data).map(([date, providers]) => (
                      <div key={date} className="border-b border-white/10 pb-4 last:border-b-0">
                        <h3 className="text-lg font-semibold text-white mb-3">
                          {new Date(date).toLocaleDateString('en-US', { 
                            weekday: 'long', 
                            year: 'numeric', 
                            month: 'long', 
                            day: 'numeric' 
                          })}
                        </h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {Object.entries(providers).map(([providerId, providerData]) => (
                            <div key={providerId} className="bg-white/5 rounded-lg p-4">
                              <h4 className="font-medium text-blue-200 mb-3">
                                {providerData.provider_name}
                              </h4>
                              <div className="space-y-2">
                                {providerData.appointments.length > 0 ? (
                                  providerData.appointments.map((appointment) => (
                                    <div
                                      key={appointment.id}
                                      className={`p-3 rounded-lg text-white text-sm ${getStatusColor(appointment.status)}`}
                                      onClick={() => setSelectedAppointment(appointment)}
                                    >
                                      <div className="font-medium">
                                        {appointment.start_time} - {appointment.patient_name}
                                      </div>
                                      <div className="text-xs opacity-80">
                                        {appointment.reason}
                                      </div>
                                    </div>
                                  ))
                                ) : (
                                  <div className="text-blue-300 text-sm">No appointments</div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-blue-300 text-2xl">📅</span>
                    </div>
                    <p className="text-blue-200">No appointments scheduled</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Appointments Tab */}
        {activeTab === 'appointments' && (
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 overflow-hidden">
            <div className="p-6 border-b border-white/20">
              <h2 className="text-xl font-bold text-white">All Appointments</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5">
                  <tr>
                    <th className="text-left p-4 text-white">Date & Time</th>
                    <th className="text-left p-4 text-white">Patient</th>
                    <th className="text-left p-4 text-white">Provider</th>
                    <th className="text-left p-4 text-white">Type</th>
                    <th className="text-left p-4 text-white">Status</th>
                    <th className="text-left p-4 text-white">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-white/10">
                    <td colSpan="6" className="p-8 text-center text-blue-200">
                      Loading appointments...
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Providers Tab */}
        {activeTab === 'providers' && (
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 overflow-hidden">
            <div className="p-6 border-b border-white/20">
              <h2 className="text-xl font-bold text-white">Healthcare Providers</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5">
                  <tr>
                    <th className="text-left p-4 text-white">Name</th>
                    <th className="text-left p-4 text-white">Title</th>
                    <th className="text-left p-4 text-white">Specialties</th>
                    <th className="text-left p-4 text-white">Schedule</th>
                    <th className="text-left p-4 text-white">Status</th>
                    <th className="text-left p-4 text-white">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {providers.map((provider) => (
                    <tr key={provider.id} className="border-b border-white/10 hover:bg-white/5">
                      <td className="p-4 text-white font-medium">
                        {provider.title} {provider.first_name} {provider.last_name}
                      </td>
                      <td className="p-4 text-blue-200">{provider.title}</td>
                      <td className="p-4 text-blue-200">
                        {provider.specialties?.join(', ') || 'General Practice'}
                      </td>
                      <td className="p-4 text-blue-200">
                        {provider.schedule_start_time} - {provider.schedule_end_time}
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 text-white text-xs rounded-full ${
                          provider.is_active ? 'bg-green-500' : 'bg-red-500'
                        }`}>
                          {provider.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="p-4">
                        <button className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                          View Schedule
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Forms */}
        {showAppointmentForm && <AppointmentForm />}
      </div>
    </div>
  );
};

// Patient Communications Module
const CommunicationsModule = ({ setActiveModule }) => {
  const [messages, setMessages] = useState([]);
  const [patients, setPatients] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [showComposeForm, setShowComposeForm] = useState(false);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [showMessageViewer, setShowMessageViewer] = useState(false);
  const [activeTab, setActiveTab] = useState('inbox');

  useEffect(() => {
    fetchMessages();
    fetchPatients();
    fetchTemplates();
  }, []);

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/communications/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error("Error fetching messages:", error);
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

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/communications/templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error("Error fetching templates:", error);
    }
  };

  const initializeTemplates = async () => {
    try {
      await axios.post(`${API}/communications/init-templates`);
      fetchTemplates();
      alert('Communication templates initialized successfully!');
    } catch (error) {
      console.error("Error initializing templates:", error);
      alert('Error initializing templates. They may already exist.');
    }
  };

  const sendMessage = async (messageData) => {
    try {
      await axios.post(`${API}/communications/send`, messageData);
      setShowComposeForm(false);
      fetchMessages();
    } catch (error) {
      console.error("Error sending message:", error);
      alert('Error sending message. Please try again.');
    }
  };

  const markAsRead = async (messageId) => {
    try {
      await axios.put(`${API}/communications/messages/${messageId}/read`);
      fetchMessages();
    } catch (error) {
      console.error("Error marking message as read:", error);
    }
  };

  const ComposeMessageForm = () => {
    const [formData, setFormData] = useState({
      patient_id: '',
      message_type: 'general',
      subject: '',
      content: '',
      template_id: ''
    });

    const handleTemplateSelect = (template) => {
      setFormData({
        ...formData,
        message_type: template.message_type,
        subject: template.subject_template,
        content: template.content_template,
        template_id: template.id
      });
    };

    const handleSubmit = (e) => {
      e.preventDefault();
      sendMessage(formData);
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <h2 className="text-xl font-bold mb-4">Compose Message</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Patient *</label>
                <select
                  value={formData.patient_id}
                  onChange={(e) => setFormData({...formData, patient_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map((patient) => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given?.[0]} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Use Template (Optional)</label>
                <select
                  value={formData.template_id}
                  onChange={(e) => {
                    const template = templates.find(t => t.id === e.target.value);
                    if (template) handleTemplateSelect(template);
                  }}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="">Select Template</option>
                  {templates.map((template) => (
                    <option key={template.id} value={template.id}>
                      {template.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Message Type</label>
                <select
                  value={formData.message_type}
                  onChange={(e) => setFormData({...formData, message_type: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="general">General</option>
                  <option value="appointment_reminder">Appointment Reminder</option>
                  <option value="follow_up">Follow Up</option>
                  <option value="test_results">Test Results</option>
                  <option value="billing">Billing</option>
                  <option value="prescription">Prescription</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Subject *</label>
                <input
                  type="text"
                  value={formData.subject}
                  onChange={(e) => setFormData({...formData, subject: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  placeholder="Message subject"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Message *</label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({...formData, content: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  rows="6"
                  placeholder="Type your message here..."
                  required
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowComposeForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
                >
                  Send Message
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-200 hover:text-white"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Patient Communications</h1>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={initializeTemplates}
              className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
            >
              📨 Init Templates
            </button>
            <button
              onClick={() => setShowComposeForm(true)}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg"
            >
              ✉️ Compose Message
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-6 mb-8">
          {['inbox', 'sent', 'templates'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg font-medium ${
                activeTab === tab
                  ? 'bg-white/20 text-white'
                  : 'text-blue-200 hover:text-white hover:bg-white/10'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Messages */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 overflow-hidden">
          <div className="p-6 border-b border-white/20">
            <h2 className="text-xl font-bold text-white">
              {activeTab === 'inbox' && 'Inbox'}
              {activeTab === 'sent' && 'Sent Messages'}
              {activeTab === 'templates' && 'Message Templates'}
            </h2>
          </div>

          {activeTab === 'inbox' && (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-white/5">
                  <tr>
                    <th className="text-left p-4 text-white">Patient</th>
                    <th className="text-left p-4 text-white">Subject</th>
                    <th className="text-left p-4 text-white">Type</th>
                    <th className="text-left p-4 text-white">Date</th>
                    <th className="text-left p-4 text-white">Status</th>
                    <th className="text-left p-4 text-white">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {messages.length > 0 ? (
                    messages.map((message) => (
                      <tr key={message.id} className="border-b border-white/10 hover:bg-white/5">
                        <td className="p-4 text-white font-medium">{message.patient_name}</td>
                        <td className="p-4 text-blue-200">{message.subject}</td>
                        <td className="p-4 text-blue-200 capitalize">
                          {message.message_type?.replace('_', ' ')}
                        </td>
                        <td className="p-4 text-blue-200">
                          {formatDate(message.sent_at)}
                        </td>
                        <td className="p-4">
                          <span className={`px-2 py-1 text-white text-xs rounded-full ${
                            message.status === 'read' ? 'bg-green-500' : 
                            message.status === 'delivered' ? 'bg-blue-500' : 'bg-yellow-500'
                          }`}>
                            {message.status}
                          </span>
                        </td>
                        <td className="p-4">
                          <button 
                            onClick={() => {
                              setSelectedMessage(message);
                              setShowMessageViewer(true);
                              if (message.status !== 'read') {
                                markAsRead(message.id);
                              }
                            }}
                            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="p-8 text-center text-blue-200">
                        No messages found
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'templates' && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {templates.map((template) => (
                  <div key={template.id} className="bg-white/5 rounded-lg p-4">
                    <h3 className="text-white font-semibold mb-2">{template.name}</h3>
                    <p className="text-blue-200 text-sm mb-3 capitalize">
                      Type: {template.message_type?.replace('_', ' ')}
                    </p>
                    <div className="bg-white/5 rounded p-3">
                      <p className="text-blue-200 text-sm">
                        <strong>Subject:</strong> {template.subject_template}
                      </p>
                      <p className="text-blue-200 text-sm mt-2">
                        <strong>Content:</strong> {template.content_template?.substring(0, 100)}...
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Forms */}
        {showComposeForm && <ComposeMessageForm />}
        
        {/* Message Viewer Modal */}
        {showMessageViewer && selectedMessage && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-xl font-bold">{selectedMessage.subject}</h2>
                    <p className="text-gray-600">
                      From: {selectedMessage.sender_name} | To: {selectedMessage.patient_name}
                    </p>
                    <p className="text-gray-500 text-sm">
                      {formatDate(selectedMessage.sent_at)}
                    </p>
                  </div>
                  <button
                    onClick={() => setShowMessageViewer(false)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    ✕
                  </button>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <pre className="whitespace-pre-wrap font-sans text-gray-800">
                    {selectedMessage.content}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


const DailyLogView = ({ setActiveModule }) => {
  const [dailyData, setDailyData] = useState({ visits: [], summary: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDailyLog();
  }, []);

  const fetchDailyLog = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/daily-log`);
      setDailyData(response.data);
    } catch (error) {
      console.error("Error fetching daily log:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-white text-center py-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Daily Log</h1>
            <p className="text-blue-200">Patients seen today with visit types and payments</p>
          </div>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg border border-white/20"
          >
            ← Back to Dashboard
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-green-200 text-sm">Patients Seen</h3>
            <p className="text-3xl font-bold text-white">{dailyData.summary.total_patients_seen || 0}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-green-200 text-sm">Total Revenue</h3>
            <p className="text-3xl font-bold text-white">${dailyData.summary.total_revenue?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-green-200 text-sm">Amount Paid</h3>
            <p className="text-3xl font-bold text-white">${dailyData.summary.total_paid?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-yellow-200 text-sm">Outstanding</h3>
            <p className="text-3xl font-bold text-white">${dailyData.summary.outstanding_amount?.toFixed(2) || '0.00'}</p>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 overflow-hidden">
          <div className="p-6 border-b border-white/20">
            <h2 className="text-xl font-bold text-white">Daily Visits - {dailyData.date}</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5">
                <tr>
                  <th className="text-left p-4 text-blue-200">Time</th>
                  <th className="text-left p-4 text-blue-200">Patient</th>
                  <th className="text-left p-4 text-blue-200">Visit Type</th>
                  <th className="text-left p-4 text-blue-200">Provider</th>
                  <th className="text-left p-4 text-blue-200">Amount</th>
                  <th className="text-left p-4 text-blue-200">Paid</th>
                  <th className="text-left p-4 text-blue-200">Status</th>
                </tr>
              </thead>
              <tbody>
                {dailyData.visits.map((visit, index) => (
                  <tr key={index} className="border-b border-white/10 hover:bg-white/5">
                    <td className="p-4 text-white">
                      {new Date(visit.completed_time).toLocaleTimeString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td className="p-4 text-white font-medium">{visit.patient_name}</td>
                    <td className="p-4 text-blue-200">{visit.visit_type}</td>
                    <td className="p-4 text-blue-200">{visit.provider}</td>
                    <td className="p-4 text-white">${visit.total_amount?.toFixed(2) || '0.00'}</td>
                    <td className="p-4 text-white">${visit.paid_amount?.toFixed(2) || '0.00'}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        visit.payment_status === 'paid' ? 'bg-green-500 text-white' :
                        visit.payment_status === 'partial' ? 'bg-yellow-500 text-white' :
                        'bg-red-500 text-white'
                      }`}>
                        {visit.payment_status}
                      </span>
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

const PatientQueueView = ({ setActiveModule }) => {
  const [queueData, setQueueData] = useState({ locations: {}, summary: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatientQueue();
    const interval = setInterval(fetchPatientQueue, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchPatientQueue = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/patient-queue`);
      setQueueData(response.data);
    } catch (error) {
      console.error("Error fetching patient queue:", error);
    } finally {
      setLoading(false);
    }
  };

  const getLocationColor = (location) => {
    const colors = {
      lobby: 'bg-blue-500',
      room_1: 'bg-green-500',
      room_2: 'bg-green-600',
      room_3: 'bg-green-700',
      room_4: 'bg-green-800',
      iv_room: 'bg-purple-500',
      checkout: 'bg-orange-500'
    };
    return colors[location] || 'bg-gray-500';
  };

  const getLocationName = (location) => {
    const names = {
      lobby: 'Lobby',
      room_1: 'Room 1',
      room_2: 'Room 2',
      room_3: 'Room 3',
      room_4: 'Room 4',
      iv_room: 'IV Room',
      checkout: 'Checkout'
    };
    return names[location] || location;
  };

  if (loading) {
    return <div className="text-white text-center py-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Patient Queue</h1>
            <p className="text-blue-200">Real-time patient locations in clinic</p>
            <p className="text-blue-300 text-sm">Last updated: {new Date(queueData.timestamp).toLocaleTimeString()}</p>
          </div>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg border border-white/20"
          >
            ← Back to Dashboard
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-blue-200 text-sm">Total Patients</h3>
            <p className="text-3xl font-bold text-white">{queueData.summary.total_patients || 0}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-blue-200 text-sm">Average Wait</h3>
            <p className="text-3xl font-bold text-white">{queueData.summary.average_wait_time || 0} min</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-blue-200 text-sm">Locations In Use</h3>
            <p className="text-3xl font-bold text-white">{queueData.summary.locations_in_use || 0}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {Object.entries(queueData.locations || {}).map(([location, patients]) => (
            <div key={location} className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
              <div className={`p-4 ${getLocationColor(location)} rounded-t-xl`}>
                <h3 className="text-white font-bold text-lg">{getLocationName(location)}</h3>
                <p className="text-white/80">{patients.length} patient{patients.length !== 1 ? 's' : ''}</p>
              </div>
              <div className="p-4 space-y-3">
                {patients.length === 0 ? (
                  <p className="text-blue-200 text-center py-4">Empty</p>
                ) : (
                  patients.map((patient, index) => (
                    <div key={index} className="bg-white/5 rounded-lg p-3">
                      <div className="flex justify-between items-start mb-2">
                        <p className="text-white font-medium text-sm">{patient.patient_name}</p>
                        <span className="text-blue-200 text-xs">{patient.wait_time_minutes}m</span>
                      </div>
                      <p className="text-blue-200 text-xs capitalize">{patient.encounter_type}</p>
                      <p className="text-blue-300 text-xs">{patient.provider}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const PendingPaymentsView = ({ setActiveModule }) => {
  const [paymentsData, setPaymentsData] = useState({ pending_payments: [], summary: {} });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPendingPayments();
  }, []);

  const fetchPendingPayments = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/pending-payments`);
      setPaymentsData(response.data);
    } catch (error) {
      console.error("Error fetching pending payments:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-white text-center py-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Pending Payments</h1>
            <p className="text-blue-200">Outstanding invoices and payment tracking</p>
          </div>
          <button
            onClick={() => setActiveModule('dashboard')}
            className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg border border-white/20"
          >
            ← Back to Dashboard
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-yellow-200 text-sm">Total Outstanding</h3>
            <p className="text-3xl font-bold text-white">${paymentsData.summary.total_outstanding_amount?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-yellow-200 text-sm">Pending Invoices</h3>
            <p className="text-3xl font-bold text-white">{paymentsData.summary.total_pending_invoices || 0}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-red-200 text-sm">Overdue</h3>
            <p className="text-3xl font-bold text-white">{paymentsData.summary.overdue_invoices || 0}</p>
          </div>
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h3 className="text-red-200 text-sm">Avg Days Overdue</h3>
            <p className="text-3xl font-bold text-white">{paymentsData.summary.average_days_overdue?.toFixed(1) || '0.0'}</p>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 overflow-hidden">
          <div className="p-6 border-b border-white/20">
            <h2 className="text-xl font-bold text-white">Outstanding Invoices</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5">
                <tr>
                  <th className="text-left p-4 text-blue-200">Invoice #</th>
                  <th className="text-left p-4 text-blue-200">Patient</th>
                  <th className="text-left p-4 text-blue-200">Visit Type</th>
                  <th className="text-left p-4 text-blue-200">Total</th>
                  <th className="text-left p-4 text-blue-200">Outstanding</th>
                  <th className="text-left p-4 text-blue-200">Days Overdue</th>
                  <th className="text-left p-4 text-blue-200">Status</th>
                  <th className="text-left p-4 text-blue-200">Phone</th>
                </tr>
              </thead>
              <tbody>
                {paymentsData.pending_payments.map((payment, index) => (
                  <tr key={index} className="border-b border-white/10 hover:bg-white/5">
                    <td className="p-4 text-white font-mono text-sm">{payment.invoice_number}</td>
                    <td className="p-4 text-white font-medium">{payment.patient_name}</td>
                    <td className="p-4 text-blue-200">{payment.encounter_type}</td>
                    <td className="p-4 text-white">${payment.total_amount?.toFixed(2) || '0.00'}</td>
                    <td className="p-4 text-white font-medium">${payment.outstanding_amount?.toFixed(2) || '0.00'}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        payment.days_overdue > 30 ? 'bg-red-500 text-white' :
                        payment.days_overdue > 0 ? 'bg-orange-500 text-white' :
                        'bg-green-500 text-white'
                      }`}>
                        {payment.days_overdue} days
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        payment.status === 'paid' ? 'bg-green-500 text-white' :
                        payment.status === 'partial' ? 'bg-yellow-500 text-white' :
                        'bg-red-500 text-white'
                      }`}>
                        {payment.status}
                      </span>
                    </td>
                    <td className="p-4 text-blue-200 text-sm">{payment.patient_phone || 'N/A'}</td>
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

// Main App Component with Authentication
function App() {
  const [activeModule, setActiveModule] = useState('dashboard');

  const renderModule = () => {
    switch (activeModule) {
      case 'patients':
        return (
          <ProtectedRoute permission="patients:read">
            <AppHeader>
              <PatientsModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'forms':
        return (
          <ProtectedRoute permission="forms:read">
            <AppHeader>
              <SmartFormsModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'inventory':
        return (
          <ProtectedRoute permission="inventory:read">
            <AppHeader>
              <InventoryModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'invoices':
        return (
          <ProtectedRoute permission="invoices:read">
            <AppHeader>
              <InvoicesModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'employees':
        return (
          <ProtectedRoute permission="employees:read">
            <AppHeader>
              <EmployeeModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'finance':
        return (
          <ProtectedRoute permission="finance:read">
            <AppHeader>
              <FinanceModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'erx-patients':
        return (
          <ProtectedRoute>
            <AppHeader>
              <CommunicationsModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'daily-log':
        return (
          <ProtectedRoute>
            <DailyLogView setActiveModule={setActiveModule} />
          </ProtectedRoute>
        );
      case 'patient-queue':
        return (
          <ProtectedRoute>
            <PatientQueueView setActiveModule={setActiveModule} />
          </ProtectedRoute>
        );
      case 'pending-payments':
        return (
          <ProtectedRoute>
            <PendingPaymentsView setActiveModule={setActiveModule} />
          </ProtectedRoute>
        );
      case 'scheduling':
        return (
          <ProtectedRoute permission="scheduling:read">
            <SchedulingModule setActiveModule={setActiveModule} />
          </ProtectedRoute>
        );
      case 'communications':
        return (
          <ProtectedRoute permission="communications:read">
            <CommunicationsModule setActiveModule={setActiveModule} />
          </ProtectedRoute>
        );
      default:
        return (
          <ProtectedRoute>
            <AppHeader>
              <Dashboard setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
    }
  };

  return (
    <AuthProvider>
      <div className="App">
        {renderModule()}
      </div>
    </AuthProvider>
  );
}

export default App;