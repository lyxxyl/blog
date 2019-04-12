from django import template

register=template.Library()


@register.inclusion_tag('tag.html')
def func(*args):
    data={"nid":args[0],"create_time":args[1],"prent":args[2],"content":args[3]}
    return data