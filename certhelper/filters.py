import django_filters
from django import forms
from django.contrib.auth.models import User
from django.db import models
from django.forms.widgets import SelectDateWidget
from django.utils import timezone

from certhelper.models import RunInfo, Type


class RunInfoFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(
        'date',
        label='Date',
        lookup_expr='contains',
        widget=forms.SelectDateWidget(
            years=range(2018, timezone.now().year + 1),
            attrs={'class': 'form-control'},
        ),
    )

    date_range = django_filters.DateFromToRangeFilter(
        'date',
        widget=django_filters.widgets.RangeWidget(attrs={
            'placeholder': 'YYYY-MM-DD',
            'class': 'form-control',
            'size': 9,
            'maxlength': 10,
        })
    )

    runs = django_filters.RangeFilter(
        'run_number',
        widget=django_filters.widgets.RangeWidget(attrs={
            'placeholder': 'run number',
            'class': 'form-control',
            'size': 7,
            'maxlength': 10,
        })
    )
    type = django_filters.ModelChoiceFilter(queryset=Type.objects.all(),
                                            widget=forms.Select(attrs={
                                                'class': 'form-control',
                                                'style': 'width: 500px;',
                                            }))

    class Meta:
        model = RunInfo
        fields = ['type', 'date', 'problem_categories']


class InFilter(django_filters.filters.BaseInFilter, django_filters.filters.CharFilter):
    pass


class ShiftLeaderRunInfoFilter(django_filters.FilterSet):
    # userid = django_filters.ModelMultipleChoiceFilter(queryset=User.objects.all())
    userid = django_filters.filters.ModelMultipleChoiceFilter(
        name='userid',
        to_field_name='pk',
        queryset=User.objects.all().order_by("first_name", "last_name", "username"),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '15',
        })
    )

    type = django_filters.ModelChoiceFilter(queryset=Type.objects.all(),
                                            widget=forms.Select(attrs={
                                                'class': 'form-control',
                                                'style': 'width: 600px;',
                                            }))

    run_number__in = InFilter(field_name='run_number', lookup_expr='in')

    date__gte = django_filters.DateFilter(
        'date',
        label='Date greater than',
        lookup_expr='gte',
        widget=forms.SelectDateWidget(
            years=range(2018, timezone.now().year + 1),
            attrs={'class': 'form-control'},
        ),
    )

    date__lte = django_filters.DateFilter(
        'date',
        label='Date lass than',
        lookup_expr='lte',
        widget=forms.SelectDateWidget(
            years=range(2018, timezone.now().year + 1),
            attrs={'class': 'form-control'},
        ),
    )

    class Meta:
        model = RunInfo
        fields = {
            'date': ['gte', 'lte', ],
            'run_number': ['gte', 'lte', ],
            'problem_categories': ['exact'],
            'type__runtype': ['exact'],
            'type__reco': ['exact'],
            'type__bfield': ['exact'],
            'type__beamtype': ['exact'],
            'type__beamenergy': ['exact'],
            'type__dataset': ['exact'],
        }
        filter_overrides = {
            models.DateField: {
                'filter_class': django_filters.DateTimeFilter,
                'extra': lambda f: {
                    'widget': SelectDateWidget
                },
            },
        }


class ComputeLuminosityRunInfoFilter(django_filters.FilterSet):
    class Meta:
        model = RunInfo
        fields = {
            'run_number': ['gte', 'lte', ],
            'date': ['gte', 'lte', ],
        }


class RunsFilter(django_filters.FilterSet):
    run_number__in = InFilter(field_name='run_number', lookup_expr='in')

    class Meta:
        model = RunInfo
        fields = {
            'date': ['gte', 'lte', ],
            'run_number': ['gte', 'lte', ],
            'problem_categories': ['exact'],
            'type__runtype': ['exact'],
            'type__reco': ['exact'],
            'type__bfield': ['exact'],
            'type__beamtype': ['exact'],
            'type__beamenergy': ['exact'],
            'type__dataset': ['exact'],
            'pixel': ['exact'],
            'sistrip': ['exact'],
            'tracking': ['exact'],
            'number_of_ls': ['gte', 'lte'],
        }
