from django.db import models


# Create your models here.
# -----------------------------------------------------
# Comment (댓글)
# -----------------------------------------------------
class Comment(models.Model):
    comment_id = models.AutoField(primary_key=True)
    comment = models.TextField()
    reg_date = models.DateTimeField(auto_now_add=True)
    delete_date = models.DateTimeField(null=True, blank=True)

    member_id = models.ForeignKey("member.Member", on_delete=models.DO_NOTHING)
    community_id = models.ForeignKey("recruitment.Community", null=True, blank=True, on_delete=models.CASCADE)
    article_id = models.ForeignKey("board.Article", null=True, blank=True, on_delete=models.CASCADE)
    board_id = models.ForeignKey("board.Board", null=True, blank=True, on_delete=models.CASCADE)
    facility = models.ForeignKey(
        "facility.Facility",
        to_field="faci_cd",
        db_column="facility",
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    class Meta:
        db_table = "comment"

    def __str__(self):
        return f"댓글 {self.comment_id}"


# -----------------------------------------------------
# AddInfo (첨부파일)
# -----------------------------------------------------
class AddInfo(models.Model):
    add_info_id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=255)  # 경로가 길 수 있으므로 255로 증가
    file_name = models.CharField(max_length=100)
    encoded_name = models.CharField(max_length=200)
    reg_date = models.DateTimeField(auto_now_add=True)

    article_id = models.ForeignKey("board.Article", null=True, blank=True, on_delete=models.SET_NULL)
    community_id = models.ForeignKey("recruitment.Community", null=True, blank=True, on_delete=models.SET_NULL)
    facility_id = models.ForeignKey("facility.FacilityInfo", null=True, blank=True, on_delete=models.SET_NULL)
    img_id = models.ForeignKey("manager.HeroImg", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "add_info"

    def __str__(self):
        return self.file_name