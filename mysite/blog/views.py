from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, login
from django.utils import timezone
from .models import Post, Comment
from .forms import PostForm, CommentForm, SignupForm
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from multiprocessing import Process
import logging
import configparser


config = configparser.ConfigParser()
config.read('cnf.ini')
logging.basicConfig(
    level=config['LOGGING']['level'],
    filename=config['LOGGING']['filename']
)
log = logging.getLogger(__name__)

def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

@login_required
def my_posts(request):
    posts = Post.objects.filter(author=request.user).order_by('author')
    return render(request, 'blog/my_posts.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return render(request, 'blog/post_detail.html', {'post': post})

@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            p = Process(target=log.info(f'{request.user} added a post {post.title}'))
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            p = Process(target=log.info(f'{request.user} edited a post {post.title}'))
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by('created_date')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})

@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    p = Process(target=log.info(f'{request.user} publish a post {post.title}'))
    return redirect('post_detail', pk=pk)

@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    p = Process(target=log.info(f'{request.user} removed a post {post.title}'))
    return redirect('post_list')

def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            p = Process(target=log.info(f'{comment.author} added a comment to {comment.post}'))
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form})

@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    p = Process(target=log.info(f'{request.user} approved a {comment.author}s comment'))
    return redirect('post_detail', pk=comment.post.pk)

@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    p = Process(target=log.info(f'{request.user} removed a {comment.author}s comment'))
    return redirect('post_detail', pk=comment.post.pk)

def register_user(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            p = Process(target=log.info(f'{request.user} registred'))
            form.save()
            return redirect('login')
    else:
        form = SignupForm(request.POST)
    return render(
        request,
        'registration/registration.html',
        {'form': form}
    )

def login_user(request):
    if request.user.is_authenticated:
        return redirect('post_list')
    if request.method == 'POST':
        form = AuthenticationForm(request, request.POST)
        print("form: ", form.data)
        print('post: ', request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                return redirect('post_list')
    else:
        form = AuthenticationForm()
    return render(
        request,
        'registration/login.html',
        {'form': form}
    )

@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')