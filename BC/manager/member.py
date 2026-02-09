
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib import messages

from common.utils import is_manager

# models import 
from member.models import Member
from recruitment.models import Community
from reservation.models import Reservation
from board.models import Article
from common.models import Comment
from common.paging import pager



def member_list(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    members = Member.objects.filter(manager_yn = 0).order_by('delete_yn', 'member_id')
    search = request.GET.get("search", "name")
    q = request.GET.get("q", "")
    member_type = request.GET.get("member_type", "")
    per_page = int(request.GET.get("per_page", 15))


    # 검색 기능
    if q:
        if search == "name":
            members = members.filter(name__icontains=q)
        elif search == "user_id":
            members = members.filter(user_id__icontains=q)
        elif search == "nickname":
            members = members.filter(nickname__icontains=q)


    # 회원 유형 필터링
    if member_type == "kakao":
        members = members.filter(user_id__startswith="kakao")
    elif member_type == "normal":
        members = members.exclude(user_id__startswith="kakao")
    elif member_type == 'withdraw':
        members = members.filter(delete_yn__in =  [1,2])


    for m in members:
        a1 = m.addr1 or ""
        a2 = m.addr2 or ""
        a3 = m.addr3 or ""

        a1 = a1.strip()
        a2 = a2.strip()
        a3 = a3.strip()

        # join할 때 None, 공백 제거
        m.full_address = " ".join([p for p in [a1, a2, a3] if p])

    paging = pager(request, members, per_page=per_page)
   
    page_obj = paging['page_obj']

    context = {
        "member_list": page_obj,     
        "page_obj": page_obj,
        "page_range": paging['page_range'],
        "per_page": per_page,
        "search": search,
        "q": q,
        "member_type": member_type,
    }

    return render(request, 'manager/member_list.html', context)


def member_delete(request):
    if request.method == "POST":
        ids = request.POST.getlist("ids")  # 선택된 member_id 목록

    if ids:
        for member_id in ids:
            delete_yn = Member.objects.get(member_id=member_id).delete_yn
            if delete_yn == 0:
                Member.objects.filter(member_id__in=ids).update(delete_yn=2)
                Member.objects.filter(member_id__in=ids).update(delete_date=timezone.now().date())
                Comment.objects.filter(member_id__in=ids).update(delete_date=timezone.now().date())
                Article.objects.filter(member_id__in=ids).update(delete_date=timezone.now().date())
                Community.objects.filter(member_id__in=ids).update(delete_date=timezone.now().date())
                Reservation.objects.filter(member_id__in=ids).update(delete_date=timezone.now().date())
                Reservation.objects.filter(member_id__in=ids).update(delete_yn=1)
                messages.success(request, "탈퇴 처리가 완료되었습니다.")
            else:
                messages.success(request, "이미 탈퇴된 회원입니다.")

    return redirect("manager:member_list")
            




def member_restore(request):
    if request.method == "POST":
        ids = request.POST.getlist("ids")

        if ids:
            Member.objects.filter(member_id__in=ids).update(delete_yn=0)
            Member.objects.filter(member_id__in=ids).update(delete_date=None)
            

    messages.success(request, "회원 복구가 완료되었습니다.")
    return redirect("manager:member_list")