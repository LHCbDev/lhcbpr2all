from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
# =============================================================================
from rest_framework.routers import DefaultRouter
from rest_framework_extensions.routers import ExtendedDefaultRouter
# =============================================================================
from lhcbpr_api import views
# =============================================================================
router = ExtendedDefaultRouter()
default_router = DefaultRouter()
# =============================================================================

router.register(r'applications', views.ApplicationViewSet)
router.register(r'versions', views.ApplicationVersionViewSet)
router_options = router.register(r'options', views.OptionViewSet)
router.register(r'groups', views.AttributeGroupViewSet)
router.register(r'attributes', views.AttributeViewSet)
router.register(r'setups', views.SetupProjectViewSet)
router_jd = router.register(r'descriptions', views.JobDescriptionViewSet)
router.register(r'thresholds', views.AttributeThresholdViewSet)
router.register(r'handlers', views.HandlerViewSet)
router.register(r'platforms', views.PlatformViewSet)
router.register(r'hosts', views.HostViewSet)
router.register(r'results', views.JobResultViewSet)
# =============================================================================

router_jobs = router.register(r'jobs', views.JobViewSet, base_name='job')
router_jobs.register(r'hosts',
                     views.HostViewSet,
                     base_name='jobs-host',
                     parents_query_lookups=['job'])
router_jobs.register(r'platforms',
                     views.PlatformViewSet,
                     base_name='jobs-platform',
                     parents_query_lookups=['jobs'])
router_jobs.register(r'job_descriptions',
                     views.JobDescriptionViewSet,
                     base_name='jobs-description',
                     parents_query_lookups=['jobs'])
router_jobs.register(r'results',
                     views.JobResultNoJobViewSet,
                     base_name='jobs-results',
                     parents_query_lookups=['job'])

router.register(
    r'result_by_opt_and_attr/(?P<option>[^/.]+)_(?P<attr>[^/.]+)', views.JobResultByOptionAndAttribute, base_name="result_by_opt_and_attr")

router.register(
    r"active/applications", views.ActiveApplicationViewSet,
    base_name="applications-active"
)

router.register(
    r"search-jobs", views.SearchJobsViewSet,
    base_name="search-jobs"
)

router.register(
    r"compare", views.CompareJobsViewSet,
    base_name="compare-jobs"
)

router.register(
    r"trends",
    views.TrendsViewSet,
    base_name="trends"
)

router.register(
    r"histograms",
    views.HistogramsViewSet,
    base_name="histograms"
)

# =============================================================================
router_jd.register(r'jobs', views.JobViewSet, base_name='jobdescription-job',
                   parents_query_lookups=['job_description'])
router_jd.register(r'options', views.OptionViewSet, base_name="jobdescription-option",
                   parents_query_lookups=['job_descriptions'])
# =============================================================================

# router.register(
#     r"active/options", views.ActiveOptionViewSet,
#     base_name="options-active"
# )


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api/', include(default_router.urls)),

    url(r'^api-auth/',
        include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^$', RedirectView.as_view(url='/api', permanent=True)),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


