from django.db import models


# Community (모집글)
# -----------------------------------------------------
class Community(models.Model):
    community_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    contents = models.TextField()
    region = models.CharField(max_length=10)
    region2 = models.CharField(max_length=10)
    sport_type = models.CharField(max_length=10)
    facility = models.CharField(max_length=100, default="미정")
    num_member = models.IntegerField()

    reg_date = models.DateTimeField(auto_now_add=True)
    chat_url = models.CharField(max_length=100, null=True, blank=True)
    view_cnt = models.IntegerField(default=0)
    update_date = models.DateTimeField(auto_now=True)
    delete_date = models.DateTimeField(null=True, blank=True)

    member_id = models.ForeignKey("member.Member", on_delete=models.CASCADE)
    reservation_id = models.ForeignKey("reservation.Reservation", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "community"

    def __str__(self):
        return f"모집글 {self.community_id}"
    
# EndStatus (마감 상황)
# -----------------------------------------------------
class EndStatus(models.Model):
    community = models.OneToOneField(Community,primary_key=True,on_delete=models.CASCADE)  # community_id로 변경 필요? (11/27)
    end_date = models.DateField(null=True, blank=True)
    end_set_date = models.DateField()               # 마감 지정날짜
    end_stat = models.IntegerField(default=0)       # 마감여부(0=마감안됨, 1=마감)

    class Meta:
        db_table = "end_status"

    def __str__(self):
        return f"Community {self.community_id} 마감상태"
    
# Rating (평점)
# -----------------------------------------------------
class Rating(models.Model):
    rating_id = models.AutoField(primary_key=True)
    facility = models.CharField(max_length=100)
    rated = models.IntegerField(default=0)
    comments = models.TextField(null=True, blank=True)
    reg_date = models.DateTimeField(auto_now_add=True)  # auto_now_add 권장 (생성 시점만)
    # update_date는 불필요 (별개 평점이므로)
    
    community_id = models.ForeignKey(Community, null=True, blank=True, on_delete=models.DO_NOTHING)
    member_id = models.ForeignKey("member.Member", on_delete=models.DO_NOTHING)
    reservation_id = models.ForeignKey("reservation.Reservation", null=True, blank=True, on_delete=models.CASCADE)
    
    class Meta:
        db_table = "rating"
        constraints = [  # 필요! (같은 예약에 중복 방지)
            models.UniqueConstraint(
                fields=["member_id", "reservation_id"],
                condition=models.Q(reservation_id__isnull=False),
                name="unique_rating_per_reservation"
            ),
        ]

    def __str__(self):
        return f"{self.facility} - {self.rated}점"
    
# JoinStat (참석 여부) — 복합 PK
# -----------------------------------------------------
class JoinStat(models.Model):
    member_id = models.ForeignKey("member.Member", on_delete=models.CASCADE)
    community_id = models.ForeignKey(Community, on_delete=models.CASCADE)
    join_status = models.IntegerField(default=0)

    class Meta:
        db_table = "join_stat"
        constraints = [
            models.UniqueConstraint(
                fields=["member_id", "community_id"],
                name="pk_join_stat"
            )
        ]
