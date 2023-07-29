import pandas as pd
import telebot
from django.conf import settings
from django.db.models import Sum
from telebot import types

from .models import (CartProduct, Category, Client, Order, OrderProduct,
                     Product, Question, Subcategory)

bot = telebot.TeleBot(settings.TG_TOKEN)


def save_order(order_id, filename='orders.xlsx'):
    '''Дополняет эксель записью о заказе'''
    order = Order.objects.get(id=order_id)
    try:
        existing_data = pd.read_excel(filename)
    except FileNotFoundError:
        existing_data = pd.DataFrame()

    data = {
        'ID клиента': [],
        'Адрес': [],
        'Товар': [],
        'Количество': [],
        'Общая стоимость': []
    }

    for order_product in order.orderproduct_set.all():
        data['ID клиента'].append(order.client.id)
        data['Адрес'].append(order.client.address)
        data['Товар'].append(order_product.product.name)
        data['Количество'].append(order_product.quantity)
        data['Общая стоимость'].append(order_product.total)

    df = pd.DataFrame(data)
    df = pd.concat([existing_data, df], ignore_index=True)
    df.to_excel(filename, index=False)


def mailing(text, users):
    '''Рассылает указанного текста выбранным клиентам'''
    for u in users:
        try:
            bot.send_message(u.id, text, parse_mode='html')
        except Exception as e:
            print(e)


def check_sub(user_id):
    '''Проверяет подписки на каналы'''
    markup = types.InlineKeyboardMarkup()

    for c in settings.TG_CHANNELS:
        if bot.get_chat_member(chat_id=c['id'],
                               user_id=user_id).status == 'left':
            b = types.InlineKeyboardButton(text=c['name'], url=c['url'])
            markup.add(b)

    if len(markup.to_dict()['inline_keyboard']):
        markup.add(types.InlineKeyboardButton(
            '🔄 Проверить подписку',
            callback_data='check'
        ))

        bot.send_message(user_id,
                         'Сначала подпишись на наши каналы',
                         reply_markup=markup)
        return False
    else:
        return True


def send_main_menu(user_id):
    '''Отправляет клавиатуру с главным меню'''
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Каталог')
    btn2 = types.KeyboardButton('Моя корзина')
    markup.add(btn1, btn2)
    bot.send_message(user_id, text='Открыто главное меню', reply_markup=markup)


def show_cats(user_id, count, page):
    '''
    Получает категории по количеству и индексу страницы (для пагинации).
    Результат отправляет пользователю.
    '''
    cats = Category.objects.all()
    total_count = cats.count()
    if total_count == 0:
        return None
    cats = cats[count*page:count*(page+1)]
    markup = types.InlineKeyboardMarkup()

    for c in cats:
        markup.add(types.InlineKeyboardButton(
            c.name, callback_data=f'subcats_{c.id}_{count}_0'))

    btns_page = []
    if page > 0:
        btns_page.append(types.InlineKeyboardButton(
                '<< пред. стр.',
                callback_data=f'cats_{count}_{page-1}'
        ))
    if total_count > count:
        btns_page.append(types.InlineKeyboardButton(
                f'{page+1}/{(total_count + count - 1) // count}',
                callback_data=f'cats_{count}_{page}'
        ))

    if count*(page+1) < total_count:
        btns_page.append(types.InlineKeyboardButton(
            'след. стр. >>',  callback_data=f'cats_{count}_{page+1}'))

    markup.row(*btns_page)
    bot.send_message(user_id, 'Выберите категорию', reply_markup=markup)


def show_subcats(user_id, cat_id, count, page):
    '''
    Получает подкатегории по количеству и индексу страницы (для пагинации).
    Результат отправляет пользователю.
    '''
    subcats = Subcategory.objects.filter(category__id=cat_id)
    total_count = subcats.count()

    subcats = subcats[count*page:count*(page+1)]
    markup = types.InlineKeyboardMarkup()

    for s in subcats:
        markup.add(types.InlineKeyboardButton(
            s.name, callback_data=f'products_{s.id}_3_0'))

    btns_page = []
    if page > 0:
        btns_page.append(types.InlineKeyboardButton(
                '<< пред. стр.',
                callback_data=f'subcats_{cat_id}_{count}_{page-1}'
        ))
    if total_count > count:
        btns_page.append(types.InlineKeyboardButton(
                            f'{page+1}/{(total_count + count - 1) // count}',
                            callback_data=f'subcats_{cat_id}_{count}_{page}'
        ))

    if count*(page+1) < total_count:
        btns_page.append(types.InlineKeyboardButton(
                'след. стр. >>',
                callback_data=f'subcats_{cat_id}_{count}_{page+1}'
        ))

    markup.row(*btns_page)
    markup.add(types.InlineKeyboardButton(
                'Вернуться к категориям',
                callback_data=f'cats_{count}_0'
    ))

    bot.send_message(user_id, 'Выберите подкатегорию', reply_markup=markup)


