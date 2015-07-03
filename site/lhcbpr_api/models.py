from django.db import models
import dateutil.parser
from django.utils import timezone


import logging
logger = logging.getLogger(__name__)

DATA_TYPE_CHOICES = (
    ('String', 'String'),
    ('Float', 'Float'),
    ('Integer', 'Integer'),
    ('DateTime', 'DateTime'),
    ('File', 'File')
)


class Host(models.Model):
    hostname = models.CharField(max_length=50)
    cpu_info = models.CharField(max_length=200)
    memory_info = models.CharField(max_length=200)

    old_id = models.IntegerField(null=True, db_index=True)
    def __unicode__(self):
        return self.hostname


class Application(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __unicode__(self):
        return '{0}'.format(self.name)

class Slot(models.Model):
    name = models.CharField(max_length=50, null=False, unique=True)
    def __unicode__(self):
        return '{0}'.format(self.name)


class ApplicationVersion(models.Model):
    application = models.ForeignKey(
        Application, related_name='versions'
    )
    version = models.CharField(max_length=50)
    slot =  models.ForeignKey(
        Slot, related_name='versions', null=True
    )
    vtime = models.DateTimeField(null=True)
    is_nightly = models.BooleanField(default=False)

    class Meta:
        unique_together = ("application", "version")

    def __unicode__(self):
        return '{0} {1}'.format(self.application.name, self.version)

    @staticmethod
    def is_it_nightly(version):
        return version and (version[0] != 'v')

    @staticmethod
    def get_slot_and_number(slot_string):
        if '.'  in slot_string:
            delim = '.'
        else: 
            delim = '-'
        
        names = slot_string.split(delim)

        slot = slot_string
        number = None
        vtime = None
        try:
            if delim == '.':
                if len(names) > 1:
                    slot = names[0]
                    number = int(names[1])
                if len(names) == 3:
                    try:
                        vtime = timezone.make_aware(dateutil.parser.parse(names[2]))
                    except:
                        pass
            elif len(names) > 1: 
                slot = delim.join(names[:-1])
                number = int(names[-1])
            else:
                return None
            return (slot, number, vtime)
        except:
            return None


class Option(models.Model):
    content = models.CharField(max_length=2000)
    description = models.CharField(max_length=2000)
    is_standalone = models.BooleanField(default=False)

    old_id = models.IntegerField(null=True)
    def __unicode__(self):
        return self.description


class SetupProject(models.Model):
    content = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    old_id = models.IntegerField(null=True)
    def __unicode__(self):
        return self.description


class JobDescription(models.Model):
    application_version = models.ForeignKey(
        ApplicationVersion, related_name='job_descriptions')
    option = models.ForeignKey(
        Option, null=True, related_name='job_descriptions')
    setup_project = models.ForeignKey(
        SetupProject, null=True, related_name='job_descriptions')
    
    old_id = models.IntegerField(null=True)
    
    def __unicode__(self):
        return '{0} (id)   {1}  {2}  {3}'.format(
            self.id,
            self.application_version.version,
            self.application_version.application.name,
            self.option.description
        )


class Platform(models.Model):
    cmtconfig = models.CharField(max_length=100, unique=True)

    old_id = models.IntegerField(null=True)
    def __unicode__(self):
        return self.cmtconfig


class RequestedPlatform(models.Model):
    job_description = models.ForeignKey(JobDescription)
    cmtconfig = models.ForeignKey(Platform)

    old_id = models.IntegerField(null=True)
    class Meta:
        unique_together = ("job_description", "cmtconfig")

    def __unicode__(self):
        return '{0} (job_description_id)   ---   {1}'.format(
            self.job_description.id, self.cmtconfig
        )


class Job(models.Model):
    host = models.ForeignKey(
        Host, null=True, related_name='job')
    job_description = models.ForeignKey('JobDescription', related_name='jobs',
                                        db_column='job_description_id')
    platform = models.ForeignKey(Platform, null=True, related_name='jobs')
    time_start = models.DateTimeField()
    time_end = models.DateTimeField()
    status = models.CharField(max_length=50)
    is_success = models.BooleanField(default=False)

    old_id = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        super(Job, self).save(*args, **kwargs) # Call the "real" save() method.
        # Insert version time if not exists
        version = self.job_description.application_version
        if not version.vtime:
            version.vtime = self.time_start
            version.save()

    def results(self):
        return self.floats + self.string + self.integers

    def __unicode__(self):
        return '{0} (id) -- {1} (job_description_id)  ---  {2}  ---  {3}'\
               '  ---  {4} --- {5}'.format(
                   self.id, self.job_description.id, self.time_end,
                   self.platform.cmtconfig, self.host.hostname, self.is_success
               )


class Handler(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200)

    old_id = models.IntegerField(null=True)
    def __unicode__(self):
        return self.name

class JobHandler(models.Model):
    job_description = models.ForeignKey(JobDescription)
    handler = models.ForeignKey(Handler)

    old_id = models.IntegerField(null=True)
    class Meta:
        unique_together = ("job_description", "handler")

    def __unicode__(self):
        return '{0} (job_description_id) -- -- {1}'.format(
            self.job_description.id, self.handler
        )

class AttributeGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)

