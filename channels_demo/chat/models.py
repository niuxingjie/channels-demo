from cProfile import label
from pyexpat import model
from django.contrib.auth.models import AbstractUser
from django.db import models


class Org(models.Model):
    """
    考虑一个用户可以拥有多个组织的情况
    """
    name = models.CharField(
        verbose_name="组织名称",
        max_length=125,
    )

    class Meta:
        db_table = 'channels_demo_org'


class Speaker(AbstractUser):
    """
    用户
    """
    phone = models.CharField(
        verbose_name="手机号",
        max_length=30,
    )
    orgs = models.ManyToManyField(Org, related_name="speakers", related_query_name="speakers_orgs", verbose_name="所属组织")

    class Meta:
        db_table = 'channels_demo_speaker'


class Bulletin(models.Model):
    """
    公告消息
    """
    content = models.TextField(verbose_name="内容", default="")
    title = models.CharField(max_length=64, verbose_name="标题")

    class Meta:
        db_table = 'channels_demo_bulletin'


class Message(models.Model):
    """
    用户消息
    """
    # 接收
    receiver = models.ForeignKey(Speaker, verbose_name="接收人", on_delete=models.DO_NOTHING)
    org = models.ForeignKey(Org, verbose_name="所属组织", on_delete=models.DO_NOTHING)
    receive_at = models.DateTimeField(auto_now_add=True, verbose_name="接收时间")

    # 内容
    bulletin = models.ForeignKey(Bulletin, null=True, blank=True, verbose_name="公告", on_delete=models.DO_NOTHING)
    content = models.TextField(verbose_name="内容", default="")
    title = models.CharField(max_length=64, default="", verbose_name="标题")
    
    # 状态
    is_read = models.BooleanField(default=False, verbose_name="已读")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="阅读时间")

    class Meta:
        db_table = 'channels_demo_message'



