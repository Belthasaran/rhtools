import scrapy
import json
from os.path import exists
from urllib.parse import urlparse
from urllib.parse import parse_qs


class Spider(scrapy.Spider):
    name = 'rhitemdetail'
    #start_urls = [ '/?p=section&a=details&id={rhid}' ]
    i1 = 0

    def __init__(self, *args, **kwargs): 
        super(Spider, self).__init__(*args, **kwargs) 
        self.start_urls = [kwargs.get('start_url')] 
        

    def parse(self, response):
        idtried = None
        parsed_url = urlparse(response.url)
        parseq = parse_qs(parsed_url.query)
        if parseq != None and 'id' in parseq:
            idtried = parseq['id'][0]
            xg = open("tried/" + str(idtried),"w")
            xg.close()
        else:
            pass
        vals = {}
        rows = response.xpath('//table[@class="list"]/tbody/tr')
        for rowi in rows:
            cols   = rowi.xpath('td')
            colst  = rowi.xpath('td//text()')
            fieldname = (colst.extract())[0].lower().split(':')[0]
            fieldtext  = (colst.extract())[1]
            link = cols[1].css('a')
            if len(link) > 0 :
               if 'href' in link.attrib:
                   url = link.attrib['href']
               else:
                   url = ''
               vals[ fieldname + "_href" ] = url
            vals[ fieldname ] = fieldtext
            #rowvals = rowi.xpath('td//text()').extract()
        vals[ "tags" ] = rows.css('.tag').xpath("text()").getall()
        vals[ "rating" ] = rows.css('.rating').xpath("text()").getall()
        vals[ "url" ] = response.url
        parsed_url = urlparse(response.url)
        captured_value = parse_qs(parsed_url.query)['id'][0]
        vals[ "id" ] = str(captured_value)
        yield vals


