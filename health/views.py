import random
import hashlib
import string
import datetime

from django.db.models.aggregates import Count
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404, HttpResponseServerError
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View, TemplateView
from django.views.generic.edit import ContextMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import *

TIME_FORMAT = '%Y-%m-%dT%H:%M'


def generate_register_code(user):
    time = timezone.now()
    id = user.id
    seed = str(time) + str(id) + str(random.randint(-10000, 10000))

    hash_obj = hashlib.md5(seed.encode())

    return hash_obj.hexdigest()


def generate_doctor(username):
    doctor = User.objects.create()
    doctor.username = username
    password = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(8))
    doctor.identity = '1'
    doctor.health_status = 101
    doctor.health_risk = '1'
    doctor.set_password(password)

    return doctor, password


def random_doctor(doctor):
    if doctor is None:
        doctors = User.objects.filter(identity='1')
    else:
        doctors = User.objects.filter(Q(identity='1') & ~Q(doctor=doctor))

    count = doctors.aggregate(count=Count('id'))['count']
    random_index = random.randint(0, count - 1)
    doctor = doctors.all()[random_index]

    return doctor


# Create your views here.
class BaseMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)

        if self.request.user.is_active:
            log_user = User.objects.get(pk=self.request.user.id)
            context['log_user'] = log_user
            context['identity'] = log_user.identity
            context['health_risk'] = log_user.health_risk
            context['health_status'] = log_user.health_status
        else:
            context['log_user'] = None

        return context


class WelcomeView(BaseMixin, TemplateView):
    template_name = 'health/welcome.html'

    def get_context_data(self, **kwargs):
        context = super(WelcomeView, self).get_context_data(**kwargs)

        # if context['log_user'].is_active:
        #     return HttpResponseRedirect(reverse('health:homepage'))

        return context


# URL name = 'calendar_page'
class CalendarView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(CalendarView, self).get_context_data(**kwargs)
        # user_id = self.kwargs.get('user_id')
        context['self'] = True

        return context

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        page_owner = self.kwargs.get('user_id')
        # # page_owner = User.objects.get(pk=user_id)
        # # context['page_owner'] = page_owner
        # # context['self'] = True
        # context['health_datas'] = HealthData.objects.filter(creator=page_owner)
        context['activities'] = Activity.objects.filter(user_id=page_owner)
        #
        # return render(self.request, 'health/health_data.html', context)
        return render(self.request, 'health/calendar.html', context)


# URL name = 'calendar_operations'
class CalendarOperationView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(CalendarOperationView, self).get_context_data(**kwargs)

        return context

    @method_decorator(login_required)
    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        context = self.get_context_data()

        if slug == 'create_activity':
            return self.create_activity(context)
        elif slug == 'delete_activity':
            return self.delete_activity(context)
        else:
            raise Http404

    def create_activity(self, context):
        context = self.get_context_data()
        now = datetime.datetime.now()
        activity_time = self.request.POST['time']
        activity_time = datetime.datetime.strptime(activity_time, TIME_FORMAT)
        if activity_time < now:
            return HttpResponseRedirect(reverse('health:homepage'))

        activity_form = ActivityForm(self.request.POST)

        if activity_form.is_valid():
            title = activity_form.cleaned_data['title']
            content = activity_form.cleaned_data['content']

            activity = Activity.objects.create(title=title, content=content, user=context['log_user'],
                                               activity_time=activity_time)

            try:
                activity.save()
            except Exception:
                pass

        return HttpResponseRedirect(reverse('health:calendar_page', kwargs={'user_id': context['log_user'].id}))

    def delete_activity(self, context):
        activity_id = self.request.POST['activity_id']
        activity = Activity.objects.get(pk=activity_id)
        context = self.get_context_data()

        try:
            activity.delete()
        except Exception:
            pass

        return HttpResponseRedirect(reverse('health:calendar_page', kwargs={'user_id': context['log_user'].id}))


# URL name = 'task_page'
class TaskView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        # user_id = self.kwargs.get('user_id')
        context['self'] = True

        return context

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        page_owner = self.kwargs.get('user_id')
        # # page_owner = User.objects.get(pk=user_id)
        # # context['page_owner'] = page_owner
        # # context['self'] = True
        # context['health_datas'] = HealthData.objects.filter(creator=page_owner)
        context['tasks'] = Task.objects.filter(user_id=page_owner)
        #
        # return render(self.request, 'health/health_data.html', context)
        return render(self.request, 'health/task.html', context)


