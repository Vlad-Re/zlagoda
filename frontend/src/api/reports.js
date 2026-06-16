import { apiFetch } from './client';

export const getChecksInPeriod = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/reports/checks-in-period/${q ? '?' + q : ''}`);
};

export const getSalesRevenue = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/reports/sales-revenue/${q ? '?' + q : ''}`);
};

export const getTotalSoldPerProduct = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/reports/total-sold-per-product/${q ? '?' + q : ''}`);
};

export const getTopCashiers = (params = {}) => {
  const q = new URLSearchParams(params).toString();
  return apiFetch(`/reports/top-cashiers/${q ? '?' + q : ''}`);
};

export const getTotalSoldPerCategory = () => apiFetch('/reports/total-sold-per-category/');
export const getCategoriesAllProductsSold = () => apiFetch('/reports/categories-all-products-sold/');
export const getCustomersServedByAll = () => apiFetch('/reports/customers-served-by-all-cashiers/');
export const getEmployeesServedAll = () => apiFetch('/reports/employees-served-all-customers/');
