__author__ = 'win7_test'
import requests, json
from sqlalchemy_wrapper import SQLAlchemy

db = SQLAlchemy('sqlite:///Test.db')

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


def get_products_list():
        result = ('req3','req4')
        post_url_api = 'http://api.epn.bz/json'
        req_pull={'req1':{'action':'list_categories','lang':'en'},
                  'req2':{'action':'offer_info','id':'32262991446','currency':'RUR','lang':'en'},
                  'req3':{'action':'search','store':'335020,1247181','limit':'10000','currency':'RUR','lang':'en'},
                  'req4': {'action': 'search', 'store': '409690,1209066', 'limit': '10000','currency': 'RUR', 'lang': 'en'}
                  }
        post_data ={'user_api_key':'8d6467cedd2db955e23ef3d4e9b32760',
                   'user_hash':'o4jauozbl5c3jfrcco1droidutid00g4',
                   'api_version': '2',
                   'requests':req_pull}

        post_req = requests.post(post_url_api,json=post_data)
        #print (post_req.status_code)
        print (post_req.text)
        data = json.loads(post_req.text)
        for k in result:
            for product in data['results'][k]['offers']:
                if 'pcs/lot' not in product['name'] and 'pcs' not in product['name'] and 'PCS' not in product['name']:
                    all_img = ';'.join(product['all_images'])
                    db.add(Product(product['id'], product['id_category'], product['name'], product['picture'], all_img, product['price'], product['store_id'], product['store_title'], product['url'], product['orders_count'], product['evaluatescore']))

#print (get_products_list())


db.create_all()
#product1 = Product('123', '44', 'name1', 'http://picture1', 'oter', 123, '123', 'title1', 'http://partner')
#product2 = Product('1234', '44', 'name2', 'http://picture2', 'oter2', 124, '12343', 'title2', 'http://partner')

#db.add(Product('123', '44', 'name1', 'http://picture1', 'oter', 123, '123', 'title1', 'http://partner'))
#db.add(Product('1234', '44', 'name2', 'http://picture2', 'oter2', 124, '12343', 'title2', 'http://partner'))
get_products_list()
db.commit()
#print(db.query(Product).filter_by(product_id="123").first())

