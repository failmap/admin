from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from jsonfield import JSONField

from failmap.organizations.models import Organization, OrganizationType, Url


class OrganizationRating(models.Model):
    """
    This is basically an aggregation of UrlRating

    Contains aggregated ratings over time. Why?

    - Reduces complexity to get ratings
        You don't need to know about dead(urls, endpoints), scanner-results.
        For convenience purposes a calculation field also contains some hints why the rating is
        the way it is.

    -   It increases speed
        Instead of continuously calculating the score, it is done on a more regular interval: for
        example once every 10 minutes and only for the last 10 minutes.

    A time dimension is kept, since it's important to see what the rating was over time. This is
    now very simple to get (you don't need a complex join which is hard in django).

    The client software does a drill down on domains and shows why things are the way they are.
    Also this should not know too much about different scanners. In OO fashion, it should ask a
    scanner to explain why something is the way it is (over time).
    """
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    rating = models.IntegerField(
        help_text="Amount of points scored by the organization based on a sum of all URL ratings at"
                  " this moment. Rating -1 is used as a default first rating, which are displayed "
                  "in gray on the map. All next ratings are between 0 (perfect) and 2147483647."
    )
    high = models.IntegerField(help_text="The number of high risk vulnerabilities and failures.", default=0)
    medium = models.IntegerField(help_text="The number of medium risk vulnerabilities and failures.", default=0)
    low = models.IntegerField(help_text="The number of low risk vulnerabilities and failures.", default=0)

    when = models.DateTimeField(db_index=True)
    calculation = JSONField(
        help_text="Contains JSON with a calculation of all scanners at this moment, for all urls "
                  "of this organization. This can be a lot."
    )  # calculations of the independent urls... and perhaps others?

    class Meta:
        managed = True
        get_latest_by = "when"
        index_together = [
            ["when", "id"],
        ]

    def __str__(self):
        return '🔴%s 🔶%s 🍋%s | %s' % (self.high, self.medium, self.low, self.when.date(),)


class UrlRating(models.Model):
    """
        Aggregrates the results of many scanners to determine a rating for a URL.
    """
    url = models.ForeignKey(Url, on_delete=models.CASCADE)
    rating = models.IntegerField(
        help_text="Amount of points scored after rating the URL. Ratings are usually positive, yet "
                  "this is not a positive integerfield because we might use -1 as an 'unknown' "
                  "default value for when there are no ratings at all. Ratings can go from 0 "
                  "up to 2147483647."
    )

    high = models.IntegerField(help_text="The number of high risk vulnerabilities and failures.", default=0)
    medium = models.IntegerField(help_text="The number of medium risk vulnerabilities and failures.", default=0)
    low = models.IntegerField(help_text="The number of low risk vulnerabilities and failures.", default=0)

    when = models.DateTimeField(db_index=True)
    calculation = JSONField(
        help_text="Contains JSON with a calculation of all scanners at this moment. The rating can "
                  "be spread out over multiple endpoints, which might look a bit confusing. Yet it "
                  "is perfectly possible as some urls change their IP every five minutes and "
                  "scans are spread out over days."
    )

    class Meta:
        managed = True

    def __str__(self):
        return '%s,%s,%s  - %s' % (self.high, self.medium, self.low, self.when.date(),)


class AdministrativeRegion(models.Model):
    """
    Helps with downloading / importing openstreetmap regions. Makes it possible for end users to add regions without
    altering code and then import / update those regions.

    Caveats:
    - The more detail you need, the more data is downloaded and processed. This can go into extremes when working with
    cities. Our advice is to only download larger regions or have a massive setup to convert the data.
    - Importing regions can be excruciatingly slow, even up to hours and days, depending on the size.
    - Importing regions will possibly block the worker that is importing the region for said time.
    """

    country = CountryField(db_index=True)

    organization_type = models.ForeignKey(OrganizationType, on_delete=models.CASCADE,
                                          help_text="The organization type desired to import. Not all organization "
                                                    "types might be present in this list by default. Create new ones"
                                                    "accordingly.")

    admin_level = models.IntegerField(
        help_text=mark_safe(
            "The administrative level as documented on the OSM Wiki. Note that each country uses a different way "
            "to organize the same thing. Some use municipalities on level 8, other on level 4 etc. Really do "
            "check the wiki before adding any missing organization. "
            "<a href='https://wiki.openstreetmap.org/wiki/Tag:boundary=administrative' target='_blank'>"
            "Visit the OSM wiki</a>."),
        default=8,
        validators=[MinValueValidator(1), MaxValueValidator(11)]
    )

    imported = models.BooleanField(
        help_text="When imported, this is checked. Helps with importing a larger number of regions manually.",
        default=False
    )

    class Meta:
        verbose_name = _('administrative_region')
        verbose_name_plural = _('administrative_regions')
