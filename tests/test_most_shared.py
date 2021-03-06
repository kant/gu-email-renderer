import unittest
import urlparse
from ophan_calls import MostSharedFetcher
from data_source import MostSharedDataSource, MostSharedCountInterpolator

OphanResponse = """
[{"hits":24037,"hitsPerMin":16,"mobilePercent":66,"onwardContent":0,"onwardOther":0,"path":"/lifeandstyle/2012/feb/01/top-five-regrets-of-the-dying","percent":4.096110424743322,"topReferrers":[{"count":10536,"url":"www.facebook.com"},{"count":7395,"url":"native-app.facebook.com"},{"count":5761,"url":"m.facebook.com"},{"count":298,"url":"t.co"},{"count":43,"url":"www.linkedin.com"},{"count":2,"url":"www.reddit.com"},{"count":2,"url":"plus.url.google.com"},{"count":0,"url":"(unknown)"}]},{"hits":19086,"hitsPerMin":13,"mobilePercent":14,"onwardContent":0,"onwardOther":0,"path":"/world/2013/jun/03/turkey-new-york-times-ad","percent":3.2524176713671027,"topReferrers":[{"count":14307,"url":"www.reddit.com"},{"count":2286,"url":"www.facebook.com"},{"count":1375,"url":"t.co"},{"count":697,"url":"native-app.facebook.com"},{"count":410,"url":"m.facebook.com"},{"count":10,"url":"plus.url.google.com"},{"count":1,"url":"www.linkedin.com"},{"count":0,"url":"(unknown)"}]}]
"""

comment_count_list = [("http://www.theguardian.com/commentisfree/2013/apr/14/thatcher-ding-dong-bbc-charlie-brooker", 49723), ("http://www.theguardian.com/music/2013/apr/14/justin-bieber-anne-frank-belieber", 27556)]
api_data = ["mr", "big", "cheese"]

class IdRememberingMultiContentDataSourceStub(object):
    def __init__(self, client):
        self.fields = []
        self.content_ids = None
        self.fetch_all_was_called = False

    def fetch_data(self):
        self.fetch_all_was_called = True;
        return api_data


class StubClient(object):
    base_url = 'base'
    actual_url = None
    api_key = "iamakeyandigetinforfree"

    def do_get(self, url):
        self.actual_url = url
        return ('headers', OphanResponse)


class StubMostSharedFetcher(object):
    def __init__(self):
        self.most_shared_urls_with_counts = comment_count_list
    def fetch_most_shared(self, age=86400):
        self.age = age
        return self.most_shared_urls_with_counts


class SharedCountInterpolator(object):
    def interpolate(self, comment_count_list, content_list):
        self.content_list = content_list
        self.comment_count_list = comment_count_list
        return 'Interpolated content'

class TestMostSharedUrlBuilding(unittest.TestCase):

    def setUp(self):
        self.stub_client = StubClient()
        self.fetcher = MostSharedFetcher(self.stub_client)

    def test_should_be_able_to_specify_countries_in_most_popular(self):
        fetcher = MostSharedFetcher(self.stub_client, country='us')
        params = fetcher.build_params(120)

        self.assertTrue('country' in params, 'Country not present in params')
        self.assertEquals('us', params['country'])

    def test_should_be_able_to_specify_a_section_in_most_popular(self):
        target_section = 'commentisfree'
        fetcher = MostSharedFetcher(self.stub_client, section=target_section)
        params = fetcher.build_params(120)

        self.assertTrue('section' in params, 'Section is not present in the params')
        self.assertEquals(target_section, params['section'])

    def test_should_build_correct_url_for_ophan_call(self):

        self.fetcher.fetch_most_shared(age=12000)

        parsed_url = urlparse.urlparse(self.stub_client.actual_url)
        self.assertEquals(parsed_url[2], 'base/api/viral')

        params = urlparse.parse_qs(parsed_url[4])

        for key, value in [('mins', '200'),
            ('referrer', 'social media'),
            ('api-key', 'iamakeyandigetinforfree'),]:
            self.assertTrue(key in params, "{key} not present in parameters: {param_string}".format(key=key,
                param_string=params.keys()))
            self.assertEquals(value, params[key][0])

