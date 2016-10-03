import requesocks, requests, BeautifulSoup
import requesocks
from stem import Signal
from stem.control import Controller

def renew_connection():
    with Controller.from_port(port=9151) as controller:
        controller.authenticate(password="password")
        controller.signal(Signal.NEWNYM)

session = requesocks.session()
# Tor uses the 9050 port as the default socks port
session.proxies = {'http':  'socks5://127.0.0.1:9150',
                   'https': 'socks5://127.0.0.1:9150'}
# Make a request through the Tor connection
# IP visible through Tor
print session.get("http://httpbin.org/ip").text
# Above should print an IP different than your public IP
# Following prints your normal public IP
print requests.get("http://httpbin.org/ip").text

renew_connection()
print session.get("http://httpbin.org/ip").text
r = session.get('http://alipromo.com/redirect/product/o4jauozbl5c3jfrcco1droidutid00g4/32417384296/en')
print r.text
#http://stackoverflow.com/questions/30286293/make-requests-using-python-over-tor