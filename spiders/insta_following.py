import scrapy
from scrapy.http import HtmlResponse
import re
import json
from urllib.parse import urlencode
from copy import deepcopy
from instaparser.items import InstaparserItem

class InstaFollowingSpider(scrapy.Spider):
    name = 'insta_following'
    allowed_domains = ['instagram.com']
    start_urls = ['http://instagram.com/']

    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = 'svetochka_petrenko_88'
    inst_pwd = '#PWD_INSTAGRAM_BROWSER:10:'
    users_for_parse = ['doorprw_vyksa', 'cleaning_____house', 'parikmakherskaiazebra']
    api_url = 'https://i.instagram.com/api/v1/friendships/'

    def parse(self, response: HtmlResponse):

        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login,
                      'enc_password': self.inst_pwd},
            headers={'X-CSRFToken': csrf}
        )

    def login(self, response: HtmlResponse):
        j_data = response.json()
        if j_data.get('authenticated'):
            for user_for_parse in self.users_for_parse:
                yield response.follow(
                    f'/{user_for_parse}',
                    callback=self.user_parse,
                    cb_kwargs={'username': user_for_parse}
                )

    def user_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        variables = {'count': 12}
        url_posts = f'{self.api_url}{user_id}/following/?{urlencode(variables)}'

        yield response.follow(url_posts,
                              callback=self.user_followers_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)},
                              headers={'User-Agent': 'Instagram 155.0.0.37.107'}
                              )

    def user_followers_parse(self, response: HtmlResponse, username, user_id, variables):

        j_data = response.json()
        if j_data.get('big_list'):
            variables['max_id'] = int(j_data.get('next_max_id'))
            url_followers = f'{self.api_url}{user_id}/followers/?{urlencode(variables)}'

            yield response.follow(url_followers,
                                  callback=self.user_followers_parse,
                                  cb_kwargs={'username': username,
                                             'user_id': user_id,
                                             'variables': deepcopy(variables)},
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'})

        followers_friends = j_data.get('users')
        for friend in followers_friends:
            item = InstaparserItem(
                user_id=user_id,
                username=username,
                friend_id=friend.get('pk'),
                friend_photo=friend.get('profile_pic_url'),
                friend_username=friend.get('username'),
                friend_full_name=friend.get('full_name'),
                friend_data=friend
            )
            yield item

    def fetch_csrf_token(self, text):
        ''' Get csrf-token for auth '''
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        matched = re.search(
            '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
        ).group()
        return json.loads(matched).get('id')