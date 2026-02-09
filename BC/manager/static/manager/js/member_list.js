document.addEventListener("DOMContentLoaded", function () {

    /* ======================
       전체 선택
    ====================== */
    document.getElementById("checkAll")?.addEventListener("change", function () {
        document.querySelectorAll("input[name='ids']").forEach(c => {
            c.checked = this.checked;
        });
    });

    /* ======================
       삭제 confirm
    ====================== */
    document.getElementById("deleteForm")?.addEventListener("submit", function (e) {
        const checked = document.querySelectorAll("input[name='ids']:checked");
        const selected = checked.length;

        if (selected === 0) {
            alert("삭제할 회원을 선택하세요.");
            e.preventDefault();
            return;
        }

        if (!confirm(selected + "명 회원을 삭제하시겠습니까?")) {
            e.preventDefault();
        }
    });

    /* ======================
       회원 복구
    ====================== */
    document.getElementById("restoreBtn")?.addEventListener("click", function () {
        const checked = document.querySelectorAll("input[name='ids']:checked");

        if (checked.length === 0) {
            alert("복구할 회원을 선택하세요.");
            return;
        }

        for (const item of checked) {
            if (item.dataset.status === "0") {
                alert("이미 현재 회원입니다.");
                return;
            }
        }

        if (!confirm(checked.length + "명 회원을 복구하시겠습니까?")) return;

        const form = document.createElement("form");
        form.method = "POST";
        form.action = "/manager/member/restore/";

        const csrf = document.querySelector("input[name='csrfmiddlewaretoken']").cloneNode();
        form.appendChild(csrf);

        checked.forEach(chk => {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "ids";
            input.value = chk.value;
            form.appendChild(input);
        });

        document.body.appendChild(form);
        form.submit();
    });

    /* ======================
       페이징
    ====================== */
    const perPageSelect = document.getElementById("perPageSelect");
    if (perPageSelect) {
        const current = perPageSelect.dataset.current;
        if (current) perPageSelect.value = current;

        perPageSelect.addEventListener("change", function () {
            const params = new URLSearchParams(window.location.search);
            params.set("per_page", this.value);
            params.set("page", 1);
            window.location.search = params.toString();
        });
    }

    
    const modal = document.getElementById("reasonModal");
    const reasonText = document.getElementById("reasonText");
    const closeBtn = document.getElementById("closeReasonModal");

    if (modal && reasonText && closeBtn) {
        document.querySelectorAll("tr.withdraw-row").forEach(row => {
            row.addEventListener("click", function (e) {
                // 체크박스 클릭 시는 무시
                if (e.target.tagName === "INPUT") return;

                const reason = row.dataset.reason || "사유 없음";
                reasonText.textContent = reason;
                modal.style.display = "block";
            });
        });

        closeBtn.addEventListener("click", function () {
            modal.style.display = "none";
        });

        modal.addEventListener("click", function (e) {
            if (e.target === modal) {
                modal.style.display = "none";
            }
        });
    }

});
