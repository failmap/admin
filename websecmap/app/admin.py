import string
from datetime import datetime, timedelta
from random import choice

import pytz
from constance.admin import Config, ConstanceAdmin, ConstanceForm
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.contrib.humanize.templatetags.humanize import naturaltime

# overwrites for period tasks, allowing import and export buttons to work.
from django.utils.safestring import mark_safe
from django_celery_beat.admin import PeriodicTaskAdmin, PeriodicTaskForm
from django_celery_beat.models import CrontabSchedule, IntervalSchedule, PeriodicTask, SolarSchedule
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from websecmap.app.models import GameUser, Job, Volunteer


class JobAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("name", "result_id", "status", "created_by", "created_on", "finished_on")
    list_filter = ("status", "created_by")
    readonly_fields = ("name", "task", "result_id", "result", "status", "created_on", "finished_on")


admin.site.register(Job, JobAdmin)


class MyPeriodicTaskForm(PeriodicTaskForm):

    fieldsets = PeriodicTaskAdmin.fieldsets

    """
    Interval schedule does not support due_ or something. Which is absolutely terrible and vague.
    I can't understand why there is not an is_due() for each type of schedule. This makes it very hazy
    when something will run.

    Because of this, we'll move to the horrifically designed absolute nightmare format Crontab.
    Crontab would be half-great if the parameters where named.

    Get your crontab guru going, this is the only way you'll understand what you're doing.
    https://crontab.guru/#0_21_*_*_*
    """

    def clean(self):

        cleaned_data = super(PeriodicTaskForm, self).clean()

        # if not self.cleaned_data['last_run_at']:
        #     self.cleaned_data['last_run_at'] = datetime.now(pytz.utc)

        return cleaned_data


class IEPeriodicTaskAdmin(PeriodicTaskAdmin, ImportExportModelAdmin):
    # most / all time schedule functions in celery beat are moot. So the code below likely makes no sense.

    list_display = (
        "name_safe",
        "enabled",
        "interval",
        "crontab",
        "next",
        "due",
        "precise",
        "last_run_at",
        "queue",
        "task",
        "args",
        "last_run",
        "runs",
    )

    list_filter = ("enabled", "queue", "crontab")

    search_fields = ("name", "queue", "args")

    form = MyPeriodicTaskForm

    save_as = True

    @staticmethod
    def name_safe(obj):
        return mark_safe(obj.name)

    @staticmethod
    def last_run(obj):
        return obj.last_run_at

    @staticmethod
    def runs(obj):
        # print(dir(obj))
        return obj.total_run_count

    @staticmethod
    def due(obj):
        if obj.last_run_at:
            return obj.schedule.remaining_estimate(last_run_at=obj.last_run_at)
        else:
            # y in seconds
            z, y = obj.schedule.is_due(last_run_at=datetime.now(pytz.utc))
            date = datetime.now(pytz.utc) + timedelta(seconds=y)

            return naturaltime(date)

    @staticmethod
    def precise(obj):
        if obj.last_run_at:
            return obj.schedule.remaining_estimate(last_run_at=obj.last_run_at)
        else:
            return obj.schedule.remaining_estimate(last_run_at=datetime.now(pytz.utc))

    @staticmethod
    def next(obj):
        if obj.last_run_at:
            return obj.schedule.remaining_estimate(last_run_at=obj.last_run_at)
        else:
            # y in seconds
            z, y = obj.schedule.is_due(last_run_at=datetime.now(pytz.utc))
            # somehow the cron jobs still give the correct countdown even last_run_at is not set.

            date = datetime.now(pytz.utc) + timedelta(seconds=y)

            return date

    class Meta:
        ordering = ["-name"]


class IEUser(ImportExportModelAdmin):
    pass


class IEGroup(ImportExportModelAdmin):
    pass


class IESolarSchedule(ImportExportModelAdmin):
    pass


class IECrontabSchedule(ImportExportModelAdmin):
    pass


class IEIntervalSchedule(ImportExportModelAdmin):
    pass


admin.site.unregister(PeriodicTask)
admin.site.unregister(SolarSchedule)
admin.site.unregister(CrontabSchedule)
admin.site.unregister(IntervalSchedule)
admin.site.register(PeriodicTask, IEPeriodicTaskAdmin)
admin.site.register(SolarSchedule, IESolarSchedule)
admin.site.register(CrontabSchedule, IECrontabSchedule)
admin.site.register(IntervalSchedule, IEIntervalSchedule)


class VolunteerInline(admin.StackedInline):
    model = Volunteer
    can_delete = False
    verbose_name_plural = "Volunteer information"


class GameUserInline(admin.StackedInline):
    model = GameUser
    can_delete = False
    verbose_name_plural = "Game Users"


