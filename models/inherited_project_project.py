# -*- coding: utf-8 -*-
# Author: Ray

from odoo import api, models, fields, _
import time
import re


class Project(models.Model):

    _name = "project.project"
    _inherit = ['project.project']
    _inherits = {'gesion.organization': "organization_id"}

    name = fields.Char(related='organization_id.name', inherited=True)
    organization_id = fields.Many2one('gesion.organization', string='Organization',
                                      required=False, ondelete='cascade', auto_join=True)
    # project information
    project_code = fields.Char('Project Code')
    design_manager = fields.Many2one('res.partner', string='Design Manager')
    project_manager = fields.Many2one('res.partner', string='Project Manager')
    craft_package = fields.Char('Craft Package')
    proprietor = fields.Many2one('res.partner', string='Proprietor')
    document_control_users = fields.Many2many('res.users', 'gesion_dms_users_rel', 'pid', 'uid',
                                              string='Document Control Staff')
    # gesion project settings
    # project_currency_conversion_reates = fields.Char(string='Project Currency Conversion Rates')
    # vendor_ids = fields.One2many('res.partner', 'project_id', string="Project Vendor List")

    @api.model
    def create(self, vals):
        project = super(Project, self).create(vals)
        project.organization_id.name = project.name
        project.organization_id.project_id = project
        project.organization_id.organization_type = 'project'
        return project

    @api.multi
    def unlink(self):
        organization = self.organization_id
        res = super(Project, self).unlink()
        organization.unlink()
        return res


