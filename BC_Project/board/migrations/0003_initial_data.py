# Generated manually for initial data

from django.db import migrations
from django.db import IntegrityError


def create_initial_data(apps, schema_editor):
    """
    Category와 Board 초기 데이터 생성
    - unique 제약으로 중복 방지
    - 대소문자 통일 (소문자)
    - 예외 처리 강화
    """
    Category = apps.get_model('board', 'Category')
    Board = apps.get_model('board', 'Board')
    
    # Category 초기 데이터 (소문자로 통일)
    categories = [
        'recruitment',
        'notice',
        'event',
        'post',
    ]
    
    created_categories = []
    for category_type in categories:
        try:
            category, created = Category.objects.get_or_create(
                category_type=category_type
            )
            if created:
                created_categories.append(category)
                print(f"[OK] Category 생성: {category.category_type} (ID: {category.category_id})")
            else:
                print(f"[SKIP] Category 이미 존재: {category.category_type} (ID: {category.category_id})")
        except IntegrityError as e:
            print(f"[ERROR] Category 생성 실패 ({category_type}): {str(e)}")
        except Exception as e:
            print(f"[ERROR] Category 생성 오류 ({category_type}): {str(e)}")
    
    # Board 초기 데이터 (소문자로 통일)
    boards = [
        'recruitment',
        'notice',
        'event',
        'post',
    ]
    
    created_boards = []
    for board_name in boards:
        try:
            board, created = Board.objects.get_or_create(
                board_name=board_name
            )
            if created:
                created_boards.append(board)
                print(f"[OK] Board 생성: {board.board_name} (ID: {board.board_id})")
            else:
                print(f"[SKIP] Board 이미 존재: {board.board_name} (ID: {board.board_id})")
        except IntegrityError as e:
            print(f"[ERROR] Board 생성 실패 ({board_name}): {str(e)}")
        except Exception as e:
            print(f"[ERROR] Board 생성 오류 ({board_name}): {str(e)}")
    
    # 검증: 필수 데이터 확인
    required_categories = set(categories)
    required_boards = set(boards)
    
    existing_categories = set(Category.objects.values_list('category_type', flat=True))
    existing_boards = set(Board.objects.values_list('board_name', flat=True))
    
    missing_categories = required_categories - existing_categories
    missing_boards = required_boards - existing_boards
    
    if missing_categories:
        raise ValueError(f"필수 Category가 생성되지 않았습니다: {missing_categories}")
    if missing_boards:
        raise ValueError(f"필수 Board가 생성되지 않았습니다: {missing_boards}")
    
    print(f"\n{'='*50}")
    print(f"초기 데이터 생성 완료:")
    print(f"  - Category: {len(created_categories)}개 생성, 총 {len(existing_categories)}개 존재")
    print(f"  - Board: {len(created_boards)}개 생성, 총 {len(existing_boards)}개 존재")
    print(f"{'='*50}")


def reverse_initial_data(apps, schema_editor):
    """
    롤백 시 초기 데이터 삭제
    - Article에서 참조 중인 것은 보존
    - 안전한 삭제
    """
    Category = apps.get_model('board', 'Category')
    Board = apps.get_model('board', 'Board')
    Article = apps.get_model('board', 'Article')
    
    try:
        # Article에서 사용 중인 Category 확인
        used_category_ids = set(
            Article.objects.exclude(category_id__isnull=True)
            .values_list('category_id', flat=True)
            .distinct()
        )
        
        # 사용 중이 아닌 Category만 삭제
        categories_to_delete = Category.objects.filter(
            category_type__in=['recruitment', 'notice', 'event', 'post']
        ).exclude(category_id__in=used_category_ids)
        
        deleted_category_count = categories_to_delete.count()
        if deleted_category_count > 0:
            categories_to_delete.delete()
            print(f"[OK] Category {deleted_category_count}개 삭제 (사용 중인 {len(used_category_ids)}개는 보존)")
        else:
            print(f"[SKIP] 삭제할 Category 없음 (모두 사용 중)")
        
        # Article에서 사용 중인 Board 확인
        used_board_ids = set(
            Article.objects.values_list('board_id', flat=True).distinct()
        )
        
        # 사용 중이 아닌 Board만 삭제
        boards_to_delete = Board.objects.filter(
            board_name__in=['recruitment', 'notice', 'event', 'post']
        ).exclude(board_id__in=used_board_ids)
        
        deleted_board_count = boards_to_delete.count()
        if deleted_board_count > 0:
            boards_to_delete.delete()
            print(f"[OK] Board {deleted_board_count}개 삭제 (사용 중인 {len(used_board_ids)}개는 보존)")
        else:
            print(f"[SKIP] 삭제할 Board 없음 (모두 사용 중)")
            
    except Exception as e:
        print(f"[ERROR] 롤백 중 오류 발생: {str(e)}")
        # 롤백 실패해도 마이그레이션은 진행 (데이터는 보존)


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0004_alter_category_category_type'),
    ]

    operations = [
        migrations.RunPython(
            create_initial_data, 
            reverse_initial_data,
            atomic=True  # 트랜잭션으로 실행
        ),
    ]

