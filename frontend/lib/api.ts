import axios from 'axios';

const API_URL = '/api';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export const auth = {
  register: (data: { email: string; password: string; full_name?: string }) =>
    api.post('/auth/register', data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

export const contacts = {
  list: (search?: string) => api.get('/contacts', { params: { search } }),
  get: (id: number) => api.get(`/contacts/${id}`),
  create: (data: any) => api.post('/contacts', data),
  update: (id: number, data: any) => api.put(`/contacts/${id}`, data),
  delete: (id: number) => api.delete(`/contacts/${id}`),
};

export const opportunities = {
  list: (params?: any) => api.get('/opportunities', { params }),
  get: (id: number) => api.get(`/opportunities/${id}`),
  create: (data: any) => api.post('/opportunities', data),
  update: (id: number, data: any) => api.put(`/opportunities/${id}`, data),
  updateStage: (id: number, stage: string) =>
    api.put(`/opportunities/${id}/stage`, null, { params: { stage } }),
  delete: (id: number) => api.delete(`/opportunities/${id}`),
};

export const tasks = {
  list: (params?: any) => api.get('/tasks', { params }),
  get: (id: number) => api.get(`/tasks/${id}`),
  create: (data: any) => api.post('/tasks', data),
  update: (id: number, data: any) => api.put(`/tasks/${id}`, data),
  updateStatus: (id: number, status: string) =>
    api.put(`/tasks/${id}/status`, null, { params: { status } }),
  delete: (id: number) => api.delete(`/tasks/${id}`),
};

export const activities = {
  list: (params?: any) => api.get('/activities', { params }),
  get: (id: number) => api.get(`/activities/${id}`),
  create: (data: any) => api.post('/activities', data),
  update: (id: number, data: any) => api.put(`/activities/${id}`, data),
  delete: (id: number) => api.delete(`/activities/${id}`),
};

export const reports = {
  dashboard: () => api.get('/reports/dashboard'),
  pipeline: () => api.get('/reports/pipeline'),
  contacts: () => api.get('/reports/contacts'),
};

export const users = {
  list: () => api.get('/users'),
  get: (id: number) => api.get(`/users/${id}`),
};

export const googleCalendar = {
  status: () => api.get('/google-calendar/credentials'),
  saveCredentials: (data: { oauth_credentials?: any; test_email?: string }) =>
    api.post('/google-calendar/credentials', data),
  oauthAuthorize: (redirect_uri?: string) =>
    api.post('/google-calendar/oauth/authorize',
      redirect_uri ? { redirect_uri } : {}),
  oauthComplete: (code: string, redirect_uri?: string, state?: string) =>
    api.post('/google-calendar/oauth/complete', {
      code,
      redirect_uri,
      state,
    }),
  clearCredentials: () => api.delete('/google-calendar/credentials'),
  listEvents: (params?: any) => api.get('/google-calendar/events', { params }),
  createEvent: (data: any, params?: any) =>
    api.post('/google-calendar/events', data, { params }),
  updateEvent: (id: string, data: any, params?: any) =>
    api.put(`/google-calendar/events/${id}`, data, { params }),
  deleteEvent: (id: string, params?: any) =>
    api.delete(`/google-calendar/events/${id}`, { params }),
  listCalendars: () => api.get('/google-calendar/gcal/users/me/calendarList'),
  createCalendar: (data: any) => api.post('/google-calendar/calendar', data),
  updateCalendar: (id: string, data: any) =>
    api.put(`/google-calendar/calendar/${id}`, data),
  deleteCalendar: (id: string) => api.delete(`/google-calendar/calendar/${id}`),
};

export const emails = {
  list: (params?: any) => api.get('/emails', { params }),
  get: (id: number) => api.get(`/emails/${id}`),
  markAsRead: (id: number) => api.post(`/emails/${id}/read`),
  sync: () => api.post('/emails/sync'),
};