# -*- coding: utf-8 -*-
from django.views.generic import TemplateView, DetailView
from django.views.generic.base import TemplateResponseMixin, ContextMixin, View
from django.views.generic.edit import ModelFormMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse_lazy
from django.core.files import File as DjangoFile
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.conf import settings
from django.utils.six import BytesIO
from django.db import transaction
from braces import views
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import Course, CourseProfessor
from core.permissions import IsAdmin
from activities.models import Activity
from course_material.models import File as TimtecFile
from .serializer import CourseExportSerializer, CourseImportSerializer
from braces.views import LoginRequiredMixin

import tarfile
import urllib
import StringIO
import os


User = get_user_model()


class AdminMixin(LoginRequiredMixin, TemplateResponseMixin, ContextMixin,):
    def get_context_data(self, **kwargs):
        context = super(AdminMixin, self).get_context_data(**kwargs)
        context['in_admin'] = True
        return context

    def get_template_names(self):
        """
        Returns two template options, either the administration specific
        or the common template
        """
        return ['administration/' + self.template_name, self.template_name]


class AdminView(AdminMixin, TemplateView, views.AccessMixin):
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):

        response = super(AdminView, self).dispatch(
            request, *args, **kwargs)

        if not request.user.is_authenticated():
            if self.raise_exception:  # *and* if an exception was desired
                raise PermissionDenied  # return a forbidden response.

        if not (request.user.is_superuser or CourseProfessor.objects.filter(user=request.user, role='coordinator')):
            if self.raise_exception:  # *and* if an exception was desired
                raise PermissionDenied  # return a forbidden response.

        return response


class UserAdminView(AdminView):
    def get_context_data(self, **kwargs):
        context = super(UserAdminView, self).get_context_data(**kwargs)
        context['total_users_number'] = User.objects.count()
        return context


class CourseAdminView(AdminMixin, DetailView, views.AccessMixin):
    model = Course
    context_object_name = 'course'
    pk_url_kwarg = 'course_id'
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):

        response = super(CourseAdminView, self).dispatch(
            request, *args, **kwargs)

        if not (request.user.is_superuser or self.object.get_professor_role(request.user) == 'coordinator'):
            if self.raise_exception:  # *and* if an exception was desired
                raise PermissionDenied  # return a forbidden response.

        return response


class CourseCreateView(views.SuperuserRequiredMixin, View, ModelFormMixin):
    model = Course
    fields = ('name',)
    raise_exception = True

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        base_slug = slugify(form.instance.name)
        slug = base_slug
        i = 1
        while Course.objects.filter(slug=slug).exists():
            slug = base_slug + str(i)
            i += 1
        form.instance.slug = slug
        return super(CourseCreateView, self).form_valid(form)

    def form_invalid(self, form):
        return HttpResponseRedirect(reverse_lazy('administration.courses'))

    def get_success_url(self):
        return reverse_lazy('administration.edit_course', kwargs={'course_id': self.object.id})


class ExportCourseView(views.SuperuserRequiredMixin, View):

    @staticmethod
    def add_files_to_export(tar_file, short_file_path):
        full_file_path = settings.MEDIA_ROOT + '/' + short_file_path
        if os.path.isfile(full_file_path):
                tar_file.add(full_file_path,
                             arcname=short_file_path)

    def get(self, request, *args, **kwargs):

        course_id = kwargs.get('course_id')
        course = Course.objects.get(id=course_id)

        course_serializer = CourseExportSerializer(course)

        json_file = StringIO.StringIO(JSONRenderer().render(course_serializer.data))

        tar_info = tarfile.TarInfo('course.json')
        tar_info.size = json_file.len

        filename = course.slug + '.tar.gz'

        response = HttpResponse(content_type='application/x-compressed-tar')
        response['Content-Disposition'] = 'attachment; filename={}'.format(filename)

        course_tar_file = tarfile.open(fileobj=response, mode='w:gz')
        course_tar_file.addfile(tar_info, json_file)

        course_authors = course_serializer.data.get('course_authors')
        for course_author in course_authors:
            picture_path = course_author.get('picture')
            if picture_path:
                picture_path = picture_path.split('/', 2)[-1]
                self.add_files_to_export(course_tar_file, picture_path)

        # Save the course thumbnail
        course_thumbnail_path = course_serializer.data.get('thumbnail')
        if course_thumbnail_path:
            self.add_files_to_export(course_tar_file, course_thumbnail_path)

        # Save the home thumbnail
        course_home_thumbnail_path = course_serializer.data.get('home_thumbnail')
        if course_home_thumbnail_path:
            self.add_files_to_export(course_tar_file, course_home_thumbnail_path)

        # Save the course material
        course_material = course_serializer.data.get('course_material')
        if course_material:
            for course_material_file in course_material['files']:
                course_material_file_path = urllib.unquote(course_material_file['file']).decode('utf8')
                self.add_files_to_export(course_tar_file, course_material_file_path)

        # If there are any activities of type 'image', its files must be saved here
        for lesson in course.lessons.all():
            for unit in lesson.units.all():
                for activity in unit.activities.all():
                    if activity.type == 'image':  # check if the current activity is of 'image' type
                            try:
                                activity_image_file_path = urllib.unquote(activity.image.url)
                                self.add_files_to_export(course_tar_file, activity_image_file_path)
                            except ValueError:
                                # There is no image file associated with the activity yet
                                pass

        course_tar_file.close()
        return response


