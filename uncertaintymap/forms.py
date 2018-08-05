import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import TextInput


class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'


class AstroAngleField(forms.IntegerField):
    default_error_messages = {
        'invalid': "Enter a valid angle value.",
    }
    format = '{}°{}\'{}"'
    widget = TextInput
    pattern = re.compile(
        r'^([+\-]?\d{1,3})'  # hours, with possible sign
        r'[h:]?\s?'  # "h" or ":" or " " or nothing
        r'(\d{1,2})'  # minutes
        r'[m:]?\s?'  # "m" or ":" or " " or nothing
        r'(\d{1,2})'  # seconds
        r'[.s:]?'  # "s" or ":" or " " or "." or nothing (ignore decimals)
    )

    def validate_format(self, value):
        if not self.pattern.match(str(value)):
            raise ValidationError(
                self.error_messages['invalid'], code='invalid')

    def to_python(self, value):
        if value in self.empty_values:
            return None
        self.validate_format(value)
        values = self.pattern.findall(str(value))[0]
        values = tuple(map(int, values))
        value = values[0] * 3600 + values[1] * 60 + values[2]
        return value

    def prepare_value(self, value):
        if value in self.empty_values:
            return None
        value = self.to_python(value)
        hours = value // 3600
        value -= hours * 3600
        minutes = value // 60
        value -= minutes * 60
        seconds = value
        value = self.format.format(hours, minutes, seconds)
        return value


class AstroRaField(AstroAngleField):
    default_error_messages = {
        'invalid': "Enter a valid RA value.",
    }
    format = '{}h {}m {}s'
    pattern = re.compile(
        r'^([+\-]?\d{1,2})'  # hours, with possible sign
        r'[h:]?\s?'  # "h" or ":" or " " or nothing
        r'(\d{1,2})'  # minutes
        r'[m:]?\s?'  # "m" or ":" or " " or nothing
        r'(\d{1,2})'  # seconds
        r'[.s:]?'  # "s" or ":" or " " or "." or nothing (ignore decimals)
    )


class AstroDeField(AstroAngleField):
    default_error_messages = {
        'invalid': "Enter a valid DE value.",
    }
    pattern = re.compile(
        r'^([+\-]?\d{1,2})'  # degrees 2 digits (max 90), with possible sign
        r'[h:]?\s?'  # "h" or ":" or " " or nothing
        r'(\d{1,2})'  # minutes
        r'[m:]?\s?'  # "m" or ":" or " " or nothing
        r'(\d{1,2})'  # seconds
        r'[.s:]?'  # "s" or ":" or " " or "." or nothing (ignore decimals)
    )


class UncertaintyForm(forms.Form):
    image_width = forms.IntegerField(min_value=1)
    image_height = forms.IntegerField(min_value=1)
    field_width = forms.IntegerField(min_value=1)
    field_height = forms.IntegerField(min_value=1)
    flip_horizontally = forms.BooleanField(required=False)
    flip_vertically = forms.BooleanField(required=False)
    image_date = forms.DateTimeField(
        widget=DateTimeInput(attrs={'step': 1}),
        input_formats=['%Y-%m-%dT%H:%M:%S'],
    )
    center_ra = AstroRaField(required=False)
    center_de = AstroDeField(required=False)
    object_name = forms.CharField(max_length=15)
    observatory_code = forms.CharField(max_length=3)
    bg_color = forms.IntegerField(min_value=0, max_value=255)
