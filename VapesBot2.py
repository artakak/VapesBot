# -*- coding: utf-8 -*-
from telegram import Emoji, ParseMode, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler, Filters, CallbackQueryHandler, ChosenInlineResultHandler
import telegram
import logging
import sys
import re
from sqlalchemy_wrapper import SQLAlchemy
import random


db = SQLAlchemy('sqlite:///Test.db')

# Enable logging
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

logger = logging.getLogger(__name__)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String(20), unique=True)
    product_cat_id = db.Column(db.String(10), unique=False)
    product_name = db.Column(db.String(200), unique=False)
    product_picture = db.Column(db.String(200), unique=False)
    product_other_picture = db.Column(db.Text, unique=False)
    product_test_one_flag = db.Column(db.Integer, unique=False)
    product_price_r = db.Column(db.Integer, unique=False)
    product_price_u = db.Column(db.Integer, unique=False)
    product_store_id = db.Column(db.String(20), unique=False)
    product_store_title = db.Column(db.String(20), unique=False)
    partner_url = db.Column(db.String(200), unique=False)
    orders_count = db.Column(db.Integer, unique=False)
    score = db.Column(db.Integer, unique=False)

    def __init__(self, product_id, product_cat_id, product_name, product_picture, product_other_picture, product_test_one_flag, product_price_r, product_price_u, product_store_id, product_store_title, partner_url, orders_count, score):
        self.product_id = product_id
        self.product_cat_id = product_cat_id
        self.product_name = product_name
        self.product_picture = product_picture
        self.product_other_picture = product_other_picture
        self.product_test_one_flag = product_test_one_flag
        self.product_price = product_price_r
        self.product_price = product_price_u
        self.product_store_id = product_store_id
        self.product_store_title = product_store_title
        self.partner_url = partner_url
        self.orders_count = orders_count
        self.score = score

    def __repr__(self):
        return '<Product %r, %r>' % (self.product_id, self.product_name)


