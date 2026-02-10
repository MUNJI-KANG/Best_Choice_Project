from django.shortcuts import render, redirect
from common.paging import pager
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from datetime import datetime
import re
import json
from member.models import Member
from common.models import Comment
from recruitment.models import Community
from board.models import Article
from common.models import Comment
from recruitment.models import Community
from board.models import Article
from facility.models import FacilityInfo
from reservation.models import Reservation, TimeSlot
from common.utils import check_login


def info(request):
    # 로그인 체크
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")
    

    try:
        # DB에서 최신 회원 정보 가져오기 (캐시 무시)
        user = Member.objects.get(user_id=login_id)
        
        # 디버깅: 현재 DB 값 확인
        print("=" * 50)
        print("info 페이지 - 현재 DB 값")
        print(f"닉네임: {user.nickname}")
        print(f"전화번호: {user.phone_num}")
        print(f"주소1: {user.addr1}")
        print("=" * 50)

        # 템플릿으로 전달될 데이터
        context = {
            "name": user.name,
            "user_id": user.user_id,
            "nickname": user.nickname,
            "birthday": user.birthday,
            "email": user.email if hasattr(user, "email") else "",
            "phone_num": user.phone_num,
            "addr1": user.addr1,
            "addr2": user.addr2,
            "addr3": user.addr3 if hasattr(user, "addr3") else "",
        }

        return render(request, "member/info.html", context)
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')

PHONE_PATTERN = re.compile(r'^\d{3}-\d{4}-\d{4}$')

def edit(request):

    # 로그인 체크
    res = check_login(request)
    if res:
        return res
    
    login_id = request.session.get("user_id")
    
    if request.method == "POST":
        # AJAX 요청인지 확인
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        print("=" * 50)
        print("POST 요청 받음")
        print("AJAX 여부:", is_ajax)
        print("받은 데이터:", dict(request.POST))
        print("=" * 50)
        
        try:
            user = Member.objects.get(user_id=login_id)
            
            # 기존 값
            old_nickname = user.nickname
            old_phone = user.phone_num
            old_addr1 = user.addr1
            
            # 새 값
            new_nickname = request.POST.get('nickname', user.nickname)
            new_phone = request.POST.get('phone', user.phone_num)
            new_addr1 = request.POST.get('addr1', user.addr1)

            print(f"닉네임 변경: {old_nickname} -> {new_nickname}")
            print(f"전화번호 변경: {old_phone} -> {new_phone}")
            print(f"주소1 변경: {old_addr1} -> {new_addr1}")

            # -----------------------------
            # 전화번호 정규식 검증 (signup 동일)
            # -----------------------------
            if not PHONE_PATTERN.match(new_phone or ""):
                error_msg = "전화번호는 010-0000-0000 형식으로 입력해주세요."

                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg})
                
                messages.error(request, error_msg)
                return redirect('member:edit')

            # -----------------------------
            # 전화번호 중복 검사 (signup 동일)
            # -----------------------------
            if Member.objects.filter(phone_num=new_phone).exclude(user_id=login_id).exists():
                error_msg = "이미 등록된 전화번호입니다."

                if is_ajax:
                    return JsonResponse({'success': False, 'message': error_msg})

                messages.error(request, error_msg)
                return redirect('member:edit')
            
            # 값 업데이트
            user.nickname = new_nickname
            user.phone_num = new_phone
            
            # 주소 파싱
            from common.utils import parse_address
            import json
            
            address_data_str = request.POST.get('address_data', '')
            address_detail = request.POST.get('address_detail', '')
            
            if address_data_str:
                try:
                    address_data = json.loads(address_data_str)
                    addr1, addr2, addr3 = parse_address(address_data, address_detail)
                    user.addr1 = addr1
                    user.addr2 = addr2
                    user.addr3 = addr3
                except (json.JSONDecodeError, Exception) as e:
                    print(f"주소 파싱 오류: {e}")
                    user.addr1 = request.POST.get('addr1', user.addr1)
                    user.addr2 = request.POST.get('addr2', user.addr2)
                    user.addr3 = request.POST.get('addr3', user.addr3)
            else:
                user.addr1 = request.POST.get('addr1', user.addr1)
                user.addr2 = request.POST.get('addr2', user.addr2)
                user.addr3 = request.POST.get('addr3', user.addr3)

            if hasattr(user, 'email'):
                user.email = request.POST.get('email', user.email)
            
            # DB에 저장
            user.save()
            print("DB 저장 완료")

            user.refresh_from_db()
            print(f"저장 후 DB 닉네임: {user.nickname}")
            print(f"저장 후 DB 전화번호: {user.phone_num}")
            print(f"저장 후 DB 주소1: {user.addr1}")

            # 세션 업데이트
            request.session['nickname'] = user.nickname
            request.session.modified = True
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': '정보가 수정되었습니다.',
                    'data': {
                        'nickname': user.nickname,
                        'phone_num': user.phone_num,
                        'addr1': user.addr1,
                        'addr2': user.addr2,
                        'addr3': user.addr3,
                    }
                })
            else:
                messages.success(request, "정보가 수정되었습니다.")
                
                # 카카오 로그인 후 정보 수정 완료 시 원래 페이지로 리다이렉트
                profile_complete_next = request.session.pop('profile_complete_next', None)
                if profile_complete_next:
                    return redirect(profile_complete_next)
                
                return redirect('member:info')

        except Member.DoesNotExist:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '회원 정보를 찾을 수 없습니다.'
                }, status=400)
            else:
                messages.error(request, "회원 정보를 찾을 수 없습니다.")
                return redirect('member:info')
        except Exception as e:
            print("edit 오류:", e)
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '수정 중 오류가 발생했습니다.'
                }, status=500)
            else:
                messages.error(request, "수정 중 오류가 발생했습니다.")
                return redirect('member:info')
    
    # GET 요청
    try:
        user = Member.objects.get(user_id=login_id)
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('member:info')
    
    # 팝업 표시 플래그 확인
    show_modal = request.session.pop('show_profile_complete_modal', False)
    
    context = {
        "name": user.name,
        "user_id": user.user_id,
        "nickname": user.nickname,
        "birthday": user.birthday,
        "gender": user.gender,
        "email": user.email if hasattr(user, "email") else "",
        "phone_num": user.phone_num,
        "addr1": user.addr1 or '',
        "addr2": user.addr2 or '',
        "addr3": user.addr3 if hasattr(user, "addr3") else '',
        "show_profile_complete_modal": show_modal,  # 팝업 표시 여부
    }
    
    return render(request, 'member/info_edit.html', context)
