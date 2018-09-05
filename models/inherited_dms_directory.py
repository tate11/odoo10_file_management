# -*- coding: utf-8 -*-
# Author: Ray

import logging

from odoo import tools, _
from odoo import models, api, fields
from odoo.tools import ustr
from odoo.tools.mimetypes import guess_mimetype
from odoo.exceptions import ValidationError, AccessError, UserError
import odoo.addons.decimal_precision as dp
from odoo.modules.module import get_module_resource

from odoo.addons.muk_dms.models import dms_base
import json

_logger = logging.getLogger(__name__)


class Directory(dms_base.DMSModel):

    _inherit = 'muk_dms.directory'

    name = fields.Char(string="Folder Name", required=True)
    repository_id = fields.Many2one('gesion_dms.repository', string='Repository', required=True, store=True)
    has_child = fields.Boolean(string='Has Child', compute='_compute_has_child',store=True)
    hierarchy = fields.Integer(string='Hierarchy', compute='_compute_hierarchy', store=True)
                               # compute='_compute_hierarchy')
    # sequence = fields.Integer(string='Sequence')
    seq = fields.Char(string='SEQ')
    doc_count = fields.Integer(string='Total Document Count', compute='_count_doc') # include sub directories file

    # folder progress
    # input_progress = fields.Float(string='Input', default=0)
    output = fields.Float(string='Output',default=0, digits=dp.get_precision('Product Unit of Measure'))
    task_id = fields.Many2one('project.task', string='Task')
    relativity_weight = fields.Float(string='Relativity Weight', default=0, digits=dp.get_precision('Product Unit of Measure'))
    absolute_weight = fields.Float(string='Absolute Weight',
                                   digits=dp.get_precision('Product Unit of Measure'), )
    earned_value = fields.Float(string='Earned Value', compute='_compute_earned_value',
                                digits=dp.get_precision('Product Unit of Measure'),store=True)

    directory_code = fields.Char(size=8, string='Directory Code')
    man_hours = fields.Integer('Man Hours')
    labor_cost = fields.Float('Labor Cost')
    labor_cost_unit = fields.Float('Labor Cost Unit')
    description = fields.Text(string="Description")
    tag_ids = fields.Many2many('directory.tags', string='Tags')

    # direction = fields.Char('default=up')
    # judge
    # image: all image fields are base64 encoded and PIL-supported
    # image = fields.Binary("Photo", attachment=True,
    #                       help="This field holds the image used as photo for the directory, limited to 1024x1024px.")
    # image_medium = fields.Binary("Medium-sized photo", attachment=True,
    #                              help="Medium-sized photo of the directory. It is automatically "
    #                                   "resized as a 128x128px image, with aspect ratio preserved. "
    #                                   "Use this field in form views or some kanban views.")
    # image_small = fields.Binary("Small-sized photo", attachment=True,
    #                             help="Small-sized photo of the directory. It is automatically "
    #                                  "resized as a 64x64px image, with aspect ratio preserved. "
    #                                  "Use this field anywhere a small image is required.")
    #
    # @api.model
    # def _default_image(self):
    #     image_path = get_module_resource('gesion_dms', 'static/src/img', 'default_image.png')
    #     return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    @api.multi
    def _count_doc(self):
        for record in self:
            direct_link_file = self.env['muk_dms.file'].search_count([('directory', '=', record.id)])
            sub_directories_file = sum(record.child_directories.mapped(lambda r: r.doc_count))
            record.doc_count = direct_link_file + sub_directories_file

    @api.constrains('relativity_weight')
    def _check_settings(self):
        if not 0<=self.relativity_weight<=1:
            raise ValidationError(_("relativity_weight must be between 0 and 1."))
        file_relativity_weights = self.parent_directory.files.mapped(lambda r: r.relativity_weight)
        directory_relativity_weights = self.parent_directory.child_directories.mapped(lambda r: r.relativity_weight)
        file_relativity_weights.extend(directory_relativity_weights)
        sum_weights = sum(file_relativity_weights)
        if not 0<=sum_weights<=1:
            raise ValidationError(_("Same level relativity_weight count must be between 0 and 1."))

    @api.onchange('relativity_weight')
    def _show_weight(self):
        for record in self:
            if record.parent_directory: # and record.hierarchy > 1:
                parent_absolute_weight = record.parent_directory.absolute_weight
            elif record.repository_id: # and record.hierarchy == 1:
                parent_absolute_weight = record.repository_id.absolute_weight
            else:
                parent_absolute_weight = 0
            record.absolute_weight = parent_absolute_weight * record.relativity_weight

                # raise UserError(_("Directory must have repository_id or parent directory!"))
            # file_relativity_weights = record.parent_directory.files.mapped(lambda r: r.relativity_weight)
            # directory_relativity_weights = record.parent_directory.child_directories.mapped(lambda r: r.relativity_weight)
            # file_relativity_weights.extend(directory_relativity_weights)
            # sum_weights = sum(file_relativity_weights)
            # if sum_weights > 1:
            #     raise UserError(_("Relativity weight bigger than 100%!"))
            # elif sum_weights < 0:
            #     raise UserError(_("Relativity weight smaller than 100%, please add more."))
            # record.earned_value = record.absolute_weight * record.progress

    # @api.onchange('files.earned_value, child_directories.earned_value')
    # def _compute_earned_value(self):
    #     for record in self:
    #         files_earned_value = sum(record.files.mapped(lambda r: r.earned_value))
    #         children_earned_value = sum(record.child_directories.mapped(lambda r: r.earned_value))
    #         record.earned_value = files_earned_value + children_earned_value
            # record.earned_value = record.absolute_weight * record.progress
            # print record.earned_value
            # if record.parent_directory:
            #     record.parent_directory.earned_value += record.earned_value
            #     print record.parent_directory.earned_value
            # elif record.repository_id:
            #     record.repository_id.earned_value += record.earned_value
            #     print record.repository_id.earned_value
            # print "=================="

    # @api.depends('child_directories', 'files')
    # def _compute_has_child(self):
    #     for record in self:
    #         record.has_child = True if (len(record.child_directories) or len(record.files))else False

    @api.onchange('parent_directory', 'repository_id')
    def _show_hierarchy(self):
        for record in self:
            parent = record.parent_directory
            if parent:
                record.repository_id = parent.repository_id
            hierarchy = 1
            while parent:
                hierarchy += 1
                parent = parent.parent_directory
            record.hierarchy = hierarchy

