# -*- coding: utf-8 -*-
# Author: Ray

import os
import json
import base64
import logging

from odoo import _
from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError

from odoo.addons.muk_dms.models import dms_base

_logger = logging.getLogger(__name__)


class FileVersion(dms_base.DMSModel):
    _name = 'gesion_dms.file_version'
    _description = "Gesion File Version"

    _inherit = ['muk_dms.access']

    name = fields.Char('File Version', required=True, index=True)
    file_id = fields.Many2one('muk_dms.file', string='Parent File', ondelete='cascade', readonly=True, required=True)
    settings = fields.Many2one('muk_dms.settings', string="Settings", related='file_id.settings')
    # content = fields.Binary(string='Content', required=True)
    # reference = fields.Reference(selection=[('muk_dms.data', _('Data'))], string="Data Reference")
    extension = fields.Char(string='Extension')
    mimetype = fields.Char(string='Type')
    size = fields.Integer(string='Size')
    md5 = fields.Char(string="MD5")
    content = fields.Binary(
        string='Content',
        required=True,
        compute='_compute_content')
        # inverse='_inverse_content')

    reference = fields.Reference(
        selection=[('muk_dms.data', _('Data'))],
        string="Data Reference",
        readonly=True)

    def _compute_content(self):
        for record in self:
            record.content = record._get_content()

    def _inverse_content(self):
        for record in self:
            if record.content:
                content = record.content
                parent_file = record.file_id
                settings = record.settings if record.settings else parent_file.settings
                reference = record.reference
                if reference:
                    record._update_reference_content(content)
                else:
                    reference = record._create_reference(
                        settings, parent_file.path, record.name, content)
                record.reference = "%s,%s" % (reference._name, reference.id)
                record.size = len(base64.b64decode(content))
            else:
                record._unlink_reference()
                record.reference = None
    # ----------------------------------------------------------
    # Reference
    # ----------------------------------------------------------

    def _create_reference(self, settings, path, filename, content):
        self.ensure_one()
        self.check_access('create', raise_exception=True)
        if settings.save_type == 'database':
            return self.env['muk_dms.data_database'].sudo().create({'data': content})
        return None

    def _update_reference_content(self, content):
        self.ensure_one()
        self.check_access('write', raise_exception=True)
        self.reference.sudo().update({'content': content})

    # def _update_reference_type(self):
    #     self.ensure_one()
    #     self.check_access('write', raise_exception=True)
    #     if self.reference and self.settings.save_type != self.reference.type():
    #         reference = self._create_reference(self.settings, self.directory.path, self.name, self.content)
    #         self._unlink_reference()
    #         self.reference = "%s,%s" % (reference._name, reference.id)

    # def _check_reference_values(self, values):
    #     self.ensure_one()
    #     self.check_access('write', raise_exception=True)
    #     if 'content' in values:
    #         self._update_reference_content(values['content'])
    #     if 'settings' in values:
    #         self._update_reference_type()

    def _get_content(self):
        self.ensure_one()
        self.check_access('read', raise_exception=True)
        return self.reference.sudo().content() if self.reference else None

    def _unlink_reference(self):
        self.ensure_one()
        self.check_access('unlink', raise_exception=True)
        if self.reference:
            self.reference.sudo().delete()
            self.reference.sudo().unlink()