class ImportCourseView(APIView):

    renderer_classes = (JSONRenderer,)
    permission_classes = (IsAdmin,)

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        import_file = tarfile.open(fileobj=request.FILES.get('course-import-file'), mode='r:gz')
        file_names = import_file.getnames()
        json_file_name = [s for s in file_names if '.json' in s][0]

        json_file = import_file.extractfile(json_file_name)

        stream = BytesIO(json_file.read())
        course_data = JSONParser().parse(stream)
        course_slug = course_data.get('slug')
        try:
            course = Course.objects.get(slug=course_slug)
            if course.has_started:
                return Response({'error': 'course_started'})
            elif not request.DATA.get('force'):
                return Response({'error': 'course_exists'})

        except Course.DoesNotExist:
            course = None

        course_thumbnail_path = course_data.pop('thumbnail')
        if course_thumbnail_path:
            course_thumbnail_path = course_thumbnail_path.replace("/media/", "", 1)

        course_home_thumbnail_path = course_data.pop('home_thumbnail')
        if course_home_thumbnail_path:
            course_home_thumbnail_path = course_home_thumbnail_path.replace("/media/", "", 1)

        # Save course professor images
        course_author_pictures = {}
        for course_author in course_data.get('course_authors'):
            author_name = course_author.get('name')
            picture_path = course_author.pop('picture')
            if picture_path and author_name:
                picture_path = picture_path.split('/', 2)[-1]
                course_author_pictures[author_name] = picture_path

        # save course material images
        course_material = course_data.get('course_material')
        course_material_files = []
        if course_material:
            course_material_files = course_data['course_material'].pop('files')
            # course_material_files = course_material.pop('files')

        # If there are any activities of 'image' type, its files must be given to django now
        for lesson in course_data['lessons']:
            for unit in lesson['units']:
                for activity in unit['activities']:
                    if activity['type'] == 'image':
                        try:
                            image_path = activity.pop('image').replace("/media/", "", 1)
                            new_activity = Activity.objects.create(
                                type='image',
                                image=DjangoFile(import_file.extractfile(image_path))
                            )
                            activity['id'] = new_activity.id
                        except AttributeError:
                            # This activity image has no file
                            pass

        if course:
            course_serializer = CourseImportSerializer(course, data=course_data)
        else:
            course_serializer = CourseImportSerializer(data=course_data)

        if course_serializer.is_valid():

            course_obj = course_serializer.save()

            # save thumbnail and home thumbnail
            if course_thumbnail_path and course_thumbnail_path in file_names:
                course_thumbnail_file = import_file.extractfile(course_thumbnail_path)
                course_obj.thumbnail = DjangoFile(course_thumbnail_file)
            if course_home_thumbnail_path and course_home_thumbnail_path in file_names:
                course_home_thumbnail_file = import_file.extractfile(course_home_thumbnail_path)
                course_obj.home_thumbnail = DjangoFile(course_home_thumbnail_file)

            # save course material files
            course_material_files_list = []
            for course_material_file in course_material_files:
                course_material_file_path = course_material_file.get('file').replace("/media/", "", 1)  # remove unnecessary "media" path, if any
                try:
                    course_material_file_obj = import_file.extractfile(course_material_file_path)
                    course_material_files_list.append(TimtecFile(file=DjangoFile(course_material_file_obj)))
                except KeyError:
                    pass
            course_obj.course_material.files = course_material_files_list
            course_obj.course_material.text = course_material['text']
            course_obj.course_material.save()

            # If the course has authors, save save their pictures, if any
            for course_author in course_obj.course_authors.all():
                picture_path = course_author_pictures.get(course_author.name).replace("/media/", "", 1)
                if picture_path and picture_path in file_names:
                    picture_file_obj = import_file.extractfile(picture_path)
                    course_author.picture = DjangoFile(picture_file_obj)
                    course_author.save()

            # Save all changes in the new imported course
            course_obj.save()

            return Response({'new_course_url': reverse_lazy('administration.edit_course',
                                                            kwargs={'course_id': course_obj.id}),
                             })
        else:
            return Response({'error': 'invalid_file'})
