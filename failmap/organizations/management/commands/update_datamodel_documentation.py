import logging
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand

log = logging.getLogger(__package__)


class Command(BaseCommand):
    help = 'Adds some documentation artifacts to this project.'

    def handle(self, *args, **options):

        apps = ['organizations', 'scanners', 'map', 'game', 'app', 'hypersh']

        for app in apps:
            log.info("creating image for: %s", app)
            call_command('graph_models', app, '-o',
                         'docs/source/topics/development/data_model/%s_models.png' % app)

        # not using -a, because it's hard to see where some of the models originate from (and then to remove them
        # using -X). So making it more explicit.
        log.info("creating image for all models in one.")
        call_command('graph_models', 'organizations', 'scanners', 'map', 'game', 'app', 'hypersh', '-o',
                     'docs/source/topics/development/data_model/failmap_models.png')

        # Creating a file that contains all above models...
        contents = "# Data Model" + os.linesep
        contents += "This is an autogenerated page about the FailMap data model." + os.linesep
        contents += "It has been generated with 'failmap docs'." + os.linesep + os.linesep

        for app in apps:
            contents += "## %s" % app + os.linesep
            contents += "![Data Model](data_model/%s_models.png)" % app + os.linesep
            contents += "" + os.linesep

        contents += "## All in one" + os.linesep
        contents += "![Data Model](data_model/failmap_models.png)" + os.linesep
        contents += "" + os.linesep

        with open("docs/source/topics/development/data_model.md", "w") as text_file:
            text_file.write(contents)