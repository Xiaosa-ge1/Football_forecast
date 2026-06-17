// ===== 绿茵神算 · 全局 JS =====

/** 显示 Toast 通知 */
function showToast(message, type) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/** 格式化日期为 YYYY-MM-DD */
function todayISO() {
  const d = new Date();
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
}

/** 设置 date input 默认值为今天 */
document.addEventListener('DOMContentLoaded', () => {
  const dateInput = document.getElementById('match_date');
  if (dateInput && !dateInput.value) {
    dateInput.value = todayISO();
  }
});
