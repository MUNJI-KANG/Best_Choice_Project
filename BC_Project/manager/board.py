import os
import json
import uuid

from datetime import datetime
from common.utils import is_manager, upload_files

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import  Case, When, Value, IntegerField
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.http import FileResponse, Http404, JsonResponse


from django.views.decorators.csrf import csrf_exempt


# models import 
from member.models import Member
from board.models import Article, Board
from common.models import Comment, AddInfo
from common.paging import pager
from manager.models import HeroImg



# 제거예정

from datetime import datetime



# 게시판 list
def board_list(request, id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    try:
        boardName = Board.objects.filter(board_id=id).values_list('board_name', flat=True).first()
        queryset = Article.objects.select_related('member_id', 'board_id') \
        .filter(board_id=id) \
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
    page_obj = paging['page_obj']

    # json 형식으로 데이터 변환
    start_index = (page_obj.number - 1) * per_page
    article_list = []
    
    for idx, article in enumerate(page_obj.object_list):
        delete_date_str = None
        if article.delete_date:
            # 이미 한국 시간으로 저장되어 있음
            delete_date_str = article.delete_date.strftime('%Y-%m-%d %H:%M')
        
        article_list.append({
            "id": article.article_id,
            "title": article.title,
            "author": article.member_id.user_id if article.member_id else "",
            "row_no": start_index + idx + 1,
            "delete_date": delete_date_str,
            "boardId" : id
        })

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "boardName":boardName,
        "article_list": json.dumps(article_list, ensure_ascii=False),
        "block_range": paging['block_range'],
        "boardId":id
    }

    return render(request, 'manager/board_list.html', context)

# 게시글 등록 & 수정
def board_write(request, id, pk=None):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    if pk:
        article = get_object_or_404(Article, board_id=id, article_id=pk)
        start_date_str = ""
        end_date_str = ""

        if article.start_date:
            start_date_str = article.start_date.strftime("%Y-%m-%dT%H:%M")

        if article.end_date:
            end_date_str = article.end_date.strftime("%Y-%m-%dT%H:%M")
        # GET = 수정 페이지 열기
        if request.method == "GET":
            context = {
                "article": article,
                "existing_files": get_existing_files(pk),
                "start_date": start_date_str,
                "end_date" : end_date_str,
                "is_edit": True,
                "boardId": id,
                "boardName": article.board_id.board_name,
            }
            return render(request, "manager/board_write.html", context)

        # POST = 실제 수정 처리
        elif request.method == "POST":
            return update_article(request, article, id, pk)

    else:
        # GET = 빈 글쓰기 폼
        if request.method == "GET":
            boardName = get_object_or_404(Board, board_id=id)
            context = {
                "boardId": id,
                "boardName": boardName,
                "is_edit": False
            }
            return render(request, "manager/board_write.html", context)

        # POST = 새 글 등록 처리
        elif request.method == "POST":
            return create_article(request, id)

# 파일 있는지 확인
def get_existing_files(article_id):
    add_info_objs = AddInfo.objects.filter(article_id=article_id)
    files = []

    for add_info in add_info_objs:
        ext = os.path.splitext(add_info.file_name)[1].lower()
        files.append({
            'id': add_info.add_info_id,
            'name': add_info.file_name,
            'url': f"{settings.MEDIA_URL}{add_info.path}",
            'is_image': ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        })
    return files


# 게시글 등록
def create_article(request, board_id):
    title = request.POST.get('title')
    contents = request.POST.get('context')

    board = get_object_or_404(Board, board_id=board_id)

    article = Article(
        title=title,
        contents=contents,
        board_id=board,
        member_id=Member.objects.get(member_id=request.session.get("manager_id"))
    )

    # 공지사항(board_id=2)일 때만 적용
    if board_id == 2:
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')

        always_on = 0 if notice_type == 'always' else 1
        if pin_top == '1':
            always_on = 0

        article.always_on = always_on
        article.start_date = parse_datetime(start_date) if start_date else None
        article.end_date = parse_datetime(end_date) if end_date else None

    article.save()

    # 파일 업로드
    upload_files(request, article, file_field="file", sub_dir="uploads/articles")

    messages.success(request, "등록되었습니다.")
    return redirect('manager:board_detail', pk=article.article_id)

