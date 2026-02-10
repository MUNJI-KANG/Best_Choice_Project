"""
Board 관련 유틸리티 함수
"""
from board.models import Category, Board
from django.core.exceptions import ObjectDoesNotExist, ValidationError


def get_category_by_type(category_type):
    """
    category_type으로 Category 조회 (대소문자 무시)
    
    Args:
        category_type: str ('recruitment', 'notice', 'event', 'post')
    
    Returns:
        Category 객체
    
    Raises:
        Category.DoesNotExist: 카테고리를 찾을 수 없을 때
        ValidationError: 유효하지 않은 category_type일 때
    """
    category_type = category_type.lower().strip()  # 소문자로 통일, 공백 제거
    
    valid_types = ['recruitment', 'notice', 'event', 'post']
    if category_type not in valid_types:
        raise ValidationError(f"유효하지 않은 category_type: {category_type}. 유효한 값: {valid_types}")
    
    return Category.objects.get(category_type=category_type)


def get_board_by_name(board_name):
    """
    board_name으로 Board 조회 (대소문자 무시)
    
    Args:
        board_name: str ('recruitment', 'notice', 'event', 'post')
    
    Returns:
        Board 객체
    
    Raises:
        Board.DoesNotExist: 게시판을 찾을 수 없을 때
        ValidationError: 유효하지 않은 board_name일 때
    """
    board_name = board_name.lower().strip()  # 소문자로 통일, 공백 제거
    
    valid_names = ['recruitment', 'notice', 'event', 'post', 'faq']
    if board_name not in valid_names:
        raise ValidationError(f"유효하지 않은 board_name: {board_name}. 유효한 값: {valid_names}")
    
    return Board.objects.get(board_name=board_name)


def validate_initial_data():
    """
    초기 데이터가 올바르게 생성되었는지 검증
    
    Returns:
        tuple: (is_valid, missing_items)
            is_valid: bool - 모든 필수 데이터가 존재하는지 여부
            missing_items: dict - 누락된 항목들
                {
                    'categories': list,
                    'boards': list
                }
    """
    required_categories = {'recruitment', 'notice', 'event', 'post'}
    required_boards = {'recruitment', 'notice', 'event', 'post'}
    
    existing_categories = set(Category.objects.values_list('category_type', flat=True))
    existing_boards = set(Board.objects.values_list('board_name', flat=True))
    
    missing_categories = required_categories - existing_categories
    missing_boards = required_boards - existing_boards
    
    is_valid = len(missing_categories) == 0 and len(missing_boards) == 0
    missing_items = {
        'categories': list(missing_categories),
        'boards': list(missing_boards)
    }
    
    return is_valid, missing_items

