import React, { useState, useEffect, createContext, useContext } from "react";
import axios from "axios";

console.log('🚨 AuthContext.js loaded successfully!');
console.log('Environment:', process.env.NODE_ENV);
console.log('Backend URL:', process.env.REACT_APP_BACKEND_URL);


const testAPIEndpoints = async () => {
  console.log('🧪 Testing API endpoints from code...');
  
  try {
    // Test 1: Without /api prefix (current broken behavior)
    console.log('Testing WITHOUT /api prefix...');
    const response1 = await axios.post('https://med-platform-fix.preview.emergentagent.com/auth/login', 
      { test: 'data' },
      { headers: { 'Content-Type': 'application/json' } }
    );
    console.log('❌ WITHOUT /api - Status:', response1.status);
  } catch (error1) {
    console.log('❌ WITHOUT /api - Error:', error1.response?.status || error1.message);
  }
  
  try {
    // Test 2: With /api prefix (should work)
    console.log('Testing WITH /api prefix...');
    const response2 = await axios.post('https://med-platform-fix.preview.emergentagent.com/api/auth/login',
      { test: 'data' },
      { headers: { 'Content-Type': 'application/json' } }
    );
    console.log('✅ WITH /api - Status:', response2.status);
  } catch (error2) {
    console.log('✅ WITH /api - Error:', error2.response?.status || error2.message);
  }
};


const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const getAPIBaseURL = () => {
  if (process.env.NODE_ENV === 'development') {
    // In development, use relative paths (proxy handles routing)
    return '/api';
  } else {
    // In production/preview, use full URL with /api prefix
    const backendUrl = process.env.REACT_APP_BACKEND_URL || 'https://med-platform-fix.preview.emergentagent.com';
    return `${backendUrl}/api`;
  }
};

const API = getAPIBaseURL();
// const API = `${BACKEND_URL}`;

// Authentication Context
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    testAPIEndpoints(); // This will run when component loads
  }, []);

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

  // const login = async (username, password) => {
  //   try {await axios.post('https://med-platform-fix.preview.emergentagent.com/api/auth/login', await axios.post(`${API}/auth/login`, { username, password });
  //     const { access_token, user: userData } = response.data;
      
  //     localStorage.setItem('token', access_token);
  //     setToken(access_token);
  //     setUser(userData);
  //     axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
  //     return { success: true };
  //   } catch (error) {
  //     return { 
  //       success: false, 
  //       error: error.response?.data?.detail || 'Login failed' 
  //     };
  //   }
  // };

  const login = async (username, password) => {
  try {
    // TEMPORARY: Use hardcoded correct URL
    console.log('🚀 Attempting login with correct /api URL...');
    const response = await axios.post(`${API}/auth/login`, { username, password });
    
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem('token', access_token);
    setToken(access_token);
    setUser(userData);
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    return { success: true };
  } catch (error) {
    console.log('🔥 Login error details:', error);
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

export default AuthContext;