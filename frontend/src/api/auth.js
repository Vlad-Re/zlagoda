import { apiFetch } from './client';

export const login = (id_employee, password) =>
  apiFetch('/auth/login', { method: 'POST', body: JSON.stringify({ id_employee, password }) });

export const logout = () =>
  apiFetch('/auth/logout', { method: 'POST' });

export const getMe = () =>
  apiFetch('/auth/me');