class TestMostShared(unittest.TestCase):
    def test_most_shared_fetcher_should_return_list_of_paths_and_share_counts(self):
        stub_client = StubClient()
        fetcher = MostSharedFetcher(stub_client)
        actual_data = fetcher.fetch_most_shared(age=12000)

        expected_data = [(u'/lifeandstyle/2012/feb/01/top-five-regrets-of-the-dying', 24037),
                         (u'/world/2013/jun/03/turkey-new-york-times-ad', 19086)]
        self.assertEquals(expected_data, actual_data)

    def test_should_fetch_each_piece_of_content_from_api(self):
        multi_content_data_source = IdRememberingMultiContentDataSourceStub('client')
        most_shared_fetcher = StubMostSharedFetcher()
        shared_count_interpolator = SharedCountInterpolator()

        data_source = MostSharedDataSource(n_items=23,
            multi_content_data_source=multi_content_data_source,
            most_shared_fetcher=most_shared_fetcher,
            shared_count_interpolator=shared_count_interpolator
        )
        data_source.fetch_data()
        self.assertTrue(multi_content_data_source.fetch_all_was_called)

    def test_should_return_interpolated_content(self):
        multi_content_data_source = IdRememberingMultiContentDataSourceStub('client')
        most_shared_fetcher = StubMostSharedFetcher()
        shared_count_interpolator = SharedCountInterpolator()

        data_source = MostSharedDataSource(n_items=23,
            multi_content_data_source=multi_content_data_source,
            most_shared_fetcher=most_shared_fetcher,
            shared_count_interpolator=shared_count_interpolator
        )
        data = data_source.fetch_data()
        self.assertEquals(list('Interpolated content'), data)

    def test_should_should_set_a_list_of_paths_on_multi_content_data_source(self):
        multi_content_data_source = IdRememberingMultiContentDataSourceStub('client')
        most_shared_fetcher = StubMostSharedFetcher()
        shared_count_interpolator = SharedCountInterpolator()

        data_source = MostSharedDataSource(n_items=23,
            multi_content_data_source=multi_content_data_source,
            most_shared_fetcher=most_shared_fetcher,
            shared_count_interpolator=shared_count_interpolator
        )
        expected_content_ids = ["/commentisfree/2013/apr/14/thatcher-ding-dong-bbc-charlie-brooker", "/music/2013/apr/14/justin-bieber-anne-frank-belieber"]
        data_source.fetch_data()
        self.assertListEqual(expected_content_ids,multi_content_data_source.content_ids)

    def test_should_call_interpolator_with_shared_counts_and_content_list(self):
        multi_content_data_source = IdRememberingMultiContentDataSourceStub('client')
        most_shared_fetcher = StubMostSharedFetcher()
        shared_count_interpolator = SharedCountInterpolator()

        data_source = MostSharedDataSource(n_items=23,
            multi_content_data_source=multi_content_data_source,
            most_shared_fetcher=most_shared_fetcher,
            shared_count_interpolator=shared_count_interpolator
        )
        data_source.fetch_data()
        self.assertEquals(api_data, shared_count_interpolator.content_list)
        self.assertEquals(comment_count_list, shared_count_interpolator.comment_count_list)

