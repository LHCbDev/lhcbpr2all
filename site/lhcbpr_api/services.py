import sys
from lhcbpr_api.models import *

import logging
logger = logging.getLogger(__name__)


class JobResultsService:
    # Returns job results grouped by attribute and by version
    # [ {id:attr_id, name:attr_name, values:[ { version:version_name, results:[ result1, ... ] }, ... ]}, ... ]
    def get_results_per_attr_per_version(self, context, only_numeric = True):
        logger.info('Service called !')
        attrs_ids = Attribute.objects
        if 'attr_filter' in context and context['attr_filter']:
            attrs_ids = attrs_ids.filter(name__icontains = context['attr_filter'])
        if only_numeric:
            attrs_ids = attrs_ids.filter(dtype__in = ['Float', 'Integer'])
        offset = context['page_size'] * (context['page'] - 1)
        limit = context['page_size']
        attrs_ids = [ i['id'] for i in attrs_ids.values('id')[offset:limit] ]
        if len(attrs_ids) < 1:
            return [];
        queryset = JobResult.objects.filter(attr__id__in = attrs_ids)
        if 'app' in context and context['app']:
            queryset = queryset.filter(job__job_description__application_version__application__id__in = context['app'])
        if 'options' in context and context['options']:
            queryset = queryset.filter(job__job_description__option__id__in = context['options'])
        if 'versions' in context and context['versions']:
            queryset = queryset.filter(job__job_description__application_version__id__in = context['versions'])
            
        queryset = queryset.select_related(
            'attr__name', 
            'job__job_description__application_version__version'
        )
        queryset = queryset.order_by('attr__id', 'job__job_description__application_version__version')
        queryset = queryset.values(
            'attr__id', 
            'attr__name',
            'job__job_description__application_version__version',
            'resultinteger',
            'resultfloat'
        )
        logger.info('Queryset Construction done')

        results = []
        current_attr_id = None
        current_result_index = -1
        current_version = None
        current_version_index = -1
        logger.info('Looping over Queryset')
        i = 1
        for item in queryset:
            # logger.info('Handeling item {0}'.format(i))
            i = i + 1
            # If new attribute, add it
            if item['attr__id'] != current_attr_id:
                results.append({
                    'id': item['attr__id'],
                    'name': item['attr__name'],
                    'values': []
                })
                current_result_index = current_result_index + 1
                current_attr_id = item['attr__id']
                current_version = None
                current_version_index = -1
            # If new version, add it
            if item['job__job_description__application_version__version'] != current_version:
                current_version = item['job__job_description__application_version__version']
                results[current_result_index]['values'].append({
                    'version': current_version,
                    'results': []
                })
                current_version_index = current_version_index + 1
            # Add the result to the current version
            if item['resultfloat']:
                results[current_result_index]['values'][current_version_index]['results'].append(item['resultfloat'] / 1000.0)
            else:
                results[current_result_index]['values'][current_version_index]['results'].append(item['resultinteger'] / 1000.0)
        
        return results

    def get_attrs_count(self, context):
        attrs = Attribute.objects
        if 'attr_filter' in context and context['attr_filter']:
            attrs = attrs.filter(name__icontains = context['attr_filter'])
        count = attrs.count()
        logger.info("Attributes count is {0}".format(count))
        return count
