import logging
from datetime import datetime

import pytz
from dal import autocomplete
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.db.utils import OperationalError
from django.shortcuts import redirect, render
from django.views.decorators.cache import cache_page

from failmap.game.forms import ContestForm, OrganisationSubmissionForm, TeamForm, UrlSubmissionForm
from failmap.game.models import Contest, OrganizationSubmission, Team, UrlSubmission
from failmap.map.calculate import get_calculation
from failmap.organizations.models import Organization, OrganizationType, Url
from failmap.scanners.models import EndpointGenericScan, TlsQualysScan, TlsScan, UrlGenericScan

log = logging.getLogger(__package__)

one_minute = 60
one_hour = 60 * 60
one_day = 24 * 60 * 60
ten_minutes = 60 * 10


# workaround to start a contest view, has to be rewritten to use the configured default and fallback etc
def get_default_contest(request):
    try:
        if request.session.get('contest', 0):
            # log.debug("Returning a contest from session.")
            return Contest.objects.get(id=request.session['contest'])
        else:
            # get the first contest that is currently active, if nothing is active, get the first contest.
            try:
                # log.debug("Trying to find the earliest active contest")
                return Contest.objects.all().filter(
                    until_moment__gte=datetime.now(pytz.utc),
                    from_moment__lte=datetime.now(pytz.utc)).first()
            except ObjectDoesNotExist:
                # log.debug("Get the first contest ever")
                return Contest.objects.first()

    except (OperationalError, Contest.DoesNotExist):
        # log.debug("Fallback contest value")
        return 0


# todo: what about urls that are being added through another contest?
@login_required(login_url='/authentication/login/')
def submit_url(request):

    # validate you're in a session
    if not request.session.get('team'):
        return redirect('/game/team/')

    if request.POST:
        form = UrlSubmissionForm(request.POST)

        if form.is_valid():
            # manually saving the form, this is not your normal 1 to 1 save.
            form.save(team=request.session.get('team'))

            # don't add the URL, so you can quickly add urls to the same organization.
            # this will cause some noise, but also more entries.
            data = {
                'organization_type_name': form.cleaned_data.get('organization_type_name'),
                'country': form.cleaned_data.get('country'),
                'for_organization': form.cleaned_data.get('for_organization')
            }
            added_url = form.cleaned_data.get('url')
            form = UrlSubmissionForm(data)

            return render(request, 'game/submit_url.html', {'form': form, 'success': True,
                                                            'url': added_url})

    else:
        form = UrlSubmissionForm()

    return render(request, 'game/submit_url.html', {'form': form,
                                                    'error': form.errors})


@login_required(login_url='/authentication/login/')
def submit_organisation(request):

    # validate you're in a session
    if not request.session.get('team'):
        return redirect('/game/team/')

    if request.POST:
        form = OrganisationSubmissionForm(request.POST)

        if form.is_valid():
            # manually saving the form, this is not your normal 1 to 1 save.
            form.save(team=request.session.get('team'))

            form = OrganisationSubmissionForm()

            return render(request, 'game/submit_organisation.html', {'form': form, 'success': True})

    else:
        form = OrganisationSubmissionForm()

    return render(request, 'game/submit_organisation.html', {'form': form})


