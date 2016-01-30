zscore
======

Sleeping competition app

Installing
----------

First, install the dependencies listed in requirements.txt

Next, follow the usual steps to installing a Django app:

1. Configure `zscore/local_settings.py`. The easiest way is to just copy over `zscore/local_settings.py.dev`.
2. Run `./manage.py migrate`

If you created an admin account in step 2 above, you'll need to create a `SleeperProfile` for it if you want to log in. Run `./manage.py shell`, and then run:

    from sleep.models import Sleeper
    Sleeper.objects.get(username='the_username').getOrCreateProfile()

At this point, you should be able to run `./manage.py runserver` successfully.