# URL name = 'healthdata_page'
class HealthDataView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(HealthDataView, self).get_context_data(**kwargs)
        # user_id = self.kwargs.get('user_id')
        context['self'] = True

        return context

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)

        page_owner = self.kwargs.get('user_id')
        # # page_owner = User.objects.get(pk=user_id)
        # # context['page_owner'] = page_owner
        # # context['self'] = True
        context['health_datas'] = HealthData.objects.filter(creator=page_owner)
        # # context['tasks'] = Task.objects.filter(user=context['page_owner'])
        #
        # return render(self.request, 'health/health_data.html', context)
        return render(self.request, 'health/health_data.html', context)


# URL name = 'health_data_operations'
class HealthDataOperationView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(HealthDataOperationView, self).get_context_data(**kwargs)

        return context

    @method_decorator(login_required)
    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        context = self.get_context_data()

        if slug == 'create_health_data':
            return self.create_health_data(context)
        else:
            raise Http404

    def create_health_data(self, context):
        form = HealthDataForm(self.request.POST)
        if form.is_valid():
            heart_rate = form.cleaned_data['heart_rate']
            weight = form.cleaned_data['weight']
            temperature = form.cleaned_data['temperature']
            creator = context['log_user']

            health_data = HealthData.objects.create(heart_rate=heart_rate, weight=weight, temperature=temperature,
                                                    creator=creator)
            try:
                health_data.save()
            except Exception:
                return HttpResponseServerError()

            return HttpResponseRedirect(reverse('health:healthdata_page', kwargs={'user_id': context['log_user'].id}))


# URL name = 'homepage'
class HomepageView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(HomepageView, self).get_context_data(**kwargs)
        context['self'] = True

        return context

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        identity = context['identity']

        if identity == '0':
            return self.tech_homepage(context)
        elif identity == '1':
            return self.doctor_homepage(context)
        elif identity == '2':
            return self.enduser_homepage(context)
        else:
            raise Http404

    def tech_homepage(self, context):
        context['doctors'] = User.objects.filter(identity='1')
        context['codes'] = RegisterCode.objects.filter(creator=context['log_user'], used=False)

        return render(self.request, 'health/tech_homepage.html', context)

    def doctor_homepage(self, context):
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        context['activities'] = Activity.objects.filter(user=context['log_user'], activity_time__gt=now)
        context['announcements'] = Announcement.objects.filter(publisher=context['log_user'])
        context['patients'] = User.objects.filter(identity='2', doctor=context['log_user'])

        return render(self.request, 'health/doctor_homepage.html', context)

    def enduser_homepage(self, context):
        context['page_owner'] = context['log_user']
        unviewed_announcements = Announcement.objects.filter(announcementreceive__enduser=context['log_user'],
                                                             announcementreceive__viewed=False)
        viewed_announcements = Announcement.objects.filter(announcementreceive__enduser=context['log_user'],
                                                           announcementreceive__viewed=True)
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        context['activities'] = Activity.objects.filter(user=context['log_user'], activity_time__gt=now)
        context['past_activities'] = Activity.objects.filter(user=context['log_user'], activity_time__lt=now)
        context['unviewed_announcements'] = unviewed_announcements
        context['viewed_announcements'] = viewed_announcements
        context['doctor'] = context['log_user'].doctor
        context['health_datas'] = HealthData.objects.filter(creator=context['log_user'])
        context['tasks'] = Task.objects.filter(user=context['log_user'])

        return render(self.request, 'health/enduser_homepage.html', context)


