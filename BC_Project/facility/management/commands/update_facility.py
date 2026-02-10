import os
import time
import requests

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone

from facility.models import Facility


class Command(BaseCommand):
    help = "전국체육시설 안전점검 API"

    def handle(self, *args, **options):
        API_KEY = os.getenv("DATA_API_KEY")
        if not API_KEY:
            self.stderr.write(self.style.ERROR("DATA_API_KEY 환경변수가 없습니다."))
            return

        base_url = "https://apis.data.go.kr/B551014/SRVC_API_FACI_SCHK_RESULT/TODZ_API_FACI_SAFETY"

        page_no = 1
        num_of_rows = 1000

        # 네트워크/공공 API 오류 대비
        max_retry = 3
        retry_sleep_sec = 2

        total_upserted = 0
        now = timezone.now()

        self.stdout.write("시설 안전점검 API 데이터 UPSERT 시작 (안정화 모드)")

        # DB 컬럼 목록 (모델 컬럼과 일치해야 함)
        columns = [
            "faci_cd", "faci_nm", "faci2_nm",
            "cp_nm", "cpb_nm", "fcob_nm", "ftype_nm",

            "faci_addr", "faci_road_addr", "faci_daddr", "faci_road_daddr",
            "faci_zip", "faci_gb_nm", "faci_lat", "faci_lot",

            "faci_stat_nm", "schk_tot_grd_nm", "schk_tot_grd_cd",

            "faci_mng_type_cd", "inout_gbn_nm", "atnm_chk_yn",
            "faci_tel_no", "faci_homepage",

            "faci_gfa",

            "base_ymd", "reg_dt", "faci_reg_ymd", "faci_upd_ymd",
            "schk_visit_ymd", "schk_open_ymd", "sdwn_ymd", "th_ymd",

            "row_num",
            "reg_date",
            "view_cnt",
        ]

        table_name = Facility._meta.db_table
        col_sql = ", ".join(f"`{c}`" for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))

        # faci_cd(키)는 업데이트 대상에서 제외
        update_cols = [c for c in columns if c != "faci_cd"]
        update_sql = ", ".join([f"`{c}` = VALUES(`{c}`)" for c in update_cols])

        insert_sql = f"""
            INSERT INTO `{table_name}` ({col_sql})
            VALUES ({placeholders})
            ON DUPLICATE KEY UPDATE {update_sql}
        """

        while True:
            params = {
                "serviceKey": API_KEY,
                "pageNo": page_no,
                "numOfRows": num_of_rows,
                "resultType": "json",
            }

   
            retry = 0
            while True:
                try:
                    res = requests.get(base_url, params=params, timeout=20)
           
                    if res.status_code >= 500:
                        raise requests.exceptions.HTTPError(f"Server error {res.status_code}")
                    res.raise_for_status()
                    break
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                    retry += 1
                    if retry > max_retry:
                        self.stderr.write(self.style.ERROR(f"API 요청 실패 (page {page_no}): {e}"))
                        return
                    self.stdout.write(self.style.WARNING(f"API 오류, 재시도 {retry}/{max_retry} (page {page_no})"))
                    time.sleep(retry_sleep_sec)

            body = res.json().get("response", {}).get("body", {})
            items = body.get("items", {}).get("item")

            if not items:
                break

            if isinstance(items, dict):
                items = [items]

            rows = []
            for item in items:
                faci_cd = item.get("faci_cd")
                if not faci_cd:
                    continue

                row = [
                    item.get("faci_cd"),
                    item.get("faci_nm"),
                    item.get("faci2_nm"),

                    item.get("cp_nm"),
                    item.get("cpb_nm"),
                    item.get("fcob_nm"),
                    item.get("ftype_nm"),

                    item.get("faci_addr"),
                    item.get("faci_road_addr"),
                    item.get("faci_daddr"),
                    item.get("faci_road_daddr"),
                    item.get("faci_zip"),
                    item.get("faci_gb_nm"),
                    item.get("faci_lat"),
                    item.get("faci_lot"),

                    item.get("faci_stat_nm"),
                    item.get("schk_tot_grd_nm"),
                    item.get("schk_tot_grd_cd"),

                    item.get("faci_mng_type_cd"),
                    item.get("inout_gbn_nm"),
                    item.get("atnm_chk_yn"),
                    item.get("faci_tel_no"),
                    item.get("faci_homepage"),

                    item.get("faci_gfa"),

                    item.get("base_ymd"),
                    item.get("reg_dt"),
                    item.get("faci_reg_ymd"),
                    item.get("faci_upd_ymd"),
                    item.get("schk_visit_ymd"),
                    item.get("schk_open_ymd"),
                    item.get("sdwn_ymd"),
                    item.get("th_ymd"),

                    item.get("row_num"),
                    now,
                    0,
                ]

                row = [None if (v == "" or v == " ") else v for v in row]
                rows.append(tuple(row))

            if rows:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.executemany(insert_sql, rows)

                total_upserted += len(rows)
                self.stdout.write(f"  - {page_no} 페이지 UPSERT 완료 (누적 {total_upserted})")

            page_no += 1

        self.stdout.write(self.style.SUCCESS(f"완료! 총 {total_upserted}건 UPSERT 처리"))
