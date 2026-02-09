from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse,FileResponse,Http404
from django.views.decorators.csrf import csrf_exempt

from django.utils.dateparse import parse_datetime


import os
import uuid
from common.utils import check_login, handle_file_uploads, is_manager, upload_files
from board.models import Article, Board, Category
from board.utils import get_board_by_name
from common.models import Comment, AddInfo
from member.models import Member

from common.paging import pager




def b_name(board_name:str):
    mapping = {
        "notice": "공지할래",
        "event": "이벤트할래",
        "post": "수다떨래",
        "faq" : "FAQ"
    }
    if board_name not in mapping:
        raise ValueError(f"잘못된 board_name: {board_name}")
    
    return mapping.get(board_name, "")

def article_list(request, board_name):
    print('dsfasdfasdasfd')
    try:
        now = timezone.now()
        b_id = get_board_by_name(board_name).board_id
        noticeList = []

        # 기본 QuerySet
        articleList = (
            Article.objects
            .select_related('member_id', 'board_id')
            .filter(board_id=b_id, delete_date__isnull=True)
        )
        total = articleList.count()
        # 공지 게시판이면 pinned_articles 세팅
        if b_id == 2:

            # 1) 현재 기간 포함된 기간공지
            p_notice = articleList.filter(
                always_on=1,
                start_date__lte=now,
                end_date__gte=now
            )

            # 2) 상시공지(always_on=0)
            a_notice = articleList.filter(always_on=0)

            notice_articles = (
                (p_notice | a_notice)
                .annotate(
                    comment_count=Count(
                        "comment",
                        filter=Q(comment__delete_date__isnull=True)
                    )
                )
                .order_by('-always_on', '-reg_date')[:5]
            )

            # 상단 고정 게시글 변환
            for article in notice_articles:
                noticeList.append({
                    'id': article.article_id,
                    'comment_count': article.comment_count,
                    'title': article.title,
                    'author': article.member_id.nickname if article.member_id else '',
                    'is_admin': article.member_id.manager_yn == 1 if article.member_id else False,
                    'date': article.reg_date.strftime('%Y-%m-%d'),
                    'views': article.view_cnt,
                })
     
        # 전체 게시글 (공지 포함 전체)
        articleList = (
            articleList
            .annotate(
                comment_count=Count("comment", filter=Q(comment__delete_date__isnull=True))
            )
            .order_by('-reg_date')
        )

        # 검색
        keyword = request.GET.get("keyword", "")
        search_type = request.GET.get("search_type", "all")

        if keyword:
            if search_type == "title":
                articleList = articleList.filter(title__icontains=keyword)
            elif search_type == "author":
                articleList = articleList.filter(member_id__nickname__icontains=keyword)
            elif search_type == "all":
                articleList = articleList.filter(
                    Q(title__icontains=keyword) |
                    Q(member_id__nickname__icontains=keyword)
                )

        # 정렬
        sort = request.GET.get("sort", "recent")
        if sort == "title":
            articleList = articleList.order_by('title')
        elif sort == "views":
            articleList = articleList.order_by('-view_cnt')
        else:
            articleList = articleList.order_by('-reg_date')

        # 페이징
        per_page = int(request.GET.get("per_page", 15))
        
        paging = pager(request, articleList, per_page=per_page)
        
        #page = int(request.GET.get("page", 1))

        page_obj = paging['page_obj']

        
        page_start = (page_obj.number - 1) * per_page + 1

    except Exception as e:
        print({str(e)})
        articleList = []
        paging = pager(request, articleList, per_page=per_page)
        page_obj = paging['page_obj']

    bName = b_name(board_name)


    sort = request.GET.get("sort", "recent")
    
    is_manager_user = is_manager(request)

    context = {
        "page_obj": page_obj,
        "per_page": per_page,
        "page_start": page_start,
        "page": page_obj.number,
        "sort": sort,
        "block_range": paging['block_range'],
        "block_start": paging['block_start'],
        "block_end": paging['block_end'],
        "noticeList": noticeList,
        "board_id": b_id,
        "board_name" : board_name,
        "b_name" : bName,
        "is_manager" : is_manager_user
        
    }

    if b_id == 5 :
        return render(request, 'board/faq.html', context)
    return render(request, 'board/list.html', context)