def edit_password(request):
    # 로그인 체크
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")

    
    # AJAX 요청인지 확인
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if request.method == "POST":
        current_pw = request.POST.get('current_pw', '')
        new_pw = request.POST.get('new_pw', '')
        new_pw2 = request.POST.get('new_pw2', '')
        
        try:
            user = Member.objects.get(user_id=login_id)
            
            # 현재 비밀번호 확인
            if not check_password(current_pw, user.password):
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '현재 비밀번호가 일치하지 않습니다.'
                    }, status=400)
                else:
                    messages.error(request, "현재 비밀번호가 일치하지 않습니다.")
                    return render(request, 'member/info_edit_password.html')
            
            # 새 비밀번호와 확인 비밀번호 일치 확인
            if new_pw != new_pw2:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '새 비밀번호와 확인 비밀번호가 일치하지 않습니다.'
                    }, status=400)
                else:
                    messages.error(request, "새 비밀번호와 확인 비밀번호가 일치하지 않습니다.")
                    return render(request, 'member/info_edit_password.html')
            
            # 비밀번호 형식 검증 (signup과 동일한 패턴)
            PASSWORD_PATTERN = re.compile(
                r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=])[A-Za-z\d!@#$%^&*()_+\-=]{8,}$'
            )
            
            if not PASSWORD_PATTERN.match(new_pw):
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '비밀번호는 8자 이상, 영문 대소문자, 숫자, 특수문자를 포함해야 합니다.'
                    }, status=400)
                else:
                    messages.error(request, "비밀번호 형식이 올바르지 않습니다.")
                    return render(request, 'member/info_edit_password.html')
            
            # 현재 비밀번호와 새 비밀번호가 같은지 확인
            if check_password(new_pw, user.password):
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': '새 비밀번호는 현재 비밀번호와 다르게 설정해주세요.'
                    }, status=400)
                else:
                    messages.error(request, "새 비밀번호는 현재 비밀번호와 다르게 설정해주세요.")
                    return render(request, 'member/info_edit_password.html')
            
            # 비밀번호 변경
            old_password_hash = user.password
            user.password = make_password(new_pw)
            user.save()
            
            print("=" * 50)
            print("비밀번호 변경")
            print("기존 해시:", old_password_hash[:50] + "..." if len(old_password_hash) > 50 else old_password_hash)
            print("새 해시:", user.password[:50] + "..." if len(user.password) > 50 else user.password)
            print("=" * 50)
            
            # 저장 확인
            user.refresh_from_db()
            
            # 새 비밀번호로 로그인 가능한지 테스트
            test_result = check_password(new_pw, user.password)
            print(f"새 비밀번호 검증 결과: {test_result}")
            
            if not test_result:
                print("경고: 비밀번호 저장 후 검증 실패!")
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': '비밀번호가 변경되었습니다.'
                })
            else:
                messages.success(request, "비밀번호가 변경되었습니다.")
                return redirect('member:info')
                
        except Member.DoesNotExist:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '회원 정보를 찾을 수 없습니다.'
                }, status=400)
            else:
                messages.error(request, "회원 정보를 찾을 수 없습니다.")
                return redirect('member:info')
        except Exception as e:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': '비밀번호 변경 중 오류가 발생했습니다.'
                }, status=500)
            else:
                messages.error(request, "비밀번호 변경 중 오류가 발생했습니다.")
                return render(request, 'member/info_edit_password.html')
    
    # GET 요청
    return render(request, 'member/info_edit_password.html')



