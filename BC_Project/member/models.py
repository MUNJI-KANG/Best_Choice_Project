from django.db import models

# Create your models here.
# -----------------------------------------------------
# Member (사용자)
# -----------------------------------------------------
class Member(models.Model):
    member_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    user_id = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=500)
    nickname = models.CharField(max_length=20, unique=True)
    birthday = models.CharField(max_length=20)
    gender = models.IntegerField()
    addr1 = models.CharField(max_length=200)
    addr2 = models.CharField(max_length=200, null=True, blank=True)
    addr3 = models.CharField(max_length=200, null=True, blank=True)
    phone_num = models.CharField(max_length=500, unique=True)
    delete_yn = models.IntegerField(default=0)                  # 탈퇴여부(0=지금회원, 1=탈퇴)
    reg_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    delete_date = models.DateTimeField(null=True, blank=True)
    manager_yn = models.IntegerField(default=0)
    delete_reason = models.CharField(max_length=200, null=True)

    class Meta:
        db_table = "member"

    def __str__(self):
        return self.user_id