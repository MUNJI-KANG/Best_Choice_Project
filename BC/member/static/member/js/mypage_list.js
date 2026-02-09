// static/js/mypage_list.js

document.addEventListener("DOMContentLoaded", function () {
    // 셀렉트 요소 찾기
    const sortEl = document.querySelector('select[name="order"]');       // 정렬
    const perPageEl = document.querySelector('select[name="page_size"]'); // 페이지당 개수
    const statusEl = document.querySelector('select[name="status"]'); // 모집상태


    // 공통 URL 파라미터 객체
    const params = new URLSearchParams(window.location.search);

    /* ===========================
       2) 페이지당 개수(per_page) 처리
       =========================== */
    if (perPageEl) {
        const nowPer = params.get("per_page") || "15";
        perPageEl.value = nowPer;

        perPageEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("per_page", this.value);
            newParams.set("page", 1); // 개수 바꾸면 1페이지로
            window.location.search = newParams.toString();
        });
    }

    /* ===========================
       3) sort 처리 (정렬 유지)
       =========================== */
    if (sortEl) {
        const nowSort = params.get("sort") || "recent";  // 기본값 recent
        sortEl.value = nowSort;

        sortEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("sort", this.value);  // recent / title / views
            newParams.set("page", 1);
            window.location.search = newParams.toString();
        });
        }

    /* ===========================
    4) status 처리 (모집상태 유지)
    =========================== */
    if (statusEl) {
        const nowStatus = params.get("status") || "all";
        statusEl.value = nowStatus;

        statusEl.addEventListener("change", function () {
            const newParams = new URLSearchParams(window.location.search);
            newParams.set("status", this.value);
            newParams.set("page", 1);
            window.location.search = newParams.toString();
        });
    }


    
});
