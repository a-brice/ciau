from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def robots_txt(request):
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")


urlpatterns = [
    path('robots.txt', robots_txt),
    path('admin/', admin.site.urls),
    path('', include('projects.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
