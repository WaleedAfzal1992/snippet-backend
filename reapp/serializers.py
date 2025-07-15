from rest_framework import serializers
from .models import RegisterBlog, LoginBlog, BlogArticle, BlogContactUs, Course


class RegisterSerializers(serializers.ModelSerializer):
    class Meta:
        model = RegisterBlog
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = RegisterBlog(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializers(serializers.ModelSerializer):
    class Meta:
        model = LoginBlog
        fields = '__all__'


class BlogArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogArticle
        fields = ['id', 'title', 'content']


class BlogContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogContactUs
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = '__all__'
