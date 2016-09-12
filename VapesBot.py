# -*- coding: utf-8 -*-
from telegram import Emoji, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram
import logging
import sys
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
        '/search - Поиск товаров по названию\n'
        '/photo - Вывод фотографий для текущего товара\n'
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
        dp.add_handler(CommandHandler('search', self.search))
        dp.add_handler(CommandHandler('photo', self.photog))
        dp.add_handler(MessageHandler([Filters.text], self.command_filter))
        dp.add_handler(CommandHandler('random', self.random))

        #dp.addUnknownTelegramCommandHandler(self.unknow)

        #dp.addErrorHandler(self.error)
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
                 u'*Магазин*: '+product.product_store_title+'\n'
                 u'*Рейтинг*: '+Emoji.WHITE_MEDIUM_STAR.decode('utf-8')*int(product.score)+'\n'
                 u'*Цена*: '+str(product.product_price)+u' РУБ\n'
                 u'[ЗАКАЗАТЬ]'+'('+product.partner_url+')\n' for product in products]
        k = 0
        self.photo[str(update.message.chat_id)] = {}
        for product in products:
            self.photo[str(update.message.chat_id)][str(k)] = []
            #self.photo[str(k)].append(product.product_picture)
            self.photo[str(update.message.chat_id)][str(k)] = product.product_other_picture.split('|')
            k+=1

        return final


    def start(self, bot, update):
        self.logger_wrap(update.message, 'start')
        bot.sendMessage(update.message.chat_id, text=u'*Электронные сигареты по доступным ценам*\n' + Emoji.CLOUD.decode('utf-8') * 3 + u' [China-Vapes.ru](http://china-vapes.ru) ' + Emoji.CLOUD.decode('utf-8') * 3, parse_mode=ParseMode.MARKDOWN)
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
        bot.sendMessage(update.message.chat_id, text='Введите ключевые слова для поиска товаров по названию', parse_mode=ParseMode.MARKDOWN)

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
        else:
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
        self.custom_keyboard = [[u'Ещё разок '+Emoji.BLACK_QUESTION_MARK_ORNAMENT.decode('utf-8')],
                                [u'Фотографии '+Emoji.CAMERA.decode('utf-8'),u'Закрыть '+Emoji.CROSS_MARK.decode('utf-8')]]
        self.reply_markup = telegram.ReplyKeyboardMarkup(self.custom_keyboard, resize_keyboard=True)
        self.result[str(update.message.chat_id)] = self.product_wrap(bot, update, 'Random')
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

    def photog(self, bot, update):
        self.logger_wrap(update.message, 'photo')
        bot.sendChatAction(update.message.chat_id, action=telegram.ChatAction.TYPING)
        link = self.photo[str(update.message.chat_id)][str(self.count[str(update.message.chat_id)])]
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

