# -*- coding: utf-8 -*-
# Author: Ray

import os
import json
import base64
import logging

from odoo import tools, _
from odoo import models, api, fields
from odoo.exceptions import ValidationError, AccessError
from odoo.modules.module import get_module_resource
import odoo.addons.decimal_precision as dp

from odoo.addons.muk_dms.models import dms_base

_logger = logging.getLogger(__name__)


class Repository(dms_base.DMSModel):
    _name = 'gesion_dms.repository'   # 文件库
    _description = "Gesion Documents Repository"

    _inherit = ['mail.thread', 'muk_dms.access']
    name = fields.Char('File library name', required=True)
    is_project = fields.Boolean(string='Is Project')
    project_id = fields.Many2one('project.project', string='Project Name')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    organization_id = fields.Many2one(related='project_id.organization_id')
    folder_ids = fields.One2many('muk_dms.directory', 'repository_id', string='Folders')   # 文件库关联文件夹
    doc_count = fields.Integer(string='Document Count', compute='_count_doc')     # 文件数量

    # project information
    project_code = fields.Char(related='project_id.project_code')  # 项目编号
    design_manager = fields.Many2one('res.partner', related='project_id.design_manager')   # 设计经理
    project_manager = fields.Many2one('res.partner', related='project_id.project_manager')  # 项目经理
    craft_package = fields.Char(related='project_id.craft_package')
    # address_id = fields.Many2one('res.partner', related='project_id.address_id')   # 项目地址
    proprietor = fields.Many2one('res.partner', related='project_id.proprietor')
    document_control_users = fields.Many2many('res.users', related='project_id.document_control_users')    # 文件关联用户
    has_child = fields.Boolean(string='Has Child', compute='_compute_has_child')  # 是否拥有子节点
    seq = fields.Char(string='SEQ')

    earned_value = fields.Float(string='Total Earned Value', compute='_compute_earned_value',
                                digits=dp.get_precision('Product Unit of Measure'))
    absolute_weight = fields.Float(string='Absolute Weight', default=1, digits=dp.get_precision('Product Unit of Measure'))

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Photo", attachment=True,
                          help="This field holds the image used as photo for the repository, limited to 1024x1024px.")
    image_medium = fields.Binary("Medium-sized photo", attachment=True,
                                 help="Medium-sized photo of the repository. It is automatically "
                                      "resized as a 128x128px image, with aspect ratio preserved. "
                                      "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized photo", attachment=True,
                                help="Small-sized photo of the repository. It is automatically "
                                     "resized as a 64x64px image, with aspect ratio preserved. "
                                     "Use this field anywhere a small image is required.")
    repository_code = fields.Char(size=16, string='Repository Code')
    man_hours = fields.Integer('Man Hours')
    labor_cost = fields.Float('Labor Cost')
    labor_cost_unit = fields.Float('Labor Cost Unit')
    description = fields.Text(string="Description")
    task_id = fields.Many2one('project.task', string='Task')

    @api.multi
    def _count_doc(self):
        for record in self:
            record.doc_count = self.env['muk_dms.file'].search_count([('repository_id', '=', record.id)])

    @api.depends('folder_ids')  # 判断是否拥有子节点
    @api.multi
    def _compute_has_child(self):
        for record in self:
            record.has_child = True if record.folder_ids else False

    @api.depends('folder_ids.earned_value')
    @api.multi
    def _compute_earned_value(self):
        for record in self:
            record.earned_value = sum(record.folder_ids.mapped(lambda r: r.earned_value))

    @api.model
    def _default_image(self):
        image_path = get_module_resource('gesion_dms', 'static/src/img', 'repository.png')
        return tools.image_resize_image_big(open(image_path, 'rb').read().encode('base64'))

    @api.model
    def create(self, vals):
        if not vals.get('image'):
            vals['image'] = self._default_image()
        tools.image_resize_images(vals)
        return super(Repository, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals)
        return super(Repository, self).write(vals)


