from django.db import models


# FacilityInfo (시설)
# -----------------------------------------------------
class FacilityInfo(models.Model):
    facility_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    # 사진 업로드
    photo = models.ImageField(upload_to="facility_photos/", null=True, blank=True)

    # 예약 시간대 JSON
    reservation_time = models.JSONField(null=True, blank=True)

    # Facility 테이블 원본 복사본
    faci_nm = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    sido = models.CharField(max_length=200, null=True, blank=True)
    sigugun = models.CharField(max_length=200, null=True, blank=True)
    tel = models.CharField(max_length=50, null=True, blank=True)
    homepage = models.CharField(max_length=200, null=True, blank=True)
    # 예약가능한상태인지(0: 불가 1: 가능)
    rs_posible = models.IntegerField(default=0) 
    faci_gb_nm = models.CharField(max_length=200,null=True, blank=True)
    faci_stat_nm = models.CharField(max_length=200,null=True, blank=True)
    reg_date = models.DateTimeField(auto_now_add=True)
    view_cnt = models.IntegerField(default=0)
    class Meta:
        db_table = "facility_info"

    def __str__(self):
        return self.faci_nm


class Facility(models.Model):
    faci_cd = models.CharField(max_length=50, unique=True)

    faci_nm = models.CharField(max_length=200, null=True, blank=True)
    faci2_nm = models.CharField(max_length=200, null=True, blank=True)
    cp_nm = models.CharField(max_length=50, null=True, blank=True)
    cpb_nm = models.CharField(max_length=50, null=True, blank=True)
    fcob_nm = models.CharField(max_length=100, null=True, blank=True)
    ftype_nm = models.CharField(max_length=100, null=True, blank=True)

    faci_addr = models.CharField(max_length=300, null=True, blank=True)
    faci_road_addr = models.CharField(max_length=300, null=True, blank=True)
    faci_daddr = models.CharField(max_length=300, null=True, blank=True)
    faci_road_daddr = models.CharField(max_length=300, null=True, blank=True)
    faci_zip = models.CharField(max_length=20, null=True, blank=True)
    faci_gb_nm = models.CharField(max_length=200,null=True, blank=True)
    faci_lat = models.FloatField(null=True, blank=True)
    faci_lot = models.FloatField(null=True, blank=True)

    faci_stat_nm = models.CharField(max_length=50, null=True, blank=True)
    schk_tot_grd_nm = models.CharField(max_length=50, null=True, blank=True)
    schk_tot_grd_cd = models.CharField(max_length=5, null=True, blank=True)

    faci_mng_type_cd = models.CharField(max_length=20, null=True, blank=True)
    inout_gbn_nm = models.CharField(max_length=10, null=True, blank=True)
    atnm_chk_yn = models.CharField(max_length=1, null=True, blank=True)
    faci_tel_no = models.CharField(max_length=50, null=True, blank=True)
    faci_homepage = models.CharField(max_length=200, null=True, blank=True)

    faci_gfa = models.CharField(max_length=50, null=True, blank=True)

    base_ymd = models.CharField(max_length=20, null=True, blank=True)
    reg_dt = models.CharField(max_length=20, null=True, blank=True)
    faci_reg_ymd = models.CharField(max_length=20, null=True, blank=True)
    faci_upd_ymd = models.CharField(max_length=20, null=True, blank=True)
    schk_visit_ymd = models.CharField(max_length=20, null=True, blank=True)
    schk_open_ymd = models.CharField(max_length=20, null=True, blank=True)
    sdwn_ymd = models.CharField(max_length=20, null=True, blank=True)
    th_ymd = models.CharField(max_length=20, null=True, blank=True)
    view_cnt = models.IntegerField(default=0)
    row_num = models.IntegerField(null=True, blank=True)

    reg_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "facility"
        
    def __str__(self):
        return f"{self.faci_nm} ({self.faci_cd})"