# URL name = 'operations'
class OperationView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(OperationView, self).get_context_data(**kwargs)

        return context

    @method_decorator(login_required)
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        context = self.get_context_data()

        if slug == 'messages':
            context['messages'] = Message.objects.filter(to_user=context['log_user'])
            return render(self.request, 'health/messages.html', context)
        elif slug == 'modify_info':
            return render(self.request, 'health/personal_info.html', context)
        else:
            raise Http404

    @method_decorator(login_required)
    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')
        context = self.get_context_data()

        if slug == 'create_code':
            return self.create_code(context)
        elif slug == 'create_health_data':
            return self.create_health_data(context)
        elif slug == 'create_doctor_account':
            return self.create_doctor_account(context)
        elif slug == 'choose_doctor':
            return self.choose_doctor(context)
        elif slug == 'publish_announcement':
            return self.publish_announcement(context)
        elif slug == 'delete_announcement':
            return self.delete_announcement(context)
        elif slug == 'modify_info':
            return self.modify_info(context)
        elif slug == 'create_activity':
            return self.create_activity()
        elif slug == 'delete_activity':
            return self.delete_activity()
        else:
            raise Http404

    def create_code(self, context):
        if context['identity'] != '0':
            return PermissionDenied

        code_content = generate_register_code(context['log_user'])
        code = RegisterCode.objects.create(code=code_content, creator=context['log_user'])

        try:
            code.save()
        except Exception as e:
            pass

        return HttpResponseRedirect(reverse('health:homepage'))

    def create_doctor_account(self, context):
        if context['identity'] != '0':
            return PermissionDenied

        doctor_name = self.request.POST['doctor_name']
        doctor, password = generate_doctor(doctor_name)

        try:
            doctor.save()
        except Exception:
            return HttpResponseServerError()

        message = Message.objects.create(from_user=context['log_user'], to_user=context['log_user'])
        message.content = 'Doctor username: ' + doctor_name + '  /  ' + 'Password: ' + password

        try:
            message.save()
        except Exception:
            doctor.delete()
            return HttpResponseServerError()

        return HttpResponseRedirect(reverse('health:homepage'))

    def choose_doctor(self, context):
        if context['identity'] != '2':
            return PermissionDenied

        context['doctor'] = context['log_user'].doctor
        doctor = random_doctor(context['doctor'])
        user = context['log_user']
        user.doctor = doctor

        try:
            user.save()
        except Exception:
            return HttpResponseServerError()

        return HttpResponseRedirect(reverse('health:homepage'))

    def publish_announcement(self, context):
        if context['identity'] != '1':
            return PermissionDenied

        content = self.request.POST['content']
        announcement = Announcement.objects.create(publisher=context['log_user'], content=content)
        announcement.save()

        users = User.objects.filter(identity='2', doctor=context['log_user'])

        for user in users:
            announcement_receive = AnnouncementReceive.objects.create(announcement=announcement, enduser=user)

            try:
                announcement_receive.save()
            except Exception:
                pass

        return HttpResponseRedirect(reverse('health:homepage'))

    def delete_announcement(self, context):
        if context['identity'] != '1':
            return PermissionDenied

        announcement_id = self.request.POST['announcement_id']
        announcement = Announcement.objects.get(pk=announcement_id)

        try:
            announcement.delete()
        except Exception:
            pass

        return HttpResponseRedirect(reverse('health:homepage'))

    def modify_info(self, context):
        password = self.request.POST['password']
        password_confirm = self.request.POST['password_confirm']

        if password == password_confirm:
            user = context['log_user']
            user.set_password(password)

            try:
                user.save()
            except Exception:
                pass

            user = authenticate(username=user.username, password=password)

            if user is not None:
                self.request.session.set_expiry(0)
                login(self.request, user)

        return HttpResponseRedirect(reverse('health:homepage'))

    def create_activity(self):
        context = self.get_context_data()
        now = datetime.datetime.now()
        activity_time = self.request.POST['time']
        activity_time = datetime.datetime.strptime(activity_time, TIME_FORMAT)
        if activity_time < now:
            return HttpResponseRedirect(reverse('health:homepage'))

        activity_form = ActivityForm(self.request.POST)

        if activity_form.is_valid():
            title = activity_form.cleaned_data['title']
            content = activity_form.cleaned_data['content']

            activity = Activity.objects.create(title=title, content=content, user=context['log_user'],
                                               activity_time=activity_time)

            try:
                activity.save()
            except Exception:
                pass

        return HttpResponseRedirect(reverse('health:calendar', kwargs={'user_id': context['log_user'].id}))
        # return HttpResponseRedirect(reverse('health:homepage'))

    def delete_activity(self):
        activity_id = self.request.POST['activity_id']
        activity = Activity.objects.get(pk=activity_id)
        context = self.get_context_data()

        try:
            activity.delete()
        except Exception:
            pass

            return render(self.request, 'health/calendar.html.html')
            # return HttpResponseRedirect(reverse('health:homepage'))


