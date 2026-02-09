import json
import traceback

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Case, When, Value, IntegerField
from django.utils import timezone
from django.contrib import messages
from django.http import Http404


from django.views.decorators.csrf import csrf_exempt

from common.utils import is_manager
from common.models import Comment
from common.paging import pager


from recruitment.models import Community, EndStatus, JoinStat
from datetime import datetime
from django.http import JsonResponse




# 모집글관리
def recruitment_manager(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    # DB에서 모집글 조회 (삭제된 것도 포함)
    try:
        queryset = Community.objects.select_related('member_id') \
        .order_by(
            Case(
                When(delete_date__isnull=True, then=Value(0)),  # 삭제 안된 글 → 우선
                default=Value(1),                               # 삭제된 글 → 뒤로
                output_field=IntegerField()
            ),
            '-reg_date'  # 그 안에서 최신순
        )
    except Exception:
        queryset = []
    
    per_page = int(request.GET.get("per_page", 15))

    try:
        page = int(request.GET.get("page", 1))
        if page < 1:
            page = 1
    except:
        page = 1

    paging = pager(request, queryset, per_page=per_page)


 

    # facility_json 형식으로 데이터 변환
    start_index = (paging['page_obj'].number - 1) * per_page
    facility_page = []
    
    for idx, community in enumerate(paging['page_obj'].object_list):
        delete_date_str = None
        if community.delete_date:
            # 이미 한국 시간으로 저장되어 있음
            delete_date_str = community.delete_date.strftime('%Y-%m-%d %H:%M')
        
        facility_page.append({
            "id": community.community_id,
            "title": community.title,
            "author": community.member_id.user_id if community.member_id else "",
            "row_no": start_index + idx + 1,
            "delete_date": delete_date_str,
        })

    context = {
        "page_obj": paging['page_obj'],
        "per_page": per_page,
        "facility_json": json.dumps(facility_page, ensure_ascii=False),
        "block_range": paging['block_range'],
    }
    return render(request, 'manager/recruitment_manager.html', context)


# 모집글 상세페이지
def recruitment_detail(request, id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')

    # 모집글 조회
    try:
        recruit = Community.objects.get(
            pk=id
        )
    except Community.DoesNotExist:
        raise Http404("관리자에 의해 삭제된 모집글입니다.")

    # 참여자 목록
    joins_qs = JoinStat.objects.filter(community_id=recruit)
    waiting_count= joins_qs.count()
    # 승인된 인원만 count
    approved_count = joins_qs.filter(join_status=1).count()
    capacity = recruit.num_member or 0

    # -------------------------
    # 🔥 자동 마감 처리 로직 (핵심)
    # -------------------------
    end_status, created = EndStatus.objects.get_or_create(
        community=recruit,
        defaults={
            "end_set_date": timezone.now().date(),
            "end_stat": 0,
        }
    )

    # 승인된 인원이 정원 이상이면 자동 마감
    if approved_count >= capacity and capacity > 0:
        if end_status.end_stat != 1:  
            end_status.end_stat = 1
            end_status.end_date = timezone.now().date()
            end_status.save()

    # -------------------------
    # 최종 마감 여부
    # -------------------------
    is_closed = (end_status.end_stat == 1)



    # 상세 참여 리스트 (owner/관리자만)
    join_list = []
    join_list = (
        joins_qs
        .select_related("member_id")
        .order_by("join_status", "member_id__user_id")
    )

    comment_objs = Comment.objects.select_related('member_id').filter(
            community_id=recruit
        ).order_by('reg_date')
        
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

    context = {
        "recruit": recruit,
        "is_manager": is_manager,
        "join_list": join_list,
        "approved_count": approved_count,
        "capacity": capacity,
        "is_closed": is_closed,
        "comments": comments,
        "waiting_rejected_count":waiting_count,
    }

    return render(request, "manager/recruitment_manager_detail.html", context)


@csrf_exempt
def delete_recruitment(request):
    """모집글 일괄 삭제 API (Community)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        community_ids = data.get("ids", [])
        
        if not community_ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})
        
        # 모집글 조회 및 삭제 처리
        communities = Community.objects.filter(community_id__in=community_ids)
        
        deleted_count = 0
        now = datetime.now()  # 한국 시간으로 저장
        
        for community in communities:
            if community.delete_date is None:  # 아직 삭제되지 않은 경우만
                community.delete_date = now
                community.save(update_fields=['delete_date'])
                deleted_count += 1
        
        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(community_ids)
        })
    
    except Exception as e:
        print(f"[ERROR] delete_communities 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})

@csrf_exempt
def hard_delete_recruitment(request):
    """모집글 일괄 삭제 API (Community)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        community_ids = data.get("ids", [])
        
        if not community_ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})
        
        # 모집글 조회 및 삭제 처리
        communities = Community.objects.filter(community_id__in=community_ids)
        
        deleted_count = 0
        
        for community in communities:
            community.delete()
            deleted_count += 1
        
        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(community_ids)
        })
    
    except Exception as e:
        print(f"[ERROR] delete_communities 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})


@csrf_exempt
def restore_recruitment(request):
    """모집글 일괄 복구 (Community)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        community_ids = data.get("ids", [])
        
        if not community_ids:
            return JsonResponse({"status": "error", "msg": "복구할 항목 없음"})
        
        # 삭제된 모집글 조회 및 복구 처리
        communities = Community.objects.filter(community_id__in=community_ids)
        
        restore_count = 0
        # now = datetime.now()  # 한국 시간으로 저장
        
        for community in communities:
            if community.delete_date:  # 이미 삭제된 경우만
                community.delete_date = None
                community.save(update_fields=['delete_date'])
                restore_count += 1
        
        return JsonResponse({
            "status": "ok",
            "restore": restore_count,
            "total": len(community_ids)
        })
    
    except Exception as e:
        print(f"[ERROR] restore_communities 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})