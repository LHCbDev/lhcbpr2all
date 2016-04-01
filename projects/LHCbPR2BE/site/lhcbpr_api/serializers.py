from lhcbpr_api.models import (Application, ApplicationVersion, Option,
                               SetupProject, JobDescription, Attribute,
                               AttributeGroup,
                               AttributeThreshold, Handler, HandlerResult,
                               JobHandler, AddedResult, Job, Host,
                               JobResult, Platform)
from rest_framework import serializers
from rest_framework_extensions.fields import ResourceUriField



class AttributeNoThresholdsSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = ResourceUriField(
        view_name='attribute-detail', read_only=True)

    class Meta:
        model = Attribute
        fields = ('id', 'resource_uri', 'name', 'dtype', 'description')


class AttributeThresholdSerializer(serializers.HyperlinkedModelSerializer):
    attribute = AttributeNoThresholdsSerializer(many=False, read_only=True)

    class Meta:
        model = AttributeThreshold
        fields = ('attribute', 'option', 'up_value', 'down_value', 'start')


class OptionSerializer(serializers.HyperlinkedModelSerializer):
    thresholds = AttributeThresholdSerializer(many=True, read_only=True)

    class Meta:
        model = Option
        fields = (
            'id', 'content', 'description', 'is_standalone', 'thresholds')


class SetupProjectSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = SetupProject
        fields = ('content', 'description')


class ApplicationNoVerSerializer(serializers.HyperlinkedModelSerializer):
    # versions = serializers.StringRelatedField(many=True)
    # versions = ApplicationVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'name')


class JobDescriptionNoVersionSerializer(serializers.HyperlinkedModelSerializer):
    option = OptionSerializer(many=False)
    setup_project = SetupProjectSerializer(many=False)

    class Meta:
        model = JobDescription
        fields = ('setup_project', 'option')

class ApplicationVersionSerializer(serializers.HyperlinkedModelSerializer):
    job_descriptions = JobDescriptionNoVersionSerializer(many=True, read_only=True)
    application = ApplicationNoVerSerializer(many=False, read_only=True)

    class Meta:
        model = ApplicationVersion
        fields = ('id', 'application', 'version', 'is_nightly', 'job_descriptions')


class JobDescriptionSerializer(serializers.HyperlinkedModelSerializer):
    application_version = ApplicationVersionSerializer(
        many=False, read_only=True)
    option = OptionSerializer(many=False)
    setup_project = SetupProjectSerializer(many=False)

    class Meta:
        model = JobDescription
        fields = ('application_version', 'setup_project', 'option')


class ApplicationSerializer(serializers.HyperlinkedModelSerializer):
    versions = ApplicationVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = ('id', 'name', 'versions')


class AttributeSerializer(serializers.HyperlinkedModelSerializer):
    thresholds = AttributeThresholdSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ('id', 'name', 'dtype', 'description', 'thresholds')



class AttributesWithJobResultsSerializer(serializers.HyperlinkedModelSerializer):
    thresholds = AttributeThresholdSerializer(many=True, read_only=True)
    jobvalues = serializers.SerializerMethodField()
    
    class Meta:
        model = Attribute
        fields = ('id', 'name', 'dtype', 'description', 'thresholds', 'jobvalues')

    def get_jobvalues(self, obj):
        jobresults = JobResult.objects.filter(job__id__in=self.context["ids"], attr=obj)
        serializer = JobResultOnlyValueSerializer(jobresults, many=True, read_only=True, context=self.context)
        return serializer.data


class AttributeGroupListSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = ResourceUriField(view_name='attributegroup-detail', read_only=True)
    class Meta:
        model = AttributeGroup
        fields = ('id', 'resource_uri', 'name')

class AttributeGroupRetrieveSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = ResourceUriField(view_name='attributegroup-detail', read_only=True)
    attributes = AttributeSerializer(many=True, read_only=True)
    class Meta:
        model = AttributeGroup
        fields = ('id', 'resource_uri', 'name', 'attributes')

class HandlerSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Handler
        fields = ('name', 'description')


class JobHandlerSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = JobHandler
        fields = ('job_description', 'handler')


class HandlerResultSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = HandlerResult
        fields = ('job', 'handler', 'is_success')


class AddedResultSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = AddedResult
        fields = ('identifier',)




class HostSerializer(serializers.HyperlinkedModelSerializer):
    #host = HostSerializer(many=False)

    class Meta:
        model = Host
        fields = ('id', 'hostname', 'cpu_info', 'memory_info')


class PlatformSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Platform
        fields = ('cmtconfig',)

class JobResultNoJobSerializer(serializers.HyperlinkedModelSerializer):
    attr = AttributeSerializer(many=False, read_only=True)
    value = serializers.CharField(source="get_value")
    class Meta:
        model = JobResult
        fields = ('attr', 'value')

class JobResultValueSerializer(serializers.HyperlinkedModelSerializer):
    attr = AttributeSerializer(many=False, read_only=True)
    value = serializers.CharField(source="get_value")
    class Meta:
        model = JobResult
        fields = ('attr', 'value')

class JobIdSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = ResourceUriField(view_name='job-detail', read_only=True)
    class Meta:
        model = Job
        fields = ('id', 'resource_uri')


class JobResultOnlyValueSerializer(serializers.HyperlinkedModelSerializer):
    value = serializers.CharField(source="get_value")
    job = JobIdSerializer()
    class Meta:
        model = JobResult
        fields = ('job', 'value')

class JobSerializer(serializers.HyperlinkedModelSerializer):
    job_description = JobDescriptionSerializer(many=False, read_only=True)
    host = HostSerializer(many=False, read_only=True)
    platform = PlatformSerializer(many=False, read_only=True)
    resource_uri = ResourceUriField(view_name='job-detail', read_only=True)
    #results = JobResultNoJobSerializer(many=True, read_only=True)
    class Meta:
        model = Job
        fields = ('id', 'resource_uri', 'job_description', 'host', 'platform',
                  'time_start', 'time_end', 'status', 'is_success')

class JobIdSerializer(serializers.HyperlinkedModelSerializer):
    resource_uri = ResourceUriField(view_name='job-detail', read_only=True)
    #results = JobResultNoJobSerializer(many=True, read_only=True)
    class Meta:
        model = Job
        fields = ('id', 'resource_uri')

class JobResultNoJobSerializer(serializers.HyperlinkedModelSerializer):
    attr = AttributeSerializer(many=False, read_only=True)
    value = serializers.CharField(source="get_value")
    class Meta:
        model = JobResult
        fields = ('attr', 'value')

class JobResultSerializer(serializers.HyperlinkedModelSerializer):
    attr = AttributeSerializer(many=False, read_only=True)
    job = JobSerializer(many=False, read_only=True)
    value = serializers.CharField(source="get_value")
    class Meta:
        model = JobResult
        fields = ('attr', 'value','job', )


class ActiveItemSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    name=serializers.CharField(max_length=200)
    count=serializers.IntegerField()

# class TrendValueSerializer(serializers.Serializer):
#     version = serializers.CharField(max_length = 200)
#     average = serializers.DecimalField(max_digits = 12, decimal_places = 2)
#     deviation = serializers.DecimalField(max_digits = 12, decimal_places = 2)

# class TrendsSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     name = serializers.CharField(max_length = 200)
#     values = serializers.ListField(serializers.DictField(child = TrendValueSerializer()))

# class HistogramValueSerializer(serializers.Serializer):
#     version = serializers.CharField(max_length = 200)
#     jobs = serializers.ListField(serializers.IntegerField())

# class HistogramsSerializer(serializers.Serializer):
#     id = serializers.IntegerField()
#     name = serializers.CharField(max_length = 200)
#     min_value = serializers.FloatField()
#     max_value = serializers.FloatField()
#     interval_width = serializers.FloatField()
#     values = serializers.ListField(serializers.DictField(child = HistogramValueSerializer()))
