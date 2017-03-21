# -*- coding: utf-8 -*-
import logging

from .scales import TomskRegionalRiskScale, SaratovRegionalRiskScale
from hippocrates.blueprints.risar.models.radzinsky_risks import (RisarTomskRegionalRisks,
    RisarRegionalRiskRate, RisarSaratovRegionalRisks)
from hippocrates.blueprints.risar.lib.chart import get_latest_pregnancy_event
from hippocrates.blueprints.risar.lib.card import PregnancyCard
from hippocrates.blueprints.risar.lib.specific import SpecificsManager
from nemesis.models.enums import TomskRegionalRiskRate, SaratovRegionalRiskRate
from nemesis.systemwide import db
from nemesis.signals import patient_saved


logger = logging.getLogger('simple')


def get_regional_risk(event, create=False):
    if SpecificsManager.is_region_tomsk():
        return get_tomsk_regional_risk(event, create)
    elif SpecificsManager.is_region_saratov():
        return get_saratov_regional_risk(event, create)


def get_tomsk_regional_risk(event, create=False):
    risk = db.session.query(RisarTomskRegionalRisks).filter(
        RisarTomskRegionalRisks.event_id == event.id
    ).first()
    if risk is None and create:
        risk = RisarTomskRegionalRisks(event=event, event_id=event.id)
        db.session.add(risk)
    return risk


def get_saratov_regional_risk(event, create=False):
    risk = db.session.query(RisarSaratovRegionalRisks).filter(
        RisarSaratovRegionalRisks.event_id == event.id
    ).first()
    if risk is None and create:
        risk = RisarSaratovRegionalRisks(event=event, event_id=event.id)
        db.session.add(risk)
    return risk


def get_regional_risk_rate(event, create=False):
    risk = db.session.query(RisarRegionalRiskRate).filter(
        RisarRegionalRiskRate.event_id == event.id
    ).first()
    if risk is None and create:
        risk = RisarRegionalRiskRate(event=event, event_id=event.id)
        db.session.add(risk)
    return risk


def get_current_region_risk_rate(regional_risk_rate):
    if not regional_risk_rate:
        return None
    if SpecificsManager.is_region_tomsk():
        return TomskRegionalRiskRate(regional_risk_rate.risk_rate_id) if regional_risk_rate.risk_rate_id else None
    elif SpecificsManager.is_region_saratov():
        return SaratovRegionalRiskRate(regional_risk_rate.risk_rate_id) if regional_risk_rate.risk_rate_id else None


def reevaluate_regional_risks(card):
    if SpecificsManager.is_region_tomsk():
        reevaluate_tomsk_regional_risks(card)
    elif SpecificsManager.is_region_saratov():
        reevaluate_saratov_regional_risks(card)


def reevaluate_tomsk_regional_risks(card):
    scale = TomskRegionalRiskScale(card, card.regional_risk, card.regional_risk_rate)
    scale.reevaluate()


def reevaluate_saratov_regional_risks(card):
    scale = SaratovRegionalRiskScale(card, card.regional_risk, card.regional_risk_rate)
    scale.reevaluate()


def get_event_regional_risks_info(card):
    if SpecificsManager.is_region_tomsk():
        scale = TomskRegionalRiskScale(card, card.regional_risk, card.regional_risk_rate)
        return scale.get_risks_info()
    elif SpecificsManager.is_region_saratov():
        scale = SaratovRegionalRiskScale(card, card.regional_risk, card.regional_risk_rate)
        return scale.get_risks_info()


def on_patient_info_saved(sender, client_id, **extra):
    event = get_latest_pregnancy_event(client_id)
    if event:
        card = PregnancyCard.get_for_event(event)
        if card.attrs:
            reevaluate_regional_risks(card)
            db.session.commit()


patient_saved.connect(on_patient_info_saved)
