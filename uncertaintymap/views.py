import logging
import mimetypes
import os
from datetime import datetime
from traceback import format_exception_only

from django.core.files.storage import default_storage
from django.http import (
    HttpResponse,
    HttpResponseRedirect,
    StreamingHttpResponse,
)
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from uncertaintymap.bitmap import Orbmap
from uncertaintymap.forms import UncertaintyForm
from uncertaintymap.source import MpcUncertaintyMap
from uncertaintymap.utils import julian_timestamp


logger = logging.getLogger(__name__)


class UncertaintyFormView(FormView):
    form_class = UncertaintyForm
    template_name = 'uncertaintymap/form.html'
    success_url = 'generate'
    generated_file_path = None

    def form_valid(self, form):
        """Form submitted successfully, all fields valid."""
        # we'll need julian date, and also datetime cannot be serialised:
        cleaned_data = form.cleaned_data.copy()
        cleaned_data['julian_date'] = julian_timestamp(
            form.cleaned_data['image_date'])
        cleaned_data['image_date'] = cleaned_data['image_date'].isoformat()
        # save form data so that other pages can access it:
        self.request.session['cleaned_data'] = cleaned_data
        # save useful form field for next time:
        self.set_initial(cleaned_data)
        # return a HTTP 302 redirect:
        return super().form_valid(form)

    def set_initial(self, cleaned_data):
        """Save common fields for future requests."""
        keys = [
            'observatory_code',
            'image_width',
            'image_height',
            'flip_horizontally',
            'flip_vertically',
            'field_width',
            'field_height',
            'bg_color',
        ]
        self.request.session['initial'] = {
            key: cleaned_data[key] for key in keys
        }

    def get_initial(self):
        """Get saved common fields from earlier requests."""
        initial = super().get_initial() or {}
        initial.update(self.request.session.get('initial', {}))
        initial['image_date'] = datetime.now().isoformat().split('.')[0]
        return initial


class UncertaintyGenerateView(TemplateView):
    template_name = 'uncertaintymap/generate.html'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cleaned_data = None
        self.source = None
        self.abort = False

    def get(self, request, *args, **kwargs):
        self.cleaned_data = self.request.session.get('cleaned_data')
        if not self.cleaned_data:
            return HttpResponseRedirect(reverse('form'))
        del self.request.session['cleaned_data']
        context = self.get_context_data(**kwargs)
        return StreamingHttpResponse(
            streaming_content=self.render_to_response(context))

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        for line in response.rendered_content.split('\n'):
            if '{requests_status}' in line:
                line = line.format(requests_status=self.query_mpc())
            if '{pil_status}' in line:
                if self.abort:
                    line = line.format(pil_status='skipped')
                else:
                    line = line.format(pil_status=self.render_image())
            if '{result}' in line:
                if self.abort:
                    result = ''
                else:
                    result = render_to_string(
                        'uncertaintymap/include/result.html',
                        {
                            'generated_file_url': self.generated_file_url,
                            'generated_file_name': self.generated_file_name,
                            'generated_file_path': self.generated_file_path,
                        },
                    )
                line = line.format(result=result)
            yield line

    def query_mpc(self):
        try:
            self.source = MpcUncertaintyMap(
                object_id=self.cleaned_data['object_name'],
                julian_date=self.cleaned_data['julian_date'],
                observatory_code=self.cleaned_data['observatory_code'],
            )
            self.source.load()
        except Exception as e:
            logger.exception('Error during query_mpc')
            self.abort = True
            return '<br />'.join(format_exception_only(type(e), e))
        else:
            return 'ok'

    def render_image(self):
        try:
            center_ra = self.cleaned_data['center_ra']
            center_de = self.cleaned_data['center_de']
            if None in (center_ra, center_de):
                ra_off, de_off = 0, 0
            else:
                ra_off = center_ra - self.source.center_ra_sec
                de_off = center_de - self.source.center_de_sec
            orb = Orbmap(
                width=self.cleaned_data['image_width'],
                height=self.cleaned_data['image_height'],
                flip_ra=self.cleaned_data['flip_horizontally'],
                flip_de=self.cleaned_data['flip_vertically'],
                angle_seconds_ra=self.cleaned_data['field_width'],
                angle_seconds_de=self.cleaned_data['field_height'],
                ra_off_s=ra_off,
                de_off_s=de_off,
                points=self.source.offsets,
                bg_color=(self.cleaned_data['bg_color'],) * 3,
            )
            orb.draw()
            orb.save(self.generated_file_path)
        except Exception as e:
            logger.exception('Error during render_image')
            self.abort = True
            return '<br />'.join(format_exception_only(type(e), e))
        else:
            return 'ok'

    @property
    def generated_file_name(self):
        return '{object_name}-{iso_datetime}.png'.format(
            object_name=self.cleaned_data['object_name'],
            iso_datetime=self.cleaned_data['image_date'].split('.')[0],
        )

    @property
    def generated_file_path(self):
        return os.path.join(default_storage.location, self.generated_file_name)

    @property
    def generated_file_url(self):
        return default_storage.url(self.generated_file_name)


class UncertaintyDownloadView(View):
    def get(self, request, path):
        full_path = default_storage.path(path)
        file_name = os.path.basename(full_path)
        with open(full_path, 'rb') as fh:
            response = HttpResponse(fh.read())
            content_type = mimetypes.guess_type(
                file_name)[0]  # Use mimetypes to get file type
            response['content_type'] = content_type
            response['Content-Disposition'] = "attachment; filename={}".format(
                file_name)
            return response
