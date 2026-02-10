# Best Choice (BC_Project)

공공시설 예약 및 팀원 모집 기능을 제공하는 Django 기반 웹 애플리케이션입니다.  
사용자는 공공시설을 조회하고 예약할 수 있으며, 모집 게시판을 통해 팀원을 모집할 수 있습니다.

---

## 📌 프로젝트 개요

- 프로젝트명: 할래말래
- 개발 기간: [YYYY.MM ~ YYYY.MM]
- 팀명 : BEST CHOICE
- 개발 인원: 4인 프로젝트 (KOREA IT ACADEMY PROJECT)
- 팀원 :
    - 강대광
    - 최무선
    - 최재영
    -오경택 
- 목적:
  - Django 기반 실전 CRUD 구조 이해
  - 예약 중복 방지 로직 구현
  - 사용자 권한 분리 및 관리자 기능 구현
  - 실제 서비스 수준의 웹 구조 설계 경험

---

## 🛠 기술 스택

### Backend
- Python [ 3.12.5]
- Django [5.2.8]
- SQLite (개발용 DB)

### Frontend
- HTML5
- CSS3
- JavaScript
- Django Template Engine

### 기타
- Git / GitHub
- AWS EC2 / Nginx / Gunicorn

## 📂 프로젝트 구조

BC_Project/
├── ai_analytics/
├── board/
├── common/
├── facility/
├── manager/
├── member/
├── recruitment/
├── reservation/
└── manage.py


### 주요 앱 설명

| App | 설명 |
|------|------|
| facility | 공공시설 정보 관리 |
| reservation | 시설 예약 로직 |
| recruitment | 팀원 모집 게시판 |
| member | 회원 관리 |
| manager | 관리자 기능 |
| board | 일반 게시판 |
| ai_analytics | 데이터 분석 기능 |

---

## 🔑 주요 기능

### 1️⃣ 회원 기능
- 회원가입 / 로그인 / 로그아웃
- 사용자 권한 분리 (일반 사용자 / 관리자)

### 2️⃣ 공공시설 기능
- 시설 목록 조회
- 시설 상세 조회

### 3️⃣ 예약 기능
- 날짜 및 시간대 선택 예약
- 예약 중복 방지 로직 구현
- 사용자별 예약 조회

### 4️⃣ 모집 기능
- 모집글 작성 / 수정 / 삭제
- 댓글 기능
- 모집 상태 관리

### 5️⃣ 관리자 기능
- 시설 등록 / 수정 / 삭제
- 사용자 관리

---

