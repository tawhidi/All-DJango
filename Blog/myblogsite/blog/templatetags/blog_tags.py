import re
from django import template
from ..models import Post
from django.db.models import Count
from django.utils.safestring import mark_safe
import markdown

register = template.Library()


@register.simple_tag
def total_posts():
    return str(Post.published.count()) + "\n"


@register.inclusion_tag('blog/latest_posts.html')
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    template_context = {
        'latest_posts': latest_posts
    }
    return template_context


@register.simple_tag
def get_most_commented_post(count=5):
    commented_post = Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]
    return commented_post


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))



