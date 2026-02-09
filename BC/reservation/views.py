from django.shortcuts import render, get_object_or_404
from common.paging import pager
from .models import Reservation, TimeSlot
import json, random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware
from datetime import datetime
from facility.models import Facility, FacilityInfo
from reservation.models import Sports, Reservation
from member.models import Member
from .models import TimeSlot
from common.utils import check_login


# TODO: DB 연결 이후 FacilityInfo 모델에서 시설 정보 조회
# from facility.models import FacilityInfo

def reservation_list(request):
    # 종목불러오기
    #sports = Sports.objects.all()


    sports = (
        Facility.objects
        .filter(
            faci_gb_nm='공공',
            faci_cd__in=FacilityInfo.objects
                .filter(rs_posible=1)
                .values_list('facility_id', flat=True)
        )
        .values_list('ftype_nm', flat=True)
        .distinct()
        .order_by('ftype_nm')
    )

    # 시설불러오기
    
    #facilities = FacilityInfo.objects.all()
    facilities = FacilityInfo.objects.filter(rs_posible=1)
    
    sido = request.GET.get('sido')
    sigungu = request.GET.get('sigungu')
    keyword = request.GET.get('keyword')
    sport = request.GET.get('sport')

    if sido:
        facilities = facilities.filter(sido=sido)
    if sigungu:
        facilities = facilities.filter(sigugun=sigungu)
    if keyword:
        facilities = facilities.filter(faci_nm__icontains=keyword)
    
    if sport:
        faci_cds = Facility.objects.filter(
            ftype_nm__in=[sport]
        ).values_list('faci_cd', flat=True)

        facilities = facilities.filter(
            facility_id__in=faci_cds
        )
        #facilities = facilities.filter(faci_nm__icontains=sport)


    
 

    sports_list = []
    for s in sports:
        sports_list.append({
            "sName" : s
        })

    # 정렬 값 (기본값: 제목순)
    sort = request.GET.get("sort", "title")

    # 정렬 적용 (모델에 존재하는 필드만 사용)
    if sort == "title":
        facilities = facilities.order_by('faci_nm')
    elif sort == "views":
        facilities = facilities.order_by('-view_cnt')

    facility_list = []  # 빈 리스트 (DB 연결 후 교체)
    
    


    for f in facilities:
        facility_list.append({
            "id": f.facility_id,
            "name": f.faci_nm or "",
            "address": f.address,
            "sido": f.sido or "",
            "sigungu": f.sigugun or "",
            "phone": f.tel or "",
            "homepage": f.homepage or "",
            "viewCnt": f.view_cnt
        })

    # 페이지당 개수
    per_page = int(request.GET.get("per_page", 15))

    # 현재 페이지
    page = int(request.GET.get("page", 1))

    # 페이징 처리
    paging = pager(request, facility_list, per_page=per_page)
    page_obj = paging['page_obj']

 

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "sido" : sido,
        "sigungu" : sigungu,
        "page": page,
        "sort": sort,
        "block_range": paging['block_range'],
        "block_start": paging['block_start'],
        "block_end": paging['block_end'],
        "sportsList" : sports_list,
        "sport" : sport
    }

    return render(request, "reservation/reservation_list.html", context)


def reservation_detail(request, facility_id):
    # 로그인 체크 (서버 사이드에서 처리)
    res = check_login(request)
    if res:
        return res
    
    facility = get_object_or_404(FacilityInfo, facility_id=facility_id)

    # delete_yn = 0 인 시간만 예약 불가 처리
    time_slots = TimeSlot.objects.filter(
        facility_id=facility,
        delete_yn=0
    ).values("date", "start_time", "end_time")

    reserved_list = []
    for t in time_slots:
        reserved_list.append({
            "date": t["date"].strftime("%Y-%m-%d"),
            "start": t["start_time"],
            "end": t["end_time"]
        })

    return render(request, "reservation/reservation_detail.html", {
        "facility": facility,
        "reservation_time_json": json.dumps(facility.reservation_time),
        "reserved_json": json.dumps(reserved_list)
    })

@csrf_exempt
def reservation_save(request):
        # 로그인 체크
    res = check_login(request)
    if res:
        return res
    
    if request.method != "POST":
        return JsonResponse({"result": "error", "msg": "잘못된 요청"})

    data = json.loads(request.body)

    date = data.get("date")
    slots = data.get("slots")
    facility_code = data.get("facility_id")

    if not (date and slots and facility_code):
        return JsonResponse({"result": "error", "msg": "필수 데이터 누락"})

    try:
        facility = FacilityInfo.objects.get(facility_id=facility_code)
    except FacilityInfo.DoesNotExist:
        return JsonResponse({"result": "error", "msg": "시설을 찾을 수 없습니다."})

    # 날짜 파싱 및 요일별 요금 확인
    try:
        res_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"result": "error", "msg": "잘못된 날짜 형식"})

    day_key = res_date.strftime("%A").lower()
    day_info = (facility.reservation_time or {}).get(day_key, {})
    if not day_info.get("active"):
        return JsonResponse({"result": "error", "msg": "해당 요일은 예약 불가합니다."})

    price_per_slot = int(day_info.get("payment") or 0)
    total_payment = price_per_slot * len(slots)

    # 예약 생성
    reservation_num = str(random.randint(10000000, 99999999))
    reservation = Reservation.objects.create(
        reservation_num=reservation_num,
        member=Member.objects.get(user_id=request.session["user_id"]),
        payment=total_payment
    )

    for slot in slots:
        start = slot["start"]
        end = slot["end"]

        TimeSlot.objects.create(
            facility_id=facility,
            date=res_date,
            start_time=start,
            end_time=end,
            reservation_id=reservation,
            delete_yn=0
        )

    return JsonResponse({"result": "ok", "payment": total_payment})
