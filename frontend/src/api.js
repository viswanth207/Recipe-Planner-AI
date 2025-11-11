import axios from "axios";

const API_URL = https://meal-planner-ai-45kt-pvirowgku-sai-viswanths-projects.vercel.app/";
const VOICEBOT_URL = process.env.REACT_APP_VOICEBOT_URL || "http://127.0.0.1:8001";

const getToken = () => localStorage.getItem("token");

export const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

axiosInstance.interceptors.request.use(config => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Separate client for Voicebot AI server (mainv.py)
export const axiosVoicebot = axios.create({
  baseURL: VOICEBOT_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

axiosVoicebot.interceptors.request.use(config => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
