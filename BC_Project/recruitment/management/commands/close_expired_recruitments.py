from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from recruitment.models import EndStatus

ALWAYS_OPEN_DATE = date(2099, 1, 1)


class Command(BaseCommand):
    help = "마감일이 지난 모집글을 자동 마감(end_stat=1) 처리합니다."

    @transaction.atomic
    def handle(self, *args, **options):
        today = date.today()

        qs = (
            EndStatus.objects
            .select_for_update()
            .filter(end_stat=0)
            .exclude(end_set_date=ALWAYS_OPEN_DATE)  
            .filter(end_set_date__lt=today)          
        )

        updated = qs.update(end_stat=1, end_date=today)
        self.stdout.write(self.style.SUCCESS(f"자동 마감 처리 완료: {updated}건"))
