import { apiFetch } from './client';

export const getChecks = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/checks/${q ? '?' + q : ''}`);
};
export const getCheck = (id) => apiFetch(`/checks/${id}/`);
export const createCheck = (data) => apiFetch('/checks/', { method: 'POST', body: JSON.stringify(data) });
export const deleteCheck = (id) => apiFetch(`/checks/${id}/`, { method: 'DELETE' });
