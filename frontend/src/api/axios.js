// app/frontend/src/api/axios.js
import axios from "axios";

// Dynamic backend URL detection for deployment flexibility
const getBackendURL = () => {
  // If explicitly set in environment, use it
  if (process.env.REACT_APP_BACKEND_URL && process.env.REACT_APP_BACKEND_URL !== '') {
    return process.env.REACT_APP_BACKEND_URL;
  }
  
  // For deployed environments, use current domain
  const currentHost = window.location.origin;
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