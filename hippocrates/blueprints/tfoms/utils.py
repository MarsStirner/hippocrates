# -*- encoding: utf-8 -*-
import re

from nemesis.systemwide import db
from nemesis.utils import create_config_func
from .models import TagsTree
from .models import ConfigVariables
from .config import MODULE_NAME


def save_template_tag_tree(data, current_template_id):
    """
        Сохранение изменений в уже существующем шаблоне
    """
    new_tags = {}
    for item in data:
        match = re.match(r'tag\[(\d+),(\d+)\]', item[0])
        if match:
            parent_id, ordernum = item[1].split(',')
            tag_id = match.group(1)
            if parent_id == u'None':
                parent_id = None
            else:
                parent_id = int(parent_id)
            tag_tree_item = TagsTree.query.filter_by(id=int(tag_id)).first()
            tag_tree_item.parent_id = parent_id
            tag_tree_item.ordernum = int(ordernum)
            db.session.commit()

        match = re.match(r'tag\[None,(\d+)\]', item[0])  #добавление нового тега в шаблон
        if match:
            parent_id, ordernum = item[1].split(',')
            parent_id_t = re.match(r't(\d+)', parent_id)
            if parent_id_t:
                if parent_id_t.group(1) not in new_tags:
                    new_tag_tree_item = TagsTree(tag_id=int(parent_id_t.group(1)),
                                                 parent_id=None,
                                                 template_id=current_template_id, ordernum=ordernum)
                    db.session.add(new_tag_tree_item)
                    db.session.commit()
                    new_tags[parent_id_t.group(1)] = new_tag_tree_item.id

                if match.group(1) not in new_tags:
                    new_tag_tree_item = TagsTree(tag_id=int(match.group(1)),
                                                 parent_id=new_tags[parent_id_t.group(1)],
                                                 template_id=current_template_id, ordernum=ordernum)
                    db.session.add(new_tag_tree_item)
                    db.session.commit()
                    new_tags[match.group(1)] = new_tag_tree_item.id
                else:
                    new_tag_tree_item = TagsTree.query.filter_by(id=new_tags[match.group(1)]).first()
                    new_tag_tree_item.parent_id = new_tags[parent_id_t.group(1)]
                    db.session.commit()
            elif parent_id != u'None':
                if match.group(1) not in new_tags:
                    new_tag_tree_item = TagsTree(tag_id=int(match.group(1)), parent_id=int(parent_id),
                                                 template_id=current_template_id, ordernum=ordernum)
                    db.session.add(new_tag_tree_item)
                    db.session.commit()
                    new_tags[match.group(1)] = new_tag_tree_item.id
                else:
                    new_tag_tree_item = TagsTree.query.filter_by(id=new_tags[match.group(1)]).first()
                    new_tag_tree_item.parent_id = int(parent_id)
                    db.session.commit()
            else:  # случай dbf
                new_tag_tree_item = TagsTree(tag_id=int(match.group(1)), parent_id=None,
                                             template_id=current_template_id, ordernum=ordernum)
                db.session.add(new_tag_tree_item)
                db.session.commit()

        match = re.match(r'removedtag\[(\d+),(\d+)\]', item[0])
        if match:
            removed_tag_tree_item = TagsTree.query.filter_by(id=match.group(1)).first()
            db.session.delete(removed_tag_tree_item)
            db.session.commit()


def save_new_template_tree(template_id, data):
    """
        Сохранение дерева тегов для нового шаблона
    """
    existing_tags = {}

    for item in data:
        match = re.match(r'tag\[(\d+),(\d+)\]', item[0])
        if match:
            standart_parent_id, ordernum = item[1].split(',')
            if standart_parent_id != 'None' and standart_parent_id not in existing_tags:
                new_parent = TagsTree(tag_id=None, template_id=template_id)
                db.session.add(new_parent)
                db.session.commit()
                new_parent_id = new_parent.id
                existing_tags[standart_parent_id] = new_parent_id
            if match.group(1) not in existing_tags:
                if standart_parent_id == 'None':
                    new_tag_tree_item = TagsTree(tag_id=int(match.group(2)), parent_id=None,
                                                 template_id=template_id, ordernum=ordernum)
                else:
                    new_tag_tree_item = TagsTree(tag_id=int(match.group(2)),
                                                 parent_id=existing_tags[standart_parent_id],
                                                 template_id=template_id, ordernum=ordernum)
                db.session.add(new_tag_tree_item)
                db.session.commit()
                existing_tags[match.group(1)] = new_tag_tree_item.id
            else:
                new_tag_tree_item = TagsTree.query.filter_by(id=existing_tags[match.group(1)]).first()
                if standart_parent_id == 'None':
                    new_tag_tree_item.parent_id = None
                else:
                    new_tag_tree_item.parent_id = existing_tags[standart_parent_id]
                new_tag_tree_item.tag_id = int(match.group(2))
                new_tag_tree_item.ordernum = ordernum
                db.session.commit()


_config = create_config_func(MODULE_NAME, ConfigVariables)