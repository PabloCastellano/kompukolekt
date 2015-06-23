from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib import admin

# Vendor = 'Generic'
# Varios modulos RAM, varias GPUs, varios HDs...

class UserProfile(models.Model):
    user = models.OneToOneField(User)

    website = models.URLField(blank=True)
    picture = models.ImageField(upload_to='profile_images', blank=True)

    def get_absolute_url(self):
        return reverse('profile', args=[str(self.id)])

    def __unicode__(self):
        return self.user.username


class Computer(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    vendor = models.CharField(max_length=50, blank=True, null=True)
    is_laptop = models.BooleanField()
    is_public = models.BooleanField()
    cpu = models.ForeignKey('CPU')
    mobo = models.ForeignKey('Motherboard')
    gpu = models.ForeignKey('GPU')
    hd = models.ForeignKey('HardDisk')
    memory = models.ForeignKey('Memory')
    network = models.ForeignKey('NetworkAdapter')
    year = models.IntegerField()
    created_at = models.DateTimeField() # TODO: hide field
    updated_at = models.DateTimeField() # TODO: hide field

    class Meta:
        unique_together = (("user", "name"),)

    def get_absolute_url(self):
        return reverse('item-detail', args=[str(self.id)])

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.user)


class CPU(models.Model):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    vendor = models.CharField(max_length=50)
    num_cores = models.IntegerField(blank=True, null=True)
    url_vendor = models.URLField(blank=True, null=True)
    benchmark = models.IntegerField(blank=True, null=True)
    url_benchmark = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return "%s %s" % (self.vendor, self.model)


class Motherboard(models.Model):
    name = models.CharField(max_length=100)
    vendor = models.CharField(max_length=50)
    url_vendor = models.URLField(blank=True, null=True)
    benchmark = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return "%s %s" % (self.vendor, self.name)


class GPU(models.Model):
    name = models.CharField(max_length=100)
    vendor = models.CharField(max_length=50)
    url_vendor = models.URLField(blank=True, null=True)
    benchmark = models.IntegerField(blank=True, null=True)
    url_benchmark = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return "%s %s" % (self.vendor, self.name)


HARDDISK_CHOICES = (
    ('HDD', 'Hard Disk Drive'),
    ('SSD', 'Solid State Drive'),
)

class HardDisk(models.Model):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    vendor = models.CharField(max_length=50)
    url_vendor = models.URLField(blank=True, null=True)
    benchmark = models.IntegerField(blank=True, null=True)
    url_benchmark = models.URLField(blank=True, null=True)
    capacity_gb = models.IntegerField()
    type = models.CharField(max_length=10, choices=HARDDISK_CHOICES)

    def __unicode__(self):
        return "%s %s (%dGB)" % (self.vendor, self.name, self.capacity_gb)


MEMORY_CHOICES = (
    (256, '256 MB'),
    (512, '512 MB'),
    (1024, '1 GB'),
    (2048, '2 GB'),
    (4096, '4 GB'),
    (8192, '8 GB'),
)

class Memory(models.Model):
    name = models.CharField(max_length=100)
    vendor = models.CharField(max_length=50)
    # serial_number, KVS1033M210B,...
    url_vendor = models.URLField(blank=True, null=True)
    benchmark = models.IntegerField(blank=True, null=True)
    url_benchmark = models.URLField(blank=True, null=True)
    capacity_mb = models.IntegerField(choices=MEMORY_CHOICES)

    def __unicode__(self):
        return "%s %s (%s)" % (self.vendor, self.name, self.get_capacity_mb_display()) # MEMORY_CHOICES[self.capacity_mb]


SPEED_CHOICES = (
    ('10 Mbps', '10 Mbps'),
    ('100 Mbps', '100 Mbps'),
    ('1 Gbps', '1 Gbps'),
    ('10 Gbps', '10 Gbps')
)

class NetworkAdapter(models.Model):
    name = models.CharField(max_length=100)
    vendor = models.CharField(max_length=50)
    url_vendor = models.URLField(blank=True, null=True)
    wireless = models.BooleanField()
    speed = models.CharField(max_length=10, choices=SPEED_CHOICES)
    mac = models.CharField(max_length=17, blank=True, null=True) # XX:XX:XX:XX:XX:XX
    driver = models.CharField(max_length=20, blank=True, null=True)

    def __unicode__(self):
        return "%s %s" % (self.vendor, self.name)


admin.site.register(Computer)
admin.site.register(CPU)
admin.site.register(Motherboard)
admin.site.register(GPU)
admin.site.register(HardDisk)
admin.site.register(Memory)
admin.site.register(NetworkAdapter)