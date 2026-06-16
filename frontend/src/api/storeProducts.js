import { apiFetch } from './client';

export const getStoreProducts = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/store-products/${q ? '?' + q : ''}`);
};
export const getStoreProduct = (upc) => apiFetch(`/store-products/${upc}/`);
export const createStoreProduct = (data) => apiFetch('/store-products/', { method: 'POST', body: JSON.stringify(data) });
export const updateStoreProduct = (upc, data) => apiFetch(`/store-products/${upc}/`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteStoreProduct = (upc) => apiFetch(`/store-products/${upc}/`, { method: 'DELETE' });
