# -*- coding: utf-8 -*-
# Author: Ray

import os
import shutil
import logging
import hashlib
import base64
import subprocess
from datetime import date, datetime
from dxf2svg.pycore import save_svg_from_dxf, extract_all

from odoo import tools, _
from odoo import models, api, fields
from odoo.tools import ustr
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import ValidationError, AccessError, UserError
import odoo.addons.decimal_precision as dp
from odoo.modules.module import get_module_resource

from odoo.addons.muk_dms.models import dms_base

from uuid import uuid4

_logger = logging.getLogger(__name__)


class File(dms_base.DMSModel):
    _name = 'muk_dms.file'
    _inherit = ['mail.thread', 'muk_dms.file']
    # ----------------------------------------------------------
    # Database
    # ----------------------------------------------------------
    repository_id = fields.Many2one('gesion_dms.repository', compute='_compute_repository', string='Repository')
    state = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'), ('first', 'First Approved'),
        ('second', 'Second Approved'), ('third', 'Third Approved'), ('done', 'Done')],
        string='State',
        help='Select File State.',
        default='draft'
    )
    # sequence = fields.Integer(string='Sequence')
    seq = fields.Char(string='SEQ')
    hierarchy = fields.Integer(string='Hierarchy', compute='_compute_hierarchy',store=True)

    version_ids = fields.One2many('gesion_dms.file_version', 'file_id', string="Old Versions")
    trigger_file_version = fields.Char(compute='create_file_version')
    md5 = fields.Char(string="MD5", compute="_compute_file_md5")
    # just for store dwg or dxf file convert to svg
    svg_content = fields.Binary(string='SVG Content')

    # document progress
    # progress 已废弃，去除会导致有progress数据的数据库升级错误，暂不删除
    progress = fields.Float(string='Progress')
    input_progress = fields.Float(string='Input', default=0)
    applied = fields.Float(string='Applied', default=0)
    task_id = fields.Many2one('project.task', string='Task')
    relativity_weight = fields.Float(string='Relativity Weight', default=0,
                                     digits=dp.get_precision('Product Unit of Measure'))
    absolute_weight = fields.Float(string='Absolute Weight', compute='_compute_weight',
                                   digits=dp.get_precision('Product Unit of Measure'), store=True)
    earned_value = fields.Float(string='Earned Value', compute='_compute_earned_value',
                                digits=dp.get_precision('Product Unit of Measure'),store=True)

    file_code = fields.Char(size=8, string='File Code')
    responsible_person_ids = fields.Many2many('res.users', 'file_user_rel', 'file_id', 'user_id', string="Responsible Person")
    man_hours = fields.Integer('Man Hours', compute='_compute_hours')
    labor_cost = fields.Float('Labor Cost',compute='_compute_cost')
    labor_cost_unit = fields.Float('Labor Cost Unit')
    # project setting
    discipline_id = fields.Many2one('project.discipline', string='Discipline')
    doc_class_id = fields.Many2one('project.doc.class', string='Doc Class')
    doc_type_id = fields.Many2one('project.doc.type', string='Doc Type')
    review_stage_id = fields.Many2one('project.doc.review.stage', string='Doc Review Stage')
    # date
    plan_date = fields.Datetime(string='Plan Date', copy=False)
    forecast_date = fields.Datetime(string='Forecast Date', copy=False)
    actual_date = fields.Datetime(string='Actual Date', copy=False)
    # image: all image fields are base64 encoded and PIL-supported
    # image = fields.Binary("Photo", attachment=True,
    #                       help="This field holds the image used as photo for the file, limited to 1024x1024px.")
    # image_medium = fields.Binary("Medium-sized photo", attachment=True,
    #                              help="Medium-sized photo of the file. It is automatically "
    #                                   "resized as a 128x128px image, with aspect ratio preserved. "
    #                                   "Use this field in form views or some kanban views.")
    # image_small = fields.Binary("Small-sized photo", attachment=True,
    #                             help="Small-sized photo of the file. It is automatically "
    #                                  "resized as a 64x64px image, with aspect ratio preserved. "
    #                                  "Use this field anywhere a small image is required.")
    #
    # @api.model
    # def _default_image(self):
    #     image_path = get_module_resource('gesion_dms', 'static/src/img', 'default_image.png')
    #     return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))
    #     Document Information

    document_number = fields.Char(string='Document Number', default='_compute_number')
    document_title = fields.Char(string='Document Title')
    project_number = fields.Char(related='repository_id.name', string='Project No.', readonly='1')
    num = fields.Char(related='repository_id.project_code')
    area_code = fields.Many2one('project.construction.area', string='Area Code')
    revision_number = fields.Char(string='Revision No')
    system_revision = fields.Char(string='System Revision')  # ,compute='_compute_revision')
    designer_ids = fields.Many2many('res.partner', string='Designer')
    sheets = fields.Integer(string='Sheets')
    Document_size = fields.Char(string='Doc Size')
    work_package = fields.Many2one('project.workpackage',string='Work Package')
    document_issue_package = fields.Many2one('project.issuepackage',string='Doc issue Package')
    document_description = fields.Text(string='Doc Description')

    #      Document Progress
    # applied = fields.Char(string='Applied')
    tag_ids = fields.Many2many('directory.tags', string='Tags')
    project_stage_id = fields.Many2one('project.stage', 'Project Stage')

    #    Man Hours
    start_date = fields.Date(string="Start Date")
    plan_end_date = fields.Date(string="Plan End Date")
    location_in_hpro_id = fields.Many2one('gesion.organization',string="Location In HPRO")
    original_budget = fields.Integer(string="Original Budget")
    approved_internal_budget = fields.Integer(string="Approved Internal Budget")
    current_budget = fields.Float(string="Current Budget")
    forecast_to_go = fields.Float(string="Forecast To Go",compute='_compute_Forecast')

    #    Miscelllaneous
    master = fields.Boolean(string="Master")
    cert_auth = fields.Boolean(string="Cert Auth")
    sub_ordinate = fields.Boolean(string="Sub Ordinate")
    canclled = fields.Boolean(string="Canclled")
    code = fields.Char(string=u"编码", required=True,default=lambda self: self.env['ir.sequence'].next_by_code('file.code'))

    # relate distribution
    distribution_id = fields.Many2one('gesion_dms_test.doc_distribution')
    # document_list = fields.One2many('document.list', 'file_name')

    # project.task
    project_task_ids = fields.One2many('project.task', 'file_id', string='Project task')
    # ----------------------------------------------------------
    # Functions
    # ----------------------------------------------------------

    @api.onchange('relativity_weight')
    def _compute_weight(self):
        for record in self:
            file_relativity_weights = record.directory.files.mapped(lambda r: r.relativity_weight)
            directory_relativity_weights = record.directory.child_directories.mapped(lambda r: r.relativity_weight)
            file_relativity_weights.extend(directory_relativity_weights)
            sum_weights = sum(file_relativity_weights)
            # if sum_weights - 1.0 > 0.000001:
            #     raise UserError(_("Relativity weight bigger than 100%!"))
            # elif sum_weights - 1.0 < 0.000001:
            #     raise UserError(_("Relativity weight smaller than 100%, please add more."))
            parent_absolute_weight = record.directory.absolute_weight
            record.absolute_weight = parent_absolute_weight * record.relativity_weight
            # record.earned_value = record.absolute_weight * record.progress

    # @api.depends('progress', 'relativity_weight')
    # def _compute_earned_value(self):
    #     for record in self:
    #         record.earned_value = record.absolute_weight * record.progress
            # if record.directory:
            #     record.directory.earned_value += record.earned_value
            # elif record.repository_id:
            #     record.repository_id.earned_value += record.earned_value

    def action_cancel(self):
        self.state = "cancel"

    def action_first_approve(self):
        self.state = "first"

    def action_second_approve(self):
        self.state = "second"

    def action_third_approve(self):
        self.state = "third"

    def action_done(self):
        self.state = "done"

    def action_alert(self):
        raise UserError(_("Feature is under development, please be patience."))

    @api.onchange('directory')
    def _show_hierarchy(self):
        for record in self:
            parent = record.directory
            hierarchy = parent.hierarchy
            record.hierarchy = hierarchy + 1

    @api.constrains('content')
    def _check_content(self):
        if not self.content:
            raise ValidationError(_("File size cannot be empty."))

    @api.depends('content')
    def _compute_file_md5(self):
        for record in self:
            m = hashlib.md5()
            m.update(record.content)
            md5 = m.hexdigest()
            record.md5 = md5

    @api.depends('md5')
    @api.multi
    def create_file_version(self):
        for record in self:
            # str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            self._cr.execute('select data from muk_dms_data_database where id =%s', (record.id,))
            res = self._cr.fetchone()
            version_values = {
                "name": "_".join([str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), record.name]),
                "file_id": record.id,
                "content": record.content,
                "extension": record.extension,
                "mimetype": record.mimetype,
                "size": record.size,
                "md5": record.md5,
            }
            if record.version_ids:
                if record.md5 != record.version_ids[-1].md5:
                    if res:
                        reference_copied = self.env['muk_dms.data_database'].sudo().create({'data': res[0]})
                    else:
                        reference_copied = record.reference
                    version_values["reference"] = "%s,%s" % (reference_copied._name, reference_copied.id)
                    new_add_version = self.env['gesion_dms.file_version'].create(version_values)
                    record.version_ids = [(4, new_add_version.id)]
            else:
                if res:
                    reference_copied = self.env['muk_dms.data_database'].sudo().create({'data': res[0]})
                else:
                    reference_copied = record.reference
                version_values["reference"] = "%s,%s" % (reference_copied._name, reference_copied.id)
                new_add_version = self.env['gesion_dms.file_version'].create(version_values)
                record.version_ids = [(4, new_add_version.id)]

