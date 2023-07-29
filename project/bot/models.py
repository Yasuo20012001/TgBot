from django.db import models
from django.utils import formats


class Question(models.Model):
    q = models.CharField('Вопрос', max_length=300)
    a = models.CharField('Ответ', max_length=300)

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Часто задаваемые вопросы'

    def __str__(self):
        return self.q


class Category(models.Model):
    name = models.CharField('Наименование категории', max_length=100)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    name = models.CharField('Наименование подкатегории', max_length=100)
    category = models.ForeignKey(
        Category, verbose_name='Категория', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'

    def __str__(self):
        return f'{self.category.name}, {self.name}'


class Product(models.Model):
    name = models.CharField('Наименование товара', max_length=100)
    subcategory = models.ForeignKey(Subcategory, verbose_name='Подкатегория',
                                    on_delete=models.CASCADE)
    image = models.ImageField('Фотография', null=True, blank=True)
    description = models.CharField('Описание товара', max_length=300)
    price = models.FloatField('Стоимпость (руб.)')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f'''{self.name} ({self.subcategory.name},
        {self.subcategory.category.name})'''


class Client(models.Model):
    full_name = models.CharField('Имя', max_length=150, blank=True, null=True)

    address = models.CharField('Адрес', max_length=150, blank=True, null=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f'ID {self.id}'


class CartProduct(models.Model):
    client = models.ForeignKey(
        Client, verbose_name='Клиент', on_delete=models.CASCADE)
    product = models.ForeignKey(
        Product, verbose_name='Товар', on_delete=models.CASCADE)
    quantity = models.IntegerField('Количество')
    added = models.DateTimeField(auto_now_add=True)
    total = models.FloatField('Общая стоимость товара', default=0)

    class Meta:
        verbose_name = 'Товар корзины'
        verbose_name_plural = 'Товары корзины'

    def __str__(self):
        return f'{self.client.id}, {self.product.name}'

    def sum(self):
        return self.product.price * self.quantity


class Order(models.Model):

    class Status(models.TextChoices):
        YES = 'YES', 'Оплачено'
        NO = 'NO', 'Не оплачено!'

    client = models.ForeignKey(Client,
                               verbose_name='Клиент',
                               on_delete=models.PROTECT)
    address = models.CharField('Адрес', max_length=150, blank=True, null=True)

    pay_status = models.CharField('Статус оплаты', max_length=100,
                                  choices=Status.choices, default=Status.NO)
    creation_date = models.DateTimeField('Дата создания', auto_now_add=True)
    total_amount = models.FloatField('Сумма', default=0)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        date = formats.date_format(self.creation_date, "d.m.Y")
        return f'Заказ клиента {self.client.id} от {date}'


class OrderProduct(models.Model):
    order = models.ForeignKey(Order,
                              verbose_name='Заказ',
                              on_delete=models.CASCADE)
    product = models.ForeignKey(Product,
                                verbose_name='Товар',
                                on_delete=models.PROTECT)
    quantity = models.IntegerField('Количество')
    total = models.FloatField('Общая стоимость товара', default=0)

    class Meta:
        verbose_name = 'Заказанный товар'
        verbose_name_plural = 'Заказанные товары'
