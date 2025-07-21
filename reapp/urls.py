from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import BlogArticleDetailView, UpdateBlogArticleView, RegistrationViewSet, LoginViewSet, ContactUsViewSet, CourseViewSet, CartItemViewSet
from django.conf.urls.static import static
from django.conf import settings

router = DefaultRouter()
router.register(r'register', RegistrationViewSet, basename='api-register')
router.register(r'login', LoginViewSet, basename='api-login')
router.register(r'contact', ContactUsViewSet, basename='api-contact')
router.register(r'course', CourseViewSet, basename='api-course')
router.register(r'cart', CartItemViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
    path('articles/', views.create_blog_article, name='create_blog_article'),
    path('articles/<int:id>/update/', UpdateBlogArticleView.as_view(), name='UpdateBlogArticleView'),
    path('articles/<int:id>/', views.get_blog_article_by_id, name='get_blog_article_by_id'),  # This is for GET
    path('articles/<int:id>/delete/', BlogArticleDetailView.as_view(), name='delete_blog_article'),  # This is for DELETE
    path('api-auth/', include('rest_framework.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