#-------------------#

    def _check_recomputation(self, values, operation=None):
        self._check_content()
        super(File,self)._check_recomputation(values,operation)
        fields = []
        if 'relativity_weight' in values:
            fields.extend(['absolute_weight', 'earned_value', 'hierarchy'])
        if 'input_progress' in values:
            fields.extend(['earned_value'])
        if fields:
            self.trigger_computation(fields)

        # self._check_reference_values(values)
        # if 'earned_value' in values:
        #     self.trigger_computation_up(['earned_value'])

    def cad2svg(self, extension, content):
        if not os.path.exists('input'):
            os.makedirs('input')
        if not os.path.exists('output'):
            os.makedirs('output')
        raw_name = self.name.split('.', -1)[0]
        input_path = u"./input/{}".format(self.name)
        output_path = u"./output/{}.dxf".format(raw_name)
        if extension == u".dwg":
            with open(input_path, 'wb+') as f:
                f.write(base64.b64decode(content))
            if os.path.exists(input_path):
                # _logger.info('QT_QPA_PLATFORM: %s' % os.environ['QT_QPA_PLATFORM'])
                # _logger.info('DISPLAY: %s' % os.environ['DISPLAY'])
                os.environ['QT_QPA_PLATFORM'] = 'offscreen'
                os.environ['DISPLAY'] = 'localhost:10.0'
                _logger.info('environ: %s' % os.environ)
                command = u'TeighaFileConverter -platform offscreen "input" "output" "ACAD2010" "DXF" "0" "1" "{}"'.format(
                    self.name)
                excute_res = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                _logger.info(u"File: {} convert dxf result is {}".format(self.name, excute_res.stdout.read()))
                os.remove(input_path)
        elif extension == u".dxf":
            with open(output_path, 'wb+') as f:
                f.write(base64.b64decode(content))
        if os.path.exists(output_path):
            # command = u'python -m dxf2svg {}'.format(output_path)
            # excute_res = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # _logger.info(excute_res.stdout.read())
            _logger.info("output_path: %s" % output_path)
            save_svg_from_dxf(output_path.encode('utf8'))
            # extract_all(output_path)
            os.remove(output_path)
            svg_path = u"./output/{}.svg".format(raw_name)
            if os.path.exists(svg_path):
                with open(svg_path, 'rb+') as f:
                    self.svg_content = base64.b64encode(f.read())
                os.remove(svg_path)
                _logger.info(u"File: {} svg storage end".format(self.name))

    def trigger_computation(self, fields, refresh=True, operation=None):
        super(File, self).trigger_computation(fields, refresh, operation)
        values = {}
        if "hierarchy" in fields:
            values.update(self.with_context(operation=operation)._compute_hierarchy(write=False))
        if "absolute_weight" in fields:
            values.update(self.with_context(operation=operation)._compute_weight(write=False))
        if "earned_value" in fields:
            values.update(self.with_context(operation=operation)._compute_earned_value(write=False))
        if "extension" in fields:
            if self.extension in [u".dwg", u".dxf"]:
                self.cad2svg(self.extension, self.content)
        if values:
            self.write(values)

            # if 'earned_value' in fields:
            #     self.trigger_computation_up(fields)
            # if "settings" in fields:
            #     self.notify_change({'save_type': self.settings.save_type})

