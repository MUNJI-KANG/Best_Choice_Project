import traceback
import os
import json



from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse

# 제거예정
from django.views.decorators.csrf import csrf_exempt

from common.utils import save_encoded_image, delete_selected_files, is_manager, upload_files
from common.models import Comment, AddInfo

from reservation.models import Reservation, TimeSlot

from common.paging import pager

from facility.models import Facility, FacilityInfo
from facility.utils import build_facility_queryset
from reservation.models import Sports



# 시설 추가
def facility(request):
    # -------------------------------
    # 관리자 권한 체크
    # -------------------------------
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect("manager:manager_login")

    # -------------------------------
    # GET 파라미터
    # -------------------------------
    cp_nm = request.GET.get("sido", "")
    cpb_nm = request.GET.get("sigungu", "")
    keyword = request.GET.get("keyword", "")
    apply_sports = request.GET.get("apply_sports", "")
    per_page = int(request.GET.get("per_page", 15))

    # -------------------------------
    # 기본 Facility queryset
    # -------------------------------
    queryset = build_facility_queryset(
        cp_nm=cp_nm or None,
        cpb_nm=cpb_nm or None,
        keyword=keyword or None,
        public_only=True,
        normal_only=False,        # 관리자 → 상태 무관
        exclude_registered=True,  # 관리자 → 이미 등록된 시설 제외
    )

    # -------------------------------
    # 종목 목록 (Facility.ftype_nm 기준)
    # -------------------------------
    all_sports = (
        Facility.objects
        .filter(faci_gb_nm='공공')
        .values_list('ftype_nm', flat=True)
        .distinct()
        .order_by('ftype_nm')
    )

    # -------------------------------
    # 선택된 종목 (세션)
    # -------------------------------
    selected_sports = request.session.get("selected_sports", [])
    selected_sports = [
        s.strip()
        for s in selected_sports
        if isinstance(s, str) and s.strip()
    ]
    # -------------------------------
    # 종목 필터 적용 (IN ONLY)
    # ※ 공공 조건은 build_facility_queryset에서 이미 처리됨
    # -------------------------------
    if apply_sports and selected_sports:
        queryset = queryset.filter(
            ftype_nm__in=selected_sports
        )
    # -------------------------------
    # 페이징
    # -------------------------------
    paging = pager(request, queryset, per_page=per_page)
    page_obj = paging["page_obj"]

    start_index = (page_obj.number - 1) * per_page

    facility_page = [
        {
            "id": item.id,
            "name": item.faci_nm,
            "address": item.faci_road_addr or item.faci_addr,
            "row_no": start_index + idx + 1,
            "faci_stat_nm": item.faci_stat_nm,
        }
        for idx, item in enumerate(page_obj.object_list)
    ]

    # -------------------------------
    # sports_json (팝업용)
    # -------------------------------
    sports_json = json.dumps(
        [
            {
                "id": idx + 1,          # UI용 순번
                "s_name": name,         # ftype_nm
                "selected": name in selected_sports,
            }
            for idx, name in enumerate(all_sports)
        ],
        ensure_ascii=False
    )

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "sido": cp_nm,
        "sigungu": cpb_nm,
        "keyword": keyword,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "sports_json": sports_json,
        "block_range": paging["block_range"],
        "block_start": paging["block_start"],
        "block_end": paging["block_end"],
        "paginator": paging["paginator"],
        "apply_sports": apply_sports,
    }

    return render(request, "manager/facility_add_manager.html", context)