class Attribute(models.Model):
    name = models.CharField(max_length=512, db_index=True)
    dtype = models.CharField(max_length=10, choices=DATA_TYPE_CHOICES)
    description = models.CharField(max_length=500)
    groups = models.ManyToManyField(AttributeGroup, related_name='attributes')

    old_id = models.IntegerField(null=True)
    def get_result_type(self):
        return globals()["Result" + self.dtype]
    def __unicode__(self):
        return '{0} (id)  {1}  --  {2}  {3}'.format(
            self.id, self.name, self.dtype, self.description
        )


class AttributeThreshold(models.Model):
    attribute = models.ForeignKey(
        Attribute, related_name='thresholds'
    )
    option = models.ForeignKey(
        Option, related_name='thresholds'
    )
    down_value = models.FloatField()
    up_value = models.FloatField()
    start = models.DateTimeField()


def content_file_name(instance, filename):
    return '/'.join([str(instance.job.job_description.pk), str(instance.job.pk), filename])

class JobResult(models.Model):
    job = models.ForeignKey(Job, related_name='results')
    attr = models.ForeignKey(
        Attribute, related_name='jobresults')

    old_id = models.IntegerField(null=True)
    def get_value(self):
        subtype = self.attr.get_result_type()
        val = subtype.objects.get(pk=self.pk)
        return str(val.data)

    def __unicode__(self):
        return '{0} (job_id) --- {1}'.format(
            self.job.id, self.job_attribute
        )

class ResultFloat(JobResult):
    data = models.FloatField()

class ResultInteger(JobResult):
    data = models.IntegerField()

class ResultString(JobResult):
    data = models.TextField()

class ResultFile(JobResult):
    data = models.FileField()

class ResultStringSync(models.Model):
    jobresult_ptr_id=models.IntegerField()
    data = models.TextField()

    class Meta:
        managed = False
        db_table = "lhcbpr_api_resultstring"

class ResultIntegerSync(models.Model):
    jobresult_ptr_id=models.IntegerField()
    data = models.TextField()

    class Meta:
        managed = False
        db_table = "lhcbpr_api_resultinteger"

class ResultFloatSync(models.Model):
    jobresult_ptr_id=models.IntegerField()
    data = models.TextField()

    class Meta:
        managed = False
        db_table = "lhcbpr_api_resultfloat"

class ResultFileSync(models.Model):
    jobresult_ptr_id=models.IntegerField()
    data = models.TextField()

    class Meta:
        managed = False
        db_table = "lhcbpr_api_resultfile"




# custom path to save the files in format
# MEDIA_ROOT/job_description_id/job_id/filename

# custom path to save the files in format
# MEDIA_ROOT/job_description_id/job_id/filename




class HandlerResult(models.Model):
    job = models.ForeignKey(Job)
    handler = models.ForeignKey(Handler)
    is_success = models.BooleanField(default=False)

    old_id = models.IntegerField(null=True)
    def __unicode__(self):
        return '{0} (job_id) {1} --- {2}'.format(
            self.job.id, self.handler.name, self.is_success
        )


class AddedResult(models.Model):
    identifier = models.CharField(max_length=64)

    old_id = models.IntegerField(null=True)
    def __unicode__(self):
        return self.identifier