class ChinaBot:

    help_text = (
        'Функционал:\n'
        '/TOP - Подборка товаров с наивысшим рейтингом\n'
        '/random - Показ случайного товара\n'
        '/find - Поиск товаров по названию\n'
        '/help - Список комманд\n'
        '/about - О боте...\n'
        'Для изменения сортировки в подборках нажмите <, находясь на первой позиции'
    )

    ut = {'help':
              {'RU':('Список комманд:\n'
                       '/TOP - Подборка товаров с наивысшим рейтингом\n'
                       '/random - Показ случайного товара\n'
                       '/find - Поиск товаров по названию\n'
                       '/EN - Изменить локализацию на En\n'
                       '/RU - Изменить локализацию на Ru\n'
                       '/help - Список комманд\n'
                       '/about - О боте...\n'
                       'Для изменения сортировки в подборках нажмите <, находясь на первой позиции'),

               'EN':('List of commands:\n'
                       '/TOP - Only best products\n'
                       '/random - Random product\n'
                       '/find - Find products by name\n'
                       '/EN - Change localisation En\n'
                       '/RU - Change localisation Ru\n'
                       '/help - List of commands\n'
                       '/about - About...\n'
                       'If you want change sorting of the results in sets press < at first position')},
          'product':
              {'RU':[u'Наименование',u'Магазин',u'Рейтинг',u'Цена',u'ЗАКАЗАТЬ'],
               'EN':['Item','Store','Rating','Cost','Purchase']},
          'hello':
              {'RU':u'Привет! Меня зовут @VapesBot, я помогу Вам найти электронные сигареты и аксессуары по доступным ценам с возможностью бесплатной доставки по всему миру.',
               'EN':'Hello! My name is @VapesBot, I can find best offers of E-cigs and accessories for you, best prices and free world-wide delivery.'},
          'hello_lang':
              {'RU':(u'\nПривет! Меня зовут @VapesBot, я помогу Вам найти электронные сигареты и аксессуары по доступным ценам с возможностью бесплатной доставки по всему миру.\n'
                     u'Для начала, необходимо выбрать язык интерфейса.\n'),
               'EN':('Hello! My name is @VapesBot, I can find best offers of E-cigs and accessories for you, best prices and free world-wide delivery.\n'
                     'Please, choose localisation.\n')},
          'main_keyboard':
              {'RU':['TOP ', u'Наугад ', u'Поиск ', u'Помощь '],
               'EN':['TOP ', 'Random ', 'Find ', 'Help ']}}

    def __init__(self, telegram, botan):
        if botan:
            from telegram.contrib.botan import Botan
            self.botan = Botan(botan)

        self.updater = Updater(telegram)
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('close', self.start))
        dp.add_handler(CommandHandler('previous', self.get_previous))
        dp.add_handler(CommandHandler('next', self.get_next))
        dp.add_handler(CommandHandler('help', self.help))
        dp.add_handler(CommandHandler('about', self.about))
        dp.add_handler(CommandHandler('TOP', self.top))
        dp.add_handler(CommandHandler('find', self.search))
        dp.add_handler(CommandHandler('random', self.random))
        dp.add_handler(CommandHandler('EN', self.engl))
        dp.add_handler(CommandHandler('RU', self.russ))
        dp.add_handler(CallbackQueryHandler(self.filter_for_inline))
        dp.add_handler(InlineQueryHandler(self.inline_search))
        dp.add_handler(ChosenInlineResultHandler(self.inline_picture))
        dp.add_handler(MessageHandler([Filters.text], self.command_filter))
        dp.add_handler(MessageHandler([Filters.command], self.unknow))

        #dp.addErrorHandler(self.error)
        self.result = {}
        self.count = {}
        self.photo_count = {}
        self.photo = {}
        self.answer = {}
        self.search_query = {}
        self.like = {}
        self.offset = {}
        self.podbor = {}
        self.choosen_locale = {}

    def logger_wrap(self, message, command):
        if self.botan:
            self.botan.track(
                message=message,
                event_name=command
            )
        user = message.from_user
        logger.info(u'%s from %s @%s %s' % (message.text[0:20],
                                            user.first_name,
                                            user.username,
                                            user.last_name))

    def product_wrap(self, bot, update, args):
        products = None
        try:
            if args == 'TOP_Down':
                products = db.query(Product).filter_by(score=5).order_by(Product.product_price_u.desc()).all()
            elif args == 'Random':
                count = db.query(Product).count()
                products = db.query(Product).filter_by(id=random.randint(1, count)).limit(10).all()
            elif args == 'Search_Down':
                string = str(self.search_query[str(update.message.chat_id)])
                products = db.query(Product).filter(Product.product_name.contains("%" + string + "%")).order_by(Product.product_price_u.desc()).all()
            elif args == 'Search_Inline':
                string = str(update.inline_query.query)
                products = db.query(Product).filter(Product.product_name.contains("%" + string + "%")).order_by(Product.product_price_u).all()
            elif args == 'ID':
                try: string = str(update.chosen_inline_result.result_id)
                except: string = self.answer[str(update.callback_query.inline_message_id)]
                products = db.query(Product).filter(Product.product_id == int(string))

        except Exception as e:
            logger.exception(e)
        if args == 'Search_Inline':
            return products
        elif args == 'ID':
            return self.good_view(bot, update, products, args)
        else:
            return self.good_view(bot, update, products, args=None)

    def good_view(self, bot, update, products, args):
        final = None
        if products:
            if args == 'Search_Inline':
                user_id = str(update.inline_query.from_user.id)
                locale = self.choosen_locale[user_id]
                if locale == 'RU':
                    final = [u'*%s*: ' % self.ut['product'][locale][0] + products.product_name + '\n'
                             u'*%s*: ' % self.ut['product'][locale][1] + str(products.product_store_title) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][2] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8') * int(products.score) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][3] + str(products.product_price_r) + u' РУБ\n'
                             u'[%s]' % self.ut['product'][locale][4] + '(' + products.partner_url + ')\n']
                elif locale == 'EN':
                    final = [u'*%s*: ' % self.ut['product'][locale][0] + products.product_name + '\n'
                             u'*%s*: ' % self.ut['product'][locale][1] + str(products.product_store_title) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][2] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8') * int(products.score) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][3] + str(products.product_price_u) + ' USD\n'
                             u'[%s]' % self.ut['product'][locale][4] + '(' + products.partner_url + ')\n']
            elif args == 'ID':
                user_id = str(update.chosen_inline_result.from_user.id)
                locale = self.choosen_locale[user_id]
                if locale == 'RU':
                    final = [u'*%s*: ' % self.ut['product'][locale][0] + products.product_name + '\n'
                             u'*%s*: ' % self.ut['product'][locale][1] + str(products.product_store_title) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][2] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8') * int(products.score) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][3] + str(products.product_price_r) + u' РУБ\n'
                             u'[%s]' % self.ut['product'][locale][4] + '(' + products.partner_url + ')\n']
                elif locale == 'EN':
                    final = [u'*%s*: ' % self.ut['product'][locale][0] + products.product_name + '\n'
                             u'*%s*: ' % self.ut['product'][locale][1] + str(products.product_store_title) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][2] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8') * int(products.score) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][3] + str(products.product_price_u) + ' USD\n'
                             u'[%s]' % self.ut['product'][locale][4] + '(' + products.partner_url + ')\n']
                self.photo[str(products[0].product_id)] = products[0].product_other_picture.split('|')
                return final
            else:
                if update.message:
                    id = str(update.message.message_id)
                    user_id = str(update.message.from_user.id)
                elif update.callback_query:
                    id = str(update.callback_query.message.message_id)
                    user_id = str(update.callback_query.from_user.id)
                locale = self.choosen_locale[user_id]
                self.photo[id] = []
                for product in products:
                    self.photo[id].append(product.product_other_picture.split('|'))
                if locale == 'RU':
                    final = [u'*%s*: ' % self.ut['product'][locale][0] + product.product_name + '\n'
                             u'*%s*: ' % self.ut['product'][locale][1] + str(product.product_store_title) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][2] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8')*int(product.score) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][3] + str(product.product_price_r) + u' РУБ\n'
                             u'[%s]' % self.ut['product'][locale][4] + '('+product.partner_url + ')\n' for product in products]
                elif locale == 'EN':
                    final = [u'*%s*: ' % self.ut['product'][locale][0] + product.product_name + '\n'
                             u'*%s*: ' % self.ut['product'][locale][1] + str(product.product_store_title) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][2] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8')*int(product.score) + '\n'
                             u'*%s*: ' % self.ut['product'][locale][3] + str(product.product_price_u) + ' USD\n'
                             u'[%s]' % self.ut['product'][locale][4] + '('+product.partner_url + ')\n' for product in products]
            return final

    def start(self, bot, update):
        try:
            self.logger_wrap(update.message, 'start')
            chat_id = str(update.message.chat_id)
            user_id = str(update.message.from_user.id)
        except:
            self.logger_wrap(update.callback_query.message, 'start')
            chat_id = str(update.callback_query.message.chat_id)
            user_id = str(update.callback_query.message.from_user.id)
        try:
            self.choosen_locale[user_id]
            local = self.choosen_locale[user_id]
            custom_keyboard = [[self.ut['main_keyboard'][local][0] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8'), self.ut['main_keyboard'][local][1] + Emoji.GAME_DIE.decode('utf-8')],
                               [self.ut['main_keyboard'][local][2] + Emoji.RIGHT_POINTING_MAGNIFYING_GLASS.decode('utf-8'), self.ut['main_keyboard'][local][3] + Emoji.ORANGE_BOOK.decode('utf-8')]]
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
            bot.sendMessage(chat_id, text=self.ut['hello'][self.choosen_locale[user_id]],
                            parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        except:
            custom_keyboard = [['/RU', '/EN']]
            reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
            bot.sendMessage(chat_id, text=(self.ut['hello_lang']['EN']+self.ut['hello_lang']['RU']), parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        self.del_previous(bot, update)

    def engl(self, bot, update):
        self.choosen_locale[str(update.message.from_user.id)] = 'EN'
        custom_keyboard = [[self.ut['main_keyboard']['EN'][0] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8'), self.ut['main_keyboard']['EN'][1] + Emoji.GAME_DIE.decode('utf-8')],
                           [self.ut['main_keyboard']['EN'][2] + Emoji.RIGHT_POINTING_MAGNIFYING_GLASS.decode('utf-8'), self.ut['main_keyboard']['EN'][3] + Emoji.ORANGE_BOOK.decode('utf-8')]]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        bot.sendMessage(update.message.chat_id, text=u'Language was set EN '+Emoji.SMILING_FACE_WITH_SUNGLASSES.decode('utf-8'), reply_markup=reply_markup)
        self.del_previous(bot, update)
        self.help(bot, update)

    def russ(self, bot, update):
        self.choosen_locale[str(update.message.from_user.id)] = 'RU'
        custom_keyboard = [[self.ut['main_keyboard']['RU'][0] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8'), self.ut['main_keyboard']['RU'][1] + Emoji.GAME_DIE.decode('utf-8')],
                           [self.ut['main_keyboard']['RU'][2] + Emoji.RIGHT_POINTING_MAGNIFYING_GLASS.decode('utf-8'), self.ut['main_keyboard']['RU'][3] + Emoji.ORANGE_BOOK.decode('utf-8')]]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        bot.sendMessage(update.message.chat_id, text=u'Язык был установлен RU '+Emoji.SMILING_FACE_WITH_SUNGLASSES.decode('utf-8'), reply_markup=reply_markup)
        self.del_previous(bot, update)
        self.help(bot, update)

    def help(self, bot, update):
        self.logger_wrap(update.message, 'help')
        try:
            local = self.choosen_locale[str(update.message.from_user.id)]
        except:
            self.start(bot, update)
            return
        bot.sendMessage(update.message.chat_id, text=self.ut['help'][local])
        self.del_previous(bot, update)

    def about(self, bot, update):
        self.logger_wrap(update.message, 'about')
        try:
            local = self.choosen_locale[str(update.message.from_user.id)]
        except:
            self.start(bot, update)
            return
        bot.sendMessage(update.message.chat_id, text=self.ut['hello'][local], parse_mode=ParseMode.MARKDOWN)
        self.del_previous(bot, update)

    def command_filter(self, bot, update):
        self.logger_wrap(update.message, 'command_filter')
        try:
            locale = self.choosen_locale[str(update.message.from_user.id)]
        except:
            self.start(bot, update)
            return
        if update.message.text == self.ut['main_keyboard'][locale][0] + Emoji.WHITE_MEDIUM_STAR.decode('utf-8'):
            self.top(bot, update)
        elif update.message.text == self.ut['main_keyboard'][locale][1] + Emoji.GAME_DIE.decode('utf-8'):
            self.random(bot, update)
        elif update.message.text == self.ut['main_keyboard'][locale][2] + Emoji.RIGHT_POINTING_MAGNIFYING_GLASS.decode('utf-8'):
            self.search(bot, update)
        elif update.message.text == self.ut['main_keyboard'][locale][3] + Emoji.ORANGE_BOOK.decode('utf-8'):
            self.help(bot, update)
        elif len(update.message.text) < 50:
            self.do_search(bot, update)

    def search(self, bot, update):
        #self.logger_wrap(update.message, 'search')
        keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text=u'Попробовать мой поиск '+Emoji.SMILING_FACE_WITH_SUNGLASSES.decode('utf-8'), switch_inline_query='ego')]])
        bot.sendMessage(update.message.chat_id, text='Введите ключевые слова для поиска товаров по названию, также, Вы можете использовать встроенный механизм поиска в любом чате, обратившись к боту через @ChinaVapesBot',
                        parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        self.del_previous(bot, update)

    def del_previous(self, bot, update):
        if update.message:
            chat_id = str(update.message.chat_id)
            id = str(update.message.message_id)
            k = 2
            m =1
        elif update.callback_query:
            chat_id = str(update.callback_query.message.chat_id)
            id = str(update.callback_query.message.message_id)
            k = 1
            m = 0
        try:
            if update.message:
                bot.editMessageText(text=u'Работа с подборкой %s была завершена, спасибо ' % self.podbor[chat_id] + Emoji.SMILING_FACE_WITH_SMILING_EYES.decode('utf-8'),
                                    chat_id=chat_id, message_id=str(int(id)-m), parse_mode=ParseMode.MARKDOWN)
            self.photo_count[chat_id].__delitem__(str(int(id)-k))
            self.result.__delitem__(str(int(id)-k))
            self.photo.__delitem__(str(int(id)-k))
            self.count.__delitem__(str(int(id)-k))
        except: pass

    def inline_search(self, bot, update):
        if update.inline_query:
            user = update.inline_query.from_user
            query = update.inline_query.query
            results = list()
            keyboard = self.do_keybord(1, 5, 'do_picture_inline')
            if query:
                logger.info('Inline: %s from %s @%s %s' % (query, user.first_name, user.username, user.last_name))
                if re.findall(r'[^A-Za-z0-9-\s]', query):
                    return
                products = self.product_wrap(bot, update, "Search_Inline")
                if products:
                    k = 0
                    for product in products:
                        if k < 50:
                            results.append(InlineQueryResultArticle(id=product.product_id, title=product.product_name,
                                                                    description=Emoji.WHITE_MEDIUM_STAR.decode('utf-8')*int(product.score)+u'  '+Emoji.BANKNOTE_WITH_DOLLAR_SIGN.decode('utf-8')+u'  '+str(product.product_price_r)+u' РУБ',
                                                                    thumb_url=product.product_picture, input_message_content=InputTextMessageContent(u''.join(self.good_view(bot, update, product, 'Search_Inline')[0]),
                                                                    parse_mode=ParseMode.MARKDOWN), reply_markup=keyboard))
                            k +=1
                        else: break
        bot.answerInlineQuery(update.inline_query.id, results, switch_pm_text=u'Я живу здесь '+Emoji.SMILING_FACE_WITH_SMILING_EYES.decode('utf-8'))

    def do_search(self, bot, update):
        #self.logger_wrap(update.message, 'do_search')
        if re.findall(r'[^A-Za-z0-9-\s]', update.message.text):
            bot.sendMessage(update.message.chat_id, text=u'Извините, мне нечего Вам показать ' + Emoji.CONFUSED_FACE.decode('utf-8'), parse_mode=ParseMode.MARKDOWN)
            return self.del_previous(bot, update)
        self.search_query[str(update.message.chat_id)] = update.message.text
        self.del_previous(bot, update)
        self.give(bot, update, 'Search_Down')
        self.podbor[str(update.message.chat_id)] = '/find'

    def give(self, bot, update, args):
        if update.message:
            try:
                self.choosen_locale[str(update.message.from_user.id)]
            except:
                self.start(bot, update)
                return
            #self.logger_wrap(update.message, 'give')
            #telegram.ReplyKeyboardHide(hide_keyboard=True)
            id = str(update.message.message_id)
            chat_id = str(update.message.chat_id)
            self.photo_count[chat_id] = {}
            self.photo_count[chat_id][id] = 1
            self.offset[chat_id] = 1
            self.result[id] = self.product_wrap(bot, update, args)
            if self.result[id]:
                self.count[id] = 0
                if args == 'Random':
                    keyboard = self.do_keybord(0, len(self.result[id]), 'random')
                    bot.sendMessage(chat_id, text=self.result[id][self.count[id]], parse_mode=ParseMode.MARKDOWN,
                                    reply_markup=keyboard)
                else:
                    keyboard = self.do_keybord(0, len(self.result[id]), 'do_picture_chat')
                    bot.sendMessage(chat_id, text=self.result[id][self.count[id]], parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            else:
                bot.sendMessage(chat_id, text=u'Извините, мне нечего Вам показать '+Emoji.CONFUSED_FACE.decode('utf-8'),
                                         parse_mode=ParseMode.MARKDOWN)
                self.result.__delitem__(id)
        elif update.callback_query:
            self.logger_wrap(update.callback_query.message, 'give')
            try:
                self.choosen_locale[str(update.callback_query.from_user.id)]
            except:
                self.start(bot, update)
                return
            # telegram.ReplyKeyboardHide(hide_keyboard=True)
            id = str(update.callback_query.message.message_id)
            chat_id = str(update.callback_query.message.chat_id)
            self.photo_count[chat_id] = {}
            self.photo_count[chat_id][id] = 1
            self.result[id] = self.product_wrap(bot, update, args)
            if self.result[id]:
                self.count[id] = 0
                if args == 'Random':
                    self.offset[chat_id] = 0
                    keyboard = self.do_keybord(0, len(self.result[id]), 'random')
                    bot.editMessageText(text=self.result[id][self.count[id]], chat_id=chat_id, message_id=id,
                                        parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
                else:
                    keyboard = self.do_keybord(0, len(self.result[id]), 'do_picture_chat')
                    bot.sendMessage(chat_id, text=self.result[id][self.count[id]], parse_mode=ParseMode.MARKDOWN,
                            reply_markup=keyboard)
            else:
                bot.sendMessage(chat_id, text=u'Извините, мне нечего Вам показать ' + Emoji.CONFUSED_FACE.decode('utf-8'),
                        parse_mode=ParseMode.MARKDOWN)
                self.result.__delitem__(id)

    def top(self, bot, update):
        self.logger_wrap(update.message, 'top')
        self.del_previous(bot, update)
        self.give(bot, update, 'TOP_Down')
        self.podbor[str(update.message.chat_id)] = '/TOP'

    def random(self, bot, update):
        if update.message:
            self.logger_wrap(update.message, 'random')
            chat_id = update.message.chat_id
        elif update.callback_query:
            self.logger_wrap(update.callback_query.message, 'random')
            chat_id = update.callback_query.message.chat_id
        self.del_previous(bot, update)
        self.give(bot, update, 'Random')
        self.podbor[str(chat_id)] = '/random'

    def do_keybord(self, current, total, flag):
        if flag == 'do_picture_chat':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text='<', callback_data='Previous_item'),
                                                       telegram.InlineKeyboardButton(text=str(current + 1) + u' ИЗ ' + str(total), callback_data='1'),
                                                       telegram.InlineKeyboardButton(text='>', callback_data='Next_item')],
                                                       [telegram.InlineKeyboardButton(text=Emoji.CAMERA.decode('utf-8'), callback_data='Do_photo_chat'),
                                                        telegram.InlineKeyboardButton(text=Emoji.HEAVY_BLACK_HEART.decode('utf-8'), callback_data='Like')]])
        elif flag == 'picture_slide':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text='<', callback_data='PreviousP'),
                                                       telegram.InlineKeyboardButton(text=str(current + 1) + u' ИЗ ' + str(total), callback_data='1'),
                                                       telegram.InlineKeyboardButton(text='>', callback_data='NextP'),
                                                       telegram.InlineKeyboardButton(text=Emoji.CROSS_MARK.decode('utf-8'), callback_data='X_c')]])

        elif flag == 'random_photo':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text='<', callback_data='PreviousP_r'),
                                                       telegram.InlineKeyboardButton(text=str(current + 1) + u' ИЗ ' + str(total), callback_data='1'),
                                                       telegram.InlineKeyboardButton(text='>', callback_data='NextP_r'),
                                                       telegram.InlineKeyboardButton(text=Emoji.CROSS_MARK.decode('utf-8'), callback_data='X_r')]])
        elif flag == 'do_picture_inline':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text=u'Фотографии', callback_data='Do_photo')]])
        elif flag == 'picture_slide_inline':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text='<', callback_data='PreviousP_in'),
                                                       telegram.InlineKeyboardButton(text=str(current + 1) + u' ИЗ ' + str(total), callback_data='1'),
                                                       telegram.InlineKeyboardButton(text='>', callback_data='NextP_in'),
                                                       telegram.InlineKeyboardButton(text=Emoji.CROSS_MARK.decode('utf-8'), callback_data='X_i')]])
        elif flag == 'random':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text=Emoji.GAME_DIE.decode('utf-8'), callback_data='More_random'),
                                                       telegram.InlineKeyboardButton(text=Emoji.CAMERA.decode('utf-8'), callback_data='Do_photo_random'),
                                                       telegram.InlineKeyboardButton(text=Emoji.HEAVY_BLACK_HEART.decode('utf-8'), callback_data='LikeR')]])
        return keyboard

    def inline_picture(self, bot, update):
        result = update.chosen_inline_result.result_id
        message = update.chosen_inline_result.inline_message_id
        self.user = update.chosen_inline_result.from_user
        self.query = update.chosen_inline_result.query
        k = telegram.ChosenInlineResult(result_id=result, from_user=self.user, query=self.query)
        self.answer[str(message)] = str(update.chosen_inline_result.result_id)
        try: self.photo[result]
        except: self.product_wrap(bot, update, 'ID')

    def filter_for_inline(self, bot, update):
        query = update.callback_query
        if query.data == 'More_random':
            self.random(bot, update)
        if query.data == '1':
            bot.answerCallbackQuery(callback_query_id=str(query.id),
                                    text=u'Не жмакайте мне там, щекотно ' + Emoji.SMILING_FACE_WITH_SMILING_EYES.decode('utf-8'))
        if query.data in ['Do_photo_chat', 'Do_photo_random']:
            self.photog(bot, update)
        if query.data == 'Next_item':
            self.get_next(bot, update)
        if query.data == 'Previous_item':
            self.get_previous(bot, update)
        if query.data == 'Close':
            self.del_previous(bot, update)
        if query.data in ['PreviousP', 'NextP', 'PreviousP_r', 'NextP_r']:
            self.slide_in_chat(bot, update)
        if query.data in ['Like', 'LikeR']:
            chat_id = str(query.message.chat_id)
            id = str(int(query.message.message_id) - self.offset[chat_id])
            self.like[chat_id] = self.result[id][self.count[id]]
            if query.data == 'LikeR':
                keyboard = self.do_keybord(int(self.count[id]), len(self.result[id]), 'random')
            else:
                keyboard = self.do_keybord(int(self.count[id]), len(self.result[id]), 'do_picture_chat')
            bot.editMessageText(text=Emoji.HEAVY_BLACK_HEART.decode('utf-8')+'\n'+self.like[chat_id],
                                chat_id=query.message.chat_id, message_id=query.message.message_id,
                                parse_mode=ParseMode.MARKDOWN)
            bot.sendMessage(chat_id, text=self.result[id][self.count[id]], parse_mode=ParseMode.MARKDOWN,
                                reply_markup=keyboard)
            bot.answerCallbackQuery(callback_query_id=str(query.id),
                                    text=u'Отложил в чатик ' + Emoji.SMILING_FACE_WITH_SMILING_EYES.decode('utf-8'))
            self.offset[chat_id]+=1
        if query.data in ['X_r', 'X_c']:
            chat_id = str(query.message.chat_id)
            id = str(int(query.message.message_id) - self.offset[chat_id])
            self.photo_count[chat_id][id] = 1
            if query.data == 'X_r':
                keyboard = self.do_keybord(int(self.count[id]), len(self.result[id]), 'random')
            else:
                keyboard = self.do_keybord(int(self.count[id]), len(self.result[id]), 'do_picture_chat')
            bot.editMessageText(text=self.result[id][self.count[id]],
                                chat_id=query.message.chat_id, message_id=query.message.message_id,
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        if query.data in ['PreviousP_in', 'NextP_in']:
            self.slide_in_inline(bot, update)
        if query.data == 'Do_photo':
            id = str(self.answer[query.inline_message_id])
            self.photo_count[id] = 0
            link = self.photo[id]
            keyboard = self.do_keybord(self.photo_count[id], len(self.photo[id]), 'picture_slide_inline')
            bot.editMessageText(text=u'[' + Emoji.CLOUD.decode('utf-8') + '](' + str(link[self.photo_count[id]]) + ')',
                                inline_message_id=query.inline_message_id,
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            self.photo_count[id] += 1
            #bot.editMessageReplyMarkup(inline_message_id=query.inline_message_id, reply_markup=keyboard)
        if query.data == 'X_i':
            id = str(self.answer[query.inline_message_id])
            self.photo_count[id] = 0
            keyboard = self.do_keybord(1, 5, 'do_picture_inline')
            product = self.product_wrap(bot, update, "ID")
            bot.editMessageText(text=u''.join(product[0]),
                                inline_message_id=query.inline_message_id,
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

    def slide_in_inline(self, bot, update):
        query = update.callback_query
        id = str(self.answer[query.inline_message_id])
        if query.data == 'PreviousP_in':
            self.photo_count[id] -= 2
        #bot.sendChatAction(query.message.chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[id]
        if 0 < self.photo_count[id] + 1 <= len(link):
            keyboard = self.do_keybord(self.photo_count[id], len(link), 'picture_slide_inline')
            bot.editMessageText(text=u'[' + Emoji.CLOUD.decode('utf-8') + '](' + str(link[self.photo_count[id]]) + ')',
                                inline_message_id=query.inline_message_id,
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            self.photo_count[id] += 1
        else:
            self.photo_count[id] = 0
            keyboard = self.do_keybord(self.photo_count[id], len(link), 'picture_slide_inline')
            try:
                bot.editMessageText(text=u'[' + Emoji.CLOUD.decode('utf-8') + '](' + str(link[self.photo_count[id]]) + ')',
                                    inline_message_id=query.inline_message_id,
                                    parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            except:
                bot.answerCallbackQuery(callback_query_id=str(query.id), text=u'Извините, но мне туда нельзя ' + Emoji.CONFUSED_FACE.decode('utf-8'))
            finally:
                self.photo_count[id] += 1

    def slide_in_chat(self, bot, update):
        query = update.callback_query
        chat_id = str(query.message.chat_id)
        id = str(int(query.message.message_id)-self.offset[chat_id])
        #if idq != self.id + 1: return
        if query.data in ['PreviousP', 'PreviousP_r']:
            self.photo_count[chat_id][id] -= 2
        #bot.sendChatAction(query.message.chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[id][self.count[id]]
        if 0 < self.photo_count[chat_id][id] + 1 <= len(link):
            if query.data in ['PreviousP_r', 'NextP_r']:
                keyboard = self.do_keybord(self.photo_count[chat_id][id], len(link), 'random_photo')
            else:
                keyboard = self.do_keybord(self.photo_count[chat_id][id],len(link), 'picture_slide')
            bot.editMessageText(text=u'['+Emoji.CLOUD.decode('utf-8')+']('+str(link[self.photo_count[chat_id][id]])+')',
                                chat_id=query.message.chat_id, message_id=query.message.message_id, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            self.photo_count[chat_id][id] +=1
        else:
            self.photo_count[chat_id][id] = 0
            try:
                if query.data in ['PreviousP_r', 'NextP_r']:
                    keyboard = self.do_keybord(self.photo_count[chat_id][id], len(link), 'random_photo')
                else:
                    keyboard = self.do_keybord(self.photo_count[chat_id][id], len(link), 'picture_slide')
                bot.editMessageText(text=u'[' + Emoji.CLOUD.decode('utf-8') + '](' + str(link[self.photo_count[chat_id][id]]) + ')',
                                    chat_id=query.message.chat_id, message_id=query.message.message_id,
                                    parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            except:
                bot.answerCallbackQuery(callback_query_id=str(query.id), text=u'Извините, но мне туда нельзя '+Emoji.CONFUSED_FACE.decode('utf-8'))
            finally: self.photo_count[chat_id][id] += 1

    def photog(self, bot, update):
        self.logger_wrap(update.callback_query.message, 'photo')
        query = update.callback_query
        chat_id = str(query.message.chat_id)
        id = str(int(query.message.message_id)-self.offset[chat_id])
        #bot.sendChatAction(chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[id][self.count[id]]
        if query.data == 'Do_photo_chat':
            keyboard = self.do_keybord(0, len(link), 'picture_slide')
        elif query.data == 'Do_photo_random':
            keyboard = self.do_keybord(0, len(link), 'random_photo')
        bot.editMessageText(text=u'['+Emoji.CLOUD.decode('utf-8')+']('+str(link[0])+')',
                            chat_id=query.message.chat_id, message_id=query.message.message_id,
                            reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)

    def get_next(self, bot, update):
        self.logger_wrap(update.callback_query.message, 'next')
        query = update.callback_query
        chat_id = str(query.message.chat_id)
        id = str(int(query.message.message_id)-self.offset[chat_id])
        try:
            self.count[id] += 1
            keyboard = self.do_keybord(int(self.count[id]), len(self.result[id]), 'do_picture_chat')
            bot.editMessageText(text=self.result[id][self.count[id]],
                                chat_id=query.message.chat_id, message_id=query.message.message_id,
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        except:
            self.count[id] -= 1
            bot.answerCallbackQuery(callback_query_id=str(query.id), text=u'Извините, но мне туда нельзя ' + Emoji.CONFUSED_FACE.decode('utf-8'))
            #self.start(bot, update)

    def get_previous(self, bot, update):
        self.logger_wrap(update.callback_query.message, 'previous')
        query = update.callback_query
        chat_id = str(query.message.chat_id)
        id = str(int(query.message.message_id) - self.offset[chat_id])
        if self.count[id] >= 1:
            self.count[id] -= 1
            keyboard = self.do_keybord(int(self.count[id]), len(self.result[id]), 'do_picture_chat')
            bot.editMessageText(text=self.result[id][self.count[id]],
                                chat_id=query.message.chat_id, message_id=query.message.message_id,
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        else:
            self.result[id] = list(self.result[id].__reversed__())
            self.photo[id] = list(self.photo[id].__reversed__())
            keyboard = self.do_keybord(int(self.count[id]), len(self.result[id]), 'do_picture_chat')
            bot.editMessageText(text=self.result[id][self.count[id]],
                                chat_id=query.message.chat_id, message_id=query.message.message_id,
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            bot.answerCallbackQuery(callback_query_id=str(query.id),
                                    text=u'Произведена смена сортировки по цене ' + Emoji.WARNING_SIGN.decode('utf-8'))
            #self.start(bot, update)

    def close(self, bot, update):
        self.logger_wrap(update.message, 'close')
        try:
            self.count[str(update.message.chat_id)] = 0
            self.result[str(update.message.chat_id)] = []
            self.search_query[str(update.message.chat_id)] = ''
            self.start(bot, update)
        except:
            self.start(bot, update)

    def unknow(self, bot, update):
        self.logger_wrap(update.message, 'unknow')

    def error(self, bot, update, error):
        self.logger_wrap(update.message, 'error')
        logger.warn('Update "%s" caused error "%s"' % (update, error))

    def idle(self):
        self.updater.start_polling()
        self.updater.idle()


def main():
    try:
        bot_token = '219477880:AAFt3Mug_afgVZdwR-ZWFSMJuUbUBQjM5Mk'
        botan_token = 'UGbapiL6McQPN02FfOy9iTdCNOa9l9E9'
        #bot_token = '207682614:AAHfnPbjo4RTAgov8cfEo3erRTLvmx43Ffg'
        #botan_token = 'A6C6UgwxORRchQbmFkqHJl56SmL-G4iy'

    except Exception as e:
        logger.exception(e)
        sys.exit()

    if not bot_token:
        logger.error('Bot token is empty')
        sys.exit()

    bot = ChinaBot(bot_token, botan_token)
    bot.idle()


if __name__ == '__main__':
    main()

