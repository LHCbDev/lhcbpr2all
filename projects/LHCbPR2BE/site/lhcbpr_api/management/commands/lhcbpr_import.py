# test
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.dateparse import parse_datetime

from lhcbpr_api.models import (
    AddedResult, Application, ApplicationVersion, Option, SetupProject,
    JobDescription, Job, Host, Platform,
    Attribute, AttributeGroup
)

from dateutil import parser
import pytz
from glob import glob
import zipfile
import json
import os


import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import job JSON result file (json_results)"

    def add_arguments(self, parser):
        parser.add_argument('dir', help="Directory with zipped results")

    def process_results(self, unzipper):
        data = json.loads(unzipper.read('json_results'))
        print(json.dumps(data, indent=2, sort_keys=True))

        app, _ = Application.objects.get_or_create(name=data['app_name'])
        ver, _ = ApplicationVersion.objects.get_or_create(
            application=app,
            vtime=data['app_version_datetime'],
            version=data['app_version']
        )

        option = Option.objects.filter(description=data['opt_name'])
        if option:
            option = option[0]
        else:
            option = Option.objects.create(
                description=data['opt_name'],
                content=data['opt_name'],
                is_standalone=data['opt_standalone']
            )

        setup = SetupProject.objects.filter(description=data['setup_name'])
        if setup:
            setup = setup[0]
        else:
            setup = SetupProject.objects.create(
                description=data['setup_name'],
                content=data['setup_content']
            )

        jd, created = JobDescription.objects.get_or_create(
            application_version=ver,
            option=option,
            setup_project=setup
        )

        if created:
            logger.info("Created new job description (id={})".format(jd.id))
        else:
            logger.info("Use existing job description (id={})".format(jd.id))

        host, _ = Host.objects.get_or_create(
            hostname=data['HOST']['hostname'],
            cpu_info=data['HOST']['cpu_info'],
            memory_info=data['HOST']['memoryinfo']
        )

        platform, _ = Platform.objects.get_or_create(
            cmtconfig=data['CMTCONFIG']['platform']
        )

        time_start = parser.parse(data['time_start'])
        time_end = parser.parse(data['time_end'])
        #tz = pytz.timezone("CET")
        #print("SASHA " + time_start)
        job = Job.objects.create(
            job_description=jd,
            host=host,
            platform=platform,
            time_start=time_start,
            time_end=time_end,
            status=data['status'],
            is_success=True
        )

        logger.info("Created new job (id={})".format(job.id))
        self.process_attributes(job, data['JobAttributes'], unzipper)

        # job.delete()

    def process_attributes(self, job, attrs, unzipper):

        for attr_source in attrs:
            attr = Attribute.objects.filter(name=attr_source['name'])
            if attr:
                attr = attr[0]
            else:
                attr = Attribute.objects.create(
                    name=attr_source['name'],
                    dtype=attr_source['type'],
                    description=attr_source['description']
                )

                if attr_source['group']:
                    group, created = AttributeGroup.objects.get_or_create(
                        name=attr_source['group'])
                    attr.groups.add(group)

            if attr.dtype != attr_source['type']:
                logger.error(
                    "Attribute {} already exists, but has type {}, not {}".format(
                        attr.name,
                        attr.dtype,
                        attr_source['type']
                    )
                )
                continue

            if attr.dtype == 'File':
                self.process_file(job.id, attr.name, unzipper.read(attr.name))

            result = attr.get_result_type().objects.create(
                job=job,
                attr=attr,
                data=attr_source[
                    'filename' if attr.dtype == 'File' else 'data']
            )
            logger.info(
                "Created {}={} (id={})".format(attr.name,
                                               result.data, result.id)
            )
            # result.delete()

    def process_file(self, job_id, name, file):
        path_dir = os.path.join(settings.JOBS_UPLOAD_DIR, str(job_id))
        path_file = os.path.join(path_dir, name)

        try:
            if not os.path.exists(path_dir):
                os.makedirs(path_dir)
            with open(path_file, 'w') as f:
                f.write(file)
        except Exception:
            logger.exception("Could not write file {}".format(path_file))
            return False
        return True

    def handle(self, *args, **options):
        ext = '*.zip'
        zip_files = glob(os.path.join(options['dir'], ext))
        logger.info(options['dir'])
        for zip_file in zip_files:
            name_noext = os.path.basename(zip_file[:-(len(ext) - 1)])
            logger.info("Zip file {}".format(name_noext))
            _, created = AddedResult.objects.get_or_create(
                identifier=name_noext)
            if not created:
                logger.info(
                    "Zip file '{}' was proccessed earlier. Abort.".format(
                        name_noext)
                )
                continue
            logger.info("Process zip file '{}'".format(name_noext))

            unzipper = zipfile.ZipFile(zip_file)
            self.process_results(unzipper)