#------------------------

    def get_all_tree(self):
        all_data = []
        # repository_list = []
        # repository_data = self.env['gesion_dms.repository'].search_read(fields=['id',
        #                                                                         'earned_value',
        #                                                                         'absolute_weight',
        #                                                                         'folder_ids'])
        # repository_list.extend(map(lambda r: {'model': 'gesion_dms.repository',
        #                                       'data': {
        #                                           'id': r.get('id'),
        #                                           'earned_value': r.get('earned_value'),
        #                                           'absolute_weight': r.get('absolute_weight'),
        #                                           'folder_ids': r.get('folder_ids'),
        #                                       }
        #                                       }, repository_data))
        # repository = self.env(['gesion_dms.repository']).search()
        # for rep in repository:
        directory_list = []
        directory_data = self.env['muk_dms.directory'].search_read(fields=['id',
                                                                             'repository_id',
                                                                             'parent_directory',
                                                                             'output',
                                                                             'relativity_weight',
                                                                             'absolute_weight',
                                                                             'earned_value',
                                                                             'hierarchy',
                                                                             'child_directories',
                                                                             'files'])
        directory_list.extend(map(lambda r: {'model': 'muk_dms.directory',
                                             'data': {
                                                 'id': r.get('id'),
                                                 'repository_id': r.get('repository_id'),
                                                 'parent_directory': r.get('parent_directory'),
                                                 'output': r.get('output'),
                                                 'relativity_weight': r.get('relativity_weight'),
                                                 'absolute_weight': r.get('absolute_weight'),
                                                 'earned_value': r.get('earned_value'),
                                                 'hierarchy': r.get('hierarchy'),
                                                 'child_directories': r.get('child_directories'),
                                                 'files': r.get('files')
                                             }}, directory_data))

        directory_list_sort = sorted(directory_list, key=lambda r: r['data']['hierarchy'])
        # max_hierarchy = directory_list_sort[-1]['data']['hierarchy']
        file_data = self.env['muk_dms.file'].search_read(fields=['id',
                                                                   'repository_id',
                                                                   'input_progress',
                                                                   'directory',
                                                                   'relativity_weight',
                                                                   'absolute_weight',
                                                                   'earned_value',
                                                                   'hierarchy'])
        file_list = []
        file_list.extend(map(lambda r: {'model': 'muk_dms.file',
                                        'data': {
                                            'id': r.get('id'),
                                            'directory': r.get('directory'),
                                            'input_progress': r.get('input_progress'),
                                            'relativity_weight': r.get('relativity_weight'),
                                            'absolute_weight': r.get('absolute_weight'),
                                            'earned_value': r.get('earned_value'),
                                            'hierarchy': r.get('hierarchy')
                                        }}, file_data))
        # absolute weight
        # directory_file_list =[]
        # all_data.extend(repository_list)
        all_data.extend(directory_list_sort)
        all_data.extend(file_list)
        # return max_hierarchy, all_data
        return all_data


    # def calculate_rw(self,max_hierarchy,tree=[]):
    #     for i in xrange(1,max_hierarchy+1):
    #         # 当前节点
    #         for current_node in tree:
    #             # 第一级的时候判断相对权重=绝对权重
    #             if current_node['model'] == 'muk_dms.directory' and current_node['data'].get('hierarchy') == 1:
    #                 current_node['data']['absolute_weight'] = current_node['data']['relativity_weight']
    #             else:
    #                 for relate_node in tree:
    #                     if (current_node['data'].get('parent_directory') == relate_node['data']['id'] and current_node['data'].get('hierarchy') == i ) or (current_node['data'].get('directory') == relate_node['data']['id']):

    def calculation(self, tree=[]):
        all_data = {}
        directory_list_sort = sorted(tree, key=lambda r: r['data']['hierarchy'])
        for record in directory_list_sort:
            if record['model'] == 'muk_dms.directory':
                if record['data']['parent_directory'] is False:
                    all_data['directory_{}'.format(record['data']['id'])] = Node(
                        name='directory_{}'.format(record['data']['id']),
                        RW=record['data']['relativity_weight'])
                else:
                    all_data['directory_{}'.format(record['data']['id'])] = Node(
                        name='directory_{}'.format(record['data']['id']),
                        parent_node=all_data['directory_{}'.format(record['data']['parent_directory'][0])],
                        RW=record['data']['relativity_weight'])
            elif record['model'] == 'muk_dms.file':
                all_data['file_{}'.format(record['data']['id'])] = Node(name='file_{}'.format(record['data']['id']),
                                                                        parent_node=all_data['directory_{}'.format(
                                                                            record['data']['directory'][0])],
                                                                        RW=record['data']['relativity_weight'],
                                                                        input_value=record['data'][
                                                                            'input_progress'])
        store_directory_data = []
        store_file_data = []
        for v in all_data.itervalues():
            if v.name.split('_')[0] == 'directory':
                result = {'id': int(v.name.split('_')[1]), 'absolute_weight': v.AW, 'earned_value': v.EV, 'output': v.output}
                store_directory_data.append(result)
            elif v.name.split('_')[0] == 'file':
                result = {'id': int(v.name.split('_')[1]), 'absolute_weight': v.AW, 'earned_value': v.EV}
                store_file_data.append(result)
        for directory in store_directory_data:
            self.env['muk_dms.directory'].browse(directory['id']).write({'absolute_weight':directory['absolute_weight'], 'earned_value':directory['earned_value'],'output':directory['output']})
            # print self.env['muk_dms.directory'].search(['id', '=', directory['id']]).write(directory)
        for file in store_file_data:
            self.env['muk_dms.file'].browse(file['id']).write({'absolute_weight':file['absolute_weight'], 'earned_value':file['earned_value']})
            # print self.env['muk_dms.file'].sudo().write(file)

    def calculation_check_button(self):
        all_data = self.get_all_tree()
        self.calculation(all_data)


