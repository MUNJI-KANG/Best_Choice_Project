document.addEventListener("DOMContentLoaded", () => {
  const agreeAll = document.getElementById("agreeAll");

  const agreeTerms = document.getElementById("agreeTermsRequired");
  const agreePrivacy = document.getElementById("agreePrivacyRequired");
  const agreeMarketing = document.getElementById("agreeMarketingOptional");

  const btnNext = document.getElementById("termsSubmitButton");
  const btnCancel = document.getElementById("termsCancelButton");

  // ================================
  // 0. 버튼을 disabled 해제 (핵심 포인트)
  // ================================
  btnNext.disabled = false;   // disabled 유지하면 클릭 이벤트 자체가 안 들어감

  // ================================
  // 1. 모두 동의하기
  // ================================
  agreeAll.addEventListener("change", () => {
    const checked = agreeAll.checked;
    agreeTerms.checked = checked;
    agreePrivacy.checked = checked;
    agreeMarketing.checked = checked;
  });

  // ================================
  // 2. 개별 체크 시 모두동의 업데이트
  // ================================
  function updateAgreeAllState() {
    if (agreeTerms.checked && agreePrivacy.checked && agreeMarketing.checked) {
      agreeAll.checked = true;
    } else {
      agreeAll.checked = false;
    }
  }

  [agreeTerms, agreePrivacy, agreeMarketing].forEach((box) => {
    box.addEventListener("change", updateAgreeAllState);
  });

  // ================================
  // 3. 동의하고 진행 버튼 클릭 시 필수 체크 검사
  // ================================
  btnNext.addEventListener("click", (e) => {
    if (!agreeTerms.checked || !agreePrivacy.checked) {
      e.preventDefault();
      alert("필수 약관에 모두 동의해야 진행할 수 있습니다.");
      return;
    }
    else{
        alert("약관에 동의 하셨습니다.");
        // 카카오 회원가입 모드 여부 확인
        const isKakaoSignup = sessionStorage.getItem('kakao_signup_mode') ||
        new URLSearchParams(window.location.search).get('kakao') === 'true';

        if (isKakaoSignup) {
          window.location.href = "/signup/?kakao=true";
        } else {
        window.location.href = "/signup";
        }
    }
  });

  // ================================
  // 4. 동의하지 않음 → 로그인 페이지로 이동
  // ================================
  btnCancel.addEventListener("click", () => {
    window.location.href = "/login";
  });
});
