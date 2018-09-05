# -*- coding: utf-8 -*-
# Author: Ray

from odoo import models, api, fields, _
from odoo.exceptions import UserError
import logging

from odoo.addons.muk_dms.models import dms_base

_logger = logging.getLogger(__name__)
_schema = logging.getLogger(__name__ + '.schema')


class Organization(models.Model):
    _name = 'gesion.organization'
    _inherit = 'muk_dms.access'
    _description = "Gesion Organization"
    _order = 'name'

    name = fields.Char('Name')
    parent_id = fields.Many2one('gesion.organization', string='Parent Organization', ondelete='restrict')
    child_ids = fields.One2many('gesion.organization', 'parent_id', string='Child Organizations')
    organization_type = fields.Selection([('project', 'Project'), ('company', 'Company'), ('department', 'Department')],
                                         string="Organization Type", default='project')
    # sequence = fields.Integer(string='Sequence')
    seq = fields.Char(string='SEQ')
    hierarchy = fields.Integer(string='Hierarchy', compute='_compute_path', store=True, track_visibility='always')
    path = fields.Char(string='Path', store=True, compute='_compute_path', track_visibility='always')
    is_root = fields.Boolean(string='Is Root', compute='_compute_root', store=True)
    is_last = fields.Boolean(string='Is Last', compute='_compute_last', store=True)
    has_child = fields.Boolean(string='Has Child', compute='_compute_has_child', store=True)
    description = fields.Text('Description', translate=True)

    project_id = fields.One2many('project.project', 'organization_id', string='Project', auto_join=True)
    company_id = fields.One2many('res.company', 'organization_id', string='Company', auto_join=True)
    department_id = fields.One2many('hr.department', 'organization_id', string='Department', auto_join=True)
    # distribution_id = fields.Many2one('gesion_dms_test.doc_distribution')

    organization_number = fields.Char(string='Organization Number')
    legal_person_id = fields.Char(string='Legal Person')
    Industry_Class_ids = fields.Char(string='Industry & Trade')
    tax_number = fields.Char(string='Tax Number')
    organization_register_no = fields.Char(string='Business License Registration Number')
    credit_rating = fields.Char(string='Credit Rating')

    @api.depends('parent_id')
    @api.multi
    def _compute_root(self):
        for record in self:
            record.is_root = True if not record.parent_id else False

    @api.depends('child_ids')
    @api.multi
    def _compute_last(self):
        for record in self:
            record.is_last = True if not record.child_ids else False

    @api.depends('child_ids')
    @api.multi
    def _compute_has_child(self):
        for record in self:
            record.has_child = True if record.child_ids else False

    @api.depends('parent_id', 'name')
    @api.multi
    def _compute_path(self):
        for record in self:
            parent = record.parent_id
            hierarchy = 1
            path = record.name
            while parent.name:
                hierarchy += 1
                path = u"{0}-{1}".format(parent.name, path)
                parent = parent.parent_id
            record.path = path
            record.hierarchy = hierarchy

    @api.model
    def create(self, vals):
        # required_fields = ["name", "organization_type"]
        # for f in required_fields:
        #     if f not in vals:
        #         raise UserError(_("{} must be set!".format(f)))
        #     elif not vals[f]:
        #         raise UserError(_("{} must be set!".format(f)))
        organization = super(Organization, self).create(vals)
        if vals.get("organization_type") and vals.get("name"):
            if vals["organization_type"] == 'project':
                project = self.env['project.project'].create({
                    'name': vals['name'],
                    'organization_id': organization.id
                })
                vals['project_id'] = project.id
            elif vals["organization_type"] == 'company':
                company = self.env['res.company'].create({
                    'name': vals['name'],
                    'organization_id': organization.id
                })
                vals['company_id'] = company.id
            elif vals["organization_type"] == 'department':
                department = self.env['hr.department'].create({
                    'name': vals['name'],
                    'organization_id': organization.id
                })
                vals['department_id'] = department.id
            # self.clear_caches()

            if vals["organization_type"] == 'project':
                organization.project_id = project
            elif vals["organization_type"] == 'company':
                organization.company_id = company
            elif vals["organization_type"] == 'department':
                organization.department_id = department
        return organization

    @api.multi
    def unlink(self):
        for record in self:
            if record.child_ids:
                raise UserError(_("You Can't Delete Record Which has Child."))
        super(Organization, self).unlink()