# 종목 추가
def add_sport(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()

        if not name:
            return JsonResponse({"status": "error", "message": "종목명을 입력하세요."})

        # 중복 체크
        if Sports.objects.filter(s_name=name).exists():
            return JsonResponse({"status": "error", "message": "이미 존재하는 종목입니다."})

        sport = Sports.objects.create(s_name=name)

        return JsonResponse({
            "status": "success",
            "id": sport.sports_id,
            "name": sport.s_name
        })

    return JsonResponse({"status": "error", "message": "Invalid request"})


# 선택된 종목 저장 (세션에 저장)
def save_selected_sports(request):
    names = request.POST.getlist("names[]")

    selected_sports = [
        n.strip()
        for n in names
        if isinstance(n, str) and n.strip()
    ]

    request.session["selected_sports"] = selected_sports
    request.session.modified = True

    return JsonResponse({
        "status": "success",
        "count": len(selected_sports),
    })


# 종목 삭제 (DB 삭제)
def sport_delete(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)

    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])

        if not ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})

        Sports.objects.filter(sports_id__in=ids).delete()

        return JsonResponse({"status": "ok", "deleted": ids})

    except Exception as e:
        return JsonResponse({"status": "error", "msg": str(e)})


# 시설등록(insert)
def facility_register(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST만 가능"}, status=405)

    try:
        ids = request.POST.getlist("ids[]", [])

        if not ids:
            return JsonResponse({"status": "error", "message": "선택된 시설이 없습니다."})

        facilities = Facility.objects.filter(id__in=ids)

        count = 0
        for fac in facilities:
            FacilityInfo.objects.create(
                facility_id = fac.faci_cd or "",
                faci_nm=fac.faci_nm or "",
                address=fac.faci_road_addr or "",
                sido = fac.cp_nm or "",
                faci_gb_nm = fac.faci_gb_nm or "",
                sigugun = fac.cpb_nm or "",
                tel=fac.faci_tel_no or "",
                homepage=fac.faci_homepage or "",
                photo=None,
                reservation_time=None,
                faci_stat_nm = fac.faci_stat_nm or "",
            )
            count += 1

        return JsonResponse({"status": "success", "count": count})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "message": str(e)})


