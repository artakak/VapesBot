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
        '/TOP - Подборка товаров по рейтингу\n'
        '/random - Случайная подборка товаров\n'
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
        dp.addTelegramCommandHandler('TOP', self.give)
        dp.addTelegramCommandHandler('search', self.search)
        dp.addTelegramCommandHandler('photo', self.photo)
        dp.addTelegramMessageHandler(self.do_search)
        dp.addTelegramCommandHandler('random', self.give)

        dp.addUnknownTelegramCommandHandler(self.unknow)

        dp.addErrorHandler(self.error)
        self.result = {}
        self.count = {}
        self.photo = {}
        self.photo_count = {}

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

    def product_wrap(self):
        try:
            products = db.query(Product).filter_by(score=5).limit(30).all()
        except Exception as e:
            logger.exception(e)

        print(products)
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
        custom_keyboard = [['/TOP','/random'],['/search','/help']]
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
        self.custom_keyboard = [['/previous','/next'],['/photo','/close']]
        self.reply_markup = telegram.ReplyKeyboardMarkup(self.custom_keyboard, resize_keyboard=True)
        bot.sendMessage(update.message.chat_id, text=update.message.text+u' Результат поиска будет тут', parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)

    def give(self, bot, update):
        self.logger_wrap(update.message, 'give')
        self.custom_keyboard = [['/previous','/next'],['/photo','/close']]
        self.reply_markup = telegram.ReplyKeyboardMarkup(self.custom_keyboard, resize_keyboard=True)
        self.result[str(update.message.chat_id)] = self.product_wrap()
        self.count[str(update.message.chat_id)] = 0
        self.photo_count = 0
        bot.sendMessage(update.message.chat_id, text=self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)

    def photo(self, bot, update):
        self.logger_wrap(update.message, 'photo')
        bot.sendChatAction(update.message.chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[str(self.count[str(update.message.chat_id)])]
        try:
            bot.sendPhoto(update.message.chat_id, photo=str(link[self.photo_count]))
            self.photo_count +=1
        except:
            self.photo_count = 0
            bot.sendPhoto(update.message.chat_id, photo=str(link[self.photo_count]))


    def get_next(self, bot, update):
        self.logger_wrap(update.message, 'next')
        try:
            self.count[str(update.message.chat_id)] += 1
            bot.sendMessage(update.message.chat_id, text=self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
        except:
            self.start(bot, update)

    def get_previous(self, bot, update):
        self.logger_wrap(update.message, 'previous')
        try:
            self.count[str(update.message.chat_id)] -= 1
            bot.sendMessage(update.message.chat_id, text=self.result[str(update.message.chat_id)][self.count[str(update.message.chat_id)]], parse_mode=ParseMode.MARKDOWN, reply_markup=self.reply_markup)
        except:
            self.start(bot, update)

    def close(self, bot, update):
        self.logger_wrap(update.message, 'close')
        try:
            self.count[str(update.message.chat_id)] += 0
            self.result[str(update.message.chat_id)] = []
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
        #bot_token = '219477880:AAFt3Mug_afgVZdwR-ZWFSMJuUbUBQjM5Mk'
        #botan_token = 'UGbapiL6McQPN02FfOy9iTdCNOa9l9E9'
        bot_token = '207682614:AAHfnPbjo4RTAgov8cfEo3erRTLvmx43Ffg'
        botan_token = 'A6C6UgwxORRchQbmFkqHJl56SmL-G4iy'

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

