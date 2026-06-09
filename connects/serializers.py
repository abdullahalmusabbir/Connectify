from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


#  USER SERIALIZER

class SimpleUserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

    def get_role(self, obj):
        if hasattr(obj, 'admin_profile') and obj.admin_profile:
            return 'Admin'
        if hasattr(obj, 'moderator_profile') and obj.moderator_profile:
            return 'Moderator'
        if hasattr(obj, 'guest_profile') and obj.guest_profile:
            return 'Guest'
        return 'Regular User'

#  PROFILE SERIALIZERS

class AdminProfileSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = AdminProfile
        fields = ['id', 'user', 'avatar', 'bio', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ModeratorProfileSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = ModeratorProfile
        fields = ['id', 'user', 'avatar', 'bio', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class RegularProfileSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = RegularProfile
        fields = ['id', 'user', 'avatar', 'bio', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class GuestProfileSerializer(serializers.ModelSerializer):
    user = SimpleUserSerializer(read_only=True)

    class Meta:
        model = GuestProfile
        fields = ['id', 'user', 'avatar', 'bio', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


#  COMMENT SERIALIZERS

class ReplySerializer(serializers.ModelSerializer):
    """Nested replies dekhanor jonno """
    author = SimpleUserSerializer(read_only=True)
    is_reply = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content',
            'is_reply', 'reply_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    author = SimpleUserSerializer(read_only=True)
    # Nested replies show korbe
    replies = ReplySerializer(many=True, read_only=True)
    is_reply = serializers.BooleanField(read_only=True)
    reply_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'parent',
            'content', 'is_reply', 'reply_count',
            'replies', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """
        Jodi parent comment dewa hoy,
        tahole parent ar post same hote hobe
        """
        parent = data.get('parent')
        post = data.get('post')

        if parent and post:
            if parent.post != post:
                raise serializers.ValidationError(
                    "Parent comment ei post er na."
                )
        return data


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Shudhu comment create er jonno.
    Author auto-assign hobe view theke.
    """

    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'content']

    def validate_parent(self, value):
        """Parent thakle check korbe reply of reply na hoy"""
        if value and value.parent is not None:
            raise serializers.ValidationError(
                "Reply er reply kora jabe na."
            )
        return value

    def create(self, validated_data):
        # Author view theke request.user hisebe pass hobe
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)

#  POST SERIALIZERS

class PostListSerializer(serializers.ModelSerializer):
    """
    List view er jonno - lightweight.
    Sob comment load korbe na.
    """
    author = SimpleUserSerializer(read_only=True)
    is_published = serializers.BooleanField(read_only=True)
    short_content = serializers.CharField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'title', 'slug',
            'short_content', 'status', 'is_pinned',
            'is_published', 'comment_count',
            'post_image', 'view_count',
            'published_at', 'created_at'
        ]
        read_only_fields = ['view_count', 'published_at', 'created_at']


class PostDetailSerializer(serializers.ModelSerializer):
    """
    Detail view - full content + comments show korbe
    """
    author = SimpleUserSerializer(read_only=True)
    # Shudhu top-level comments (parent=None)
    comments = serializers.SerializerMethodField()
    is_published = serializers.BooleanField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'title', 'slug', 'content',
            'status', 'is_pinned', 'is_published',
            'post_image', 'post_video',
            'view_count', 'comment_count', 'comments',
            'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['view_count', 'published_at', 'created_at', 'updated_at']

    def get_comments(self, obj):
        """Shudhu top-level comments fetch korbe"""
        top_level_comments = obj.comments.filter(parent=None)
        return CommentSerializer(
            top_level_comments,
            many=True,
            context=self.context
        ).data


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Post create/update er jonno.
    Author auto-assign hobe.
    """

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'content',
            'status', 'is_pinned',
            'post_image', 'post_video',
        ]

    def validate_status(self, value):
        request = self.context.get('request')
        if not request:
            return value

        user = request.user
        # Allow staff/superuser, or users with admin/moderator profiles
        is_privileged = (
            user.is_staff
            or user.is_superuser
            or hasattr(user, 'admin_profile')
            or hasattr(user, 'moderator_profile')
        )

        if value == PostStatus.PUBLISHED and not is_privileged:
            raise serializers.ValidationError(
                "Apnar post publish korar permission nei."
            )
        return value

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError(
                "Title kom poke 5 character hote hobe."
            )
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
        return super().create(validated_data)
    
    