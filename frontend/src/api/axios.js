// app/frontend/src/api/axios.js
import axios from "axios";

// Dynamic backend URL detection for deployment flexibility
const getBackendURL = () => {
  // If explicitly set in environment, use it
  if (process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL !== '') {
    return process.env.REACT_APP_BACKEND_URL;
  }
  
  // Get current host information
  const currentHost = window.location.origin;
  const hostname = window.location.hostname;
  
  // Check if we're in local development
  if (hostname === 'localhost' && window.location.port === '3000') {
    return 'http://localhost:8001';  // Point to local backend
  }
  
  // For all production/deployed environments, backend is on same domain
  return currentHost;
};

const api = axios.create({
  baseURL: getBackendURL()
});

api.interceptors.response.use(
  (response) => response,
  (err) => {
    const payload = err?.response?.data ?? { message: err.message || "Network error" };
    return Promise.reject({ ...err, payload });
  }
);

export default api;