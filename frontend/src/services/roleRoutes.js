export const roleHome = (role) => ({
  banker: '/banker', government: '/government', superadmin: '/admin', entrepreneur: '/dashboard',
})[role] || '/login';

export const isStaffRole = (role) => ['banker', 'government', 'superadmin'].includes(role);
