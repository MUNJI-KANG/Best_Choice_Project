# 🏆 Best Choice (BC_Project) - 할래말래
> **공공데이터 활용 공모전을 참가한 Django 기반 체육시설 예약 및 커뮤니티 서비스**
---
## 📌 프로젝트 소개 (KOREA IT ACADEMY 국비지원 과정 팀 프로젝트)

**할래말래**는 체육진흥공단이 주관한 공공데이터 활용 공모전에 참가하기 위해 개발한 Django 기반 공공시설 예약 및 커뮤니티 웹 서비스입니다.

사용자는 공공데이터를 기반으로 체육 시설을 조회 및 예약할 수 있으며,
모집 게시판을 통해 운동 정보 공유 및 함께 운동할 사용자를 모집할 수 있습니다.

단순 예약 시스템을 넘어, 공공시설 이용 활성화와 사용자 간 커뮤니티 형성을 목표로 설계된 서비스입니다.

---

## 📌 프로젝트 배경

공공 체육시설은 예약 시스템이 기관별로 분산되어 있어 접근성이 낮은 문제가 있습니다.
또한 최근 러닝크루, 단체 운동 등 개인 운동보다 함께하는 운동 문화가 증가하고 있으나,
공공시설 예약 시스템과 모집 커뮤니티 기능은 대부분 분리되어 운영되고 있습니다.

이에 공공시설 예약 기능과 모집 커뮤니티 기능을 하나의 플랫폼에 통합한다면,
공공시설 이용률을 높이고 사용자 간 상호작용을 활성화할 수 있다고 판단했습니다.

본 프로젝트는 공공데이터를 활용하여

- 공공 체육시설 정보를 통합 제공하고
- 온라인 예약 기능을 구현하며
- 사용자 간 소통 및 운동 모집 기능을 결합한 플랫폼을 구축하는 것을 목표로 기획되었습니다.


---

## 📌 프로젝트 개요

- 프로젝트명: 할래말래
- 개발 기간: 2025.11.17 ~ 2025.12.24
- 팀명: 최강선택
- 개발 형태: 4인 팀 프로젝트 (KOREA IT ACADEMY 과정)

## 👥 팀 구성 및 역할 (최강선택)
- **강대광**: 예약 시스템 설계 및 구현, 회원 관리 및 인증 기능 개발
- **최무선**: 카카오 로그인 연동, 통계 대시보드 및 AI 분석 기능 구현
- **최재영**: 모집 게시판, 마이페이지, 공지사항 기능 개발
- **오경택**: 서버 관리 및 공공시설 관리 기능 구현

### 🎯 프로젝트 목표

- 공공데이터 기반 공공시설 예약 서비스 구현
- 예약 시간 중복 방지 로직 설계
- 사용자 권한 분리 및 관리자 기능 구현
- 커뮤니티 기능을 통한 공공시설 이용 활성화

---

## 🛠 Tech Stack

### Backend
- ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) **3.12.5**
- ![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white) **5.2.8**

### Database
- ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white) **(AWS RDS)**

### Frontend
- ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
- ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
- ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
- **Django Template**

