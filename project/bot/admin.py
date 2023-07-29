from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ActionForm

from .models import (CartProduct, Category, Client, Order, OrderProduct,
                     Product, Question, Subcategory)
# Register your models here.
from .mybot import mailing

admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Product)


@admin.action(description='Рассылка')
def my_action(modeladmin, request, queryset):
    form = None
    print(request.POST)
    if request.POST:

        text = request.POST['text']

        mailing(text, queryset)

        modeladmin.message_user(request, 'Рассылка выполнена')
        return None

    if not form:
        form = MyActionForm()

    return {
        'form': form,
        'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
    }


class MyActionForm(ActionForm):
    text = forms.CharField(
        label='Текст для рассылки',
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 70})
    )


class ClientAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'address']
    actions = [my_action]
    action_form = MyActionForm


admin.site.register(Client, ClientAdmin)
admin.site.register(CartProduct)
admin.site.register(Question)


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1


class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderProductInline]

    def has_change_permission(self, request, obj=None):
        return False


admin.site.register(Order, OrderAdmin)