# 게시글 수정
def update_article(request, article, board_id, pk):
    title = request.POST.get('title')
    contents = request.POST.get('context')

    article.title = title
    article.contents = contents

    if board_id == 2:
        notice_type = request.POST.get('notice_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        pin_top = request.POST.get('pin_top', '0')

        always_on = 0 if notice_type == 'always' else 1
        print("notice_type : ", notice_type)
        print("always_on : ", always_on)

        article.always_on = always_on
        article.start_date = parse_datetime(start_date) if start_date else None
        article.end_date = parse_datetime(end_date) if end_date else None

    article.save()

    # 기존 파일 삭제
    delete_ids = request.POST.getlist("delete_files")
    if delete_ids:
        files_to_delete = AddInfo.objects.filter(add_info_id__in=delete_ids)
        for f in files_to_delete:
            if f.path:
                file_path = os.path.join(settings.MEDIA_ROOT, f.path)
                if os.path.exists(file_path):
                    os.remove(file_path)
        files_to_delete.delete()

    # 새 파일 업로드
    upload_files(request, article, file_field="file", sub_dir="uploads/articles")

    messages.success(request, "수정되었습니다.")
    return redirect('manager:board_detail',pk=pk)



# 게시글 상세페이지
def board_detail(request, pk):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    article = get_object_or_404(Article, article_id=pk)
    memberNm = get_object_or_404(Member, member_id = article.member_id_id ).nickname

    board_type = article.board_id.board_name  # notice / event / post

    # 파일 로딩
    add_info = AddInfo.objects.filter(article_id=pk)
    files = []
    images = []
    for f in add_info:
        ext = os.path.splitext(f.file_name)[1].lower()
        info = {
            "url": f"{settings.MEDIA_URL}{f.path}",
            "name": f.file_name,
            "is_image": ext in ['.jpg', '.jpeg', '.png', '.gif'],
            "add_info_id" : f.add_info_id,
            "file_name" : f.file_name
        }
        if info["is_image"]:
            images.append(info)
        else:
            files.append(info)
    comment_objs = Comment.objects.select_related('member_id').filter(
        article_id = pk
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
    return render(request, "manager/board_manager_detail.html", {
        "article": article,
        "author" : memberNm,
        "board_type": board_type,
        "files": files,
        "images": images,
        "comments" : comments
    })

@csrf_exempt
def delete_articles(request):
    """게시글 일괄 삭제 API (Article)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        article_ids = data.get("ids", [])
        #board_type = data.get("board_type", "")  # 'notice', 'event', 'post'
        
        if not article_ids:
            return JsonResponse({"status": "error", "msg": "삭제할 항목 없음"})
        
        # 게시판 확인
        # try:
        #     board = get_board_by_name(board_type)
        # except Exception:
        #     return JsonResponse({"status": "error", "msg": f"잘못된 게시판 타입: {board_type}"})
        
        # 게시글 조회 및 삭제 처리
        articles = Article.objects.filter(
            article_id__in=article_ids
            #,board_id=board
        )
        
        deleted_count = 0
        now = datetime.now()  # 한국 시간으로 저장
        
        for article in articles:
            if article.delete_date is None:  # 아직 삭제되지 않은 경우만
                article.delete_date = now
                article.save(update_fields=['delete_date'])
                deleted_count += 1
        
        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(article_ids)
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_articles 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})

@csrf_exempt
def hard_delete_articles(request):
    """게시글 일괄 영구 삭제 (Article)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        article_ids = data.get("ids", [])
        
        if not article_ids:
            return JsonResponse({"status": "error", "msg": "영구 삭제할 항목 없음"})
        
        
        # 게시글 조회 및 삭제 처리
        articles = Article.objects.filter(
            article_id__in=article_ids
            #,board_id=board
        )
        
        deleted_count, _ = articles.delete()

        return JsonResponse({
            "status": "ok",
            "deleted": deleted_count,
            "total": len(article_ids)
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] hard_delete_articles 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})


@csrf_exempt
def restore_articles(request):
    """게시글 일괄 복구 (Article)"""
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST만 가능"}, status=405)
    
    # 관리자 체크
    if not request.session.get('manager_id'):
        return JsonResponse({"status": "error", "msg": "관리자 권한이 필요합니다."}, status=403)
    
    try:
        data = json.loads(request.body)
        article_ids = data.get("ids", [])
        #board_type = data.get("board_type", "")  # 'notice', 'event', 'post'
        
        if not article_ids:
            return JsonResponse({"status": "error", "msg": "복구할 항목 없음"})
        
        # 게시판 확인
        # try:
        #     board = get_board_by_name(board_type)
        # except Exception:
        #     return JsonResponse({"status": "error", "msg": f"잘못된 게시판 타입: {board_type}"})
        
        # 게시글 조회 및 복구 처리
        articles = Article.objects.filter(
            article_id__in=article_ids
            #,board_id=board
        )
        
        restore_count = 0
        # now = datetime.now()  # 한국 시간으로 저장
        
        for article in articles:
            if article.delete_date:  # 이미 삭제된 경우만
                article.delete_date = None
                article.save(update_fields=['delete_date'])
                restore_count += 1
        
        return JsonResponse({
            "status": "ok",
            "restore": restore_count,
            "total": len(article_ids)
        })
    
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_articles 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({"status": "error", "msg": str(e)})

# 배너 관리----------------------------------
def banner_manager(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    per_page = int(request.GET.get("per_page", 15))
    page = int(request.GET.get("page", 1))

    # 모델 그대로 가져오기 ( dict로 재조립 절대 안함 )
    queryset = HeroImg.objects.filter(delete_date__isnull=True).order_by('-img_id')

    paging = pager(request, queryset, per_page=per_page)
    page_obj = paging['page_obj']

    # row_no 계산 (import 없음)
    start_index = (page_obj.number - 1) * per_page

    # 모델 객체 그대로 사용하면서 row_no만 붙여줌
    for idx, obj in enumerate(page_obj.object_list):
        obj.row_no = start_index + idx + 1

    context = {
        "page_obj": page_obj,
        "banner_list": page_obj.object_list,   # 모델 객체 그대로 전달!
        "per_page": per_page,
        "block_range": paging['block_range'],
    }

    return render(request, "manager/banner_manager.html", context)

def banner_detail(request, img_id):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    banner = get_object_or_404(HeroImg, img_id=img_id, delete_date__isnull=True)
    return render(request, "manager/banner_detail.html", {"banner": banner})


def banner_form(request):
    # 관리자 권한 확인
    if not is_manager(request):
        messages.error(request, "관리자 권한이 필요합니다.")
        return redirect('manager:manager_login')
    
    if request.method == "POST":
        upload_file = request.FILES.get("file")
        title = request.POST.get("title", "").strip()
        context = request.POST.get("context", "").strip()
        img_status = request.POST.get("img_status", "").strip()
        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        # ====== 필수값 검증 ======
        if not upload_file:
            return render(request, "manager/banner_form.html", {
                "alert": "배너 이미지를 첨부해주세요.",
                "title": title,
                "context": context,
                "selected_status": img_status,
                "start_date": start_date,
                "end_date": end_date,
            })

        if img_status == "":
            return render(request, "manager/banner_form.html", {
                "alert": "배너 상태를 선택해주세요.",
                "title": title,
                "context": context,
                "start_date": start_date,
                "end_date": end_date,
            })
        
        if title == "":
            return render(request, "manager/banner_form.html", {
                "alert" : "제목을 입력해주세요.",
                "title": title,
                "context": context,
                "selected_status": img_status,
                "start_date": start_date,
                "end_date": end_date,
            })
        img_status = int(img_status)

        # 기간 지정 아닐 때는 기간 날리기
        if img_status != 1:
            start_date = None
            end_date = None

        # ====== 파일 저장 ======
        save_dir = os.path.join(settings.MEDIA_ROOT, "banners")
        os.makedirs(save_dir, exist_ok=True)

        filename = f"{uuid.uuid4().hex}_{upload_file.name}"
        filepath = os.path.join(save_dir, filename)

        with open(filepath, "wb+") as f:
            for chunk in upload_file.chunks():
                f.write(chunk)

        file_url = f"banners/{filename}"

        HeroImg.objects.create(
            url=file_url,
            title=title,
            context=context,
            img_status=img_status,
            start_date=start_date,
            end_date=end_date,
        )

        return redirect("manager:banner_manager")

    # GET
    return render(request, "manager/banner_form.html")

def banner_edit(request, img_id):
    banner = get_object_or_404(HeroImg, img_id=img_id, delete_date__isnull=True)

    if request.method == "POST":
        upload_file = request.FILES.get("file")
        title = request.POST.get("title")
        context = request.POST.get("context")

        img_status = int(request.POST.get("img_status", 0))
        start_date = request.POST.get("start_date") or None
        end_date = request.POST.get("end_date") or None

        if img_status != 1:
            start_date = None
            end_date = None

        # 삭제 플래그 (X 버튼 또는 새 파일 선택 시 "1")
        delete_flag = request.POST.get("delete_file", "0")

        banner.title = title
        banner.context = context
        banner.img_status = img_status
        banner.start_date = start_date
        banner.end_date = end_date

        # 파일 저장 디렉터리
        save_dir = os.path.join(settings.MEDIA_ROOT, "banners")
        os.makedirs(save_dir, exist_ok=True)

        # 새 파일 업로드 우선 처리
        if upload_file:
            # 기존 파일 삭제
            if banner.url:
                old_path = os.path.join(settings.MEDIA_ROOT, banner.url)
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = f"{uuid.uuid4().hex}_{upload_file.name}"
            filepath = os.path.join(save_dir, filename)

            with open(filepath, "wb+") as f:
                for chunk in upload_file.chunks():
                    f.write(chunk)

            banner.url = f"banners/{filename}"

        # 새 파일은 없고, delete_flag == "1" 인 경우 → 기존 파일만 삭제
        elif delete_flag == "1":
            # 이미지 삭제 후 새 이미지가 없으면 에러
            messages.error(request, "이미지를 삭제하셨습니다. 새 이미지를 첨부해주세요.")
            return render(request, "manager/banner_edit.html", {"banner": banner})
        # 새 파일도 없고 삭제 플래그도 없는 경우는 그대로 유지

        banner.save()
        return redirect("manager:banner_manager")

    return render(request, "manager/banner_edit.html", {"banner": banner})

def banner_delete(request):
    data = json.loads(request.body)
    ids = data.get("ids", [])

    HeroImg.objects.filter(img_id__in=ids).update(delete_date=timezone.now())

    return JsonResponse({"status": "ok"})


def banner_download(request, img_id):
    banner = get_object_or_404(HeroImg, img_id=img_id, delete_date__isnull=True)

    if not banner.url:
        raise Http404("파일이 없습니다.")

    file_path = os.path.join(settings.MEDIA_ROOT, banner.url)

    if not os.path.exists(file_path):
        raise Http404("파일을 찾을 수 없습니다.")

    return FileResponse(
        open(file_path, "rb"),
        as_attachment=True,
        filename=os.path.basename(file_path),
    )