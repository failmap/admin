from failmap_admin.scanners.models import State
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
import pytz
from datetime import datetime
from failmap_admin.organizations.models import Organization


class StateManager(models.Manager):

    @staticmethod
    def set_state(scanner, value):

        try:
            state = State.objects.get(scanner=scanner)
            state.value = value
            state.since = datetime.now(pytz.utc)
            state.save()
        except ObjectDoesNotExist:
            state = State()  # recursive exceptions?
            state.scanner = scanner
            state.value = value
            state.since = datetime.now(pytz.utc)
            state.save()

    @staticmethod
    def get_state(scanner):
        try:
            state = State.objects.get(scanner=scanner)
            return state.value
        except ObjectDoesNotExist:
            return ""

    # todo: there is probably a better way to do this :)
    @staticmethod
    def create_resumed_organizationlist(scanner):
        """
        The list of organizations is complete, all of them are in here. Only the starting point
        of the list changes based on the state.
        :return: list with all organizations. From current state. Ex: state = F. List = F-Z, A-E
        """
        state = StateManager.get_state(scanner)
        print("Resuming from %s" % state)
        next = []
        previous = []
        o = Organization.objects.all()
        for organization in o:
            if state <= organization.name:
                next.append(organization)
            else:
                previous.append(organization)
        resume = next + previous
        print(resume)
        return resume
