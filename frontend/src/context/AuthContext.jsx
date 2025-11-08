import React, { createContext, useState, useEffect, useContext } from 'react';
import { axiosInstance } from '../api';
import { useNavigate } from 'react-router-dom';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUser = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await axiosInstance.get('/auth/me');
          setUser(response.data);
        } catch (error) {
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    fetchUser();
  }, []);

  const login = async (email, password, phone) => {
    try {
      const payload = { email: (email || '').trim(), password };
      if (phone !== undefined) {
        payload.phone = (phone || '').trim();
      }
      const res = await axiosInstance.post('/auth/login', payload);
      localStorage.setItem('token', res.data.access_token);
      const userRes = await axiosInstance.get('/auth/me');
      setUser(userRes.data);
      return true;
    } catch (error) {
      return false;
    }
  };

  const signup = async (userData) => {
    try {
      const res = await axiosInstance.post('/auth/signup', userData);
      localStorage.setItem('token', res.data.access_token);
      const userRes = await axiosInstance.get('/auth/me');
      setUser(userRes.data);
      return true;
    } catch (error) {
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    navigate('/');
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;