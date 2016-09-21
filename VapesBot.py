# -*- coding: utf-8 -*-
from telegram import Emoji, ParseMode, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, InlineQueryHandler, Filters, CallbackQueryHandler, ChosenInlineResultHandler
import telegram
import logging
import time
import sys
import re
import json
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
    product_picture = db.Column(db.String(200), unique=True)
    product_other_picture = db.Column(db.Text, unique=False)
    product_price = db.Column(db.Integer, unique=False)
    product_store_id = db.Column(db.String(20), unique=False)
    product_store_title = db.Column(db.String(20), unique=False)
    partner_url = db.Column(db.String(200), unique=False)
    orders_count = db.Column(db.Integer, unique=False)
    score = db.Column(db.Integer, unique=False)

    def __init__(self, product_id, product_cat_id, product_name, product_picture, product_other_picture, product_price, product_store_id, product_store_title, partner_url, orders_count, score):
        self.product_id = product_id
        self.product_cat_id = product_cat_id
        self.product_name = product_name
        self.product_picture = product_picture
        self.product_other_picture = product_other_picture
        self.product_price = product_price
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
    )

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
        dp.add_handler(CommandHandler('sort_up', self.top_up))
        dp.add_handler(CommandHandler('sort_down', self.top_down))
        dp.add_handler(CommandHandler('search_sort_up', self.search_up))
        dp.add_handler(CommandHandler('search_sort_down', self.search_down))
        dp.add_handler(CommandHandler('find', self.search))
        dp.add_handler(CommandHandler('random', self.random))
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

    def logger_wrap(self, message, command):
        if self.botan:
            self.botan.track(
                message=message,
                event_name=command
            )
        user = message.from_user
        logger.info(u'%s from %s @%s %s' % (message.text,
                                            user.first_name,
                                            user.username,
                                            user.last_name))

    def product_wrap(self, bot, update, args):
        products = None
        try:
            if args == 'TOP_Up':
                products = db.query(Product).filter_by(score=5).order_by(Product.product_price).all()
            elif args == 'TOP_Down':
                products = db.query(Product).filter_by(score=5).order_by(Product.product_price.desc()).all()
            elif args == 'Random':
                count = db.query(Product).count()
                products = db.query(Product).filter_by(id=random.randint(1, count)).limit(10).all()
            elif args == 'Search_Down':
                string = str(self.search_query[str(update.message.chat_id)])
                products = db.query(Product).filter(Product.product_name.contains("%" + string + "%")).order_by(Product.product_price.desc()).all()
            elif args == 'Search_Up':
                string = str(self.search_query[str(update.message.chat_id)])
                products = db.query(Product).filter(Product.product_name.contains("%"+string+"%")).order_by(Product.product_price).all()
            elif args == 'Search_Inline':
                string = str(update.inline_query.query)
                products = db.query(Product).filter(Product.product_name.contains("%" + string + "%")).order_by(Product.product_price).all()
            elif args == 'ID':
                try: string = str(update.chosen_inline_result.result_id)
                except: string = self.answer[str(update.callback_query.inline_message_id)]
                products = db.query(Product).filter(Product.product_id == int(string))

        except Exception as e:
            logger.exception(e)
        if args == 'Search_Inline' and products:
            return products
        elif args == 'ID' and products:
            return self.good_view(bot, update, products, args)
        else:
            return self.good_view(bot, update, products, args=None)

    def good_view(self, bot, update, products, args):
        final = None
        if args == 'Search_Inline':
            final = [u'*Наименование*: ' + products.product_name + '\n'
                     u'*Магазин*: ' + products.product_store_title + '\n'
                     u'*Рейтинг*: ' + Emoji.WHITE_MEDIUM_STAR.decode('utf-8') * int(products.score) + '\n'
                     u'*Цена*: ' + str(products.product_price) + u' РУБ\n'
                     u'[ЗАКАЗАТЬ]' + '(' + products.partner_url + ')\n']
        elif args == 'ID':
            final = [u'*Наименование*: ' + products[0].product_name + '\n'
                     u'*Магазин*: ' + products[0].product_store_title + '\n'
                     u'*Рейтинг*: ' + Emoji.WHITE_MEDIUM_STAR.decode('utf-8') * int(products[0].score) + '\n'
                     u'*Цена*: ' + str(products[0].product_price) + u' РУБ\n'
                     u'[ЗАКАЗАТЬ]' + '(' + products[0].partner_url + ')\n']
            self.photo[str(products[0].product_id)] = products[0].product_other_picture.split('|')
            return final
        else:
            k = 0
            self.photo[str(update.message.chat_id)] = {}
            for product in products:
                self.photo[str(update.message.chat_id)][str(k)] = []
                # self.photo[str(k)].append(product.product_picture)
                self.photo[str(update.message.chat_id)][str(k)] = product.product_other_picture.split('|')
                k += 1
            final = [u'*Наименование*: '+product.product_name+'\n'
                     u'*Магазин*: '+product.product_store_title+'\n'
                     u'*Рейтинг*: '+Emoji.WHITE_MEDIUM_STAR.decode('utf-8')*int(product.score)+'\n'
                     u'*Цена*: '+str(product.product_price)+u' РУБ\n'
                     u'[ЗАКАЗАТЬ]'+'('+product.partner_url+')\n' for product in products]
        return final

    def start(self, bot, update):
        self.logger_wrap(update.message, 'start')
        bot.sendMessage(update.message.chat_id, text=u'*Электронные сигареты по доступным ценам*\n' + Emoji.CLOUD.decode('utf-8') * 3 + u' [China-Vapes.ru](http://china-vapes.ru) ' + Emoji.CLOUD.decode('utf-8') * 3,
                        parse_mode=ParseMode.MARKDOWN)
        custom_keyboard = [['TOP '+Emoji.WHITE_MEDIUM_STAR.decode('utf-8'),u'Наугад '+Emoji.BLACK_QUESTION_MARK_ORNAMENT.decode('utf-8')],
                           [u'Поиск '+Emoji.RIGHT_POINTING_MAGNIFYING_GLASS.decode('utf-8'),u'Помощь '+Emoji.ORANGE_BOOK.decode('utf-8')]]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        bot.sendMessage(update.message.chat_id, text=self.help_text, reply_markup=reply_markup)

    def help(self, bot, update):
        self.logger_wrap(update.message, 'help')
        bot.sendMessage(update.message.chat_id, text=self.help_text)

    def about(self, bot, update):
        self.logger_wrap(update.message, 'about')
        bot.sendMessage(update.message.chat_id, text=u'*Электронные сигареты по доступным ценам*\n'+Emoji.CLOUD.decode('utf-8')*3+u' [China-Vapes.ru](http://china-vapes.ru) '+Emoji.CLOUD.decode('utf-8')*3, parse_mode=ParseMode.MARKDOWN)

    def search(self, bot, update):
        self.logger_wrap(update.message, 'search')
        bot.sendMessage(update.message.chat_id, text='Введите ключевые слова для поиска товаров по названию, также, Вы можете использовать встроенный механизм поиска в любом чате, обратившись к боту через @ChinaVapesBot', parse_mode=ParseMode.MARKDOWN)

    def inline_search(self, bot, update):
        if update.inline_query:
            user = update.inline_query.from_user
            query = update.inline_query.query
            results = list()
            keyboard = self.do_keybord(1, 5, 'do_picture_inline')
            if query:
                logger.info('Inline: %s from %s @%s %s' % (query, user.first_name, user.username, user.last_name))
                products = self.product_wrap(bot, update, "Search_Inline")
                if products:
                    k = 0
                    for product in products:
                        if k < 50:
                            print str(product.product_id)
                            results.append(InlineQueryResultArticle(id=product.product_id, title=product.product_name,
                                                                    description=Emoji.WHITE_MEDIUM_STAR.decode('utf-8')*int(product.score)+u'  '+Emoji.BANKNOTE_WITH_DOLLAR_SIGN.decode('utf-8')+u'  '+str(product.product_price)+u' РУБ',
                                                                    thumb_url=product.product_picture, input_message_content=InputTextMessageContent(u''.join(self.good_view(bot, update, product, 'Search_Inline')[0]),
                                                                    parse_mode=ParseMode.MARKDOWN), reply_markup=keyboard))
                            k +=1
                        else: break
        bot.answerInlineQuery(update.inline_query.id, results)

    def command_filter(self, bot, update):
        self.logger_wrap(update.message, 'command_filter')
        if update.message.text == 'TOP '+Emoji.WHITE_MEDIUM_STAR.decode('utf-8'):
            self.top(bot, update)
        elif update.message.text == u'Наугад ' + Emoji.BLACK_QUESTION_MARK_ORNAMENT.decode('utf-8') or update.message.text == u'Ещё разок ' + Emoji.BLACK_QUESTION_MARK_ORNAMENT.decode('utf-8'):
            self.random(bot, update)
        elif update.message.text == u'Поиск '+Emoji.RIGHT_POINTING_MAGNIFYING_GLASS.decode('utf-8'):
            self.search(bot, update)
        elif update.message.text == u'Помощь ' + Emoji.ORANGE_BOOK.decode('utf-8'):
            self.help(bot, update)
        elif update.message.text == Emoji.LEFTWARDS_BLACK_ARROW.decode('utf-8')+u' Предыдущий':
            self.get_previous(bot, update)
        elif update.message.text == u'Следующий '+Emoji.BLACK_RIGHTWARDS_ARROW.decode('utf-8'):
            self.get_next(bot, update)
        elif update.message.text == u'По возрастанию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8'):
            self.search_up(bot, update)
        elif update.message.text == u'По убыванию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8'):
            self.search_down(bot, update)
        elif update.message.text == u'Пo возрастанию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8'):
            self.top_up(bot, update)
        elif update.message.text == u'Пo убыванию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8'):
            self.top_down(bot, update)
        elif update.message.text == u'Фотографии ' + Emoji.CAMERA.decode('utf-8'):
            self.photog(bot, update)
        elif update.message.text == u'Закрыть ' + Emoji.CROSS_MARK.decode('utf-8'):
            self.start(bot, update)
        elif len(update.message.text) < 50:
            self.do_search(bot, update)

    def do_search(self, bot, update):
        self.logger_wrap(update.message, 'do_search')
        self.search_query[str(update.message.chat_id)] = update.message.text
        self.give(bot,update, 'Search_Down')

    def give(self, bot, update, args):
        self.logger_wrap(update.message, 'give')
        if args in ['Search_Down','Search_Up']:
            self.custom_keyboard = [[Emoji.LEFTWARDS_BLACK_ARROW.decode('utf-8')+u' Предыдущий',u'Следующий '+Emoji.BLACK_RIGHTWARDS_ARROW.decode('utf-8')],
                                    [u'По возрастанию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8'),u'По убыванию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8')],
                                    [u'Фотографии '+Emoji.CAMERA.decode('utf-8'),u'Закрыть '+Emoji.CROSS_MARK.decode('utf-8')]]
        else:
            self.custom_keyboard = [[Emoji.LEFTWARDS_BLACK_ARROW.decode('utf-8')+u' Предыдущий',u'Следующий '+Emoji.BLACK_RIGHTWARDS_ARROW.decode('utf-8')],
                                    [u'Пo возрастанию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8'),u'Пo убыванию '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8')],
                                    [u'Фотографии '+Emoji.CAMERA.decode('utf-8'),u'Закрыть '+Emoji.CROSS_MARK.decode('utf-8')]]
        self.reply_markup = telegram.ReplyKeyboardMarkup(self.custom_keyboard, resize_keyboard=True)
        self.result[str(update.message.chat_id)] = self.product_wrap(bot, update, args)
        self.count[str(update.message.chat_id)] = 0
        try:
            bot.sendMessage(update.message.chat_id, text=u'1 ИЗ %s\n' % (str(len(self.result[str(update.message.chat_id)])))+self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
        except:
            bot.sendMessage(update.message.chat_id, text=u'Извините, мне нечего Вам показать '+Emoji.CONFUSED_FACE.decode('utf-8'),
                                                    parse_mode=ParseMode.MARKDOWN)

    def top(self, bot, update):
        self.logger_wrap(update.message, 'top')
        self.give(bot, update, 'TOP_Down')

    def random(self, bot, update):
        self.logger_wrap(update.message, 'random')
        self.custom_keyboard = [[u'Ещё разок '+Emoji.BLACK_QUESTION_MARK_ORNAMENT.decode('utf-8')],
                                [u'Фотографии '+Emoji.CAMERA.decode('utf-8'),u'Закрыть '+Emoji.CROSS_MARK.decode('utf-8')]]
        self.reply_markup = telegram.ReplyKeyboardMarkup(self.custom_keyboard, resize_keyboard=True)
        self.result[str(update.message.chat_id)] = self.product_wrap(bot, update, 'Random')
        self.count[str(update.message.chat_id)] = 0
        bot.sendMessage(update.message.chat_id, text=self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]],
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=self.reply_markup)

    def top_down(self, bot, update):
        self.logger_wrap(update.message, 'top_down')
        self.give(bot, update, 'TOP_Down')

    def top_up(self, bot, update):
        self.logger_wrap(update.message, 'top_up')
        self.give(bot, update, 'TOP_Up')

    def search_down(self, bot, update):
        self.logger_wrap(update.message, 'search_down')
        self.give(bot, update, 'Search_Down')

    def search_up(self, bot, update):
        self.logger_wrap(update.message, 'search_up')
        self.give(bot, update, 'Search_Up')

    def do_keybord(self, current, total, flag):
        if flag == 'picture_slide':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text='<', callback_data='PreviousP'),
                                                       telegram.InlineKeyboardButton(text=str(current + 1) + u' ИЗ ' + str(total), callback_data='1'),
                                                       telegram.InlineKeyboardButton(text='>', callback_data='NextP')]])
        elif flag == 'do_picture_inline':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text=u'Фотографии', callback_data='Do_photo')]])

        elif flag == 'picture_slide_inline':
            keyboard = telegram.InlineKeyboardMarkup([[telegram.InlineKeyboardButton(text='<', callback_data='PreviousP_in'),
                                                       telegram.InlineKeyboardButton(text=str(current + 1) + u' ИЗ ' + str(total), callback_data='1'),
                                                       telegram.InlineKeyboardButton(text='>', callback_data='NextP_in'),
                                                       telegram.InlineKeyboardButton(text='X', callback_data='X')]])
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
        #print result
        #print k
        #print picture

    def filter_for_inline(self, bot, update):
        query = update.callback_query
        if query.data in ['PreviousP', 'NextP']:
            self.slide_in_chat(bot, update)
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
        if query.data == 'X':
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
                pass
            finally:
                self.photo_count[id] += 1

    def slide_in_chat(self, bot, update):
        query = update.callback_query
        id = str(int(query.message.message_id)-1)
        chat_id = str(query.message.chat_id)
        if int(id) != int(self.id): return
        if query.data == 'PreviousP':
            self.photo_count[chat_id][id] -= 2
        #bot.sendChatAction(query.message.chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[str(query.message.chat_id)][str(self.count[str(query.message.chat_id)])]
        if 0 < self.photo_count[chat_id][id] + 1 <= len(link):
            keyboard = self.do_keybord(self.photo_count[chat_id][id],len(link), 'picture_slide')
            bot.editMessageText(text=u'['+Emoji.CLOUD.decode('utf-8')+']('+str(link[self.photo_count[chat_id][id]])+')',
                                chat_id=query.message.chat_id, message_id=query.message.message_id, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            self.photo_count[chat_id][id] +=1
        else:
            self.photo_count[chat_id][id] = 0
            keyboard = self.do_keybord(self.photo_count[chat_id][id], len(link), 'picture_slide')
            try:
                bot.editMessageText(text=u'[' + Emoji.CLOUD.decode('utf-8') + '](' + str(link[self.photo_count[chat_id][id]]) + ')',
                                    chat_id=query.message.chat_id, message_id=query.message.message_id,
                                    parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
            except: pass
            finally: self.photo_count[chat_id][id] += 1

    def photog(self, bot, update):
        self.logger_wrap(update.message, 'photo')
        #bot.sendChatAction(update.message.chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[str(update.message.chat_id)][str(self.count[str(update.message.chat_id)])]
        keyboard = self.do_keybord(0, len(link), 'picture_slide')
        bot.sendMessage(update.message.chat_id, text=u'['+Emoji.CLOUD.decode('utf-8')+']('+str(link[0])+')', reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        id = str(update.message.message_id)
        chat_id = str(update.message.chat_id)
        self.photo_count[chat_id] = {}
        self.photo_count[chat_id][id] = 1
        self.id = id

    def get_next(self, bot, update):
        self.logger_wrap(update.message, 'next')
        try:
            self.count[str(update.message.chat_id)] += 1
            bot.sendMessage(update.message.chat_id, text=u'%s ИЗ %s\n' % (str(self.count[str(update.message.chat_id)]+1), str(len(self.result[str(update.message.chat_id)])))+self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
        except:
            self.count[str(update.message.chat_id)] -= 1
            bot.sendMessage(update.message.chat_id, text=u'Извините, это последний элемент в данной подборке '+Emoji.CONFUSED_FACE.decode('utf-8'), parse_mode=ParseMode.MARKDOWN)
            #self.start(bot, update)

    def get_previous(self, bot, update):
        self.logger_wrap(update.message, 'previous')
        if self.count[str(update.message.chat_id)] >= 1:
            self.count[str(update.message.chat_id)] -= 1
            bot.sendMessage(update.message.chat_id, text=u'%s ИЗ %s\n' % (str(self.count[str(update.message.chat_id)]+1), str(len(self.result[str(update.message.chat_id)])))+self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
        else:
            bot.sendMessage(update.message.chat_id, text=u'Извините, это первый элемент в данной подборке '+Emoji.CONFUSED_FACE.decode('utf-8'), parse_mode=ParseMode.MARKDOWN)
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