def show_products(user_id, subcat_id, count, page):
    '''
    Получает товары по количеству и индексу страницы (для пагинации).
    Результат отправляет пользователю.
    '''
    products = Product.objects.filter(subcategory__id=subcat_id)
    total_count = products.count()
    if total_count == 0:
        show_cats(user_id, 4, 0)
        return

    products = products[count*page:count*(page+1)]

    rms = []

    for p in products:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            'Добавить в корзину', callback_data=f'cart_add_{p.id}'))
        rms.append(markup)

    markup = rms[-1]
    btns_page = []
    if page > 0:
        btns_page.append(types.InlineKeyboardButton(
                '<< пред. стр.',
                callback_data=f'products_{subcat_id}_{count}_{page-1}'
        ))
    if total_count > count:
        btns_page.append(
            types.InlineKeyboardButton(
                f'{page+1}/{(total_count + count - 1) // count}',
                callback_data=f'products_{subcat_id}_{count}_{page}'
            )
        )

    if count*(page+1) < total_count:
        btns_page.append(types.InlineKeyboardButton(
                    'след. стр. >>',
                    callback_data=f'products_{subcat_id}_{count}_{page+1}'
                ))

    markup.row(*btns_page)
    markup.add(
        types.InlineKeyboardButton(
            'Вернуться к подкатегориям',
            callback_data=f'subcats_{products[0].subcategory.category.id}_4_0'
        )
    )

    for i, p in enumerate(products):
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
                    'Добавить в корзину',
                    callback_data=f'cart_add_{p.id}'
        ))
        bot.send_photo(
            chat_id=user_id,
            photo=p.image,
            caption=f'''<b>{p.name} - {p.price:.2f} руб.</b>
                        \n\n{p.description}''',
            parse_mode='HTML',
            reply_markup=rms[i]
        )


def ask_quantity(user_id, product_id):
    '''Отправляет сообщение с запросом количества выбранного товара'''
    product = Product.objects.filter(id=product_id).first()

    markup = types.InlineKeyboardMarkup()

    r1 = []
    r2 = []
    for i in range(1, 6):
        r1.append(types.InlineKeyboardButton(
                    f'{i}',
                    callback_data=f'cart_add_q_{product_id}_{i}'
        ))

    for i in range(6, 11):
        r2.append(types.InlineKeyboardButton(
                    f'{i}',
                    callback_data=f'cart_add_q_{product_id}_{i}'
        ))

    markup.row(*r1)
    markup.row(*r2)

    bot.send_photo(
        chat_id=user_id,
        photo=product.image,
        caption=f'''<b>{product.name} - {product.price:.2f} руб.</b>
                    \n{product.description}
                    \n\n<b>Укажите количество товара для покупки</b>''',
        parse_mode='HTML',
        reply_markup=markup
        )


def ask_confirm(user_id, product_id, quantity):
    '''Отравляет запрос о подтверждении добавления в корзину'''
    product = Product.objects.filter(id=product_id).first()

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('Да, добавить в корзину',
               callback_data=f'cart_confirm_add_{product_id}_{quantity}'))
    markup.add(types.InlineKeyboardButton(
        'Отменить', callback_data='cats_4_0'))

    bot.send_photo(
        chat_id=user_id,
        photo=product.image,
        caption=f'''<b>{product.name} - {product.price:.2f} руб.
                    \nКоличество: {quantity}\nОбщая стоимость:
                    {quantity*product.price:.2f}</b>\n{product.description}
                    \n\n<b>Подтвердите добавление товара в корзину</b>''',
        parse_mode='HTML', reply_markup=markup)


def cart_add(user_id, product_id, quantity):
    '''Добавление в корзину'''
    p = Product.objects.get(id=product_id)
    cartp = CartProduct.objects.filter(
        client_id=user_id, product_id=product_id).first()
    if cartp:
        cartp.quantity = quantity
        cartp.total = quantity * p.price
        cartp.save()
        bot.send_message(user_id, 'Количество товара в корзине изменено')
    else:
        CartProduct.objects.create(
            client_id=user_id,
            product_id=product_id,
            quantity=quantity,
            total=quantity*p.price
        )
        bot.send_message(user_id, 'Товар добавлен в корзину')


