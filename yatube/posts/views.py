from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User
from .utils import get_page_context


@cache_page(20, key_prefix='index_page')
def index(request):
    """Главная страница."""
    posts_list = Post.objects.select_related('author', 'group').all()
    page_obj = get_page_context(posts_list, request)
    context = {'page_obj': page_obj}

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница сообществ."""
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.select_related('author', 'group')
    page_obj = get_page_context(posts_list, request)
    context = {
        'group': group,
        'page_obj': page_obj
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница профиля пользователя."""
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.select_related('author', 'group')
    page_obj = get_page_context(posts_list, request)
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }

    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница просмотра записей."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'), pk=post_id
    )
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание новых записей."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    context = {'form': form}
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)

    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    """Редактирование записей."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'), pk=post_id,
    )
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }

    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    """Создание комментариев."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'), pk=post_id,
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    """Посты авторов."""
    posts_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    page_obj = get_page_context(posts_list, request)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
