// DOM 로드 후 실행
document.addEventListener("DOMContentLoaded", () => {
    const btn_edit = document.querySelector(".btn-edit");
    const btn_password = document.querySelector(".btn-password");
    const btn_withdraw = document.querySelector(".btn-withdraw");


    // 1) 정보 수정 클릭
    btn_edit.addEventListener("click", function() {
        handle_edit_profile();
    });
    
    // 2) 비밀번호 변경 클릭
    btn_password.addEventListener("click", function() {
        handle_password_change();
    });
    
    // 3) 회원탈퇴 클릭
    btn_withdraw.addEventListener("click", function() {
        handle_withdraw();
    });

    // 탈퇴 모달 관련 요소
    const withdrawModal = document.getElementById("withdrawModal");
    const withdrawStep1 = document.getElementById("withdrawStep1");
    const withdrawStep2 = document.getElementById("withdrawStep2");
    const cancelWithdrawBtn = document.getElementById("cancelWithdraw");
    const nextToPasswordBtn = document.getElementById("nextToPassword");
    const backToReasonBtn = document.getElementById("backToReason");
    const confirmWithdrawBtn = document.getElementById("confirmWithdraw");
    const reasonRadios = document.querySelectorAll('input[name="delete_reason"]');
    const otherReasonBox = document.getElementById("otherReasonBox");
    const otherReasonText = document.getElementById("otherReasonText");
    const confirmPasswordInput = document.getElementById("confirmPassword");
    const passwordError = document.getElementById("passwordError");

    // 카카오 사용자 여부 확인 (user_id가 'kakao_'로 시작하는지 확인)
    // 세션에서 user_id를 가져올 수 없으므로, 페이지에서 전달받거나 직접 확인
    // 여기서는 간단히 user_id를 확인하는 방법 사용
    function isKakaoUser() {
        // user_id를 확인할 수 있는 방법이 필요합니다
        // 예: HTML에서 data 속성으로 전달하거나, 세션 정보를 JavaScript로 전달
        // 임시로 user_id를 확인하는 방법 사용
        const userInfo = document.querySelector('[data-user-id]');
        if (userInfo) {
            const userId = userInfo.getAttribute('data-user-id');
            return userId && userId.startsWith('kakao_');
        }
        return false;
    }

    // 라디오 버튼 변경 시 기타 입력창 표시/숨김
    reasonRadios.forEach(radio => {
        radio.addEventListener("change", function() {
            if (this.value === '6') {
                otherReasonBox.style.display = 'block';
                otherReasonText.required = true;
            } else {
                otherReasonBox.style.display = 'none';
                otherReasonText.required = false;
                otherReasonText.value = '';
            }
        });
    });

    // 취소 버튼
    cancelWithdrawBtn.addEventListener("click", function() {
        closeWithdrawModal();
    });

    // 다음 버튼 (Step 1 → Step 2 또는 바로 제출)
    nextToPasswordBtn.addEventListener("click", function() {
        const selectedReason = document.querySelector('input[name="delete_reason"]:checked');
        
        if (!selectedReason) {
            alert('탈퇴 사유를 선택해주세요.');
            return;
        }

        // 6번(기타) 선택 시 입력값 확인
        if (selectedReason.value === '6') {
            const otherText = otherReasonText.value.trim();
            if (!otherText) {
                alert('기타 사유를 입력해주세요.');
                return;
            }
            // "6:직접 입력한 내용" 형태로 저장
            document.getElementById("delete_reason_input").value = '6:' + otherText;
        } else {
            // 1~5번은 번호만 전송 (서버에서 내용으로 변환)
            document.getElementById("delete_reason_input").value = selectedReason.value;
        }

        // 카카오 사용자인 경우 비밀번호 확인 단계 건너뛰고 바로 제출
        if (isKakaoUser()) {
            const ok = confirm('정말 회원 탈퇴를 진행하시겠습니까?');
            if (ok) {
                document.getElementById("withdrawForm").submit();
            }
        } else {
            // 일반 사용자는 Step 2로 이동
            withdrawStep1.style.display = 'none';
            withdrawStep2.style.display = 'block';
            confirmPasswordInput.focus();
        }
    });

    // 이전 버튼 (Step 2 → Step 1)
    backToReasonBtn.addEventListener("click", function() {
        withdrawStep2.style.display = 'none';
        withdrawStep1.style.display = 'block';
        confirmPasswordInput.value = '';
        passwordError.style.display = 'none';
    });

    // 탈퇴 확인 버튼 (비밀번호 확인 후 최종 제출)
    confirmWithdrawBtn.addEventListener("click", function() {
        const password = confirmPasswordInput.value.trim();
        
        if (!password) {
            passwordError.textContent = '비밀번호를 입력해주세요.';
            passwordError.style.display = 'block';
            return;
        }

        // 비밀번호를 hidden input에 저장
        document.getElementById("password_input").value = password;

        // 최종 확인
        const ok = confirm('정말 회원 탈퇴를 진행하시겠습니까?');
        if (ok) {
            document.getElementById("withdrawForm").submit();
        }
    });

    // 모달 외부 클릭 시 닫기
    withdrawModal.addEventListener("click", function(e) {
        if (e.target.classList.contains('withdraw-modal-backdrop') || e.target === withdrawModal) {
            closeWithdrawModal();
        }
    });

    // ESC 키로 모달 닫기
    document.addEventListener("keydown", function(e) {
        if (e.key === 'Escape' && withdrawModal.classList.contains('show')) {
            closeWithdrawModal();
        }
    });

    // 모달 닫기 함수
    function closeWithdrawModal() {
        withdrawModal.classList.remove('show');
        // 폼 초기화
        document.getElementById("withdrawReasonForm").reset();
        otherReasonBox.style.display = 'none';
        otherReasonText.value = '';
        confirmPasswordInput.value = '';
        passwordError.style.display = 'none';
        // Step 1로 리셋
        withdrawStep2.style.display = 'none';
        withdrawStep1.style.display = 'block';
    }
});

// -----------------------------
// 함수 분리
// -----------------------------

// 정보 수정 버튼 클릭 시
function handle_edit_profile() {
    window.location.href = typeof MEMBER_EDIT_URL !== 'undefined' ? MEMBER_EDIT_URL : "/member/edit/";
}

// 비밀번호 변경 버튼 클릭 시
function handle_password_change() {
    window.location.href = typeof MEMBER_PASSWORD_URL !== 'undefined' ? MEMBER_PASSWORD_URL : "/member/password/";
}

// 회원 탈퇴 버튼 클릭 시
function handle_withdraw(){
    const withdrawModal = document.getElementById("withdrawModal");
    withdrawModal.classList.add('show');
    // Step 1로 리셋
    document.getElementById("withdrawStep1").style.display = 'block';
    document.getElementById("withdrawStep2").style.display = 'none';
}