#---------------------------------------


    def get_man_hour_tree(self):
        repository_data = self.env['gesion_dms.repository'].search_read(fields=['id',
                                                                                'man_hours'])

        directory_data = self.env['muk_dms.directory'].search_read(fields=['id',
                                                                           'repository_id',
                                                                           'parent_directory',
                                                                           'hierarchy',
                                                                           'relativity_weight',
                                                                           'man_hours'])

        file_data = self.env['muk_dms.file'].search_read(fields=['id',
                                                                 'directory',
                                                                 'relativity_weight',
                                                                 'man_hours',
                                                                 'hierarchy'])

        repository_list = []
        repository_list.extend(map(lambda r: {'model': 'gesion_dms.repository',
                                             'data': {
                                                 'id': r.get('id'),
                                                 'man_hours': r.get('man_hours'),
                                                 'hierarchy': r.get('hierarchy'),
                                             }}, repository_data))

        directory_list = []
        directory_list.extend(map(lambda r: {'model': 'muk_dms.directory',
                                             'data': {
                                                 'id': r.get('id'),
                                                 'repository_id': r.get('repository_id'),
                                                 'parent_directory': r.get('parent_directory'),
                                                 'hierarchy': r.get('hierarchy'),
                                                 'man_hours': r.get('man_hours'),
                                             }}, directory_data))
        directory_list = sorted(directory_list, key=lambda r: r['data']['hierarchy'])

        file_list = []
        file_list.extend(map(lambda r: {'model': 'muk_dms.file',
                                        'data': {
                                            'id': r.get('id'),
                                            'relativity_weight': r.get('relativity_weight'),
                                            'directory': r.get('directory'),
                                            'hierarchy': r.get('hierarchy'),
                                            'man_hours': r.get('man_hours'),
                                        }}, file_data))
        all_data = []
        all_data.extend(repository_list)
        all_data.extend(directory_list)
        all_data.extend(file_list)
        return all_data

    def calculation_rweight(self, tree=[]):
        all_data = {}
        directory_list_sort = sorted(tree, key=lambda r: r['data']['hierarchy'])
        for record in directory_list_sort:
            if record['model'] == 'gesion_dms.repository':
                all_data['repository_{}'.format(record['data']['id'])] = ManHour(
                    name='repository_{}'.format(record['data']['id']),
                    man_hour=record['data']['man_hours'])
            elif record['model'] == 'muk_dms.directory':
                if record['data']['parent_directory'] is False:
                    all_data['directory_{}'.format(record['data']['id'])] = ManHour(
                        name='directory_{}'.format(record['data']['id']),
                        parent_node=all_data['repository_{}'.format(record['data']['repository_id'][0])],
                        man_hour=record['data']['man_hours'])
                else:
                    all_data['directory_{}'.format(record['data']['id'])] = ManHour(
                        name='directory_{}'.format(record['data']['id']),
                        parent_node=all_data['directory_{}'.format(record['data']['parent_directory'][0])],
                        man_hour=record['data']['man_hours'])
            elif record['model'] == 'muk_dms.file':
                all_data['file_{}'.format(record['data']['id'])] = ManHour(name='file_{}'.format(record['data']['id']),
                                                                        parent_node=all_data['directory_{}'.format(
                                                                            record['data']['directory'][0])],
                                                                        man_hour=record['data'][
                                                                            'man_hours'])
        store_repository_data = []
        store_directory_data = []
        store_file_data = []
        for v in all_data.itervalues():
            if v.name.split('_')[0] == 'repository':
                result = {'id': int(v.name.split('_')[1]), 'relativity_weight': v.RW}
                store_repository_data.append(result)
            elif v.name.split('_')[0] == 'directory':
                result = {'id': int(v.name.split('_')[1]), 'relativity_weight': v.RW}
                store_directory_data.append(result)
            elif v.name.split('_')[0] == 'file':
                result = {'id': int(v.name.split('_')[1]), 'relativity_weight': v.RW}
                store_file_data.append(result)
        # for repository in store_repository_data:
        #     self.env['gesion_dms.repository'].browse(repository['id']).write({'relativity_weight': repository['relativity_weight']})
        for directory in store_directory_data:
            self.env['muk_dms.directory'].browse(directory['id']).write({'relativity_weight': directory['relativity_weight']})
            # print self.env['muk_dms.directory'].search(['id', '=', directory['id']]).write(directory)
        for file in store_file_data:
            self.env['muk_dms.file'].browse(file['id']).write({'relativity_weight': file['relativity_weight']})
            # print self.env['muk_dms.file'].sudo().write(file)

    def calculation_relativity_weight(self):
        all_data = self.get_man_hour_tree()
        self.calculation_rweight(all_data)






