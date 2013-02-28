import jinja2
import os
import webapp2
import datetime
import math


from google.appengine.api import memcache
from guardianapi.client import Client
from data_source import \
    CultureDataSource, TopStoriesDataSource, SportDataSource, EyeWitnessDataSource, \
    MostViewedDataSource, MediaDataSource, MediaMonkeyDataSource, MediaCommentDataSource, \
    BusinessDataSource, TravelDataSource, TechnologyDataSource, LifeAndStyleDataSource, \
    MusicMostViewedDataSource, MusicNewsDataSource, MusicWatchListenDataSource, \
    MusicBlogDataSource, MusicEditorsPicksDataSource, fetch_all, build_unique_trailblocks
from template_filters import first_paragraph
from ads import AdFetcher

VERSION = str(int(math.floor(float(os.environ['CURRENT_VERSION_ID']))))
URL_ROOT = '' if os.environ['SERVER_SOFTWARE'].startswith('Development') else "http://" + VERSION + ".***REMOVED***.appspot.com"
CACHE_PREFIX = 'V' + VERSION

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "template"))
)

jinja_environment.globals['URL_ROOT'] = URL_ROOT
jinja_environment.filters['first_paragraph'] = first_paragraph
jinja_environment.cache = None

api_key = '***REMOVED***'
base_url = 'http://content.guardianapis.com/'

client = Client(base_url, api_key)
adFetcher = AdFetcher()


class EmailTemplate(webapp2.RequestHandler):
    def template(self):
        return jinja_environment.get_template(self.template_name + '.html')

    def get(self):
        cache_key = CACHE_PREFIX + self.template_name
        page = memcache.get(cache_key)

        if not page:
            retrieved_data = fetch_all(client, self.data_sources)
            trail_blocks = build_unique_trailblocks(3, retrieved_data, self.priority_list)
            today = datetime.datetime.now()
            date = today.strftime('%A %d %b %Y')

            page = self.template().render(ad_html=adFetcher.leaderboard(), date=date, **trail_blocks)
            memcache.add(cache_key, page, 300)

        self.response.out.write(page)


class MediaBriefing(EmailTemplate):

    data_sources = {
        'media_stories': MediaDataSource(),
        'media_comment': MediaCommentDataSource(),
        'media_monkey': MediaMonkeyDataSource()
        }
    priority_list = [('media_stories', 8), ('media_comment', 1), ('media_monkey', 1)]
    template_name = 'media-briefing'


class DailyEmail(EmailTemplate):
    data_sources = {
        'business': BusinessDataSource(),
        'technology': TechnologyDataSource(),
        'travel': TravelDataSource(),
        'lifeandstyle': LifeAndStyleDataSource(),
        'sport': SportDataSource(),
        'culture': CultureDataSource(),
        'top_stories': TopStoriesDataSource(),
        'eye_witness': EyeWitnessDataSource(),
        'most_viewed': MostViewedDataSource(),
        }
    priority_list = [('top_stories', 6), ('most_viewed', 6), ('eye_witness', 1), ('sport', 3),
                     ('culture', 3), ('business', 2),
                     ('technology', 2), ('travel', 2), ('lifeandstyle', 2)]
    template_name = 'daily-email'


class SleeveNotes(EmailTemplate):
    data_sources = {
        'music_most_viewed': MusicMostViewedDataSource(),
        'music_news': MusicNewsDataSource(),
        'music_blog': MusicBlogDataSource(),
        'music_watch_listen': MusicWatchListenDataSource(),
        'music_editors_picks': MusicEditorsPicksDataSource(),
        }
    priority_list = [('music_most_viewed', 3), ('music_news', 5), ('music_blog', 5),
                     ('music_watch_listen', 5), ('music_editors_picks', 3)]
    template_name = 'sleeve-notes'

app = webapp2.WSGIApplication([('/daily-email', DailyEmail),
                               ('/media-briefing', MediaBriefing),
                               ('/sleeve-notes', SleeveNotes)],
                              debug=True)
