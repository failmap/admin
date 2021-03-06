class FourDigitYearConverter:
    regex = "[0-9]{4}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%04d" % value


class OrganizationTypeConverter:
    regex = r"[a-z_\-]{0,50}"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return "%s" % value


class OrganizationIdConverter:
    regex = "[0-9]{1,6}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%d" % value


class OrganizationConverter:
    regex = r"[a-z_\-]{0,50}"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return "%s" % value


class JsonConverter:
    # Supports {"key": "value", "key2": "value2"} syntax.
    regex = r'[a-zA-Z0-9:_\-=}{, "\']{0,1024}'

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return "%s" % value


class WeeksConverter:
    regex = "[0-9]{0,2}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%d" % value


class DaysConverter:
    regex = "[0-9]{0,3}"

    def to_python(self, value):
        return int(value)

    def to_url(self, value):
        return "%d" % value


class CountryConverter:
    regex = "[A-Z]{2}"

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return "%s" % value
