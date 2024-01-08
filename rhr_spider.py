#
# #scrapy runspider rhr_spider.py  -O rhrnew.json -s CONCURRENT_REQUESTS_PER_DOMAIN=2   -s DOWNLOAD_DELAY=180 
#
import scrapy
import time
import re
import base64
from os.path import exists
from urllib.parse import urlparse
from urllib.parse import parse_qs

RHR_DOMAINNAME = 'romhackraces' + '.' + 'com'


def imagepath_to_d(pathstr):
    oinput = pathstr
    pathstr = pathstr.replace('Images/','')
    pathstr = pathstr.replace('.png', '')
    pathstr = pathstr.replace('AStar','A')
    pathstr = pathstr.replace('IStar','I')
    pathstr = pathstr.replace('Star','S')
    pathstr = pathstr.replace('Block','B')
    if len(pathstr) > 1 or len(pathstr) < 1:
       raise Exception(f"err: pathstr {pathstr} (OINPUT={oinput}) len ne 1")
    return pathstr  



class Spider(scrapy.Spider):
    name = 'hacklist'
    SEASON_LOWER_BOUND = 22
    start_urls = [f'https://{RHR_DOMAINNAME}/levels.php?sort=&season=23']
    allowed_domains = [RHR_DOMAINNAME]
    download_delay = 10

    def parse(self, response):
        parsedurl = urlparse(response.url)
        season = parse_qs(parsedurl.query)['season'][0]
        tables = response.xpath('//span[contains(.,"Week ")]/img[contains(@src,"Images")]/../../../../..')

        for i in range(len(tables)):
             weekspan = tables[i].xpath('.//span[contains(.,"Week")]')
             weekimages_0 = tables[i].xpath('.//span[contains(.,"Week")]/img/@src').extract()
             weekimages_1 = list(map(lambda g: g.replace("Images/",""), weekimages_0))
             weekimages   = list(map(lambda g: g.replace(".png",""), weekimages_1))
             weeknumber   = ''.join(weekimages)
             #
             infodiv = tables[i].xpath('.//div[contains(.,"Levels by")]')
             #levelsby = re.sub(r'^Levels by\s+','',''.join(infodiv.xpath("text()").extract()).strip()) # Author
             infotexts = infodiv.xpath("text()").extract()
             kaizotype = ''
             for ai in range(len(infotexts)):
                 if re.match(r'^Levels by', infotexts[ai].strip()):
                     levelsby = re.sub(r'^Levels by\s+','', infotexts[ai].strip()).strip()
                 if re.match(r'^Intro Kaizo', infotexts[ai]):
                     kaizotype = infotexts[ai].strip()
             if kaizotype == '':
                 kaizotype = infodiv.xpath('span/text()')[1].get()
             #
             difficulty_imagepaths= infodiv.xpath('.//td[contains(.,"Difficulty:")]/following-sibling::td/img/@src').extract()
             difficulty_vector = list(map(imagepath_to_d, difficulty_imagepaths))
             difficulty_stars = len(list(filter(lambda g: g == 'S', difficulty_vector)))
             difficulty_astars = len(list(filter(lambda g: g == 'A', difficulty_vector)))
             difficulty_istars = len(list(filter(lambda g: g == 'I', difficulty_vector)))
             difficulty_blocks = len(list(filter(lambda g: g == 'B', difficulty_vector)))
             # evels/SMW_2023-12-23.bps
             filedate = ''
             #
             download_link_a = infodiv.xpath('../..//a[contains(.,"Download Level Patch")]')
             download_path = ''.join(download_link_a.xpath("@href").extract())

             basegame = ''
 
             matchdate = re.match('.*_(\d+)-(\d+)-(\d+)\.[ib]ps', download_path)
             
             if matchdate:
                    filedate = f'{matchdate.group(1)}-{matchdate.group(2)}-{matchdate.group(3)}'

             if re.match(r'^.*\/SMW_\d+-\d+-\d+.bps$', download_path) or \
                re.match(r'^.*\/SMW_[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+.bps$', download_path) or \
                re.match(r'.*rhr7_3orka_final\.bps$', download_path) or \
                re.match(r'.*Legends of the Hidden Thwimple.bps$', download_path):
                 basegame = 'SuperMarioWorld'
             if re.match(r'^.*\/SMB2_\d+-\d+-\d+.ips$', download_path):
                 basegame = 'SuperMarioBros2'

             as_filename = download_path.split('/')[-1]


             #
             leveltitle = infodiv.xpath('../..//a[contains(.,"Download Level Patch")]/following-sibling::table/tr/td/text()').extract()
             leveltitle = leveltitle[0].strip()
             #twitchvod = infodiv.xpath('../..//a[contains(.,"Twitch VOD")]')
             twitchvod = infodiv.xpath('../../*//*[contains(.,"Twitch VOD")]//following-sibling::iframe[contains(@src,"twitch.tv")]/@src').get()
             dict = {
                  "id": f"rhr_s{season}w{weeknumber}",
                  "name": f"romhackraces_{weeknumber}-{leveltitle}",
                  "basegame": basegame,
                  "author": f"{levelsby}",
                  "authors": f"{levelsby}",
                  "download_url": f"https://{RHR_DOMAINNAME}/{download_path}",
                  "patch_filename" : as_filename,
                  "name_href": f"https://{RHR_DOMAINNAME}/{download_path}",
                  "author_href": "",
                  "demo": "no",
                  "racelevel": "yes",
                  "contest" : "no",
                  "url": f"{response.url}",
                  "added": f"{filedate}",
                 "type": f"Intermediate {kaizotype}",
                 "rhrstars": { "stars": difficulty_stars,
                      "astars": difficulty_astars,
                     "istars": difficulty_istars, "blocks": difficulty_blocks,
                     "difficulty_string": ','.join(difficulty_vector)
                },
                "tags": [ "rhr", "races", "racelevel", kaizotype ],
                "description": f"Season {season} Romhackraces week {weeknumber} race level\n\n",
                "length": "1 exit(s)"
             }
             yield dict

        if int(season) > 1 and int(season)-1 >= self.SEASON_LOWER_BOUND : 
            time.sleep(3)
            next_page_url = f'https://{RHR_DOMAINNAME}/levels.php?sort=&season={int(season)-1}'
            print('next_page_url: ' + next_page_url)
            request = scrapy.Request(url=next_page_url)
            yield request
                