class TestMostSharedInterpolator(unittest.TestCase):
    def test_should_interpolate_share_counts_into_content(self):

        content_list = [
            {
                "id": "id_1",
                "sectionId": "cif",
                "sectionName": "cif name",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/anthony-weiner-wife-huma-abedin",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/anthony-weiner-wife-huma-abedin",
                "fields": {
                    "trailText": "happy trails",
                    "standfirst": "Stand pipe",
                    "shortUrl": "http://gu.com/p/3f1xj",
                    "thumbnail": "well thumbed",
                    "byline": "Branch line",
                    }},
            {
                "id": "id_2",
                "sectionId": "cif",
                "sectionName": "cif name",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/boston-bomb",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/boston-bomb",
                "fields": {
                    "trailText": "happy trails",
                    "standfirst": "Stand pipe",
                    "shortUrl": "http://gu.com/p/3f2xj",
                    "thumbnail": "well thumbed 2",
                    "byline": "Branch line 2",
                    }},
            {
                "id": "id_3",
                "sectionId": "cif 3",
                "sectionName": "cif name 3",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/iain-duncan-smith-exposed-as-popper-sniffer",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/iain-duncan-smith-exposed-as-popper-sniffer",
                "fields": {
                    "trailText": "happy trails 3",
                    "standfirst": "Stand pipe",
                    "shortUrl": "http://gu.com/p/3f3xj",
                    "thumbnail": "well thumbed",
                    "byline": "Branch line",
                    }},
            {
                "id": "id_4",
                "sectionId": "cif 4",
                "sectionName": "cif name",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/monbiot-declarers-he-is-god",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/monbiot-declarers-he-is-god",
                "fields": {
                    "trailText": "happy trails 4",
                    "standfirst": "Stand pipe 4",
                    "shortUrl": "http://gu.com/p/3f4xj",
                    "thumbnail": "well thumbed",
                    "byline": "Branch line",
                    }}]

        shared_count_list = [('http://www.theguardian.com/commentisfree/2013/apr/12/anthony-weiner-wife-huma-abedin', 99), ('http://www.theguardian.com/commentisfree/2013/apr/12/boston-bomb', 3), ('http://www.theguardian.com/commentisfree/2013/apr/12/iain-duncan-smith-exposed-as-popper-sniffer', 28), ('http://www.theguardian.com/commentisfree/2013/apr/12/monbiot-declarers-he-is-god', 102)]

        expected_interpolated_content = [
            {
                "share_count": 99,
                "id": "id_1",
                "sectionId": "cif",
                "sectionName": "cif name",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/anthony-weiner-wife-huma-abedin",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/anthony-weiner-wife-huma-abedin",
                "fields": {
                    "trailText": "happy trails",
                    "standfirst": "Stand pipe",
                    "shortUrl": "http://gu.com/p/3f1xj",
                    "thumbnail": "well thumbed",
                    "byline": "Branch line",
                    }},
            {
                "share_count": 3,
                "id": "id_2",
                "sectionId": "cif",
                "sectionName": "cif name",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/boston-bomb",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/boston-bomb",
                "fields": {
                    "trailText": "happy trails",
                    "standfirst": "Stand pipe",
                    "shortUrl": "http://gu.com/p/3f2xj",
                    "thumbnail": "well thumbed 2",
                    "byline": "Branch line 2",
                    }},
            {
                "share_count": 28,
                "id": "id_3",
                "sectionId": "cif 3",
                "sectionName": "cif name 3",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/iain-duncan-smith-exposed-as-popper-sniffer",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/iain-duncan-smith-exposed-as-popper-sniffer",
                "fields": {
                    "trailText": "happy trails 3",
                    "standfirst": "Stand pipe",
                    "shortUrl": "http://gu.com/p/3f3xj",
                    "thumbnail": "well thumbed",
                    "byline": "Branch line",
                    }},
            {
                "share_count": 102,
                "id": "id_4",
                "sectionId": "cif 4",
                "sectionName": "cif name",
                "webPublicationDate": "2013-04-12T14:15:00Z",
                "webTitle": "Why I wish Huma Abedin had left Anthony Weiner in the dust | Jill Filipovic",
                "webUrl": "http://www.theguardian.com/commentisfree/2013/apr/12/monbiot-declarers-he-is-god",
                "apiUrl": "http://content.guardianapis.com/commentisfree/2013/apr/12/monbiot-declarers-he-is-god",
                "fields": {
                    "trailText": "happy trails 4",
                    "standfirst": "Stand pipe 4",
                    "shortUrl": "http://gu.com/p/3f4xj",
                    "thumbnail": "well thumbed",
                    "byline": "Branch line",
                    }}]

        interpolator = MostSharedCountInterpolator()
        interpolated_data = interpolator.interpolate(content_list=content_list, shared_count_list=shared_count_list)
        self.maxDiff = None
        self.assertListEqual(expected_interpolated_content, interpolated_data)







