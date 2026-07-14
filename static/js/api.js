/* ===== API Client ===== */
const API = {
  async request(method, path, body = null, token = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const json = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data: json };
  },
  post: (path, body, token) => API.request('POST', path, body, token),
  get:  (path, token)       => API.request('GET',  path, null, token),
};

/* ===== Token helpers ===== */
const Auth = {
  save(tokens, info) {
    localStorage.setItem('access_token',  tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    if (info) localStorage.setItem('user_info', JSON.stringify(info));
  },
  getAccess()       { return localStorage.getItem('access_token'); },
  getUserInfo()     { return JSON.parse(localStorage.getItem('user_info') || 'null'); },
  getAccountType()  { return localStorage.getItem('account_type'); },          // 'business' | 'client'
  setAccountType(t) { localStorage.setItem('account_type', t); },
  getDashboardUrl() {
    return localStorage.getItem('account_type') === 'business'
      ? '/dashboard/admin'
      : '/dashboard/client';
  },
  clear() {
    ['access_token', 'refresh_token', 'user_info', 'account_type']
      .forEach(k => localStorage.removeItem(k));
  },
  isLoggedIn() { return !!localStorage.getItem('access_token'); },
};

/* ===== UI helpers ===== */
function showAlert(id, msg, type = 'danger') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `alert alert-${type} show`;
}
function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.className = 'alert';
}
function setLoading(btn, loading) {
  if (loading) {
    btn.dataset.origText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> جارٍ المعالجة...';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.origText || btn.innerHTML;
    btn.disabled = false;
  }
}
function fieldError(inputId, msg) {
  const el = document.getElementById(inputId + '_err');
  const inp = document.getElementById(inputId);
  if (el) { el.textContent = msg; el.classList.toggle('show', !!msg); }
  if (inp) inp.classList.toggle('error', !!msg);
}
function clearErrors(...ids) { ids.forEach(id => fieldError(id, '')); }

/* ===== Slug generator ===== */
function toSlug(str) {
  return str.toLowerCase()
    .replace(/[\u0600-\u06FF]/g, '') // remove Arabic chars
    .replace(/[^a-z0-9\s-]/g, '')
    .trim().replace(/\s+/g, '-')
    .replace(/-+/g, '-');
}

/* ===== Password toggle ===== */
function togglePassword(inputId) {
  const inp = document.getElementById(inputId);
  if (!inp) return;
  inp.type = inp.type === 'password' ? 'text' : 'password';
}

/* ===== JWT decoder (no validation — client display only) ===== */
function decodeJWT(token) {
  try {
    return JSON.parse(atob(token.split('.')[1].replace(/-/g,'+').replace(/_/g,'/')));
  } catch { return {}; }
}
