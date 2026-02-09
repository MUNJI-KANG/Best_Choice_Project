from django.db import models

# -----------------------------------------------------
# HeroImg
# -----------------------------------------------------

class HeroImg(models.Model):
    img_id = models.AutoField(primary_key=True)
    url = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    context = models.CharField(max_length=200)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    reg_date = models.DateTimeField(auto_now_add=True)
    delete_date = models.DateTimeField(null=True, blank=True)
    img_status = models.IntegerField(default=0)

    class Meta:
        db_table = "hero_img"

    def __str__(self):
        return self.title