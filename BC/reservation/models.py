from django.db import models


# Reservation (예약)
# -----------------------------------------------------
class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key=True)
    reservation_num = models.CharField(max_length=8)
    delete_yn = models.IntegerField(default=0)          # 예약상태 (0=예약중, 1=취소)
    reg_date = models.DateTimeField(auto_now_add=True)
    delete_date = models.DateTimeField(null=True, blank=True)
    expire_yn = models.IntegerField(default=0) 
    payment = models.IntegerField(default=0) 
   

    member = models.ForeignKey("member.Member", on_delete=models.DO_NOTHING)
    
    class Meta:
        db_table = "reservation"

    def __str__(self):
        return f"예약 {self.reservation_id}"


# Sports (운동종류)
# -----------------------------------------------------
class Sports(models.Model):
    sports_id = models.AutoField(primary_key=True)
    s_name = models.CharField(max_length=100)

    class Meta:
        db_table = "sports"

    def __str__(self):
        return self.s_name


# TimeSlot (예약된 시간테이블)
# -----------------------------------------------------
class TimeSlot(models.Model):
    t_id = models.AutoField(primary_key=True)
    date = models.DateField()
    start_time = models.CharField(max_length=20)
    end_time = models.CharField(max_length=20)
    delete_yn = models.IntegerField(default=0) 
    reservation_id = models.ForeignKey(Reservation, null=True, blank=True, on_delete=models.SET_NULL)
    facility_id = models.ForeignKey("facility.FacilityInfo", on_delete=models.CASCADE)

    class Meta:
        db_table = "time_slot"

    def __str__(self):
        return f"시간슬롯 {self.t_id}"