# 시설관리
def facility_list(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    # 필터 파라미터
    sido = request.GET.get("sido", "")
    sigungu = request.GET.get("sigungu", "")
    keyword = request.GET.get("keyword", "")
    per_page = int(request.GET.get("per_page", 15))
    rsPosible = request.GET.get("rsPosible","")

    queryset = FacilityInfo.objects.all()
    # 시설 api 정보
    if rsPosible == '1' :
        queryset = queryset.order_by('-rs_posible','-reg_date')
    elif rsPosible == '0' :
        queryset = queryset.order_by('rs_posible','-reg_date')
    else :
        queryset = queryset.order_by('-reg_date')

    if sido:
        queryset = queryset.filter(sido__icontains=sido)

    if sigungu:
        queryset = queryset.filter(sigugun__icontains=sigungu)

    if keyword:
        queryset = queryset.filter(faci_nm__icontains=keyword)


    paging = pager(request, queryset, per_page=per_page)
    page_obj = paging['page_obj']

 
    start_index = (page_obj.number - 1) * per_page
    facility_page = []
    
    # 오늘 날짜
    today = timezone.now().date()

    for idx, item in enumerate(page_obj.object_list):
        # 금일 활성 예약: 오늘 날짜 기준으로 예약이 발생한 건 수 (Reservation의 reg_date가 오늘)
        # TimeSlot을 통해 해당 시설의 예약을 찾고, Reservation의 reg_date가 오늘인 것
        today_reservations = Reservation.objects.filter(
            timeslot__facility_id=item,
            reg_date__date=today,
            delete_yn=0
        ).distinct().count()
        
        # 누적 예약: 오늘까지 누적된 예약 건 수, 취소된 건 제외 (delete_yn=0)
        total_reservations = Reservation.objects.filter(
            timeslot__facility_id=item,
            reg_date__date__lte=today,
            delete_yn=0
        ).distinct().count()
        
        facility_page.append({
            "id": item.id,
            "name": item.faci_nm,
            "address": item.address,
            "row_no": start_index + idx + 1,
            "facilityCd": item.facility_id,
            "today_count": today_reservations,
            "total_count": total_reservations,
            "rsPosible" : item.rs_posible
        })

    context = {
        "page_obj": paging['page_obj'],
        "per_page": per_page,
        "sido": sido,
        "sigungu": sigungu,
        "keyword": keyword,
        "rsPosible": rsPosible,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "block_range": paging['block_range'],
    }

    return render(request, "manager/facility_list_manager.html", context)


# 시설상세보기 
def facility_detail(request, id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    facilityInfo = get_object_or_404(FacilityInfo, facility_id=id)
    facility = get_object_or_404(Facility,faci_cd=id )

    # 요일 한국어 매핑 + 순서 정의
    DAY_ORDER = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

    KOREAN_DAYS = {
        "monday": "월요일",
        "tuesday": "화요일",
        "wednesday": "수요일",
        "thursday": "목요일",
        "friday": "금요일",
        "saturday": "토요일",
        "sunday": "일요일",
    }

    # reservation_time 정렬
    reservation_list = []
    rt = facilityInfo.reservation_time or {}

    for day in DAY_ORDER:  # 👉 월요일부터 반복
        info = rt.get(day, {})
        reservation_list.append({
            "day_kr": KOREAN_DAYS[day],
            "active": info.get("active", False),
            "open": info.get("open"),
            "close": info.get("close"),
            "interval": info.get("interval"),
            "payment" : info.get("payment"),
        })


    comment_objs = Comment.objects.select_related("member_id").filter(
        facility=id
    ).order_by("reg_date")

    comments = []
    for comment_obj in comment_objs:
        comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
        comment_is_admin = comment_obj.member_id.manager_yn == 1 if comment_obj.member_id else False
        is_deleted = comment_obj.delete_date is not None
        comment = "관리자에 의해 삭제된 댓글입니다." if comment_obj.delete_date else comment_obj.comment
        
        comments.append({
            'comment_id': comment_obj.comment_id,
            'comment': comment,
            'author': comment_author,
            'is_admin': comment_is_admin,
            'reg_date': comment_obj.reg_date,
            'is_deleted': is_deleted,
            
        })

    # 첨부파일
    files = AddInfo.objects.filter(facility_id=facilityInfo.id)

    downloadable_files = [
        f for f in files 
        if not f.encoded_name.lower().endswith(('.jpg','.jpeg','.png','.gif','.bmp','.webp'))
    ]


    context = {
        "facilityInfo": facilityInfo,
        "facility" : facility,
        "comments" : comments,
        "reservation_list": reservation_list,
        "files":files,
        "downloadable_files": downloadable_files,
    }
    return render(request, "manager/facility_detail.html", context)


# 시설수정
def facility_modify(request, id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    info = get_object_or_404(FacilityInfo, id=id)

    # -----------------------------
    # GET — 수정 페이지
    # -----------------------------
    if request.method == "GET":

        time_json = json.dumps(info.reservation_time, ensure_ascii=False) if info.reservation_time else "{}"

        # ✔ AddInfo는 FK → facility_id = info.id
        files = AddInfo.objects.filter(facility_id=info.id)

        return render(request, "manager/facility_write.html", {
            "info": info,
            "files": files,
            "time_json": time_json
        })

    # -----------------------------
    # POST — 실제 저장
    # -----------------------------
    info.tel = request.POST.get("tel", "")
    info.homepage = request.POST.get("homepage", "")
    rs_posible = 1 if request.POST.get("rs_posible") else 0
    info.rs_posible = rs_posible
    # 예약 JSON 파싱
    raw_time = request.POST.get("reservation_time", "{}")
    try:
        info.reservation_time = json.loads(raw_time)
    except:
        info.reservation_time = {}

    info.save()

    # 1) 대표 이미지 저장
    save_encoded_image(
        request=request,
        instance=info,
        field_name="photo",
        sub_dir="uploads/facility/photo",
        delete_old=True
    )

    # 2) 첨부파일 삭제
    delete_selected_files(request)

    # 3) 첨부파일 업로드 (FK 자동 저장됨)
    upload_files(
        request=request,
        instance=info,
        file_field="attachment_files",
        sub_dir="uploads/facility/files"
    )

    messages.success(request, "시설 정보가 수정되었습니다.")
    return redirect("manager:facility_detail", id=info.facility_id)

@csrf_exempt
def facility_delete(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)

    try:
        data = json.loads(request.body)
        ids = data.get("ids", [])

        if not ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목이 없습니다."})

        # 1) 삭제 대상 FacilityInfo
        infos = FacilityInfo.objects.filter(id__in=ids)

        # 2) 관련 AddInfo 가져오기 (PK 기반)
        files = AddInfo.objects.filter(facility_id__in=ids)

        # 2-1) 파일 삭제
        for f in files:
            if f.path:
                file_path = os.path.join(settings.MEDIA_ROOT, f.path)
                if os.path.exists(file_path):
                    os.remove(file_path)

        # 2-2) DB 레코드 삭제
        files.delete()

        # 3) FacilityInfo 대표이미지 삭제
        for info in infos:
            if info.photo and info.photo.name:
                photo_path = os.path.join(settings.MEDIA_ROOT, info.photo.name)
                if os.path.exists(photo_path):
                    os.remove(photo_path)

        # 4) FacilityInfo 삭제 (FK CASCADE로 AddInfo 자동삭제 가능)
        infos.delete()

        return JsonResponse({"status": "success", "deleted": ids})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"status": "error", "msg": str(e)})
    
def facility_file_download(request, file_id):
    """
    Facility 첨부파일 다운로드 (원본 파일명으로 저장되도록)
    """
    file_obj = get_object_or_404(AddInfo, add_info_id=file_id)

    # 실제 파일 경로 (AddInfo.path 안에 이미 encoded_name까지 들어있음)
    file_path = os.path.join(settings.MEDIA_ROOT, file_obj.path)

    if not os.path.exists(file_path):
        raise Http404("파일을 찾을 수 없습니다.")

    original_name = file_obj.file_name or os.path.basename(file_path)

    # ❗ Django 5.x 에서 제일 깔끔한 방법
    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,          # 무조건 다운로드
        filename=original_name,      # 여기 이름이 저장창에 뜸 (한글도 OK)
    )


