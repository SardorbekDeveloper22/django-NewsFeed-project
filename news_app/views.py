from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, UpdateView, DeleteView, CreateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from hitcount.utils import get_hitcount_model
from hitcount.views import HitCountMixin
from django.urls import reverse
# from django.views import View

from django.shortcuts import redirect
from .models import News, Category
from .forms import ContactForm, CommentForm
from news_project.custom_permissions import OnlyLoggedSuperUser


def news_list(request):
    # news_list = News.objects.filter(status=News.Status.Published)
    news_list = News.published.all()
    context = {
        "news_list": news_list
    }
    return render(request, "news/news_list.html", context)


def news_detail(request, news):
    news = get_object_or_404(News, slug=news, status=News.Status.Published)
    context = {}
    #hitcount logic
    hit_count = get_hitcount_model().objects.get_for_object(news)
    hits = hit_count.hits
    hitcontext = context['hitcount'] = {'pk': hit_count.pk}
    hit_count_response = HitCountMixin.hit_count(request, hit_count)
    if hit_count_response.hit_counted:
        hits = hits + 1
        hitcontext['hit_counted'] = hit_count_response.hit_counted
        hitcontext['hit_message'] = hit_count_response.hit_message
        hitcontext['total_hits'] = hits

    comments = news.comments.filter(active=True)
    comment_count = comments.count()
    new_comment = None

    if request.method == "POST":
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            #yangi komment obyektini yaratamiz lekin DB ga saqlamaymiz
            new_comment = comment_form.save(commit=False)
            new_comment.news = news
            #izoh egasini so'rov yuborayotgan userga bog'ladik
            new_comment.user = request.user
            # ma'lumotlar bazasiga saqlaymiz
            new_comment.save()
            comment_form = CommentForm()
    else:
        comment_form = CommentForm()
    sport_xabarlari = News.published.all().filter(category__name="Sport").order_by("-publish_time")[:5]
    news_list = News.published.all().order_by('-publish_time')[:4]
    context = {
        "news": news,
        'comments': comments,
        'comment_count': comment_count,
        'new_comment': new_comment,
        'comment_form': comment_form,
        'sport_xabarlari':sport_xabarlari,
        'news_list':news_list
    }

    return render(request, 'news/news_detail.html', context)


def homePageView(request):
    categories = Category.objects.all()
    news_list = News.published.all().order_by('-publish_time')[:15]
    local_one = News.published.filter(category__name="Mahalliy").order_by("-publish_time")[:1]
    local_news = News.published.all().filter(category__name="Mahalliy").order_by("-publish_time")[1:6]

    context = {
        'news_list': news_list,
        "categories": categories,
        'local_one': local_one,
        "local_news": local_news
    }

    return render(request, 'news/home.html', context)


