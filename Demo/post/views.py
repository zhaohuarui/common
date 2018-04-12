from math import ceil

from django.shortcuts import render, redirect

from common import rds
from common import keys
from post.models import Post
from post.helper import page_cache
from post.helper import get_top_n


def post_list(request):
    page = int(request.GET.get('page', 0)) or 1  # 当前页数
    total = Post.objects.count()              # 文章总数
    pages = ceil(total / 10)                  # 总页数

    start = (page - 1) * 10
    end = start + 10
    posts = Post.objects.all().order_by('-create')[start:end]

    return render(request, 'post_list.html', {'posts': posts, 'pages': range(1, pages + 1)})


def create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        post = Post.objects.create(title=title, content=content)
        return redirect('/post/read/?post_id=%s' % post.id)

    return render(request, 'create.html')


# @page_cache(1)
def read(request):
    post_id = int(request.GET.get('post_id'))
    try:
        post = Post.objects.get(id=post_id)   # 缓存没有取到时，从数据库获取一次
        rds.zincrby(keys.READ_RANK, post.id)  # 增加阅读计数
    except Post.DoseNotExist as e:
        return redirect('/')

    return render(request, 'read.html', {'post': post})


def edit(request):
    if request.method == 'POST':
        post_id = int(request.POST.get('post_id'))
        post = Post.objects.get(id=post_id)

        post.title = request.POST.get('title', '')
        post.content = request.POST.get('content', '')
        post.save()
        return redirect('/post/read/?post_id=%s' % post.id)
    else:
        post_id = int(request.GET.get('post_id'))
        post = Post.objects.get(id=post_id)
        return render(request, 'edit.html', {'post': post})


def search(request):
    keyword = request.POST.get('keyword', '')
    posts = Post.objects.filter(content__contains=keyword)
    return render(request, 'search.html', {'posts': posts})


def top10(request):
    # [
    #     (post1, 100),
    #     (post2, 99),
    #     (post3, 90),
    # ]
    rank_data = get_top_n(10)
    return render(request, 'top10.html', {'rank_data': rank_data})
