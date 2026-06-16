import { apiFetch } from './client';

export const getDropdown = (entity) => apiFetch(`/ui/dropdowns/${entity}/`);
