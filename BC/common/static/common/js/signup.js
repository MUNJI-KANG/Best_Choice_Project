document.addEventListener('DOMContentLoaded', function () {
  function showMsg(id, message, success = false) {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = message;
    el.className = success ? "msg-area msg-success" : "msg-area msg-error";
  }

  const usernameRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$/;
  const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=]).{8,}$/;
  const phoneRegex = /^\d{3}-\d{4}-\d{4}$/;

  const signupForm = document.querySelector(".register-form");

  const usernameInput = document.getElementById('username');
  const nicknameInput = document.getElementById('nickname');
  const phoneInput = document.querySelector('input[name="phone"]');

  const pw = document.getElementById("password");
  const pw2 = document.getElementById("password2");

  const usernameCheckBtn = document.getElementById('usernameCheckBtn');
  const nicknameCheckBtn = document.getElementById('nicknameCheckBtn');
  const phoneCheckBtn = document.getElementById('phoneCheckBtn');

  const state = {
    usernameAvailable: false,
    nicknameAvailable: false,
    phoneAvailable: false,
    pwValid: false,
    pwMatch: false
  };
  
  /* ---------------- 주소 검색 ---------------- */
const addressSearchBtn = document.getElementById("addressSearchBtn");
const addressInput = document.getElementById("address");

if (addressSearchBtn && addressInput) {
  addressSearchBtn.addEventListener("click", function () {
    new daum.Postcode({
      oncomplete: function (data) {
        // 도로명주소 또는 지번주소 선택
        let addr = '';
        if (data.userSelectedType === 'R') {
          // 사용자가 도로명 주소를 선택했을 경우
          addr = data.roadAddress;
        } else {
          // 사용자가 지번 주소를 선택했을 경우
          addr = data.jibunAddress;
        }
        
        addressInput.value = addr;
        
        // 주소 데이터를 hidden input에 저장 (서버에서 파싱용)
        const addrDataInput = document.getElementById("address_data");
        if (!addrDataInput) {
          // hidden input이 없으면 생성
          const hiddenInput = document.createElement('input');
          hiddenInput.type = 'hidden';
          hiddenInput.id = 'address_data';
          hiddenInput.name = 'address_data';
          addressInput.parentElement.appendChild(hiddenInput);
        }
        document.getElementById("address_data").value = JSON.stringify({
          sido: data.sido,
          sigungu: data.sigungu,
          roadAddress: data.roadAddress,
          jibunAddress: data.jibunAddress,
          userSelectedType: data.userSelectedType
        });
        
        document.getElementById("address_detail").focus();
      }
    }).open();
  });
}

  if (usernameCheckBtn) {
    usernameCheckBtn.addEventListener('click', function () {
    const username = usernameInput.value.trim();

    if (!usernameRegex.test(username)) {
      showMsg("username_msg", "아이디는 6자 이상, 영문+숫자 조합이어야 합니다.");
      state.usernameAvailable = false;
      return;
    }

    fetch(`/check/userid?username=${username}`)
      .then(res => res.json())
      .then(data => {
        if (data.exists) {
          showMsg("username_msg", "이미 사용 중인 아이디입니다.");
          state.usernameAvailable = false;
        } else {
          showMsg("username_msg", "사용 가능한 아이디입니다.", true);
          state.usernameAvailable = true;
        }
      });
    });
  }

  if (nicknameCheckBtn) {
    nicknameCheckBtn.addEventListener('click', function () {
      const nickname = nicknameInput.value.trim();

      if (!nickname) {
        showMsg("nickname_msg", "닉네임을 입력해주세요.");
        state.nicknameAvailable = false;
        return;
      }

      fetch(`/check/nickname?nickname=${nickname}`)
        .then(res => res.json())
        .then(data => {
          if (data.exists) {
            showMsg("nickname_msg", "이미 사용 중인 닉네임입니다.");
            state.nicknameAvailable = false;
          } else {
            showMsg("nickname_msg", "사용 가능한 닉네임입니다.", true);
            state.nicknameAvailable = true;
          }
        });
    });
  }

  if (phoneCheckBtn) {
    phoneCheckBtn.addEventListener('click', function () {
      const phone = phoneInput.value.trim();

      if (!phoneRegex.test(phone)) {
        showMsg("phone_msg", "전화번호는 010-0000-0000 형식으로 입력해주세요.");
        state.phoneAvailable = false;
        return;
      }

      fetch(`/check/phone?phone=${phone}`)
        .then(res => res.json())
        .then(data => {
          if (data.exists) {
            showMsg("phone_msg", "이미 등록된 전화번호입니다.");
            state.phoneAvailable = false;
          } else {
            showMsg("phone_msg", "사용 가능한 전화번호입니다.", true);
            state.phoneAvailable = true;
          }
        });
    });
  }

  function checkPw() {
    const val1 = pw.value;
    const val2 = pw2.value;

    if (!passwordRegex.test(val1)) {
      showMsg("pw_msg", "비밀번호는 8자 이상, 대문자/소문자/숫자/특수문자 포함해야 합니다.");
      state.pwValid = false;
      return;
    }

    if (val1 && val2 && val1 === val2) {
      showMsg("pw_msg", "비밀번호가 일치합니다.", true);
      state.pwValid = true;
      state.pwMatch = true;
    } else if (val2.length > 0 && val1 !== val2) {
      showMsg("pw_msg", "비밀번호가 일치하지 않습니다.");
      state.pwValid = false;
      state.pwMatch = false;
    }
  }

  if (pw && pw2) {
    pw.addEventListener("input", checkPw);
    pw2.addEventListener("input", checkPw);
  }

  if (signupForm) {
    signupForm.addEventListener("submit", function (e) {
      // 카카오 회원가입 모드인지 확인
      const isKakaoSignup = document.querySelector('input[name="kakao_signup"]') !== null;
      
      const requiredFields = signupForm.querySelectorAll("input[required]");
      for (let field of requiredFields) {
        if (!field.value.trim()) {
          e.preventDefault();
          alert("모든 항목을 입력해주세요.");
          field.focus();
          return;
        }
      }

      // 카카오 회원가입 모드가 아닐 때만 아이디 형식 및 중복 확인 체크
      if (!isKakaoSignup) {
        if (usernameInput && !usernameRegex.test(usernameInput.value.trim())) {
          e.preventDefault();
          alert("아이디 형식을 확인해주세요.");
          usernameInput.focus();
          return;
        }
        if (!state.usernameAvailable) {
          e.preventDefault();
          alert("아이디 중복확인을 완료해주세요.");
          return;
        }
      }

      if (pw && (!state.pwValid || !state.pwMatch)) {
        e.preventDefault();
        alert("비밀번호를 다시 확인해주세요.");
        pw.focus();
        return;
      }

      if (phoneInput && !phoneRegex.test(phoneInput.value.trim())) {
        e.preventDefault();
        alert("전화번호 형식을 확인해주세요.");
        phoneInput.focus();
        return;
      }
      if (!state.phoneAvailable) {
        e.preventDefault();
        alert("전화번호 중복확인을 완료해주세요.");
        return;
      }
    });
  }
});