class ProjectTask(models.Model):
    _inherit = "project.task"
    _order = 'seq_order'

    user_id = fields.Many2many('res.users','user_project_task_ref', 'user_id', 'project_task_id',
        string='Assigned to',
        index=True,)

    project_stage_id = fields.Many2one('project.stage', 'Project Stage')
    workpackage_id = fields.Many2one('project.workpackage', 'Workpackage')
    file_ids = fields.One2many('muk_dms.file', 'task_id', string='Files')
    directory_ids = fields.One2many('muk_dms.directory', 'task_id', string='Directory')
    repository_ids = fields.One2many('gesion_dms.repository', 'task_id', string='Repository')
    task_stage_ids = fields.One2many('task.stage', 'task_id', string='Stage')
    # relate muk_dms.file

    file_id = fields.Many2one('muk_dms.file', string='File Name')
    task_number = fields.Char(string='Task Number')
    task_level = fields.Integer(string='Task Level', compute='_compute_task_level', store=True)

    parent_task = fields.Many2one('project.task',
                                  auto_join=True,
                                  ondelete='restrict',
                                  string='Parent Task')

    child_tasks = fields.One2many('project.task',
                                  'parent_task',
                                  copy=False,
                                  string='Subtasks')

    is_root_task = fields.Boolean('Root tasks',
                                  default=False)

    project_construction_area_id = fields.Many2one('project.construction.area',
                                                    string='Project Construction area',
                                                    ondelete='restrict')

    discipline_id = fields.Many2one('project.discipline',
                                    string='Discipline')

    doc_number = fields.Char(string="Document Number",)

    doc_amount = fields.Integer(string='Doc Sheets amount')

    convert_a1 = fields.Float(string='Convert A1')

    designer = fields.Many2one('hr.employee',
                               string='Designer')

    man_hours= fields.Integer(string='Man Hours', )

    labor_cost_unit = fields.Float('Labor Cost Unit',)

    currency = fields.Char(string='Currency')

    labor_cost = fields.Float(string='Labor Cost',)
    # date
    plan_start_date = fields.Date(string='Plan Start Date', )
    forcast_start_date = fields.Date(string='Forcast Start Date',)
    actual_start_date = fields.Date(string='Actual Start Date', )
    plan_end_date = fields.Date(string='Plan End Date',)
    forcast_end_date = fields.Date(string='Forcast End Date',)
    actual_end_date = fields.Date(string='Actual End Date',)
    #earned value
    input_progress = fields.Float(string='Input Progresss', )
    relativity_weight = fields.Float(string='Relativity Weight', )
    absolute_weight = fields.Float(string='Absolute Weight',)
    earned_value = fields.Float(string='Earned Value', )

    early_days = fields.Float(string='Lead Time(h)')

    remark = fields.Text(string='Remark')

    grade = fields.Integer(string='QA/QC Grade')

    stat_rate = fields.Selection([("0", "0星"), ("1", "1星"), ("2", "2星"), ("3", "3星"), ("4", "4星"), ("5", "5星")],
                                 string='星级评价',default='0')

    task_class_id = fields.Many2one('project.task.class', string='Task Class')
    # sequence = fields.Integer(string='Sequence')
    seq = fields.Char(string='SEQ')

    seq_order = fields.Integer(string='Seq Order')
    # # relate repository
    # repository_id = fields.Many2one('gesion_dms.repository', string='Repository')
    # # relate directory
    # directory_id = fields.Many2one('muk_dms.directory', string='Folder')
    #
    # task_relate = fields.Selection([('file', 'file_id'), ('repository', 'repository_id'), ('folder', 'directory_id')], string='Task Relate', default='file')

    @api.depends('parent_task')
    @api.multi
    def _compute_task_level(self):
        for record in self:
            parent = record.parent_task
            hierarchy = 1
            while parent.name:
                hierarchy += 1
                parent = parent.parent_task
            record.task_level = hierarchy


    @api.depends('plan_start_date', 'actual_end_date')
    def _get_human_month(self):

        for record in self:
            if record.plan_start_date > record.actual_end_date:
                record.early_days = 0
            else:
                value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.mktime(time.strptime(record.plan_start_date, "%Y-%m-%d")) - time.mktime(time.strptime(record.actual_end_date, "%Y-%m-%d"))))
                record.early_days = value

    @api.depends('task_level')
    def _choose_root_task(self):
        for record in self:
            if record.task_level <= 1:
                record.is_root_task = True
            else:
                record.is_root_task = False

    @api.constrains('input_progress')
    def _limit_input_progress(self):
        for record in self:
            if not 0<= record.input_progress <= 1:
                raise ValueError('Input progress must between 0 and 1.')

    # @api.depends('grade')
    # def _show_star(self):
    #     for record in self:
    #         if record.grade == 0:
    #             record.stat_rate = '0'
    #         elif 0 < record.grade< 20:
    #             record.stat_rate = '1'
    #         elif 20 <= record.grade <40:
    #             record.stat_rate = '2'
    #         elif 40 <= record.grade < 60:
    #             record.stat_rate = '3'
    #         elif 60 <= record.grade < 80:
    #             record.stat_rate = '4'
    #         else:
    #             record.stat_rate = '5'
    @api.constrains('seq')
    def _limit_seq(self):
        for record in self:
            reg_seq = re.compile('^\d+(.\d+)*$')
            if not reg_seq.match(record.seq) or not record.seq:
                raise ValueError(_('Seq input format is incorrect,e.g 1.1.1.1'))

    @api.multi
    def _get_order_seq_id(self):
        versions = self.env['project.task'].search_read(fields=['id','seq','seq_order'])
        for item in versions:
            if item['seq']:
                item['seq'] = list(map(int, item['seq'].split('.')))
            else:
                item['seq'] = [-1]
        lens = [len(item['seq']) for item in versions]
        max_len = max(lens)
        for item in versions:
            item['seq'] = item['seq'] + [-1] * (max_len - len(item['seq']))
        seq_list_sort = sorted(versions, key=lambda r: r['seq'])
        number = 1
        for item in seq_list_sort:
            item['seq_order'] = number
            number += 1
        return seq_list_sort


    @api.multi
    def _compute_seq_order(self):
        result = []
        res = self._get_order_seq_id()
        for item in res:
            item.pop('seq')
            result.append(item)
        return result

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        reuslt = self._compute_seq_order()
        update = "UPDATE project_task SET seq_order=%s WHERE id=%s"
        for item in reuslt:
            self._cr.execute(update, (item['seq_order'], item['id']))
        return res

    @api.multi
    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        reuslt = self._compute_seq_order()
        update = "UPDATE project_task SET seq_order=%s WHERE id=%s"
        for item in reuslt:
            self._cr.execute(update, (item['seq_order'], item['id']))
        return res


class ProjectTaskClass(models.Model):
    _name = 'project.task.class'

    name = fields.Char(string='name')
    description = fields.Text(string='description')
    task_ids = fields.One2many('project.task', 'task_class_id', string='Project Task')

class Partner(models.Model):
    _inherit = "res.partner"

    project_id = fields.Many2one('project.project', string='Project')