#------------------------------#
#------------------------------#

    # def _after_create(self, vals):
    #     record = super(Directory, self)._after_create(vals)
    #     record._check_recomputation(vals)
    #     return record
    #
    # def _after_write_record(self, vals, operation):
    #     vals = super(Directory, self)._after_write_record(vals, operation)
    #     self._check_recomputation(vals, operation)
    #     return vals

#-------------------------------#
    # 重写该方法

    #
    def trigger_computation(self, fields, refresh=True, operation=None):
        super(Directory, self).trigger_computation(fields, refresh, operation)
        values = {}
        if "hierarchy" in fields:
            values.update(self.with_context(operation=operation)._compute_hierarchy(write=False))
            values.update(self.with_context(operation=operation)._compute_has_child(write=False))
        # if "absolute_weight" in fields:
        #     values.update(self.with_context(operation=operation)._compute_weight(write=False))
        if "earned_value" in fields:
            values.update(self.with_context(operation=operation)._compute_earned_value(write=False))
        if values:
            self.write(values)                        # 更新数据的节点
            # if "has_child" in fields or 'earned_value' in fields :
            #     self.calculation_up(fields, operation)
            # if "absolute_weight" in fields:
            #     self.absolute_weight_computation_down(fields, operation)


    def calculation_up(self, fields, operation=None):    # trigger_computation保证记录为1条
        parent_directory = self.parent_directory   #取上级目录id
        if parent_directory:
            parent_directory.trigger_computation(fields, False)


    # def absolute_weight_computation_down(self, fields, operation=None):
    #     for child in self.child_directories:
    #         child.with_context(is_subnode=True).trigger_computation(fields, False, operation)   # 选取下级目录
    #     for index, file in enumerate(self.files):
    #         if index == len(self.files) - 1:    #去最后一个文件
    #             if self.env.context.get('is_subnode'):
    #                 file.trigger_computation(fields, False, operation)
    #             else:
    #                 file.trigger_computation(fields, True, operation)
    #         else:
    #             file.trigger_computation(fields, False, operation)






     # 写入fields
    def _check_recomputation(self, values, operation=None):
        super(Directory,self.sudo())._check_recomputation(values,operation)
        fields = []
        if ('parent_directory' in values or 'repository_id' in values):
            fields.extend(['has_child', 'hierarchy'])
        if 'relativity_weight' in values:
            fields.extend(['absolute_weight', 'earned_value'])
        if fields:
            self.trigger_computation(fields, operation=operation)
        # if 'has_child' in values or 'earned_value' in values:
        #     self.calculation_up(['has_child', 'earned_value'])




#------------------------#


    # 计算层级
    def _compute_hierarchy(self, write=True):
        def get_hierarchy(record):
            parent = record.parent_directory
            hierarchy = 1
            while parent:
                hierarchy += 1
                parent = parent.parent_directory
            return hierarchy
        if write:
            for record in self:
                record.hierarchy = get_hierarchy(record)
        else:
            self.ensure_one()
            return {'hierarchy': get_hierarchy(self)}

    # 计算是否含有子节点
    def _compute_has_child(self,write=True):
        def judge_has_child(record):
            has_child = False
            count = 0
            for directory in record.child_directories:
                count+=1
            for file in record.files:
                count+=1
            if count>0:
                has_child = True
            return has_child
        if write:
            for record in self:
                record.has_child = judge_has_child(record)
        else:
            self.ensure_one()
            return {'has_child': judge_has_child(self)}


    # # 计算绝对权重,向下计算
    # def _compute_weight(self, write=True):
    #     def calculation_weight(record):
    #         if record.parent_directory:  # and record.hierarchy > 1:
    #             parent_absolute_weight = record.parent_directory.absolute_weight
    #         elif record.repository_id:  # and record.hierarchy == 1:
    #             parent_absolute_weight = record.repository_id.absolute_weight
    #         else:
    #             parent_absolute_weight = 0
    #         absolute_weight = parent_absolute_weight * record.relativity_weight
    #         return {'absolute_weight':absolute_weight}
    #     if write:
    #         for record in self:
    #             record.absolute_weight = calculation_weight(record)
    #             # record.direction = calculation_weight(record)['direction']
    #     else:
    #         self.ensure_one()
    #         return {'absolute_weight':calculation_weight(self)}


    # 计算赢得值，向上计算
    def _compute_earned_value(self,write=True):
        def get_earned_value(record):
            files_earned_value = sum(record.files.mapped(lambda r: r.earned_value))
            children_earned_value = sum(record.child_directories.mapped(lambda r: r.earned_value))
            earned_value = files_earned_value + children_earned_value
            return earned_value
        if write:
            for record in self:
                record.earned_value = get_earned_value(record)
                # record.direction = get_earned_value(record)['direction']
        else:
            self.ensure_one()
            return {'earned_value': get_earned_value(self)}



