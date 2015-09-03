from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from users.forms import UserEmailCreationForm
from sleep.models import SleeperProfile, Sleeper, Metric

class CreateUser(CreateView):
    model = Sleeper
    template_name = "users/create.html"
    form_class = UserEmailCreationForm
    success_url = "/"

    def form_valid(self, form):
        response = super(CreateUser, self).form_valid(form)
        s = SleeperProfile.objects.get_or_create(user=form.instance)[0]
        for m in Metric.objects.filter(show_by_default=True):
            s.metrics.add(m)
        s.save()
        return response
