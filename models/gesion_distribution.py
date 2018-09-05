# -*- coding: utf-8 -*-
# Author: Ray
import datetime
import hashlib

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging

from odoo.addons.muk_dms.models import dms_base

_logger = logging.getLogger(__name__)
_schema = logging.getLogger(__name__ + '.schema')


class Distribution(dms_base.DMSModel):   # 分发单
    _name = 'gesion_dms_test.doc_distribution'
    _description = "Gesion Documents Distribution"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def get_employee(self):
        obj = self.env['hr.employee']
        idsobj = obj.search([('user_id', '=', self.env.user.id)])
        res = idsobj.read()
        return res and res[0]['id'] or 0

    now_time = fields.Datetime(string='Current Time', default=fields.Datetime.now)
    addperson = fields.Many2one('hr.employee', string='Executive Reviewer',  default=lambda self: self.get_employee(), track_visibility='always')
    control = fields.Many2one('hr.employee', string='Document Control Read', track_visibility='always')
    manager = fields.Many2one('hr.employee', string='Manager Approver', track_visibility='always')
    # distribution_name = fields.Char('Distribution Name', required=True, translate=True)
    # distribution_number = fields.Char(string='Distribution Number', required=True)
    # distribution_description = fields.Text(string='Distribution Description', required=True, translate=True)

    approve_id = fields.Many2one('gesion_dms.approve')

    # organization info
    organization_id = fields.Many2one('gesion.organization', string='Organization')
    organization_no = fields.Char(related='organization_id.organization_number', string='Organization No')
    title = fields.Char(string='Title', related='approve_id.title')
    remarks = fields.Text(string='Remarks', related='approve_id.remarks')

    # sender info
    sender_id = fields.Many2one('hr.employee', string='Sender', track_visibility='always')
    positon_id = fields.Many2one('hr.job', string='Position')

    # receiver list
    receiver_list = fields.One2many('reciver.list', 'doc_distribution_id', required=True,  track_visibility='always')
    doc_list = fields.Many2many('muk_dms.file', 'distribution_file_rel', 'file_id', 'distribution')
    review_id = fields.One2many('review.info', 'pay_id', copy=True)

    state = fields.Selection([('draft', 'Draft'), ('control', 'Document Control Approval'), ('approving', 'General Manager Approval'), ('review', 'Executive Review'),
                              ('done', 'Distribution Completed')], string='State', default='draft', track_visibility='always')

    @api.model
    def create(self, vals):
        result = super(Distribution, self).create(vals)
        return result

    @api.multi
    def write(self, values):
        result = super(Distribution, self).write(values)
        return result

    @api.multi
    def unlink(self):
        return super(Distribution, self).unlink()

    @api.multi
    def copy(self, default=None):
        return super(Distribution, self).copy(default)

    @api.multi
    def search(self, args, offset=0, limit=None, order=None, context=None, count=False):
        domain = None
        domain = [('state', '=', '0')]
        return super(Distribution, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def _onchage_organization(self):
        for r in self:
            self._cr.execute('select organization_number from gesion_organization where id =%s', (r.id,))
            res = self._cr.fetchone()
            self.organization_no = res
            self.env['gesion_dms_test.doc_distribution'].write({'self.organization_no': res})


class ReceiverList(dms_base.DMSModel):
    _name = 'reciver.list'

    doc_distribution_id = fields.Many2one('gesion_dms_test.doc_distribution')

    reveiver_ids = fields.Many2one('hr.employee', string='Reciver')
    discipline_id = fields.Many2one('project.discipline', string='Discipline')
    positon_id = fields.Many2one('hr.job', string='Position')
    remarks = fields.Char(string='Remarks')


class ReviewInfo(models.Model):
    _name = 'review.info'

    def get_employee(self, cr, uid, context={}):
        obj = self.pool.get('hr.employee')
        ids = obj.search(cr, uid, [('user_id', '=', uid)])
        res = obj.read(cr, uid, ids, ['id', 'name'], context)
        return res and res[0]['id'] or 0

    pay_id = fields.Many2one('gesion_dms_test.doc_distribution', required=True, index=True, copy=False)

    title = fields.Char(u'标题', readonly=False, required=False, translate=False)
    remarks = fields.Text(u'备注', readonly=False, required=False, translate=False)
    addperson = fields.Many2one('hr.employee', u'审批人', readonly=False, required=False, translate=False)
    submitdate = fields.Datetime(u'提交时间', readonly=False, required=False, translate=False, default=fields.Datetime.now)
    adddate = fields.Datetime(u'处理时间', readonly=False, required=False, translate=False)
    status = fields.Selection([('0', u'同意'), ('1', u'驳回')], u'结果', readonly=False, required=False, translate=False)

    @api.model
    def create(self, vals):
        result = super(ReviewInfo, self).create(vals)
        return result

    @api.multi
    def write(self, values):
        result = super(ReviewInfo, self).write(values)

        return result

    @api.multi
    def unlink(self):
        return super(ReviewInfo, self).unlink()

    @api.multi
    def copy(self, default=None):
        return super(ReviewInfo, self).copy(default)

    @api.multi
    def search(self, args, offset=0, limit=None, order=None, context=None, count=False):
        domain = None
        domain = [('state', '=', '0')]
        return super(ReviewInfo, self).search(args, offset=offset, limit=limit, order=order, count=count)