def article_detail(request, board_name:str, article_id:int):
   
    # 로그인 체크
    redirect_response = check_login(request)
    if redirect_response:
        return redirect_response
    

    nickname = request.session.get('nickname')
    try:
        bName = b_name(board_name)
        board_id = get_board_by_name(board_name).board_id
        
        article_obj = Article.objects.select_related('member_id', 'board_id').get(
            article_id=article_id,
            board_id=board_id,
            delete_date__isnull=True
        )
         
        # 조회수 증가 (삭제되지 않은 게시글만)
        if not article_obj.delete_date:
            article_obj.view_cnt += 1
            article_obj.save(update_fields=['view_cnt'])
        
        # 댓글 조회 및 변환 (삭제된 댓글도 포함)
        comment_objs = Comment.objects.select_related('member_id').filter(
            article_id=article_id
        ).order_by('reg_date')
        
        comments = []
        for comment_obj in comment_objs:
            comment_author = comment_obj.member_id.nickname if comment_obj.member_id and hasattr(comment_obj.member_id, 'nickname') else '알 수 없음'
            comment_is_admin = comment_obj.member_id.manager_yn == 1 if comment_obj.member_id else False
            is_deleted = comment_obj.delete_date is not None
            
            comments.append({
                'comment_id': comment_obj.comment_id,
                'comment': comment_obj.comment,
                'author': comment_author,
                'is_admin': comment_is_admin,
                'reg_date': comment_obj.reg_date,
                'is_deleted': is_deleted,
            })
        
        
        author_name = article_obj.member_id.nickname if article_obj.member_id and hasattr(article_obj.member_id, 'nickname') else '알 수 없음'
        is_admin = article_obj.member_id.manager_yn == 1 if article_obj.member_id else False
        
        # 첨부파일 조회
        add_info_objs = AddInfo.objects.filter(article_id=article_id)
        files = []
        images = []
        for add_info in add_info_objs:
            file_ext = os.path.splitext(add_info.file_name)[1].lower()
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            file_data = {
                'id': add_info.add_info_id,
                'name': add_info.file_name,
                'url': f"{settings.MEDIA_URL}{add_info.path}",
                'is_image': is_image,
            }
            if is_image:
                images.append(file_data)
                # 이미지 파일도 다운로드 링크로 표시하기 위해 files에 추가
                files.append(file_data)
            else:
                files.append(file_data)
        
        article = {
            'article_id': article_obj.article_id,
            'title': article_obj.title,
            'contents': article_obj.contents if article_obj.contents else '',
            'author': author_name,
            'is_admin': is_admin,
            'date': article_obj.reg_date.strftime('%Y-%m-%d'),
            'views': article_obj.view_cnt,
            'reg_date': article_obj.reg_date,
            'images': images,  # 이미지 파일들
            'files': files,     # 일반 파일들 (PDF 등)
            'delete_date': article_obj.delete_date.strftime('%Y-%m-%d %H:%M') if article_obj.delete_date else None,
            'board_id' : article_obj.board_id_id,
        }
        
        is_manager_user = is_manager(request)

        is_author = (nickname and nickname.strip() == author_name.strip())

        context = {
            'article': article,
            'comments': comments,
            'board_name' : board_name,
            'is_author' : is_author,
            'b_name' : bName,
            "is_manager" : is_manager_user
        }
        
        return render(request, 'board/detail.html', context)
    
    except Exception as e:
        messages.error(request, f"게시글을 불러오는 중 오류가 발생했습니다: {str(e)}")
        return redirect('board:list', board_name)
    