def scores(request):

    # todo: this param handling code is absolutely disgusting, it should be more beautiful.
    submitted_contest = request.GET.get('contest', "")
    if submitted_contest is not None and submitted_contest.isnumeric():
        submitted_contest = int(submitted_contest)
    else:
        submitted_contest = 0

    if submitted_contest > -1:
        try:
            contest = Contest.objects.get(id=submitted_contest)
        except ObjectDoesNotExist:
            contest = get_default_contest(request)
    else:
        contest = get_default_contest(request)

    teams = Team.objects.all().filter(participating_in_contest=contest)

    scores = []
    for team in teams:
        """
        Out of simplicity _ALL_ scores are retrieved instead of the last one per URL. Last one-per is not supported
        in Django and therefore requires a lot of code. The deviation is negligible during a contest as not so much
        will change in a day or two. On the long run it might increase the score a bit when incorrect fixes are applied
        or a new error is found. If the discovered issue is fixed it doesn't deliver additional points.
        """
        scans = list(TlsQualysScan.objects.all().filter(
            endpoint__url__urlsubmission__added_by_team=team.id,
            endpoint__url__urlsubmission__has_been_accepted=True
        ))

        scans += list(TlsScan.objects.all().filter(
            endpoint__url__urlsubmission__added_by_team=team.id,
            endpoint__url__urlsubmission__has_been_accepted=True
        ))

        scans += list(EndpointGenericScan.objects.all().filter(
            endpoint__url__urlsubmission__added_by_team=team.id,
            endpoint__url__urlsubmission__has_been_accepted=True
        ))

        scans += list(UrlGenericScan.objects.all().filter(
            url__urlsubmission__added_by_team=team.id,
            url__urlsubmission__has_been_accepted=True
        ))

        added_organizations = OrganizationSubmission.objects.all().filter(
            added_by_team=team.id,
            has_been_accepted=True,
            has_been_rejected=False

        ).count()

        rejected_urls = UrlSubmission.objects.all().filter(
            added_by_team=team.id,
            has_been_accepted=False,
            has_been_rejected=True,
        ).count()

        final_calculation = {
            'high': 0,
            'medium': 0,
            'low': 0,
        }

        for scan in scans:
            temp_calculation = get_calculation(scan)

            final_calculation['high'] += temp_calculation['high']
            final_calculation['medium'] += temp_calculation['medium']
            final_calculation['low'] += temp_calculation['low']

        score_multiplier = {
            'low': 100,
            'medium': 250,
            'high': 1000,
            'rejected': 1337,
            'organization': 500,
        }

        score = {
            'team': team.name,
            'team_color': team.color,
            'high': final_calculation['high'],
            'high_multiplier': score_multiplier['high'],
            'high_score': final_calculation['high'] * score_multiplier['high'],
            'medium': final_calculation['medium'],
            'medium_multiplier': score_multiplier['medium'],
            'medium_score': final_calculation['medium'] * score_multiplier['medium'],
            'low': final_calculation['low'],
            'low_multiplier': score_multiplier['low'],
            'low_score': final_calculation['low'] * score_multiplier['low'],
            'added_organizations': added_organizations,
            'added_organizations_multiplier': score_multiplier['organization'],
            'added_organizations_score': added_organizations * score_multiplier['organization'],
            'rejected': rejected_urls,
            'rejected_multiplier': score_multiplier['rejected'],
            'rejected_score': rejected_urls * score_multiplier['rejected'],
            'total_score': final_calculation['high'] * score_multiplier['high'] +
            final_calculation['medium'] * score_multiplier['medium'] +
            final_calculation['low'] * score_multiplier['low'] +
            added_organizations * score_multiplier['organization'] - rejected_urls * score_multiplier['rejected']
        }

        scores.append(score)

    # order the scores from high to low.
    scores = sorted(scores, key=lambda k: (k['high'], k['medium'], k['low']), reverse=True)

    return render(request, 'game/scores.html', {'team': get_team_info(request),
                                                'scores': scores,
                                                'contest': contest})


def contests(request):

    if request.POST:
        form = ContestForm(request.POST)

        # todo: you cannot join expired contests... only active or future contests. Check this somewhere.
        if form.is_valid():
            if form.cleaned_data['id']:
                request.session['contest'] = form.cleaned_data['id']
                request.session['team'] = None  # resetting the team when switching
                return redirect('/game/team/')
            else:
                request.session['contest'] = None
    else:
        form = ContestForm()

    expired_contests = Contest.objects.all().filter(until_moment__lt=datetime.now(pytz.utc))

    active_contests = Contest.objects.all().filter(from_moment__lt=datetime.now(pytz.utc),
                                                   until_moment__gte=datetime.now(pytz.utc))

    future_contests = Contest.objects.all().filter(from_moment__gte=datetime.now(pytz.utc))

    # don't select a contest if you don't have one in your session.
    contest = None
    try:
        if request.session.get("contest", 0):
            contest = get_default_contest(request)
    except Contest.DoesNotExist:
        contest = None

    return render(request, 'game/contests.html', {
        'contest': contest,
        'expired_contests': expired_contests,
        'active_contests': active_contests,
        'future_contests': future_contests,
        'error': form.errors
    })