# ---------- 마이 페이지 예약 ----------------------
def myreservation(request):

    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")

    try:
        user = Member.objects.get(user_id=login_id)

        reservations = Reservation.objects.filter(
            member=user
        ).order_by('-reg_date')

        reservation_list = []

        for r in reservations:
            # 모든 슬롯 조회
            slots = TimeSlot.objects.filter(reservation_id=r)

            # 슬롯이 하나도 없다 = 완전 취소
            if not slots.exists():
                reservation_list.append({
                    "facility_name": "(취소된 예약)",
                    "reservation_date": "-",
                    "reservation_num": r.reservation_num,
                    "status": "cancelled"
                })
                continue

            # 취소된 슬롯 개수
            cancelled_slots = slots.filter(delete_yn=1).count()
            total_slots = slots.count()

            # 상태 계산
            if cancelled_slots == total_slots:
                status = "cancelled"     # 전체 취소
            elif cancelled_slots > 0:
                status = "partial"       # 부분 취소
            else:
                status = "active"        # 예약중

            # 시설 정보
            facility = slots.first().facility_id
            representative_date = slots.first().date.strftime("%Y-%m-%d")

            reservation_list.append({
                "facility_name": facility.faci_nm,
                "reservation_date": representative_date,
                "reservation_num": r.reservation_num,
                "status": status
            })

    except Exception as e:
        print("[myreservation ERROR]", e)
        reservation_list = []

    # 페이징 처리
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))

    paging = pager(request, reservation_list, per_page=per_page)
   
    page_obj = paging['page_obj']

    return render(request, "member/myreservation.html", {
        "page_obj": page_obj,
        "per_page": per_page,
        "page": page,
        "block_range": paging['block_range'],
        "block_start": paging['block_start'],
        "block_end": paging['block_end'],
    })

@csrf_exempt
def cancel_timeslot(request, reservation_num):
    res = check_login(request)
    if res:
        return res
    
    data = json.loads(request.body)
    slots = data.get("slots", [])

    try:
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
            reservation.delete_date = datetime.now()
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

    except Exception as e:
        return JsonResponse({"result": "error", "msg": "취소 실패"})

# 예약 상세페이지 