# 수정 & 작성
def article_write(request, board_name:str, article_id:int=None):
   # 로그인 체크
    redirect_response = check_login(request)

    if redirect_response:
        return redirect_response
    
    b_id = get_board_by_name(board_name).board_id

    bName = b_name(board_name)

    user_id = request.session.get('user_id')
 
    member = Member.objects.get(user_id=user_id)

    # 수정
    if article_id:
        
        try:
            article = Article.objects.get(
                article_id=article_id,
                member_id=member,
                board_id=b_id
            )
        except Article.DoesNotExist:
            messages.error(request, "권한이 없습니다.")
            return redirect('board:list', board_name)

        start_date_str = ""
        end_date_str = ""

        if article.start_date:
            start_date_str = article.start_date.strftime("%Y-%m-%dT%H:%M")

        if article.end_date:
            end_date_str = article.end_date.strftime("%Y-%m-%dT%H:%M")

        # GET = 수정 페이지
        if request.method == "GET":
            context = {
                "article": article,
                "existing_files": get_existing_files(article_id),
                "start_date": start_date_str,
                "end_date": end_date_str,
                "is_edit": True,
                "boardId": b_id,
                "b_name": bName,
                "board_name" : board_name
            }
            return render(request, "board/write.html", context)

        # POST = 수정 처리
        elif request.method == "POST":
            return update_article(request, article, b_id, article_id)

    else:
        # GET = 빈 글쓰기 폼
        if request.method == "GET":

            context = {
                "boardId": b_id,
                "b_name": bName,
                "board_name" : board_name,
                "is_edit": False
            }
            return render(request, "board/write.html", context)

        # POST = 새 글 등록 처리
        elif request.method == "POST":
            return create_article(request, b_id, member)



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
def create_article(request, b_id, member_id):
    title = request.POST.get('title')
    contents = request.POST.get('context')
    board_name = Board.objects.get(board_id = b_id).board_name
    board = get_object_or_404(Board, board_id=b_id)

    article = Article(
        title=title,
        contents=contents,
        board_id=board,
        member_id=member_id
    )

    # 공지사항(board_id=2)일 때만 적용
    if b_id == 2:
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
    # handle_file_uploads(request, article)

    messages.success(request, "등록되었습니다.")
    return redirect('board:detail', board_name=board_name, article_id=article.article_id)



# 게시글 수정
def update_article(request, article, b_id, pk):

    title = request.POST.get('title')
    contents = request.POST.get('context')
    board_name = Board.objects.get(board_id = b_id).board_name
    article.title = title
    article.contents = contents

    if b_id == 2:
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
    # handle_file_uploads(request, article)

    messages.success(request, "수정되었습니다.")
    return redirect('board:detail', board_name=board_name, article_id=pk)

# 첨부파일 다운로드
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

# 댓글 작성 함수들
def article_comment(request, board_name:str, article_id:int):
    """공지사항 댓글 작성"""
    return create_comment(request, article_id, board_name)


