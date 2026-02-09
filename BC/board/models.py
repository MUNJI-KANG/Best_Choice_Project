from django.db import models

# Board (게시판)
# -----------------------------------------------------
class Board(models.Model):
    board_id = models.AutoField(primary_key=True)
    board_name = models.CharField(max_length=200, unique=True)

    class Meta:
        db_table = "board"
        verbose_name = "게시판"
        verbose_name_plural = "게시판"

    def __str__(self):
        return self.board_name


# Article (게시글)
# -----------------------------------------------------
class Article(models.Model):
    article_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    contents = models.TextField()
    view_cnt = models.IntegerField(default=0)
    update_date = models.DateTimeField(auto_now=True)
    delete_date = models.DateTimeField(null=True, blank=True)
    reg_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    always_on = models.IntegerField(default=1)              # 상시표시 (0=상시표시, 1=상시표시x)

    member_id = models.ForeignKey("member.Member", on_delete=models.DO_NOTHING)
    board_id = models.ForeignKey(Board, on_delete=models.CASCADE)
    category_id = models.ForeignKey("board.Category", null=True, blank=True, on_delete=models.SET_NULL)

    etc_int1 = models.IntegerField(null=True, blank=True)
    etc_int2 = models.IntegerField(null=True, blank=True)
    etc_int3 = models.IntegerField(null=True, blank=True)

    etc_text1 = models.CharField(max_length=100, null=True, blank=True)
    etc_text2 = models.CharField(max_length=100, null=True, blank=True)
    etc_text3 = models.CharField(max_length=100, null=True, blank=True)

    etc_date1 = models.DateTimeField(null=True, blank=True)
    etc_date2 = models.DateTimeField(null=True, blank=True)
    etc_date3 = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "article"

    def __str__(self):
        return self.title


# Category (카테고리)
# -----------------------------------------------------
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_type = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = "catergory"
        verbose_name = "카테고리"
        verbose_name_plural = "카테고리"

    def __str__(self):
        return f"{self.category_type} (ID: {self.category_id})"