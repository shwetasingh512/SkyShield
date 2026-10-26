/**
 * SkyShield: Aviation Safety & Incident Reporting System
 * Frontend UI Scripts & Client Interactivity
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Mobile Sidebar Toggle
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const appSidebar = document.getElementById('appSidebar');

    if (sidebarToggleBtn && appSidebar) {
        let backdrop = null;

        sidebarToggleBtn.addEventListener('click', function () {
            appSidebar.classList.toggle('show');

            if (appSidebar.classList.contains('show')) {
                backdrop = document.createElement('div');
                backdrop.className = 'sidebar-backdrop';
                document.body.appendChild(backdrop);

                backdrop.addEventListener('click', function () {
                    appSidebar.classList.remove('show');
                    if (backdrop) backdrop.remove();
                });
            } else if (backdrop) {
                backdrop.remove();
            }
        });
    }

    // 2. Real-Time Risk Score Calculator (Form Helpers)
    const likelihoodSelect = document.getElementById('id_likelihood');
    const severitySelect = document.getElementById('id_severity');
    const liveScoreBadge = document.getElementById('liveRiskScoreBadge');
    const liveScoreText = document.getElementById('liveRiskScoreText');

    function updateLiveRiskPreview() {
        if (!likelihoodSelect || !severitySelect || !liveScoreBadge) return;

        const lVal = parseInt(likelihoodSelect.value) || 1;
        const sVal = parseInt(severitySelect.value) || 1;
        const score = lVal * sVal;

        let level = 'LOW';
        let bgClass = 'bg-success';

        if (score <= 4) {
            level = 'LOW';
            bgClass = 'bg-success';
        } else if (score <= 9) {
            level = 'MODERATE';
            bgClass = 'bg-warning text-dark';
        } else if (score <= 15) {
            level = 'HIGH';
            bgClass = 'bg-orange text-white';
        } else {
            level = 'CRITICAL';
            bgClass = 'bg-danger text-white';
        }

        liveScoreBadge.className = `badge ${bgClass} px-3 py-2 fs-6`;
        if (liveScoreText) {
            liveScoreText.textContent = `${score} / 25 (${level})`;
        } else {
            liveScoreBadge.textContent = `${score} (${level})`;
        }
    }

    if (likelihoodSelect && severitySelect && liveScoreBadge) {
        likelihoodSelect.addEventListener('change', updateLiveRiskPreview);
        severitySelect.addEventListener('change', updateLiveRiskPreview);
        updateLiveRiskPreview();
    }

    // 3. Destructive Action Confirmation
    const confirmButtons = document.querySelectorAll('[data-confirm-message]');
    confirmButtons.forEach(btn => {
        btn.addEventListener('click', function (e) {
            const message = this.getAttribute('data-confirm-message') || 'Are you sure you wish to perform this action?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});