### Deployment
- ![AWS](https://img.shields.io/badge/AWS_EC2-FF9900?style=flat-square&logo=amazonec2&logoColor=white) **(Ubuntu)**
- ![Gunicorn](https://img.shields.io/badge/Gunicorn-499848?style=flat-square&logo=gunicorn&logoColor=white)
- ![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white)
- ![AWS](https://img.shields.io/badge/AWS_RDS-527FFF?style=flat-square&logo=amazonrds&logoColor=white) **(MySQL)**

### Collaboration
- ![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white) / ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)
---
## 🔑 주요 기능

### 1️⃣ 회원 기능
- 일반 회원가입 및 카카오 소셜 로그인 지원
- 사용자 권한 분리 (일반 사용자 / 관리자)
- 주소 기반 사용자 정보 관리

### 2️⃣ 공공시설 기능
- 공공데이터 기반 시설 목록 조회
- 회원 주소 기반 지역 시설 필터링
- 시설 상세 정보 제공

### 3️⃣ 예약 기능
- 날짜 및 시간대 선택 예약
- 시간 구간 겹침 방지를 통한 예약 중복 차단
- 사용자별 예약 내역 조회

### 4️⃣ 모집 기능
- 모집 게시글 CRUD
- 모집 참여 신청 및 상태 관리 (승인 / 대기 / 거절)
- 댓글 기능
- 모집 상태 관리

### 5️⃣ 관리자 기능
- 시설 및 사용자 관리
- 통계 대시보드 제공 (예약 추이, 신규 회원 수 시각화)
- 관리자 전용 AI 챗봇 기능 제공

## 🤖 관리자용 AI 챗봇 (OpenAI API 연동)

웹사이트 운영을 보다 효율적으로 관리하기 위해
OpenAI API를 연동한 관리자 전용 AI 챗봇 기능을 구현했습니다.

- Django 서버에서 OpenAI API 호출
- 관리자 페이지 내 AJAX 기반 비동기 응답 처리
- 통계 데이터 기반 운영 질의응답 지원

관리자가 자연어로 질문을 입력하면,
서버(View)에서 OpenAI API에 요청을 전송하고
응답을 JSON 형태로 반환하여 관리자 화면에 출력하는 구조로 구현했습니다.

API Key는 환경변수로 관리하여 보안을 유지했습니다.

---
## 🗂 Database Design (ERD)

![ERD](./ERD/BC_erd.png)

- Member를 중심으로 Reservation, Community, Comment, Rating 등 주요 도메인이 1:N 관계로 연결됩니다.
- Reservation은 Facility 및 Time_slot과 연결되어 예약 흐름을 관리합니다.
- Community는 Article, Comment, Join_stat과 연결되어 모집 및 커뮤니티 활동을 구성합니다.
- Add_file은 게시글 및 시설과 연결되어 파일 업로드 기능을 지원합니다.
- 각 도메인은 상태(status) 및 날짜 필드를 활용하여 흐름 제어가 가능하도록 설계했습니다.
---

## 🧩 주요 App 구조

| App | 역할 |
|------|------|
| facility | 공공데이터 기반 시설 정보 관리 및 조회 기능 |
| reservation | 예약 생성, 시간 중복 검증, 예약 상태 관리 |
| recruitment | 운동 모집 게시글 및 참여 관리 |
| member | 사용자 인증 및 권한 관리 |
| manager | 관리자 전용 통계 및 운영 기능 |
| board | 일반 게시판 및 공지사항 기능 |
| ai_analytics | 예약/회원 데이터 기반 통계 및 분석 기능 |

---
## ⚠️ Trouble Shooting & Technical Highlights

### 1. 데이터 일관성을 위한 원자적 연산(Atomic Update) 적용
**[Situation]**
모집 게시판 상세 페이지 조회 시, 사용자 접속에 따른 실시간 조회수 업데이트가 필요했습니다.

**[Problem]**
일반적인 파이썬 객체 수정(`instance.view_cnt += 1`) 방식은 다수의 사용자가 동시에 접속할 경우 데이터가 덮어씌워져 조회수가 누락되는 **경쟁 상태(Race Condition)**를 유발할 수 있었습니다.

**[Solution]**
Django의 `F()` 객체를 활용하여 파이썬 메모리가 아닌 데이터베이스 레벨에서 직접 값을 증가시키는 업데이트 쿼리를 수행하도록 로직을 개선했습니다.

**[Result]**
동시 접속 환경에서도 단 한 건의 데이터 누락 없이 정확한 조회수 정합성을 유지하는 안정적인 시스템을 구축했습니다.

**💻 핵심 코드**
```python
# recruitment/views.py (상세 조회 로직 중)
try:
    recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
    # F() 객체를 활용한 DB 레벨의 원자적 업데이트로 동시성 이슈 해결
    Community.objects.filter(pk=pk, delete_date__isnull=True).update(view_cnt=F("view_cnt") + 1)
except Community.DoesNotExist:
    raise Http404("존재하지 않는 모집글입니다.")
```

---

### 2. 효율적인 대용량 데이터 로딩 및 N+1 문제 해결
**[Situation]**
모집글 목록을 불러올 때 게시글 정보뿐만 아니라 마감 상태, 현재 참가자 수, 댓글 수 등 연관된 여러 테이블의 데이터를 함께 렌더링해야 했습니다.

**[Problem]**
ORM의 지연 로딩(Lazy Loading)으로 인해 게시글 개수만큼 추가적인 SQL 쿼리가 발생하는 **N+1 문제**가 발생하여 서버 성능 저하가 우려되었습니다.

**[Solution]**
`select_related`를 적용하여 연관 객체(`EndStatus`)를 SQL JOIN으로 한 번에 가져오도록 최적화하고, `annotate`와 `Count`를 조합해 참가자 수와 댓글 수를 DB 레벨에서 미리 계산했습니다.

**[Result]**
데이터베이스 호출 횟수를 획기적으로 줄여, 다량의 게시글 조회 시에도 일관되고 빠른 로딩 속도를 보장하는 쿼리 최적화를 달성했습니다.

**💻 핵심 코드**
```python
# recruitment/views.py (목록 조회 로직 중)
qs = (
    Community.objects
    .filter(delete_date__isnull=True)
    .select_related("endstatus")  # JOIN을 통한 N+1 문제 해결
    .annotate(
        current_member=Count("joinstat"),              # DB 레벨 집계 연산
        comment_count=Count('comment', distinct=True),
    )
)
```

---

### 3. 사용자 경험(UX)과 데이터 신뢰도를 높인 예약-모집 연동
**[Situation]**
사용자가 자신이 예약한 시설을 기반으로 모집글을 작성하거나 수정할 때, 이미 사용된 예약을 걸러내고 지역 정보를 일치시켜야 했습니다.

**[Problem]**
이미 다른 모집글에 사용된 예약 내역이 중복 노출될 경우, 데이터의 신뢰도가 떨어지고 사용자의 혼란을 초래할 수 있었습니다.

**[Solution]**
`exclude` 쿼리를 복합적으로 사용하여 로그인한 사용자의 전체 예약 중 **이미 다른 게시글에 연결된 `reservation_id`를 완벽하게 제외**하는 필터링 로직을 구현했습니다.

**[Result]**
사용자의 입력 실수를 방지하는 동시에 시스템적인 데이터 불일치 가능성을 원천 차단하여 서비스의 완성도를 높였습니다.

**💻 핵심 코드**
```python
# recruitment/views.py (모집글 수정 로직 중)
# 이미 다른 모집글에서 사용 중인 예약 내역 중복 노출 차단
used_reservation_ids = (
    Community.objects
    .filter(member_id=member, delete_date__isnull=True)
    .exclude(reservation_id__isnull=True)
    .exclude(reservation_id_id=current_reservation_id) # 현재 수정 중인 글은 예외 처리
    .values_list("reservation_id_id", flat=True)
)
```

---

## 🎥 발표 영상

- 프로젝트 발표 영상 : [발표 영상 링크](https://www.youtube.com/watch?v=LaZt3GMA-yY&feature=youtu.be)
- 프로젝트 발표 화면 영상 : [발표 화면 영상 링크](https://www.youtube.com/watch?v=XAM7G9b4QOg&feature=youtu.be)
- 발표 자료(PPT): [PDF 링크](https://github.com/MUNJI-KANG/Best_Choice_Project/blob/main/docs/%EC%B5%9C%EA%B0%95%EC%84%A0%ED%83%9D%20%EB%B0%9C%ED%91%9C%20PPT.pptx)
---
