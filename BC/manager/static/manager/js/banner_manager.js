/* ------------------------------------------------------------------
   CSRF Token 가져오기
------------------------------------------------------------------ */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') return value;
    }
    return null;
}

/* ------------------------------------------------------------------
   배너 선택 삭제(목록 페이지)
------------------------------------------------------------------ */
function deleteBanners() {
    const checked = document.querySelectorAll('input[name="delete_ids"]:checked');
    if (checked.length === 0) {
        alert("삭제할 항목을 선택하세요.");
        return;
    }

    const ids = Array.from(checked).map(c => c.value);

    fetch("/manager/banner_delete/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ ids: ids })
    }).then(r => {
        if (r.ok) location.reload();
    });
}

/* ------------------------------------------------------------------
   수정 페이지: 기존 파일 “X” 버튼 삭제 + 새 파일 선택 처리
------------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", function () {

    // ---- 기존 파일 삭제(X 버튼) ----
    const deleteBtn = document.getElementById("deleteFileBtn");
    const deleteFlag = document.getElementById("deleteFileFlag");
    const currentFileBox = document.getElementById("currentFileBox");

    if (deleteBtn && deleteFlag && currentFileBox) {
        deleteBtn.addEventListener("click", function () {
            // 화면에서 숨기고
            currentFileBox.style.display = "none";
            // 서버에 삭제 요청 플래그
            deleteFlag.value = "1";
        });
    }

    // ---- 파일 선택 시 파일명 표시 + 기존 파일 무시 처리 ----
    const fileInput = document.getElementById("fileInput");
    const fileNameDisplay = document.getElementById("uploadedFileName");

    if (fileInput) {
        fileInput.addEventListener("change", function () {
            if (fileInput.files.length > 0) {
                if (fileNameDisplay) {
                    fileNameDisplay.style.display = "block";
                    fileNameDisplay.textContent = "선택된 파일: " + fileInput.files[0].name;
                }
                // 새 파일 업로드 시 기존 파일 무시하도록 플래그도 1로
                if (deleteFlag) {
                    deleteFlag.value = "1";
                    if (currentFileBox) currentFileBox.style.display = "none";
                }
            } else {
                if (fileNameDisplay) {
                    fileNameDisplay.style.display = "none";
                    fileNameDisplay.textContent = "";
                }
            }
        });
    }

});
