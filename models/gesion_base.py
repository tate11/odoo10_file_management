# -*- coding: utf-8 -*-
# Author: Ray

from odoo import _, api, exceptions, fields, models, tools
from odoo.exceptions import UserError, AccessError, MissingError, RedirectWarning


class ProjectDurationBaseModel(models.BaseModel):
    """Main super-class for duration models.

        The ProjectDurationBaseModel itself inherits the BaseModel class from Odoo
        so every model which inherits it can be used as a normal
        Odoo model.
        """

    _auto = False
    _register = False
    _abstract = True
    _transient = False

    _name = None
    _description = None

    date_start = fields.Datetime(string='Starting Date', default=fields.Datetime.now, index=True, copy=False)
    date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    fist_task_date_start = fields.Datetime(compute='_get_first_date_start', copy=False)
    last_task_date_end = fields.Datetime(compute='_get_last_date_end', copy=False)

    @api.depends('task_ids.date_start')
    def _get_first_date_start(self):
        task_date_starts = self.task_ids.mapped(lambda r: r.date_start)
        if task_date_starts:
            self.fist_task_date_start = task_date_starts.sort()[0]

    @api.depends('task_ids.date_end')
    def _get_last_date_end(self):
        task_date_ends = self.task_ids.mapped(lambda r: r.date_end)
        if task_date_ends:
            self.fist_task_date_end = task_date_ends.sort()[-1]

    @api.onchange('date_start')
    def check_date_start(self):
        if self.fist_task_date_start and self.date_start:
            if self.date_start > self.fist_task_date_start:
                raise UserError(_('There is a task start before this time, do you really want to set this time? '
                                  'If not, please reset the time.'))
            # action = self.env.ref('sales_team.action_sale_config')
            # raise RedirectWarning(_('One parameter is missing.'),
            #                       action.id, _('Configure The eBay Integrator Now'))

    @api.onchange('date_end')
    def check_date_end(self):
        if self.last_task_date_end and self.date_end:
            if self.date_end < self.last_task_date_end:
                raise UserError(_('There is a task end after this time, do you really want to set this time? '
                                  'If not, please reset the time.'))


class ProjectDurationModel(ProjectDurationBaseModel):
    """Main super-class for regular database-persisted duration models.

    duration models are created by inheriting from this class:

        class class_name(ProjectDurationModel):

    The ProjectDurationBaseModel itself inherits the BaseModel class from Odoo
    so every model which inherits it can be used as a normal
    Odoo model.
    """

    _auto = True
    _register = False
    _transient = False
    _abstract = False
