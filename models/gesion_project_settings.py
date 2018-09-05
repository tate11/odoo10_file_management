# -*- coding: utf-8 -*-
# Author: Ray

from odoo import api, models, fields, _

from odoo.addons.gesion_dms.models import gesion_base


class ProjectStage(gesion_base.ProjectDurationModel):
    _name = 'project.stage'
    _description = 'Project Stage'
    _order = 'sequence, id'

    # def _get_mail_template_id_domain(self):
    #     return [('model', '=', 'project.task')]

    name = fields.Char(string='Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    task_ids = fields.One2many('project.task', 'project_stage_id', string='Tasks')
    # mail_template_id = fields.Many2one('mail.template', string='Email Template',
    #                                    domain=lambda self: self._get_mail_template_id_domain(),
    #                     help="If set an email will be sent to the customer when the task or issue reaches this step.")
    fold = fields.Boolean(string='Folded in Kanban',
                  help='This area is folded in the kanban view when there are no records in that area to display.')
    project_stage_code = fields.Char(string='Project Stage Code', size=4)
    std = fields.Float(string='STD%')
    task_stage_id = fields.One2many('task.stage', 'stage')


class ProjectConstructionArea(models.Model):
    _name = 'project.construction.area'
    _description = 'Project Construction Area'
    _order = 'sequence, id'

    name = fields.Char(string='Construction Area Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban',
                  help='This area is folded in the kanban view when there are no records in that area to display.')
    project_cons_area_code = fields.Char(string='Project Construction Area Code', size=4)

    project_task_ids = fields.One2many('project.task', 'project_construction_area_id', string='Project Task')



class ProjectDiscipline(models.Model):
    _name = 'project.discipline'
    _description = 'Project Discipline'
    _order = 'sequence, id'

    name = fields.Char(string='Discipline Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban',
        help='This discipline is folded in the kanban view when there are no records in that discipline to display.')
    project_discipline_code = fields.Char(string='Project Discipline Code', size=4)
    user_ids = fields.Many2many('hr.employee', 'discipline_employee_rel', 'discipline_id', 'employee_id',
                                string='Engineers')

    project_task_ids = fields.One2many('project.task', 'discipline_id', string='Project Tasks')

class ProjectAddress(models.Model):
    _name = 'project.address'
    _description = 'Project Address'
    _order = 'sequence, id'

    name = fields.Char(string='Process Address Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban')
    project_address_code = fields.Char(string='Project Address Code', size=4)
    address_id = fields.Many2one('res.partner', string='Address')
    # telephone = fields.Char(related=address_id.mobile)
    # fax = fields.Char(related=address_id.fax)


class ProjectDeliveryPoint(models.Model):
    _name = 'project.delivery.point'
    _description = 'Project Delivery Point'
    _order = 'sequence, id'

    name = fields.Char(string='Process Delivery Point Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban')
    project_address_code = fields.Char(string='Project Delivery Point Code', size=4)
    address_id = fields.Many2one('res.partner', string='Address')


class ProjectProcessArea(models.Model):
    _name = 'project.process.area'
    _description = 'Project Process Area'
    _order = 'sequence, id'

    name = fields.Char(string='Process Area Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban')


# class ProjectCostArea(models.Model):
#     _name = 'project.cost.area'
#     _description = 'Project Cost Area'
#     _order = 'sequence, id'
#
#     name = fields.Char(string='Cost Area Name', required=True, translate=True)
#     description = fields.Text(translate=True)
#     sequence = fields.Integer(default=1)
#     project_id = fields.Many2one('project.project', 'Project')
#     # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
#     fold = fields.Boolean(string='Folded in Kanban')


# class ProjectWorkcode(models.Model):
#     _name = 'project.workcode'
#     _description = 'Project Workcode'
#     _order = 'sequence, id'
#
#     name = fields.Char(string='Workcode Name', required=True, translate=True)
#     description = fields.Text(translate=True)
#     sequence = fields.Integer(default=1)
#     project_id = fields.Many2one('project.project', 'Project')
#     # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
#     fold = fields.Boolean(string='Folded in Kanban')


class ProjectWorkpackage(gesion_base.ProjectDurationModel):
    _name = 'project.workpackage'
    _description = 'Project Workpackage'
    _order = 'sequence, id'

    name = fields.Char(string='Workpackage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    # date_start = fields.Datetime(string='Starting Date', default=fields.Datetime.now, index=True, copy=False)
    # date_end = fields.Datetime(string='Ending Date', index=True, copy=False)
    # fist_task_date_start = fields.Datetime(compute='_get_first_date_start', copy=False)
    # last_task_date_end = fields.Datetime(compute='_get_last_date_end', copy=False)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'workpackage_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban')
    contract_id = fields.Many2one('hr.contract', string='Contract')

    # @api.depends('task_ids.date_start')
    # def _get_first_date_start(self):
    #     task_date_states = self.task_ids.mapped(lambda r: r.date_state)
    #     self.fist_task_date_start = task_date_states.sort()[0]
    #
    # @api.depends('task_ids.date_end')
    # def _get_first_date_start(self):
    #     task_date_ends = self.task_ids.mapped(lambda r: r.date_end)
    #     self.fist_task_date_end = task_date_ends.sort()[-1]
    #
    # @api.onchange('date_start')
    # def check_date_start(self):
    #     if self.date_start > self.fist_task_date_start:
    #         raise UserWarning(_('There is a task start before this time!'))
    #
    # @api.onchange('date_end')
    # def check_date_end(self):
    #     if self.date_end < self.last_task_date_end:
    #         raise UserWarning(_('There is a task end after this time!'))


class ProjectIssuepackage(gesion_base.ProjectDurationModel):
    _name = 'project.issuepackage'
    _description = 'Project issuepackage'
    _order = 'sequence, id'

    name = fields.Char(string='Issuepackage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    fold = fields.Boolean(string='Folded in Kanban')
    contract_id = fields.Many2one('hr.contract', string='Contract')


class ProjectDocClass(models.Model):
    _name = 'project.doc.class'
    _description = 'Project Doc Class'
    _order = 'sequence, id'

    name = fields.Char(string='Doc Class Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban')
    project_doc_class_code = fields.Char(string='Project Doc Class Code')

    # task_id = fields.One2many('project.task', 'task_class_id' ,string='Project Task')


class ProjectDocType(models.Model):
    _name = 'project.doc.type'
    _description = 'Project Doc Type'
    _order = 'sequence, id'

    name = fields.Char(string='Doc Type Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban')
    project_doc_type_code = fields.Char(string='Project Doc Type Code', size=4)
    design_doc_indicate = fields.Selection([('design', 'D'), ('other', 'O')], string='Design Doc Indicate',
                                           help='D is design file, O is other file.', default='design')
    special_doc_type = fields.Selection([('requisition', 'Requisition'), ('purchase_order', 'Purchase Order'),
                                         ('transimittal', 'Transimittal'), ('bid_approval', 'Bid Approval'),
                                         ('enquiry', 'Enquiry'), ('other', 'Other')], string='Special Doc Indicate')


class ProjectDocReviewStage(models.Model):
    _name = 'project.doc.review.stage'
    _description = 'Project Doc Review Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Doc Review Stage Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')
    # task_ids = fields.One2many('project.task', 'construction_area_id', string='Tasks')
    fold = fields.Boolean(string='Folded in Kanban')
    stage_indicate = fields.Char(string='Project Doc Review Stage Code', size=1)
    design_doc_indicate = fields.Selection([('design', 'D'), ('other', 'O')], string='Design Doc Indicate',
                                           help='D is design file, O is other file.', default='design')


class DirectoryTags(models.Model):
    _name = "directory.tags"
    _description = "Tags of directories"

    name = fields.Char(required=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]


class TaskStage(models.Model):
    _name = 'task.stage'

    link_id = fields.Many2one('muk_dms.file')
    task_id = fields.Many2one('project.task', string='Task')
    # std = fields.Many2one('std')
    std = fields.Float(related='stage.std')
    description = fields.Text(related='stage.description', string='Description')
    # stage_id = fields.Many2one('project.stage', string='Stage')
    stage = fields.Many2one('project.stage')
    issued = fields.Boolean(string='Issued')
    planned_date = fields.Date(string='Planned Date')
    forcast_date = fields.Date(string='Forcast Date')
    actual_date = fields.Date(string='Actual Date')
    milestone = fields.Many2one('milestone', string='Milestone')
    project_id = fields.Many2one(related='task_id.project_id', store=True)


class Milestone(models.Model):
    _name = 'milestone'
    _description = 'Milestone'
    _order = 'name, sequence, id'

    name = fields.Char(string='Milestone', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    project_id = fields.Many2one('project.project', 'Project')

#
# class STD(models.Model):
#     _name = 'std'
#
#     name = fields.Char(string='STD')
#     value = fields.Float(string='STD%')
#     description = fields.Text(string='Description')