def reservation_list_manager(request):
    """
    관리자용 예약 목록 페이지
    - facility_id: 시설 ID (선택)
    - type: 'today' (금일 활성 예약) 또는 'all' (누적 예약)
    """
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    # 필터 파라미터
    facility_id = request.GET.get("facility_id", "")
    reservation_type = request.GET.get("type", "all")  # 'today' or 'all'
    status = request.GET.get("status", "active")  # 'active' (예약완료) or 'cancelled' (예약취소)
    sort_by = request.GET.get("sort", "reg_date")  # 'reg_date' or 'timeslot'
    search_type = request.GET.get("search_type", "reservation_num")  # 'reservation_num', 'member_id', 'member_name'
    search_keyword = request.GET.get("search_keyword", "")
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    # 오늘 날짜
    today = timezone.now().date()
    
    # 예약 조회 (TimeSlot을 통해 시설과 연결)
    queryset = Reservation.objects.filter(
        timeslot__isnull=False
    ).select_related('member').distinct()
    
    # 상태 필터 (누적 예약일 때만 적용, 금일 활성 예약은 항상 예약완료만)
    if reservation_type == 'all':
        if status == 'cancelled':
            queryset = queryset.filter(delete_yn=1)  # 취소된 예약만
        else:
            queryset = queryset.filter(delete_yn=0)  # 예약완료만 (기본값)
    else:
        # 금일 활성 예약은 항상 예약완료만
        queryset = queryset.filter(delete_yn=0)
    
    # 시설 필터
    if facility_id:
        try:
            facility = FacilityInfo.objects.get(facility_id=facility_id)
            queryset = queryset.filter(timeslot__facility_id=facility)
        except FacilityInfo.DoesNotExist:
            messages.error(request, "시설을 찾을 수 없습니다.")
            return redirect('manager:facility_list')
    
    # 타입 필터 (금일 활성 예약)
    if reservation_type == 'today':
        queryset = queryset.filter(reg_date__date=today)
    
    # 누적 예약 (type='all')은 reg_date__date__lte=today 조건 추가
    else:
        queryset = queryset.filter(reg_date__date__lte=today)
    
    # 검색 필터
    if search_keyword:
        if search_type == 'reservation_num':
            queryset = queryset.filter(reservation_num__icontains=search_keyword)
        elif search_type == 'member_id':
            queryset = queryset.filter(member__user_id__icontains=search_keyword)
        elif search_type == 'member_name':
            queryset = queryset.filter(member__nickname__icontains=search_keyword)
    
    # 정렬
    if sort_by == 'timeslot':
        # 시설 예약 시간 순 (TimeSlot의 date, start_time 기준)
        queryset = queryset.order_by('timeslot__date', 'timeslot__start_time')
    else:
        # 예약 발생 시간 순 (reg_date 기준, default)
        queryset = queryset.order_by('-reg_date')
    
    # 페이징
    paging = pager(request, queryset, per_page=per_page)
    
    # 페이지 블록
    block_size = 10
    current_block = (page - 1) // block_size
    block_start = current_block * block_size + 1
    block_end = block_start + block_size - 1
    if block_end > paging['paginator'].num_pages:
        block_end = paging['paginator'].num_pages
    block_range = range(block_start, block_end + 1)
    
    # 데이터 변환
    start_index = (paging['page_obj'].number - 1) * per_page
    reservation_page = []
    
    for idx, reservation in enumerate(paging['page_obj'].object_list):
        # 시설 정보 가져오기 (TimeSlot을 통해) - 취소된 예약도 포함
        timeslots = TimeSlot.objects.filter(
            reservation_id=reservation
        ).select_related('facility_id').first()
        
        facility_name = timeslots.facility_id.faci_nm if timeslots and timeslots.facility_id else "미정"
        facility_id_val = timeslots.facility_id.facility_id if timeslots and timeslots.facility_id else ""
        
        # 종목 정보 가져오기 (Facility 모델에서)
        sport_type = "미정"
        if timeslots and timeslots.facility_id and timeslots.facility_id.facility_id:
            try:
                facility = Facility.objects.filter(faci_cd=timeslots.facility_id.facility_id).first()
                if facility and facility.ftype_nm:
                    sport_type = facility.ftype_nm
            except:
                pass
        
        # 이용 시간 정보 (모든 TimeSlot의 시간을 합쳐서 표시) - 취소된 예약도 포함
        time_slots = TimeSlot.objects.filter(
            reservation_id=reservation
        ).order_by('date', 'start_time')
        

        slot_list_for_json = []  # 팝업에서 사용할 상세 시간 정보
        earliest_date = None
        
        for ts in time_slots:
            date_str = ts.date.strftime('%Y-%m-%d') if ts.date else ""
            time_str = f"{ts.start_time}~{ts.end_time}" if ts.start_time and ts.end_time else ""

            
            # 가장 빠른 예약 날짜 확인 (체크박스 활성화 여부 판단용)
            if not earliest_date and ts.date:
                earliest_date = ts.date
            
            # 팝업용 상세 정보
            slot_list_for_json.append({
                "date": date_str,
                "start": ts.start_time,
                "end": ts.end_time,
                "is_cancelled": (ts.delete_yn == 1),
                "t_id": ts.t_id,
                "time_str":time_str,
            })
        
        
        # 오늘 날짜와 비교 (체크박스 활성화 여부)
        is_past = False
        if earliest_date and earliest_date < today:
            is_past = True
            # 예약 날짜가 지난 경우 자동으로 expire_yn 업데이트
            if reservation.expire_yn == 0:  # 아직 만료 처리되지 않은 경우만
                reservation.expire_yn = 1
                reservation.save(update_fields=['expire_yn'])
        
        # 회원 정보
        member_name = reservation.member.nickname if reservation.member else "알 수 없음"
        member_id = reservation.member.user_id if reservation.member else ""
        member_phone_num = reservation.member.phone_num if reservation.member else ""
        
        reservation_page.append({
            "id": reservation.reservation_id,
            "reservation_num": reservation.reservation_num,
            "member_name": member_name,
            "member_id": member_id,
            "member_phone_num": member_phone_num,
            "facility_name": facility_name,
            "facility_id": facility_id_val,
            "facility_address": timeslots.facility_id.address if timeslots and timeslots.facility_id else "",
            "facility_tel": timeslots.facility_id.tel if timeslots and timeslots.facility_id else "",
            "sport_type": sport_type,
            "slot_list": slot_list_for_json,  # 팝업에서 사용할 상세 시간 정보
            "reg_date": reservation.reg_date.strftime('%Y-%m-%d %H:%M') if reservation.reg_date else "",
            "delete_date": reservation.delete_date.strftime('%Y-%m-%d %H:%M') if reservation.delete_date else "",
            "delete_yn": reservation.delete_yn,  # 예약 상태 (0: 예약완료, 1: 취소)
            "is_past": is_past,  # 예약 날짜가 지났는지 여부
            "row_no": start_index + idx + 1,
        })
    
    # 시설 정보 (필터용)
    facility_info = None
    if facility_id:
        try:
            facility_info = FacilityInfo.objects.get(facility_id=facility_id)
        except FacilityInfo.DoesNotExist:
            pass
    
    context = {
        "page_obj": paging['page_obj'],
        "per_page": paging['per_page'],
        "facility_id": facility_id,
        "reservation_type": reservation_type,
        "status": status,
        "sort_by": sort_by,
        "search_type": search_type,
        "search_keyword": search_keyword,
        "facility_info": facility_info,
        "reservation_json": json.dumps(reservation_page, ensure_ascii=False),
        "block_range": block_range,
    }
    
    return render(request, "manager/reservation_list_manager.html", context)


