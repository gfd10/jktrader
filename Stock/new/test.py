from bs4 import BeautifulSoup
import requests

BaseUrl = 'https://finance.naver.com/'

r = requests.get(BaseUrl)
soup = BeautifulSoup(r.text,'lxml')
items = soup.find_all('dl',{'class':'dl'})
count = 0
for item in items:
    dd = item.text.split()
    print(dd)
    if count == 0:
        kospi = int(dd[1].replace(',','').lstrip('+')), int(dd[4].replace(',','').lstrip('+')), int(dd[7].replace(',','').lstrip('+'))
        print(kospi)
    elif count == 1:
        kosdaq = int(dd[1].replace(',','').lstrip('+')), int(dd[4].replace(',','').lstrip('+')), int(dd[7].replace(',','').lstrip('+'))
    elif count == 2:
        kospi200 = int(dd[1].replace(',','').lstrip('+')), int(dd[4].replace(',','').lstrip('+')), int(dd[7].replace(',','').lstrip('+'))
    count = count + 1

print(kospi, kosdaq, kospi200)