// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".password-form");
    
    if (form) {
        // 폼 제출 이벤트 처리
        form.addEventListener("submit", function(e) {
            e.preventDefault();
            handlePasswordChange(this);
        });
    }
});

// -----------------------------
// 비밀번호 변경 처리 함수 (AJAX)
// -----------------------------

function handlePasswordChange(form) {
    const submitBtn = form.querySelector("button[type='submit']");
    const originalText = submitBtn.textContent;
    
    // 입력값 검증
    const currentPw = form.querySelector('input[name="current_pw"]').value;
    const newPw = form.querySelector('input[name="new_pw"]').value;
    const newPw2 = form.querySelector('input[name="new_pw2"]').value;
    
    if (!currentPw || !newPw || !newPw2) {
        showToast('모든 필드를 입력해주세요.', 'error');
        return;
    }
    
    if (newPw !== newPw2) {
        showToast('새 비밀번호와 확인 비밀번호가 일치하지 않습니다.', 'error');
        return;
    }
    
    // 버튼 비활성화 및 로딩 상태
    submitBtn.disabled = true;
    submitBtn.textContent = "변경 중...";
    
    // FormData 생성
    const formData = new FormData(form);
    
    // CSRF 토큰 가져오기
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // AJAX 요청
    const passwordUrl = typeof MEMBER_PASSWORD_URL !== 'undefined' ? MEMBER_PASSWORD_URL : '/member/password/';
    fetch(passwordUrl, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrftoken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // 성공 토스트 메시지 표시
            showToast(data.message, 'success');
            
            // 폼 초기화
            form.reset();
            
            // 2초 후 내 정보 페이지로 이동
            setTimeout(function() {
                const infoUrl = typeof MEMBER_INFO_URL !== 'undefined' ? MEMBER_INFO_URL : '/member/info/';
                window.location.href = infoUrl;
            }, 2000);
        } else {
            // 실패 토스트 메시지 표시
            showToast(data.message, 'error');
            
            // 버튼 복원
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('비밀번호 변경 중 오류가 발생했습니다.', 'error');
        
        // 버튼 복원
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    });
}