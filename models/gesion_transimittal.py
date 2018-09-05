# -*- coding: utf-8 -*-
# Author: Ray

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging

from odoo.addons.muk_dms.models import dms_base

_logger = logging.getLogger(__name__)
_schema = logging.getLogger(__name__ + '.schema')


class Transimittal(dms_base.DMSModel):   # 传递单
    _name = 'gesion_dms.transimittal'
    _description = "Gesion Documents Transimittal"

    _inherit = ['mail.thread', 'muk_dms.access']

    name = fields.Char('Name', required=True)
    date = fields.Datetime('Create Date', default=fields.Date.context_today, readonly=True)




