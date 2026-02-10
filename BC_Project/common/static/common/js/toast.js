/**
 * 전역 Toast 알림 함수
 * @param {string} message - 표시할 메시지
 * @param {string} type - 알림 타입 ('success', 'error', 'info', 'warning')
 */
function showToast(message, type = "success") {
    const existingToast = document.getElementById("toast");
    if (existingToast) existingToast.remove();

    const toast = document.createElement("div");
    toast.id = "toast";
    toast.className = `toast toast-${type}`;

    // 타입별 아이콘 설정
    let icon = "✓";
    if (type === "error") icon = "✕";
    else if (type === "info") icon = "ℹ";
    else if (type === "warning") icon = "⚠";

    toast.innerHTML = `
        <div class="toast-content">
            <span class="toast-icon">${icon}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;

    document.body.appendChild(toast);

    // 애니메이션 표시
    setTimeout(() => toast.classList.add("show"), 10);
    
    // 5초 후 자동 사라짐
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

/**
 * Django messages를 Toast로 자동 변환
 * 페이지 로드 시 Django messages를 감지하여 Toast로 표시
 */
(function() {
    // 이미 실행되었는지 체크 (중복 실행 방지)
    if (window.toastInitialized) return;
    window.toastInitialized = true;

    document.addEventListener("DOMContentLoaded", function() {
        let toastIndex = 0;
        
        // 이미 처리된 메시지를 추적하기 위한 Set (중복 방지)
        const processedMessages = new Set();
        
        // message-area 내부의 alert만 처리 (더 정확한 선택)
        const messageArea = document.querySelector(".message-area");
        if (!messageArea) return;
        
        const allAlerts = messageArea.querySelectorAll(".alert, [class*='alert-']");
        
        allAlerts.forEach(function(alert) {
            // 이미 숨겨진 것은 건너뛰기
            if (alert.style.display === "none") return;
            
            // 이미 처리된 메시지인지 확인 (data-toast-processed 속성 사용)
            if (alert.hasAttribute("data-toast-processed")) return;
            
            const message = alert.textContent.trim();
            if (!message) return;
            
            // 메시지 내용으로 중복 체크 (동일한 메시지와 타입 조합)
            let type = "info";
            
            // 클래스에서 타입 추출
            if (alert.classList.contains("alert-success") || alert.className.includes("alert-success")) {
                type = "success";
            } else if (alert.classList.contains("alert-error") || alert.className.includes("alert-error")) {
                type = "error";
            } else if (alert.classList.contains("alert-warning") || alert.className.includes("alert-warning")) {
                type = "warning";
            } else if (alert.classList.contains("alert-info") || alert.className.includes("alert-info")) {
                type = "info";
            } else {
                // 클래스명에서 타입 추출 시도
                const classMatch = alert.className.match(/alert-(\w+)/);
                if (classMatch) {
                    type = classMatch[1];
                }
            }
            
            // 메시지 키 생성 (메시지 내용 + 타입)
            const messageKey = message + "|" + type;
            if (processedMessages.has(messageKey)) {
                alert.style.display = "none";
                return;
            }
            processedMessages.add(messageKey);
            
            // 처리됨 표시
            alert.setAttribute("data-toast-processed", "true");
            
            // Toast 표시 (여러 개일 경우 순차적으로, 약간의 지연 추가)
            setTimeout(function() {
                showToast(message, type);
            }, 100 + toastIndex * 200);
            
            toastIndex++;
            
            // 원본 메시지 숨기기
            alert.style.display = "none";
        });
        
        // 모든 메시지 처리 후 message-area 숨기기 (타이밍 개선)
        if (allAlerts.length > 0) {
            setTimeout(() => {
                const remainingAlerts = messageArea.querySelectorAll(".alert:not([style*='display: none'])");
                if (remainingAlerts.length === 0) {
                    messageArea.style.display = "none";
                }
            }, 100 + toastIndex * 200);
        }
    });
})();

