// app/frontend/src/api/axios.js
import axios from "axios";

// Hardcoded API configuration to bypass environment variable issues in deployment
const BACKEND_URL = "/api";

const api = axios.create({
  baseURL: BACKEND_URL
});

api.interceptors.response.use(
  (response) => response,
  (err) => {
    const payload = err?.response?.data ?? { message: err.message || "Network error" };
    return Promise.reject({ ...err, payload });
  }
);

export default api;