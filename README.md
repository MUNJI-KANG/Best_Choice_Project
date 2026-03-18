# 🏆 Best Choice (BC_Project) - 할래말래
> **공공 체육시설 예약, 모집, 관리자 운영 기능을 포함한 Django 서비스**

---

## 📌 프로젝트 요약

공공 체육시설 데이터를 기반으로 **시설 조회 -> 예약 -> 모집 커뮤니티 -> 관리자 운영** 흐름을 구성한 Django 웹 서비스입니다.

이 프로젝트에서 저는 **예약 도메인 설계, 회원 인증/세션 처리, 예약과 모집 기능 간 연결 로직**을 담당했습니다.

---

## 🙋 담당 범위

### 1. 예약 도메인 설계 및 구현

- `Reservation` + `TimeSlot` 구조로 시간대 단위 예약 모델 설계
- 시설별 `reservation_time` JSON 정책 기반 예약 가능 여부 검증
- 서버 기준 결제 금액 계산 로직 구현
- 마이페이지 / 관리자 화면에서 부분 취소 지원
- 예약 만료 상태(`expire_yn`) 관리

### 2. 회원 인증 및 세션 처리

- 일반 로그인 / 로그아웃 / 회원가입 구현
- 세션 기반 인증 흐름 구현
- 로그인 유지 여부에 따른 세션 만료 제어
- 아이디 / 비밀번호 찾기 기능 구현
- 회원정보 수정 / 비밀번호 변경 / 회원 탈퇴 처리

### 3. 예약-모집 연결 로직

- 실제 예약 이력이 있는 일정만 모집글과 연결되도록 제한
- 이미 사용 중인 예약은 모집글 작성/수정 후보에서 제외
- 예약 데이터와 모집 데이터 간 1:N 혼선을 막는 검증 로직 구현

---

## 🛠 Tech Stack

- Backend: Python 3.12.5, Django 5.2.8
- Database: SQLite, MySQL 확장 고려
- Frontend: HTML, CSS, JavaScript, Django Template
- External APIs: Kakao OAuth / Maps, OpenAI, Naver Search, OpenWeather, 공공데이터포털

---

## 🔑 주요 기능

- 공공 체육시설 조회 및 지역/종목 필터링
- 시간대 단위 시설 예약
- 예약 내역 조회 및 부분 취소
- 예약 기반 운동 모집글 작성 및 참여 관리
- 일반 로그인 / 카카오 로그인 / 회원가입
- 관리자 시설 / 회원 / 예약 / 게시글 / 모집글 관리
- 관리자 AI 분석 대시보드

---

## ⚠️ Technical Decisions / Trouble Shooting

### 1. 예약 금액과 예약 가능 여부를 클라이언트 입력값에 의존하지 않도록 처리

**문제**  
예약 요청에서 날짜, 시간대, 금액 계산을 클라이언트 값만 신뢰하면 잘못된 요청이나 변조 요청을 그대로 반영할 수 있습니다.

**해결**  
서버에서 예약 날짜를 직접 파싱하고, 시설별 `reservation_time` 정책으로 예약 가능 여부를 다시 검증한 뒤 시간대 수 기준으로 결제 금액을 계산했습니다.

```python
day_key = res_date.strftime("%A").lower()
day_info = (facility.reservation_time or {}).get(day_key, {})
if not day_info.get("active"):
    return JsonResponse({"result": "error", "msg": "해당 요일은 예약 불가합니다."})

price_per_slot = int(day_info.get("payment") or 0)
total_payment = price_per_slot * len(slots)
```

**결과**  
예약 정책과 결제 금액의 기준을 서버로 일원화했습니다.

---

### 2. 부분 취소 이후 예약 상태와 결제 금액 불일치 문제 해결

**문제**  
예약 일부 시간대만 취소되는 경우, 예약은 남아 있는데 결제 금액이 기존 총액으로 유지되면 상태와 금액이 맞지 않게 됩니다.

