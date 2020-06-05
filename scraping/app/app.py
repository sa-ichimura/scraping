import requests
import time
import csv
import json
import re
from bs4 import BeautifulSoup

class ShopScraping:
  def __init__(self,domain,headers):
    self.domain = domain
    self.headers = headers

  def item_link(self,DOMAIN,itemLinks):
    for itemLink in itemLinks:
      URL = str(DOMAIN+itemLink.get("href"))
    return URL
  
  def item_details(self,itemDetailLinks):
    time.sleep(1)
    itemCode = []
    itemBrand = []
    item_infomation_dict ={}
    infomation = {}
    
    for code ,itemDetailLink in itemDetailLinks.items():
      itemCode.append(code)
      item_infomation_dict = {code:{}}
      response = requests.get(itemDetailLink, timeout=5, headers=headers)
      response.encoding = response.apparent_encoding 
      soup = BeautifulSoup(response.text, 'html.parser')
      
      itemContents = soup.find_all(class_='p-itemscope')

      #商品の会社か取れているはず
      #しばらくは使わない
      itemBrand.append(self.item(itemContents,'p-brand__name'))

      #商品詳細情報取得
      
      item_infomation_dict[code]=self.item_infomation(itemContents,'p-desc__toggle__main',code)
      infomation.update(item_infomation_dict)
    
    return infomation

  
  def item(self,contents,target):
    for content in contents:
      itemName = content.find(class_=target)
      if itemName is None:
        return 'no-brand'
    return itemName.string
  
  def item_infomation(self,contents,target,code):
    food ={
      'id':code,
      '対象':'',
      '成分':{},
      '特徴':{},
      '量':'',
      '材料':'',
      'サイズ':'',
      'タイプ':''
      }
    ingredients_name=[]
    ingredients_ini=[]

    for content in contents:
      infomatonTables = content.find(class_=target)
      if infomatonTables is None:
        break    
      for features in infomatonTables.find_all('tr'):
        if "対象" in str(features.find('th')):
          if features.find('p') is None:
            food['対象'] = ''
          else:
            target = features.find('p').string
            target_dict=re.split('・|などの',target)
            food['対象'] = dict(zip(range(len(target_dict)), target_dict))

        if "成分" in str(features.find('th')) or '標準分析値' in str(features.find('th')):
          if features.find('p') is None:
            food['成分'] = ''
          else:
            ingredients_list=re.split('、|:',features.find('p').string)
            ingredients_dict=dict(zip(range(len(ingredients_list)), ingredients_list))
            for k, v in ingredients_dict.items():
              if k == 0 or k%2 ==0:
                ingredients_name.append(v)
              else:
                ingredients_ini.append(v)
            ingredients=dict(zip(ingredients_name,ingredients_ini))
            food['成分'] =ingredients

        if "特長" in str(features.find('th')):
          if features.find_all(class_='item') is None:
            food = ''
          else:
            count = 0
            for feature in features.find_all(class_='item'):
              food['特徴'][count] = feature.string
              count +=1
        if "量" in str(features.find('th')):
          if features.find('p') is None:
            food['量'] = ''
          else:
            food['量'] = features.find('p').string

        if "材料" in str(features.find('th')):
          if features.find('p') is None:
            food['材料'] = ''
          else:
            food['材料'] = features.find('p').string    

        if "サイズ" in str(features.find('th')):
          if features.find('p') is None:
            food['サイズ'] = ''
          else:
            food['サイズ'] = features.find('p').string

        if "タイプ" in str(features.find('th')):
          if features.find('p').string is None:
            food['タイプ'] = ''
          else:
            food['タイプ'] = features.find('p').string
    return food

  
DOMAIN = 'https://www.shopping-charm.jp'
headers = {"User-Agent": "your user agent"}

shopScraping = ShopScraping(DOMAIN,headers)



for i in range(5):
  page = str(i)
  URL = "https://www.shopping-charm.jp/category/2c2c2c2c-2c2c-3131-3139-303030303030?page=" + page
  try:
    response = requests.get(URL, timeout=5, headers=headers)


    response.encoding = response.apparent_encoding 
    # textでunicode, contentでstr

    soup = BeautifulSoup(response.text, 'html.parser') #要素を抽出

    itemContents = soup.find_all(class_='p-items__list')

    ResultItemCodes = []
    ResultItemNames = []
    ResultItemPrices = []
    ResultItemLinks =[]
    ResultNameJson = {}
    ResultPriceJson = {}
    ResultLinkJson = {}


    for itemContent in itemContents:
      itemCodes = itemContent.find_all(class_='c-item__code')
      itemNames = itemContent.find_all(class_= 'c-item__name')
      itemPrices = itemContent.find_all(class_='c-price c-item__price')
      itemLinks = itemContent.find_all('a')
      

      ResultItemLinks.append(shopScraping.item_link(DOMAIN,itemLinks))

      for itemName in itemNames:
        s1 = itemName.string
        s2 = s1.replace('\n','')
        s3 = s2.replace('                                        ','')
        strItemName = s3.replace('                                    ','')
        #特定のワードが含まれる商品は除外
        strItemNameFlag = False
        if '+' in strItemName: 
          strItemNameFlag = True                    
          break
        elif 'アウトレット' in strItemName:
          strItemNameFlag = True
          break
        elif '訳あり' in strItemName:
          strItemNameFlag = True
          break
        else:
          ResultItemNames.append(strItemName)    
      if strItemNameFlag is False:
        for itemCode in itemCodes:
          s = itemCode.string
          strItemCode = s.replace('\n','')
          ResultItemCodes.append(strItemCode)
        
        for itemPrice in itemPrices:
          itemPrice.find('span').extract()
          s1 = itemPrice.text
          s2 = s1.replace('\n                                        ','')
          strItemPrice = s2.replace('\n','')
          ResultItemPrices.append(strItemPrice)

      #商品詳細ページのリンク
      ResultLinkJson.update(zip(ResultItemCodes,ResultItemLinks))
      
    time.sleep(1)
    #商品名を格納したdict
    ResultNameJson.update(zip(ResultItemCodes,ResultItemNames))

    #商品金額を格納したdict
    ResultPriceJson.update(zip(ResultItemCodes,ResultItemPrices))
  except requests.exceptions.HTTPError:
    print('アクセスエラー')
    print(URL)
  except Exception as e:
    print(e)

#商品詳細情報を格納したdict
#jsonに書き出してwebアプリケーション側に渡す

'''
ResultLinkJson = {}
ResultLinkJson = {'214332':'https://www.shopping-charm.jp/product/2c2c2c2c-2c2c-2c2c-2c2c-323134333332',
'897317':'https://www.shopping-charm.jp/product/2c2c2c2c-2c2c-2c2c-2c2c-383937333137'}
'''
item_imfomation = shopScraping.item_details(ResultLinkJson)

#webアプリケーションに渡すjsonを作成
with open('infomation.json', 'w') as infomation_write:
  json.dump(item_imfomation,infomation_write,indent=4,ensure_ascii=False)

with open('name.json','w') as name_write:
  json.dump(ResultNameJson,name_write,indent=4,ensure_ascii=False)

with open('price.json','w') as price_write:
  json.dump(ResultPriceJson,price_write,indent=4,ensure_ascii=False)







 