# Thank you:
# https://stackoverflow.com/questions/47941038/how-should-i-add-django-import-export-on-the-user-model?rq=1
class UserResource(resources.ModelResource):
    class Meta:
        model = User
        # fields = ('first_name', 'last_name', 'email')


class GroupResource(resources.ModelResource):
    class Meta:
        model = Group


def generate_password():
    password = "".join(choice("ACDEFGHKLMNPRSTUVWXZ234567") for i in range(20))
    return "%s-%s-%s-%s-%s" % (password[0:4], password[4:8], password[8:12], password[12:16], password[16:20])


def generate_username():
    # generate nice names like docker container names
    # https://github.com/moby/moby/blob/master/pkg/namesgenerator/names-generator.go

    # slightly redacted list to make all names always positive.
    traits = [
        "admiring",
        "adoring",
        "affectionate",
        "amazing",
        "awesome",
        "blissful",
        "bold",
        "brave",
        "charming",
        "clever",
        "cool",
        "compassionate",
        "competent",
        "confident",
        "crazy",
        "dazzling",
        "determined",
        "dreamy",
        "eager",
        "ecstatic",
        "elastic",
        "elated",
        "elegant",
        "eloquent",
        "epic",
        "fervent",
        "festive",
        "flamboyant",
        "focused",
        "friendly",
        "gallant",
        "gifted",
        "goofy",
        "gracious",
        "happy",
        "hardcore",
        "heuristic",
        "hopeful",
        "infallible",
        "inspiring",
        "jolly",
        "jovial",
        "keen",
        "kind",
        "laughing",
        "loving",
        "lucid",
        "magical",
        "mystifying",
        "modest",
        "musing",
        "naughty",
        "nifty",
        "nostalgic",
        "objective",
        "optimistic",
        "peaceful",
        "pensive",
        "practical",
        "priceless",
        "quizzical",
        "recursing",
        "relaxed",
        "reverent",
        "romantic",
        "serene",
        "sharp",
        "silly",
        "sleepy",
        "sweet",
        "tender",
        "trusting",
        "unruffled",
        "upbeat",
        "vibrant",
        "vigilant",
        "vigorous",
        "wizardly",
        "wonderful",
        "youthful",
        "zealous",
        "zen",
    ]

    # See the elaborate explanations of all these names in the original file.
    names = [
        "albattani",
        "allen",
        "almeida",
        "antonelli",
        "agnesi",
        "archimedes",
        "ardinghelli",
        "aryabhata",
        "austin",
        "babbage",
        "banach",
        "banzai",
        "bardeen",
        "bartik",
        "bassi",
        "beaver",
        "bell",
        "benz",
        "bhabha",
        "bhaskara",
        "black",
        "blackburn",
        "blackwell",
        "bohr",
        "booth",
        "borg",
        "bose",
        "boyd",
        "brahmagupta",
        "brattain",
        "brown",
        "burnell",
        "buck",
        "burnell",
        "cannon",
        "carson",
        "cartwright",
        "chandrasekhar",
        "chaplygin",
        "chatelet",
        "chatterjee",
        "chebyshev",
        "cocks",
        "cohen",
        "chaum",
        "clarke",
        "colden",
        "cori",
        "cray",
        "curran",
        "curie",
        "darwin",
        "davinci",
        "dewdney",
        "dhawan",
        "diffie",
        "dijkstra",
        "dirac",
        "driscoll",
        "dubinsky",
        "easley",
        "edison",
        "einstein",
        "elbakyan",
        "elgamal",
        "elion",
        "ellis",
        "engelbart",
        "euclid",
        "euler",
        "faraday",
        "feistel",
        "fermat",
        "fermi",
        "feynman",
        "franklin",
        "gagarin",
        "galileo",
        "galois",
        "ganguly",
        "gates",
        "gauss",
        "germain",
        "goldberg",
        "goldstine",
        "goldwasser",
        "golick",
        "goodall",
        "gould",
        "greider",
        "grothendieck",
        "haibt",
        "hamilton",
        "haslett",
        "hawking",
        "hellman",
        "heisenberg",
        "hermann",
        "herschel",
        "hertz",
        "heyrovsky",
        "hodgkin",
        "hofstadter",
        "hoover",
        "hopper",
        "hugle",
        "hypatia",
        "ishizaka",
        "jackson",
        "jang",
        "jennings",
        "jepsen",
        "johnson",
        "joliot",
        "jones",
        "kalam",
        "kapitsa",
        "kare",
        "keldysh",
        "keller",
        "kepler",
        "khayyam",
        "khorana",
        "kilby",
        "kirch",
        "knuth",
        "kowalevski",
        "lalande",
        "lamarr",
        "lamport",
        "leakey",
        "leavitt",
        "lederberg",
        "lehmann",
        "lewin",
        "lichterman",
        "liskov",
        "lovelace",
        "lumiere",
        "mahavira",
        "margulis",
        "matsumoto",
        "maxwell",
        "mayer",
        "mccarthy",
        "mcclintock",
        "mclaren",
        "mclean",
        "mcnulty",
        "mendel",
        "mendeleev",
        "meitner",
        "meninsky",
        "merkle",
        "mestorf",
        "minsky",
        "mirzakhani",
        "moore",
        "morse",
        "murdock",
        "moser",
        "napier",
        "nash",
        "neumann",
        "newton",
        "nightingale",
        "nobel",
        "noether",
        "northcutt",
        "noyce",
        "panini",
        "pare",
        "pascal",
        "pasteur",
        "payne",
        "perlman",
        "pike",
        "poincare",
        "poitras",
        "proskuriakova",
        "ptolemy",
        "raman",
        "ramanujan",
        "ride",
        "montalcini",
        "ritchie",
        "rhodes",
        "robinson",
        "roentgen",
        "rosalind",
        "rubin",
        "saha",
        "sammet",
        "sanderson",
        "shannon",
        "shaw",
        "shirley",
        "shockley",
        "shtern",
        "sinoussi",
        "snyder",
        "solomon",
        "spence",
        "sutherland",
        "stallman",
        "stonebraker",
        "swanson",
        "swartz",
        "swirles",
        "taussig",
        "tereshkova",
        "tesla",
        "tharp",
        "thompson",
        "torvalds",
        "tu",
        "turing",
        "varahamihira",
        "vaughan",
        "visvesvaraya",
        "volhard",
        "villani",
        "wescoff",
        "wiles",
        "williams",
        "williamson",
        "wilson",
        "wing",
        "wozniak",
        "wright",
        "wu",
        "yalow",
        "yonath",
        "zhukovsky",
    ]

    return "%s %s" % (choice(traits).capitalize(), choice(names).capitalize())


