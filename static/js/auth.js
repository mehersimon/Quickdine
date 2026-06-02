// Shared auth utilities
function getToken() { return localStorage.getItem('qd_token'); }
function getRid()   { return localStorage.getItem('qd_rid'); }
function v(id)      { return document.getElementById(id)?.value?.trim() || ''; }

function requireAuth() {
  if (!getToken()) { window.location.href = '/login'; return; }
  // Populate sidebar user info
  const name = localStorage.getItem('qd_name') || 'Manager';
  const sbName = document.getElementById('sb-name');
  if (sbName) sbName.textContent = name;
  const avatar = document.querySelector('.avatar');
  if (avatar) avatar.textContent = name[0].toUpperCase();
}

function logout() {
  localStorage.clear();
  window.location.href = '/login';
}

async function api(url, options = {}) {
  const token = getToken();
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) { logout(); return; }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

// Mobile sidebar
function toggleSidebar() {
  document.querySelector('.sidebar')?.classList.toggle('open');
  document.querySelector('.sidebar-overlay')?.classList.toggle('open');
}
function closeSidebar() {
  document.querySelector('.sidebar')?.classList.remove('open');
  document.querySelector('.sidebar-overlay')?.classList.remove('open');
}
