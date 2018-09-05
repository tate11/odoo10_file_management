# -*- coding: utf-8 -*-
# Author: Ray

from odoo import api, models, fields, _


class Company(models.Model):

    _name = "res.company"
    _inherit = ['res.company']
    _inherits = {'gesion.organization': "organization_id"}

    organization_id = fields.Many2one('gesion.organization', string='Organization',
                                      required=True, ondelete='cascade', auto_join=True)

    @api.model
    def create(self, vals):
        company = super(Company, self).create(vals)
        company.organization_id.name = company.name
        company.organization_id.company_id = company
        company.organization_id.organization_type = 'company'
        return company

    @api.multi
    def unlink(self):
        organization = self.organization_id
        res = super(Company, self).unlink()
        organization.unlink()
        return res
