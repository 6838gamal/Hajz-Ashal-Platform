/* Platform-admin dashboard logic: Tenants / Branches / Users / Roles CRUD.
   Talks only to /api/v1/platform-admin/* via PA_API (see admin-api.js). */

const API_BASE = '/api/v1/platform-admin';
let paDebounceTimer = null;
let currentBranchTenantId = null;
let allPermissions = [];
let allTenantsForUserForm = [];

function paDebounce(fn, delay = 350) {
  clearTimeout(paDebounceTimer);
  paDebounceTimer = setTimeout(fn, delay);
}

function paSwitchPage(page) {
  document.querySelectorAll('.pa-page').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.pa-tab').forEach(el => el.classList.remove('active'));
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.add('active');
  const tab = document.querySelector(`.pa-tab[data-page="${page}"]`);
  if (tab) tab.classList.add('active');
  if (page === 'tenants') loadTenants();
  if (page === 'users') loadUsers();
  if (page === 'roles') loadRoles();
}

function paOpenModal(id) { document.getElementById(id).classList.add('open'); }
function paCloseModal(id) { document.getElementById(id).classList.remove('open'); }

const STATUS_LABELS = {
  trial: 'تجربة', active: 'فعّالة', suspended: 'موقوفة', disabled: 'معطّل',
};

/* ===================== TENANTS ===================== */

