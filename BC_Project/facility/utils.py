from django.db.models import Q
from facility.models import Facility, FacilityInfo


def build_facility_queryset(
    *,
    cp_nm=None,
    cpb_nm=None,
    keyword=None,
    public_only=True,
    normal_only=False,
    exclude_registered=False,
):

    qs = Facility.objects.all()


    if cp_nm:
        qs = qs.filter(cp_nm=cp_nm)

    if cpb_nm:
        if qs.filter(cpb_nm=cpb_nm).exists():
            qs = qs.filter(cpb_nm=cpb_nm)
        else:
            qs = qs.filter(
                Q(faci_addr__icontains=cpb_nm) |
                Q(faci_road_addr__icontains=cpb_nm)
            )
    if keyword:
        qs = qs.filter(faci_nm__icontains=keyword)

    if public_only:
        qs = qs.filter(faci_gb_nm__icontains="공공")

    if normal_only:
        qs = qs.filter(faci_stat_nm__icontains="정상")

    if exclude_registered:
        registered_ids = FacilityInfo.objects.values_list(
            "facility_id", flat=True
        )
        qs = qs.exclude(faci_cd__in=registered_ids)

    return qs
