// 페이징 처리
document.addEventListener("DOMContentLoaded", function () {
    const perPage = document.getElementById("perPageSelect");

    if (!perPage) return;

    // 현재 GET 파라미터에서 per_page 값을 읽어서 셀렉터에 적용
    const currentParams = new URLSearchParams(window.location.search);
    const nowPer = currentParams.get("per_page") || "15";
    perPage.value = nowPer;

    // 변경되면 페이지 새로고침
    perPage.addEventListener("change", function () {
        currentParams.set("per_page", this.value);
        currentParams.set("page", 1);  // 개수 바뀌면 1페이지로 이동
        window.location.search = currentParams.toString();
    });
});



// sort 처리 
document.addEventListener("DOMContentLoaded", function () {
    const sortSelect = document.getElementById("sortSelect");
    
    if (!sortSelect) return;
    
    const params = new URLSearchParams(window.location.search);

    // 현재 정렬 적용 (GET 기준)
    const nowSort = params.get("sort") || "recent";
    sortSelect.value = nowSort;

    sortSelect.addEventListener("change", function () {
        params.set("sort", this.value);
        params.set("page", 1); 
        window.location.search = params.toString();
    });
});

// 검색 기능
document.addEventListener("DOMContentLoaded", function () {
    const searchBtn = document.getElementById("searchBtn");
    const searchKeyword = document.getElementById("searchKeyword");
    const searchType = document.getElementById("searchType");

    if (!searchBtn || !searchKeyword || !searchType) return;

    // 검색 버튼 클릭
    searchBtn.addEventListener("click", function () {
        performSearch();
    });

    // 엔터 키로 검색
    searchKeyword.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            performSearch();
        }
    });

    function performSearch() {
        const keyword = searchKeyword.value.trim();
        const type = searchType.value;

        const params = new URLSearchParams(window.location.search);
        
        if (keyword) {
            params.set("keyword", keyword);
            params.set("search_type", type);
        } else {
            params.delete("keyword");
            params.delete("search_type");
        }
        
        params.set("page", 1); // 검색 시 1페이지로 이동
        window.location.search = params.toString();
    }
});

