import { apiFetch } from './client';

export const getProducts = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/products/${q ? '?' + q : ''}`);
};
export const getProduct = (id) => apiFetch(`/products/${id}/`);
export const createProduct = (data) => apiFetch('/products/', { method: 'POST', body: JSON.stringify(data) });
export const updateProduct = (id, data) => apiFetch(`/products/${id}/`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteProduct = (id) => apiFetch(`/products/${id}/`, { method: 'DELETE' });