def myreservation_detail(request, reservation_num):
    res = check_login(request)
    if res:
        return res
    try:
        reservation = Reservation.objects.get(reservation_num=reservation_num)

        slots = TimeSlot.objects.filter(reservation_id=reservation).order_by("date", "start_time")

        if not slots.exists():
            messages.error(request, "예약 정보가 존재하지 않습니다.")
            return redirect("member:myreservation")

        facility = slots.first().facility_id

        # 전체 취소 여부 확인
        all_cancelled = True
        
        # 오늘 날짜
        from django.utils import timezone
        today = timezone.now().date()
        
        # 가장 빠른 예약 날짜 확인 (취소 불가 여부 판단용)
        earliest_date = None

        slot_list = []
        for s in slots:
            is_cancelled = (s.delete_yn == 1)
            if not is_cancelled:
                all_cancelled = False
            
            # 가장 빠른 예약 날짜 확인
            if not earliest_date and s.date:
                earliest_date = s.date

            slot_list.append({
                "date": s.date.strftime("%Y-%m-%d"),
                "start": s.start_time,
                "end": s.end_time,
                "is_cancelled": is_cancelled
            })
        
        # 예약 날짜가 지났는지 확인
        is_past = False
        if earliest_date and earliest_date < today:
            is_past = True
            # 예약 날짜가 지난 경우 자동으로 expire_yn 업데이트
            if reservation.expire_yn == 0:  # 아직 만료 처리되지 않은 경우만
                reservation.expire_yn = 1
                reservation.save(update_fields=['expire_yn'])

        context = {
            "facility_name": facility.faci_nm,
            "facility_address": facility.address,
            "facility_tel": facility.tel,
            "reservation_num": reservation.reservation_num,
            "reg_date": reservation.reg_date.strftime("%Y-%m-%d %H:%M"),
            "payment": reservation.payment,
            "slot_list": slot_list,
            "all_cancelled": all_cancelled,   # ← 상세페이지에서 버튼 숨기기 용도
            "is_past": is_past,  # 예약 날짜가 지났는지 여부
        }

        return render(request, "member/myreservation_detail.html", context)

    except Reservation.DoesNotExist:
        messages.error(request, "예약을 찾을 수 없습니다.")
        return redirect("member:myreservation")


@csrf_exempt
def reservation_cancel(request, reservation_num):
    res = check_login(request)
    if res:
        return res
    
    if request.method != "POST":
        return JsonResponse({"result": "error", "msg": "잘못된 요청"})

    try:
        reservation = Reservation.objects.get(reservation_num=reservation_num)

        # 예약 취소 상태 업데이트
        reservation.delete_yn = 1
        reservation.delete_date = datetime.now()
        reservation.save()

        # 연결된 모든 TimeSlot 삭제
        TimeSlot.objects.filter(reservation_id=reservation).delete()

        return JsonResponse({"result": "ok"})

    except Reservation.DoesNotExist:
        return JsonResponse({"result": "error", "msg": "예약을 찾을 수 없습니다."})


from django.db.models import F
def myrecruitment(request):
    # 로그인 체크
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")
    
    try:
        # 로그인한 사용자 정보 가져오기
        user = Member.objects.get(user_id=login_id)
        
        # DB에서 본인이 작성한 모집글 조회 (삭제되지 않은 것만)
        from recruitment.models import Community
        
        communities = (Community.objects.filter(
            member_id=user,
        ).select_related("endstatus")
        .annotate(
            end_status=F("endstatus__end_stat"),
        )
        .order_by('-reg_date'))



    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')
    except Exception as e:
        import traceback
        print(f"[ERROR] 내 모집글 조회 오류: {str(e)}")
        print(traceback.format_exc())
        communities = Community.objects.none()
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        communities = communities.order_by('title')
    elif sort == "views":
        communities = communities.order_by('-view_cnt')
    else:  # recent
        communities = communities.order_by('-reg_date')

    # 모집 상태 필터
    status = request.GET.get("status", "all")
    if status == "closed":
        communities=communities.filter(endstatus__end_stat=1)
    elif status == "open":
        communities=communities.exclude(endstatus__end_stat=1)   

    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    
    paging = pager(request, communities, per_page=per_page)
    page_obj = paging['page_obj']
    

    
    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "page": page,
        "sort": sort,
        "block_range": paging['block_range'],
        "block_start": paging['block_start'],
        "block_end": paging['block_end'],
    }
    
    return render(request, 'member/myrecruitment.html', context)


