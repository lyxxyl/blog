from django.shortcuts import render,redirect,HttpResponse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from geetest import GeetestLib
from django.http import JsonResponse
from django.forms import widgets,fields,Form
from  django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from app01 import models
from django.db.models import Count
from django.core import serializers
from bs4 import BeautifulSoup
from blog import settings
from django.db.models import F
import os
import datetime
import json

# Create your views here.


#geetest滑动验证码的id，key
pc_geetest_id = "b46d1900d0a894591916ea94ea91bd2c"
pc_geetest_key = "36fc3fe98530eea08dfc6ce76e3d24c4"

#登录页面处理
def login(request):
    if request.method == "POST":
        #存放状态码和错误信息，用于返回
        ret={}
        #运用geetest插件的参数
        gt = GeetestLib(pc_geetest_id, pc_geetest_key)
        challenge = request.POST.get(gt.FN_CHALLENGE, '')
        validate = request.POST.get(gt.FN_VALIDATE, '')
        seccode = request.POST.get(gt.FN_SECCODE, '')
        status = request.session[gt.GT_STATUS_SESSION_KEY]
        user_id = request.session["user_id"]
        if status:
            result = gt.success_validate(challenge, validate, seccode, user_id)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        username = request.POST.get("username")
        pwd = request.POST.get("password")
        #运用auth中间件检测user
        user = auth.authenticate(username=username, password=pwd)
        if result:
            if user:
                #当static为1，将url传过去，当static为0，传错误信息
                ret['static']=1
                #将user对象放入request中，可通过request.user获取登录用户信息
                auth.login(request, user)
                ret["msg"]="/index/"
            else:
                ret['static']=0
                ret["msg"]='用户名或密码错误'
        else:
            ret['static'] = 0
            ret["msg"] = '验证码错误'
        return JsonResponse(ret)
    return render(request,'login.html')

#blog主页面展示信息
def index(request):
    #获取所有文章信息，并展示，如果数据过多，可以分页展示
    article_list=models.Article.objects.all()
    return render(request,'index.html',{"article_list":article_list})

#auth中间件，处理注销功能
def logout(request):
    auth.logout(request)
    return redirect('/index/')

#geetest插件函数
def pcgetcaptcha(request):
    user_id = 'test'
    gt = GeetestLib(pc_geetest_id, pc_geetest_key)
    status = gt.pre_process(user_id)
    request.session[gt.GT_STATUS_SESSION_KEY] = status
    request.session["user_id"] = user_id
    response_str = gt.get_response_str()
    return HttpResponse(response_str)


#图片,文件上传处理
def upload(request):
    img_obj=request.FILES.get("imgFile")
    #在setting.py中配置media文件路径，用于存放头像，文件
    path=os.path.join(settings.MEDIA_ROOT,"add_article_img",img_obj.name)
    with open(path,"wb")as f:
        for line in img_obj:
            f.write(line)
    ret={
        "error":0,
        "url":"/media/add_article_img/"+img_obj.name
    }
    return HttpResponse(json.dumps(ret))



#用于注册功能，采用form组件
def register(request):
    if request.method=='POST':
        #将request中的数据放入RegForm对象
        regForm=RegForm(request.POST)
        img_obj=request.FILES.get("picture")
        #将图片保存到本地服务器
        url=settings.MEDIA_ROOT+"/picture/"+img_obj.name
        with open(url,'wb')as f:
            for line in img_obj.chunks():
                f.write(line)
        #对数据进行校验，没错误为True
        if regForm.is_valid():
            regForm.cleaned_data.pop("repassword")
            # **用于将map,dict逐个拆开
            models.UserInfo.objects.create_user(**regForm.cleaned_data,avatar='/picture/'+img_obj.name)
            return redirect('/index/')
        else:
            return render(request, "register.html", {"reg": regForm})
    #实例化Regform，生成表单
    regForm=RegForm()
    return render(request, "register.html", {"reg":regForm})
#arg1是url使用正则分组匹配产生的参数
def home(request,arg1):
    user, article_list, count_byCategory, count_byTag, count_byCreate=info_get(arg1)
    return render(request,'home.html',{"user":user,"article_list":article_list,"count_byCategory":count_byCategory,"count_byTag":count_byTag,"count_byCreate":count_byCreate})

#通过用户名获取数据
def info_get(arg1):
    user = models.UserInfo.objects.get(username=arg1)
    article_list = models.Article.objects.filter(user=user)
    #根据这篇blog所拥有的文章分类进行分组求和
    count_byCategory = models.Category.objects.filter(blog=user.blog).annotate(c=Count("article")).values("title", "c")
    #根据这篇blog所拥有的标签分类进行分组求和
    count_byTag = models.Tag.objects.filter(blog=user.blog).annotate(c=Count("article")).values("title", "c")
    #根据当前文章作者的所有文章创造时间的年，月进行分组求和
    count_byCreate = models.Article.objects.filter(user=user).extra(
        select={"archive_ym": "date_format(create_time,'%%Y-%%m')"}).values("archive_ym").annotate(
        c=Count("nid")).values("archive_ym", "c")
    return user,article_list,count_byCategory,count_byTag,count_byCreate

