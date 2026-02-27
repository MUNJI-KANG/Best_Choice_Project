import traceback
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from common.utils import is_manager
from member.models import Member
from django.contrib.auth.hashers import make_password, check_password


def manager(request):
    """
    관리자 전용 로그인 인터페이스를 제공하고 인증을 처리하는 뷰 함수입니다.

    [기술적 주안점]
    - 권한 기반 인증 보안: 단순 아이디/비밀번호 일치를 넘어, DB 내 'manager_yn' 플래그를 검증하여 인가된 관리자만 접근 가능하도록 설계했습니다.
    - 세션 하이재킹 방지: 로그인 성공 시 request.session.flush()를 호출하여 기존 세션을 완전히 초기화하고 새로운 세션 ID를 생성함으로써, 세션 고정 공격(Session Fixation)을 원천 차단했습니다.
    - 단방향 해시 검증: Django의 check_password를 활용해 DB에 해시화되어 저장된 비밀번호를 안전하게 비교 검증합니다.
    """
    admin = request.session.get("manager_id")
    if not admin : 
        if request.method == "POST":
            admin_id = request.POST.get("admin_id", "").strip()
            admin_pw = request.POST.get("admin_pw", "").strip()
        
            # 입력값 검증
            if not admin_id or not admin_pw:
                return render(request, 'manager/login_manager.html', {
                    'error': '아이디와 비밀번호를 입력해주세요.'
                })
        
            try:
                from django.contrib.auth.hashers import check_password
                from member.models import Member
            
                # user_id로 계정 조회
                try:
                    admin_user = Member.objects.get(user_id=admin_id)
                except Member.DoesNotExist:
                    return render(request, 'manager/login_manager.html', {
                        'error': '존재하지 않는 아이디입니다.'
                    })
            
                # 관리자 권한 확인 (member_id == 1만 관리자)
                if admin_user.manager_yn != 1:
                    return render(request, 'manager/login_manager.html', {
                        'error': '관리자 권한이 없습니다.'
                    })
            
                # 비밀번호 검증
                if not check_password(admin_pw, admin_user.password):
                    return render(request, 'manager/login_manager.html', {
                        'error': '비밀번호가 올바르지 않습니다.'
                    })
            
                # 세션 완전히 삭제
                request.session.flush()
                
                # 세션 쿠키도 삭제하기 위해 만료 시간 설정
                request.session.set_expiry(0)
    
                # 로그인 성공 → 세션에 저장
                request.session["user_id"] = admin_user.user_id
                request.session["user_name"] = admin_user.name
                request.session["nickname"] = admin_user.nickname
                request.session['manager_id'] = admin_user.member_id
                #request.session['manager_name'] = admin_user.name

                return redirect('manager:dashboard')
            
            except Exception as e:
                print(f"[ERROR] 관리자 로그인 오류: {str(e)}")
                print(traceback.format_exc())
                return render(request, 'manager/login_manager.html', {
                    'error': '로그인 중 오류가 발생했습니다.'
            })
            
        return render(request, 'manager/login_manager.html')
    else:
        return redirect('manager:dashboard')
def logout(request):
    """
    관리자 세션을 안전하게 파기하고 로그인 페이지로 리다이렉트합니다.

    [기술적 주안점]
    - 세션 데이터 완전 소거: 세션 내 모든 키를 명시적으로 삭제하고 flush()를 호출하여 서버 측 세션 데이터를 즉시 무효화합니다.
    - 클라이언트 보안 강화: set_expiry(0)를 통해 브라우저 종료 시 세션 쿠키가 즉시 만료되도록 설정하여 공용 PC 등에서의 보안 취약점을 방어했습니다.
    """
    # 로그인하지 않은 경우 바로 리다이렉트
    if not request.session.get('manager_id'):
        return redirect('manager:manager_login')
    
    # 세션 데이터 명시적 개별 삭제 (인증 정보 파편 제거)
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    
    # 세션 엔진에서 현재 세션 완전 파기
    request.session.flush()
    
    # 세션 쿠키 만료 시간 설정 (즉시 만료)
    request.session.set_expiry(0)
    
    messages.success(request, "관리자 로그아웃되었습니다.")
    return redirect('manager:manager_login')

def info_edit(request):
    """
    관리자의 비밀번호를 포함한 계정 정보를 안전하게 갱신하는 뷰 함수입니다.

    [기술적 주안점]
    - 다중 검증 아키텍처: 기존 비밀번호 대조, 새 비밀번호의 일치 여부를 단계별로 검증하여 비정상적인 정보 수정을 방지합니다.
    - 데이터 암호화 저장: 변경된 비밀번호를 make_password로 단방향 해시화하여 저장함으로써, DB 노출 시에도 관리자 계정의 보안성을 확보했습니다.
    - 권한 재검증: 요청 시마다 is_manager 유틸리티를 호출하여 비인가 사용자의 접근을 차단하는 방어적 프로그래밍을 적용했습니다.
    """
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')

    login_id = request.session.get('user_id')

    try:
        manager = Member.objects.get(
            user_id=login_id,
            manager_yn=1
        )
    except Member.DoesNotExist:
        messages.error(request, "관리자 정보를 찾을 수 없습니다.")
        return redirect('manager:manager_login')

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        new_password_confirm = request.POST.get("new_password_confirm")

        if not check_password(current_password, manager.password):
            messages.error(request, "기존 비밀번호가 올바르지 않습니다.")
            return redirect("manager:info_edit")

        if not new_password or not new_password_confirm:
            messages.error(request, "새 비밀번호를 입력해 주세요.")
            return redirect("manager:info_edit")

        if new_password != new_password_confirm:
            messages.error(request, "새 비밀번호가 일치하지 않습니다.")
            return redirect("manager:info_edit")

        manager.password = make_password(new_password)
        manager.save()

        messages.success(request, "비밀번호가 변경되었습니다.")
        return redirect("manager:info_edit")

    return render(request, "manager/info_edit.html")
