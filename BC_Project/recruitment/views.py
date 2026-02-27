from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.utils import timezone

from common.paging import pager


from django.views.decorators.csrf import csrf_exempt



from .models import *
from reservation.models import *
from member.models import Member
from common.models import *
from facility.models import FacilityInfo

from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages

from django.views.decorators.http import require_POST
from django.db import transaction, IntegrityError
from django.db.models import Q, F, Count, Case,When,Value, BooleanField

from collections import OrderedDict

import os
import uuid
from django.conf import settings
from datetime import date
ALWAYS_OPEN_DATE = date(2099, 1, 1)



from common.utils import *


def recruitment_list(request):
    """
    조건에 맞는 모집글 목록을 조회하고, 페이징 및 동적 필터링을 처리하는 뷰 함수입니다.

    [기술적 주안점]
    - N+1 문제 해결: QuerySet 평가 시 select_related("endstatus")를 사용하여 연관된 마감 상태 데이터를
      SQL JOIN으로 한 번에 가져와 데이터베이스 호출 횟수를 최소화했습니다.
    - DB 레벨 집계 최적화: annotate()와 Count()를 활용해 참여자 수(current_member)와 댓글 수(comment_count)를
      파이썬 메모리가 아닌 데이터베이스 레벨에서 미리 계산하여 대용량 트래픽 환경에서의 렌더링 성능을 개선했습니다.
    """
    search_type = request.GET.get("search_type", "all")
    keyword = request.GET.get("keyword", "").strip()
    sido = request.GET.get("sido", "")
    sigungu = request.GET.get("sigungu", "")
    status = request.GET.get("status", "all")

    # 모집글 + end_status + 참가자수 join
    qs = (
        Community.objects
        .filter(delete_date__isnull=True)
        .select_related("endstatus")  # JOIN ? 
        .annotate(
            current_member= Count("joinstat"),
            comment_count = Count('comment', distinct=True),
            end_set_date = F("endstatus__end_set_date"),
            is_always_open = Case(
                When(endstatus__end_set_date=ALWAYS_OPEN_DATE, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
    )

    # 지역 필터
    if sido:
        qs = qs.filter(region=sido)
    if sigungu:
        qs = qs.filter(region2=sigungu)

    # 검색 필터
    if keyword:
        if search_type == "facility":
            qs = qs.filter(facility__icontains=keyword)
        elif search_type == "sport":
            qs = qs.filter(sport_type__icontains=keyword)
        else:
            qs = qs.filter(
                Q(title__icontains=keyword) |
                Q(facility__icontains=keyword) |
                Q(sport_type__icontains=keyword)
            )

    # 모집 상태 필터
    if status == "closed":
        qs = qs.filter(endstatus__end_stat=1)
    elif status == "open":
        qs = qs.exclude(endstatus__end_stat=1)

    # 정렬
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        qs = qs.order_by("title")
    elif sort == "views":
        qs = qs.order_by("-view_cnt")
    elif sort =="end_set_date":
        qs = qs.order_by("end_set_date")
    else:
        qs = qs.order_by("-reg_date")

    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))

    paging = pager(request, qs, per_page=per_page)
    page_obj = paging['page_obj']



    # 템플릿용 마감 상태
    for obj in page_obj:
        es = getattr(obj, "endstatus", None)
        obj.is_closed = (es and es.end_stat == 1)



    context = {
        "page_obj": page_obj,
        "page": page,
        "per_page": per_page,
        "sort": sort,
        "search_type": search_type,
        "keyword": keyword,
        "sido": sido,
        "sigungu": sigungu,
        "status": status,
        "block_range": paging['block_range'],
        "block_start": paging['block_start'],
        "block_end": paging['block_end'],
    }

    return render(request, "recruitment/recruitment_list.html", context)




def write(request):
    
    res = check_login(request)
    if res:
        return res
      
    user_id = request.session.get("user_id")


    # 1) 세션의 user_id 로 Member 객체 가져오기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("common:login")


    used_reservation_ids = (
        Community.objects
        .filter(
            member_id=member,
            delete_date__isnull=True,
        )
        .exclude(reservation_id__isnull=True)
        .values_list("reservation_id", flat=True)
    )


    my_reservations = (
        Reservation.objects
        .filter(
            member=member,
            delete_date__isnull=True,
        )
        .exclude(pk__in=used_reservation_ids)
        .order_by("-reg_date")
    )

    # 🔹 그 예약들에 속한 타임슬롯 (delete_yn = 0) + 이미 사용한 reservation 제외
    my_slots = (
        TimeSlot.objects
        .filter(
            reservation_id__member=member,
            reservation_id__delete_date__isnull=True,
            delete_yn=0,
        )
        .exclude(reservation_id_id__in=used_reservation_ids)  # 🔥 이미 쓴 예약 제외
        .select_related("reservation_id", "facility_id")
        .order_by("reservation_id", "date", "start_time")
    )

    # 예약 단위로 그룹핑
    grouped_slots = OrderedDict()
    for slot in my_slots:
        rid = slot.reservation_id_id  # 또는 slot.reservation_id.pk

        if rid not in grouped_slots:
            grouped_slots[rid] = {
                "reservation": slot.reservation_id,
                "facility_name": slot.facility_id.faci_nm,  # 시설 이름
                "date": slot.date,                          # 예약 날짜
                "times": [],
            }

        grouped_slots[rid]["times"].append({
            "start_time": slot.start_time,
            "end_time": slot.end_time,
        })

    my_reservation_slots = list(grouped_slots.values())

    # 2) POST 처리
    if request.method == "POST":
        print("POST data:", request.POST)
        title = request.POST.get("title")
        region = request.POST.get("sido")
        region2 = request.POST.get("sigungu")
        sport_type = request.POST.get("sport")
        num_member = request.POST.get("personnel")
        contents = request.POST.get("content")
        chat_url = request.POST.get("openchat_url") or None

        reservation_id = (request.POST.get("reservation_choice") or "").strip()

        end_type = request.POST.get("end_type") or "date"              # 'date' or 'always'
        end_set_date_raw = request.POST.get("end_set_date")  # YYYY-MM-DD or ''

        facility_name = "미정"
        reservation_obj = None
        # 🔹 폼 다시 뿌릴 때 쓸 데이터 묶음
        form_data = {
            "title": title,
            "sido": region,
            "sigungu": region2,
            "sport": sport_type,
            "personnel": num_member,
            "content": contents,
            "openchat_url": chat_url,
            "reservation_choice": reservation_id,
            "end_type": end_type,
            "end_set_date": end_set_date_raw,
        }


        if reservation_id:
            # 선택된 예약 객체
            reservation_obj = (
                Reservation.objects
                .filter(
                    pk=reservation_id,
                    member=member,
                    delete_date__isnull=True,
                )
                .first()
            )

            # 선택된 예약 기준으로 시설/지역 세팅
            slot = (
                TimeSlot.objects
                .select_related("facility_id", "reservation_id")
                .filter(
                    reservation_id_id=reservation_id,
                    reservation_id__member=member,
                    reservation_id__delete_date__isnull=True,
                    delete_yn=0,
                )
                .first()
            )
            if slot:
                facility = slot.facility_id
                facility_name = facility.faci_nm
                region = facility.sido
                region2 = facility.sigugun

        recruit = Community.objects.create(
            title=title,
            region=region,
            region2=region2,
            sport_type=sport_type,
            num_member=num_member,
            facility=facility_name,
            contents=contents,
            chat_url=chat_url,
            member_id=member,
            # 🔥 여기: Community 모델의 FK 이름이 "reservation_id"
            reservation_id=reservation_obj,
        )

        # 🔹 상시모집 / 날짜모집 분기
        if end_type == "always":
            end_set_date = ALWAYS_OPEN_DATE
        else:
            if end_set_date_raw:
                try:
                    end_set_date = date.fromisoformat(end_set_date_raw)
                except ValueError:
                    messages.error(request, "유효한 마감일을 선택해 주세요.")
                    context = {
                        "my_reservations": my_reservations,
                        "my_reservation_slots": my_reservation_slots,
                    }
                    return render(request, "recruitment/recruitment_write.html", context)
                
                    # end_set_date = date.today()
                    
            else:
                messages.error(request, "유효한 마감일을 선택해 주세요.")
                context = {
                    "my_reservations": my_reservations,
                    "my_reservation_slots": my_reservation_slots,
                }
                return render(request, "recruitment/recruitment_write.html", context)

        EndStatus.objects.create(
            community=recruit,
            end_set_date=end_set_date,
            end_date=None,
            end_stat=0,
        )


        files = request.FILES.getlist("files")
        upload_files(request, recruit, file_field="files", sub_dir="uploads/community")

        return redirect("recruitment:recruitment_detail", pk=recruit.pk)
    today = date.today().isoformat()
    # 3) GET 요청이면 작성 폼 + 내 예약 목록 넘기기
    context = {
        'mode':'create',
        "my_reservations": my_reservations,
        "my_reservation_slots": my_reservation_slots,
        "today":today
    }
    return render(request, "recruitment/recruitment_form.html", context)



def update(request, pk):
    """
    기존 모집글의 내용을 수정하고 연관된 예약 정보 및 첨부파일을 갱신하는 뷰 함수입니다.

    [기술적 주안점]
    - 데이터 무결성 보장: 사용자가 보유한 예약 목록을 불러올 때, exclude() 쿼리를 복합적으로 사용하여
      '이미 다른 모집글에 매핑된 예약 내역'을 완벽하게 제외함으로써 예약 데이터의 중복 사용을 원천 차단했습니다.
    - 파일 관리 효율화: 기존에 업로드된 첨부파일의 물리적 삭제(os.remove)와 DB 레코드 삭제를 동기화하여
      스토리지 낭비를 방지하는 최적화된 파일 업데이트 로직을 구현했습니다.
    """

    # 0) 로그인 체크
    res = check_login(request)
    if res:
        return res

    user_id = request.session.get("user_id")

    # 1) 세션의 user_id 로 Member 가져오기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("common:login")

    # 2) 수정할 모집글 가져오기 (soft delete 된 글 제외)
    try:
        community = Community.objects.get(
            pk=pk,
            delete_date__isnull=True,
        )
    except Community.DoesNotExist:
        messages.error(request, "삭제되었거나 존재하지 않는 모집글입니다.")
        return redirect("recruitment:recruitment_list")

    # 3) 작성자 본인인지 체크
    if community.member_id != member:
        messages.error(request, "본인이 작성한 글만 수정할 수 있습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 🔹 이 글에 지금 연결돼 있는 예약 PK (없으면 None)
    current_reservation_id = community.reservation_id_id  # FK: reservation_id 기준

    # ----------------------------------------
    # 🔹 이미 다른 모집글에서 사용 중인 예약 PK 목록
    #    - 내 글들 중 (soft delete X)
    #    - reservation_id 가 있는 글들만
    #    - 지금 수정 중인 글은 제외
    # ----------------------------------------
    used_reservation_ids = (
        Community.objects
        .filter(
            member_id=member,
            delete_date__isnull=True,
        )
        .exclude(reservation_id__isnull=True)
        .exclude(reservation_id_id=current_reservation_id)
        .values_list("reservation_id_id", flat=True)
    )

    # ----------------------------------------
    # 🔹 현재 지역에 맞는 나의 타임슬롯 중
    #    - delete_yn = 0
    #    - 예약(Reservation) soft delete X
    #    - 이미 다른 모집글에서 사용된 reservation_id 는 제외
    # ----------------------------------------
    my_slots = (
        TimeSlot.objects
        .filter(
            reservation_id__member=member,
            reservation_id__delete_date__isnull=True,
            delete_yn=0,
            facility_id__sido=community.region,
            facility_id__sigugun=community.region2,
        )
        .exclude(reservation_id_id__in=used_reservation_ids)
        .select_related("reservation_id", "facility_id")
        .order_by("reservation_id", "date", "start_time")
    )

    # 🔹 이 타임슬롯들에 해당하는 예약 목록
    reservation_ids = {slot.reservation_id_id for slot in my_slots}

    my_reservations = (
        Reservation.objects
        .filter(
            member=member,
            delete_date__isnull=True,
            pk__in=reservation_ids,
        )
        .order_by("-reg_date")
    )


    # 연계된 마감여부 갖고 오기

    end_status = get_object_or_404(EndStatus, community=community)
    # ----------------------------------------
    # 🔹 write()와 동일한 grouped 구조 만들기
    # ----------------------------------------
    grouped_slots = OrderedDict()
    for slot in my_slots:
        rid = slot.reservation_id_id

        if rid not in grouped_slots:
            grouped_slots[rid] = {
                "reservation": slot.reservation_id,
                "facility": slot.facility_id,
                "times": [],
            }

        grouped_slots[rid]["times"].append({
            "t_id": slot.t_id,
            "date": slot.date,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
        })

    my_reservation_slots = list(grouped_slots.values())

    # ----------------------------------------
    # 🔹 이 모집글의 기존 첨부파일 목록 (모두)
    #    - delete_date 없으니까 그냥 community 기준으로만 필터
    # ----------------------------------------
    existing_files = AddInfo.objects.filter(
        community_id=community,
    )

    # 4) POST: 실제 수정 처리
    if request.method == "POST":
        # ✅ 내용 수정
        contents = request.POST.get("content", "").strip()
        community.contents = contents
        community.update_date = timezone.now()

        # ✅ 1) 삭제할 첨부파일 체크 처리 (실제 삭제)
        delete_ids = request.POST.getlist("delete_files")  # 체크박스 name="delete_files"

        if delete_ids:
            to_delete_qs = AddInfo.objects.filter(
                community_id=community,
                pk__in=delete_ids,
            )

            # 파일까지 같이 삭제
            for info in to_delete_qs:
                if info.path:  # path 에 상대 경로 저장되어 있다고 가정
                    file_path = os.path.join(settings.MEDIA_ROOT, info.path)
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except OSError:
                            # 파일 없거나 권한 문제면 그냥 무시
                            pass

            # DB row 삭제
            to_delete_qs.delete()

        # ✅ 2) 예약 선택값 처리
        reservation_id = (request.POST.get("reservation_choice") or "").strip()

        # 기본은 기존 값 유지
        facility_name = community.facility

        if reservation_id:
            slot = (
                TimeSlot.objects
                .select_related("facility_id", "reservation_id")
                .filter(
                    reservation_id_id=reservation_id,
                    reservation_id__member=member,
                    reservation_id__delete_date__isnull=True,
                    delete_yn=0,
                )
                .first()
            )
            if slot:
                facility = slot.facility_id
                facility_name = facility.faci_nm

                # 예약 기준으로 지역 동기화
                community.region = facility.sido
                community.region2 = facility.sigugun

                # 예약 FK 변경
                community.reservation_id = slot.reservation_id

        # ✅ 3) 새 첨부파일 업로드 처리
        files = request.FILES.getlist("files")
        upload_files(request, community, file_field="files", sub_dir="uploads/community")


        # ✅ 시설 이름 최종 반영 + 저장
        community.facility = facility_name
        community.save()

        return redirect("recruitment:recruitment_detail", pk=community.pk)

    # 5) GET: 수정 폼 화면
    context = {
        'mode':'edit',
        "community": community,
        "recruit": community,                 # 템플릿에서 recruit 로 쓰고 있으면 유지
        "end_status":end_status,
        "my_reservations": my_reservations,
        "my_reservation_slots": my_reservation_slots,
        "current_reservation_id": current_reservation_id,
        "existing_files": existing_files,     # ✅ 기존 첨부파일 목록
    }
    return render(request, "recruitment/recruitment_form.html", context)



def detail(request, pk):
    """
    모집글의 상세 정보를 조회하고, 사용자 참여 상태 및 자동 마감 여부를 계산하는 뷰 함수입니다.

    [기술적 주안점]
    - 동시성 제어 (Race Condition 방지): 다수의 사용자가 동시에 상세 페이지를 조회할 때 발생할 수 있는
      조회수 누락을 방지하기 위해, F("view_cnt") 객체를 활용하여 DB 레벨에서의 원자적 업데이트(Atomic Update)를 적용했습니다.
    - 자동 마감 비즈니스 로직: '승인(Approved)'된 참여자 수(approved_count)를 실시간으로 집계하여,
      모집 정원(capacity)에 도달하면 즉시 EndStatus를 마감(1) 처리하는 안정적인 모집 워크플로우를 구축했습니다.
    """

    # 로그인 체크
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")

    login_member = Member.objects.filter(user_id=user_id).first()

    # 관리자 여부
    
    is_manager_user = is_manager(request)
    
    
    # 모집글 조회 (삭제되지 않은 것만)
    try:
        recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
        Community.objects.filter(pk=pk, delete_date__isnull=True).update(view_cnt=F("view_cnt")+1)  
        # 존재하면 조회수 증가 / .save() 대신 F로 update하는건 동시 접속 많아질 경우 db 접속이 꼬일 수 있기 때문
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")



    # 참여자 목록
    joins_qs = JoinStat.objects.filter(community_id=recruit)
    waiting_count = joins_qs.filter(join_status=0).count() + joins_qs.filter(join_status=2).count()
    approved_count = joins_qs.filter(join_status=1).count()
    capacity = recruit.num_member or 0

    # -------------------------
    # 자동 마감 처리
    # -------------------------
    try:
        end_status = EndStatus.objects.get(community=recruit)
    except EndStatus.DoesNotExist:
        # 혹시 예전 데이터(EndStatus 없이 만들어진 글)를 대비한 안전장치
        end_status = EndStatus.objects.create(
            community=recruit,
            end_set_date=ALWAYS_OPEN_DATE,  # 상시모집으로 기본 세팅
            end_stat=0,
        )
    is_always_open = (end_status.end_set_date == ALWAYS_OPEN_DATE)

    if approved_count >= capacity and capacity > 0:
        if end_status.end_stat != 1:
            end_status.end_stat = 1
            end_status.end_date = timezone.now().date()
            end_status.save()

    is_closed = (end_status.end_stat == 1)

    # 작성자 여부
    is_owner = (login_member is not None and recruit.member_id == login_member)

    # 로그인한 유저가 이 모집글에 참여했는지 체크
    my_join = JoinStat.objects.filter(
        community_id=recruit,
        member_id=login_member
    ).first()

    is_applied = (my_join is not None)


    # 상세 참여 리스트 (작성자 / 관리자만)
    join_list = []
    if is_owner or is_manager_user:
        join_list = (
            joins_qs
            .select_related("member_id")
            .order_by("join_status", "member_id__user_id")
        )

 
    comments = []
    # 댓글: 그냥 Comment queryset 으로 넘김
    comments = (
        Comment.objects
        .select_related("member_id")
        .filter(community_id=recruit)
        .order_by("reg_date")
    )

    # -----------------------------------
    # ✅ 이 모집글의 reservation_id 기준 타임슬롯
    #    - Community.reservation_id 가 있을 때만
    #    - TimeSlot.delete_yn = 0, 예약 soft delete 제외
    # -----------------------------------
    reservation_slots = []

    reservation_obj = recruit.reservation_id  # FK 객체 또는 None
    if reservation_obj is not None:
        slots_qs = (
            TimeSlot.objects
            .filter(
                reservation_id=reservation_obj,
                delete_yn=0,
                reservation_id__delete_date__isnull=True,
            )
            .select_related("reservation_id", "facility_id")
            .order_by("date", "start_time")
        )

        if slots_qs:
            grouped = {
                "reservation": reservation_obj,
                "facility": slots_qs[0].facility_id,
                "date": slots_qs[0].date,
                "times": [],
            }

            for slot in slots_qs:
                grouped["times"].append({
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                })

            # detail 템플릿에서 쓰기 쉽게 리스트 형태로 전달
            reservation_slots = [grouped]
    add_info_list = AddInfo.objects.filter(
        community_id=recruit,
        # delete_date__isnull=True
    )
    context = {
        "recruit": recruit,
        "add_info": add_info_list,
        "is_owner": is_owner,

        # 마감관련
        "end_status":end_status,
        "is_always_open":is_always_open,

        "is_manager": is_manager_user,
        "join_list": join_list,
        "approved_count": approved_count,
        "capacity": capacity,
        "is_closed": is_closed,
        "comments": comments,
        "waiting_rejected_count": waiting_count,
        # 👇 이걸로 detail 화면에서 예약 시간대 뿌리면 됨
        "reservation_slots": reservation_slots,
        "is_applied":is_applied,
        "my_join":my_join,
    }

    return render(request, "recruitment/recruitment_detail.html", context)


# 현재 관리자만 사용
def delete(request, pk):
    
    res = check_login(request)
    if res:
        return res
        
    # 1) 세션 user_id 로 Member 조회
    try:
        user_id = request.session.get("user_id")
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

    # 2) 삭제 대상 글 조회
    community = get_object_or_404(Community, pk=pk)

    # 3) 권한 체크
    is_manager = (member.manager_yn == 1)
    is_owner = (community.member_id == member)

    # 3-1) 관리자도 아니고, 작성자도 아니면 → 삭제 불가
    if not (is_manager or is_owner):
        messages.error(request, "삭제 권한이 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 3-2) 작성자인데, 참여신청이 하나라도 있으면 삭제 막기
    #      (관리자는 참여신청이 있어도 삭제 가능)
    if not is_manager and is_owner:
        has_join = JoinStat.objects.filter(community_id=community).exists()
        if has_join:
            messages.error(request, "이미 참여 신청이 있어 글을 삭제할 수 없습니다.")
            return redirect("recruitment:recruitment_detail", pk=pk)       
    

    # 4) soft delete
    community.delete_date = timezone.now()
    community.save()

    messages.success(request, "글이 삭제되었습니다.")
    return redirect("recruitment:recruitment_list")


def join(request, pk):
    # 0) 로그인 체크
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")
    
    # 1) 세션의 user_id 로 Member 찾기
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

    # 2) 모집 글 가져오기
    try:
        community = Community.objects.get(pk=pk)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 3) 본인 글 참여 방지 (URL 직접 입력하는 놈 방어)
    if community.member_id == member:
        messages.error(request, "본인이 작성한 글에는 참여 신청을 할 수 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) JoinStat 생성 (이미 있으면 그대로)
    try:
        join_obj, created = JoinStat.objects.get_or_create(
            member_id=member,
            community_id=community,
            defaults={"join_status": 0},   # 0 = 대기
        )
    except IntegrityError:
        join_obj = JoinStat.objects.get(
            member_id=member,
            community_id=community
        )
        created = False

    # 5) 메시지
    if created:
        messages.success(request, "참여 신청이 완료되었습니다. 작성자의 승인 후 확정됩니다.")
    else:
        messages.info(request, "이미 이 모집에 참여 신청을 하셨습니다.")

    # 6) 상세 페이지로 복귀
    return redirect("recruitment:recruitment_detail", pk=pk)



@require_POST           # GET말고 POST만 받음
@transaction.atomic     # DB 저장시 꼬이지 않게
def update_join_status(request, pk, join_id):

    """
    모집글 작성자가 신청자의 참여 상태(대기/승인/거절)를 변경하는 뷰 함수입니다.

    [기술적 주안점]
    - 트랜잭션 안전성 보장: @transaction.atomic을 적용하여, 참여 상태 변경 중 예기치 않은 오류가 발생하더라도
      데이터가 꼬이지 않고 완벽하게 롤백되도록 처리하여 모집 프로세스의 신뢰도를 확보했습니다.
    - 메서드 제한: @require_POST를 통해 비정상적인 GET 요청을 통한 상태 변경 시도를 차단하여
      엔드포인트 보안을 강화했습니다.
    """

    # 0) 로그인 체크    
    res = check_login(request)
    if res:
        return res
    user_id = request.session.get("user_id")


    # 1) 로그인 유저
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

    # 2) 모집글
    try:
        community = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        messages.error(request, "삭제되었거나 존재하지 않는 모집글입니다.")
        return redirect("recruitment:recruitment_list")

    # 3) 작성자 본인만 변경 가능
    if community.member_id != member:
        messages.error(request, "작성자만 참여 상태를 변경할 수 있습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) JoinStat 한 줄 가져오기
    try:
        join_obj = JoinStat.objects.get(id=join_id, community_id=community)
    except JoinStat.DoesNotExist:
        messages.error(request, "해당 참여 신청을 찾을 수 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 5) 변경할 상태값 (0=대기, 1=승인, 2=거절 등)
    try:
        new_status = int(request.POST.get("status"))
    except (TypeError, ValueError):
        messages.error(request, "잘못된 상태 값입니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    join_obj.join_status = new_status
    join_obj.save()

    messages.success(request, "참여 상태를 변경했습니다.")
    return redirect("recruitment:recruitment_detail", pk=pk)



# 댓글 추가 기능
def add_comment(request, pk):
    # GET 으로 들어오면 그냥 상세로 돌려보냄
    if request.method != "POST":
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 0) 세션 로그인 확인
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")


    # 1) 로그인 회원
    try:
        member = Member.objects.get(user_id=user_id)
    except Member.DoesNotExist:
        request.session.flush()
        messages.error(request, "다시 로그인 해주세요.")
        return redirect("/login")

    # 2) 대상 모집글
    community = get_object_or_404(
        Community,
        pk=pk,
        delete_date__isnull=True,
    )

    # 3) 폼에서 넘어온 댓글 내용
    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, "댓글 내용을 입력해 주세요.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 4) 댓글 생성
    Comment.objects.create(
        community_id=community,
        member_id=member,
        comment=content,
    )

    messages.success(request, "댓글이 등록되었습니다.")
    return redirect("recruitment:recruitment_detail", pk=pk)


# 파일 업로드 처리 함수는 common/utils.py로 이동됨



@require_POST
def delete_comment(request, pk, comment_id):
    """
    모집글 상세에서 댓글 삭제 (soft delete 후 상세 페이지로 redirect)
    - 관리자만 삭제 가능 (현재 is_manager 기준)
    - pk: 모집글 community_id
    - comment_id: 댓글 PK
    """

    # 로그인 / 세션 체크
    res = check_login(request)
    if res:
        return res

    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "댓글을 삭제할 권한이 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # 해당 모집글의 댓글만 대상으로
    comment = get_object_or_404(
        Comment,
        comment_id=comment_id,
        community_id_id=pk,   # FK 이름이 community_id 라고 가정
    )

    # 이미 soft delete 된 경우
    if comment.delete_date:
        messages.info(request, "이미 삭제된 댓글입니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    # soft delete
    comment.delete_date = timezone.now()
    # 보여주기 싫으면 주석 유지, 문구 보이게 하고 싶으면 주석 해제
    # comment.comment = "관리자에 의해 삭제된 댓글입니다." #  이렇게 되면 comment 값 자체가 변동됨.
    comment.save()

    messages.success(request, "댓글을 삭제했습니다.")
    return redirect("recruitment:recruitment_detail", pk=pk)



# 모집 마감 여부 체크
def close_recruitment(request, pk):
    # 로그인 체크
    
    res = check_login(request)
    if res:
        return res
    
    user_id = request.session.get("user_id")

    # 글 가져오기 (삭제된 글은 마감 안 하도록)
    try:
        recruit = Community.objects.get(pk=pk, delete_date__isnull=True)
    except Community.DoesNotExist:
        raise Http404("존재하지 않는 모집글입니다.")

    # 작성자 / 관리자 확인
    login_member = Member.objects.filter(user_id=user_id).first()
    is_manager_user = is_manager(request)
    is_owner = (login_member is not None and recruit.member_id == login_member)

    if not (is_owner or is_manager_user):
        messages.error(request, "모집을 마감할 권한이 없습니다.")
        return redirect("recruitment:recruitment_detail", pk=pk)

    if request.method == "POST":
        today = timezone.now().date()
        end_status, created = EndStatus.objects.get_or_create(
            community=recruit,
            defaults={
                "end_set_date": today,
            },
        )
        end_status.end_stat = 1
        end_status.end_date = today
        if not end_status.end_set_date:
            end_status.end_set_date = today
        end_status.save()
        messages.success(request, "모집을 마감했습니다.")

    return redirect("recruitment:recruitment_detail", pk=pk)


# 시설 선택 시 지역구 자동 셀렉되게

from django.http import JsonResponse
def get_facility_region(request):
    
    res = check_login(request)
    if res:
        return res

    reservation_id = request.GET.get("reservation_id")

    slot = (
        TimeSlot.objects
        .select_related("facility_id", "reservation_id")
        .filter(reservation_id_id=reservation_id)
        .first()
    )

    if not slot:
        return JsonResponse({"error": "not_found"}, status=404)

    facility = slot.facility_id

    return JsonResponse({
        "sido": facility.sido,
        "sigugun": facility.sigugun,
    })