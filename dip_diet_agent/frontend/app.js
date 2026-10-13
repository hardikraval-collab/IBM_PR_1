/**
 * DIP Diet RAG Agent — Frontend Application Logic
 * Handles all UI interactions, API calls, and rendering.
 */

'use strict';

// ── Configuration ──────────────────────────────────────────────────────────────
const API_BASE = '';  // Same-origin; relative paths work
let currentUserId = localStorage.getItem('dipDietUserId') || null;
let conversationHistory = [];
let currentPlanType = 'weekly';

// ── Initialisation ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  checkHealth();
  if (currentUserId) {
    restoreProfileUI();
  }
});

// ── Health Check ──────────────────────────────────────────────────────────────
async function checkHealth() {
  const dot = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    if (res.ok) {
      const data = await res.json();
      dot.className = 'status-dot online';
      text.textContent = data.mode === 'demo'
        ? `Demo Mode • ${data.knowledge_base_chunks} chunks`
        : `IBM Granite • ${data.knowledge_base_chunks} chunks`;
    } else {
      dot.className = 'status-dot error';
      text.textContent = 'API Error';
    }
  } catch {
    dot.className = 'status-dot error';
    text.textContent = 'Offline';
  }
}

// ── Tab Navigation ────────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${tabId}`).classList.add('active');
    });
  });
}

// ── Profile Form ───────────────────────────────────────────────────────────────
document.getElementById('profileForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  await saveProfile();
});

