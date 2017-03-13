# -*- coding: utf-8 -*-
import logging

from .scales import RadzinksyRiskScale
from hippocrates.blueprints.risar.models.radzinsky_risks import RisarRadzinskyRisks
from hippocrates.blueprints.risar.lib.chart import get_latest_pregnancy_event
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from nemesis.models.enums import RadzinskyRiskRate
from nemesis.systemwide import db
from nemesis.signals import patient_saved


logger = logging.getLogger('simple')


def get_radz_risk(event, create=False):
    radz_risk = db.session.query(RisarRadzinskyRisks).filter(
        RisarRadzinskyRisks.event_id == event.id
    ).first()
    if radz_risk is None and create:
        radz_risk = RisarRadzinskyRisks(event=event, event_id=event.id)
        db.session.add(radz_risk)
    return radz_risk


def get_radz_risk_rate(radz_risk):
    return RadzinskyRiskRate(radz_risk.risk_rate_id) if radz_risk.risk_rate_id else None


def reevaluate_radzinsky_risks(card):
    scale = RadzinksyRiskScale(card, card.radz_risk)
    scale.reevaluate()


def get_event_radzinsky_risks_info(card):
    scale = RadzinksyRiskScale(card, card.radz_risk)
    return scale.get_risks_info()


def on_patient_info_saved(sender, client_id, **extra):
    event = get_latest_pregnancy_event(client_id)
    if event:
        card = PregnancyCard.get_for_event(event)
        if card.attrs:
            reevaluate_radzinsky_risks(card)
            db.session.commit()


patient_saved.connect(on_patient_info_saved)
