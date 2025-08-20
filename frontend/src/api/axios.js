// app/frontend/src/api/axios.js
import axios from "axios";

// Use direct environment variable for backend URL
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "/api";

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