async function saveProfile() {
  const profile = buildProfilePayload();
  if (!profile) return;

  showLoading('Saving your profile…');
  try {
    const res = await fetch(`${API_BASE}/api/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    });
    const data = await res.json();
    if (res.ok) {
      currentUserId = data.user_id;
      localStorage.setItem('dipDietUserId', currentUserId);
      showAlert('profileAlert', `✅ ${data.message}`, 'alert-success');
      showProfileCard(profile, currentUserId);
    } else {
      showAlert('profileAlert', `❌ Error: ${data.detail || 'Could not save profile.'}`, 'alert-error');
    }
  } catch (err) {
    showAlert('profileAlert', `❌ Network error: ${err.message}`, 'alert-error');
  } finally {
    hideLoading();
  }
}

function buildProfilePayload() {
  const name = document.getElementById('pName').value.trim();
  const age = parseInt(document.getElementById('pAge').value);
  if (!name || !age) {
    showAlert('profileAlert', '⚠️ Please fill in at least your name and age.', 'alert-error');
    return null;
  }

  const goals = Array.from(document.querySelectorAll('input[name="goals"]:checked')).map(c => c.value);
  const allergies = Array.from(document.querySelectorAll('input[name="allergies"]:checked')).map(c => c.value);
  const medical = Array.from(document.querySelectorAll('input[name="medical"]:checked'))
    .map(c => c.value).filter(v => v !== 'none');

  const customAllergies = document.getElementById('pAllergyCustom').value
    .split(',').map(s => s.trim()).filter(Boolean);
  const customMedical = document.getElementById('pMedicalCustom').value
    .split(',').map(s => s.trim()).filter(Boolean);

  return {
    user_id: currentUserId || undefined,
    name,
    age,
    gender: document.getElementById('pGender').value,
    weight_kg: parseFloat(document.getElementById('pWeight').value) || null,
    height_cm: parseFloat(document.getElementById('pHeight').value) || null,
    diet_preference: document.getElementById('pDiet').value,
    activity_level: document.getElementById('pActivity').value,
    food_allergies: [...allergies, ...customAllergies],
    medical_history: [...medical, ...customMedical],
    nutrition_goals: goals.length ? goals : ['maintenance'],
    location: {
      city: document.getElementById('pCity').value.trim() || 'Unknown',
      country: document.getElementById('pCountry').value.trim() || 'Unknown',
    },
  };
}

function showProfileCard(profile, userId) {
  const card = document.getElementById('profileCard');
  const content = document.getElementById('profileCardContent');
  card.classList.remove('hidden');

  const items = [
    ['Name', profile.name],
    ['Age', profile.age],
    ['User ID', userId],
    ['Diet', formatEnum(profile.diet_preference)],
    ['Activity', formatEnum(profile.activity_level)],
    ['Goals', (profile.nutrition_goals || []).map(formatEnum).join(', ')],
    ['Allergies', profile.food_allergies.length ? profile.food_allergies.join(', ') : 'None'],
    ['Location', `${profile.location.city}, ${profile.location.country}`],
  ];

  content.innerHTML = `<div class="profile-card-grid">${
    items.map(([label, value]) =>
      `<div class="profile-item"><div class="pi-label">${label}</div><div class="pi-value">${value || '—'}</div></div>`
    ).join('')
  }</div>`;
}

function loadSampleProfile() {
  document.getElementById('pName').value = 'Priya Sharma';
  document.getElementById('pAge').value = '30';
  document.getElementById('pGender').value = 'female';
  document.getElementById('pWeight').value = '65';
  document.getElementById('pHeight').value = '165';
  document.getElementById('pDiet').value = 'vegetarian';
  document.getElementById('pActivity').value = 'moderately_active';
  document.getElementById('pCity').value = 'Mumbai';
  document.getElementById('pCountry').value = 'India';

  document.querySelectorAll('input[name="goals"]').forEach(c => { c.checked = c.value === 'maintenance'; });
  document.querySelectorAll('input[name="allergies"]').forEach(c => { c.checked = false; });
  document.querySelectorAll('input[name="medical"]').forEach(c => { c.checked = c.value === 'none'; });
}

async function restoreProfileUI() {
  try {
    const res = await fetch(`${API_BASE}/api/profile/${currentUserId}`);
    if (res.ok) {
      const profile = await res.json();
      showProfileCard(profile, currentUserId);
    }
  } catch { /* ignore */ }
}

// ── Chat / RAG Q&A ─────────────────────────────────────────────────────────────
async function sendChat() {
  const input = document.getElementById('chatInput');
  const message = input.value.trim();
  if (!message) return;

  if (!currentUserId) {
    addChatMessage('assistant', '⚠️ Please save your profile first to get personalized recommendations!');
    return;
  }

  input.value = '';
  addChatMessage('user', message);
  conversationHistory.push({ role: 'user', content: message });

  const typingId = addTypingIndicator();
  const sendBtn = document.querySelector('.chat-send-btn');
  sendBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUserId,
        message,
        conversation_history: conversationHistory.slice(-8),
      }),
    });
    const data = await res.json();
    removeTypingIndicator(typingId);

    const responseText = data.response || 'No response received.';
    const sources = data.sources || [];
    conversationHistory.push({ role: 'assistant', content: responseText });
    addChatMessage('assistant', responseText, sources);
  } catch (err) {
    removeTypingIndicator(typingId);
    addChatMessage('assistant', `❌ Error: ${err.message}. Please check that the server is running.`);
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

function askQuestion(q) {
  document.getElementById('chatInput').value = q;
  // Switch to chat tab
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelector('[data-tab="chat"]').classList.add('active');
  document.getElementById('tab-chat').classList.add('active');
  sendChat();
}

function handleChatKey(e) {
  if (e.key === 'Enter' && e.ctrlKey) {
    e.preventDefault();
    sendChat();
  }
}

function addChatMessage(role, text, sources = []) {
  const container = document.getElementById('chatContainer');
  const div = document.createElement('div');
  div.className = `chat-message ${role}`;

  const avatar = role === 'user' ? '👤' : '🤖';
  const contentHtml = renderMarkdown(text);

  let sourcesHtml = '';
  if (sources.length > 0) {
    sourcesHtml = `<details class="msg-sources">
      <summary>📚 ${sources.length} source${sources.length > 1 ? 's' : ''} cited</summary>
      ${sources.map((s, i) =>
        `<div class="source-item"><strong>[${i+1}] ${escapeHtml(s.source)}</strong> (relevance: ${(s.relevance_score * 100).toFixed(0)}%)<br>${escapeHtml(s.excerpt)}</div>`
      ).join('')}
    </details>`;
  }

  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-content md-content">
      ${contentHtml}
      ${sourcesHtml}
    </div>`;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
  const container = document.getElementById('chatContainer');
  const div = document.createElement('div');
  const id = 'typing-' + Date.now();
  div.id = id;
  div.className = 'chat-message assistant';
  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-content">
      <div class="typing-indicator">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function clearChat() {
  const container = document.getElementById('chatContainer');
  container.innerHTML = `<div class="chat-message assistant">
    <div class="msg-avatar">🤖</div>
    <div class="msg-content">
      <p>Chat cleared. Ask me anything about DIP Diet and nutrition! 🥗</p>
    </div>
  </div>`;
  conversationHistory = [];
}

// ── Meal Plan ──────────────────────────────────────────────────────────────────
function selectPlanType(type, btn) {
  currentPlanType = type;
  document.querySelectorAll('.plan-type-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

async function generateMealPlan() {
  if (!currentUserId) {
    showAlert('mealPlanError', '⚠️ Please save your profile first!', 'alert-error');
    document.getElementById('mealPlanError').classList.remove('hidden');
    return;
  }

  const btn = document.getElementById('mealPlanBtnText');
  btn.textContent = '⏳ Generating…';
  showLoading(`Generating your ${currentPlanType} meal plan with IBM Granite…`);
  document.getElementById('mealPlanError').classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/meal-plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: currentUserId, plan_type: currentPlanType }),
    });
    const data = await res.json();
    if (res.ok) {
      renderMealPlan(data);
    } else {
      document.getElementById('mealPlanError').textContent = `❌ ${data.detail || 'Error generating meal plan'}`;
      document.getElementById('mealPlanError').classList.remove('hidden');
    }
  } catch (err) {
    document.getElementById('mealPlanError').textContent = `❌ Network error: ${err.message}`;
    document.getElementById('mealPlanError').classList.remove('hidden');
  } finally {
    btn.textContent = '🍽️ Generate Meal Plan';
    hideLoading();
  }
}

