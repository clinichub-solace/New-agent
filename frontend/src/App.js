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

        {activeTab === 'payroll' && (
          <PayrollTab employee={employee} />
        )}
    </div>
  );
};
const Dashboard = () => {
  const [stats, setStats] = useState({});
  const [recentPatients, setRecentPatients] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  const modules = [
    { name: "Patients/EHR", key: "patients", icon: "👥", color: "bg-blue-500", permission: "patients:read" },
    { name: "Smart Forms", key: "forms", icon: "📋", color: "bg-green-500", permission: "forms:read" },
    { name: "Inventory", key: "inventory", icon: "📦", color: "bg-orange-500", permission: "inventory:read" },
    { name: "Invoices", key: "invoices", icon: "🧾", color: "bg-purple-500", permission: "invoices:read" },
    { name: "Lab Orders", key: "lab-orders", icon: "🧪", color: "bg-teal-600", permission: "lab:read" },
    { name: "Insurance", key: "insurance", icon: "🏥", color: "bg-cyan-600", permission: "insurance:read" },
    { name: "Employees", key: "employees", icon: "👨‍⚕️", color: "bg-indigo-500", permission: "employees:read" },
    { name: "Finance", key: "finance", icon: "💰", color: "bg-green-600", permission: "finance:read" },
    { name: "Scheduling", key: "scheduling", icon: "📅", color: "bg-blue-600", permission: "scheduling:read" },
    { name: "Communications", key: "communications", icon: "📨", color: "bg-teal-500", permission: "communications:read" },
    { name: "Referrals", key: "referrals", icon: "🔄", color: "bg-red-500", permission: "referrals:read" },
    { name: "Clinical Templates", key: "clinical-templates", icon: "📋", color: "bg-green-700", permission: "templates:read" },
    { name: "Quality Measures", key: "quality-measures", icon: "📊", color: "bg-blue-700", permission: "quality:read" },
    { name: "Patient Portal", key: "patient-portal-mgmt", icon: "🚪", color: "bg-purple-600", permission: "portal:read" },
    { name: "Documents", key: "documents", icon: "📄", color: "bg-gray-600", permission: "documents:read" },
    { name: "Telehealth", key: "telehealth", icon: "📹", color: "bg-pink-600", permission: "telehealth:read" }
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
                <button
                  onClick={() => window.open('/patient-portal', '_blank')}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  Patient Portal
                </button>
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
  const [formData, setFormData] = useState({
    first_name: '', 
    last_name: '', 
    email: '', 
    phone: '', 
    date_of_birth: '', 
    gender: '', 
    address_line1: '', 
    city: '', 
    state: '', 
    zip_code: ''
  });
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
      setShowPatientForm(false);
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
            onClick={() => setShowPatientForm(true)}
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
                    onClick={() => setShowPatientForm(false)}
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
                    onClick={() => setShowPatientForm(false)}
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

// ===== PAYROLL MANAGEMENT COMPONENT =====
const PayrollTab = ({ employee }) => {
  const [payrollPeriods, setPayrollPeriods] = useState([]);
  const [payrollRecords, setPayrollRecords] = useState([]);
  const [selectedPeriod, setSelectedPeriod] = useState(null);
  const [showCreatePeriod, setShowCreatePeriod] = useState(false);
  const [showPaystub, setShowPaystub] = useState(false);
  const [paystubData, setPaystubData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPayrollPeriods();
  }, []);

  useEffect(() => {
    if (selectedPeriod) {
      fetchPayrollRecords(selectedPeriod.id);
    }
  }, [selectedPeriod]);

  const fetchPayrollPeriods = async () => {
    try {
      const response = await axios.get(`${API}/payroll/periods`);
      setPayrollPeriods(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching payroll periods:', error);
      setLoading(false);
    }
  };

  const fetchPayrollRecords = async (periodId) => {
    try {
      const response = await axios.get(`${API}/payroll/records/${periodId}`);
      setPayrollRecords(response.data.filter(record => record.employee_id === employee.id));
    } catch (error) {
      console.error('Error fetching payroll records:', error);
    }
  };

  const calculatePayroll = async (periodId) => {
    try {
      setLoading(true);
      await axios.post(`${API}/payroll/calculate/${periodId}`);
      fetchPayrollPeriods();
      fetchPayrollRecords(periodId);
    } catch (error) {
      console.error('Error calculating payroll:', error);
      alert('Error calculating payroll');
    } finally {
      setLoading(false);
    }
  };

  const generatePaystub = async (recordId) => {
    try {
      const response = await axios.get(`${API}/payroll/paystub/${recordId}`);
      setPaystubData(response.data);
      setShowPaystub(true);
    } catch (error) {
      console.error('Error generating paystub:', error);
      alert('Error generating paystub');
    }
  };

  const approvePayroll = async (periodId) => {
    try {
      await axios.post(`${API}/payroll/approve/${periodId}`, { approved_by: 'admin' });
      fetchPayrollPeriods();
      alert('Payroll approved successfully');
    } catch (error) {
      console.error('Error approving payroll:', error);
      alert('Error approving payroll');
    }
  };

  const markPaid = async (periodId) => {
    try {
      await axios.post(`${API}/payroll/pay/${periodId}`);
      fetchPayrollPeriods();
      alert('Payroll marked as paid');
    } catch (error) {
      console.error('Error marking payroll as paid:', error);
      alert('Error marking payroll as paid');
    }
  };

  if (loading) {
    return <div className="text-center text-white py-8">Loading payroll data...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-white">Payroll Management</h3>
        <button
          onClick={() => setShowCreatePeriod(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
        >
          Create Pay Period
        </button>
      </div>

      {/* Payroll Periods */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Payroll Periods */}
        <div className="bg-white/5 rounded-lg p-4">
          <h4 className="text-white font-medium mb-4">Pay Periods</h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {payrollPeriods.map((period) => (
              <div
                key={period.id}
                onClick={() => setSelectedPeriod(period)}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedPeriod?.id === period.id
                    ? 'border-blue-400 bg-blue-500/20'
                    : 'border-white/20 bg-white/5 hover:bg-white/10'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-white font-medium">
                      {new Date(period.period_start).toLocaleDateString()} - {new Date(period.period_end).toLocaleDateString()}
                    </p>
                    <p className="text-blue-200 text-sm">Pay Date: {new Date(period.pay_date).toLocaleDateString()}</p>
                    <p className="text-blue-200 text-sm">Type: {period.period_type}</p>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded text-xs ${
                      period.status === 'draft' ? 'bg-gray-500/20 text-gray-300' :
                      period.status === 'calculated' ? 'bg-yellow-500/20 text-yellow-300' :
                      period.status === 'approved' ? 'bg-blue-500/20 text-blue-300' :
                      period.status === 'paid' ? 'bg-green-500/20 text-green-300' :
                      'bg-gray-500/20 text-gray-300'
                    }`}>
                      {period.status.toUpperCase()}
                    </span>
                    <p className="text-blue-200 text-xs mt-1">{period.employee_count} employees</p>
                  </div>
                </div>
                
                {/* Action Buttons */}
                <div className="flex space-x-2 mt-3">
                  {period.status === 'draft' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        calculatePayroll(period.id);
                      }}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs"
                    >
                      Calculate
                    </button>
                  )}
                  {period.status === 'calculated' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        approvePayroll(period.id);
                      }}
                      className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs"
                    >
                      Approve
                    </button>
                  )}
                  {period.status === 'approved' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        markPaid(period.id);
                      }}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-xs"
                    >
                      Mark Paid
                    </button>
                  )}
                </div>
              </div>
            ))}
            {payrollPeriods.length === 0 && (
              <div className="text-center text-blue-200 py-8">
                No payroll periods found
              </div>
            )}
          </div>
        </div>

        {/* Right: Employee Payroll Records */}
        <div className="bg-white/5 rounded-lg p-4">
          <h4 className="text-white font-medium mb-4">
            {employee.first_name} {employee.last_name} - Payroll Records
          </h4>
          {selectedPeriod ? (
            <div className="space-y-4">
              {payrollRecords.map((record) => (
                <div key={record.id} className="bg-white/10 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <p className="text-white font-medium">
                        {new Date(selectedPeriod.period_start).toLocaleDateString()} - {new Date(selectedPeriod.period_end).toLocaleDateString()}
                      </p>
                      <p className="text-blue-200 text-sm">Check #{record.check_number || 'Pending'}</p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      record.check_status === 'draft' ? 'bg-gray-500/20 text-gray-300' :
                      record.check_status === 'calculated' ? 'bg-yellow-500/20 text-yellow-300' :
                      record.check_status === 'approved' ? 'bg-blue-500/20 text-blue-300' :
                      record.check_status === 'paid' ? 'bg-green-500/20 text-green-300' :
                      'bg-gray-500/20 text-gray-300'
                    }`}>
                      {record.check_status?.toUpperCase() || 'DRAFT'}
                    </span>
                  </div>

                  {/* Hours Breakdown */}
                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div>
                      <p className="text-blue-200 text-sm">Regular Hours</p>
                      <p className="text-white">{record.regular_hours?.toFixed(1) || '0.0'}h</p>
                    </div>
                    <div>
                      <p className="text-blue-200 text-sm">Overtime Hours</p>
                      <p className="text-white">{record.overtime_hours?.toFixed(1) || '0.0'}h</p>
                    </div>
                  </div>

                  {/* Pay Breakdown */}
                  <div className="grid grid-cols-2 gap-4 mb-3">
                    <div>
                      <p className="text-blue-200 text-sm">Gross Pay</p>
                      <p className="text-white font-semibold">${record.gross_pay?.toFixed(2) || '0.00'}</p>
                    </div>
                    <div>
                      <p className="text-blue-200 text-sm">Net Pay</p>
                      <p className="text-green-300 font-semibold">${record.net_pay?.toFixed(2) || '0.00'}</p>
                    </div>
                  </div>

                  {/* Taxes */}
                  <div className="mb-3">
                    <p className="text-blue-200 text-sm">Total Taxes: ${record.total_taxes?.toFixed(2) || '0.00'}</p>
                    <div className="grid grid-cols-2 gap-2 text-xs text-blue-300">
                      <span>Federal: ${record.federal_tax?.toFixed(2) || '0.00'}</span>
                      <span>State: ${record.state_tax?.toFixed(2) || '0.00'}</span>
                      <span>SS: ${record.social_security_tax?.toFixed(2) || '0.00'}</span>
                      <span>Medicare: ${record.medicare_tax?.toFixed(2) || '0.00'}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex space-x-2">
                    <button
                      onClick={() => generatePaystub(record.id)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-xs"
                    >
                      View Paystub
                    </button>
                    {record.check_status === 'approved' && (
                      <button
                        onClick={() => {/* Print check functionality */}}
                        className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-xs"
                      >
                        Print Check
                      </button>
                    )}
                  </div>
                </div>
              ))}
              {payrollRecords.length === 0 && (
                <div className="text-center text-blue-200 py-8">
                  No payroll records found for this period
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-blue-200 py-8">
              Select a pay period to view records
            </div>
          )}
        </div>
      </div>

      {/* Create Pay Period Modal */}
      {showCreatePeriod && (
        <PayPeriodForm
          onClose={() => setShowCreatePeriod(false)}
          onSuccess={() => {
            setShowCreatePeriod(false);
            fetchPayrollPeriods();
          }}
        />
      )}

      {/* Paystub Modal */}
      {showPaystub && paystubData && (
        <PaystubModal
          paystubData={paystubData}
          onClose={() => {
            setShowPaystub(false);
            setPaystubData(null);
          }}
        />
      )}
    </div>
  );
};

// Pay Period Form Component
const PayPeriodForm = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    period_start: '',
    period_end: '',
    pay_date: '',
    period_type: 'biweekly',
    created_by: 'admin'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/payroll/periods`, formData);
      onSuccess();
    } catch (error) {
      console.error('Error creating pay period:', error);
      alert('Error creating pay period');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 w-full max-w-2xl border border-white/20">
        <h2 className="text-xl font-bold text-white mb-4">Create Pay Period</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-blue-200 text-sm mb-1">Period Start</label>
              <input
                type="date"
                value={formData.period_start}
                onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
                className="w-full bg-white/10 text-white rounded px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-blue-200 text-sm mb-1">Period End</label>
              <input
                type="date"
                value={formData.period_end}
                onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
                className="w-full bg-white/10 text-white rounded px-3 py-2"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-blue-200 text-sm mb-1">Pay Date</label>
              <input
                type="date"
                value={formData.pay_date}
                onChange={(e) => setFormData({ ...formData, pay_date: e.target.value })}
                className="w-full bg-white/10 text-white rounded px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-blue-200 text-sm mb-1">Period Type</label>
              <select
                value={formData.period_type}
                onChange={(e) => setFormData({ ...formData, period_type: e.target.value })}
                className="w-full bg-white/10 text-white rounded px-3 py-2"
              >
                <option value="weekly">Weekly</option>
                <option value="biweekly">Bi-weekly</option>
                <option value="semimonthly">Semi-monthly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-blue-200 hover:text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
            >
              Create Period
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Paystub Modal Component
const PaystubModal = ({ paystubData, onClose }) => {
  const printPaystub = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6 print:p-0">
          {/* Header */}
          <div className="flex justify-between items-center mb-6 print:hidden">
            <h2 className="text-xl font-bold">Employee Paystub</h2>
            <div className="space-x-2">
              <button
                onClick={printPaystub}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Print
              </button>
              <button
                onClick={onClose}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                Close
              </button>
            </div>
          </div>

          {/* Paystub Content */}
          <div className="bg-white text-black print:shadow-none">
            {/* Company Header */}
            <div className="text-center border-b-2 border-gray-300 pb-4 mb-6">
              <h1 className="text-2xl font-bold">ClinicHub Medical Practice</h1>
              <p className="text-gray-600">Employee Pay Statement</p>
            </div>

            {/* Employee and Pay Period Info */}
            <div className="grid grid-cols-2 gap-8 mb-6">
              <div>
                <h3 className="font-bold text-lg mb-2">Employee Information</h3>
                <p><strong>Name:</strong> {paystubData.employee_info.name}</p>
                <p><strong>Employee ID:</strong> {paystubData.employee_info.employee_id}</p>
                <p><strong>Address:</strong> {paystubData.employee_info.address}</p>
                <p><strong>SSN:</strong> ***-**-{paystubData.employee_info.ssn_last_four}</p>
              </div>
              <div>
                <h3 className="font-bold text-lg mb-2">Pay Period Information</h3>
                <p><strong>Pay Period:</strong> {new Date(paystubData.pay_period.start_date).toLocaleDateString()} - {new Date(paystubData.pay_period.end_date).toLocaleDateString()}</p>
                <p><strong>Pay Date:</strong> {new Date(paystubData.pay_period.pay_date).toLocaleDateString()}</p>
                <p><strong>Check Number:</strong> {paystubData.check_number || 'Electronic'}</p>
                <p><strong>Period Type:</strong> {paystubData.pay_period.period_type}</p>
              </div>
            </div>

            {/* Hours and Earnings */}
            <div className="mb-6">
              <h3 className="font-bold text-lg mb-4">Hours & Earnings</h3>
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border border-gray-300 px-4 py-2 text-left">Description</th>
                    <th className="border border-gray-300 px-4 py-2 text-right">Hours</th>
                    <th className="border border-gray-300 px-4 py-2 text-right">Rate</th>
                    <th className="border border-gray-300 px-4 py-2 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">Regular Hours</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">{paystubData.hours_breakdown.regular_hours.toFixed(1)}</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">$--</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.pay_breakdown.regular_pay.toFixed(2)}</td>
                  </tr>
                  {paystubData.hours_breakdown.overtime_hours > 0 && (
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">Overtime Hours</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">{paystubData.hours_breakdown.overtime_hours.toFixed(1)}</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">$--</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.pay_breakdown.overtime_pay.toFixed(2)}</td>
                    </tr>
                  )}
                  {paystubData.pay_breakdown.bonus_pay > 0 && (
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">Bonus</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">--</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">--</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.pay_breakdown.bonus_pay.toFixed(2)}</td>
                    </tr>
                  )}
                  <tr className="bg-gray-100 font-bold">
                    <td className="border border-gray-300 px-4 py-2">GROSS PAY</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">--</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">--</td>
                    <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.pay_breakdown.gross_pay.toFixed(2)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Deductions & Taxes */}
            <div className="grid grid-cols-2 gap-8 mb-6">
              <div>
                <h3 className="font-bold text-lg mb-4">Deductions</h3>
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 px-4 py-2 text-left">Description</th>
                      <th className="border border-gray-300 px-4 py-2 text-right">Current</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paystubData.deductions_breakdown.map((deduction, index) => (
                      <tr key={index}>
                        <td className="border border-gray-300 px-4 py-2">{deduction.description}</td>
                        <td className="border border-gray-300 px-4 py-2 text-right">${deduction.amount.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <h3 className="font-bold text-lg mb-4">Taxes</h3>
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 px-4 py-2 text-left">Tax</th>
                      <th className="border border-gray-300 px-4 py-2 text-right">Current</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">Federal Income Tax</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.taxes_breakdown.federal_tax.toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">State Income Tax</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.taxes_breakdown.state_tax.toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">Social Security</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.taxes_breakdown.social_security_tax.toFixed(2)}</td>
                    </tr>
                    <tr>
                      <td className="border border-gray-300 px-4 py-2">Medicare</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.taxes_breakdown.medicare_tax.toFixed(2)}</td>
                    </tr>
                    <tr className="bg-gray-100 font-bold">
                      <td className="border border-gray-300 px-4 py-2">TOTAL TAXES</td>
                      <td className="border border-gray-300 px-4 py-2 text-right">${paystubData.taxes_breakdown.total_taxes.toFixed(2)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Net Pay */}
            <div className="text-center border-t-2 border-gray-300 pt-4">
              <h2 className="text-2xl font-bold">NET PAY: ${paystubData.net_pay.toFixed(2)}</h2>
            </div>

            {/* YTD Totals */}
            <div className="mt-6">
              <h3 className="font-bold text-lg mb-4">Year-to-Date Totals</h3>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p><strong>YTD Gross:</strong> ${paystubData.ytd_totals.ytd_gross_pay.toFixed(2)}</p>
                  <p><strong>YTD Net:</strong> ${paystubData.ytd_totals.ytd_net_pay.toFixed(2)}</p>
                </div>
                <div>
                  <p><strong>YTD Federal Tax:</strong> ${paystubData.ytd_totals.ytd_federal_tax.toFixed(2)}</p>
                  <p><strong>YTD State Tax:</strong> ${paystubData.ytd_totals.ytd_state_tax.toFixed(2)}</p>
                </div>
                <div>
                  <p><strong>YTD Social Security:</strong> ${paystubData.ytd_totals.ytd_social_security_tax.toFixed(2)}</p>
                  <p><strong>YTD Medicare:</strong> ${paystubData.ytd_totals.ytd_medicare_tax.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Employee Management Module
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

  // Document Management Form
  const DocumentForm = () => {
    const [documentData, setDocumentData] = useState({
      document_type: 'performance_review',
      title: '',
      content: '',
      effective_date: new Date().toISOString().split('T')[0],
      expiry_date: '',
      due_date: '',
      priority: 'medium'
    });

    const documentTypes = [
      { value: 'performance_review', label: 'Performance Review' },
      { value: 'warning', label: 'Warning Notice' },
      { value: 'vacation_request', label: 'Vacation Request' },
      { value: 'sick_leave', label: 'Sick Leave' },
      { value: 'training_certificate', label: 'Training Certificate' },
      { value: 'policy_acknowledgment', label: 'Policy Acknowledgment' },
      { value: 'contract', label: 'Employment Contract' },
      { value: 'other', label: 'Other' }
    ];

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const submitData = {
          ...documentData,
          employee_id: selectedEmployee.id,
          created_by: 'admin' // Should be current user
        };
        await axios.post(`${API}/employee-documents`, submitData);
        setShowDocumentForm(false);
        setDocumentData({
          document_type: 'performance_review',
          title: '',
          content: '',
          effective_date: new Date().toISOString().split('T')[0],
          expiry_date: '',
          due_date: '',
          priority: 'medium'
        });
        alert('Document created successfully!');
      } catch (error) {
        console.error("Error creating document:", error);
        alert('Error creating document: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">Document Type *</label>
          <select
            value={documentData.document_type}
            onChange={(e) => setDocumentData({...documentData, document_type: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg"
            required
          >
            {documentTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Title *</label>
          <input
            type="text"
            value={documentData.title}
            onChange={(e) => setDocumentData({...documentData, title: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg"
            placeholder="Document title"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Content *</label>
          <textarea
            value={documentData.content}
            onChange={(e) => setDocumentData({...documentData, content: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg"
            rows="6"
            placeholder="Document content..."
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Effective Date</label>
            <input
              type="date"
              value={documentData.effective_date}
              onChange={(e) => setDocumentData({...documentData, effective_date: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Due Date</label>
            <input
              type="date"
              value={documentData.due_date}
              onChange={(e) => setDocumentData({...documentData, due_date: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium mb-2">Priority</label>
          <select
            value={documentData.priority}
            onChange={(e) => setDocumentData({...documentData, priority: e.target.value})}
            className="w-full p-3 border border-gray-300 rounded-lg"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
        <div className="flex justify-end space-x-4 pt-4">
          <button
            type="button"
            onClick={() => setShowDocumentForm(false)}
            className="px-6 py-2 border border-gray-300 rounded-lg"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Create Document
          </button>
        </div>
      </form>
    );
  };

  // Schedule & Shift Management Form
  const ScheduleForm = () => {
    const [activeScheduleTab, setActiveScheduleTab] = useState('shifts');
    const [shiftData, setShiftData] = useState({
      shift_date: new Date().toISOString().split('T')[0],
      start_time: '09:00',
      end_time: '17:00',
      break_duration: 60,
      department: '',
      notes: ''
    });
    const [workShifts, setWorkShifts] = useState([]);
    const [timeEntries, setTimeEntries] = useState([]);

    useEffect(() => {
      fetchWorkShifts();
      fetchTimeEntries();
    }, []);

    const fetchWorkShifts = async () => {
      try {
        const response = await axios.get(`${API}/work-shifts/employee/${selectedEmployee.id}`);
        setWorkShifts(response.data);
      } catch (error) {
        console.error("Error fetching work shifts:", error);
      }
    };

    const fetchTimeEntries = async () => {
      try {
        const response = await axios.get(`${API}/time-entries/employee/${selectedEmployee.id}`);
        setTimeEntries(response.data);
      } catch (error) {
        console.error("Error fetching time entries:", error);
      }
    };

    const handleShiftSubmit = async (e) => {
      e.preventDefault();
      try {
        const submitData = {
          ...shiftData,
          employee_id: selectedEmployee.id
        };
        await axios.post(`${API}/work-shifts`, submitData);
        setShiftData({
          shift_date: new Date().toISOString().split('T')[0],
          start_time: '09:00',
          end_time: '17:00',
          break_duration: 60,
          department: '',
          notes: ''
        });
        fetchWorkShifts();
        alert('Work shift scheduled successfully!');
      } catch (error) {
        console.error("Error creating work shift:", error);
        alert('Error creating work shift: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <div className="space-y-6">
        {/* Tab Navigation */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            {['shifts', 'schedule', 'time-tracking'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveScheduleTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeScheduleTab === tab
                    ? 'border-indigo-500 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.replace('-', ' ')}
              </button>
            ))}
          </nav>
        </div>

        {/* Shifts Tab */}
        {activeScheduleTab === 'shifts' && (
          <div className="space-y-6">
            <form onSubmit={handleShiftSubmit} className="space-y-4">
              <h3 className="text-lg font-semibold">Schedule New Shift</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Shift Date *</label>
                  <input
                    type="date"
                    value={shiftData.shift_date}
                    onChange={(e) => setShiftData({...shiftData, shift_date: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Department</label>
                  <select
                    value={shiftData.department}
                    onChange={(e) => setShiftData({...shiftData, department: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  >
                    <option value="">Select Department</option>
                    <option value="Emergency">Emergency</option>
                    <option value="ICU">ICU</option>
                    <option value="Surgery">Surgery</option>
                    <option value="Pediatrics">Pediatrics</option>
                    <option value="Cardiology">Cardiology</option>
                    <option value="Nursing">Nursing</option>
                    <option value="Administration">Administration</option>
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Start Time *</label>
                  <input
                    type="time"
                    value={shiftData.start_time}
                    onChange={(e) => setShiftData({...shiftData, start_time: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">End Time *</label>
                  <input
                    type="time"
                    value={shiftData.end_time}
                    onChange={(e) => setShiftData({...shiftData, end_time: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Break Duration (min)</label>
                  <input
                    type="number"
                    value={shiftData.break_duration}
                    onChange={(e) => setShiftData({...shiftData, break_duration: parseInt(e.target.value)})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    min="0"
                    max="240"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Notes</label>
                <textarea
                  value={shiftData.notes}
                  onChange={(e) => setShiftData({...shiftData, notes: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  rows="3"
                  placeholder="Shift notes or special instructions..."
                />
              </div>
              <button
                type="submit"
                className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700"
              >
                Schedule Shift
              </button>
            </form>

            {/* Scheduled Shifts */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Scheduled Shifts</h3>
              <div className="space-y-3">
                {workShifts.length > 0 ? (
                  workShifts.map((shift) => (
                    <div key={shift.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{new Date(shift.shift_date).toLocaleDateString()}</p>
                          <p className="text-sm text-gray-600">
                            {shift.start_time} - {shift.end_time}
                            {shift.department && ` • ${shift.department}`}
                          </p>
                          {shift.notes && (
                            <p className="text-sm text-gray-500 mt-1">{shift.notes}</p>
                          )}
                        </div>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          new Date(shift.shift_date) >= new Date() ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {new Date(shift.shift_date) >= new Date() ? 'Upcoming' : 'Completed'}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-500 text-center py-4">No shifts scheduled</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Time Tracking Tab */}
        {activeScheduleTab === 'time-tracking' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Recent Time Entries</h3>
            <div className="space-y-3">
              {timeEntries.length > 0 ? (
                timeEntries.slice(0, 10).map((entry) => (
                  <div key={entry.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium capitalize">{entry.entry_type.replace('_', ' ')}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(entry.timestamp).toLocaleString()}
                        </p>
                        {entry.notes && (
                          <p className="text-sm text-gray-500 mt-1">{entry.notes}</p>
                        )}
                      </div>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        entry.entry_type === 'clock_in' ? 'bg-green-100 text-green-800' :
                        entry.entry_type === 'clock_out' ? 'bg-red-100 text-red-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {entry.entry_type.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-4">No time entries found</p>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Time Entry Form
  const TimeEntryForm = () => {
    const [timeEntryData, setTimeEntryData] = useState({
      entry_type: 'clock_in',
      timestamp: new Date().toISOString().slice(0, 16),
      notes: ''
    });
    const [currentStatus, setCurrentStatus] = useState(null);

    useEffect(() => {
      fetchCurrentStatus();
    }, []);

    const fetchCurrentStatus = async () => {
      try {
        const response = await axios.get(`${API}/time-entries/employee/${selectedEmployee.id}/current-status`);
        setCurrentStatus(response.data);
      } catch (error) {
        console.error("Error fetching current status:", error);
      }
    };

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const submitData = {
          ...timeEntryData,
          employee_id: selectedEmployee.id,
          timestamp: new Date(timeEntryData.timestamp).toISOString()
        };
        await axios.post(`${API}/time-entries`, submitData);
        setTimeEntryData({
          entry_type: 'clock_in',
          timestamp: new Date().toISOString().slice(0, 16),
          notes: ''
        });
        fetchCurrentStatus();
        setShowTimeEntry(false);
        alert('Time entry recorded successfully!');
      } catch (error) {
        console.error("Error creating time entry:", error);
        alert('Error recording time entry: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    const getNextAction = () => {
      if (!currentStatus) return 'clock_in';
      
      if (currentStatus.status === 'clocked_out' || currentStatus.status === 'not_started') {
        return 'clock_in';
      } else if (currentStatus.status === 'clocked_in') {
        return 'break_start';
      } else if (currentStatus.status === 'on_break') {
        return 'break_end';
      }
      return 'clock_out';
    };

    const suggestedAction = getNextAction();

    return (
      <div className="space-y-6">
        {/* Current Status */}
        {currentStatus && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-medium mb-2">Current Status</h3>
            <p className="text-sm">
              <span className="font-medium">Status:</span> 
              <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                currentStatus.status === 'clocked_in' ? 'bg-green-100 text-green-800' :
                currentStatus.status === 'on_break' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {currentStatus.status?.replace('_', ' ').toUpperCase() || 'Unknown'}
              </span>
            </p>
            {currentStatus.last_entry && (
              <p className="text-sm text-gray-600 mt-1">
                Last action: {new Date(currentStatus.last_entry).toLocaleString()}
              </p>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Action *</label>
            <select
              value={timeEntryData.entry_type}
              onChange={(e) => setTimeEntryData({...timeEntryData, entry_type: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            >
              <option value="clock_in">Clock In</option>
              <option value="clock_out">Clock Out</option>
              <option value="break_start">Start Break</option>
              <option value="break_end">End Break</option>
            </select>
            {suggestedAction !== timeEntryData.entry_type && (
              <p className="text-sm text-blue-600 mt-1">
                Suggested next action: {suggestedAction.replace('_', ' ')}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Date & Time *</label>
            <input
              type="datetime-local"
              value={timeEntryData.timestamp}
              onChange={(e) => setTimeEntryData({...timeEntryData, timestamp: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Notes</label>
            <textarea
              value={timeEntryData.notes}
              onChange={(e) => setTimeEntryData({...timeEntryData, notes: e.target.value})}
              className="w-full p-3 border border-gray-300 rounded-lg"
              rows="3"
              placeholder="Optional notes about this time entry..."
            />
          </div>
          <div className="flex justify-end space-x-4">
            <button
              type="button"
              onClick={() => setShowTimeEntry(false)}
              className="px-6 py-2 border border-gray-300 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Record Entry
            </button>
          </div>
        </form>
      </div>
    );
  };

  // Enhanced Employee Detail View
  const EmployeeDetailView = ({ employee }) => {
    const [employeeDocuments, setEmployeeDocuments] = useState([]);
    const [employeeHours, setEmployeeHours] = useState(null);

    useEffect(() => {
      if (employee?.id) {
        fetchEmployeeDocuments();
        fetchEmployeeHours();
      }
    }, [employee]);

    const fetchEmployeeDocuments = async () => {
      try {
        const response = await axios.get(`${API}/employee-documents/employee/${employee.id}`);
        setEmployeeDocuments(response.data);
      } catch (error) {
        console.error("Error fetching employee documents:", error);
      }
    };

    const fetchEmployeeHours = async () => {
      try {
        const response = await axios.get(`${API}/employees/${employee.id}/hours-summary`);
        setEmployeeHours(response.data);
      } catch (error) {
        console.error("Error fetching employee hours:", error);
      }
    };

    const handleDocumentAction = async (documentId, action) => {
      try {
        await axios.put(`${API}/employee-documents/${documentId}/${action}`);
        fetchEmployeeDocuments();
        alert(`Document ${action}ed successfully!`);
      } catch (error) {
        console.error(`Error ${action}ing document:`, error);
        alert(`Error ${action}ing document: ` + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-indigo-500 rounded-full flex items-center justify-center">
              <span className="text-white text-2xl">
                {employee.first_name?.[0]}{employee.last_name?.[0]}
              </span>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white">
                {employee.first_name} {employee.last_name}
              </h2>
              <p className="text-blue-200">{employee.role?.replace('_', ' ').toUpperCase()} • {employee.department}</p>
              <p className="text-blue-200 text-sm">ID: {employee.employee_id}</p>
            </div>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowTimeEntry(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
            >
              ⏰ Time Entry
            </button>
            <button
              onClick={() => setShowDocumentForm(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
            >
              📄 New Document
            </button>
            <button
              onClick={() => setShowScheduleForm(true)}
              className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg"
            >
              📅 Schedule
            </button>
            <button
              onClick={() => setSelectedEmployee(null)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
            >
              ← Back to Employees
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-white/20 mb-6">
          <nav className="flex space-x-8">
            {['overview', 'documents', 'schedule', 'hours', 'payroll'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-1 border-b-2 font-medium text-sm capitalize ${
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

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Personal Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Personal Information</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-blue-200">Email</label>
                    <p className="text-white">{employee.email}</p>
                  </div>
                  <div>
                    <label className="block text-sm text-blue-200">Phone</label>
                    <p className="text-white">{employee.phone || 'Not provided'}</p>
                  </div>
                  <div>
                    <label className="block text-sm text-blue-200">Address</label>
                    <p className="text-white">
                      {employee.address ? `${employee.address}, ${employee.city}, ${employee.state} ${employee.zip_code}` : 'Not provided'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Employment Details */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-white">Employment Details</h3>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-blue-200">Hire Date</label>
                    <p className="text-white">{new Date(employee.hire_date).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <label className="block text-sm text-blue-200">Employment Type</label>
                    <p className="text-white">{employee.employment_type?.replace('_', ' ').toUpperCase()}</p>
                  </div>
                  <div>
                    <label className="block text-sm text-blue-200">Compensation</label>
                    <p className="text-white">
                      {employee.salary ? `$${employee.salary.toLocaleString()}/year` : 
                       employee.hourly_rate ? `$${employee.hourly_rate}/hour` : 'Not specified'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm text-blue-200">Status</label>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      employee.is_active ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                    }`}>
                      {employee.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Emergency Contact */}
            {employee.emergency_contact_name && (
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">Emergency Contact</h3>
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-white font-medium">{employee.emergency_contact_name}</p>
                  <p className="text-blue-200">{employee.emergency_contact_relationship}</p>
                  <p className="text-blue-200">{employee.emergency_contact_phone}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'documents' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-white">Employee Documents</h3>
              <button
                onClick={() => setShowDocumentForm(true)}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm"
              >
                + New Document
              </button>
            </div>
            <div className="space-y-3">
              {employeeDocuments.length > 0 ? (
                employeeDocuments.map((doc) => (
                  <div key={doc.id} className="bg-white/5 rounded-lg p-4">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h4 className="text-white font-medium">{doc.title}</h4>
                        <p className="text-blue-200 text-sm capitalize">
                          {doc.document_type.replace('_', ' ')} • Created: {new Date(doc.created_at).toLocaleDateString()}
                        </p>
                        {doc.effective_date && (
                          <p className="text-blue-200 text-sm">
                            Effective: {new Date(doc.effective_date).toLocaleDateString()}
                          </p>
                        )}
                        <p className="text-gray-300 text-sm mt-2">{doc.content}</p>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          doc.status === 'approved' ? 'bg-green-500 text-white' :
                          doc.status === 'signed' ? 'bg-blue-500 text-white' :
                          doc.status === 'pending_approval' ? 'bg-yellow-500 text-white' :
                          'bg-gray-500 text-white'
                        }`}>
                          {doc.status.replace('_', ' ').toUpperCase()}
                        </span>
                        {doc.status === 'draft' && (
                          <button
                            onClick={() => handleDocumentAction(doc.id, 'sign')}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs"
                          >
                            Sign
                          </button>
                        )}
                        {doc.status === 'signed' && (
                          <button
                            onClick={() => handleDocumentAction(doc.id, 'approve')}
                            className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs"
                          >
                            Approve
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-blue-200 text-center py-4">No documents found</p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'hours' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white">Hours Summary</h3>
            {employeeHours ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white/5 rounded-lg p-4">
                  <h4 className="text-blue-200 text-sm">This Week</h4>
                  <p className="text-2xl font-bold text-white">
                    {employeeHours.current_week_hours?.toFixed(1) || '0.0'}h
                  </p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <h4 className="text-blue-200 text-sm">This Month</h4>
                  <p className="text-2xl font-bold text-white">
                    {employeeHours.current_month_hours?.toFixed(1) || '0.0'}h
                  </p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <h4 className="text-blue-200 text-sm">Total Hours</h4>
                  <p className="text-2xl font-bold text-white">
                    {employeeHours.total_hours?.toFixed(1) || '0.0'}h
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-blue-200">Loading hours data...</p>
            )}
          </div>
        )}
      </div>
    );
  };

  if (selectedEmployee) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <EmployeeDetailView employee={selectedEmployee} />
        </div>
        {showEmployeeForm && <EmployeeForm />}
        {showDocumentForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Create Employee Document</h2>
                  <button
                    onClick={() => setShowDocumentForm(false)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <DocumentForm />
              </div>
            </div>
          </div>
        )}
        
        {showScheduleForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Manage Schedule & Shifts</h2>
                  <button
                    onClick={() => setShowScheduleForm(false)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <ScheduleForm />
              </div>
            </div>
          </div>
        )}

        {showTimeEntry && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-lg w-full">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Time Entry</h2>
                  <button
                    onClick={() => setShowTimeEntry(false)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <TimeEntryForm />
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

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
        {showDocumentForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Create Employee Document</h2>
                  <button
                    onClick={() => setShowDocumentForm(false)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <DocumentForm />
              </div>
            </div>
          </div>
        )}
        
        {showScheduleForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Manage Schedule & Shifts</h2>
                  <button
                    onClick={() => setShowScheduleForm(false)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <ScheduleForm />
              </div>
            </div>
          </div>
        )}

        {showTimeEntry && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-lg w-full">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Time Entry</h2>
                  <button
                    onClick={() => setShowTimeEntry(false)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <TimeEntryForm />
              </div>
            </div>
          </div>
        )}
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
                        <div className="w-10 h-10 bg-indigo-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-medium">
                            {employee.first_name?.[0]}{employee.last_name?.[0]}
                          </span>
                        </div>
                        <div>
                          <p className="text-white font-medium">
                            {employee.first_name} {employee.last_name}
                          </p>
                          <p className="text-blue-200 text-sm">{employee.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-1 text-xs rounded-full bg-blue-500 text-white">
                        {employee.role?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="p-4 text-blue-200">{employee.department}</td>
                    <td className="p-4 text-blue-200">
                      {new Date(employee.hire_date).toLocaleDateString()}
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-1 text-xs rounded-full bg-green-500 text-white">
                        {employee.employment_type?.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        employee.is_active ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                      }`}>
                        {employee.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleEmployeeSelect(employee)}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded text-sm"
                        >
                          View Details
                        </button>
                        <button
                          onClick={() => {
                            setSelectedEmployee(employee);
                            setShowTimeEntry(true);
                          }}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm"
                          title="Quick Time Entry"
                        >
                          ⏰
                        </button>
                        <button
                          onClick={() => {
                            setSelectedEmployee(employee);
                            setShowDocumentForm(true);
                          }}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                          title="New Document"
                        >
                          📄
                        </button>
                      </div>
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

// Lab Integration Module
const LabIntegrationModule = ({ setActiveModule }) => {
  const [activeTab, setActiveTab] = useState('orders');
  const [labOrders, setLabOrders] = useState([]);
  const [labResults, setLabResults] = useState([]);
  const [labTests, setLabTests] = useState([]);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);
  const [showOrderForm, setShowOrderForm] = useState(false);
  const [showResultForm, setShowResultForm] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [icd10Codes, setIcd10Codes] = useState([]);

  useEffect(() => {
    fetchLabTests();
    fetchLabOrders();
    fetchPatients();
    fetchProviders();
    fetchIcd10Codes();
  }, []);

  const fetchLabTests = async () => {
    try {
      const response = await axios.get(`${API}/lab-tests`);
      setLabTests(response.data);
    } catch (error) {
      console.error("Error fetching lab tests:", error);
    }
  };

  const fetchLabOrders = async () => {
    try {
      const response = await axios.get(`${API}/lab-orders`);
      setLabOrders(response.data);
    } catch (error) {
      console.error("Error fetching lab orders:", error);
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

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`);
      setProviders(response.data);
    } catch (error) {
      console.error("Error fetching providers:", error);
    }
  };

  const fetchIcd10Codes = async () => {
    try {
      const response = await axios.get(`${API}/icd10/search?query=common`);
      setIcd10Codes(response.data.slice(0, 50)); // Limit for UI
    } catch (error) {
      console.error("Error fetching ICD-10 codes:", error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status) => {
    const colors = {
      ordered: 'bg-blue-500',
      collected: 'bg-yellow-500',
      processing: 'bg-purple-500',
      completed: 'bg-green-500',
      cancelled: 'bg-red-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  const OrderForm = () => {
    const [orderData, setOrderData] = useState({
      patient_id: '',
      provider_id: '',
      lab_test_ids: [],
      icd10_codes: [],
      priority: 'routine',
      clinical_notes: '',
      fasting_required: false
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/lab-orders`, orderData);
        setShowOrderForm(false);
        setOrderData({
          patient_id: '',
          provider_id: '',
          lab_test_ids: [],
          icd10_codes: [],
          priority: 'routine',
          clinical_notes: '',
          fasting_required: false
        });
        fetchLabOrders();
        alert('Lab order created successfully!');
      } catch (error) {
        console.error("Error creating lab order:", error);
        alert('Error creating lab order: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Create Lab Order</h2>
              <button
                onClick={() => setShowOrderForm(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Patient *</label>
                <select
                  value={orderData.patient_id}
                  onChange={(e) => setOrderData({...orderData, patient_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Provider *</label>
                <select
                  value={orderData.provider_id}
                  onChange={(e) => setOrderData({...orderData, provider_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Select Provider</option>
                  {providers.map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.first_name} {provider.last_name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Lab Tests *</label>
                <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-2">
                  {labTests.map(test => (
                    <label key={test.id} className="flex items-center space-x-2 p-1">
                      <input
                        type="checkbox"
                        checked={orderData.lab_test_ids.includes(test.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setOrderData({
                              ...orderData,
                              lab_test_ids: [...orderData.lab_test_ids, test.id]
                            });
                          } else {
                            setOrderData({
                              ...orderData,
                              lab_test_ids: orderData.lab_test_ids.filter(id => id !== test.id)
                            });
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm">{test.name} ({test.loinc_code})</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">ICD-10 Diagnosis Codes</label>
                <div className="max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-2">
                  {icd10Codes.map(code => (
                    <label key={code.code} className="flex items-center space-x-2 p-1">
                      <input
                        type="checkbox"
                        checked={orderData.icd10_codes.includes(code.code)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setOrderData({
                              ...orderData,
                              icd10_codes: [...orderData.icd10_codes, code.code]
                            });
                          } else {
                            setOrderData({
                              ...orderData,
                              icd10_codes: orderData.icd10_codes.filter(c => c !== code.code)
                            });
                          }
                        }}
                        className="rounded"
                      />
                      <span className="text-sm">{code.code} - {code.description}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Priority</label>
                <select
                  value={orderData.priority}
                  onChange={(e) => setOrderData({...orderData, priority: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="routine">Routine</option>
                  <option value="urgent">Urgent</option>
                  <option value="stat">STAT</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Clinical Notes</label>
                <textarea
                  value={orderData.clinical_notes}
                  onChange={(e) => setOrderData({...orderData, clinical_notes: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  rows="3"
                  placeholder="Enter clinical notes..."
                />
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="fasting"
                  checked={orderData.fasting_required}
                  onChange={(e) => setOrderData({...orderData, fasting_required: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="fasting" className="text-sm">Fasting Required</label>
              </div>
              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowOrderForm(false)}
                  className="px-6 py-2 border border-gray-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700"
                >
                  Create Order
                </button>
              </div>
            </form>
          </div>
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
            <h1 className="text-3xl font-bold text-white">Lab Integration</h1>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowOrderForm(true)}
              className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg"
            >
              + New Lab Order
            </button>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="border-b border-white/20">
            <nav className="flex space-x-8 px-6">
              {['orders', 'tests', 'results'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-2 border-b-2 font-medium text-sm capitalize ${
                    activeTab === tab
                      ? 'border-teal-400 text-teal-400'
                      : 'border-transparent text-blue-200 hover:text-white'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'orders' && (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-white/5">
                    <tr>
                      <th className="text-left p-4 text-blue-200">Order ID</th>
                      <th className="text-left p-4 text-blue-200">Patient</th>
                      <th className="text-left p-4 text-blue-200">Provider</th>
                      <th className="text-left p-4 text-blue-200">Tests</th>
                      <th className="text-left p-4 text-blue-200">Status</th>
                      <th className="text-left p-4 text-blue-200">Priority</th>
                      <th className="text-left p-4 text-blue-200">Date</th>
                      <th className="text-left p-4 text-blue-200">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {labOrders.length > 0 ? (
                      labOrders.map((order) => (
                        <tr key={order.id} className="border-b border-white/10 hover:bg-white/5">
                          <td className="p-4 text-white font-mono text-sm">{order.order_number}</td>
                          <td className="p-4 text-white">{order.patient_name}</td>
                          <td className="p-4 text-blue-200">{order.provider_name}</td>
                          <td className="p-4 text-blue-200">{order.lab_tests?.length || 0} tests</td>
                          <td className="p-4">
                            <span className={`px-2 py-1 text-xs rounded-full text-white ${getStatusColor(order.status)}`}>
                              {order.status}
                            </span>
                          </td>
                          <td className="p-4">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              order.priority === 'stat' ? 'bg-red-500 text-white' :
                              order.priority === 'urgent' ? 'bg-orange-500 text-white' :
                              'bg-blue-500 text-white'
                            }`}>
                              {order.priority?.toUpperCase()}
                            </span>
                          </td>
                          <td className="p-4 text-blue-200">{formatDate(order.created_at)}</td>
                          <td className="p-4">
                            <button
                              onClick={() => setSelectedOrder(order)}
                              className="bg-teal-600 hover:bg-teal-700 text-white px-3 py-1 rounded text-sm"
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="8" className="p-8 text-center text-blue-200">
                          No lab orders found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'tests' && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {labTests.map((test) => (
                  <div key={test.id} className="bg-white/5 rounded-lg p-6">
                    <h3 className="text-white font-semibold mb-2">{test.name}</h3>
                    <p className="text-blue-200 text-sm mb-2">LOINC: {test.loinc_code}</p>
                    <p className="text-blue-200 text-sm mb-2">Category: {test.category}</p>
                    <p className="text-blue-200 text-sm">{test.description}</p>
                    {test.reference_range && (
                      <div className="mt-3 p-2 bg-white/5 rounded">
                        <p className="text-xs text-blue-200">Reference Range:</p>
                        <p className="text-xs text-white">{test.reference_range}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'results' && (
              <div className="text-center py-8">
                <p className="text-blue-200">Lab results functionality coming soon...</p>
                <p className="text-blue-200 text-sm mt-2">
                  This section will display completed lab results with values and interpretations.
                </p>
              </div>
            )}
          </div>
        </div>

        {showOrderForm && <OrderForm />}
        
        {/* Order Details Modal */}
        {selectedOrder && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Lab Order Details</h2>
                  <button
                    onClick={() => setSelectedOrder(null)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Order Number</p>
                      <p className="font-mono">{selectedOrder.order_number}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Status</p>
                      <span className={`px-2 py-1 text-xs rounded-full text-white ${getStatusColor(selectedOrder.status)}`}>
                        {selectedOrder.status}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Patient</p>
                      <p>{selectedOrder.patient_name}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Provider</p>
                      <p>{selectedOrder.provider_name}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Priority</p>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        selectedOrder.priority === 'stat' ? 'bg-red-500 text-white' :
                        selectedOrder.priority === 'urgent' ? 'bg-orange-500 text-white' :
                        'bg-blue-500 text-white'
                      }`}>
                        {selectedOrder.priority?.toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Fasting Required</p>
                      <p>{selectedOrder.fasting_required ? 'Yes' : 'No'}</p>
                    </div>
                  </div>
                  {selectedOrder.clinical_notes && (
                    <div>
                      <p className="text-sm font-medium text-gray-600">Clinical Notes</p>
                      <p className="bg-gray-50 p-3 rounded">{selectedOrder.clinical_notes}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-600">Ordered Tests</p>
                    <div className="bg-gray-50 p-3 rounded">
                      {selectedOrder.lab_tests?.map((test, index) => (
                        <div key={index} className="mb-2">
                          <p className="font-medium">{test.name}</p>
                          <p className="text-sm text-gray-600">LOINC: {test.loinc_code}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  {selectedOrder.icd10_codes?.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-gray-600">ICD-10 Diagnosis Codes</p>
                      <div className="bg-gray-50 p-3 rounded">
                        {selectedOrder.icd10_codes.map((code, index) => (
                          <span key={index} className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs mr-2 mb-1">
                            {code}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Insurance Verification Module
const InsuranceVerificationModule = ({ setActiveModule }) => {
  const [activeTab, setActiveTab] = useState('cards');
  const [insuranceCards, setInsuranceCards] = useState([]);
  const [eligibilityResponses, setEligibilityResponses] = useState([]);
  const [priorAuths, setPriorAuths] = useState([]);
  const [patients, setPatients] = useState([]);
  const [showCardForm, setShowCardForm] = useState(false);
  const [showEligibilityForm, setShowEligibilityForm] = useState(false);
  const [showPriorAuthForm, setShowPriorAuthForm] = useState(false);
  const [selectedCard, setSelectedCard] = useState(null);

  useEffect(() => {
    fetchPatients();
    fetchInsuranceCards();
    fetchEligibilityResponses();
    fetchPriorAuths();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await axios.get(`${API}/patients`);
      setPatients(response.data);
    } catch (error) {
      console.error("Error fetching patients:", error);
    }
  };

  const fetchInsuranceCards = async () => {
    try {
      const response = await axios.get(`${API}/insurance/cards`);
      setInsuranceCards(response.data);
    } catch (error) {
      console.error("Error fetching insurance cards:", error);
    }
  };

  const fetchEligibilityResponses = async () => {
    try {
      // This would need to be implemented to get all eligibility responses
      // For now, we'll just set an empty array
      setEligibilityResponses([]);
    } catch (error) {
      console.error("Error fetching eligibility responses:", error);
    }
  };

  const fetchPriorAuths = async () => {
    try {
      // This would fetch prior authorizations for all patients
      // For demo purposes, we'll just set an empty array
      setPriorAuths([]);
    } catch (error) {
      console.error("Error fetching prior auths:", error);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const InsuranceCardForm = () => {
    const [cardData, setCardData] = useState({
      patient_id: '',
      insurance_company: '',
      policy_number: '',
      group_number: '',
      member_id: '',
      plan_name: '',
      effective_date: '',
      expiration_date: '',
      copay_primary: '',
      copay_specialist: '',
      deductible: '',
      is_primary: true
    });

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        await axios.post(`${API}/insurance/cards`, cardData);
        setShowCardForm(false);
        setCardData({
          patient_id: '',
          insurance_company: '',
          policy_number: '',
          group_number: '',
          member_id: '',
          plan_name: '',
          effective_date: '',
          expiration_date: '',
          copay_primary: '',
          copay_specialist: '',
          deductible: '',
          is_primary: true
        });
        fetchInsuranceCards();
        alert('Insurance card added successfully!');
      } catch (error) {
        console.error("Error adding insurance card:", error);
        alert('Error adding insurance card: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Add Insurance Card</h2>
              <button
                onClick={() => setShowCardForm(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Patient *</label>
                <select
                  value={cardData.patient_id}
                  onChange={(e) => setCardData({...cardData, patient_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Insurance Company *</label>
                  <input
                    type="text"
                    value={cardData.insurance_company}
                    onChange={(e) => setCardData({...cardData, insurance_company: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Plan Name</label>
                  <input
                    type="text"
                    value={cardData.plan_name}
                    onChange={(e) => setCardData({...cardData, plan_name: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Policy Number *</label>
                  <input
                    type="text"
                    value={cardData.policy_number}
                    onChange={(e) => setCardData({...cardData, policy_number: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Member ID *</label>
                  <input
                    type="text"
                    value={cardData.member_id}
                    onChange={(e) => setCardData({...cardData, member_id: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Group Number</label>
                <input
                  type="text"
                  value={cardData.group_number}
                  onChange={(e) => setCardData({...cardData, group_number: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Effective Date</label>
                  <input
                    type="date"
                    value={cardData.effective_date}
                    onChange={(e) => setCardData({...cardData, effective_date: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Expiration Date</label>
                  <input
                    type="date"
                    value={cardData.expiration_date}
                    onChange={(e) => setCardData({...cardData, expiration_date: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Primary Copay ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={cardData.copay_primary}
                    onChange={(e) => setCardData({...cardData, copay_primary: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Specialist Copay ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={cardData.copay_specialist}
                    onChange={(e) => setCardData({...cardData, copay_specialist: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Deductible ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={cardData.deductible}
                    onChange={(e) => setCardData({...cardData, deductible: e.target.value})}
                    className="w-full p-3 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_primary"
                  checked={cardData.is_primary}
                  onChange={(e) => setCardData({...cardData, is_primary: e.target.checked})}
                  className="rounded"
                />
                <label htmlFor="is_primary" className="text-sm">Primary Insurance</label>
              </div>
              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCardForm(false)}
                  className="px-6 py-2 border border-gray-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
                >
                  Add Card
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  };

  const EligibilityForm = () => {
    const [eligibilityData, setEligibilityData] = useState({
      patient_id: '',
      insurance_card_id: '',
      service_type: 'medical',
      date_of_service: new Date().toISOString().split('T')[0]
    });

    const [availableCards, setAvailableCards] = useState([]);

    useEffect(() => {
      if (eligibilityData.patient_id) {
        // Filter cards for selected patient
        const patientCards = insuranceCards.filter(card => card.patient_id === eligibilityData.patient_id);
        setAvailableCards(patientCards);
      }
    }, [eligibilityData.patient_id, insuranceCards]);

    const handleSubmit = async (e) => {
      e.preventDefault();
      try {
        const response = await axios.post(`${API}/insurance/verify-eligibility`, eligibilityData);
        alert(`Eligibility verified! Status: ${response.data.coverage_status}`);
        setShowEligibilityForm(false);
        setEligibilityData({
          patient_id: '',
          insurance_card_id: '',
          service_type: 'medical',
          date_of_service: new Date().toISOString().split('T')[0]
        });
      } catch (error) {
        console.error("Error verifying eligibility:", error);
        alert('Error verifying eligibility: ' + (error.response?.data?.detail || 'Unknown error'));
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl max-w-lg w-full">
          <div className="p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold">Verify Eligibility</h2>
              <button
                onClick={() => setShowEligibilityForm(false)}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ✕
              </button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Patient *</label>
                <select
                  value={eligibilityData.patient_id}
                  onChange={(e) => setEligibilityData({...eligibilityData, patient_id: e.target.value, insurance_card_id: ''})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                >
                  <option value="">Select Patient</option>
                  {patients.map(patient => (
                    <option key={patient.id} value={patient.id}>
                      {patient.name?.[0]?.given} {patient.name?.[0]?.family}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Insurance Card *</label>
                <select
                  value={eligibilityData.insurance_card_id}
                  onChange={(e) => setEligibilityData({...eligibilityData, insurance_card_id: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                  disabled={!eligibilityData.patient_id}
                >
                  <option value="">Select Insurance Card</option>
                  {availableCards.map(card => (
                    <option key={card.id} value={card.id}>
                      {card.insurance_company} - {card.member_id} {card.is_primary ? '(Primary)' : ''}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Service Type</label>
                <select
                  value={eligibilityData.service_type}
                  onChange={(e) => setEligibilityData({...eligibilityData, service_type: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                >
                  <option value="medical">Medical</option>
                  <option value="surgical">Surgical</option>
                  <option value="diagnostic">Diagnostic</option>
                  <option value="pharmacy">Pharmacy</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Date of Service</label>
                <input
                  type="date"
                  value={eligibilityData.date_of_service}
                  onChange={(e) => setEligibilityData({...eligibilityData, date_of_service: e.target.value})}
                  className="w-full p-3 border border-gray-300 rounded-lg"
                  required
                />
              </div>
              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => setShowEligibilityForm(false)}
                  className="px-6 py-2 border border-gray-300 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-cyan-600 text-white rounded-lg hover:bg-cyan-700"
                >
                  Verify Eligibility
                </button>
              </div>
            </form>
          </div>
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
            <h1 className="text-3xl font-bold text-white">Insurance Verification</h1>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={() => setShowCardForm(true)}
              className="bg-cyan-600 hover:bg-cyan-700 text-white px-4 py-2 rounded-lg"
            >
              + Add Insurance Card
            </button>
            <button
              onClick={() => setShowEligibilityForm(true)}
              className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
            >
              Verify Eligibility
            </button>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="border-b border-white/20">
            <nav className="flex space-x-8 px-6">
              {['cards', 'eligibility', 'prior-auth'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-4 px-2 border-b-2 font-medium text-sm capitalize ${
                    activeTab === tab
                      ? 'border-cyan-400 text-cyan-400'
                      : 'border-transparent text-blue-200 hover:text-white'
                  }`}
                >
                  {tab.replace('-', ' ')}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'cards' && (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-white/5">
                    <tr>
                      <th className="text-left p-4 text-blue-200">Patient</th>
                      <th className="text-left p-4 text-blue-200">Insurance Company</th>
                      <th className="text-left p-4 text-blue-200">Plan</th>
                      <th className="text-left p-4 text-blue-200">Member ID</th>
                      <th className="text-left p-4 text-blue-200">Type</th>
                      <th className="text-left p-4 text-blue-200">Status</th>
                      <th className="text-left p-4 text-blue-200">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {insuranceCards.length > 0 ? (
                      insuranceCards.map((card) => (
                        <tr key={card.id} className="border-b border-white/10 hover:bg-white/5">
                          <td className="p-4 text-white">{card.patient_name}</td>
                          <td className="p-4 text-white">{card.insurance_company}</td>
                          <td className="p-4 text-blue-200">{card.plan_name || 'N/A'}</td>
                          <td className="p-4 text-blue-200 font-mono">{card.member_id}</td>
                          <td className="p-4">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              card.is_primary ? 'bg-blue-500 text-white' : 'bg-gray-500 text-white'
                            }`}>
                              {card.is_primary ? 'Primary' : 'Secondary'}
                            </span>
                          </td>
                          <td className="p-4">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              new Date(card.expiration_date) > new Date() ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
                            }`}>
                              {new Date(card.expiration_date) > new Date() ? 'Active' : 'Expired'}
                            </span>
                          </td>
                          <td className="p-4">
                            <button
                              onClick={() => setSelectedCard(card)}
                              className="bg-cyan-600 hover:bg-cyan-700 text-white px-3 py-1 rounded text-sm"
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="7" className="p-8 text-center text-blue-200">
                          No insurance cards found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'eligibility' && (
              <div className="text-center py-8">
                <p className="text-blue-200">Eligibility verification history will appear here...</p>
                <p className="text-blue-200 text-sm mt-2">
                  This section will show all previous eligibility verifications with results.
                </p>
              </div>
            )}

            {activeTab === 'prior-auth' && (
              <div className="text-center py-8">
                <p className="text-blue-200">Prior authorization requests will appear here...</p>
                <p className="text-blue-200 text-sm mt-2">
                  This section will show prior authorization status and management.
                </p>
              </div>
            )}
          </div>
        </div>

        {showCardForm && <InsuranceCardForm />}
        {showEligibilityForm && <EligibilityForm />}
        
        {/* Card Details Modal */}
        {selectedCard && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl max-w-2xl w-full">
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold">Insurance Card Details</h2>
                  <button
                    onClick={() => setSelectedCard(null)}
                    className="text-gray-500 hover:text-gray-700 text-xl"
                  >
                    ✕
                  </button>
                </div>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Patient</p>
                      <p>{selectedCard.patient_name}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Insurance Company</p>
                      <p>{selectedCard.insurance_company}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Plan Name</p>
                      <p>{selectedCard.plan_name || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Member ID</p>
                      <p className="font-mono">{selectedCard.member_id}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Policy Number</p>
                      <p className="font-mono">{selectedCard.policy_number}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Group Number</p>
                      <p className="font-mono">{selectedCard.group_number || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Effective Date</p>
                      <p>{formatDate(selectedCard.effective_date)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Expiration Date</p>
                      <p>{formatDate(selectedCard.expiration_date)}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Primary Care Copay</p>
                      <p>{selectedCard.copay_primary ? `$${selectedCard.copay_primary}` : 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Specialist Copay</p>
                      <p>{selectedCard.copay_specialist ? `$${selectedCard.copay_specialist}` : 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Deductible</p>
                      <p>{selectedCard.deductible ? `$${selectedCard.deductible}` : 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">Coverage Type</p>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        selectedCard.is_primary ? 'bg-blue-500 text-white' : 'bg-gray-500 text-white'
                      }`}>
                        {selectedCard.is_primary ? 'Primary' : 'Secondary'}
                      </span>
                    </div>
                  </div>
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

// ===== PHASE 3: GLOBAL SEARCH COMPONENT =====
const GlobalSearchComponent = ({ onSelectResult }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (searchQuery.trim().length > 2) {
        performSearch();
      } else {
        setSearchResults([]);
        setShowResults(false);
      }
    }, 300);

    return () => clearTimeout(delayedSearch);
  }, [searchQuery]);

  const performSearch = async () => {
    setIsSearching(true);
    try {
      const response = await axios.get(`${API}/search`, {
        params: { query: searchQuery, limit: 20 }
      });
      setSearchResults(response.data.results);
      setShowResults(true);
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleResultClick = (result) => {
    setShowResults(false);
    setSearchQuery('');
    onSelectResult(result);
  };

  const getResultIcon = (type) => {
    const icons = {
      patient: '👤',
      referral: '🔄',
      document: '📄',
      template: '📋',
      telehealth: '📹',
      appointment: '📅'
    };
    return icons[type] || '📋';
  };

  return (
    <div className="relative w-full max-w-md">
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search patients, referrals, documents..."
          className="w-full bg-white/10 text-white placeholder-blue-200 rounded-lg px-4 py-2 pr-10 border border-white/20 focus:border-blue-400 focus:outline-none"
        />
        <div className="absolute right-3 top-2.5">
          {isSearching ? (
            <div className="animate-spin w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></div>
          ) : (
            <span className="text-blue-300">🔍</span>
          )}
        </div>
      </div>

      {/* Search Results Dropdown */}
      {showResults && searchResults.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white/10 backdrop-blur-md rounded-lg border border-white/20 max-h-96 overflow-y-auto z-50">
          <div className="p-2">
            <div className="text-xs text-blue-200 px-2 py-1">
              {searchResults.length} results for "{searchQuery}"
            </div>
            {searchResults.map((result) => (
              <div
                key={`${result.type}-${result.id}`}
                onClick={() => handleResultClick(result)}
                className="flex items-center space-x-3 p-2 hover:bg-white/10 rounded cursor-pointer transition-colors"
              >
                <span className="text-lg">{getResultIcon(result.type)}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium truncate">{result.title}</p>
                  <p className="text-blue-200 text-sm truncate">{result.subtitle}</p>
                  <p className="text-blue-300 text-xs">in {result.module}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ===== PHASE 3: NOTIFICATION COMPONENT =====
const NotificationCenter = ({ userId }) => {
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (userId) {
      fetchNotifications();
      // Set up polling for new notifications
      const interval = setInterval(fetchNotifications, 30000); // Check every 30 seconds
      return () => clearInterval(interval);
    }
  }, [userId]);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`, {
        params: { user_id: userId, limit: 50 }
      });
      setNotifications(response.data);
      setUnreadCount(response.data.filter(n => !n.is_read).length);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`);
      fetchNotifications(); // Refresh notifications
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'text-gray-300',
      normal: 'text-blue-300',
      high: 'text-yellow-300',
      urgent: 'text-red-300'
    };
    return colors[priority] || 'text-blue-300';
  };

  const getTypeIcon = (type) => {
    const icons = {
      workflow: '🔄',
      reminder: '⏰',
      alert: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || 'ℹ️';
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative p-2 text-white hover:text-blue-300 transition-colors"
      >
        <span className="text-xl">🔔</span>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {showNotifications && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white/10 backdrop-blur-md rounded-lg border border-white/20 max-h-96 overflow-y-auto z-50">
          <div className="p-4 border-b border-white/20">
            <h3 className="text-white font-semibold">Notifications</h3>
            {unreadCount > 0 && (
              <p className="text-blue-200 text-sm">{unreadCount} unread</p>
            )}
          </div>
          
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-blue-200">No notifications</div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 border-b border-white/10 hover:bg-white/5 cursor-pointer ${
                    !notification.is_read ? 'bg-blue-500/10' : ''
                  }`}
                  onClick={() => !notification.is_read && markAsRead(notification.id)}
                >
                  <div className="flex items-start space-x-2">
                    <span className="text-lg">{getTypeIcon(notification.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`font-medium ${getPriorityColor(notification.priority)}`}>
                        {notification.title}
                      </p>
                      <p className="text-blue-200 text-sm">{notification.message}</p>
                      <p className="text-blue-300 text-xs">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!notification.is_read && (
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    )}
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

// ===== PHASE 3: WORKFLOW INTEGRATION COMPONENT =====
const WorkflowIntegrationPanel = ({ setActiveModule }) => {
  const [workflows, setWorkflows] = useState([]);
  const [showCreateWorkflow, setShowCreateWorkflow] = useState(false);
  const [referrals, setReferrals] = useState([]);
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    fetchWorkflows();
    fetchReferrals();
    fetchProviders();
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await axios.get(`${API}/workflows`);
      setWorkflows(response.data);
    } catch (error) {
      console.error('Error fetching workflows:', error);
    }
  };

  const fetchReferrals = async () => {
    try {
      const response = await axios.get(`${API}/referrals`);
      setReferrals(response.data.filter(r => r.status === 'pending'));
    } catch (error) {
      console.error('Error fetching referrals:', error);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`);
      setProviders(response.data);
    } catch (error) {
      console.error('Error fetching providers:', error);
    }
  };

  const createWorkflow = async (workflowData) => {
    try {
      await axios.post(`${API}/workflows/referral-to-appointment`, workflowData);
      fetchWorkflows();
      setShowCreateWorkflow(false);
    } catch (error) {
      console.error('Error creating workflow:', error);
      alert('Error creating workflow');
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Smart Workflows</h2>
        <button
          onClick={() => setShowCreateWorkflow(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
        >
          Create Workflow
        </button>
      </div>

      {/* Recent Workflows */}
      <div className="space-y-3">
        {workflows.slice(0, 5).map((workflow) => (
          <div key={workflow.id} className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">{workflow.type.replace('_', ' → ')}</p>
                <p className="text-blue-200 text-sm">
                  Status: {workflow.status} • {workflow.steps?.filter(s => s.status === 'completed').length || 0} steps completed
                </p>
              </div>
              <span className={`px-2 py-1 rounded text-xs ${
                workflow.status === 'active' ? 'bg-green-500/20 text-green-300' : 
                workflow.status === 'completed' ? 'bg-blue-500/20 text-blue-300' :
                'bg-gray-500/20 text-gray-300'
              }`}>
                {workflow.status}
              </span>
            </div>
          </div>
        ))}
        
        {workflows.length === 0 && (
          <div className="text-center text-blue-200 py-4">
            No workflows created yet
          </div>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showCreateWorkflow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 w-full max-w-2xl border border-white/20">
            <h3 className="text-xl font-bold text-white mb-4">Create Referral → Appointment Workflow</h3>
            <WorkflowForm
              referrals={referrals}
              providers={providers}
              onSubmit={createWorkflow}
              onCancel={() => setShowCreateWorkflow(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

// Workflow Form Component
const WorkflowForm = ({ referrals, providers, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    referral_id: '',
    appointment_data: {
      provider_id: '',
      date: '',
      time: '',
      duration: 30
    },
    enable_telehealth: false
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-blue-200 text-sm mb-1">Select Referral</label>
        <select
          value={formData.referral_id}
          onChange={(e) => setFormData({ ...formData, referral_id: e.target.value })}
          className="w-full bg-white/10 text-white rounded px-3 py-2"
          required
        >
          <option value="">Choose a pending referral</option>
          {referrals.map(referral => (
            <option key={referral.id} value={referral.id}>
              {referral.patient_name} → {referral.referred_to_specialty}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Provider</label>
          <select
            value={formData.appointment_data.provider_id}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, provider_id: e.target.value }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          >
            <option value="">Select Provider</option>
            {providers.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.first_name} {provider.last_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Duration (minutes)</label>
          <select
            value={formData.appointment_data.duration}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, duration: parseInt(e.target.value) }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          >
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={45}>45 minutes</option>
            <option value={60}>60 minutes</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Date</label>
          <input
            type="date"
            value={formData.appointment_data.date}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, date: e.target.value }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Time</label>
          <input
            type="time"
            value={formData.appointment_data.time}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, time: e.target.value }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          />
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="telehealth"
          checked={formData.enable_telehealth}
          onChange={(e) => setFormData({ ...formData, enable_telehealth: e.target.checked })}
          className="rounded"
        />
        <label htmlFor="telehealth" className="text-blue-200">
          Enable telehealth session for this appointment
        </label>
      </div>

      <div className="flex justify-end space-x-4 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-blue-200 hover:text-white"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
        >
          Create Workflow
        </button>
      </div>
    </form>
  );
};

// ===== ENHANCED HEADER WITH SEARCH AND NOTIFICATIONS =====
const EnhancedAppHeader = ({ children, user, onSearch }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900">
      {/* Enhanced Header */}
      <header className="bg-white/10 backdrop-blur-md border-b border-white/20 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-white">ClinicHub</h1>
            </div>
            
            {/* Center: Global Search */}
            <div className="flex-1 max-w-lg mx-8">
              <GlobalSearchComponent onSelectResult={onSearch} />
            </div>
            
            {/* Right: Notifications and User */}
            <div className="flex items-center space-x-4">
              <NotificationCenter userId={user?.id} />
              <div className="text-white">
                Welcome, {user?.username || 'User'}
              </div>
            </div>
          </div>
        </div>
      </header>
      
      {/* Content */}
      <div className="p-6">
        {children}
      </div>
    </div>
  );
};

// ===== PHASE 3: NOTIFICATION COMPONENT =====
const NotificationCenter = ({ userId }) => {
  const [notifications, setNotifications] = useState([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (userId) {
      fetchNotifications();
      // Set up polling for new notifications
      const interval = setInterval(fetchNotifications, 30000); // Check every 30 seconds
      return () => clearInterval(interval);
    }
  }, [userId]);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/notifications`, {
        params: { user_id: userId, limit: 50 }
      });
      setNotifications(response.data);
      setUnreadCount(response.data.filter(n => !n.is_read).length);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.put(`${API}/notifications/${notificationId}/read`);
      fetchNotifications(); // Refresh notifications
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: 'text-gray-300',
      normal: 'text-blue-300',
      high: 'text-yellow-300',
      urgent: 'text-red-300'
    };
    return colors[priority] || 'text-blue-300';
  };

  const getTypeIcon = (type) => {
    const icons = {
      workflow: '🔄',
      reminder: '⏰',
      alert: '⚠️',
      info: 'ℹ️'
    };
    return icons[type] || 'ℹ️';
  };

  return (
    <div className="relative">
      <button
        onClick={() => setShowNotifications(!showNotifications)}
        className="relative p-2 text-white hover:text-blue-300 transition-colors"
      >
        <span className="text-xl">🔔</span>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {showNotifications && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-white/10 backdrop-blur-md rounded-lg border border-white/20 max-h-96 overflow-y-auto z-50">
          <div className="p-4 border-b border-white/20">
            <h3 className="text-white font-semibold">Notifications</h3>
            {unreadCount > 0 && (
              <p className="text-blue-200 text-sm">{unreadCount} unread</p>
            )}
          </div>
          
          <div className="max-h-80 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-blue-200">No notifications</div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-3 border-b border-white/10 hover:bg-white/5 cursor-pointer ${
                    !notification.is_read ? 'bg-blue-500/10' : ''
                  }`}
                  onClick={() => !notification.is_read && markAsRead(notification.id)}
                >
                  <div className="flex items-start space-x-2">
                    <span className="text-lg">{getTypeIcon(notification.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`font-medium ${getPriorityColor(notification.priority)}`}>
                        {notification.title}
                      </p>
                      <p className="text-blue-200 text-sm">{notification.message}</p>
                      <p className="text-blue-300 text-xs">
                        {new Date(notification.created_at).toLocaleString()}
                      </p>
                    </div>
                    {!notification.is_read && (
                      <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    )}
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

// ===== PHASE 3: WORKFLOW INTEGRATION COMPONENT =====
const WorkflowIntegrationPanel = ({ setActiveModule }) => {
  const [workflows, setWorkflows] = useState([]);
  const [showCreateWorkflow, setShowCreateWorkflow] = useState(false);
  const [referrals, setReferrals] = useState([]);
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    fetchWorkflows();
    fetchReferrals();
    fetchProviders();
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await axios.get(`${API}/workflows`);
      setWorkflows(response.data);
    } catch (error) {
      console.error('Error fetching workflows:', error);
    }
  };

  const fetchReferrals = async () => {
    try {
      const response = await axios.get(`${API}/referrals`);
      setReferrals(response.data.filter(r => r.status === 'pending'));
    } catch (error) {
      console.error('Error fetching referrals:', error);
    }
  };

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API}/providers`);
      setProviders(response.data);
    } catch (error) {
      console.error('Error fetching providers:', error);
    }
  };

  const createWorkflow = async (workflowData) => {
    try {
      await axios.post(`${API}/workflows/referral-to-appointment`, workflowData);
      fetchWorkflows();
      setShowCreateWorkflow(false);
    } catch (error) {
      console.error('Error creating workflow:', error);
      alert('Error creating workflow');
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Smart Workflows</h2>
        <button
          onClick={() => setShowCreateWorkflow(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm"
        >
          Create Workflow
        </button>
      </div>

      {/* Recent Workflows */}
      <div className="space-y-3">
        {workflows.slice(0, 5).map((workflow) => (
          <div key={workflow.id} className="bg-white/5 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white font-medium">{workflow.type.replace('_', ' → ')}</p>
                <p className="text-blue-200 text-sm">
                  Status: {workflow.status} • {workflow.steps?.filter(s => s.status === 'completed').length || 0} steps completed
                </p>
              </div>
              <span className={`px-2 py-1 rounded text-xs ${
                workflow.status === 'active' ? 'bg-green-500/20 text-green-300' : 
                workflow.status === 'completed' ? 'bg-blue-500/20 text-blue-300' :
                'bg-gray-500/20 text-gray-300'
              }`}>
                {workflow.status}
              </span>
            </div>
          </div>
        ))}
        
        {workflows.length === 0 && (
          <div className="text-center text-blue-200 py-4">
            No workflows created yet
          </div>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showCreateWorkflow && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 w-full max-w-2xl border border-white/20">
            <h3 className="text-xl font-bold text-white mb-4">Create Referral → Appointment Workflow</h3>
            <WorkflowForm
              referrals={referrals}
              providers={providers}
              onSubmit={createWorkflow}
              onCancel={() => setShowCreateWorkflow(false)}
            />
          </div>
        </div>
      )}
    </div>
  );
};

// Workflow Form Component
const WorkflowForm = ({ referrals, providers, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    referral_id: '',
    appointment_data: {
      provider_id: '',
      date: '',
      time: '',
      duration: 30
    },
    enable_telehealth: false
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-blue-200 text-sm mb-1">Select Referral</label>
        <select
          value={formData.referral_id}
          onChange={(e) => setFormData({ ...formData, referral_id: e.target.value })}
          className="w-full bg-white/10 text-white rounded px-3 py-2"
          required
        >
          <option value="">Choose a pending referral</option>
          {referrals.map(referral => (
            <option key={referral.id} value={referral.id}>
              {referral.patient_name} → {referral.referred_to_specialty}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Provider</label>
          <select
            value={formData.appointment_data.provider_id}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, provider_id: e.target.value }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          >
            <option value="">Select Provider</option>
            {providers.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.first_name} {provider.last_name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Duration (minutes)</label>
          <select
            value={formData.appointment_data.duration}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, duration: parseInt(e.target.value) }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          >
            <option value={15}>15 minutes</option>
            <option value={30}>30 minutes</option>
            <option value={45}>45 minutes</option>
            <option value={60}>60 minutes</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Date</label>
          <input
            type="date"
            value={formData.appointment_data.date}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, date: e.target.value }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Time</label>
          <input
            type="time"
            value={formData.appointment_data.time}
            onChange={(e) => setFormData({
              ...formData,
              appointment_data: { ...formData.appointment_data, time: e.target.value }
            })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          />
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="telehealth"
          checked={formData.enable_telehealth}
          onChange={(e) => setFormData({ ...formData, enable_telehealth: e.target.checked })}
          className="rounded"
        />
        <label htmlFor="telehealth" className="text-blue-200">
          Enable telehealth session for this appointment
        </label>
      </div>

      <div className="flex justify-end space-x-4 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-blue-200 hover:text-white"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
        >
          Create Workflow
        </button>
      </div>
    </form>
  );
};

// ===== NEW MODULES COMPONENTS =====

// 1. Referrals Management Module
const ReferralsModule = ({ setActiveModule }) => {
  const [referrals, setReferrals] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedReferral, setSelectedReferral] = useState(null);
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);

  useEffect(() => {
    fetchReferrals();
    fetchPatientsAndProviders();
  }, []);

  const fetchReferrals = async () => {
    try {
      const response = await axios.get(`${API}/referrals`);
      setReferrals(response.data);
    } catch (error) {
      console.error('Error fetching referrals:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPatientsAndProviders = async () => {
    try {
      const [patientsRes, providersRes] = await Promise.all([
        axios.get(`${API}/patients`),
        axios.get(`${API}/providers`)
      ]);
      setPatients(patientsRes.data);
      setProviders(providersRes.data);
    } catch (error) {
      console.error('Error fetching patients/providers:', error);
    }
  };

  const handleCreateReferral = async (formData) => {
    try {
      await axios.post(`${API}/referrals`, formData);
      fetchReferrals();
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error creating referral:', error);
      alert('Error creating referral');
    }
  };

  const updateReferralStatus = async (referralId, status) => {
    try {
      await axios.put(`${API}/referrals/${referralId}`, { status });
      fetchReferrals();
    } catch (error) {
      console.error('Error updating referral status:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-3 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Enhanced Mobile-Responsive Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 sm:mb-8 space-y-4 sm:space-y-0">
          <div className="w-full sm:w-auto">
            <button
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-400 hover:text-blue-300 mb-2 flex items-center text-sm sm:text-base"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">Referrals Management</h1>
            <p className="text-blue-200 text-sm sm:text-base">Manage patient referrals to specialists</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white px-4 sm:px-6 py-2 rounded-lg text-sm sm:text-base"
          >
            New Referral
          </button>
        </div>

        {/* Create Referral Modal - Enhanced for Mobile */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-4 sm:p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-white/20">
              <h2 className="text-lg sm:text-xl font-bold text-white mb-4">Create New Referral</h2>
              <ReferralForm
                patients={patients}
                providers={providers}
                onSubmit={handleCreateReferral}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          </div>
        )}

        {/* Enhanced Mobile-Responsive Referrals List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="p-4 sm:p-6">
            <h2 className="text-lg sm:text-xl font-bold text-white mb-4">Active Referrals</h2>
            {loading ? (
              <div className="text-center text-white py-8">Loading referrals...</div>
            ) : referrals.length === 0 ? (
              <div className="text-center text-blue-200 py-8">No referrals found</div>
            ) : (
              <div className="space-y-4">
                {referrals.map((referral) => (
                  <div key={referral.id} className="bg-white/5 rounded-lg p-3 sm:p-4 border border-white/10">
                    {/* Mobile: Stack layout, Desktop: Flex layout */}
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
                      <div className="flex-1 space-y-1 sm:space-y-0">
                        <h3 className="text-white font-semibold text-sm sm:text-base">{referral.patient_name}</h3>
                        <p className="text-blue-200 text-xs sm:text-sm">To: {referral.referred_to_provider_name}</p>
                        <p className="text-blue-300 text-xs">Specialty: {referral.referred_to_specialty}</p>
                        <p className="text-blue-300 text-xs">Reason: {referral.reason_for_referral}</p>
                      </div>
                      <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-start space-x-3 sm:space-x-0 sm:space-y-2">
                        <span className={`px-2 sm:px-3 py-1 rounded-full text-xs ${
                          referral.status === 'pending' ? 'bg-yellow-500/20 text-yellow-300' :
                          referral.status === 'scheduled' ? 'bg-blue-500/20 text-blue-300' :
                          referral.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                          'bg-gray-500/20 text-gray-300'
                        }`}>
                          {referral.status.charAt(0).toUpperCase() + referral.status.slice(1)}
                        </span>
                        <select
                          value={referral.status}
                          onChange={(e) => updateReferralStatus(referral.id, e.target.value)}
                          className="bg-white/10 text-white rounded px-2 py-1 text-xs sm:text-sm"
                        >
                          <option value="pending">Pending</option>
                          <option value="scheduled">Scheduled</option>
                          <option value="completed">Completed</option>
                          <option value="cancelled">Cancelled</option>
                        </select>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Referral Form Component
const ReferralForm = ({ patients, providers, onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    patient_id: '',
    referring_provider_id: '',
    referred_to_provider_name: '',
    referred_to_specialty: '',
    reason_for_referral: '',
    urgency: 'routine',
    notes: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Patient</label>
          <select
            value={formData.patient_id}
            onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          >
            <option value="">Select Patient</option>
            {patients.map(patient => (
              <option key={patient.id} value={patient.id}>
                {patient.name?.[0]?.given} {patient.name?.[0]?.family}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Referring Provider</label>
          <select
            value={formData.referring_provider_id}
            onChange={(e) => setFormData({ ...formData, referring_provider_id: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          >
            <option value="">Select Provider</option>
            {providers.map(provider => (
              <option key={provider.id} value={provider.id}>
                {provider.first_name} {provider.last_name}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Specialist Name</label>
          <input
            type="text"
            value={formData.referred_to_provider_name}
            onChange={(e) => setFormData({ ...formData, referred_to_provider_name: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Specialty</label>
          <input
            type="text"
            value={formData.referred_to_specialty}
            onChange={(e) => setFormData({ ...formData, referred_to_specialty: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-blue-200 text-sm mb-1">Reason for Referral</label>
        <textarea
          value={formData.reason_for_referral}
          onChange={(e) => setFormData({ ...formData, reason_for_referral: e.target.value })}
          className="w-full bg-white/10 text-white rounded px-3 py-2 h-20"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Urgency</label>
          <select
            value={formData.urgency}
            onChange={(e) => setFormData({ ...formData, urgency: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          >
            <option value="routine">Routine</option>
            <option value="urgent">Urgent</option>
            <option value="stat">STAT</option>
          </select>
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Notes</label>
          <input
            type="text"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          />
        </div>
      </div>

      <div className="flex justify-end space-x-4 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-blue-200 hover:text-white"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
        >
          Create Referral
        </button>
      </div>
    </form>
  );
};

// 2. Clinical Templates Module
const ClinicalTemplatesModule = ({ setActiveModule }) => {
  const [templates, setTemplates] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
    initializeTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/clinical-templates`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeTemplates = async () => {
    try {
      await axios.post(`${API}/clinical-templates/init`);
    } catch (error) {
      console.error('Error initializing templates:', error);
    }
  };

  const handleCreateTemplate = async (formData) => {
    try {
      await axios.post(`${API}/clinical-templates`, formData);
      fetchTemplates();
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error creating template:', error);
      alert('Error creating template');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-400 hover:text-blue-300 mb-2 flex items-center"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Clinical Templates</h1>
            <p className="text-blue-200">Manage clinical protocols and care plans</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            New Template
          </button>
        </div>

        {/* Create Template Modal */}
        {showCreateForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 w-full max-w-2xl border border-white/20">
              <h2 className="text-xl font-bold text-white mb-4">Create Clinical Template</h2>
              <ClinicalTemplateForm
                onSubmit={handleCreateTemplate}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          </div>
        )}

        {/* Templates List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Available Templates</h2>
            {loading ? (
              <div className="text-center text-white py-8">Loading templates...</div>
            ) : templates.length === 0 ? (
              <div className="text-center text-blue-200 py-8">No templates found</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => (
                  <div key={template.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <h3 className="text-white font-semibold mb-2">{template.name}</h3>
                    <p className="text-blue-200 text-sm mb-2">Type: {template.template_type}</p>
                    {template.specialty && (
                      <p className="text-blue-300 text-sm mb-2">Specialty: {template.specialty}</p>
                    )}
                    {template.condition && (
                      <p className="text-blue-300 text-sm mb-2">Condition: {template.condition}</p>
                    )}
                    <span className={`px-3 py-1 rounded-full text-xs ${
                      template.is_active ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-300'
                    }`}>
                      {template.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Clinical Template Form Component
const ClinicalTemplateForm = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    template_type: 'protocol',
    specialty: '',
    condition: '',
    age_group: 'adult',
    sections: [],
    protocols: [],
    guidelines: '',
    evidence_level: 'A',
    created_by: 'admin'
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Template Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
            required
          />
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Template Type</label>
          <select
            value={formData.template_type}
            onChange={(e) => setFormData({ ...formData, template_type: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          >
            <option value="visit_template">Visit Template</option>
            <option value="assessment_template">Assessment Template</option>
            <option value="procedure_template">Procedure Template</option>
            <option value="protocol">Protocol</option>
            <option value="care_plan">Care Plan</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Specialty</label>
          <input
            type="text"
            value={formData.specialty}
            onChange={(e) => setFormData({ ...formData, specialty: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Condition</label>
          <input
            type="text"
            value={formData.condition}
            onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-blue-200 text-sm mb-1">Age Group</label>
          <select
            value={formData.age_group}
            onChange={(e) => setFormData({ ...formData, age_group: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          >
            <option value="pediatric">Pediatric</option>
            <option value="adult">Adult</option>
            <option value="geriatric">Geriatric</option>
          </select>
        </div>
        <div>
          <label className="block text-blue-200 text-sm mb-1">Evidence Level</label>
          <select
            value={formData.evidence_level}
            onChange={(e) => setFormData({ ...formData, evidence_level: e.target.value })}
            className="w-full bg-white/10 text-white rounded px-3 py-2"
          >
            <option value="A">A - High Quality Evidence</option>
            <option value="B">B - Moderate Quality Evidence</option>
            <option value="C">C - Low Quality Evidence</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-blue-200 text-sm mb-1">Guidelines</label>
        <textarea
          value={formData.guidelines}
          onChange={(e) => setFormData({ ...formData, guidelines: e.target.value })}
          className="w-full bg-white/10 text-white rounded px-3 py-2 h-20"
        />
      </div>

      <div className="flex justify-end space-x-4 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-blue-200 hover:text-white"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
        >
          Create Template
        </button>
      </div>
    </form>
  );
};

// 3. Quality Measures Module
const QualityMeasuresModule = ({ setActiveModule }) => {
  const [measures, setMeasures] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [reportData, setReportData] = useState(null);

  useEffect(() => {
    fetchMeasures();
  }, []);

  const fetchMeasures = async () => {
    try {
      const response = await axios.get(`${API}/quality-measures`);
      setMeasures(response.data);
    } catch (error) {
      console.error('Error fetching measures:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    try {
      const response = await axios.get(`${API}/quality-measures/report`);
      setReportData(response.data);
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-400 hover:text-blue-300 mb-2 flex items-center"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Quality Measures & Reporting</h1>
            <p className="text-blue-200">Track HEDIS, CQMs, and MIPS quality measures</p>
          </div>
          <div className="space-x-4">
            <button
              onClick={generateReport}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg"
            >
              Generate Report
            </button>
          </div>
        </div>

        {/* Report Section */}
        {reportData && (
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 mb-8">
            <div className="p-6">
              <h2 className="text-xl font-bold text-white mb-4">Quality Measures Report</h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-blue-200 text-sm">Total Measures</p>
                  <p className="text-2xl font-bold text-white">{reportData.summary?.total_measures || 0}</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-green-200 text-sm">Passed</p>
                  <p className="text-2xl font-bold text-green-300">{reportData.summary?.passed_measures || 0}</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-red-200 text-sm">Failed</p>
                  <p className="text-2xl font-bold text-red-300">{reportData.summary?.failed_measures || 0}</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4">
                  <p className="text-blue-200 text-sm">Overall Score</p>
                  <p className="text-2xl font-bold text-white">{reportData.summary?.overall_score || 0}%</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Measures List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Quality Measures</h2>
            {loading ? (
              <div className="text-center text-white py-8">Loading measures...</div>
            ) : measures.length === 0 ? (
              <div className="text-center text-blue-200 py-8">No measures found</div>
            ) : (
              <div className="space-y-4">
                {measures.map((measure) => (
                  <div key={measure.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="text-white font-semibold">{measure.name}</h3>
                        <p className="text-blue-200">{measure.description}</p>
                        <p className="text-blue-300 text-sm">Type: {measure.measure_type}</p>
                        {measure.measure_id && (
                          <p className="text-blue-300 text-sm">ID: {measure.measure_id}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          measure.is_active ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-300'
                        }`}>
                          {measure.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// 4. Patient Portal Management Module
const PatientPortalMgmtModule = ({ setActiveModule }) => {
  const [portalAccess, setPortalAccess] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPortalAccess();
  }, []);

  const fetchPortalAccess = async () => {
    try {
      const response = await axios.get(`${API}/patient-portal`);
      setPortalAccess(response.data);
    } catch (error) {
      console.error('Error fetching portal access:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePortalAccess = async (formData) => {
    try {
      await axios.post(`${API}/patient-portal`, formData);
      fetchPortalAccess();
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error creating portal access:', error);
      alert('Error creating portal access');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-400 hover:text-blue-300 mb-2 flex items-center"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Patient Portal Management</h1>
            <p className="text-blue-200">Manage patient portal access and features</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Grant Portal Access
          </button>
        </div>

        {/* Portal Access List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Portal Access Records</h2>
            {loading ? (
              <div className="text-center text-white py-8">Loading portal access...</div>
            ) : portalAccess.length === 0 ? (
              <div className="text-center text-blue-200 py-8">No portal access records found</div>
            ) : (
              <div className="space-y-4">
                {portalAccess.map((access) => (
                  <div key={access.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="text-white font-semibold">{access.patient_name}</h3>
                        <p className="text-blue-200">Access Level: {access.access_level}</p>
                        <p className="text-blue-300 text-sm">
                          Features: {access.features_enabled?.join(', ') || 'None'}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          access.is_active ? 'bg-green-500/20 text-green-300' : 'bg-gray-500/20 text-gray-300'
                        }`}>
                          {access.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// 5. Documents Module
const DocumentsModule = ({ setActiveModule }) => {
  const [documents, setDocuments] = useState([]);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadDocument = async (formData) => {
    try {
      await axios.post(`${API}/documents/upload`, formData);
      fetchDocuments();
      setShowUploadForm(false);
    } catch (error) {
      console.error('Error uploading document:', error);
      alert('Error uploading document');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-400 hover:text-blue-300 mb-2 flex items-center"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Document Management</h1>
            <p className="text-blue-200">Manage clinical documents and workflows</p>
          </div>
          <button
            onClick={() => setShowUploadForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Upload Document
          </button>
        </div>

        {/* Documents List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Documents</h2>
            {loading ? (
              <div className="text-center text-white py-8">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="text-center text-blue-200 py-8">No documents found</div>
            ) : (
              <div className="space-y-4">
                {documents.map((document) => (
                  <div key={document.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="text-white font-semibold">{document.title}</h3>
                        <p className="text-blue-200">Type: {document.document_type}</p>
                        <p className="text-blue-300 text-sm">Patient: {document.patient_name || 'N/A'}</p>
                        <p className="text-blue-300 text-sm">Category: {document.category_name || 'Uncategorized'}</p>
                      </div>
                      <div className="text-right">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          document.status === 'active' ? 'bg-green-500/20 text-green-300' :
                          document.status === 'pending' ? 'bg-yellow-500/20 text-yellow-300' :
                          'bg-gray-500/20 text-gray-300'
                        }`}>
                          {document.status?.charAt(0).toUpperCase() + document.status?.slice(1) || 'Unknown'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// 6. Telehealth Module
const TelehealthModule = ({ setActiveModule }) => {
  const [sessions, setSessions] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/telehealth`);
      setSessions(response.data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSession = async (formData) => {
    try {
      await axios.post(`${API}/telehealth`, formData);
      fetchSessions();
      setShowCreateForm(false);
    } catch (error) {
      console.error('Error creating session:', error);
      alert('Error creating session');
    }
  };

  const joinSession = async (sessionId) => {
    try {
      const response = await axios.post(`${API}/telehealth/${sessionId}/join`, { user_type: 'provider' });
      window.open(response.data.join_url, '_blank');
    } catch (error) {
      console.error('Error joining session:', error);
      alert('Error joining session');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <button
              onClick={() => setActiveModule('dashboard')}
              className="text-blue-400 hover:text-blue-300 mb-2 flex items-center"
            >
              ← Back to Dashboard
            </button>
            <h1 className="text-3xl font-bold text-white">Telehealth Sessions</h1>
            <p className="text-blue-200">Manage video consultations and virtual visits</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
          >
            Schedule Session
          </button>
        </div>

        {/* Sessions List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20">
          <div className="p-6">
            <h2 className="text-xl font-bold text-white mb-4">Telehealth Sessions</h2>
            {loading ? (
              <div className="text-center text-white py-8">Loading sessions...</div>
            ) : sessions.length === 0 ? (
              <div className="text-center text-blue-200 py-8">No sessions found</div>
            ) : (
              <div className="space-y-4">
                {sessions.map((session) => (
                  <div key={session.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <h3 className="text-white font-semibold">{session.patient_name}</h3>
                        <p className="text-blue-200">Provider: {session.provider_name}</p>
                        <p className="text-blue-300 text-sm">Type: {session.session_type}</p>
                        <p className="text-blue-300 text-sm">
                          Scheduled: {new Date(session.scheduled_start).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right space-y-2">
                        <span className={`px-3 py-1 rounded-full text-sm block ${
                          session.status === 'scheduled' ? 'bg-blue-500/20 text-blue-300' :
                          session.status === 'active' ? 'bg-green-500/20 text-green-300' :
                          session.status === 'completed' ? 'bg-gray-500/20 text-gray-300' :
                          'bg-yellow-500/20 text-yellow-300'
                        }`}>
                          {session.status?.charAt(0).toUpperCase() + session.status?.slice(1)}
                        </span>
                        {session.status === 'scheduled' && (
                          <button
                            onClick={() => joinSession(session.id)}
                            className="bg-green-600 hover:bg-green-700 text-white px-4 py-1 rounded text-sm"
                          >
                            Join Session
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
          <ProtectedRoute permission="patients:read">
            <AppHeader>
              <PatientsModule setActiveModule={setActiveModule} />
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
            <AppHeader>
              <CommunicationsModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'lab-orders':
        return (
          <ProtectedRoute permission="lab:read">
            <LabIntegrationModule setActiveModule={setActiveModule} />
          </ProtectedRoute>
        );
      case 'insurance':
        return (
          <ProtectedRoute permission="insurance:read">
            <InsuranceVerificationModule setActiveModule={setActiveModule} />
          </ProtectedRoute>
        );
      case 'referrals':
        return (
          <ProtectedRoute permission="referrals:read">
            <AppHeader>
              <ReferralsModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'clinical-templates':
        return (
          <ProtectedRoute permission="templates:read">
            <AppHeader>
              <ClinicalTemplatesModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'quality-measures':
        return (
          <ProtectedRoute permission="quality:read">
            <AppHeader>
              <QualityMeasuresModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'patient-portal-mgmt':
        return (
          <ProtectedRoute permission="portal:read">
            <AppHeader>
              <PatientPortalMgmtModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'documents':
        return (
          <ProtectedRoute permission="documents:read">
            <AppHeader>
              <DocumentsModule setActiveModule={setActiveModule} />
            </AppHeader>
          </ProtectedRoute>
        );
      case 'telehealth':
        return (
          <ProtectedRoute permission="telehealth:read">
            <AppHeader>
              <TelehealthModule setActiveModule={setActiveModule} />
            </AppHeader>
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