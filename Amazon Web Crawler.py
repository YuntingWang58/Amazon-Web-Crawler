import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
%matplotlib inline
import re
import time
from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import json
import random

def GET_UserAgent():
    uastrings = ["Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.72 Safari/537.36",\
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",\
                "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",\
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.111 Safari/537.36",\
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/600.1.17 (KHTML, like Gecko) Version/7.1 Safari/537.85.10",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",\
                "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:33.0) Gecko/20100101 Firefox/33.0",\
                "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36"\
                ]
 
    return random.choice(uastrings)


def delay() -> None:
    time.sleep(random.uniform(5, 30))
    return None


##################   Get all pagination links  #######################

def get_pagination_link(url):
    headers = {'User-Agent': GET_UA()}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.content, "lxml")
    #  Page Number    
    page_node = soup.select("ul.a-pagination")[0].findAll('li')
    pageNo = len(page_node) - 2
    page_link_list = []
    
    if pageNo > 3:
        # if the totoal number of pagination> 3, all middle pages will be hidden, so the number of pages is li class='a-disabled'. Page link logic should be changed.
        pageNo = soup.select("ul.a-pagination li.a-disabled")[1].get_text()
        
        pagination_node = soup.select("ul.a-pagination")[0].findAll('a')
        # Get the second link and change page number
        second_page_link = pagination_node[1].get('href')
        page_index = second_page_link.find("page=") + 5
        pg_index =  second_page_link.find("pg_") + 3
        
        x = range(1, int(pageNo)+1)
        for i in x:
            page_link = second_page_link[:page_index] + str(i) + second_page_link[page_index+1:]
            page_link = page_link[:pg_index] + str(i)
            page_link_list.append('https://www.amazon.co.uk'+ page_link)                     
    else: 
        # Best seller (Only for 2 paginations)
        pagination_node = soup.select("ul.a-pagination")[0].findAll('a', limit=pageNo)

        for link in pagination_node:
            page_link = link.get('href')
            if  page_link is not None:
                if page_link[:5] == 'https':
                    page_link_list.append(page_link)
                else:
                    page_link_list.append('https://www.amazon.co.uk'+ page_link)
                                    
    return page_link_list

##################   Get all product links from each pagination  #######################

def get_product_link(url):
    # add header
#     headers = {'User-Agent': GET_UA()}
#     headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10) AppleWebKit/600.1.25 (KHTML, like Gecko) Version/8.0 Safari/600.1.25'}
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'}
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}
    content = None
    try:
        r = requests.get(url, headers = headers)
        ct = r.headers['Content-Type'].lower().strip()
        if 'text/html' in ct:
            content = r.content
            soup = BeautifulSoup(content, "lxml")
            if len(soup.select("#zg-center-div li.zg-item-immersion")) != 0 :   # Best sellers page
                links = soup.find_all('a', {'class': 'a-link-normal a-text-normal'})
            elif len(soup.select("div.s-main-slot")) != 0 :   # Amazon deals
                links = soup.find_all('a', {'class': 'a-link-normal a-text-normal'})[1:]
            else :
                links = None 

            link_list = []
            
            if links is not None:
                for link in links:
                    url = 'https://www.amazon.co.uk' + link.get('href')
                    link_list.append(url)
            else:
                print('Cannot find product link.')
    
            return link_list
    
        else:
            content = r.content
            soup = None
            return None
    
    except Exception as e:
        print("Error:", str(e))


####################  Get detailed product information  #######################