function renderMealPlan(data) {
  const container = document.getElementById('mealPlanContainer');
  const summary = data.nutrition_summary || {};

  const summaryHtml = summary.target_calories ? `
    <div class="plan-summary">
      <h3>📊 Nutrition Targets for ${escapeHtml(data.user_name)}</h3>
      <div class="summary-grid">
        <div class="summary-item"><div class="summary-value">${summary.target_calories}</div><div class="summary-label">Target kcal</div></div>
        <div class="summary-item"><div class="summary-value">${summary.protein_g}g</div><div class="summary-label">Protein</div></div>
        <div class="summary-item"><div class="summary-value">${summary.carbs_g}g</div><div class="summary-label">Carbohydrates</div></div>
        <div class="summary-item"><div class="summary-value">${summary.fat_g}g</div><div class="summary-label">Fat</div></div>
        <div class="summary-item"><div class="summary-value">${(summary.primary_goal || 'maintenance').replace('_', ' ')}</div><div class="summary-label">Primary Goal</div></div>
      </div>
    </div>` : '';

  const daysHtml = (data.days || []).map(day => {
    const mealsHtml = (day.meals || []).map(meal => `
      <div class="meal-card">
        <div class="meal-type">${meal.meal_type}</div>
        <div class="meal-name">${escapeHtml(meal.name)}</div>
        <div class="meal-ingredients">🥄 ${(meal.ingredients || []).map(escapeHtml).join(', ')}</div>
        <div class="meal-macros">
          <span class="macro-badge macro-cal">⚡ ${meal.calories_approx} kcal</span>
          <span class="macro-badge macro-prot">💪 ${meal.protein_g}g P</span>
          <span class="macro-badge macro-carb">🌾 ${meal.carbs_g}g C</span>
          <span class="macro-badge macro-fat">🥑 ${meal.fat_g}g F</span>
        </div>
        ${meal.preparation_notes ? `<div class="meal-note">💡 ${escapeHtml(meal.preparation_notes)}</div>` : ''}
      </div>`).join('');

    return `<div class="day-card">
      <div class="day-header">
        <div class="day-name">📅 ${day.day}</div>
        <div class="day-totals">
          Total: ${day.total_calories} kcal<br>
          P: ${day.total_protein_g}g | C: ${day.total_carbs_g}g | F: ${day.total_fat_g}g
        </div>
      </div>
      <div class="meals-grid">${mealsHtml}</div>
      ${day.hydration_tip ? `<div class="day-tip">💧 ${escapeHtml(day.hydration_tip)}</div>` : ''}
    </div>`;
  }).join('');

  const disclaimer = `<div class="alert" style="background:#fffbeb;border:1px solid #fcd34d;color:#92400e;margin-top:16px;">⚕️ ${escapeHtml(data.disclaimer)}</div>`;

  container.innerHTML = summaryHtml + daysHtml + disclaimer;
}

