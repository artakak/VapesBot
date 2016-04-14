# -*- coding: utf-8 -*-
from telegram import Emoji, ParseMode
from telegram.ext import Updater
import logging
import telegram
import sys
import re
import requests
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
    about_text = ('Электронные сигареты по доступным ценам http://china-vapes.ru')

    help_text = (
        'Функционал:\n'
        '/TOP - Подборка товаров с наивысшим рейтингом\n'
        '/random - Показ случайного товара\n'
        '/search - Поиск товаров по названию\n'
        '/photo - Вывод фотографий для текущего товара\n'
        '/help - Список комманд\n'
        '/about - О боте...\n'
    )

    def __init__(self, telegram, botan):
        if botan:
            from telegram.utils.botan import Botan
            self.botan = Botan(botan)

        self.updater = Updater(telegram)
        dp = self.updater.dispatcher
        dp.addTelegramCommandHandler('start', self.start)
        dp.addTelegramCommandHandler('close', self.start)
        dp.addTelegramCommandHandler('previous', self.get_previous)
        dp.addTelegramCommandHandler('next', self.get_next)
        dp.addTelegramCommandHandler('help', self.help)
        dp.addTelegramCommandHandler('about', self.about)
        dp.addTelegramCommandHandler('TOP', self.top)
        dp.addTelegramCommandHandler('sort_up', self.top_up)
        dp.addTelegramCommandHandler('sort_down', self.top_down)
        dp.addTelegramCommandHandler('search_sort_up', self.search_up)
        dp.addTelegramCommandHandler('search_sort_down', self.search_down)
        dp.addTelegramCommandHandler('search', self.search)
        dp.addTelegramCommandHandler('photo', self.photo)
        dp.addTelegramMessageHandler(self.do_search)
        dp.addTelegramCommandHandler('random', self.random)

        dp.addUnknownTelegramCommandHandler(self.unknow)

        dp.addErrorHandler(self.error)
        self.result = {}
        self.count = {}
        self.photo = {}
        self.photo_count = {}
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
                products = db.query(Product).filter(Product.product_name.contains("%"+string+"%")).order_by(Product.product_price.desc()).all()
            elif args == 'Search_Up':
                string = str(self.search_query[str(update.message.chat_id)])
                products = db.query(Product).filter(Product.product_name.contains("%"+string+"%")).order_by(Product.product_price).all()


        except Exception as e:
            logger.exception(e)

        #print(products)
        final = [u'*Наименование*: '+product.product_name+'\n'
                 u'*Рейтинг*: '+Emoji.WHITE_MEDIUM_STAR.decode('utf-8')*int(product.score)+'\n'
                 u'*Цена*: '+str(product.product_price)+u' РУБ\n'
                 u'[ЗАКАЗАТЬ]'+'('+product.partner_url+')\n' for product in products]

        k = 0
        for product in products:
            self.photo[str(k)] = []
            #self.photo[str(k)].append(product.product_picture)
            self.photo[str(k)] = product.product_other_picture.split(';')
            k+=1

        return final


    def start(self, bot, update):
        self.logger_wrap(update.message, 'start')
        custom_keyboard = [['/TOP '+Emoji.WHITE_MEDIUM_STAR.decode('utf-8'),'/random '+Emoji.BLACK_QUESTION_MARK_ORNAMENT.decode('utf-8')],
                           ['/search '+Emoji.RIGHT_POINTING_MAGNIFYING_GLASS.decode('utf-8'),'/help '+Emoji.ORANGE_BOOK.decode('utf-8')]]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
        bot.sendMessage(update.message.chat_id, text=self.help_text, reply_markup=reply_markup)

    def help(self, bot, update):
        self.logger_wrap(update.message, 'help')
        bot.sendMessage(update.message.chat_id, text=self.help_text)

    def about(self, bot, update):
        self.logger_wrap(update.message, 'about')
        bot.sendMessage(update.message.chat_id, text=self.about_text, parse_mode=ParseMode.MARKDOWN)

    def search(self, bot, update):
        self.logger_wrap(update.message, 'search')
        bot.sendMessage(update.message.chat_id, text='Введите ключевые слова для поиска товаров по названию', parse_mode=ParseMode.MARKDOWN)

    def do_search(self, bot, update):
        self.logger_wrap(update.message, 'do_search')
        self.search_query[str(update.message.chat_id)] = update.message.text
        self.give(bot,update, 'Search_Down')


    def give(self, bot, update, args):
        self.logger_wrap(update.message, 'give')
        if args in ['Search_Down','Search_Up']:
            self.custom_keyboard = [['/previous','/next'],
                                    ['/search_sort_up '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8')+Emoji.UPWARDS_BLACK_ARROW.decode('utf-8'),'/search_sort_down '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8')+Emoji.DOWNWARDS_BLACK_ARROW.decode('utf-8')],
                                    ['/photo','/close']]
        else:
            self.custom_keyboard = [['/previous','/next'],
                                    ['/sort_up '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8')+Emoji.UPWARDS_BLACK_ARROW.decode('utf-8'),'/sort_down '+Emoji.HEAVY_DOLLAR_SIGN.decode('utf-8')+Emoji.DOWNWARDS_BLACK_ARROW.decode('utf-8')],
                                    ['/photo','/close']]
        self.reply_markup = telegram.ReplyKeyboardMarkup(self.custom_keyboard, resize_keyboard=True)
        self.result[str(update.message.chat_id)] = self.product_wrap(bot, update, args)
        self.count[str(update.message.chat_id)] = 0
        self.photo_count = 0
        try:
            bot.sendMessage(update.message.chat_id, text=u'1 ИЗ %s\n' % (str(len(self.result[str(update.message.chat_id)])))+self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
        except:
            bot.sendMessage(update.message.chat_id, text=u'Извините, мне нечего Вам показать '+Emoji.CONFUSED_FACE.decode('utf-8'), parse_mode=ParseMode.MARKDOWN)


    def top(self, bot, update):
        self.logger_wrap(update.message, 'top')
        self.give(bot, update, 'TOP_Down')

    def random(self, bot, update):
        self.logger_wrap(update.message, 'random')
        self.custom_keyboard = [['/random'],
                                ['/photo','/close']]
        self.reply_markup = telegram.ReplyKeyboardMarkup(self.custom_keyboard, resize_keyboard=True)
        self.result[str(update.message.chat_id)] = self.product_wrap('Random')
        self.count[str(update.message.chat_id)] = 0
        self.photo_count = 0
        bot.sendMessage(update.message.chat_id, text=self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)

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

    def photo(self, bot, update):
        self.logger_wrap(update.message, 'photo')
        bot.sendChatAction(update.message.chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[str(self.count[str(update.message.chat_id)])]
        if self.photo_count+1 <= len(link):
            bot.sendMessage(update.message.chat_id, text=u'%s ИЗ %s\n' % (str(self.photo_count+1), str(len(link))), parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
            bot.sendPhoto(update.message.chat_id, photo=str(link[self.photo_count]))
            self.photo_count +=1
        else:
            self.photo_count = 0
            bot.sendMessage(update.message.chat_id, text=u'%s ИЗ %s\n' % (str(self.photo_count+1), str(len(link))), parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
            bot.sendPhoto(update.message.chat_id, photo=str(link[self.photo_count]))
            self.photo_count +=1


    def get_next(self, bot, update):
        self.logger_wrap(update.message, 'next')
        self.photo_count = 0
        try:
            self.count[str(update.message.chat_id)] += 1
            bot.sendMessage(update.message.chat_id, text=u'%s ИЗ %s\n' % (str(self.count[str(update.message.chat_id)]+1), str(len(self.result[str(update.message.chat_id)])))+self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
        except:
            self.count[str(update.message.chat_id)] -= 1
            bot.sendMessage(update.message.chat_id, text=u'Извините, это последний элемент в данной подборке '+Emoji.CONFUSED_FACE.decode('utf-8'), parse_mode=ParseMode.MARKDOWN)
            #self.start(bot, update)

    def get_previous(self, bot, update):
        self.logger_wrap(update.message, 'previous')
        self.photo_count = 0
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
            self.photo_count = 0
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

