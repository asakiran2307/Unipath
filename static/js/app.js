/* Opportunity Pulse — Main JS */

// ── Toast Helper ──────────────────────────────────────────────────────────────
window.showToast = function(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = 'toast';
  el.textContent = msg;
  document.body.appendChild(el);
  requestAnimationFrame(() => { requestAnimationFrame(() => el.classList.add('show')); });
  setTimeout(() => {
    el.classList.remove('show');
    setTimeout(() => el.remove(), 400);
  }, 2800);
};

// ── Smooth page transitions ───────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.body.style.opacity = '0';
  document.body.style.transition = 'opacity .3s ease';
  requestAnimationFrame(() => { document.body.style.opacity = '1'; });
});
document.querySelectorAll('a.card-apply-btn').forEach(a => {
  a.addEventListener('click', () => showToast('Opening application page…'));
});

// ── Auto-hide flash messages ──────────────────────────────────────────────────
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .5s, transform .5s';
    el.style.opacity = '0';
    el.style.transform = 'translateX(100%)';
    setTimeout(() => el.remove(), 500);
  }, 5000);
  el.querySelector('.flash-close')?.addEventListener('click', () => el.remove());
});