// ── Shopping List ──────────────────────────────────────────────────────────────
async function generateShoppingList() {
  if (!currentUserId) {
    showAlert('shoppingError', '⚠️ Please save your profile first!', 'alert-error');
    document.getElementById('shoppingError').classList.remove('hidden');
    return;
  }

  const btn = document.getElementById('shopBtnText');
  btn.textContent = '⏳ Generating…';
  showLoading('Building your shopping list…');
  document.getElementById('shoppingError').classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/shopping`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: currentUserId, plan_type: 'weekly' }),
    });
    const data = await res.json();
    if (res.ok) {
      renderShoppingList(data);
    } else {
      document.getElementById('shoppingError').textContent = `❌ ${data.detail || 'Error generating shopping list'}`;
      document.getElementById('shoppingError').classList.remove('hidden');
    }
  } catch (err) {
    document.getElementById('shoppingError').textContent = `❌ Network error: ${err.message}`;
    document.getElementById('shoppingError').classList.remove('hidden');
  } finally {
    btn.textContent = '🛒 Generate Shopping List';
    hideLoading();
  }
}

function renderShoppingList(data) {
  const container = document.getElementById('shoppingContainer');

  // Group by category
  const categories = {};
  (data.items || []).forEach(item => {
    if (!categories[item.category]) categories[item.category] = [];
    categories[item.category].push(item);
  });

  const categoryIcons = {
    'Vegetables': '🥦', 'Fruits': '🍎', 'Grains & Cereals': '🌾',
    'Legumes & Pulses': '🫘', 'Proteins (Non-Veg)': '🍗', 'Plant Proteins': '🌱',
    'Dairy & Alternatives': '🥛', 'Nuts & Seeds': '🌰', 'Oils & Fats': '🫙',
    'Herbs & Spices': '🌿', 'Condiments': '🧂', 'Other': '📦',
  };

  const categoriesHtml = Object.entries(categories).map(([cat, items]) => `
    <div class="shop-category">
      <div class="shop-category-name">${categoryIcons[cat] || '📦'} ${cat} (${items.length})</div>
      <div class="shop-items">
        ${items.map((item, i) => `
          <div class="shop-item" id="si-${i}" onclick="toggleShopItem(this)">
            <div class="shop-item-check">✓</div>
            <div>
              <div class="shop-item-name">${escapeHtml(item.item)}</div>
              <div class="shop-item-qty">${escapeHtml(item.quantity)}</div>
            </div>
          </div>`).join('')}
      </div>
    </div>`).join('');

  const tipsHtml = data.tips && data.tips.length ? `
    <div class="shop-tips">
      <h4>💡 Smart Shopping Tips</h4>
      <ul>${data.tips.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>
    </div>` : '';

  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
      <h3>🛒 Shopping List for ${escapeHtml(data.user_name)} — ${data.total_items} items</h3>
    </div>
    ${categoriesHtml}
    ${tipsHtml}`;
}

function toggleShopItem(el) {
  el.classList.toggle('checked');
}

function printShoppingList() {
  window.print();
}

// ── Dashboard ──────────────────────────────────────────────────────────────────
async function loadDashboard() {
  if (!currentUserId) {
    showAlert('dashboardError', '⚠️ Please save your profile first!', 'alert-error');
    document.getElementById('dashboardError').classList.remove('hidden');
    return;
  }

  showLoading('Loading your nutrition dashboard…');
  document.getElementById('dashboardError').classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/dashboard/${currentUserId}`);
    const data = await res.json();
    if (res.ok) {
      renderDashboard(data);
    } else {
      document.getElementById('dashboardError').textContent = `❌ ${data.detail || 'Error loading dashboard'}`;
      document.getElementById('dashboardError').classList.remove('hidden');
    }
  } catch (err) {
    document.getElementById('dashboardError').textContent = `❌ Network error: ${err.message}`;
    document.getElementById('dashboardError').classList.remove('hidden');
  } finally {
    hideLoading();
  }
}

function renderDashboard(data) {
  const container = document.getElementById('dashboardContainer');
  const macros = data.macros || {};
  const bmi = data.bmi;
  const bmiCategory = bmi ? getBmiCategory(bmi) : null;

  // Macro percentages
  const totalCal = macros.target_calories || 2000;
  const protPct = Math.round((macros.protein_g * 4 / totalCal) * 100);
  const carbPct = Math.round((macros.carbs_g * 4 / totalCal) * 100);
  const fatPct = Math.round((macros.fat_g * 9 / totalCal) * 100);

  // BMI indicator position
  const bmiLeft = bmi ? Math.max(2, Math.min(98, ((bmi - 15) / (40 - 15)) * 100)) : 50;

  const bmiSection = bmi ? `
    <div class="bmi-scale">
      <h3>📏 Body Mass Index (BMI)</h3>
      <div class="bmi-bar">
        <div class="bmi-indicator" style="left:${bmiLeft}%"></div>
      </div>
      <div class="bmi-labels">
        <span>Underweight (&lt;18.5)</span>
        <span>Normal (18.5–24.9)</span>
        <span>Overweight (25–29.9)</span>
        <span>Obese (&gt;30)</span>
      </div>
      <p style="margin-top:12px;font-weight:600;color:var(--primary)">
        Your BMI: ${bmi} — <span style="color:${bmiCategory.color}">${bmiCategory.label}</span>
      </p>
      <p style="font-size:0.82rem;color:var(--text-muted);margin-top:4px">${bmiCategory.advice}</p>
    </div>` : '';

  const infoHtml = `
    <div class="dash-info">
      <div class="dash-info-item"><div class="dash-info-label">Diet Preference</div><div class="dash-info-value">${formatEnum(data.diet_preference || '')}</div></div>
      <div class="dash-info-item"><div class="dash-info-label">Activity Level</div><div class="dash-info-value">${formatEnum(data.activity_level || '')}</div></div>
      <div class="dash-info-item"><div class="dash-info-label">TDEE</div><div class="dash-info-value">${data.tdee_kcal || '—'} kcal/day</div></div>
      <div class="dash-info-item"><div class="dash-info-label">Nutrition Goals</div><div class="dash-info-value">${(data.goals || []).map(formatEnum).join(', ') || '—'}</div></div>
    </div>`;

  container.innerHTML = `
    <h3 style="margin-bottom:16px">Hello, ${escapeHtml(data.user_name || 'User')}! Here's your nutrition snapshot. 👋</h3>
    <div class="dash-grid">
      <div class="dash-card card-cal">
        <div class="dash-value" style="color:#f59e0b">${macros.target_calories || '—'}</div>
        <div class="dash-unit">kcal / day</div>
        <div class="dash-label">Daily Calories</div>
      </div>
      <div class="dash-card card-prot">
        <div class="dash-value" style="color:#3b82f6">${macros.protein_g || '—'}g</div>
        <div class="dash-unit">${protPct}% of calories</div>
        <div class="dash-label">Protein Target</div>
        <div class="dash-macro-bar"><div class="dash-macro-fill" style="width:${protPct}%;background:#3b82f6"></div></div>
      </div>
      <div class="dash-card card-carb">
        <div class="dash-value" style="color:#10b981">${macros.carbs_g || '—'}g</div>
        <div class="dash-unit">${carbPct}% of calories</div>
        <div class="dash-label">Carbs Target</div>
        <div class="dash-macro-bar"><div class="dash-macro-fill" style="width:${carbPct}%;background:#10b981"></div></div>
      </div>
      <div class="dash-card card-fat">
        <div class="dash-value" style="color:#ec4899">${macros.fat_g || '—'}g</div>
        <div class="dash-unit">${fatPct}% of calories</div>
        <div class="dash-label">Fat Target</div>
        <div class="dash-macro-bar"><div class="dash-macro-fill" style="width:${fatPct}%;background:#ec4899"></div></div>
      </div>
      ${bmi ? `<div class="dash-card card-bmi">
        <div class="dash-value" style="color:#8b5cf6">${bmi}</div>
        <div class="dash-unit">${bmiCategory ? bmiCategory.label : ''}</div>
        <div class="dash-label">BMI</div>
      </div>` : ''}
    </div>
    ${bmiSection}
    ${infoHtml}
    <div class="alert" style="background:#fffbeb;border:1px solid #fcd34d;color:#92400e;margin-top:16px;font-size:0.82rem;">⚕️ ${escapeHtml(data.disclaimer || '')}</div>`;
}

function getBmiCategory(bmi) {
  if (bmi < 18.5) return { label: 'Underweight', color: '#3b82f6', advice: 'Consider increasing caloric intake with nutrient-dense foods.' };
  if (bmi < 25) return { label: 'Normal Weight ✅', color: '#10b981', advice: 'You are in a healthy BMI range. Maintain with balanced DIP Diet eating.' };
  if (bmi < 30) return { label: 'Overweight', color: '#f59e0b', advice: 'DIP Diet with mild caloric deficit and regular activity recommended.' };
  return { label: 'Obese', color: '#ef4444', advice: 'Consult a healthcare provider. DIP Diet with medical supervision advised.' };
}

// ── Food Substitutions ─────────────────────────────────────────────────────────
async function getSubstitutions() {
  const food = document.getElementById('subFood').value.trim();
  if (!food) {
    document.getElementById('subError').textContent = '⚠️ Please enter a food item to substitute.';
    document.getElementById('subError').classList.remove('hidden');
    return;
  }
  if (!currentUserId) {
    document.getElementById('subError').textContent = '⚠️ Please save your profile first for personalized substitutions!';
    document.getElementById('subError').classList.remove('hidden');
    return;
  }

  const btn = document.getElementById('subBtnText');
  btn.textContent = '⏳ Finding…';
  showLoading('Finding smart substitutions…');
  document.getElementById('subError').classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/substitute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUserId,
        food_item: food,
        reason: document.getElementById('subReason').value,
      }),
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById('subContainer').innerHTML = `
        <div class="sub-result">
          <h3>🔄 Substitutions for: <em>${escapeHtml(data.original_food)}</em></h3>
          <div class="md-content" style="margin-top:12px">${renderMarkdown(data.explanation)}</div>
          <div class="alert" style="background:#fffbeb;border:1px solid #fcd34d;color:#92400e;margin-top:16px;font-size:0.82rem;">⚕️ ${escapeHtml(data.disclaimer)}</div>
        </div>`;
    } else {
      document.getElementById('subError').textContent = `❌ ${data.detail || 'Error finding substitutions'}`;
      document.getElementById('subError').classList.remove('hidden');
    }
  } catch (err) {
    document.getElementById('subError').textContent = `❌ Network error: ${err.message}`;
    document.getElementById('subError').classList.remove('hidden');
  } finally {
    btn.textContent = '🔄 Find Substitutions';
    hideLoading();
  }
}

// ── Utility Functions ──────────────────────────────────────────────────────────
function showLoading(text = 'Processing…') {
  document.getElementById('loadingText').textContent = text;
  document.getElementById('loadingOverlay').classList.remove('hidden');
}
function hideLoading() {
  document.getElementById('loadingOverlay').classList.add('hidden');
}

function showAlert(id, message, type = 'alert-error') {
  const el = document.getElementById(id);
  el.textContent = message;
  el.className = `alert ${type}`;
  el.classList.remove('hidden');
  setTimeout(() => { if (type === 'alert-success') el.classList.add('hidden'); }, 5000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatEnum(str) {
  if (!str) return '';
  return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Simple markdown renderer for chat messages.
 * Handles bold, italic, headers, lists, and line breaks.
 */
function renderMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  html = html.replace(/_(.+?)_/g, '<em>$1</em>');

  // Code
  html = html.replace(/`(.+?)`/g, '<code>$1</code>');

  // Bullet lists
  html = html.replace(/^• (.+)$/gm, '<li>$1</li>');
  html = html.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`);

  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Paragraphs (double newlines)
  html = html.replace(/\n\n/g, '</p><p>');
  html = html.replace(/\n/g, '<br>');
  html = `<p>${html}</p>`;

  return html;
}
