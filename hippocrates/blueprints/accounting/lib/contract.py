# -*- coding: utf-8 -*-

import datetime

from sqlalchemy import or_

from nemesis.systemwide import db
from nemesis.models.accounting import Contract, rbContractType, Contract_Contragent, ContractContingent
from nemesis.models.refbooks import rbFinance
from nemesis.models.client import Client
from nemesis.models.organisation import Organisation
from nemesis.models.enums import ContragentType
from nemesis.lib.utils import safe_int, safe_date, safe_unicode, safe_traverse


class BaseModelController(object):

    def __init__(self):
        self.session = db.session

    def get_selecter(self, args):
        raise NotImplementedError()

    def get_listed_data(self, args):
        selecter = self.get_selecter(args)
        selecter.apply_filter(**args)
        selecter.apply_sort_order(**args)
        listed_data = selecter.get_all()
        return listed_data

    def get_paginated_data(self, args):
        per_page = safe_int(args.get('per_page')) or 20
        page = safe_int(args.get('page')) or 1
        selecter = self.get_selecter(args)
        paginated_data = selecter.paginate(page, per_page)
        return paginated_data

    def store(self, *entity_list):
        self.session.add_all(entity_list)
        self.session.commit()


class ContractController(BaseModelController):

    def __init__(self):
        super(ContractController, self).__init__()
        self.contragent_ctrl = ContragentController()
        self.contingent_ctrl = ContingentController()

    def get_selecter(self, args):
        return ContractSelecter()

    def get_new_contract(self, params=None):
        if params is None:
            params = {}
        now = datetime.datetime.now()
        contract = Contract()
        contract.date = now
        contract.begDate = now
        finance_id = safe_int(params.get('finance_id'))
        if finance_id:
            contract.finance = self.session.query(rbFinance).filter(rbFinance.id == finance_id).first()
        contract.deleted = 0

        contract.payer = self.contragent_ctrl.get_new_contragent()
        contract.recipient = self.contragent_ctrl.get_new_contragent()

        contract.contingent = []
        return contract

    def get_contract(self, contract_id):
        contract = self.session.query(Contract).get(contract_id)
        return contract

    def update_contract(self, contract, json_data):
        json_data = self._format_contract_data(json_data)
        for attr in ('number', 'date', 'begDate', 'endDate', 'finance', 'contract_type', 'resolution', ):
            if attr in json_data:
                setattr(contract, attr, json_data.get(attr))
        self.update_contract_ca_payer(contract, json_data['payer'])
        self.update_contract_ca_recipient(contract, json_data['recipient'])
        return contract

    def update_contract_ca_payer(self, contract, ca_data):
        contragent_id = safe_traverse(ca_data, 'id')
        if contragent_id:
            ca_payer = self.contragent_ctrl.get_contragent(contragent_id)
        else:
            ca_payer = self.contragent_ctrl.update_contragent(contract.payer, ca_data)
        contract.payer = ca_payer
        return ca_payer

    def update_contract_ca_recipient(self, contract, ca_data):
        contragent_id = safe_traverse(ca_data, 'id')
        if contragent_id:
            ca_recipient = self.contragent_ctrl.get_contragent(contragent_id)
        else:
            ca_recipient = self.contragent_ctrl.update_contragent(contract.recipient, ca_data)
        contract.recipient = ca_recipient
        return ca_recipient

    def _format_contract_data(self, data):
        finance_id = safe_traverse(data, 'finance', 'id')
        contract_type_id = safe_traverse(data, 'contract_type', 'id')
        data['number'] = data['number']
        data['date'] = safe_date(data['date'])
        data['begDate'] = safe_date(data['beg_date'])
        data['endDate'] = safe_date(data['end_date'])
        data['finance'] = self.session.query(rbFinance).get(finance_id)
        data['contract_type'] = self.session.query(rbContractType).get(contract_type_id)
        data['resolution'] = safe_unicode(data['resolution'])
        return data


class ContragentController(BaseModelController):

    def get_selecter(self, args):
        return ContragentSelecter()

    def get_new_contragent(self, params=None):
        if params is None:
            params = {}
        ca = Contract_Contragent()
        ca.deleted = 0
        return ca

    def get_contragent(self, ca_id):
        ca = self.session.query(Contract_Contragent).get(ca_id)
        return ca

    def update_contragent(self, contragent, json_data):
        json_data = self._format_contragent_data(json_data)
        contragent.client = json_data['client']
        contragent.org = json_data['org']
        return contragent

    def _format_contragent_data(self, data):
        client_id = safe_traverse(data, 'client', 'id')
        org_id = safe_traverse(data, 'org', 'id')
        data = {
            'client': self.session.query(Client).filter(Client.id == client_id).first() if client_id else None,
            'org': self.session.query(Organisation).filter(Organisation.id == org_id).first() if org_id else None
        }
        return data


