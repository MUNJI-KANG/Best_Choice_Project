document.addEventListener("DOMContentLoaded", () => {
    console.log("info_edit.js 로드됨");
    const form = document.querySelector(".mypage-form");

    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();
            e.stopPropagation();
            handle_edit_profile(this);
            return false;
        });
    }

    const addressSearchBtn = document.getElementById("addressSearchBtn");
    const addressInput = document.getElementById("address");

    if (addressSearchBtn && addressInput) {
        addressSearchBtn.addEventListener("click", function () {
            new daum.Postcode({
                oncomplete: function (data) {
                    let addr =
                        data.userSelectedType === "R"
                            ? data.roadAddress
                            : data.jibunAddress;

                    addressInput.value = addr;

                    let addrDataInput = document.getElementById("address_data");
                    if (!addrDataInput) {
                        addrDataInput = document.createElement("input");
                        addrDataInput.type = "hidden";
                        addrDataInput.id = "address_data";
                        addrDataInput.name = "address_data";
                        form.appendChild(addrDataInput);
                    }

                    addrDataInput.value = JSON.stringify({
                        sido: data.sido,
                        sigungu: data.sigungu,
                        roadAddress: data.roadAddress,
                        jibunAddress: data.jibunAddress,
                        userSelectedType: data.userSelectedType,
                    });

                    updateAddressDisplay(data);

                    const addressDetailInput = document.getElementById(
                        "address_detail"
                    );
                    if (addressDetailInput) addressDetailInput.focus();
                },
            }).open();
        });
    }

    // -----------------------------
    // 전화번호 제어 (3개 input)
    // -----------------------------
    const p1 = document.getElementById("phone1");
    const p2 = document.getElementById("phone2");
    const p3 = document.getElementById("phone3");

    if (p1 && p2 && p3) {
        // ★ 첫 번째 칸: 무조건 010 고정
        p1.value = "010";
        p1.readOnly = true;

        // ★ 두 번째 칸: 숫자만, 최대 4자리
        p2.addEventListener("input", function () {
            this.value = this.value.replace(/[^0-9]/g, "").slice(0, 4);
        });

        // ★ 세 번째 칸: 숫자만, 최대 4자리
        p3.addEventListener("input", function () {
            this.value = this.value.replace(/[^0-9]/g, "").slice(0, 4);
        });

        // 자동 이동 UX
        p2.addEventListener("keyup", function () {
            if (this.value.length === 4) p3.focus();
        });
    }
});

function updateAddressDisplay(data) {
    const sido = data.sido || "";
    const sigungu = data.sigungu || "";

    let gu = "";
    let addr1 = sido;

    if (sigungu) {
        if (sigungu.endsWith("구")) {
            if (sigungu.includes("시 ")) {
                const parts = sigungu.split("시 ");
                if (parts.length === 2) {
                    addr1 = sido + " " + parts[0] + "시";
                    gu = parts[1];
                } else {
                    gu = sigungu;
                }
            } else {
                gu = sigungu;
            }
        } else if (sigungu.endsWith("시") || sigungu.endsWith("군")) {
            addr1 = sido + " " + sigungu;
        }
    }

    const displayAddr1 = document.getElementById("display_addr1");
    const displayAddr2 = document.getElementById("display_addr2");

    if (displayAddr1) displayAddr1.textContent = addr1;
    if (displayAddr2) displayAddr2.textContent = gu || sigungu;
}

function handle_edit_profile(form) {
    const submitBtn = form.querySelector(".btn-edit-complete");
    const originalText = submitBtn.textContent;

    submitBtn.disabled = true;
    submitBtn.textContent = "수정 중...";

    // ★ 전화번호 3개 → 1개 합치기 (정규식 대응)
    const p1 = document.getElementById("phone1").value;
    const p2 = document.getElementById("phone2").value;
    const p3 = document.getElementById("phone3").value;

    const fullPhone = `${p1}-${p2}-${p3}`;
    document.getElementById("phone").value = fullPhone;

    // 전화번호 정규식 (signup과 동일)
    const phoneRegex = /^\d{3}-\d{4}-\d{4}$/;
    if (!phoneRegex.test(fullPhone)) {
        showToast("전화번호 형식이 올바르지 않습니다.", "error");
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
        return;
    }

    // 상세주소 hidden 업데이트
    const addressDetailInput = document.getElementById("address_detail");
    const addr3Hidden = document.getElementById("addr3");
    if (addressDetailInput && addr3Hidden) {
        addr3Hidden.value = addressDetailInput.value;
    }

    const formData = new FormData(form);
    formData.set("phone", fullPhone);
    formData.set("addr3", addressDetailInput.value);

    const csrftoken = document.querySelector(
        "[name=csrfmiddlewaretoken]"
    ).value;

    const editUrl =
        typeof MEMBER_EDIT_URL !== "undefined"
            ? MEMBER_EDIT_URL
            : "/member/edit/";

    fetch(editUrl, {
        method: "POST",
        body: formData,
        headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrftoken,
        },
    })
        .then((response) => {
            if (!response.ok) throw new Error(`HTTP ERROR: ${response.status}`);
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                showToast(data.message, "success");
                setTimeout(() => {
                    window.location.href =
                        MEMBER_INFO_URL + "?_=" + new Date().getTime();
                }, 1500);
            } else {
                showToast(data.message, "error");
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        })
        .catch(() => {
            showToast("수정 중 오류가 발생했습니다.", "error");
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
}

