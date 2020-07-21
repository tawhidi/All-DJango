from django.shortcuts import render, get_object_or_404
from django.contrib.postgres.search import SearchVector,SearchQuery,SearchRank
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger  # for function based view use
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm, SearchForm
from django.core.mail import send_mail
from taggit.models import Tag
from django.db.models import Count


# class based views
# class PostList(ListView):
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/list.html'
#


def post_share(request, post_id):
    # retrieve / get post by id
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == "POST":
        # Form was submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed validation
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}{cd['name']}'s comments {cd['comments']}"
            send_mail(subject, message, 'tawhidi.pro@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/share.html', {'form': form, 'post': post, 'sent': sent})


# Function based view
def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)  # 3 post in each page
    page = request.GET.get('page')  # indicates the current page number
    try:
        posts = paginator.page(page)  # obtaining the objects for the desired page by calling the page()
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    template_name = 'blog/list.html'
    context = {
        'posts': posts,
        'page': page,
        'tag': tag
    }

    return render(request, template_name, context)


def post_details(request, post, year, month, day):
    post = get_object_or_404(Post, slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day
                             )
    # List of active comments for this post
    comments = post.comments.filter(active=True)
    new_comment = None
    if request.method == 'POST':
        # Comment was posted
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Create Comment object but don't save to database yet
            new_comment = comment_form.save(commit=False)
            # Assign the current post to the comment
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()

    # List of similar posts
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    template_name = 'blog/detail.html'
    context = {
        'post': post,
        'comments': comments,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'similar_posts': similar_posts
    }
    return render(request, template_name, context)


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('title',weight='A') + SearchVector('body',weight='B')
            search_query = SearchQuery(query)
            results = Post.published.annotate(search=search_vector,rank=SearchRank(search_vector,search_query)
                                              ).filter(rank__gte=0.3).order_by('-rank')
    template_name = 'blog/search.html'
    context = {
        'form': form,
        'query': query,
        'results': results
    }

    return render(request, template_name, context)
