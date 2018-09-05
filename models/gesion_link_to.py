# -*- coding: utf-8 -*-
# Author: Ray
from odoo import models, api, fields, _
from odoo.addons.muk_dms.models import dms_base
import logging


_logger = logging.getLogger(__name__)
_schema = logging.getLogger(__name__ + '.schema')


class LinkTo(models.Model): #link to 按钮
    _name = 'link_to.model'

    link_document = fields.One2many('link_to.doc','link_id')




class DocLinkTo(models.Model):
    _name = 'link_to.doc'

    link_id = fields.Many2one('link_to.model')

    link_document_name = fields.Many2one('muk_dms.file',string='Link Document Name')
    link_document_number = fields.Char(string='Link Document Number',related='link_document_name.document_number')
    link_document_title = fields.Char(string='Link Document Title',related='link_document_name.document_title')
    organization_id = fields.Many2one('project.project',string='Orginzation Id')
    master_id = fields.Boolean(string='Master',related='link_document_name.master')
    sub_ordinate_ids = fields.Boolean(string='SubOrdinate',related='link_document_name.sub_ordinate')






