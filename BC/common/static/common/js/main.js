// 메인 페이지 JavaScript

// 지역 설정 상수수
const WEATHER_CITIES = [
  { code: 'seoul',   label: '서울' },
  { code: 'busan',   label: '부산' },
  { code: 'incheon', label: '인천' },
  { code: 'daejeon', label: '대전' },
  { code: 'daegu',   label: '대구' },
  { code: 'gwangju', label: '광주' },
  { code: 'ulsan',    label: '울산' },
  { code: 'jeju',     label: '제주' },
  { code: 'suwon',    label: '수원' },
  { code: 'cheongju', label: '청주' },
  { code: 'jeonju',   label: '전주' },
];

// ------------------------- 날씨 테마 적용 ------------------------- //
let lightningInterval = null;

function applyWeatherTheme(main) {
  const container = document.querySelector('.template-section-01 .inner1');
  if (!container) return;

  container.classList.add('weather-visual');
  container.classList.remove(
    'weather-visual--sunny',
    'weather-visual--rain',
    'weather-visual--snow',
    'weather-visual--cloudy',
    'weather-visual--wind',
    'weather-lightning-active'
  );

  // 기존 번개 인터벌 정리
  if (lightningInterval) {
    clearInterval(lightningInterval);
    lightningInterval = null;
  }

  const key = (main || '').toLowerCase();
  let themeClass = 'weather-visual--cloudy';

  if (key === 'clear') themeClass = 'weather-visual--sunny';
  else if (key === 'rain' || key === 'drizzle' || key === 'thunderstorm') {
    themeClass = 'weather-visual--rain';
    // 비가 내릴 때 번개 효과 (thunderstorm인 경우에만)
    if (key === 'thunderstorm') {
      startLightningEffect(container);
    }
  }
  else if (key === 'snow') themeClass = 'weather-visual--snow';
  else if (key === 'clouds') themeClass = 'weather-visual--cloudy';
  else if (
    key === 'mist' ||
    key === 'smoke' ||
    key === 'haze' ||
    key === 'dust' ||
    key === 'fog' ||
    key === 'sand' ||
    key === 'ash' ||
    key === 'squall' ||
    key === 'tornado'
  )
    themeClass = 'weather-visual--wind';

  container.classList.add(themeClass);
}

// 번개 효과 함수
function startLightningEffect(container) {
  function triggerLightning() {
    container.classList.add('weather-lightning-active');
    setTimeout(() => {
      container.classList.remove('weather-lightning-active');
    }, 300);
  }

  // 처음 1.2초 후 번개
  setTimeout(triggerLightning, 1200);
  
  // 이후 랜덤하게 번개 (3-8초 간격)
  function scheduleNextLightning() {
    const delay = 3000 + Math.random() * 5000; // 3-8초
    lightningInterval = setTimeout(() => {
      triggerLightning();
      scheduleNextLightning();
    }, delay);
  }
  
  scheduleNextLightning();
}

function renderWeatherWidget(data) {
  const weatherInfo = document.getElementById('weatherInfo');
  if (!weatherInfo) return;

  const temp = Math.round(data.temp);
  const description = data.description || '';
  const cityLabel = data.city_label || data.city_name || '';
  const precipitation = data.precipitation ?? 0;
  const humidity = data.humidity ?? 0;

  const cityChipsHtml = WEATHER_CITIES.map((city) => {
    const isActive = city.code === data.city_code;
    return `<button class="weather-city-chip${
      isActive ? ' weather-city-chip--active' : ''
    }" data-city="${city.code}">${city.label}</button>`;
  }).join('');

  weatherInfo.innerHTML = `
    <div class="weather-temp">${temp}°C</div>
    <div class="weather-desc">${cityLabel} · ${description}</div>
    <div class="weather-detail">
      <div><span>강수량</span><strong>${precipitation.toFixed(1)}mm</strong></div>
      <div><span>습도</span><strong>${humidity}%</strong></div>
    </div>
    <div class="weather-city-chips">
      ${cityChipsHtml}
    </div>
  `;

  // 도시 선택 버튼
  document.querySelectorAll('.weather-city-chip').forEach((btn) => {
    btn.addEventListener('click', () => {
      const city = btn.getAttribute('data-city');
      loadWeather(city);
    });
  });
}

// ------------------------- 오늘의 날씨 LOADER ------------------------- //
async function loadWeather(cityCode = 'seoul') {
  const weatherInfo = document.getElementById('weatherInfo');
  if (!weatherInfo) return;

  weatherInfo.innerHTML =
    '<div class="weather-loading">날씨 정보를 불러오는 중...</div>';

  try {
    const resp = await fetch(`/api/weather/?city=${encodeURIComponent(cityCode)}`);
    if (!resp.ok) throw new Error('Weather API error');

    const data = await resp.json();
    renderWeatherWidget(data);
    applyWeatherTheme(data.main);
  } catch (error) {
    console.error('날씨 정보 로드 실패:', error);
    weatherInfo.innerHTML =
      '<div class="weather-error">날씨 정보를 불러올 수 없습니다.</div>';
  }
}

// ============================================
// 페이지 로드 시 초기화
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  loadWeather();
});

