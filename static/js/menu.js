let editingId = null;

async function loadMenuItems() {
  const grid = document.getElementById('menu-grid');
  try {
    const items = await api('/api/dashboard/menu');
    if (!items.length) {
      grid.innerHTML = '<div class="loading-spinner">No menu items yet. Add your first item!</div>';
      return;
    }
    grid.innerHTML = items.map(renderFoodCard).join('');
  } catch(e) {
    grid.innerHTML = `<div class="loading-spinner" style="color:#ff5064">${e.message}</div>`;
  }
}

function renderFoodCard(item) {
  const img = item.image_url
    ? `<img src="${item.image_url}" class="food-img" alt="${item.name}">`
    : `<div class="food-img-placeholder">🍽️</div>`;
  return `
    <div class="food-card ${item.is_available ? '' : 'unavailable'}" id="fc-${item.id}">
      ${img}
      <div class="food-body">
        <div class="food-cat">${item.category}</div>
        <div class="food-name">${item.name}</div>
        <div class="food-desc">${item.description || 'No description'}</div>
        <div class="food-price">₹${item.price.toFixed(2)}</div>
      </div>
      <div class="food-actions">
        <button class="btn btn-ghost" onclick="editItem(${item.id})">✏ Edit</button>
        <button class="btn btn-ghost" onclick="toggleAvail(${item.id})">${item.is_available ? '🚫 Hide' : '✅ Show'}</button>
        <button class="btn btn-ghost" style="color:#ff5064" onclick="deleteItem(${item.id})">🗑</button>
      </div>
    </div>`;
}

function openModal(reset = true) {
  if (reset) {
    editingId = null;
    document.getElementById('modal-title').textContent = 'Add Food Item';
    document.getElementById('f-name').value = '';
    document.getElementById('f-desc').value = '';
    document.getElementById('f-category').value = '';
    document.getElementById('f-price').value = '';
    document.getElementById('f-image').value = '';
    document.getElementById('f-preview').style.display = 'none';
    document.getElementById('avail-group').style.display = 'none';
    document.getElementById('form-error').style.display = 'none';
    document.getElementById('save-btn').textContent = 'Save Item';
  }
  document.getElementById('modal').style.display = 'flex';
}

function closeModal() { document.getElementById('modal').style.display = 'none'; }

async function editItem(id) {
  const items = await api('/api/dashboard/menu');
  const item = items.find(i => i.id === id);
  if (!item) return;
  editingId = id;
  document.getElementById('modal-title').textContent = 'Edit Food Item';
  document.getElementById('f-name').value = item.name;
  document.getElementById('f-desc').value = item.description;
  document.getElementById('f-category').value = item.category;
  document.getElementById('f-price').value = item.price;
  document.getElementById('f-avail').checked = item.is_available;
  document.getElementById('avail-group').style.display = 'block';
  if (item.image_url) {
    document.getElementById('f-preview').src = item.image_url;
    document.getElementById('f-preview').style.display = 'block';
  }
  document.getElementById('save-btn').textContent = 'Update Item';
  openModal(false);
}

async function saveItem() {
  const btn = document.getElementById('save-btn');
  const err = document.getElementById('form-error');
  err.style.display = 'none';
  const name  = document.getElementById('f-name').value.trim();
  const price = document.getElementById('f-price').value.trim();
  if (!name || !price) { err.textContent='Name and price are required'; err.style.display='block'; return; }
  btn.disabled = true; btn.textContent = 'Saving…';

  const fd = new FormData();
  fd.append('name', name);
  fd.append('description', document.getElementById('f-desc').value);
  fd.append('category', document.getElementById('f-category').value || 'General');
  fd.append('price', parseFloat(price));
  if (editingId) fd.append('is_available', document.getElementById('f-avail').checked ? 'true' : 'false');
  const img = document.getElementById('f-image').files[0];
  if (img) fd.append('file', img);

  try {
    const url = editingId ? `/api/dashboard/menu/${editingId}` : '/api/dashboard/menu';
    const method = editingId ? 'PUT' : 'POST';
    const res = await fetch(url, {
      method, headers: {'Authorization': `Bearer ${getToken()}`}, body: fd
    });
    if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Failed'); }
    closeModal(); loadMenuItems();
  } catch(e) {
    err.textContent = e.message; err.style.display = 'block';
    btn.disabled = false; btn.textContent = editingId ? 'Update Item' : 'Save Item';
  }
}

async function toggleAvail(id) {
  await api(`/api/dashboard/menu/${id}/toggle`, {method:'PATCH'});
  loadMenuItems();
}

async function deleteItem(id) {
  if (!confirm('Delete this item?')) return;
  await api(`/api/dashboard/menu/${id}`, {method:'DELETE'});
  loadMenuItems();
}
