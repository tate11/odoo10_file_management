# -*- coding: utf-8 -*-
# Author: Ray

from odoo import api, models, fields, _


class Users(models.Model):
    _inherit = "res.users"

    organization_ids = fields.Many2many('gesion.organization', 'gesion_organization_users_rel', 'user_id', 'oid',
                                        string='Organizations')


class Employee(models.Model):

    _inherit = ['hr.employee']

    description = fields.Text('Description')
    project_task_ids = fields.One2many('project.task', 'designer', string='Project Tasks')
    organization_ids = fields.Many2many(related='user_id.organization_ids', readonly=True)



