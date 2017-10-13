import random
import hashlib
import string

from django.db.models.aggregates import Count
from django.db.models import F, Q
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, Http404, HttpResponseNotAllowed, HttpResponseServerError
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View, TemplateView
from django.views.generic.edit import ContextMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import *


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
        else:
            context['log_user'] = None

        return context


class WelcomeView(BaseMixin, TemplateView):
    template_name = 'health/welcome.html'

    def get_context_data(self, **kwargs):
        context = super(WelcomeView, self).get_context_data(**kwargs)

        return context


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
        context['announcements'] = Announcement.objects.filter(publisher=context['log_user'])
        context['patients'] = User.objects.filter(identity='2', doctor=context['log_user'])
        return render(self.request, 'health/doctor_homepage.html', context)

    def enduser_homepage(self, context):
        context['page_owner'] = context['log_user']

        unviewed_announcements = Announcement.objects.filter(announcementreceive__enduser=context['log_user'], announcementreceive__viewed=False)
        viewed_announcements = AnnouncementReceive.objects.filter(announcementreceive__enduser=context['log_user'], announcementreceive__viewed=True)

        context['unviewed_announcements'] = unviewed_announcements
        context['viewed_announcements'] = viewed_announcements
        context['doctor'] = context['log_user'].doctor
        context['health_datas'] = HealthData.objects.filter(creator=context['log_user'])
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
        else:
            raise Http404

    def create_code(self, context):
        if context['identity'] != '0':
            return

        code_content = generate_register_code(context['log_user'])
        code = RegisterCode.objects.create(code=code_content, creator=context['log_user'])

        try:
            code.save()
        except Exception as e:
            pass

        return HttpResponseRedirect(reverse('health:homepage'))

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

        return HttpResponseRedirect(reverse('health:homepage'))

    def create_doctor_account(self, context):
        if context['identity'] != '0':
            return

        doctor_name = self.request.POST['doctor_name']
        doctor, password = generate_doctor(doctor_name)

        try:
            doctor.save()
        except Exception:
            return HttpResponseServerError()

        message = Message.objects.create(from_user=context['log_user'], to_user=context['log_user'])
        message.content = 'Doctor username: ' + doctor_name + '<br>' + 'Password: ' + password

        try:
            message.save()
        except Exception:
            doctor.delete()
            return HttpResponseServerError()

        return HttpResponseRedirect(reverse('health:homepage'))

    def choose_doctor(self, context):
        if context['identity'] != '2':
            return

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
            return

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


# URL name = 'user_control'
class UserControlView(BaseMixin, View):
    def get(self, *args, **kwargs):
        slug = self.kwargs.get('slug')

        if slug == 'register':
            return render(self.request, 'health/register.html')

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
                    user = User.objects.create(username=username, identity='2')
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

        return context


# URL name = 'doctor_operations'
class DoctorOperationView(BaseMixin, View):
    def get_context_data(self, **kwargs):
        context = super(DoctorOperationView, self).get_context_data(**kwargs)

        return context

    @method_decorator(login_required)
    def get(self):
        slug = self.kwargs.get('slug')

    @method_decorator(login_required)
    def post(self):
        slug = self.kwargs.get('slug')