def submitted_organizations(request):
    submitted_organizations = OrganizationSubmission.objects.all().filter(
        added_by_team__participating_in_contest=get_default_contest(request)).order_by('organization_name')

    already_known_organizations = Organization.objects.all().filter().exclude(
        id__in=submitted_organizations.values('organization_in_system'))

    return render(request, 'game/submitted_organizations.html', {
        'submitted_organizations': submitted_organizations,
        'already_known_organizations': already_known_organizations,
        'contest': get_default_contest(request)})


# todo: contest required!
def submitted_urls(request):
    submitted_urls = UrlSubmission.objects.all().filter(
        added_by_team__participating_in_contest=get_default_contest(request)).order_by('for_organization', 'url')

    # todo: query doesn't work yet
    # Another competition might be adding urls too.
    # todo: show all other urls for this competition filter.
    # this is an expensive query, which will break with a lot of data... todo: determine when /if it breaks.
    already_known_urls = Url.objects.all().filter().exclude(id__in=submitted_urls.values('url_in_system'))

    return render(request, 'game/submitted_urls.html',
                  {'submitted_urls': submitted_urls,
                   'already_known_urls': already_known_urls,
                   'contest': get_default_contest(request)})


@cache_page(ten_minutes)
def rules_help(request):
    return render(request, 'game/rules_help.html')


@login_required(login_url='/authentication/login/')
def teams(request):

    # if you don't have a contest selected, you're required to do so...
    # contest 0 can exist. ?
    if request.session.get('contest', -1) < 0:
        return redirect('/game/contests/')

    if request.POST:
        form = TeamForm(request.POST, contest=get_default_contest(request))

        if form.is_valid():
            if form.cleaned_data['team']:
                request.session['team'] = form.cleaned_data['team'].id
            else:
                request.session['team'] = None

            request.session.modified = True
            request.session.save()
            form = TeamForm(initial={'team': get_team_id(request)}, contest=get_default_contest(request))

    else:
        form = TeamForm(initial={'team': get_team_id(request)}, contest=get_default_contest(request))

    return render(request, 'game/team.html', {'form': form, 'team': get_team_info(request)})


def get_team_id(request):
    try:
        team = Team.objects.get(pk=request.session.get('team', 0))
    except (ObjectDoesNotExist, ValueError):
        team = {"id": "-"}
    return team


def get_team_info(request):
    try:
        team = Team.objects.get(pk=request.session.get('team', 0))
    except (ObjectDoesNotExist, ValueError):
        team = {"name": "-"}
    return team


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Todo: Don't forget to filter out results depending on the visitor !
        # if not self.request.user.is_authenticated():
        #     return Organization.objects.none()

        qs = Organization.objects.all()

        organization_type = self.forwarded.get('organization_type_name', None)
        country = self.forwarded.get('country', None)

        if organization_type:
            qs = qs.filter(type=organization_type)

        if country:
            qs = qs.filter(country=country)

        """
        Do not search on a single character, it will give too many results. Two characters is a minimum.
        """
        if not self.q or len(self.q) < 3:
            return qs

        """
        You can also search for organization type, which helps if you know the object is of a certain type.
        It even supports multiple words, if you have a space, each word will be searched for. Up to three words...
        """
        if len(self.q.split(" ")) < 4:
            for query in self.q.split(" "):
                qs = qs.filter(Q(name__icontains=query) | Q(type__name__icontains=query))
        else:
            qs = qs.filter(name__icontains=self.q)

        return qs


class OrganizationTypeAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):

        qs = OrganizationType.objects.all().filter()

        # country = self.forwarded.get('country', None)
        #
        # todo: this gives a carthesian product, of course. Distinct on fields not supported by sqlite...
        # so that doesn't work during development.
        # if country:
        #     qs = qs.filter(organization__country=country)

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