class HomePageView(ListView):
    model = News
    template_name = 'news/home.html'
    context_object_name = 'news'

    def get_context_data(self, ** kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['news_list'] = News.published.all().order_by('-publish_time')[:4]
        context['mahalliy_xabarlar'] = News.published.all().filter(category__name="Mahalliy").order_by("-publish_time")[:5]
        context['xorij_xabalari'] = News.published.all().filter(category__name="Xorij").order_by("-publish_time")[:5]
        context['sport_xabarlari'] = News.published.all().filter(category__name="Sport").order_by("-publish_time")[:5]
        context['texnologiya_xabarlari'] = News.published.all().filter(category__name="Texnologiya").order_by("-publish_time")[:5]

        return context


class ContactPageView(TemplateView):
    template_name = 'news/contact.html'

    def get(self, request, *args, **kwargs):
        news_list = News.published.all().order_by('-publish_time')[:5]
        form = ContactForm()
        context = {
            'form': form,
            'news_list':news_list
        }
        return render(request, 'news/contact.html', context)

    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if request.method == 'POST' and form.is_valid():
            form.save()
            return HttpResponse("<h2> Biz bilan bog'langaningiz uchun tashakkur</h2>")
        news_list = News.published.all().order_by('-publish_time')[:5]
        context = {
            "form": form,
            'news_list':news_list
        }

        return render(request, 'news/contact.html', context)


class LocalNewsView(View):
    def get(self,request):
        news_list = News.published.all().filter(category__name="Mahalliy").order_by('-publish_time')
        paginator = Paginator(news_list, 8) # her sayfada 10 öğe
        page_number = request.GET.get('page')
        news_list = paginator.get_page(page_number)



        # page_size = request.GET.get('page_size', 4)
        # paginator = Paginator(news_list, page_size)

        # page_num = request.GET.get('page', 1)
        # page_obj = paginator.get_page(page_num)

        return render(
            request,
            "news/mahalliy.html",
            {"news_list": news_list,}
        )


class ForeignNewsView(ListView):
    def get(self,request):
        xorij_yangiliklari = News.published.all().filter(category__name="Xorij").order_by('-publish_time')
        paginator = Paginator(xorij_yangiliklari, 8) # her sayfada 10 öğe
        page_number = request.GET.get('page')
        xorij_yangiliklari = paginator.get_page(page_number)



        # page_size = request.GET.get('page_size', 4)
        # paginator = Paginator(xorij_yangiliklari, page_size)

        # page_num = request.GET.get('page', 1)
        # page_obj = paginator.get_page(page_num)

        return render(
            request,
            "news/xorij.html",
            {"xorij_yangiliklari": xorij_yangiliklari,}
        )


class TechnologyNewsView(ListView):
    def get(self,request):
        texnoligik_yangiliklar = News.published.all().filter(category__name="Texnologiya").order_by('-publish_time')
        paginator = Paginator(texnoligik_yangiliklar, 8) # her sayfada 10 öğe
        page_number = request.GET.get('page')
        texnoligik_yangiliklar = paginator.get_page(page_number)


        return render(
            request,
            "news/texnologiya.html",
            {"texnoligik_yangiliklar": texnoligik_yangiliklar,}
        )

class SportNewsView(ListView):
    def get(self,request):
        sport_yangiliklari = News.published.all().filter(category__name="Sport").order_by('-publish_time')
        paginator = Paginator(sport_yangiliklari, 8) # her sayfada 10 öğe
        page_number = request.GET.get('page')
        sport_yangiliklari = paginator.get_page(page_number)


        return render(
            request,
            "news/sport.html",
            {"sport_yangiliklari": sport_yangiliklari,}
        )


class NewsUpdateView(OnlyLoggedSuperUser, UpdateView):
    model = News
    fields = ('title', 'body', 'image', 'category', 'status', )
    template_name = 'crud/news_edit.html'


class NewsDeleteView(OnlyLoggedSuperUser, DeleteView):
    model = News
    template_name = 'crud/news_delete.html'
    success_url = reverse_lazy('home_page')


# from googletrans import Translator

# # translator obyekti yaratish
# translator = Translator()

class NewsCreateView(OnlyLoggedSuperUser, CreateView):
    model = News
    template_name = 'crud/news_create.html'
    fields = ('title', 'title_uz', 'title_en', 'title_ru','slug',
             'body', 'body_uz', 'body_en',
              'body_ru', 'image', 'category', 'status')


    # def form_valid(self, form):
    #     # formdan malumotlarni olish
    #     # form.instance.author = self.request.user
    #     # form.instance.language = 'uz'

    #     news = form.save(commit=False)
    #     news.author = self.request.user
    #     news.save()

    #     # Tarjima qilish
    #     for field_name in form.cleaned_data:
    #         field_value = form.cleaned_data[field_name]
    #         if field_value and field_name in ['title_uz', 'title_en', 'title_ru', 'body_uz', 'body_en', 'body_ru']:
    #             translated_value = translator.translate(field_value, dest='uz').text
    #             setattr(form.instance, field_name, translated_value)
    #     return super().form_valid(form)



@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_page_view(request):
    admin_users = User.objects.filter(is_superuser=True)
    paginator = Paginator(admin_users, 20) # her sayfada 10 öğe
    page_number = request.GET.get('page')
    admin_users = paginator.get_page(page_number)

    context = {
        'admin_users': admin_users
    }
    return render(request, 'pages/admin_page.html', context)


class SearchResultsList(View):
    def get(self, request):
        search_query = self.request.GET.get('q')
        if search_query:
            model=News.objects.filter(Q(title__icontains=search_query) | Q(body__icontains=search_query))
            paginator = Paginator(model, 8) # her sayfada 10 öğe
            page_number = request.GET.get('page')
            model = paginator.get_page(page_number)


            context = {
            'barcha_yangiliklar': model,
            'search_query':search_query,
            }

            return render(request, 'news/search_result.html', context)
        else:
            return redirect(reverse("home_page"))