def cart_show(user_id, count, page):
    '''
    Выводит пользователю корзину.
    count и page, аналогично выводу категорий, для пагинации кнопок удаления
    '''
    all_cproducts = CartProduct.objects.filter(client_id=user_id)
    if not all_cproducts:
        bot.send_message(user_id, 'Корзина пуста')
        return
    total_count = all_cproducts.count()
    cproducts = all_cproducts[count*page:count*(page+1)]

    rms = []
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('💳 Оплатить',
                                          callback_data='cart_buy'))

    for p in cproducts:
        markup.add(types.InlineKeyboardButton(
            f'❌ {p.product.name}',
            callback_data=f'cart_del_{p.product.id}'
        ))
        rms.append(markup)

    btns_page = []
    if page > 0:
        btns_page.append(types.InlineKeyboardButton(
            '<< пред. стр.', callback_data=f'cart_show_{count}_{page-1}'))
    if total_count > count:
        btns_page.append(types.InlineKeyboardButton(
            f'{page+1}/{(total_count + count - 1) // count}',
            callback_data=f'cart_show_{count}_{page}')
        )

    if count*(page+1) < total_count:
        btns_page.append(types.InlineKeyboardButton(
            'след. стр. >>',  callback_data=f'cart_show_{count}_{page+1}'))

    markup.row(*btns_page)

    text = ''
    for p in all_cproducts:
        text += f'{p.product.name} ({p.quantity} шт.) - {p.total:.2f} руб.\n'

    total_sum = all_cproducts.aggregate(Sum('total'))['total__sum']
    text += f'\n<B>Общая сумма: {total_sum:.2f} руб.</B>'

    bot.send_message(user_id, text, parse_mode='HTML', reply_markup=markup)


def cart_del(user_id, product_id):
    '''Удаление товара из корзины'''
    CartProduct.objects.filter(
        client_id=user_id, product_id=product_id).delete()


def handle_address(message):
    '''Отправляет запрос о подтверждении адреса'''
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton(
        'Верно', callback_data=f'confirm_address_{message.text}'))
    markup.add(types.InlineKeyboardButton(
        'Нет, изменить', callback_data='cart_buy'))

    markup.add(types.InlineKeyboardButton('Вернуться назад',
                                          callback_data='cart_show_5_0'))
    bot.send_message(
        message.chat.id,
        f'Ваш адрес: {message.text}\n\nВсе верно?',
        reply_markup=markup
    )


def save_address(user_id, address):
    '''Сохраняет адрес'''
    user = Client.objects.get(id=user_id)
    user.address = address
    user.save()


def send_invoice(user_id):
    '''Отправляет  счет'''
    all_cproducts = CartProduct.objects.filter(client_id=user_id)
    if not all_cproducts:
        bot.send_message(user_id, 'Корзина пуста')
        return

    text = ''
    order = Order.objects.create(
        client_id=user_id,
        address=Client.objects.get(id=user_id).address
    )
    for p in all_cproducts:
        OrderProduct.objects.create(
            order=order,
            product=p.product,
            quantity=p.quantity,
            total=p.total
        )

        text += f'{p.product.name} ({p.quantity} шт.) - {p.total:.2f} руб.\n'

    total_sum = all_cproducts.aggregate(Sum('total'))['total__sum']

    order.total_amount = total_sum
    order.save()

    text += f'\nОбщая сумма: {total_sum:.2f} руб.'

    bot.send_invoice(
        user_id,
        title='Оплата',
        description=text,
        provider_token=settings.YK_TOKEN,
        currency='rub',
        is_flexible=False,
        prices=[types.LabeledPrice(
            label='Общая сумма',
            amount=int(total_sum * 100)
        )],
        invoice_payload=str(order.id),
        start_parameter='example'
    )


def get_faq(query):
    '''Получет вопросы по их началу и формирует список для inline ответа'''
    qs = Question.objects.filter(q__istartswith=query)
    result = []
    for i, q in enumerate(qs):
        result.append(
            telebot.types.InlineQueryResultArticle(
                id=i,
                title=q.q,
                description=q.a,
                input_message_content=telebot.types.InputTextMessageContent(
                    f'<b>Вопрос:</b> {q.q}\n<b>Ответ:</b>{q.a}',
                    parse_mode='HTML'
                )
            )
        )
    return result


@bot.inline_handler(lambda query: True)
def query_text(inline_query):
    '''Отвечает на inline запросы'''
    bot.answer_inline_query(
            inline_query.id,
            get_faq(inline_query.query)
        )


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    '''Изменяет статус оплаты, очищает корзину'''
    order_id = int(message.successful_payment.invoice_payload)
    user_id = message.from_user.id
    order = Order.objects.get(id=order_id)
    order.pay_status = Order.Status.YES
    order.save()

    save_order(order_id)

    CartProduct.objects.filter(client_id=user_id).delete()

    bot.send_message(message.chat.id, 'Спасибо за покупку')


