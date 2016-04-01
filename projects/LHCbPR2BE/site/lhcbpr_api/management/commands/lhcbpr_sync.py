from django.core.management.base import BaseCommand
import lhcbpr.models as v1
import lhcbpr_api.models
from lhcbpr_api.models import *
from django.db import connection
from django.db import IntegrityError

import logging
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Synchronize with v1 database"

    applications = {}
    options = {}
    setups = {}
    descriptions = {}
    platforms = {}
    handlers = {}
    job_handlers = {}
    hosts = {}
    groups = {}
    attributes = {}

    def handle(self, *args, **options):
        # Applications

        for app_source in v1.Application.objects.using('v1').all():
            Command.applications[app_source.id] = self._application(app_source)
 
        # Options
        for option_source in v1.Options.objects.using('v1').all():
            Command.options[option_source.id] = self._option(option_source)
  
        # Setup project
        for setup_source in v1.SetupProject.objects.using('v1').all():
            Command.setups[setup_source.id] = self._setup_project(setup_source)

        # Job descriptions
        for jd_source in v1.JobDescription.objects.using('v1').all():
            Command.descriptions[jd_source.id] = self._job_description(jd_source)
            

        # Platform
        for pl_source in v1.Platform.objects.using('v1').all():
            Command.platforms[pl_source.id] = self._platform(pl_source)

        # Handler
        for handler_source in v1.Handler.objects.using('v1').all():
            Command.handlers[handler_source.id] = self._handler(handler_source)

        # JobHandler
        for jh_source in v1.JobHandler.objects.using('v1').all():
            Command.job_handlers[jh_source.id] = self._job_handler(jh_source)


        # Host
        for host_source in v1.Host.objects.using('v1').all():
            Command.hosts[host_source.id] = self._host(host_source)

        # Attributes
        for attr_source in v1.JobAttribute.objects.using('v1').iterator():
            if attr_source.name not in Command.attributes:
                Command.attributes[attr_source.name] = self._job_attribute(attr_source)


    
        self._jobs();
        self._job_results();


    def _application(self, app_source):
        app_target, created = Application.objects.get_or_create(name=app_source.appName)
        
        app_version_target = ApplicationVersion.objects.filter(
            version=app_source.appVersion, application=app_target)
        
        if not app_version_target:
            is_nightly = ApplicationVersion.is_it_nightly(app_source.appVersion)
            
            slot = None 
            slotname = None
            number = None
            vtime = None
            
            if is_nightly:
                res = ApplicationVersion.get_slot_and_number(app_source.appVersion)

                if res:
                    slotname,number,vtime = res
                else:
                    slotname = app_source.appVersion
                if slotname:    
                    slot, created = Slot.objects.get_or_create(name=slotname)

            app_version_target = ApplicationVersion.objects.create(
                version=app_source.appVersion,
                application=app_target,
                slot=slot,
                vtime=vtime,
                is_nightly=is_nightly
            )
            app_version_target.save()

        else:
            app_version_target = app_version_target[0]

        return app_version_target.id

    def _option(self, option_source):
        option_target, created = Option.objects.get_or_create(
            old_id=option_source.id,
            content=option_source.content,
            description=option_source.description
        )
        return option_target.id

    def _setup_project(self, setup_source):
        setup_target, created = SetupProject.objects.get_or_create(
            content=setup_source.content,
            description=setup_source.description,
            old_id=setup_source.id
        )
        return setup_target.id

    def _job_description(self, jd_source):
        if jd_source.setup_project:
            setup_id = Command.setups[jd_source.setup_project_id]
        else:
            setup_id = None

        jd_target, created = JobDescription.objects.get_or_create(
            old_id=jd_source.id,
            application_version_id=Command.applications[jd_source.application_id], 
            option_id=Command.options[jd_source.options_id],
            setup_project_id=setup_id
        )
        return jd_target.id

    def _platform(self, pl_source):
        pl_target, created = Platform.objects.get_or_create(
            cmtconfig=pl_source.cmtconfig,
            old_id=pl_source.id
        )
        return pl_target.id

    def _handler(self, handler_source):
        handler_target, created = Handler.objects.get_or_create(
            old_id=handler_source.id,
            name=handler_source.name,
            description=handler_source.description
        )
        return handler_target.id

    def _job_handler(self, jh_source):
 
        jh_target, created = JobHandler.objects.get_or_create(
            old_id=jh_source.id,
            job_description_id=Command.descriptions[jh_source.jobDescription_id],
            handler_id=Command.handlers[jh_source.handler_id]
        )
        return jh_target.id

    def _host(self, host_source):
        host_target, created = Host.objects.get_or_create(
            hostname=host_source.hostname,
            cpu_info=host_source.cpu_info,
            memory_info=host_source.memoryinfo,
            old_id=host_source.id
        )
     
        return host_target.id

    def _jobs(self):
        njobs = v1.Job.objects.using('v1').count()
        logger.info("Number of jobs in V1 %d" % njobs)
        jobs = []
        for job_source in v1.Job.objects.using('v1').order_by('-time_start').iterator():
            if (len(jobs) % 1000 == 0):
                Job.objects.bulk_create(jobs)
                jobs = []
            njobs -= 1
            logger.info("Jobs to process: %d" % njobs) 
        
            job_target = Job(
                id=job_source.id,
                host_id= Command.hosts[job_source.host_id],
                job_description_id= Command.descriptions[job_source.jobDescription_id],
                platform_id=Command.platforms[job_source.platform_id],
                time_start=job_source.time_start,
                time_end=job_source.time_end,
                status=job_source.status,
                is_success=True if job_source.success else False
            )
            jobs.append(job_target)

        Job.objects.bulk_create(jobs)

    def _job_attribute(self, ja_source):
        if ja_source.group:
            group_id = Command.groups.get(ja_source.group, None)
            if  not group_id :
                group, created = AttributeGroup.objects.get_or_create(name=ja_source.group)
                group_id = group.id
                Command.groups[ja_source.group] = group_id
        else:
            group_id = None
        
        ja_target = Attribute.objects.filter(name=ja_source.name)
        if not ja_target:
            ja_target = Attribute.objects.create(
                name=ja_source.name,
                dtype=ja_source.type,
                description=ja_source.description
            )

            if group_id:
                ja_target.groups.add(group_id)
        else:
            ja_target = ja_target[0]
            
        return (ja_target.id, ja_target.dtype)

    def _job_results(self):
        objs  = []
        count = 0
        max_jr = 0
        for jr in v1.JobResults.objects.using('v1').order_by('-id').values("id", "job_id", "jobAttribute__name").iterator():
            if len(objs) == 100000:
                logger.info("Processed %d results" % count)
                JobResult.objects.bulk_create(objs)
                objs = []
            if max_jr == 0:
                max_jr = jr['id']
            count += 1
            objs.append(JobResult(id=jr['id'], job_id=jr['job_id'], attr_id=Command.attributes[jr[ "jobAttribute__name"]][0]))
        JobResult.objects.bulk_create(objs)
        
        failed = [] 
        exists = {}
        for t in ["Float", "File", "Integer", "String"]:
            source_type = "Int" if t == "Integer" else t
            field = 'file' if t == "File" else "data"

            source_class = getattr(v1, "Result" + source_type)
            target_class = getattr(lhcbpr_api.models, "Result%sSync" % t)
            
            #table_name = "lhcbpr_api_Result%s" % t 
            objs = []
            count = 0
  
            q = source_class.objects.using('v1').filter(jobresults_ptr_id__lt=max_jr).select_related('jobAttribute__name').values_list('jobresults_ptr_id', field,'jobAttribute__name')
            for value in q.iterator():
                if len(objs) == 1000000:
                    target_class.objects.bulk_create(objs)
                    objs = []
                    logger.info("Inserted %d records to %s results" % (count, t))

                if value[0] not in exists:
                    objs.append(target_class(jobresult_ptr_id=value[0], data=value[1]))
                else:
                    logger.warning("jobresults_ptr_id already exists: %d" % value[0])
                    failed.append(value[0])
                exists[value[0]] = True
                count += 1
            
            target_class.objects.bulk_create(objs)


        if failed:
            logger.warning("Duplicates of  jobresults_ptr_id: %s" % str(failed))
