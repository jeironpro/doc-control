// Alternar apertura/cierre del sidebar en móvil
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const backdrop = document.getElementById('sidebarBackdrop');

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
        backdrop.classList.toggle('open');
    });
}

if (backdrop) {
    backdrop.addEventListener('click', () => {
        sidebar.classList.remove('open');
        backdrop.classList.remove('open');
    });
}

// Cerrar sidebar al navegar (tras intercambio HTMX) en móvil
document.addEventListener('htmx:afterSwap', () => {
    if (window.innerWidth <= 768) {
        sidebar.classList.remove('open');
        backdrop.classList.remove('open');
    }
});

// Copia al portapapeles (CSV o expediente) y muestra "Copiado"
document.body.addEventListener('click', (e) => {
    const btn = e.target.closest('.doc-copy-btn');
    if (!btn) return;
    const text = btn.dataset.token || btn.dataset.exp;
    if (!text) return;

    const parent = btn.closest('.doc-vault-code, .doc-expediente-row');
    const valueSpan = parent.querySelector('.doc-vault-value, .doc-expediente-value') || parent.querySelector('.doc-expediente');
    const original = valueSpan.textContent;

    navigator.clipboard.writeText(text).catch(() => {});
    valueSpan.textContent = 'Copiado';
    parent.classList.add('copiado');
    btn.style.display = 'none';

    setTimeout(() => {
        valueSpan.textContent = original;
        parent.classList.remove('copiado');
        btn.style.display = '';
    }, 1800);
});

// Alternar entre input datetime-local y date
document.body.addEventListener('click', (e) => {
    const btn = e.target.closest('.dt-btn');
    if (!btn) return;
    const container = btn.closest('.input-group');
    container.querySelectorAll('.dt-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const input = container.querySelector('input');
    input.type = btn.dataset.mode;
});

// Cierre de modal: clic en fondo, botón ×, botón Cancelar
document.body.addEventListener('click', (e) => {
    const backdrop = e.target.closest('.modal-backdrop');
    if (backdrop) {
        if (e.target === backdrop || e.target.closest('.modal-close') || e.target.closest('.modal-close-btn')) {
            backdrop.remove();
            return;
        }
    }
});

// Cerrar modal con tecla Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) backdrop.remove();
    }
});