class Node(object):
    def __init__(self, name="Node", parent_node=None, child_nodes=None, RW=0.0, input_value=None):
        self.name = name
        self.parent_node = parent_node
        self.child_nodes = child_nodes or set()
        self.RW = RW
        self.input_value = input_value
        if self.parent_node is not None:
            self.parent_node.child_nodes.add(self)

    @property
    def AW(self):
        if self.parent_node is None:
            return self.RW
        return self.RW * self.parent_node.AW
    @property
    def EV(self):
        if self.input_value is None:
            return sum([child_node.EV for child_node in self.child_nodes])
        else:
            return self.input_value * self.AW

    @property
    def output(self):
        if self.AW > 0:
            return self.EV/self.AW
        else:
            return 0


    # def summary(self):
    #     yield {'model':self.name.split('_')[0], 'data':{'id': self.name.split(('_')[1]), 'absolute_weight':self.AW, 'earned_value': self.EV}}
    #     for child_ndoe in self.child_nodes:
    #         child_ndoe.summary()


class ManHour(object):
    def __init__(self, name='Node', parent_node=None, child_nodes=None, man_hour=0.0):
        self.name = name
        self.parent_node = parent_node
        self.child_nodes = child_nodes or set()
        self.man_hour = man_hour
        if self.parent_node is not None:
            self.parent_node.child_nodes.add(self)

    @property
    def RW(self):
        if self.parent_node is None:
            return 1
        else:
            if self.parent_node.man_hour > 0.0:
                return float(self.man_hour)/float(self.parent_node.man_hour)
            else:
                return 0