document.addEventListener("DOMContentLoaded", function () {

    /* 대한민국 시/도 + 시/군/구 데이터 */
    const regionData = {
        "서울특별시": [
            "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구",
            "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구",
            "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구",
            "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
        ],
        "부산광역시": [
            "강서구", "금정구", "기장군", "남구", "동구", "동래구", "부산진구",
            "북구", "사상구", "사하구", "서구", "수영구", "연제구", "영도구",
            "중구", "해운대구"
        ],
        "대구광역시": ["남구", "달서구", "달성군", "동구", "북구", "서구", "수성구", "중구"],
        "인천광역시": [
            "강화군", "계양구", "남동구", "동구", "미추홀구", "부평구",
            "서구", "연수구", "옹진군", "중구"
        ],
        "광주광역시": ["광산구", "남구", "동구", "북구", "서구"],
        "대전광역시": ["대덕구", "동구", "서구", "유성구", "중구"],
        "울산광역시": ["남구", "동구", "북구", "울주군", "중구"],
        "세종특별자치시": ["세종시"],
        "경기도": [
            "가평군", "고양시 덕양구", "고양시 일산동구", "고양시 일산서구",
            "과천시", "광명시", "광주시", "구리시", "군포시", "김포시",
            "남양주시", "동두천시", "부천시", "성남시 분당구", "성남시 수정구",
            "성남시 중원구", "수원시 권선구", "수원시 영통구", "수원시 장안구",
            "수원시 팔달구", "시흥시", "안산시 단원구", "안산시 상록구",
            "안성시", "안양시 동안구", "안양시 만안구", "양주시", "양평군",
            "여주시", "연천군", "오산시", "용인시 기흥구", "용인시 수지구",
            "용인시 처인구", "의왕시", "의정부시", "이천시", "파주시",
            "평택시", "포천시", "하남시", "화성시"
        ],
        "강원특별자치도": [
            "강릉시", "고성군", "동해시", "삼척시", "속초시", "양구군", "양양군",
            "영월군", "원주시", "인제군", "정선군", "철원군", "춘천시", "태백시",
            "평창군", "홍천군", "화천군", "횡성군"
        ],
        "충청북도": [
            "괴산군", "단양군", "보은군", "영동군", "옥천군", "음성군", "제천시",
            "증평군", "진천군", "청주시 상당구", "청주시 서원구", "청주시 청원구",
            "청주시 흥덕구", "충주시"
        ],
        "충청남도": [
            "계룡시", "공주시", "금산군", "논산시", "당진시", "보령시", "부여군",
            "서산시", "서천군", "아산시", "예산군", "천안시 동남구", "천안시 서북구",
            "청양군", "태안군", "홍성군"
        ],
        "전북특별자치도": [
            "고창군", "군산시", "김제시", "남원시", "무주군", "부안군",
            "순창군", "완주군", "익산시", "임실군", "장수군", "전주시 덕진구",
            "전주시 완산구", "정읍시", "진안군"
        ],
        "전라남도": [
            "강진군", "고흥군", "곡성군", "광양시", "구례군", "나주시",
            "담양군", "목포시", "무안군", "보성군", "순천시", "신안군",
            "여수시", "영광군", "영암군", "완도군", "장성군", "장흥군",
            "진도군", "함평군", "해남군", "화순군"
        ],
        "경상북도": [
            "경산시", "경주시", "고령군", "구미시", "군위군", "김천시", "문경시",
            "봉화군", "상주시", "성주군", "안동시", "영덕군", "영양군",
            "영주시", "영천시", "예천군", "울릉군", "울진군", "의성군",
            "청도군", "청송군", "칠곡군", "포항시 남구", "포항시 북구"
        ],
        "경상남도": [
            "거제시", "거창군", "고성군", "김해시", "남해군", "밀양시",
            "사천시", "산청군", "양산시", "의령군", "진주시",
            "창녕군", "창원시 마산합포구", "창원시 마산회원구",
            "창원시 성산구", "창원시 의창구", "창원시 진해구",
            "통영시", "하동군", "함안군", "함양군", "합천군"
        ],
        "제주특별자치도": ["서귀포시", "제주시"]
    };

    const params = new URLSearchParams(window.location.search);

    const sidoEl = document.getElementById("sido");
    const sigunguEl = document.getElementById("sigungu");
    const perPageEl = document.getElementById("perPageSelect");
    const rsPosible = document.getElementById('rsPosible');

    /* 시도 옵션 채우기 */
    Object.keys(regionData).forEach(sido => {
        sidoEl.insertAdjacentHTML("beforeend", `<option value="${sido}">${sido}</option>`);
    });

    const nowSido = params.get("sido") || "";
    const nowSigungu = params.get("sigungu") || "";
    sidoEl.value = nowSido;

    /* 시군구 렌더링 */
    function renderSigungu(sido) {
        sigunguEl.innerHTML = `<option value="">구/군 선택</option>`;
        if (!regionData[sido]) return;
        regionData[sido].forEach(sgg => {
            sigunguEl.insertAdjacentHTML("beforeend", `<option value="${sgg}">${sgg}</option>`);
        });
    }

    renderSigungu(nowSido);

    if (nowSigungu) sigunguEl.value = nowSigungu;
    
    /*  활성 비활성 변경 */
    rsPosible.addEventListener("change", function () {
        params.set("rsPosible", this.value);
        params.set("page", 1);
        window.location.search = params.toString();
    });


    /* 시도 변경 */
    sidoEl.addEventListener("change", function () {
        params.set("sido", this.value);
        params.delete("sigungu");
        params.set("page", 1);
        window.location.search = params.toString();
    });

    /* 시군구 변경 */
    sigunguEl.addEventListener("change", function () {
        params.set("sigungu", this.value);
        params.set("page", 1);
        window.location.search = params.toString();
    });

    /* per page */
    if (perPageEl) {
        const nowPer = params.get("per_page") || "15";
        perPageEl.value = nowPer;
        perPageEl.addEventListener("change", function () {
            params.set("per_page", this.value);
            params.set("page", 1);
            window.location.search = params.toString();
        });
    }

    /* 시설 목록 렌더링 */
    function renderFacilityList(data) {
        const box = document.getElementById("facilityList");
        box.innerHTML = "";

        if (!data || data.length === 0) {
            box.innerHTML = `<tr><td colspan="6">검색 결과가 없습니다.</td></tr>`;
            return;
        }

        box.innerHTML = data.map(item => `
            <tr>
                <td>${item.row_no}</td>
                <td><input type="checkbox" value="${item.id}"></td>
                <td><a href="/manager/facility/${item.facilityCd}/"> ${item.name}</a> ${item.rsPosible == 1 
                ? '<span class="status-active">활성</span>' 
                : '<span class="status-inactive">비활성</span>'
            }</td>
                <td>${item.address}</td>
                <td>
                    <a href="/manager/reservations/?facility_id=${item.facilityCd}&type=today" 
                       class="reservation-count-link" 
                       title="금일 활성 예약 상세보기">
                        ${item.today_count || 0}건
                    </a>
                </td>
                <td>
                    <a href="/manager/reservations/?facility_id=${item.facilityCd}&type=all" 
                       class="reservation-count-link" 
                       title="누적 예약 상세보기">
                        ${item.total_count || 0}건
                    </a>
                </td>
            </tr>
        `).join("");
    }

    /* JSON 파싱 */
    try {
        const list = JSON.parse(document.getElementById("facilityData").textContent.trim());
        renderFacilityList(list);
    } catch (e) {
        console.error("JSON 오류:", e);
    }



    document.querySelector(".delete-btn").addEventListener("click", function () {

        if (!confirm("선택된 시설을 삭제하시겠습니까?")) return;

        // 체크된 ID들 수집
        const checked = Array.from(
            document.querySelectorAll("#facilityList input[type='checkbox']:checked")
        ).map(ch => ch.value);

        if (checked.length === 0) {
            alert("삭제할 시설을 선택하세요.");
            return;
        }

        fetch("/manager/delete/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ ids: checked })
        })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("삭제 완료되었습니다.");
                    window.location.reload();
                } else {
                    alert("삭제 실패: " + data.msg);
                }
            })
            .catch(err => {
                console.error("삭제 에러:", err);
                alert("서버 오류");
            });
    });


    // CSRF 가져오는 함수 (필요)
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }



});