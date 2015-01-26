# -*- encoding: utf-8 -*-
from sphinxit.core.helpers import BaseSearchConfig
from sphinxit.core.nodes import Count, OR, RawAttr
from sphinxit.core.processor import Search, Snippet
from config import DEBUG, SEARCHD_CONNECTION


class SearchConfig(BaseSearchConfig):
    DEBUG = DEBUG
    WITH_META = True
    WITH_STATUS = DEBUG
    if SEARCHD_CONNECTION:
        SEARCHD_CONNECTION = SEARCHD_CONNECTION


class SearchPerson():

    @staticmethod
    def search(name):
        search = Search(indexes=['person'], config=SearchConfig)
        search = search.match(name).limit(0, 100)
        result = search.ask()
        return result


class SearchPatient():

    @staticmethod
    def search(name):
        search = Search(indexes=['patient'], config=SearchConfig)
        search = search.match(name).limit(0, 100)
        search = search.options(field_weights={'code': 100,
                                               'lastName': 90,
                                               'birthDate_f1': 80,
                                               'birthDate_f2': 80,
                                               'firstName': 70,
                                               'patrName': 60,
                                               'SNILS': 50,
                                               'document': 50,
                                               'policy': 50})
        #fixme: after sphinxit merge https://github.com/semirook/sphinxit/pull/20
        search = search.order_by('@weight desc, lastName asc, firstName asc, patrName', 'asc')
        result = search.ask()
        return result


class SearchEventService():

    @staticmethod
    def search(query, eventType_id=None, contract_id=None, speciality_id=None):
        search = Search(indexes=['event_service'], config=SearchConfig)
        search = search.match(query)
        if eventType_id:
            search = search.filter(eventType_id__eq=int(eventType_id))
        if contract_id:
            search = search.filter(contract_id__eq=int(contract_id))
        if speciality_id:
            search = search.filter(speciality_id__in=[0, int(speciality_id)])
        search = search.limit(0, 100)
        result = search.ask()
        return result


class SearchEvent():

    @staticmethod
    def search(query):
        search = Search(indexes=['events'], config=SearchConfig)
        search = search.match(query)
        search = search.limit(0, 50)
        result = search.ask()
        return result


if __name__ == '__main__':
    data = SearchPerson.search(u'аллерг')
    data = SearchPatient.search(u'Тапка')
    data = SearchEventService.search(u'11.')