# URL name = 'user_control'
class UserControlView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'register':
            return render(self.request, 'health/register.html')

        if slug == 'login':
            return render(self.request, 'health/base.html')

    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'login':
            return self.login()
        elif slug == 'logout':
            return self.logout()
        elif slug == 'register':
            return self.register()

    def login(self):
        form = LoginForm(self.request.POST)

        if form.is_valid():
            name = form.cleaned_data['username']
            pwd = form.cleaned_data['password']
            user = authenticate(username=name, password=pwd)

            if user is not None:
                self.request.session.set_expiry(0)
                login(self.request, user)

        return HttpResponseRedirect(reverse('health:homepage'))

    def logout(self):
        logout(self.request)

        return HttpResponseRedirect(reverse('health:welcome'))

    def register(self):
        form = RegisterForm(self.request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            pwd = form.cleaned_data['password']
            pwd_confirm = form.cleaned_data['password_confirm']
            code = form.cleaned_data['register_code']

            if pwd == pwd_confirm:
                if RegisterCode.objects.filter(code=code).exists():
                    user = User.objects.create(username=username, identity='2', health_status=97,
                                               health_risk='no health risk')
                    user.set_password(pwd)
                    register_code = RegisterCode.objects.get(code=code)
                    register_code.used = True

                    try:
                        user.save()
                        register_code.save()
                        user = authenticate(username=username, password=pwd)
                        login(self.request, user)
                    except Exception:
                        pass

                    return HttpResponseRedirect(reverse('health:homepage'))
                else:
                    return HttpResponseRedirect(reverse('health:user_control', kwargs={'slug': 'register'}))
            else:
                return HttpResponseRedirect(reverse('health:user_control', kwargs={'slug': 'register'}))
        else:
            return HttpResponseRedirect(reverse('health:user_control', kwargs={'slug': 'register'}))


# URL name = 'patient_homepage'
class PatientHomepageView(BaseMixin, TemplateView):
    template_name = 'health/enduser_homepage.html'

    def get_context_data(self, **kwargs):
        context = super(PatientHomepageView, self).get_context_data(**kwargs)

        if context['log_user'] is None:
            raise Http404

        patient_id = self.kwargs.get('user_id')
        page_owner = User.objects.get(pk=patient_id)
        context['page_owner'] = page_owner
        context['self'] = False
        context['health_datas'] = HealthData.objects.filter(creator=page_owner)
        context['tasks'] = Task.objects.filter(user=context['page_owner'])
        context['health_risk'] = page_owner.health_risk
        context['health_status'] = page_owner.health_status
        context['patients'] = User.objects.filter(identity='2', doctor=context['log_user'])

        return context


# URL name = 'doctor_operations'
class DoctorOperationView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(DoctorOperationView, self).get_context_data(**kwargs)
        patient_id = self.kwargs.get('user_id')
        page_owner = User.objects.get(pk=patient_id)
        context['page_owner'] = page_owner
        context['self'] = False
        context['health_datas'] = HealthData.objects.filter(creator=page_owner)
        context['tasks'] = Task.objects.filter(user=context['page_owner'])
        context['health_risk'] = page_owner.health_risk
        context['health_status'] = page_owner.health_status

        return context

    @method_decorator(login_required)
    def get(self):
        slug = self.kwargs.get('slug')

    @method_decorator(login_required)
    def post(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'create_task':
            return self.create_task()
        elif slug == 'update_health_risk':
            return self.update_health_risk()
        elif slug == 'update_health_status':
            return self.update_health_status()
        elif slug == 'delete_task':
            return self.delete_task()
        else:
            raise Http404

    def create_task(self):
        context = self.get_context_data()
        content = self.request.POST['content']
        task = Task.objects.create(doctor=context['log_user'], user=context['page_owner'], content=content)

        try:
            task.save()
        except Exception:
            pass

        return HttpResponseRedirect(reverse('health:patient_homepage', kwargs={'user_id': context['page_owner'].id}))

    def update_health_risk(self):
        context = self.get_context_data()
        content = self.request.POST['content']
        # task = Task.objects.create(doctor=context['log_user'], user=context['page_owner'], content=content)
        patient_id = self.kwargs.get('user_id')
        User.objects.filter(pk=patient_id).update(health_risk=content)

        return HttpResponseRedirect(reverse('health:patient_homepage', kwargs={'user_id': context['page_owner'].id}))

    def update_health_status(self):
        context = self.get_context_data()
        score = self.request.POST['score']
        patient_id = self.kwargs.get('user_id')
        User.objects.filter(pk=patient_id).update(health_status=score)

        return HttpResponseRedirect(reverse('health:patient_homepage', kwargs={'user_id': context['page_owner'].id}))

    def delete_task(self):
        context = self.get_context_data()
        task_id = self.request.POST['task_id']
        task = Task.objects.get(pk=task_id)

        try:
            task.delete()
        except Exception:
            pass

        return HttpResponseRedirect(reverse('health:patient_homepage', kwargs={'user_id': context['page_owner'].id}))
