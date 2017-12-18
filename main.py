# -*- coding: utf-8 -*-

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

import os
import json
import urllib2
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
timestr = None
rates = {}

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class LtcExtension(Extension):

    def __init__(self):
        super(LtcExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        # Set timestr as global so we can keep track of time
        global timestr
        # Results to display
        items = []
        # Preferred currency - configurable in the future
        symbol = ('usd', '$')
        # Current script directory
        script_dir = os.path.dirname(os.path.realpath(__file__))
        # URLs for ticker APIs
        # api_name, api_url, json_key
        urls = [
            ('Bitstamp', 'https://www.bitstamp.net/api/v2/ticker/ltc{}'.format(symbol[0]), 'last'),
            ('Bitfinex', 'https://api.bitfinex.com/v1/pubticker/ltc{}'.format(symbol[0]), 'last_price'),
            ('CoinMarketCap', 'https://api.coinmarketcap.com/v1/ticker/litecoin', 'price_{}'.format(symbol[0]))
            ]
        # Loop through the APIs
        for i in range(len(urls)):
            try:
                # Check if we have rates from less than a minute ago
                if timestr != datetime.now().strftime("%Y-%m-%d %H:%M"):
                    req = urllib2.Request(urls[i][1], headers={'User-Agent': 
                        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'})
                    res = urllib2.urlopen(req).read()
                    if len(urls[i]) == 3:
                        rate = float(json.loads(res)[urls[i][2]])
                    elif len(urls[i]) == 4:
                        rate = float(json.loads(res)[urls[i][2]][urls[i][3]])
                    else:
                        # Not enough or too many JSON keys
                        rate = 0
                        continue
                    # Add rate to cached rates dictionary
                    rates[urls[i][0]] = rate
                    # If we've reached the last URL we can set the timestamp again
                    # (a minute has passed and all rates have been set)
                    if i == len(urls)-1:
                        timestr = datetime.now().strftime("%Y-%m-%d %H:%M")
                else:
                    rate = rates[urls[i][0]]
                # Get user input term (expecting number)
                amount = event.get_argument() if event.get_argument() else None
                # Default to 1 LTC
                if not amount:
                    amount = 1
                elif is_number(amount):
                    amount = float(amount)
                else:
                    amount = 1
                # Check if API icon file exists (expecting same name)
                api_icon = os.path.join(script_dir, 'images', '{}.png'.format(urls[i][0].lower()))
                if os.path.isfile(api_icon):
                    icon_path = 'images/{}.png'.format(urls[i][0].lower())
                # Default to extension icon
                else:
                    icon_path = 'images/icon.png'
                items.append(ExtensionResultItem(icon=icon_path,
                                                 name='{}{:,}'.format(symbol[1], rate*amount),
                                                 description='{}'.format(urls[i][0]),
                                                 on_enter=CopyToClipboardAction(str(rate*amount))))
            except Exception as e:
                logger.debug('Exception occurred: {}'.format(str(e)))
                continue

        return RenderResultListAction(items)

if __name__ == '__main__':
    LtcExtension().run()