@bot.pre_checkout_query_handler(func=lambda call: True)
def checkout(pre_checkout_query):
    '''Проверка перед оплатой. Здесь просто отвечает.'''
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    '''Обработка всех callback'''
    if callback.data == 'check':
        check_sub(callback.message.chat.id)
        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)
        bot.send_message(callback.message.chat.id,
                         'Спасибо за подписку! Можете пользоваться ботом')

        send_main_menu(callback.message.chat.id)

    elif callback.data.startswith('cats_'):
        count, page = callback.data.split('_')[1:]
        count, page = int(count), int(page)
        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)

        show_cats(callback.message.chat.id, count, page)

    elif callback.data.startswith('subcats_'):
        cat_id, count, page = callback.data.split('_')[1:]
        cat_id, count, page = int(cat_id), int(count), int(page)
        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)

        show_subcats(callback.message.chat.id, cat_id, count, page)

    elif callback.data.startswith('products_'):
        subcat_id, count, page = callback.data.split('_')[1:]
        subcat_id, count, page = int(subcat_id), int(count), int(page)
        try:
            bot.delete_message(message_id=callback.message.id,
                               chat_id=callback.message.chat.id)
            bot.delete_message(message_id=callback.message.id-1,
                               chat_id=callback.message.chat.id)
            bot.delete_message(message_id=callback.message.id-2,
                               chat_id=callback.message.chat.id)
        except Exception as e:
            print(e)

        show_products(callback.message.chat.id, subcat_id, count, page)

    elif callback.data.startswith('cart_add_q_'):
        product_id, quantity = callback.data.split('_')[3:]
        product_id, quantity = int(product_id), int(quantity)

        try:
            bot.delete_message(message_id=callback.message.id,
                               chat_id=callback.message.chat.id)
            bot.delete_message(message_id=callback.message.id-1,
                               chat_id=callback.message.chat.id)
            bot.delete_message(message_id=callback.message.id-2,
                               chat_id=callback.message.chat.id)
        except Exception as e:
            print(e)

        ask_confirm(callback.message.chat.id, product_id, quantity)

    elif callback.data.startswith('cart_add_'):
        product_id = int(callback.data.split('_')[-1])

        try:
            bot.delete_message(message_id=callback.message.id,
                               chat_id=callback.message.chat.id)
            bot.delete_message(message_id=callback.message.id-1,
                               chat_id=callback.message.chat.id)
            bot.delete_message(message_id=callback.message.id-2,
                               chat_id=callback.message.chat.id)
        except Exception as e:
            print(e)

        ask_quantity(callback.message.chat.id, product_id)

    elif callback.data.startswith('cart_confirm_add_'):
        product_id, quantity = callback.data.split('_')[3:]
        product_id, quantity = int(product_id), int(quantity)

        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)

        cart_add(callback.message.chat.id, product_id, quantity)

    elif callback.data.startswith('cart_show_'):
        count, page = callback.data.split('_')[2:]
        count, page = int(count), int(page)
        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)

        cart_show(callback.message.chat.id, count, page)

    elif callback.data.startswith('cart_del_'):
        product_id = int(callback.data.split('_')[-1])
        cart_del(callback.message.chat.id, product_id)
        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)

        cart_show(callback.message.chat.id, 5, 0)

    elif callback.data.startswith('cart_buy'):
        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)
        bot.send_message(callback.message.chat.id,
                         'Введите свой домашний адрес')
        bot.register_next_step_handler(callback.message, handle_address)

    elif callback.data.startswith('confirm_address_'):
        address = callback.data.split('_')[-1]
        bot.delete_message(message_id=callback.message.id,
                           chat_id=callback.message.chat.id)

        save_address(callback.message.chat.id, address)
        send_invoice(callback.message.chat.id)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    '''Приветствует, регистрирует клиента'''
    if Client.objects.filter(id=message.chat.id):
        bot.reply_to(message, 'Снова здравствуйте!')
    else:
        full_name = message.chat.first_name
        if message.chat.last_name:
            full_name += ' '+message.chat.last_name
        Client.objects.create(id=message.chat.id, full_name=full_name)
        bot.reply_to(message, 'Здравствуйте!')

    if check_sub(message.chat.id):
        send_main_menu(message.chat.id)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    '''Обработка текстовых сообщений'''
    if 'каталог' in message.text.lower():
        show_cats(message.chat.id, 4, 0)
    if 'корзина' in message.text.lower():
        cart_show(message.chat.id, 5, 0)
