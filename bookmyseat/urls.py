from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import book_seats
from users.views import home

urlpatterns = [
    path('admin/', admin.site.urls),  
    path('users/', include('users.urls')),
    path('movies/', include('movies.urls')),
    path('theater/<int:theater_id>/seats/book/', book_seats, name='book_seats'),
    path('', home, name='home'), 
]

urlpatterns += [
    path('', include('movies.urls')), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
