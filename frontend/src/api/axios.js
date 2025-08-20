// app/frontend/src/api/axios.js
import axios from "axios";

// Dynamic backend URL detection for deployment flexibility
const getBackendURL = () => {
  // Always use environment variable if set
  if (process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL !== '') {
    return process.env.REACT_APP_BACKEND_URL;
  }
  
  // Fallback to same domain as frontend
  return window.location.origin;
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