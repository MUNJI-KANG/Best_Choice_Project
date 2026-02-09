// ============ 팝업 관련 요소 ============
const sportsPopup = document.getElementById("sportsPopup");
const openBtn = document.getElementById("openSportsPopup");
const closeBtn = document.getElementById("closeSportsPopup");
const saveBtn = document.getElementById("saveSportsBtn");
const cardContainer = document.getElementById("sportsCardContainer");

// 종목 데이터 가져오기 (Django → JS)
let sportsData = [];
try {
    sportsData = JSON.parse(document.getElementById("sportData").textContent);
} catch (e) {
    console.error("sports_json 없음");
}

// 선택된 종목 저장용
let selectedSports = new Set();


// ============ 팝업 열기 ============ 
openBtn.addEventListener("click", () => {
    sportsPopup.style.display = "flex";
    renderSportsCards();
});


// ============ 팝업 닫기 ============
closeBtn.addEventListener("click", () => {
    sportsPopup.style.display = "none";
});


// ============ 종목 카드 렌더링 ============
function renderSportsCards() {
    cardContainer.innerHTML = "";

    sportsData.forEach(sport => {
        const card = document.createElement("div");
        card.className = "sports-card";
        card.dataset.id = sport.id;
        card.innerText = sport.s_name;

        // 이미 선택된 경우 표시
        if (selectedSports.has(sport.id)) {
            card.classList.add("selected");
        }

        // 클릭 시 선택/해제
        card.addEventListener("click", () => {
            if (selectedSports.has(sport.id)) {
                selectedSports.delete(sport.id);
                card.classList.remove("selected");
            } else {
                selectedSports.add(sport.id);
                card.classList.add("selected");
            }
        });

        cardContainer.appendChild(card);
    });
}


// ============ 저장 버튼 ============
saveBtn.addEventListener("click", () => {

    console.log("선택된 종목 ID:", [...selectedSports]);

    // Ajax로 서버에 저장할 수도 있음

    alert("종목 선택이 저장되었습니다.");
    sportsPopup.style.display = "none";
});
