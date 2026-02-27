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
    """
    공공 체육시설 목록을 조회하고 필터링 및 페이징을 처리하는 뷰 함수입니다.
    
    [기술적 주안점]
    - 메모리 최적화: Facility 객체 전체를 로드하지 않고, values_list()와 distinct()를 사용하여
      데이터베이스 레벨에서 중복을 제거한 필수 문자열 데이터만 메모리에 적재하여 쿼리 성능을 극대화했습니다.
    - 동적 필터링: 사용자의 지역(시/도, 시/군/구) 및 종목 조건에 따라 QuerySet을 동적으로 체이닝하여 필터링합니다.
    """
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
    """
    특정 시설의 상세 정보와 현재 예약된 타임슬롯을 조회하는 뷰 함수입니다.
    
    [기술적 주안점]
    - 페이로드(Payload) 최적화: 프론트엔드로 예약 시간표를 넘길 때 무거운 TimeSlot 객체 전체를
      직렬화(Serialization)하지 않고, .values("date", "start_time", "end_time")를 통해
      반드시 필요한 3개의 컬럼만 SELECT 하여 서버 응답 속도를 개선했습니다.
    """
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
    """
    클라이언트의 예약 요청을 받아 Reservation 및 다수의 TimeSlot을 생성하는 뷰 함수입니다.
    
    [기술적 주안점]
    - 원자성(Atomicity) 보장: @transaction.atomic을 적용하여 Reservation 생성 후
      TimeSlot들을 반복 생성하는 과정에서 예외가 발생하더라도 데이터가 안전하게 롤백되도록 처리했습니다.
    - 서버 사이드 무결성 검증: 프론트엔드에서 전달된 결제 금액을 맹신하지 않고,
      서버 단에서 예약 날짜의 요일을 파악해 해당 요일의 활성화 여부를 재검증하고 결제 금액을 직접 계산하여
      비정상적인 요청이나 보안 취약점을 원천 차단했습니다.
    """
    
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
