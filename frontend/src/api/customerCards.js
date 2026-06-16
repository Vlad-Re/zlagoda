import { apiFetch } from './client';

export const getCustomerCards = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/customer-cards/${q ? '?' + q : ''}`);
};
export const getCustomerCard = (id) => apiFetch(`/customer-cards/${id}/`);
export const createCustomerCard = (data) => apiFetch('/customer-cards/', { method: 'POST', body: JSON.stringify(data) });
export const updateCustomerCard = (id, data) => apiFetch(`/customer-cards/${id}/`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteCustomerCard = (id) => apiFetch(`/customer-cards/${id}/`, { method: 'DELETE' });
