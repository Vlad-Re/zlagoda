import { apiFetch } from './client';

export const getEmployees = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/employees/${q ? '?' + q : ''}`);
};
export const getEmployee = (id) => apiFetch(`/employees/${id}/`);
export const createEmployee = (data) => apiFetch('/employees/', { method: 'POST', body: JSON.stringify(data) });
export const updateEmployee = (id, data) => apiFetch(`/employees/${id}/`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteEmployee = (id) => apiFetch(`/employees/${id}/`, { method: 'DELETE' });
export const searchEmployees = (surname) => apiFetch(`/employees/search/?surname=${encodeURIComponent(surname)}`);