#文章详情
def articledetail(request,pk,username):
    article=models.Article.objects.filter(nid=pk).first()
    comment_list=models.Comment.objects.filter(article=article)
    user, article_list, count_byCategory, count_byTag, count_byCreate=info_get(username)
    return render(request,'article_detail.html',{"article":article,"user":user,"article_list":article_list,"count_byCategory":count_byCategory,"count_byTag":count_byTag,"count_byCreate":count_byCreate,"comment_list":comment_list})
#处理点赞，踩事件
def up_down(request):
    article_id=request.POST.get("num")
    article=models.Article.objects.get(nid=article_id)
    #将字符串转化为boolean
    is_up=json.loads(request.POST.get("is_up"))
    use=request.user
    result={}
    #如果用户第一次点击赞或踩，ArticleUpDown表中就可以创建数据，如果用户已点击，就会报错，用try/except处理异常
    try:
        models.ArticleUpDown.objects.create(user=use,is_up=is_up,article=article)
        if is_up:
            models.Article.objects.filter(nid=article_id).update(article_up=F("article_up")+1)
        else:
            models.Article.objects.filter(nid=article_id).update(article_down=F("article_down")+1)
        result.update({"static":1})
    except Exception:
        temp=models.ArticleUpDown.objects.get(article=article,user=use).is_up
        result.update({"static":0,"is_up":temp})
    return JsonResponse(result)
#处理提交的comment数据，如果在数据库新增一条记录
def comment(request):
    article_id=request.POST.get("article_id")
    content=request.POST.get("content")
    user=request.user
    parent=request.POST.get("parent")
    if parent:
        parent=int(request.POST.get("parent"))
    if not parent:
        models.Comment.objects.create(article_id=article_id,content=content,user=user)
    else:
        content=content.split("\n")[1]
        obj=models.Comment.objects.get(nid=parent)
        models.Comment.objects.create(article_id=article_id, content=content, user=user,parent_comment=obj)
    return HttpResponse("")
#新增文章
def article_add(request):
    if request.method=="POST":
        content=request.POST.get("article_content")
        bs=BeautifulSoup(content,"html.parser")
        #运用BeautifulSoup提取文字，以前150个为文章描述
        desc=bs.text[0:150]
        title=request.POST.get("title")
        user=request.user
        #预防xss注入，将所有的<script>标签删除
        for tag in bs.find_all():
            if tag.name in ["script"]:
                tag.decompose()
        content=str(bs)
        obj=models.Article.objects.create(title=title,user=user,desc=desc)
        models.ArticleDetail.objects.create(content=content,article=obj)
        return redirect("/index/")
    return render(request,'article_add.html')
#form组件类，用于生成form表单
class RegForm(Form):
    username=fields.CharField(
        max_length=16,
        label="用户名",
        required=True,
        error_messages={
            "max_length":"长度不能超过16",
            "required":"不能为空"
        },
        widget=widgets.TextInput(
            attrs={
                "class":"form-control",
            }
        )
    )
    password=fields.CharField(
        min_length=6,
        required=True,
        label="密码",
        error_messages={
            "min_length": "长度不能低于6",
            "required": "不能为空"
        },
        widget=widgets.PasswordInput(
            attrs={
                "class": "form-control",
            }
        )

    )
    repassword=fields.CharField(
        min_length=6,
        required=True,
        label="确认密码",
        error_messages={
            "min_length": "长度不能低于6",
            "required": "不能为空"
        },
        widget=widgets.PasswordInput(
            attrs={
                "class": "form-control",
            }
        )

    )
    email=fields.EmailField(
        required=True,
        label="邮箱",
        error_messages={
            "invalid":"邮箱格式错误",
            "required": "不能为空"
        },
        widget=widgets.EmailInput(
            attrs={
                "class": "form-control",
            }
        )
    )
    #使用form组件源码的钩子，用于判断用户名是否存在
    def clean_username(self):
        username=self.cleaned_data.get("username")
        ret=models.UserInfo.objects.filter(username=username)
        if ret:
            self.add_error("username",ValidationError("用户名已存在"))
        else:
            return username
    #用于判断邮箱是否存在
    def clean_email(self):
        email=self.cleaned_data.get("email")
        ret=models.UserInfo.objects.filter(email=email)
        if ret:
            self.add_error("email",ValidationError("邮箱已存在"))
        else:
            return email

    #用于判断密码是否一致是否存在
    def clean(self):
        password = self.cleaned_data.get("password")
        repassword = self.cleaned_data.get("repassword")
        if repassword and repassword != password:
            self.add_error("repassword", ValidationError("两次密码不一致"))
        else:
            return self.cleaned_data









