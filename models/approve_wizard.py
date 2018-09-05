# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class Approve(models.Model):
    """审核"""
    _name = 'gesion_dms.approve'

    distribution_ids = fields.One2many('gesion_dms_test.doc_distribution', 'approve_id')
    title = fields.Char(string='Title', readonly=False, required=False, translate=False, track_visibility='always')
    remarks = fields.Text(string='Remarks', readonly=False, required=False, translate=False, track_visibility='always')

    @api.multi
    def write(self, values):
        result = super(Approve, self).write(values)
        return result

    def base(self):
        model_data = self.env['ir.model.data']
        model_self = super(Approve, self).read(['title', 'remarks'])[0]
        vals = {}
        vals['pay_id'] = self._context.get('pay_id')
        vals['title'] = model_self['title']
        vals['remarks'] = model_self['remarks']
        vals['addperson'] = self.env.user.id
        vals['adddate'] = fields.Datetime.now()
        vals['status'] = '0'
        return self.env['review.info'].create(vals)

    def agree(self):
        Approve.base(self)
        obj = self.env['gesion_dms_test.doc_distribution']
        if obj.search([('state', '=', 'draft')]):
            obj.search([('state', '=', 'draft')]).write({'state': 'control', 'approve_id': self.id})
            # obj.search([('state', '=', 'control')]).write({'approve_id': self.id})
        elif obj.search([('state', '=', 'control')]):
            obj.search([('state', '=', 'control')]).write({'state': 'approving', 'approve_id': self.id})
        elif obj.search([('state', '=', 'approving')]):
            obj.search([('state', '=', 'approving')]).write({'state': 'review', 'approve_id': self.id})
        else:
            obj.search([('state', '=', 'review')]).write({'state': 'done', 'approve_id': self.id})

        return True

    def refuse(self):
        Approve.base(self)
        obj = self.env['gesion_dms_test.doc_distribution']
        if obj.search([('state', '=', 'control')]):
            obj.search([('state', '=', 'control')]).write({'state': 'draft', 'approve_id': self.id})
        elif obj.search([('state', '=', 'approving')]):
            obj.search([('state', '=', 'approving')]).write({'state': 'control', 'approve_id': self.id})
        else:
            obj.search([('state', '=', 'review')]).write({'state': 'approving', 'approve_id': self.id})
        return True