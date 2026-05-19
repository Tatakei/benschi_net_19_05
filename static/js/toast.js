const toastConfig = {
    duration: 5000,
    colors: {
        success: '#00ff88',
        error: '#ff4444',
        info: '#00f2ff'
    },
    tints: {
        success: 'rgba(0, 255, 136, 0.05)',
        error: 'rgba(255, 68, 68, 0.05)',
        info: 'rgba(0, 242, 255, 0.05)'
    }
};

const style = document.createElement('style');
style.innerHTML = `
    #toast-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .toast-card {
        width: 320px;
        padding: 16px;
        border-radius: 12px;
        background: rgba(15, 17, 26, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
        position: relative;
        overflow: hidden;
        animation: slideIn 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28) forwards;
        box-shadow: 0 10px 30px -5px rgba(0,0,0,0.5);
    }
    .toast-header {
        display: block;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .toast-msg {
        font-size: 13px;
        color: rgba(224, 224, 224, 0.6);
        line-height: 1.4;
    }
    .toast-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        height: 2px; /* Thinner for the glass look */
        width: 100%;
        transform-origin: left;
        opacity: 0.8;
    }
    .toast-card.fade-out {
        animation: fadeOut 0.4s ease forwards;
    }
    @keyframes slideIn {
        from { transform: translateX(100%) scale(0.9); opacity: 0; }
        to { transform: translateX(0) scale(1); opacity: 1; }
    }
    @keyframes fadeOut {
        to { transform: translateX(40px); opacity: 0; }
    }
`;
document.head.appendChild(style);

const container = document.createElement('div');
container.id = 'toast-container';
document.body.appendChild(container);

/**
 * Main function to trigger the Glass toast
 * @param {string} type - 'success', 'error', or 'info'
 * @param {string} message - The text content
 */
function showToast(type, message) {
    const toast = document.createElement('div');
    toast.className = 'toast-card';

    toast.style.borderBottom = `2px solid ${toastConfig.colors[type]}`;
    toast.style.background = `linear-gradient(to bottom, rgba(15, 17, 26, 0.7), ${toastConfig.tints[type]})`;

    toast.innerHTML = `
        <strong class="toast-header" style="color: ${toastConfig.colors[type]}">${type}</strong>
        <p class="toast-msg">${message}</p>
        <div class="toast-progress" style="background: ${toastConfig.colors[type]}"></div>
    `;

    container.appendChild(toast);

    const progressBar = toast.querySelector('.toast-progress');
    progressBar.animate([
        { transform: 'scaleX(1)' },
        { transform: 'scaleX(0)' }
    ], {
        duration: toastConfig.duration,
        easing: 'linear'
    });

    const timer = setTimeout(() => {
        dismiss();
    }, toastConfig.duration);

    const dismiss = () => {
        toast.classList.add('fade-out');
        toast.addEventListener('animationend', () => toast.remove());
    };

    toast.onclick = dismiss;
}