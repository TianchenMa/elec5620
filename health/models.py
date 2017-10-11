from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


GENDER = (
    ('0', u'Male'),
    ('1', u'Female')
)


IDENTITY = (
    ('0', u'TechTeam'),
    ('1', u'Doctor'),
    ('2', u'EndUser')
)


# Create your models here.
class User(AbstractUser):
    gender = models.CharField(max_length=1, default='0', choices=GENDER)
    identity = models.CharField(max_length=1, default='0', choices=IDENTITY)
    unread = models.IntegerField(default=0)
    doctor = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True
    )


class RegisterCode(models.Model):
    code = models.CharField(max_length=100, null=False)
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Creator'
    )
    used = models.BooleanField(default=False)


class HealthData(models.Model):
    heart_rate = models.IntegerField()
    weight = models.FloatField(max_length=3)
    temperature = models.FloatField(max_length=3)
    note = models.CharField(max_length=500)
    sub_date = models.DateTimeField('date submitted')

    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Owner'
    )

    def save(self, *args, **kwargs):
        if not self.id:
            self.sub_date = timezone.now()

        return super(HealthData, self).save(*args, **kwargs)


class Message(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sender'
    )

    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='receiver'
    )

    content = models.CharField(max_length=200, null=True)
    viewed = models.BooleanField(default=False)
    send_date = models.DateTimeField('send date.')

    def save(self, *args, **kwargs):
        if not self.id:
            self.send_date = timezone.now()

        return super(Message, self).save(*args, **kwargs)