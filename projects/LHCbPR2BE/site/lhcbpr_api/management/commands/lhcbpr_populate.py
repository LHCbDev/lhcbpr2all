from django.core.management.base import BaseCommand, CommandError
from lhcbpr_api.models import (Application, ApplicationVersion, SetupProject,
                               Option, JobDescription, JobResult,
                               Attribute, AttributeThreshold, Job, Platform,
                               Host, Handler)
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Fill initial data'

    def handle(self, *args, **options):

        gauss_app = Application(name='Gauss')
        brunel_app = Application(name='Brunel')

        gauss_app.save()
        brunel_app.save()

        v1 = ApplicationVersion(application=gauss_app, version='v1r0')
        v2 = ApplicationVersion(application=gauss_app, version='v2r0')
        v3 = ApplicationVersion(application=gauss_app, version='v3r0')
        
        v4 = ApplicationVersion(application=brunel_app, version='v1r0')
        v1.save()
        v2.save()
        v3.save()
        v4.save()

        setup1 = SetupProject(
            content='--no-user-area', description='some description')

        opt1 = Option(
            content='my_option.py', description='run my option', is_standalone=False)
        opt2 = Option(content='my_standalone_option.py',
                      description='run my standalone option', is_standalone=True)
        setup1.save()
        opt1.save()
        opt2.save()

        jd1 = JobDescription(
            setup_project=setup1, application_version=v1, option=opt1)
        
        jd2 = JobDescription(
            setup_project=setup1, application_version=v2, option=opt1)
        jd3 = JobDescription(
            setup_project=setup1, application_version=v3, option=opt1)
        jd4 = JobDescription(
            setup_project=setup1, application_version=v4, option=opt2)
        
        jd1.save()
        jd2.save()
        jd3.save()
        jd4.save()

        a1 = Attribute(name="timer", dtype='float', description="My timer")
        a1.save()

        at1 = AttributeThreshold(option=opt1, attribute=a1, down_value=0,
                                 up_value=2, start=timezone.now())
        at1.save()

        pl1 = Platform(cmtconfig="x86_64-slc6-gcc48-opt")
        pl1.save()

        h1 = Host(hostname="mazurov-host", cpu_info="my cpu_info",
                  memory_info="my memory_info")
        h1.save()

        tstart = timezone.now()
        td = timedelta(hours=1)
        tend = tstart + td

        j1 = Job(host=h1, job_description=jd1, platform=pl1,
            time_start=tstart, time_end=tend,status='OK', is_success=True)
        j1.save()
        
        j2 = Job(host=h1, job_description=jd2, platform=pl1,
            time_start=tstart, time_end=tend,status='OK', is_success=True)
        j2.save()

        j3 = Job(host=h1, job_description=jd3, platform=pl1,
            time_start=tstart, time_end=tend,status='OK', is_success=True)
        j3.save()
        j4 = Job(host=h1, job_description=jd4, platform=pl1,
            time_start=tstart, time_end=tend,status='OK', is_success=True)
        j4.save()

        hn1 = Handler(name="SimpleHandler", description="Description")
        hn1.save()

        jr1= JobResult(job=j1, handler=hn1, attr=a1, val_float=10.5)
        jr2= JobResult(job=j2, handler=hn1, attr=a1, val_float=11.2)
        jr3= JobResult(job=j3, handler=hn1, attr=a1, val_float=10.6)
        jr1.save()
        jr2.save()
        jr3.save()