async function loadTenants() {
  const search = document.getElementById('tenants-search').value.trim();
  const qs = new URLSearchParams({ page: '1', page_size: '100' });
  if (search) qs.set('search', search);
  const res = await PA_API.get(`${API_BASE}/tenants?${qs}`);
  const tbody = document.getElementById('tenants-tbody');
  const empty = document.getElementById('tenants-empty');
  if (!res.ok) { paShowAlert('alert-box', 'فشل تحميل المنشآت.'); return; }
  const rows = res.data.data || [];
  allTenantsForUserForm = rows;
  empty.style.display = rows.length ? 'none' : 'block';
  tbody.innerHTML = rows.map(t => `
    <tr>
      <td><a href="#" onclick="openBranches('${t.id}','${paEscape(t.name)}');return false;" style="color:var(--primary);text-decoration:none;font-weight:600;">${paEscape(t.name)}</a></td>
      <td dir="ltr" style="color:var(--text-muted);">${paEscape(t.slug)}</td>
      <td><span class="pa-badge pa-badge--${t.status}">${STATUS_LABELS[t.status] || t.status}</span></td>
      <td>
        <div class="pa-actions">
          <button class="pa-btn-icon" title="تعديل" onclick='openTenantModal(${JSON.stringify(t)})'>✏️</button>
          <button class="pa-btn-icon danger" title="حذف" onclick="deleteTenant('${t.id}','${paEscape(t.name)}')">🗑️</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function openTenantModal(tenant) {
  document.getElementById('tenant-edit-id').value = tenant.id;
  document.getElementById('tenant-edit-name').value = tenant.name;
  document.getElementById('tenant-edit-status').value = tenant.status;
  paOpenModal('modal-tenant');
}

async function saveTenant() {
  const id = document.getElementById('tenant-edit-id').value;
  const btn = document.getElementById('tenant-save-btn');
  paSetLoading(btn, true);
  try {
    const res = await PA_API.patch(`${API_BASE}/tenants/${id}`, {
      name: document.getElementById('tenant-edit-name').value.trim(),
      status: document.getElementById('tenant-edit-status').value,
    });
    if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حفظ المنشأة.'); return; }
    paCloseModal('modal-tenant');
    loadTenants();
  } finally { paSetLoading(btn, false); }
}

async function deleteTenant(id, name) {
  if (!confirm(`حذف المنشأة "${name}"؟ سيتم إخفاؤها ولا يمكن التراجع بسهولة.`)) return;
  const res = await PA_API.delete(`${API_BASE}/tenants/${id}`);
  if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حذف المنشأة.'); return; }
  loadTenants();
}

/* ===================== BRANCHES ===================== */

function openBranches(tenantId, tenantName) {
  currentBranchTenantId = tenantId;
  document.getElementById('branches-tenant-name').textContent = tenantName;
  paSwitchPage('branches');
  loadBranches();
}

async function loadBranches() {
  const res = await PA_API.get(`${API_BASE}/tenants/${currentBranchTenantId}/branches`);
  const tbody = document.getElementById('branches-tbody');
  const empty = document.getElementById('branches-empty');
  if (!res.ok) { paShowAlert('alert-box', 'فشل تحميل الفروع.'); return; }
  const rows = res.data.data || [];
  empty.style.display = rows.length ? 'none' : 'block';
  tbody.innerHTML = rows.map(b => `
    <tr>
      <td>${paEscape(b.name)}</td>
      <td style="color:var(--text-muted);">${paEscape(b.address || '—')}</td>
      <td dir="ltr">${paEscape(b.timezone)}</td>
      <td>
        <div class="pa-actions">
          <button class="pa-btn-icon" title="تعديل" onclick='openBranchModal(${JSON.stringify(b)})'>✏️</button>
          <button class="pa-btn-icon danger" title="حذف" onclick="deleteBranch('${b.id}','${paEscape(b.name)}')">🗑️</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function openBranchModal(branch) {
  document.getElementById('branch-modal-title').textContent = branch ? 'تعديل فرع' : 'فرع جديد';
  document.getElementById('branch-edit-id').value = branch?.id || '';
  document.getElementById('branch-edit-name').value = branch?.name || '';
  document.getElementById('branch-edit-address').value = branch?.address || '';
  document.getElementById('branch-edit-timezone').value = branch?.timezone || 'UTC';
  paOpenModal('modal-branch');
}

async function saveBranch() {
  const id = document.getElementById('branch-edit-id').value;
  const btn = document.getElementById('branch-save-btn');
  const payload = {
    name: document.getElementById('branch-edit-name').value.trim(),
    address: document.getElementById('branch-edit-address').value.trim() || null,
    timezone: document.getElementById('branch-edit-timezone').value.trim() || 'UTC',
  };
  paSetLoading(btn, true);
  try {
    const res = id
      ? await PA_API.patch(`${API_BASE}/branches/${id}`, payload)
      : await PA_API.post(`${API_BASE}/tenants/${currentBranchTenantId}/branches`, payload);
    if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حفظ الفرع.'); return; }
    paCloseModal('modal-branch');
    loadBranches();
  } finally { paSetLoading(btn, false); }
}

async function deleteBranch(id, name) {
  if (!confirm(`حذف الفرع "${name}"؟`)) return;
  const res = await PA_API.delete(`${API_BASE}/branches/${id}`);
  if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حذف الفرع.'); return; }
  loadBranches();
}

/* ===================== USERS ===================== */

async function loadUsers() {
  if (!allTenantsForUserForm.length) {
    const tRes = await PA_API.get(`${API_BASE}/tenants?page=1&page_size=200`);
    if (tRes.ok) allTenantsForUserForm = tRes.data.data || [];
  }
  const search = document.getElementById('users-search').value.trim();
  const qs = new URLSearchParams({ page: '1', page_size: '100' });
  if (search) qs.set('search', search);
  const res = await PA_API.get(`${API_BASE}/users?${qs}`);
  const tbody = document.getElementById('users-tbody');
  const empty = document.getElementById('users-empty');
  if (!res.ok) { paShowAlert('alert-box', 'فشل تحميل المستخدمين.'); return; }
  const rows = res.data.data || [];
  empty.style.display = rows.length ? 'none' : 'block';
  const tenantNameById = Object.fromEntries(allTenantsForUserForm.map(t => [t.id, t.name]));
  tbody.innerHTML = rows.map(u => `
    <tr>
      <td>${paEscape(u.full_name)}<div style="color:var(--text-muted);font-size:.78rem;">${paEscape(tenantNameById[u.tenant_id] || u.tenant_id)}</div></td>
      <td dir="ltr">${paEscape(u.email)}</td>
      <td><span class="pa-badge pa-badge--${u.status === 'active' ? 'active' : 'disabled'}">${STATUS_LABELS[u.status] || u.status}</span></td>
      <td>
        <div class="pa-actions">
          <button class="pa-btn-icon" title="تعديل" onclick='openUserModal(${JSON.stringify(u)})'>✏️</button>
          <button class="pa-btn-icon" title="الأدوار" onclick="manageUserRoles('${u.id}','${paEscape(u.full_name)}')">🔐</button>
          <button class="pa-btn-icon danger" title="حذف" onclick="deleteUser('${u.id}','${paEscape(u.full_name)}')">🗑️</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function openUserModal(user) {
  const isEdit = !!user;
  document.getElementById('user-modal-title').textContent = isEdit ? 'تعديل مستخدم' : 'مستخدم جديد';
  document.getElementById('user-edit-id').value = user?.id || '';
  document.getElementById('user-edit-name').value = user?.full_name || '';
  document.getElementById('user-edit-email').value = user?.email || '';
  document.getElementById('user-edit-password').value = '';
  document.getElementById('user-edit-status').value = user?.status || 'active';
  document.getElementById('user-password-hint').textContent = isEdit ? '(اتركه فارغاً للاحتفاظ بالحالية)' : '';

  document.getElementById('user-tenant-group').style.display = isEdit ? 'none' : 'block';
  document.getElementById('user-email-group').style.display = isEdit ? 'none' : 'block';
  document.getElementById('user-status-group').style.display = isEdit ? 'block' : 'none';

  const select = document.getElementById('user-edit-tenant');
  select.innerHTML = allTenantsForUserForm.map(t => `<option value="${t.id}">${paEscape(t.name)}</option>`).join('');

  paOpenModal('modal-user');
}

async function saveUser() {
  const id = document.getElementById('user-edit-id').value;
  const btn = document.getElementById('user-save-btn');
  const password = document.getElementById('user-edit-password').value;
  paSetLoading(btn, true);
  try {
    let res;
    if (id) {
      const payload = { full_name: document.getElementById('user-edit-name').value.trim(), status: document.getElementById('user-edit-status').value };
      if (password) payload.password = password;
      res = await PA_API.patch(`${API_BASE}/users/${id}`, payload);
    } else {
      if (!password) { paShowAlert('alert-box', 'كلمة المرور مطلوبة للمستخدم الجديد.'); return; }
      res = await PA_API.post(`${API_BASE}/users`, {
        tenant_id: document.getElementById('user-edit-tenant').value,
        email: document.getElementById('user-edit-email').value.trim(),
        password,
        full_name: document.getElementById('user-edit-name').value.trim(),
      });
    }
    if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حفظ المستخدم.'); return; }
    paCloseModal('modal-user');
    loadUsers();
  } finally { paSetLoading(btn, false); }
}

async function deleteUser(id, name) {
  if (!confirm(`حذف المستخدم "${name}"؟`)) return;
  const res = await PA_API.delete(`${API_BASE}/users/${id}`);
  if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حذف المستخدم.'); return; }
  loadUsers();
}

async function manageUserRoles(userId, userName) {
  const [rolesRes, userRolesRes] = await Promise.all([
    PA_API.get(`${API_BASE}/roles`),
    PA_API.get(`${API_BASE}/users/${userId}/roles`),
  ]);
  if (!rolesRes.ok || !userRolesRes.ok) { paShowAlert('alert-box', 'فشل تحميل الأدوار.'); return; }
  const allRoles = rolesRes.data.data || [];
  const assignedIds = new Set((userRolesRes.data.data || []).map(r => r.id));

  if (!allRoles.length) { alert('لا توجد أدوار عامة معرّفة بعد. أنشئ دوراً أولاً من تبويب "الأدوار والصلاحيات".'); return; }

  const choice = prompt(
    `أدوار "${userName}"\nالمعيّنة حالياً: ${[...assignedIds].map(id => allRoles.find(r => r.id === id)?.name).filter(Boolean).join('، ') || 'بدون'}\n\n` +
    `أدخل اسم الدور لتعيينه، أو اكتب "-اسم الدور" لإزالته.\nالأدوار المتاحة: ${allRoles.map(r => r.name).join('، ')}`
  );
  if (!choice) return;
  const remove = choice.trim().startsWith('-');
  const roleName = remove ? choice.trim().slice(1).trim() : choice.trim();
  const role = allRoles.find(r => r.name === roleName);
  if (!role) { alert('اسم الدور غير معروف.'); return; }

  const res = remove
    ? await PA_API.delete(`${API_BASE}/users/${userId}/roles/${role.id}`)
    : await PA_API.post(`${API_BASE}/users/${userId}/roles`, { role_id: role.id });
  if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشلت العملية.'); return; }
  paShowAlert('alert-box', 'تم تحديث أدوار المستخدم.', 'success');
}

/* ===================== ROLES & PERMISSIONS ===================== */

async function loadRoles() {
  if (!allPermissions.length) {
    const pRes = await PA_API.get(`${API_BASE}/permissions`);
    if (pRes.ok) allPermissions = pRes.data.data || [];
  }
  const res = await PA_API.get(`${API_BASE}/roles`);
  const tbody = document.getElementById('roles-tbody');
  const empty = document.getElementById('roles-empty');
  if (!res.ok) { paShowAlert('alert-box', 'فشل تحميل الأدوار.'); return; }
  const rows = res.data.data || [];
  empty.style.display = rows.length ? 'none' : 'block';
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${paEscape(r.name)}${r.is_system_role ? ' <span class="pa-badge pa-badge--active">نظامي</span>' : ''}</td>
      <td><div class="pa-chip-list">${(r.permission_codes || []).map(c => `<span class="pa-chip">${paEscape(c)}</span>`).join('') || '<span style="color:var(--text-muted);">بدون صلاحيات</span>'}</div></td>
      <td>
        <div class="pa-actions">
          <button class="pa-btn-icon" title="تعديل" onclick='openRoleModal(${JSON.stringify(r)})'>✏️</button>
          <button class="pa-btn-icon danger" title="حذف" onclick="deleteRole('${r.id}','${paEscape(r.name)}')">🗑️</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function openRoleModal(role) {
  document.getElementById('role-modal-title').textContent = role ? 'تعديل دور' : 'دور جديد';
  document.getElementById('role-edit-id').value = role?.id || '';
  document.getElementById('role-edit-name').value = role?.name || '';
  const selectedCodes = new Set(role?.permission_codes || []);
  const list = document.getElementById('role-permissions-list');
  list.innerHTML = allPermissions.map(p => `
    <label>
      <input type="checkbox" value="${p.code}" ${selectedCodes.has(p.code) ? 'checked' : ''}>
      ${paEscape(p.code)}
    </label>
  `).join('');
  paOpenModal('modal-role');
}

async function saveRole() {
  const id = document.getElementById('role-edit-id').value;
  const btn = document.getElementById('role-save-btn');
  const name = document.getElementById('role-edit-name').value.trim();
  const permission_codes = [...document.querySelectorAll('#role-permissions-list input:checked')].map(el => el.value);
  paSetLoading(btn, true);
  try {
    const res = id
      ? await PA_API.patch(`${API_BASE}/roles/${id}`, { name, permission_codes })
      : await PA_API.post(`${API_BASE}/roles`, { name, permission_codes });
    if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حفظ الدور.'); return; }
    paCloseModal('modal-role');
    loadRoles();
  } finally { paSetLoading(btn, false); }
}

async function deleteRole(id, name) {
  if (!confirm(`حذف الدور "${name}"؟`)) return;
  const res = await PA_API.delete(`${API_BASE}/roles/${id}`);
  if (!res.ok) { paShowAlert('alert-box', res.data?.error?.message || 'فشل حذف الدور.'); return; }
  loadRoles();
}

/* ===================== INIT ===================== */
loadTenants();
