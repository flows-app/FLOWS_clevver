from bs4 import BeautifulSoup
import urllib.request
import http.cookiejar
import json
import datetime
import time
import re
import base64
from urllib.request import Request, urlopen

urllib.request.HTTPHandler(debuglevel=1)
http.client.HTTPConnection.debuglevel = 1

def handler(event, context):
  username = event['account']['username']
  password = event['account']['password']

  if context is not None and context.client_context is not None:
    customcontext = context.client_context.custom
  else:
    customcontext = {"lastvalue":"unkown"}
  
  cj = http.cookiejar.CookieJar()
  opener = urllib.request.build_opener(
      urllib.request.HTTPCookieProcessor(cj),
      urllib.request.HTTPRedirectHandler(),
      urllib.request.HTTPHandler())
  opener.addheaders = [('User-agent', "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36")]

  req = Request('https://eu.clevver.io/customers/auth/login', headers={})
  html = opener.open(req).read()
  postdata = urllib.parse.urlencode({"user_name":username,
                                      "password":password}).encode("utf-8")

  req = Request('https://eu.clevver.io/customers/auth/token',
              data=postdata,
              method='POST')

  response = opener.open(req)
  html = response.read()

  req = Request('https://eu.clevver.io/invoices', headers={})
  html = opener.open(req).read()

  postdata = urllib.parse.urlencode({"_search":"false",
                                    "nd":int(time.time())*1000,
                                    "rows":"",
                                    "page":"1",
                                    "sidx":"",
                                    "sord":"asc"}).encode("utf-8")
  req = Request('https://eu.clevver.io/invoices/load_old_invoice',
    headers={"referer": "https://eu.clevver.io/invoices",
            "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
            "accept": "application/json, text/javascript, */*; q=0.01",
            "origin": "https://eu.clevver.io",
            "x-requested-with": "XMLHttpRequest"},
    data=postdata,
    method='POST')
  response = opener.open(req)

  html = response.read()
  invoices = json.loads(html)
  result_invoices = []

  for entry in invoices['rows']:
    if entry["cell"][1] == "Invoice":
      invoice= {
          "number":entry["cell"][3],
          "date":datetime.datetime.strptime(entry["cell"][2], '%d/%m/%Y').date(),
          "net":(entry["cell"][4])[7:].replace(",","."),
          "price":(entry["cell"][5])[7:].replace(",","."),
          "customer":entry["cell"][8]
        }
      if "lastvalue" in customcontext and invoice['number'] == customcontext['lastvalue']:
        break;
      else:
        print("requesting invoice")
        req = Request('https://eu.clevver.io/invoices/export/'+invoice['number']+'?type=invoice&cusomter_id='+invoice['customer'], headers={})
        iframe_response = opener.open(req).read().decode('utf-8')
        p = re.compile('src="(.[a-z:\/\.0-9A-Z_?=&%]*)')    
        pdf_url = p.findall(iframe_response)[0]
        req = Request(pdf_url)
        pdf_response = opener.open(req).read()
        invoice['pdf'] = base64.b64encode(pdf_response).decode('utf-8')
        result_invoices.append(invoice)
        print(invoice)
  return result_invoices
