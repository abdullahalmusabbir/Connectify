from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

#  PROFILE MODELS

class AdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='admin_profile', null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', null=True, blank=True, verbose_name=_('Avatar'))
    bio = models.TextField(max_length=500, blank=True, verbose_name=_('Biography'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin: {self.user.username}"


class ModeratorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='moderator_profile', null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Moderator: {self.user.username}"


class RegularProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='regular_profile', null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Regular User: {self.user.username}"


class GuestProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, related_name='guest_profile', null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/%Y/%m/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Guest: {self.user.username}"

#  POST MODEL

class PostStatus(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    PUBLISHED = 'published', _('Published')
    ARCHIVED = 'archived', _('Archived')


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255,  blank=True)
    content = models.TextField()

    status = models.CharField(max_length=20, choices=PostStatus.choices, default=PostStatus.DRAFT, db_index=True)
    is_pinned = models.BooleanField(default=False)

    post_image = models.ImageField(upload_to='post_images/%Y/%m/', null=True, blank=True)
    post_video = models.FileField(upload_to='post_videos/%Y/%m/', null=True, blank=True)

    view_count = models.PositiveIntegerField(default=0, editable=False)
    published_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['author', 'status']),
        ]

    def __str__(self):
        author = self.author.username if self.author else "Unknown"
        return f'"{self.title}" by {author}'

    def publish(self):
        self.status = PostStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])

    def archive(self):
        self.status = PostStatus.ARCHIVED
        self.save(update_fields=['status', 'updated_at'])

    def increment_view(self):
        self.view_count += 1
        self.save(update_fields=['view_count'])

    @property
    def is_published(self):
        return self.status == PostStatus.PUBLISHED

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def short_content(self):
        return self.content[:150] + '...' if len(self.content) > 150 else self.content

#  COMMENT MODEL 

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, related_name='comments', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='comments', null=True, blank=True)
    parent = models.ForeignKey('self',on_delete=models.SET_NULL,related_name='replies',null=True,blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['author', '-created_at']),
        ]

    def __str__(self):
        author = self.author.username if self.author else "Unknown"
        post = self.post.title if self.post else "Unknown Post"
        return f'Comment by {author} on "{post}"'

    @property
    def is_reply(self):
        return self.parent is not None

    @property
    def reply_count(self):
        return self.replies.count()