class ContingentController(BaseModelController):

    def get_new_contingent(self, params=None):
        if params is None:
            params = {}
        cont = ContractContingent()
        cont.deleted = 0
        return cont

    # def get_contragent(self, ca_id):
    #     ca = self.session.query(Contract_Contragent).get(ca_id)
    #     return ca
    #
    # def update_contragent(self, contragent, json_data):
    #     json_data = self._format_contragent_data(json_data)
    #     contragent.client = json_data['client']
    #     contragent.org = json_data['org']
    #     return contragent
    #
    # def _format_contragent_data(self, data):
    #     client_id = safe_traverse(data, 'client', 'id')
    #     org_id = safe_traverse(data, 'org', 'id')
    #     data = {
    #         'client': self.session.query(Client).filter(Client.id == client_id).first() if client_id else None,
    #         'org': self.session.query(Organisation).filter(Organisation.id == org_id).first() if org_id else None
    #     }
    #     return data


from flask import abort


class BaseSelecter(object):

    session = db.session

    def __init__(self, query):
        self.query = query

    def apply_filter(self, **flt_args):
        pass

    def apply_sort_order(self, **order_args):
        pass

    def get_all(self):
        return self.query.all()

    def paginate(self, page, per_page=20, error_out=False):
        """Returns `per_page` items from page `page`.  By default it will
        abort with 404 if no items were found and the page was larger than
        1.  This behavor can be disabled by setting `error_out` to `False`.

        Returns an :class:`Pagination` object.
        """
        if error_out and page < 1:
            abort(404)
        items = self.query.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            abort(404)

        # No need to count if we're on the first page and there are fewer
        # items than we expected.
        if page == 1 and len(items) < per_page:
            total = len(items)
        else:
            total = self.query.order_by(None).count()

        return Pagination(self, page, per_page, total, items)


class ContractSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(Contract)
        super(ContractSelecter, self).__init__(query)


class ContragentSelecter(BaseSelecter):

    def __init__(self):
        query = self.session.query(Contract_Contragent)
        super(ContragentSelecter, self).__init__(query)

    def apply_filter(self, **flt_args):
        if 'ca_type_code' in flt_args:
            ca_type_id = ContragentType.getId(flt_args['ca_type_code'])
            if ca_type_id == ContragentType.legal[0]:
                self.query = self.query.join(Organisation)
            elif ca_type_id == ContragentType.individual[0]:
                self.query = self.query.join(Client)
            if 'query' in flt_args:
                query = u'%{0}%'.format(flt_args['query'])
                if ca_type_id == ContragentType.legal[0]:
                    self.query = self.query.filter(or_(
                        Organisation.shortName.like(query),
                        Organisation.fullName.like(query)
                    ))
                elif ca_type_id == ContragentType.individual[0]:
                    self.query = self.query.filter(or_(
                        Client.firstName.like(query),
                        Client.lastName.like(query),
                        Client.patrName.like(query)
                    ))
        return self

    # def apply_sort_order(self, **order_options):
    #     desc_order = order_options.get('order', 'ASC') == 'DESC'
    #     if order_options:
    #         pass
    #     else:
    #         source_action = aliased(Action, name='SourceAction')
    #         self.query = self.query.join(
    #             source_action, EventMeasure.sourceAction_id == source_action.id
    #         ).order_by(
    #             source_action.begDate.desc(),
    #             EventMeasure.begDateTime.desc(),
    #             EventMeasure.id.desc()
    #         )
    #     return self


from math import ceil


class Pagination(object):
    """Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        This is how you could render such a pagination in the templates:

        .. sourcecode:: html+jinja

            {% macro render_pagination(pagination, endpoint) %}
              <div class=pagination>
              {%- for page in pagination.iter_pages() %}
                {% if page %}
                  {% if page != pagination.page %}
                    <a href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                  {% else %}
                    <strong>{{ page }}</strong>
                  {% endif %}
                {% else %}
                  <span class=ellipsis>…</span>
                {% endif %}
              {%- endfor %}
              </div>
            {% endmacro %}
        """
        last = 0
        for num in xrange(1, self.pages + 1):
            if num <= left_edge or \
               (num > self.page - left_current - 1 and \
                num < self.page + right_current) or \
               num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num
