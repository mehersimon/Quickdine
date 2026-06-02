let ws = null;

function initOrders() {
  loadOrders();
  connectWS();
}

async function loadOrders() {
  try {
    const orders = await api('/api/dashboard/orders');
    // Clear columns
    ['Pending','Preparing','Ready','Served'].forEach(s => document.getElementById(`body-${s}`).innerHTML='');
    orders.forEach(o => insertCard(o));
  } catch(e) { console.error(e); }
}

function connectWS() {
  const rid = getRid();
  if (!rid) return;
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  ws = new WebSocket(`${proto}://${location.host}/ws/orders/${rid}`);
  const dot = document.getElementById('ws-status');

  ws.onopen = () => {
    dot.textContent = '● Connected'; dot.className = 'ws-dot connected';
  };
  ws.onclose = () => {
    dot.textContent = '● Disconnected'; dot.className = 'ws-dot disconnected';
    setTimeout(connectWS, 3000); // auto-reconnect
  };
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.type === 'new_order') {
      insertCard(msg.order, true);
      playNotif();
    } else if (msg.type === 'status_update') {
      moveCard(msg.order_id, msg.status);
    }
  };
}

function insertCard(order, isNew = false) {
  const col = document.getElementById(`body-${order.status}`);
  if (!col) return;
  const el = document.createElement('div');
  el.className = `order-card ${isNew ? 'new-order' : ''}`;
  el.id = `oc-${order.id}`;
  el.innerHTML = cardHTML(order);
  col.insertBefore(el, col.firstChild);
}

function moveCard(orderId, newStatus) {
  const el = document.getElementById(`oc-${orderId}`);
  if (!el) { loadOrders(); return; }
  const col = document.getElementById(`body-${newStatus}`);
  if (!col) return;
  el.remove();
  el.className = 'order-card new-order';
  // Update badge + buttons inside
  el.querySelector('.badge').textContent = newStatus;
  el.querySelector('.badge').className = `badge badge-${newStatus}`;
  const btnContainer = el.querySelector('.order-status-btns');
  if (btnContainer) {
    btnContainer.innerHTML = statusButtons(orderId, newStatus);
  }
  col.insertBefore(el, col.firstChild);
}

function cardHTML(order) {
  const items = order.ordered_items.map(i => `<div class="order-item-line">• ${i.name} <span style="color:var(--accent)">₹${i.price}</span></div>`).join('');
  const time  = new Date(order.timestamp).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  return `
    <div class="order-meta">
      <span class="order-id">#${order.id}</span>
      ${order.table_number ? `<span class="order-table">Table ${order.table_number}</span>` : ''}
      <span class="badge badge-${order.status}">${order.status}</span>
    </div>
    <div class="order-customer">${order.customer_name}</div>
    <div class="order-items">${items}</div>
    <div class="order-total">₹${order.total_amount.toFixed(2)}</div>
    <div class="order-time">🕐 ${time}</div>
    <div class="order-status-btns">${statusButtons(order.id, order.status)}</div>
  `;
}

function statusButtons(orderId, currentStatus) {
  return ['Pending','Preparing','Ready','Served'].map(s => `
    <button class="status-btn ${s===currentStatus?'current':''}"
      onclick="updateStatus(${orderId},'${s}')">
      ${s}
    </button>
  `).join('');
}

async function updateStatus(orderId, status) {
  try {
    await api(`/api/dashboard/orders/${orderId}/status`, {
      method:'PATCH', body: JSON.stringify({status})
    });
    // WS broadcast will handle the UI update
  } catch(e) { alert(e.message); }
}

function playNotif() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain); gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + .2);
    gain.gain.setValueAtTime(.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(.001, ctx.currentTime + .3);
    osc.start(); osc.stop(ctx.currentTime + .3);
  } catch(e) {}
}
