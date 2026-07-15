/* Platform-admin API client & session helpers. Deliberately separate from
   /static/js/api.js: different localStorage namespace (pa_*) so a tenant
   session and a platform-admin session can coexist in the same browser
   without clobbering each other. */

const PA_API = {
  async request(method, path, body = null) {
    const headers = { 'Content-Type': 'application/json' };
    const token = PAAuth.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const opts = { method, headers };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const json = await res.json().catch(() => ({}));
    if (res.status === 401 || res.status === 403) {
      // Session expired or not a platform-admin session anymore.
      if (path !== '/api/v1/platform-admin/auth/login') {
        PAAuth.clear();
        location.href = '/admin/login';
      }
    }
    return { ok: res.ok, status: res.status, data: json };
  },
  get:    (path)       => PA_API.request('GET', path),
  post:   (path, body) => PA_API.request('POST', path, body),
  patch:  (path, body) => PA_API.request('PATCH', path, body),
  delete: (path)        => PA_API.request('DELETE', path),
};

const PAAuth = {
  save(token, info) {
    localStorage.setItem('pa_access_token', token);
    if (info) localStorage.setItem('pa_user_info', JSON.stringify(info));
  },
  getToken()    { return localStorage.getItem('pa_access_token'); },
  getUserInfo() { return JSON.parse(localStorage.getItem('pa_user_info') || 'null'); },
  isLoggedIn()  { return !!localStorage.getItem('pa_access_token'); },
  clear() {
    ['pa_access_token', 'pa_user_info'].forEach(k => localStorage.removeItem(k));
  },
};

/* ===== Small UI helpers (mirrors static/js/api.js conventions) ===== */
function paShowAlert(id, msg, type = 'danger') {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.className = `alert alert-${type} show`;
}
function paHideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.className = 'alert';
}
function paSetLoading(btn, loading, loadingText = 'جارٍ المعالجة...') {
  if (loading) {
    btn.dataset.origText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> ${loadingText}`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.origText || btn.innerHTML;
    btn.disabled = false;
  }
}
function paEscape(str) {
  return String(str ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}
