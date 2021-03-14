from django.db import models
from django.contrib.auth.models import AbstractUser


class Dataset(models.Model):
    name = models.CharField(max_length=64, primary_key=True)
    file = models.FileField(upload_to='datahome')
    size = models.FloatField(default=0)
    times = models.IntegerField(default=0)
    cbtype = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    price = models.FloatField(default=0)
    create_time = models.DateTimeField(auto_now_add=True)
    modify_time = models.DateTimeField(auto_now=True)
    expire_time = models.DateTimeField(auto_now=False)
    verified = models.IntegerField(default=0)
    owner = models.ForeignKey('Account', related_name='owner', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'service_dataset'

    def __str__(self):
        return self.name.split('.')[0]


class ConfigFile(models.Model):
    room = models.ForeignKey('RoomDB', null=True, blank=True, on_delete=models.SET_NULL)
    file = models.FileField(upload_to='configs')

    class Meta:
        db_table = 'service_configfile'


class Account(AbstractUser):
    account = models.AutoField(primary_key=True)
    nickname = models.CharField(max_length=32, null=True, blank=True, unique=False)
    wallet = models.FloatField(default=1000)
    accessdataset = models.ManyToManyField(Dataset)
    accessroom = models.ManyToManyField('RoomDB')
    locate = models.ForeignKey('RoomDB', related_name='location', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = 'service_account'

    def __str__(self):
        return '%s' % self.username


class RoomDB(models.Model):
    chatipport = models.CharField(max_length=32)
    gradipport = models.CharField(max_length=32)
    max_memory = models.FloatField(default=1024)
    members = models.ManyToManyField(Account)
    dataset = models.ForeignKey(Dataset, null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField()
    closed = models.BooleanField(default=False)
    running = models.BooleanField(default=True)

    class Meta:
        db_table = 'service_roomdb'

    def __str__(self):
        return 'R%010d' % self.id


class GPU(models.Model):
    ipport = models.CharField(max_length=32)
    cuda = models.IntegerField(default=0)
    gputype = models.CharField(max_length=32)
    memory = models.FloatField(default=0)
    price = models.FloatField(default=20000)
    rooms = models.ManyToManyField('RoomDB')
    lat = models.FloatField(default=22.93772)
    lng = models.FloatField(default=113.38424)
    nation = models.CharField(max_length=32)
    province = models.CharField(max_length=32)
    city = models.CharField(max_length=32)
    district = models.CharField(max_length=32)
    adcode = models.IntegerField(default=440113)
    status = models.IntegerField(default=0)
    master = models.ForeignKey(Account, related_name='master', null=True, blank=True, on_delete=models.SET_NULL)
    create_time = models.DateTimeField(auto_now_add=True)
    modify_time = models.DateTimeField(auto_now=True)
    expire_time = models.DateTimeField(auto_now_add=False)

    class Meta:
        db_table = 'service_gpu'

    def __str__(self):
        return 'G%010d' % self.id


class DatasetServer(models.Model):
    ipport = models.CharField(max_length=32)

    class Meta:
        db_table = 'service_datasetserver'

    def __str__(self):
        return self.ipport
