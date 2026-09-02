// DMF Notification System Client App

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    loadWatchlist();
    loadLogs();
    loadSettings();

    // Event Listeners
    document.getElementById('btnOpenSearch').addEventListener('click', () => openModal('searchModal'));
    document.getElementById('btnCloseSearch').addEventListener('click', () => closeModal('searchModal'));
    
    document.getElementById('btnOpenSettings').addEventListener('click', () => openModal('settingsModal'));
    document.getElementById('btnCloseSettings').addEventListener('click', () => closeModal('settingsModal'));

    document.getElementById('searchForm').addEventListener('submit', handleSearchSubmit);
    document.getElementById('btnCheckNow').addEventListener('click', handleCheckNow);

    document.getElementById('settingsForm').addEventListener('submit', handleSettingsSubmit);
    document.getElementById('btnTestNotify').addEventListener('click', handleTestNotify);
}

// Modal Helpers
function openModal(id) {
    document.getElementById(id).classList.add('active');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
}

// Toast Helper
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Fetch Watchlist
async function loadWatchlist() {
    try {
        const res = await fetch('/api/watchlist');
        const data = await res.json();

        const container = document.getElementById('watchlistContainer');
        document.getElementById('statTotalItems').innerText = data.length;
        document.getElementById('watchCountBadge').innerText = `${data.length}개 품목`;

        if (!data || data.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <p>현재 모니터링 중인 원료의약품이 없습니다.</p>
                    <button class="btn btn-sm btn-primary" onclick="openModal('searchModal')">관심 DMF 검색 및 추가</button>
                </div>
            `;
            return;
        }

        container.innerHTML = data.map(item => `
            <div class="watch-card">
                <div class="watch-card-header">
                    <div class="watch-title">
                        <i class="fa-solid fa-capsules" style="color: var(--accent-blue);"></i>
                        ${escapeHtml(item.ingredient)}
                    </div>
                    <span class="badge-doc">${escapeHtml(item.doc_no || 'v0.0.0')}</span>
                </div>

                <div class="watch-details-grid">
                    <div class="detail-item"><strong>등록번호:</strong> ${escapeHtml(item.reg_no)}</div>
                    <div class="detail-item"><strong>신청인:</strong> ${escapeHtml(item.applicant)}</div>
                    <div class="detail-item"><strong>제조소:</strong> ${escapeHtml(item.manufacturer)}</div>
                    <div class="detail-item"><strong>최초등록:</strong> ${escapeHtml(item.first_reg_date || '-')}</div>
                </div>

                <div class="watch-card-footer">
                    <span>최종변경: ${escapeHtml(item.last_change_date || '변경이력없음')}</span>
                    <button class="btn btn-sm btn-danger" onclick="deleteWatchItem('${escapeHtml(item.reg_no)}')">
                        <i class="fa-solid fa-trash"></i> 삭제
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Failed to load watchlist:', err);
    }
}

// Fetch Change Logs Timeline
async function loadLogs() {
    try {
        const res = await fetch('/api/logs');
        const logs = await res.json();

        const container = document.getElementById('timelineContainer');
        document.getElementById('statTotalChanges').innerText = logs.length;

        if (logs.length > 0) {
            const latestTime = new Date(logs[0].created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            document.getElementById('statLastSync').innerText = latestTime;
        }

        if (!logs || logs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-inbox"></i>
                    <p>아직 변경 이력이 기록되지 않았습니다.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = logs.map(log => `
            <div class="timeline-item">
                <div class="timeline-header">
                    <span><i class="fa-solid fa-clock"></i> ${formatDate(log.created_at)}</span>
                    <span class="badge badge-info">문서번호 업데이트</span>
                </div>
                <div class="timeline-title">${escapeHtml(log.ingredient)} (${escapeHtml(log.reg_no)})</div>
                <div style="font-size: 12px; color: var(--text-secondary);">${escapeHtml(log.applicant)}</div>

                <div class="diff-box">
                    <span class="old-ver">${escapeHtml(log.old_doc_no || 'v0.0.0')}</span>
                    <i class="fa-solid fa-arrow-right diff-arrow"></i>
                    <span class="new-ver">${escapeHtml(log.new_doc_no)}</span>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error('Failed to load logs:', err);
    }
}

// Live Search Submission
async function handleSearchSubmit(e) {
    e.preventDefault();
    const ingredient = document.getElementById('inputIngredient').value.trim();
    const reg_no = document.getElementById('inputRegNo').value.trim();
    const applicant = document.getElementById('inputApplicant').value.trim();

    const spinner = document.getElementById('searchLoading');
    const resultsContainer = document.getElementById('searchResults');

    spinner.classList.remove('hidden');
    resultsContainer.innerHTML = '';

    try {
        const queryParams = new URLSearchParams({ ingredient, reg_no, applicant, limit: 10 });
        const res = await fetch(`/api/search?${queryParams}`);
        const data = await res.json();

        spinner.classList.add('hidden');

        if (!data.success || !data.items || data.items.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <p>의약품안전나라 검색 결과가 없습니다.</p>
                </div>
            `;
            return;
        }

        resultsContainer.innerHTML = data.items.map(item => `
            <div class="watch-card" style="margin-bottom: 12px;">
                <div class="watch-card-header">
                    <div class="watch-title">
                        <i class="fa-solid fa-pills" style="color: var(--accent-emerald);"></i>
                        ${escapeHtml(item.ingredient)}
                    </div>
                    <span class="badge-doc">${escapeHtml(item.doc_no || 'v0.0.0')}</span>
                </div>
                <div class="watch-details-grid">
                    <div class="detail-item"><strong>등록번호:</strong> ${escapeHtml(item.reg_no)}</div>
                    <div class="detail-item"><strong>신청인:</strong> ${escapeHtml(item.applicant)}</div>
                    <div class="detail-item"><strong>제조소:</strong> ${escapeHtml(item.manufacturer)}</div>
                </div>
                <div class="watch-card-footer">
                    <span>최초등록: ${escapeHtml(item.first_reg_date || '-')}</span>
                    <button class="btn btn-sm btn-primary" onclick="addWatchItem(${escapeJsonAttr(item)})">
                        <i class="fa-solid fa-plus"></i> 모니터링 등록
                    </button>
                </div>
            </div>
        `).join('');

    } catch (err) {
        spinner.classList.add('hidden');
        showToast('검색 실패: 네트워크 상태를 확인하세요.', 'error');
    }
}

// Add Item to Watchlist
async function addWatchItem(item) {
    try {
        const res = await fetch('/api/watchlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(item)
        });
        const data = await res.json();
        if (data.success) {
            showToast(`'${item.ingredient}' 품목이 관심 목록에 등록되었습니다.`);
            closeModal('searchModal');
            loadWatchlist();
        } else {
            showToast(data.message || '등록 실패', 'error');
        }
    } catch (err) {
        showToast('등록 중 오류 발생', 'error');
    }
}

// Delete Item from Watchlist
async function deleteWatchItem(regNo) {
    if (!confirm(`등록번호 '${regNo}' 모니터링을 삭제하시겠습니까?`)) return;

    try {
        const res = await fetch(`/api/watchlist/${encodeURIComponent(regNo)}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            showToast('모니터링 목록에서 삭제되었습니다.');
            loadWatchlist();
        }
    } catch (err) {
        showToast('삭제 실패', 'error');
    }
}

// Trigger Manual Check Now
async function handleCheckNow() {
    const btn = document.getElementById('btnCheckNow');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> 확인 중...`;
    btn.disabled = true;

    try {
        const res = await fetch('/api/check-now', { method: 'POST' });
        const data = await res.json();

        btn.innerHTML = originalText;
        btn.disabled = false;

        if (data.changes_detected > 0) {
            showToast(`⚡ ${data.changes_detected}개 품목의 문서번호 변경이 감지되었습니다!`);
            loadWatchlist();
            loadLogs();
        } else {
            showToast('모든 관심 품목의 문서번호가 변경 없이 최신 상태입니다.');
        }

    } catch (err) {
        btn.innerHTML = originalText;
        btn.disabled = false;
        showToast('동기화 실패', 'error');
    }
}

// Load Settings
async function loadSettings() {
    try {
        const res = await fetch('/api/settings');
        const s = await res.json();

        document.getElementById('emailEnabled').checked = s.email_enabled === 'true';
        document.getElementById('emailRecipient').value = s.email_recipient || '';
        document.getElementById('smtpServer').value = s.smtp_server || '';
        document.getElementById('smtpPort').value = s.smtp_port || '587';
        document.getElementById('smtpUser').value = s.smtp_user || '';
        document.getElementById('smtpPassword').value = s.smtp_password || '';

        document.getElementById('smsEnabled').checked = s.sms_enabled === 'true';
        document.getElementById('smsPhone').value = s.sms_phone || '';
        document.getElementById('checkInterval').value = s.check_interval_minutes || '60';

    } catch (err) {
        console.error('Failed to load settings:', err);
    }
}

// Save Settings
async function handleSettingsSubmit(e) {
    e.preventDefault();
    const payload = {
        email_enabled: document.getElementById('emailEnabled').checked ? 'true' : 'false',
        email_recipient: document.getElementById('emailRecipient').value.trim(),
        smtp_server: document.getElementById('smtpServer').value.trim(),
        smtp_port: document.getElementById('smtpPort').value.trim(),
        smtp_user: document.getElementById('smtpUser').value.trim(),
        smtp_password: document.getElementById('smtpPassword').value.trim(),
        sms_enabled: document.getElementById('smsEnabled').checked ? 'true' : 'false',
        sms_phone: document.getElementById('smsPhone').value.trim(),
        check_interval_minutes: document.getElementById('checkInterval').value.trim()
    };

    try {
        const res = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast('알림 설정을 성공적으로 저장했습니다.');
            closeModal('settingsModal');
        }
    } catch (err) {
        showToast('설정 저장 실패', 'error');
    }
}

// Test Notification Trigger
async function handleTestNotify() {
    try {
        const res = await fetch('/api/test-notify', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast('테스트 알림이 발송되었습니다! (로그 및 이메일/SMS 확인)');
        }
    } catch (err) {
        showToast('테스트 발송 실패', 'error');
    }
}

// Helpers
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, m => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
    }[m]));
}

function escapeJsonAttr(obj) {
    return escapeHtml(JSON.stringify(obj));
}

function formatDate(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    return d.toLocaleString('ko-KR');
}
