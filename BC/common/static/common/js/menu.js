// ============================================
// 모바일 메뉴 토글
// ============================================
function initMobileMenu() {
  const menuBtn = document.getElementById('menuBtn');
  const nav = document.querySelector('.header__nav');
  const overlay = document.getElementById('mobileMenuOverlay');
  const navItems = document.querySelectorAll('.header__nav-item');

  if (!menuBtn || !nav || !overlay) return;

  // 햄버거 메뉴 버튼 클릭
  menuBtn.addEventListener('click', () => {
    menuBtn.classList.toggle('active');
    nav.classList.toggle('active');
    overlay.classList.toggle('active');
    document.body.classList.toggle('menu-open');
  });

  // 오버레이 클릭 시 메뉴 닫기
  overlay.addEventListener('click', (e) => {
    // 오버레이 자체를 클릭한 경우에만 메뉴 닫기
    e.preventDefault();
    e.stopPropagation();
    menuBtn.classList.remove('active');
    nav.classList.remove('active');
    overlay.classList.remove('active');
    document.body.classList.remove('menu-open');
    // 모든 서브메뉴 닫기
    navItems.forEach(navItem => {
      navItem.classList.remove('active');
    });
  });

  // 터치 이벤트도 처리 (모바일)
  overlay.addEventListener('touchend', (e) => {
    e.preventDefault();
    e.stopPropagation();
    menuBtn.classList.remove('active');
    nav.classList.remove('active');
    overlay.classList.remove('active');
    document.body.classList.remove('menu-open');
    navItems.forEach(navItem => {
      navItem.classList.remove('active');
    });
  });

  // 메뉴 영역 클릭 시 이벤트 전파 방지 (오버레이 클릭 이벤트와 충돌 방지)
  nav.addEventListener('click', (e) => {
    e.stopPropagation();
  });

  // 모바일 메뉴 아이템 클릭 (서브메뉴 토글)
  navItems.forEach(item => {
    const link = item.querySelector('.header__nav-link');
    const submenu = item.querySelector('.header__submenu');
    
    if (link && submenu) {
      // 서브메뉴가 있는 아이템만 처리
      link.addEventListener('click', (e) => {
        // 서브메뉴 내부 링크 클릭 시에는 기본 동작만 수행
        if (e.target.closest('.header__submenu')) {
          return; // 서브메뉴 링크는 기본 동작 유지
        }
        
        // 모바일(768px 이하)에서만 서브메뉴 토글
        if (window.innerWidth <= 768) {
          e.preventDefault();
          e.stopPropagation();
          item.classList.toggle('active');
        }
        // 데스크탑에서는 기본 동작 유지 (hover로 서브메뉴 표시)
      });
    }
    
    // 서브메뉴 내부 링크 클릭 시 이벤트 전파 방지
    if (submenu) {
      const submenuLinks = submenu.querySelectorAll('a');
      submenuLinks.forEach(subLink => {
        subLink.addEventListener('click', (e) => {
          // 서브메뉴 링크 클릭 시 메뉴 닫기 (모바일에서만)
          if (window.innerWidth <= 768) {
            menuBtn.classList.remove('active');
            nav.classList.remove('active');
            overlay.classList.remove('active');
            document.body.classList.remove('menu-open');
            // 모든 서브메뉴 닫기
            navItems.forEach(navItem => {
              navItem.classList.remove('active');
            });
          }
        });
      });
    }
  });

  // 화면 크기 변경 시 메뉴 닫기
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      menuBtn.classList.remove('active');
      nav.classList.remove('active');
      overlay.classList.remove('active');
      document.body.classList.remove('menu-open');
    }
  });
}

// ============================================
// 스크롤 리빌 애니메이션
// ============================================
function initScrollReveal() {
  const targets = document.querySelectorAll('.reveal');
  if (!targets.length) return;

  // IntersectionObserver 미지원 브라우저 대비
  if (!('IntersectionObserver' in window)) {
    targets.forEach((el) => el.classList.add('is-visible'));
    return;
  }

  const observer = new IntersectionObserver(
    (entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          obs.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.2,
    }
  );

  targets.forEach((el) => observer.observe(el));
}

function initApp() {
  initMobileMenu();
  initScrollReveal();
}

// DOM이 로드된 후 초기화
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  // DOM이 이미 로드된 경우
  initApp();
}
