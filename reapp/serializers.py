from rest_framework import serializers
from .models import RegisterBlog, LoginBlog, BlogArticle, BlogContactUs, Course, CartItem


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


class CartItemSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True
    )
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'user',
            'session_key',
            'course',
            'course_id',
            'quantity',
            'added_at',
            'total_price'
        ]
        read_only_fields = ['user', 'session_key', 'added_at']

    def get_total_price(self, obj):
        # Handle both model instances and dictionaries
        if isinstance(obj, dict):
            return float(obj['course']['price']) * int(obj['quantity'])
        return obj.quantity * obj.course.price

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class CartSummarySerializer(serializers.Serializer):
    items = CartItemSerializer(many=True)
    total_items = serializers.IntegerField()
    grand_total = serializers.DecimalField(max_digits=10, decimal_places=2)

    def to_representation(self, instance):
        return {
            'items': CartItemSerializer(instance['items'], many=True).data,
            'total_items': instance['total_items'],
            'grand_total': instance['grand_total']
            }
