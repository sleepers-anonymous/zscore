from django.utils import timezone

t = timezone.get_current_timezone()

for s in Sleep.objects.all():
    if timezone.is_aware(s.start_time): s.start_time = timezone.make_naive(s.start_time, t)
    if timezone.is_aware(s.end_time): s.end_time = timezone.make_naive(s.end_time,t)
    s.save()
