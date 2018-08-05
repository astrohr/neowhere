from django.urls import path

from uncertaintymap.views import (
    UncertaintyDownloadView,
    UncertaintyFormView,
    UncertaintyGenerateView,
)

urlpatterns = [
    path('', UncertaintyFormView.as_view(), name="form"),
    path('generate/', UncertaintyGenerateView.as_view(), name="generate"),
    path('download/<path>', UncertaintyDownloadView.as_view(), name="download"),
]