def create_comment(request, article_id, board_type):
    """댓글 작성 공통 함수"""
    print(f"[DEBUG] create_comment 호출: article_id={article_id}, board_type={board_type}")
    
    # 로그인 체크
    redirect_response = check_login(request)
    if redirect_response:
        print(f"[DEBUG] create_comment: 로그인 필요 - 리다이렉트")
        return redirect_response
    
    if request.method != "POST":
        messages.error(request, "잘못된 요청입니다.")
        return redirect(f'/board/{board_type}/')
    
    try:
        # 로그인한 사용자 정보 가져오기 (관리자 우선)
        manager_id = request.session.get('manager_id')
        if manager_id:
            # 관리자인 경우
            member = Member.objects.get(member_id=manager_id)
        else:
            # 일반 사용자인 경우
            login_id = request.session.get('user_id')
            if not login_id:
                messages.error(request, "로그인이 필요합니다.")
                return redirect(f'/login?next=/board/{board_type}/{article_id}/')
            member = Member.objects.get(user_id=login_id)
        print(f"[DEBUG] create_comment: member={member.user_id}")
        
        # 게시글 확인
        board = get_board_by_name(board_type)
        article = Article.objects.get(
            article_id=article_id,
            board_id=board,
            delete_date__isnull=True
        )
        print(f"[DEBUG] create_comment: article={article.title}")
        
        # 댓글 내용 가져오기
        content = request.POST.get('content', '').strip()
        if not content:
            messages.error(request, "댓글 내용을 입력해주세요.")
            return redirect(f'/board/{board_type}/{article_id}/')
        
        # 댓글 생성
        comment = Comment.objects.create(
            comment=content,
            member_id=member,
            article_id=article,
        )
        
        print(f"[DEBUG] create_comment: 댓글 생성 성공 - comment_id={comment.comment_id}")
        
        messages.success(request, "댓글이 등록되었습니다.")
        return redirect(f'/board/{board_type}/{article_id}/')
        
    except Member.DoesNotExist:
        import traceback
        print(f"[ERROR] create_comment: Member.DoesNotExist - user_id={login_id}")
        print(traceback.format_exc())
        messages.error(request, "회원 정보를 찾을 수 없습니다.")
        return redirect(f'/login/')
    except Article.DoesNotExist:
        import traceback
        print(f"[ERROR] create_comment: Article.DoesNotExist - article_id={article_id}, board_type={board_type}")
        print(traceback.format_exc())
        messages.error(request, "게시글을 찾을 수 없습니다.")
        return redirect(f'/board/{board_type}/')
    except Board.DoesNotExist:
        import traceback
        print(f"[ERROR] create_comment: Board.DoesNotExist - board_type={board_type}")
        print(traceback.format_exc())
        messages.error(request, "게시판을 찾을 수 없습니다.")
        return redirect(f'/board/{board_type}/')
    except Exception as e:
        import traceback
        print(f"[ERROR] create_comment 오류: {str(e)}")
        print(f"[ERROR] article_id={article_id}, board_type={board_type}")
        print(traceback.format_exc())
        messages.error(request, f"댓글 작성 중 오류가 발생했습니다: {str(e)}")
        return redirect(f'/board/{board_type}/{article_id}/')


# 파일 업로드 처리 함수는 common/utils.py로 이동됨

@csrf_exempt
def delete_comment(request):
    """관리자 댓글 삭제 API (soft delete)"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'msg': '잘못된 요청입니다.'}, status=400)
    
    # 관리자 권한 확인
    if not is_manager(request):
        return JsonResponse({'status': 'error', 'msg': '관리자 권한이 필요합니다.'}, status=403)
    
    try:
        import json
        data = json.loads(request.body)
        comment_id = data.get('comment_id')
        
        if not comment_id:
            return JsonResponse({'status': 'error', 'msg': '댓글 ID가 필요합니다.'}, status=400)
        
        # 댓글 조회
        comment = Comment.objects.get(comment_id=comment_id)
        
        # 이미 삭제된 댓글인지 확인
        if comment.delete_date:
            return JsonResponse({'status': 'error', 'msg': '이미 삭제된 댓글입니다.'}, status=400)
        
        # Soft delete: delete_date 설정
        from datetime import datetime
        comment.delete_date = datetime.now()
        #comment.comment = '관리자에 의해 삭제된 댓글입니다.'
        comment.save()
        
        return JsonResponse({
            'status': 'ok',
            'msg': '댓글이 삭제되었습니다.',
            'comment_id': comment_id
        })
        
    except Comment.DoesNotExist:
        return JsonResponse({'status': 'error', 'msg': '댓글을 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        import traceback
        print(f"[ERROR] delete_comment 오류: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'msg': f'삭제 중 오류가 발생했습니다: {str(e)}'}, status=500)

# def faq(request):
#     return render(request, 'board/faq.html')