@csrf_exempt
def manager_cancel_timeslot(request, reservation_num):
    """
    관리자용 예약 시간대 취소 API
    """
    # 관리자 권한 확인
    if not is_manager(request):
        return JsonResponse({"result": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    if request.method != "POST":
        return JsonResponse({"result": "error", "msg": "POST만 가능합니다."}, status=405)
    
    try:
        data = json.loads(request.body)
        slots = data.get("slots", [])
        
        reservation = Reservation.objects.get(reservation_num=reservation_num)
        
        # 예약 날짜가 지났는지 확인
        from django.utils import timezone
        today = timezone.now().date()
        
        # 예약된 모든 슬롯 중 가장 빠른 날짜 확인
        all_slots = TimeSlot.objects.filter(reservation_id=reservation, delete_yn=0)
        if all_slots.exists():
            earliest_date = min(slot.date for slot in all_slots if slot.date)
            if earliest_date and earliest_date < today:
                return JsonResponse({"result": "error", "msg": "예약 날짜가 지나 취소할 수 없습니다."})
        
        # 선택한 시간대 취소 처리
        for s in slots:
            TimeSlot.objects.filter(
                reservation_id=reservation,
                date=s["date"],
                start_time=s["start"],
                end_time=s["end"]
            ).update(delete_yn=1)
        
        # 남은 슬롯 집계
        remaining_slots = TimeSlot.objects.filter(reservation_id=reservation, delete_yn=0)
        
        # 모두 취소되었다면 예약도 취소 처리
        if not remaining_slots.exists():
            reservation.delete_yn = 1
            reservation.delete_date = timezone.now()
            reservation.payment = 0
            reservation.save()
            return JsonResponse({"result": "ok", "msg": "선택한 시간대가 취소되었습니다.", "payment": 0})
        
        # 남은 슬롯 기반으로 결제 금액 재계산
        facility = remaining_slots.first().facility_id
        rt = facility.reservation_time or {}
        
        total_payment = 0
        for slot in remaining_slots:
            day_key = slot.date.strftime("%A").lower()
            day_info = rt.get(day_key, {})
            price_per_slot = int(day_info.get("payment") or 0)
            total_payment += price_per_slot
        
        reservation.payment = total_payment
        reservation.save()
        
        return JsonResponse({
            "result": "ok",
            "msg": "선택한 시간대가 취소되었습니다.",
            "payment": total_payment
        })
        
    except Reservation.DoesNotExist:
        return JsonResponse({"result": "error", "msg": "예약을 찾을 수 없습니다."}, status=404)
    except Exception as e:
        import traceback
        print(f"[ERROR] 관리자 예약 취소 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"result": "error", "msg": "취소 실패"})
