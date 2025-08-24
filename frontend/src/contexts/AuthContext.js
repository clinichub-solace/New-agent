import React, { useState, useEffect, createContext, useContext } from "react";
import api from '../api/axios';

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
    if (token && !user) {
      // Only fetch user if we have token but no user data (e.g., on page refresh)
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchCurrentUser();
    } else if (!token) {
      setLoading(false);
    }
  }, [token, user]);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
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
      console.log('Environment check:', {
        REACT_APP_BACKEND_URL: process.env.REACT_APP_BACKEND_URL,
        BACKEND_URL: BACKEND_URL,
        API: API
      });
      
      console.log('Making login request to:', `${API}/auth/login`);
      console.log('Request payload:', { username, password });
      
      const response = await axios.post(`${API}/auth/login`, { username, password });
      console.log('Login response:', response.data);
      
      const { access_token, user: userData } = response.data;
      
      // Set token and user data immediately
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      // Set both token and user to trigger re-render
      setToken(access_token);
      setUser(userData);
      setLoading(false);
      
      console.log('Login successful, user set:', userData);
      
      return { success: true };
    } catch (error) {
      console.error('Login error details:', error);
      
      let errorMessage = 'Network Error';
      
      if (error.response) {
        // Server responded with error status
        errorMessage = error.response.data?.detail || error.response.data?.message || `Server Error (${error.response.status})`;
      } else if (error.request) {
        // Network error - no response received
        errorMessage = 'Network Error - Unable to reach server';
      } else {
        // Other error
        errorMessage = error.message || 'Login failed';
      }
      
      return { 
        success: false, 
        error: errorMessage 
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