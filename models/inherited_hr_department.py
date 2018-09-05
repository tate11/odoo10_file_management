# -*- coding: utf-8 -*-
# Author: Ray

from odoo import api, models, fields, _


class Department(models.Model):

    _name = "hr.department"
    _inherit = ['hr.department']
    _inherits = {'gesion.organization': "organization_id"}

    organization_id = fields.Many2one('gesion.organization', string='Organization',
                                      required=True, ondelete='cascade', auto_join=True)

    @api.model
    def create(self, vals):
        department = super(Department, self).create(vals)
        department.organization_id.name = department.name
        department.organization_id.department_id = department
        department.organization_id.organization_type = 'department'
        return department

    @api.multi
    def unlink(self):
        organization = self.organization_id
        res = super(Department, self).unlink()
        organization.unlink()
        return res