**해결**  
취소 후 남아 있는 `TimeSlot`만 다시 조회하고, 남은 시간대 기준으로 결제 금액을 재계산했습니다. 남은 시간대가 없으면 예약 전체를 취소 상태로 전환했습니다.

```python
remaining_slots = TimeSlot.objects.filter(reservation_id=reservation, delete_yn=0)

if not remaining_slots.exists():
    reservation.delete_yn = 1
    reservation.payment = 0
    reservation.save()

total_payment = 0
for slot in remaining_slots:
    day_key = slot.date.strftime("%A").lower()
    day_info = rt.get(day_key, {})
    total_payment += int(day_info.get("payment") or 0)
```

**결과**  
부분 취소가 가능한 구조에서도 예약 상태와 결제 금액의 정합성을 유지했습니다.

---

### 3. 예약과 모집글의 중복 연결 방지

**문제**  
동일한 예약이 여러 모집글에 연결되면 어떤 일정이 실제 모집 기준인지 불명확해지고 데이터 신뢰도가 떨어집니다.

**해결**  
이미 사용 중인 `reservation_id`를 먼저 수집하고, 모집글 작성/수정 시 후보 예약 목록에서 제외했습니다.

```python
used_reservation_ids = (
    Community.objects
    .filter(member_id=member, delete_date__isnull=True)
    .exclude(reservation_id__isnull=True)
    .exclude(reservation_id_id=current_reservation_id)
    .values_list("reservation_id_id", flat=True)
)
```

**결과**  
예약 1건이 여러 모집글에 중복 연결되는 상황을 방지했습니다.

---

### 4. 사용자/관리자 권한과 로그인 유지 정책을 분리한 세션 처리

**문제**  
일반 사용자와 관리자가 동일한 로그인 엔트리를 사용하면서, 로그인 유지 여부까지 같이 처리해야 해 세션 흐름이 복잡해질 수 있습니다.

**해결**  
세션에 사용자 정보와 관리자 식별값을 분리 저장하고, `remember` 여부에 따라 세션 만료 시간을 다르게 적용했습니다.

```python
request.session["user_id"] = user.user_id
request.session["nickname"] = user.nickname

if user.manager_yn == 1:
    request.session["manager_id"] = user.member_id

if remember:
    request.session.set_expiry(60 * 60)
else:
    request.session.set_expiry(0)
```

**결과**  
권한 분기와 로그인 유지 정책을 분리해 인증 흐름을 단순화했습니다.

---

## 🗂 관련 모듈

- `reservation`: 예약 생성, 시간대 관리, 결제 금액 계산
- `member`: 로그인, 회원가입, 내 예약/회원정보 관리
- `recruitment`: 모집글, 참여 상태, 예약 연결
- `common`: 공통 인증 및 메인 기능
- `manager`: 관리자 운영 화면
- `ai_analytics`: 관리자 통계 / AI 분석

---

## 🚀 로컬 실행

```powershell
cd BC_Project
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

필수 환경변수 예시:

```env
OPENAI_API_KEY=
KAKAO_REST_API_KEY=
KAKAO_SCRIPT_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
OPEN_WEATHER_KEY=
DATA_API_KEY=
```

주요 관리 명령:

```powershell
python manage.py update_facility
python manage.py close_expired_recruitments
```

---

## 🎥 발표 영상

- 프로젝트 발표 영상 : [발표 영상 링크](https://www.youtube.com/watch?v=LaZt3GMA-yY&feature=youtu.be)
- 프로젝트 발표 화면 영상 : [발표 화면 영상 링크](https://www.youtube.com/watch?v=XAM7G9b4QOg&feature=youtu.be)
- 발표 자료(PPT): [PDF 링크](https://github.com/MUNJI-KANG/Best_Choice_Project/blob/main/docs/%EC%B5%9C%EA%B0%95%EC%84%A0%ED%83%9D%20%EB%B0%9C%ED%91%9C%20PPT.pptx)

---

## 한 줄 정리

팀 프로젝트 내에서 **예약 시스템과 인증 흐름을 중심으로 핵심 사용자 플로우를 구현한 Django 프로젝트**입니다.