def get_product_data(url):
    headers = {'User-Agent': GET_UA()}
    content = None
    try:
        
        r = requests.get(url, headers = headers)
        ct = r.headers['Content-Type'].lower().strip()
        if 'text/html' in ct:
            content = r.content
            soup = BeautifulSoup(content, "lxml")
            productInfo = []
            # 1. Title  #
            title = soup.find('span', attrs={'id':'productTitle'})
            if title is not None:
                title = title.get_text().strip()
            else: 
                title = np.nan
            # 2. ASIN  #
            asin = url.split('/')[5]
            # 3. Categories  #
            categories_node = soup.select("#wayfinding-breadcrumbs_container ul.a-unordered-list")
            if len(categories_node) != 0:
                categories = ''
                i = 0
                for li in categories_node[0].findAll("li"):
                    if i % 2 == 0: # avoid extracting special character (>)
                        categories += li.get_text().strip() + ' '
                    i = i + 1
            else:
                categories = np.nan
            # 4. Brand  #
            brand = soup.find('a', attrs={'id':'bylineInfo'})
            if brand is not None:
                brand = brand.get_text().strip()
            else: 
                brand = np.nan
            # 5. Price  #
            if len(soup.select("#priceblock_ourprice")) != 0:            
                price_node = soup.select("#priceblock_ourprice")
                price = price_node[0].get_text()
            elif len(soup.select("#olp-upd-new-used-freeshipping-threshold span.a-size-base.a-color-price")) != 0 :    
                price_node = soup.select("#olp-upd-new-used-freeshipping-threshold span.a-size-base.a-color-price")
                price = price_node[0].get_text()
            elif len(soup.select("#olp-upd-new-used span.a-size-base.a-color-price")) != 0 : 
                price_node = soup.select("#olp-upd-new-used span.a-size-base.a-color-price")
                price = price_node[0].get_text()
            else:
                price = np.nan                
            # delete currency
            currency = '£'
            if currency in price:
                price = price.replace(currency, '')
            # 6. Colour  #
            color_node = soup.select("#variation_color_name span.selection")
            if len(color_node) != 0:
                color = color_node[0].get_text().strip()
            else:
                color = np.nan    
            # 7. Stock  #
            stock_node = soup.select("#availability span.a-size-medium") 
            if len(stock_node) != 0:
                stock = re.sub(r'[^\w\s]','', stock_node[0].get_text().strip())
            else:
                stock = np.nan 
            # 8. Features  #
            features_node = soup.select("#feature-bullets ul.a-unordered-list")
            if len(features_node) != 0:
                features = ''
                for li in features_node[0].findAll('li'):
                    features += li.get_text().strip() + ' '
            else:
                features = np.nan 
            # 9. Product Description  #
            pd_node = soup.select("#productDescription")
            if len(pd_node) != 0:
                pd = ''
                for p in pd_node[0].findAll('p'):
                    pd += p.get_text().strip() + ' '
            else:
                pd = np.nan 
            # 10. Customer Reviews  #
            reviews_node = soup.select("#acrPopover i.a-icon-star")
            if len(reviews_node) != 0:
                reviews = reviews_node[0].get_text().strip()
            else:
                reviews = np.nan 
            # 11. Number of Reviews  #
            count_node = soup.select("#acrCustomerReviewText")
            if len(count_node) != 0:
                review_count = count_node[0].get_text().split()[0]
            else:
                review_count = np.nan            
            # 12. Link of Prodcut  #           
            link = url           
            # 13. Sizes # 
            sizes_node = soup.select("#native_dropdown_selected_size_name option.dropdownAvailable")
            if len(sizes_node) != 0:
                sizes = sizes_node[0].get_text().strip()
            else:
                sizes = np.nan
            # 14. Weight # 
            weight_node = soup.select("#variation_size_name span.selection")
            if len(weight_node) != 0:
                weight = weight_node[0].get_text().strip()
            else:
                weight = np.nan

            productInfo.append(title)
            productInfo.append(asin)
            productInfo.append(categories)
            productInfo.append(brand)
            productInfo.append(price)
            productInfo.append(color)
            productInfo.append(stock)
            productInfo.append(features)
            productInfo.append(pd)
            productInfo.append(reviews)
            productInfo.append(review_count)
            productInfo.append(link)
            productInfo.append(sizes)
            productInfo.append(weight)

            return productInfo
        else:
            content = r.content
            soup = None
            return None

    except Exception as e:
        print("Error:", str(e))


####################  Get all product links (Call get_pagination_link &  get_product_link) #######################

# Sports & Outdoors URL :
# url = 'https://www.amazon.co.uk/s?i=sports&bbn=3581866031&dc&fst=as%3Aoff&qid=1599740185&ref=lp_3581866031_nr_i_3'

page_link_list = get_pagination_link(url)
page_link_with_error = []
product_link_list = []
for page_link in page_link_list:
    try:
        product_link_list += get_product_link(page_link)
        delay()
    except:
        page_link_with_error.append(page_link)
        
print(len(product_link_list))
print(page_link_with_error)


####################  Get all product information (Call get_product_data) #######################

product_link_with_error = []
results = []
for product_link in product_link_list:
    try:
        product_data = get_product_data(product_link)
        if product_data is not None:
            results.append(product_data)
        delay()
    except:
        product_link_with_error.append(product_link)
df = pd.DataFrame(results,columns=['Title','ASIN','Categories','Brand','Price','Color','Stock','Features','Product Description','Customer Reviews','Number of Reviews','Product URL','Sizes','Weight'])
df.to_csv('amazon_warehouse_Prodcut.csv', index=False, encoding='utf-8')