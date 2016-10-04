# -*- coding: utf-8 -*-
import requests, requesocks, json, BeautifulSoup, re, time, random
from sqlalchemy_wrapper import SQLAlchemy
from stem import Signal
from stem.control import Controller

db = SQLAlchemy('sqlite:///Test.db')

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
        self.product_price_r = product_price_r
        self.product_price_u = product_price_u
        self.product_store_id = product_store_id
        self.product_store_title = product_store_title
        self.partner_url = partner_url
        self.orders_count = orders_count
        self.score = score

    def __repr__(self):
        return '<Product %r, %r>' % (self.product_id, self.product_name)


def get_products_list():
        result = ('req3','req4','req5','req6')
        post_url_api = 'http://api.epn.bz/json'
        req_pull={'req1':{'action':'list_categories','lang':'en'},
                  'req2':{'action':'offer_info','id':'32611301612','currency':'RUR,USD','lang':'en'},
                  'req3':{'action':'search','store':'335020,1247181','limit':'10000','currency':'RUR,USD','lang':'en'},
                  'req4': {'action': 'search', 'store': '409690,1209066', 'limit': '10000','currency': 'RUR,USD', 'lang': 'en'},
                  'req5': {'action': 'search', 'store': '2144005', 'limit': '10000', 'currency': 'RUR,USD', 'lang': 'en'},
                  'req6': {'action': 'search', 'store': '1185223', 'limit': '10000', 'currency': 'RUR,USD', 'lang': 'en'}
                 }
        post_data ={'user_api_key':'8d6467cedd2db955e23ef3d4e9b32760',
                   'user_hash':'o4jauozbl5c3jfrcco1droidutid00g4',
                   'api_version': '2',
                   'requests':req_pull}

        post_req = requests.post(post_url_api,json=post_data)
        data = json.loads(post_req.text)
        for k in result:
            print k + ': ' + str(len(data['results'][k]['offers']))
            for product in data['results'][k]['offers']:
                if 'pcs/lot' not in product['name'] and 'pcs' not in product['name'] and 'PCS' not in product['name']:
                    all_img = '|'.join(product['all_images'])
                    db.add(Product(product['id'], product['id_category'], product['name'], product['picture'], all_img, 0, product['prices']['RUR'], product['prices']['USD'], product['store_id'], product['store_title'], product['url'], product['orders_count'], product['evaluatescore']))

def renew_connection():
    with Controller.from_port(port=9151) as controller:
        controller.authenticate(password="password")
        controller.signal(Signal.NEWNYM)

def get_all_picture():
    #session = requesocks.session()
    proxies = {'http': 'socks5://127.0.0.1:9150',
               'https': 'socks5://127.0.0.1:9150'}
    all_products_list = db.query(Product).all()
    print len(all_products_list)
    count = 1
    for product in all_products_list:
        product_p = product.product_other_picture.split('|')
        print ('Process' + str(count))
        if len(product_p) < 2 and product.product_test_one_flag == 0:
            while True:
                try:
                    req = requesocks.get(product.partner_url, proxies=proxies)
                    #time.sleep(random.randint(0,5))
                    soup = BeautifulSoup.BeautifulSoup(req.text)
                    print product.partner_url
                    #print soup
                    name2 = []
                    for t in soup.findAll("span", {"class": "img-thumb-item"}):
                        name2.append(t.next['src'])
                    name = re.findall(r'[^/]+\.jpg$', product.product_picture)
                    print name
                    print name2
                    assert (name2 != [])
                    true = []
                    for s in name2:
                        true.append(re.sub(ur'[^/]+\.jpg$', name[0], s))
                    print 'OK_PARS'+str(count)
                    count+=1
                    product.product_other_picture = '|'.join(true)
                    db.session.add(product)
                    db.session.commit()
                    break
                except:
                    if soup.findAll("div", {"class": "ui-image-viewer-thumb-wrap"}):
                        print 'OK_SetFlag_to_1'
                        product.product_test_one_flag = 1
                        db.session.add(product)
                        db.session.commit()
                        count += 1
                        break
                    else:
                        print 'Change Proxy'
                        renew_connection()
        else:
            count += 1

a = raw_input()
if a == '1':
    db.create_all()
    get_products_list()
    db.commit()
elif a =='2':
    get_all_picture()