def generate_game_user():
    game_user_number = User.objects.all().filter(username__contains="game_user_").count()
    game_user_number += 1

    password = generate_password()

    user = User.objects.create_user(
        username="game_user_%s" % game_user_number,
        # can log into other things
        is_active=True,
        # No access to admin interface needed
        is_staff=False,
        # No permissions needed anywhere
        is_superuser=False,
        password=password,
    )
    user.save()

    # store the password to this account in plain text. It doesn't have any permissions so well...
    # in django we trust :)
    game_user = GameUser()
    game_user.user = user
    game_user.password = password
    game_user.save()

    return user


class UserAdmin(BaseUserAdmin, ImportExportModelAdmin):
    resource_class = UserResource
    inlines = (VolunteerInline, GameUserInline)

    list_display = (
        "username",
        "organization",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "in_groups",
    )

    actions = []

    def add_game_user(self, request, queryset):
        generate_game_user()
        self.message_user(request, "Game user added, rename if needed!")

    add_game_user.short_description = "💖 Add Game User (select a user first)"
    actions.append(add_game_user)

    def add_volunteer(self, request, queryset):

        # password is random and non-recoverable. It has to be set explicitly by the admin
        alphabet = string.ascii_letters + string.digits
        password = "".join(choice(alphabet) for i in range(42))

        # determine number:
        volunteer_number = User.objects.all().filter(username__contains="Volunteer").count()
        volunteer_number += 1

        user = User.objects.create_user(
            username="Volunteer%s" % volunteer_number,
            is_active=False,
            is_staff=True,
            is_superuser=False,
            password=password,
        )

        user.save()

        # and add the user to the comply or explain group.
        user.groups.add(Group.objects.get(name="comply_or_explain"))
        user.save()

        # add volunteering information
        volunteer = Volunteer()
        volunteer.organization = "tbd"
        volunteer.added_by = "Automatically added"
        volunteer.notes = "-"
        volunteer.user = user
        volunteer.save()

        self.message_user(request, "Volunteer added!")

        return True

    add_volunteer.short_description = "💖 Add Volunteer (select something first)"
    actions.append(add_volunteer)

    @staticmethod
    def in_groups(obj):
        value = ""
        for group in obj.groups.all():
            value += group.name
        return value

    @staticmethod
    def organization(obj):
        return obj.volunteer.organization


# I don't know if the permissions between two systems have the same numbers... Only one way to find out :)
class GroupAdmin(BaseGroupAdmin, ImportExportModelAdmin):
    resource_class = GroupResource


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)


# Overwrite the ugly Constance forms with something nicer


class CustomConfigForm(ConstanceForm):
    def __init__(self, *args, **kwargs):
        super(CustomConfigForm, self).__init__(*args, **kwargs)
        # ... do stuff to make your settings form nice ...


class ConfigAdmin(ConstanceAdmin):
    change_list_form = CustomConfigForm
    change_list_template = "admin/config/settings.html"


admin.site.unregister([Config])
admin.site.register([Config], ConfigAdmin)
