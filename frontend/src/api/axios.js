// app/frontend/src/api/axios.js
import axios from "axios";

// Dynamic backend URL detection for deployment flexibility
const getBackendURL = () => {
  // If explicitly set in environment, use it
  if (process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL !== '') {
    return process.env.REACT_APP_BACKEND_URL;
  }
  
  // For deployed environments, assume backend is on same domain
  // Since frontend runs on port 3000 and backend on port 8001 in development
  // In production, both frontend and backend are on the same domain
  const currentHost = window.location.origin;
  
  // Check if we're in development (localhost:3000)
  if (currentHost.includes('localhost:3000')) {
    return 'http://localhost:8001';  // Point to local backend
  }
  
  // In production, backend is on same domain as frontend
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