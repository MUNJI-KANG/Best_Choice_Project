import traceback
import os

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from common.utils import is_manager
from member.models import Member
from django.contrib.auth.hashers import make_password, check_password


def manager(request):
    """
    관리자 로그인 페이지
    member_id == 1인 계정만 관리자로 인정
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

# 로그아웃
def logout(request):
    """
    로그아웃 처리
    - 카카오 로그인 사용자: 세션 삭제 후 카카오 로그아웃 페이지로 이동
    - 일반 로그인 사용자: 세션 삭제 후 메인 페이지로 이동
    """
    # 로그인하지 않은 경우
    if not request.session.get('user_id'):
        return redirect('/')
    
    # 카카오 로그인 사용자 여부 확인
    is_kakao_user = request.session.get('is_kakao_user', False)
    if not is_kakao_user:
        user_id = request.session.get('user_id', '')
        is_kakao_user = user_id.startswith('kakao_') if user_id else False
    
    # 카카오 로그인 사용자인 경우: 세션 먼저 삭제 후 카카오 로그아웃 페이지로 이동
    if is_kakao_user:
        # 세션의 모든 키를 명시적으로 삭제
        session_keys = list(request.session.keys())
        for key in session_keys:
            del request.session[key]
        
        # 세션 완전히 삭제
        request.session.flush()
        request.session.set_expiry(0)
        
        KAKAO_REST_API_KEY = os.getenv('KAKAO_REST_API_KEY')
        if KAKAO_REST_API_KEY:
            # 카카오 로그아웃 후 메인 페이지로 돌아옴 (세션은 이미 삭제됨)
            kakao_logout_url = (
                "https://kauth.kakao.com/oauth/logout"
                f"?client_id={KAKAO_REST_API_KEY}"
                f"&logout_redirect_uri={request.build_absolute_uri('/')}"
            )
            return redirect(kakao_logout_url)
    
    # 일반 로그인 사용자: 세션 삭제 후 메인 페이지로
    # 세션의 모든 키를 명시적으로 삭제
    session_keys = list(request.session.keys())
    for key in session_keys:
        del request.session[key]
    
    # 세션 완전히 삭제
    request.session.flush()
    
    # 세션 쿠키도 삭제하기 위해 만료 시간 설정
    request.session.set_expiry(0)
    
    messages.success(request, "로그아웃되었습니다.")
    return redirect('manager:manager_login')


def info_edit(request):
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