def myarticle(request):
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")
    try:
        user = Member.objects.get(user_id=login_id)

        from board.models import Article
        from board.utils import get_board_by_name
        
        board = get_board_by_name('post')

        # 삭제된 게시글 포함 전체 조회
        articles = Article.objects.filter(
            member_id=user,
            board_id=board
        )

    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')
    except Exception:
        import traceback
        print(traceback.format_exc())
        articles = Article.objects.none()

    sort = request.GET.get("sort", "recent")
    if sort == "title":
        articles = articles.order_by('title')
    elif sort == "views":
        articles = articles.order_by('-view_cnt')
    else:
        articles = articles.order_by('-reg_date')

    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))

    paging = pager(request, articles, per_page=per_page)
    page_obj = paging['page_obj']


    return render(request, 'member/myarticle.html', {
        "page_obj": page_obj,
        "per_page": per_page,
        "page": page,
        "sort": sort,
        "block_range": paging['block_range'],
        "block_start": paging['block_start'],
        "block_end": paging['block_end'],
    })


def myjoin(request):
    # 로그인 체크
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")
    
    try:
        # 로그인한 사용자 정보 가져오기
        user = Member.objects.get(user_id=login_id)
        
        # DB에서 본인이 신청한 참여 내역 조회 (JoinStat)
        from recruitment.models import JoinStat, Community
        
        # 본인이 신청한 참여 내역 조회 (삭제되지 않은 모집글만)
        join_stats = JoinStat.objects.filter(
            member_id=user
        ).select_related('community_id').filter(
            community_id__delete_date__isnull=True
        ).order_by('-community_id__reg_date')
        
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')
    except Exception as e:
        import traceback
        print(f"[ERROR] 내 참여 내역 조회 오류: {str(e)}")
        print(traceback.format_exc())
        join_stats = JoinStat.objects.none()
    
    # 정렬 기능
    sort = request.GET.get("sort", "recent")
    if sort == "title":
        join_stats = join_stats.order_by('community_id__title')
    elif sort == "views":
        join_stats = join_stats.order_by('-community_id__view_cnt')
    else:  # recent
        join_stats = join_stats.order_by('-community_id__reg_date')
    
    # 페이지네이션
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))
    
    paging = pager(request, join_stats, per_page=per_page)
    page_obj = paging['page_obj']
   
    context = {
        "page_obj": paging["page_obj"],
        "per_page": per_page,
        "page": page,
        "sort": sort,
        "block_range": paging["block_range"],
        "block_start": paging["block_start"],
        "block_end": paging["block_end"],
        "paginator": paging["paginator"],   # ⭐ 반드시 추가
    }
    
    return render(request, 'member/myjoin.html', context)


@csrf_exempt
def delete_my_article(request):
    """마이페이지에서 본인이 작성한 게시글 삭제 API"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 로그인 체크
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")
    
    try:
        user = Member.objects.get(user_id=login_id)
        data = json.loads(request.body)
        article_id = data.get("article_id")
        
        if not article_id:
            return JsonResponse({"status": "error", "msg": "게시글 ID가 필요합니다."})
        
        # 본인이 작성한 게시글인지 확인
        from board.models import Article
        from board.utils import get_board_by_name
        
        board = get_board_by_name('post')
        article = Article.objects.get(
            article_id=article_id,
            member_id=user,
            board_id=board
        )
        
        # 이미 삭제된 경우
        if article.delete_date:
            return JsonResponse({"status": "error", "msg": "이미 삭제된 게시글입니다."})
        
        # 삭제 처리 (soft delete)
        article.delete_date = datetime.now()  # 한국 시간으로 저장
        article.save(update_fields=['delete_date'])
        
        return JsonResponse({"status": "ok", "msg": "게시글이 삭제되었습니다."})
    
    except Member.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "회원 정보를 찾을 수 없습니다."}, status=404)
    except Article.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "게시글을 찾을 수 없거나 권한이 없습니다."}, status=404)
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_my_article 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})


@csrf_exempt
def delete_my_community(request):
    """마이페이지에서 본인이 작성한 모집글 삭제 API"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 로그인 체크
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")
    
    try:
        user = Member.objects.get(user_id=login_id)
        data = json.loads(request.body)
        community_id = data.get("community_id")
        
        if not community_id:
            return JsonResponse({"status": "error", "msg": "모집글 ID가 필요합니다."})
        
        # 본인이 작성한 모집글인지 확인
        from recruitment.models import Community
        
        community = Community.objects.get(
            community_id=community_id,
            member_id=user
        )
        
        # 이미 삭제된 경우
        if community.delete_date:
            return JsonResponse({"status": "error", "msg": "이미 삭제된 모집글입니다."})
        
        # 삭제 처리 (soft delete)
        community.delete_date = datetime.now()  # 한국 시간으로 저장
        community.save(update_fields=['delete_date'])
        
        return JsonResponse({"status": "ok", "msg": "모집글이 삭제되었습니다."})
    
    except Member.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "회원 정보를 찾을 수 없습니다."}, status=404)
    except Community.DoesNotExist:
        return JsonResponse({"status": "error", "msg": "모집글을 찾을 수 없거나 권한이 없습니다."}, status=404)
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_my_community 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})