#----------------#
    # # 计算层级
    def _compute_hierarchy(self, write=True):
        def get_hierarchy(record):
            parent = record.directory
            if parent.hierarchy:
                hierarchy = parent.hierarchy + 1
            return hierarchy
        if write:
            for record in self:
                record.hierarchy = get_hierarchy(record)
        else:
            self.ensure_one()
            return {'hierarchy': get_hierarchy(self)}

     # 计算绝对权重
    def _compute_weight(self, write=True):
        def calculation_weight(record):
            if record.directory:  # and record.hierarchy > 1:
                parent_absolute_weight = record.directory.absolute_weight
            else:
                parent_absolute_weight = 0
            absolute_weight = parent_absolute_weight * record.relativity_weight
            return absolute_weight
        if write:
            for record in self:
                record.absolute_weight = calculation_weight(record)
        else:
            self.ensure_one()
            return {'absolute_weight':calculation_weight(self)}

    # # 计算赢得值
    def _compute_earned_value(self,write=True):
        def get_earned_value(record):
            earned_value = record.input_progress * record.absolute_weight
            return earned_value
        if write:
            for record in self:
                record.earned_value = get_earned_value(record)
        else:
            self.ensure_one()
            return {'earned_value': get_earned_value(self)}

    @api.multi
    @api.onchange('directory')
    def _compute_repository(self):
        for rec in self:
            rec.repository_id = rec.directory.repository_id

    @api.multi
    @api.onchange('num', 'area_code', 'discipline_id', 'doc_type_id', 'code')
    def _compute_number(self):
        for rec in self:
            rec.document_number = '%s-%s-%s-%s-%s' % (rec.num, rec.area_code.project_cons_area_code, rec.discipline_id.project_discipline_code, rec.doc_type_id.project_doc_type_code, rec.code)

    @api.multi
    @api.onchange('labor_cost_unit', 'man_hours')
    def _compute_cost(self):
        for rec in self:
            rec.labor_cost = rec.labor_cost_unit * rec.man_hours
        # self.labor_cost = self.labor_cost_unit * self.man_hours

    @api.onchange('current_budget', 'approved_internal_budget')
    def _compute_Forecast(self):
        self.forecast_to_go = self.current_budget - self.approved_internal_budget

    @api.multi
    @api.onchange('current_budget')
    def _compute_hours(self):
        for rec in self:
            rec.man_hours = rec.current_budget

    @api.model
    def create(self, vals):
        if vals.get('code' 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('file.code') or '/'
        return super(File, self).create(vals)