# 회원탈퇴
def withdraw(request):
    # 로그인 체크
    res = check_login(request)
    if res:
        return res

    login_id = request.session.get("user_id")
    

    try:
        # DB에서 최신 회원 정보 가져오기 (캐시 무시)
        user = Member.objects.get(user_id=login_id)

        # 카카오 유저 여부 확인(user_id가 'kakao_'로 시작함)
        is_kakao_user = login_id.startswith('kakao_') if login_id else False

        # 카카오 사용자가 아닌 경우에만 비밀번호 확인
        if not is_kakao_user:
            password = request.POST.get('password', '')
            if not check_password(password, user.password):
                messages.error(request, "비밀번호가 올바르지 않습니다.")
                return redirect('/member/info/')

        # 탈퇴 사유 받기
        delete_reason = request.POST.get('delete_reason', '')
        
        # 탈퇴 사유 매핑 (1~5번은 객관식 내용으로 변환)
        reason_map = {
            '1': '서비스 이용이 불편함',
            '2': '원하는 기능이 없음',
            '3': '이용 빈도가 낮음',
            '4': '개인정보 보호 우려',
            '5': '다른 서비스 이용',
        }
        
        # 1~5번 선택 시 해당 내용으로 변환, 6번(기타)은 직접 입력값 사용
        if delete_reason in reason_map:
            user.delete_reason = reason_map[delete_reason]
        elif delete_reason.startswith('6:'):
            # 6번 선택 시 "6:직접입력내용" 형식으로 전송되므로 ":" 이후만 저장
            user.delete_reason = delete_reason.split(':', 1)[1] if ':' in delete_reason else delete_reason
        else:
            user.delete_reason = delete_reason

        user.delete_yn = 1
        user.delete_date = timezone.now()
        user.save()
        # 회원 탈퇴시 관련된것들 다 삭제
        if user:
            Comment.objects.filter(member_id=user).update(delete_date=timezone.now().date())
            Article.objects.filter(member_id=user).update(delete_date=timezone.now().date())
            Community.objects.filter(member_id=user).update(delete_date=timezone.now().date())
            Reservation.objects.filter(member_id=user).update(delete_date=timezone.now().date())
            Reservation.objects.filter(member_id=user).update(delete_yn=1)

        request.session.flush()

        # 카카오 사용자 안내 메세지
        if is_kakao_user:
            messages.info(
                request,
                "탈퇴가 완료되었습니다. 완전한 탈퇴는 카카오 계정 설정 > 연결된 서비스 관리에서 앱 연결을 해제해 주세요."
            )
        else:
            messages.success(request,'회원 탈퇴가 완료되었습니다.')
            
        return redirect('/')
    except Member.DoesNotExist:
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect('/login/')

@csrf_exempt
def clear_rejoin_message(request):
    """재가입 메시지 세션 정리"""
    if 'kakao_rejoin_message' in request.session:
        del request.session['kakao_rejoin_message']
    return JsonResponse({'status': 'ok'})