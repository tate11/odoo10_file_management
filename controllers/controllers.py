
# -*- coding: utf-8 -*-
import json
import logging
import re
import traceback
import time

from openerp import SUPERUSER_ID
from openerp import http, _
from openerp.http import request

_logger = logging.getLogger(__name__)
_schema = logging.getLogger(__name__ + '.schema')


class GesionDMSApi(http.Controller):

    @http.route(['/gesion_api/dms/table_data'], type="json", auth='public', website=True)
    def table_data(self, nodes=[], **kwargs):
        columns = [{"field": "type", "title": "类型"},
                   {"field": "name", "title": "名称"},
                   {"field": "desc", "title": "描述"}]
        data = []
        for node in nodes:
            [node_type, node_id] = node.split('_', 1)
            node_ins = request.env[node_type].browse(int(node_id))
            row_data = node_ins.child_ids.mapped(lambda r: {"model": "organization_{}".format(r.id),
                                                            "type": r.organization_type,
                                                            "name": r.name,
                                                            "desc": r.description})
            # get employee information
            employees = []
            if node_ins.organization_type == "company":
                employees = request.env['hr.employee'].search_read(fields=['name', 'description'],
                                                                   domain=[('company_id', '=', node_ins.company_id.id)])
            elif node_ins.organization_type == "department":
                employees = request.env['hr.employee'].search_read(fields=['name', 'description'],
                                                                   domain=[('department_id', '=', node_ins.department_id.id)])
            elif node_ins.organization_type == "project":
                users = request.env['project.task'].search_read(fields=['user_id'],
                                                                domain=[('project_id', '=', node_ins.project_id.id)])
                user_ids = map(lambda r: r.get("user_id"), users)
                employees = request.env['hr.employee'].search_read(fields=['name', 'description'],
                                                                   domain=[('user_id', 'in', user_ids)])
            row_data.extend(map(lambda r: {"model": "employee_{}".format(r.get('id')),
                                           "type": "human",
                                           "name": r.get('name'),
                                           "desc": r.get('description')}, employees))
            data.append(row_data)
        return {"columns": columns, "data": data}

    @staticmethod
    def get_parent_node_ids_which_children_loaded(parent_key_and_data={}):
        parent_set = set()
        for parent_key in parent_key_and_data:
            parent_set.update(set(map(lambda x: x[parent_key], parent_key_and_data[parent_key])))
        return parent_set

    @staticmethod
    def node_data_constructor(fetched_data, model, init=True, parent_d_ids=[]):
        return_data = []
        for d in fetched_data:
            join_left = d.get("seq") or " "
            d_text = " ".join([join_left, d.get("name")])
            if model == "gesion.organization":
                d_id = "{}_{}".format(model, d.get("id"))
                d_parent_id = "{}_{}".format(model, d.get("parent_id")) if d.get("parent_id") else "#"
                '''
                Set children=True shows a folder that can be open,but if node's children loading with node at 
                the same time while initializing, parent node's children must be set []
                '''
                if init:
                    children = [] if (d.get("id") in parent_d_ids or not d.get("has_child")) else True
                    node_state = {"opened": True}
                else:
                    children = True if d.get("has_child") else []
                    node_state = {}
                browser = request.env[model].browse(d.get("id"))
                # print "%s: %s" % (model, d_id)
                # print browser.check_access_rights('read')
                # print browser.check_access_rights('create')
                # print browser.check_access_rights('write')
                # print browser.check_access_rights('unlink')
                node_data = {
                    "id": d_id,
                    "children": children,
                    "parent": d_parent_id,
                    "text": d_text,
                    "icon": "fa fa-folder-o",
                    "type": model,
                    "seq": d.get("seq"),
                    "state": node_state,        # {"opened": True}
                    "data": {
                        "container": False,
                        "odoo_id": d.get("id"),
                        "odoo_parent_id": d.get("parent_id"),
                        "odoo_model": model,
                        "perm_read": browser.perm_read,
                        "perm_create": browser.perm_create,
                        "perm_write": browser.perm_write,
                        "perm_unlink": browser.perm_unlink
                    }
                }
            return_data.append(node_data)
        return return_data

    @http.route(['/gesion_api/organization_tree_init_data',
                 '/gesion_api/organization_tree_init_data/<string:node_id>',
                 '/gesion_api/organization_tree_init_data/<string:node_id>/<int:hierarchy>'
                 ], type="http", auth='public', website=True)
    def organization_tree_init_data(self, node_id='#', hierarchy=2, **kwargs):
        if node_id != '#':
            return _('Error tree root!')
        # sql way
        # cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        # sql_organization = """SELECT id, name, seq, parent_id, has_child FROM gesion_organization
        #           WHERE hierarchy <= %s ORDER BY id ASC;"""
        # params = (hierarchy,)
        # cr.execute(sql_organization, params)
        # fetched_organization_data = cr.dictfetchall()
        # orm way
        organization_data = request.env['gesion.organization'].search_read(fields=['name', 'seq', 'parent_id', 'has_child'],
                                                                           domain=[('hierarchy', '<=', hierarchy)],
                                                                           order='id')
        fetched_organization_data = map(lambda r: {'id': r.get('id'),
                                                   'seq': r.get('seq'),
                                                   'name': r.get('name'),
                                                   'has_child': r.get('has_child'),
                                                   'parent_id': r.get('parent_id')[0] if r.get('parent_id') else False
                                                   }, organization_data)
        parent_d_ids = self.get_parent_node_ids_which_children_loaded({"parent_id": fetched_organization_data})
        initial_data = self.node_data_constructor(fetched_organization_data, "gesion.organization", True, parent_d_ids)
        return_data = json.dumps(initial_data)
        return request.make_response(return_data, headers=[('Content-Length', len(return_data)),
                                                           ('Content-Type', 'application/json; charset=utf-8')])

    @http.route(['/gesion_api/organization_tree_data',
                 '/gesion_api/organization_tree_data/<string:node_id>'], type="http", auth='public', website=True)
    def organization_tree_data(self, node_id, **kwargs):
        node_num_id = node_id.split('_', 1)[1]
        # sql way
        # cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        # sql_organization = """SELECT id, name, seq, parent_id, has_child FROM gesion_organization
        #                   WHERE parent_id = %s ORDER BY id ASC;"""
        # params = (node_num_id,)
        # cr.execute(sql_organization, params)
        # fetched_organization_data = cr.dictfetchall()
        # orm way
        organization_data = request.env['gesion.organization'].search_read(fields=['name', 'seq', 'parent_id', 'has_child'],
                                                                           domain=[('parent_id', '=', int(node_num_id))],
                                                                           order='id')
        fetched_organization_data = map(lambda r: {'id': r.get('id'),
                                                   'seq': r.get('seq'),
                                                   'name': r.get('name'),
                                                   'has_child': r.get('has_child'),
                                                   'parent_id': r.get('parent_id')[0] if r.get('parent_id') else False
                                                   }, organization_data)
        tree_data = self.node_data_constructor(fetched_organization_data, "gesion.organization", False)
        return_data = json.dumps(tree_data)
        # < type
        # 'list' >: [{'state': {}, 'data': {'perm_write': True, 'odoo_id': 8, 'container': False, 'perm_unlink': True,
        #                                   'odoo_parent_id': 7, 'perm_read': True, 'perm_create': True,
        #                                   'odoo_model': 'gesion.organization'}, 'parent': 'gesion.organization_7',
        #             'seq': None, 'text': u'  test', 'icon': 'fa fa-folder-o', 'type': 'gesion.organization',
        #             'id': 'gesion.organization_8', 'children': []}]
        return request.make_response(return_data, headers=[('Content-Length', len(return_data)),
                                                           ('Content-Type', 'application/json; charset=utf-8')])

# --------------------------------
# ----------------------------------
# --------------------------------
    # 文件树状图


    @staticmethod
    def judge_directory_has_child(directory_ids):
        has_child_directory = []
        directory_ids = list(directory_ids)
        for directory_id in directory_ids:
            directory = request.env['muk_dms.directory'].browse(int(directory_id))
            if len(directory.child_directories):
                has_child_directory.append(directory_id)
        return has_child_directory

    @staticmethod
    def node_directory_constructor(fetched_data, model, init=True, parent_d_ids=[], has_child_directory=[]):
        return_data = []
        for d in fetched_data:
            join_left = d.get("seq") or " "
            d_text = " ".join([join_left, d.get("name")])
            if model == "gesion_dms.repository":
                d_id = "{}_{}".format(model, d.get("id"))
                d_parent_id = "#"
                if init:
                    children = [] if (d.get("id") in parent_d_ids ) else True  # 判断下级节点是否存在
                    node_state = {"opened": True}
                browser = request.env[model].browse(d.get("id"))
                node_data = {
                    "id": d_id,
                    "children": children,
                    "parent": d_parent_id,
                    "text": d_text,
                    "icon": "fa fa-bookmark-o",
                    "type": model,
                    "seq": d.get("seq"),
                    "state": node_state,
                    "data": {
                        "container": False,
                        "odoo_id": d.get("id"),
                        "odoo_parent_id": None,
                        "odoo_model": model,
                        "perm_read": browser.perm_read,
                        "perm_create": browser.perm_create,
                        "perm_write": browser.perm_write,
                        "perm_unlink": browser.perm_unlink
                    }
                }
            # 文件夹
            elif model == "muk_dms.directory":
                d_id = "{}_{}".format(model, d.get("id"))  # 模型+id名字
                if d.get("is_root_directory"):
                    d_parent_id = "{}_{}".format('gesion_dms.repository', d.get("repository_id")) if d.get("repository_id") else "#"  # 上级节点名字
                    odoo_parent_id = d.get("repository_id")
                else:
                    d_parent_id = "{}_{}".format(model, d.get("parent_directory")) if d.get(
                        "parent_directory") else "#"  # 上级节点名字
                    odoo_parent_id = d.get("parent_directory")
                '''
                Set children=True shows a folder that can be open,but if node's children loading with node at 
                the same time while initializing, parent node's children must be set []
                '''
                if d.get('parent_directory'):
                        children = True if d.get("id") in has_child_directory else []
                        node_state = {}
                else:
                    if init:
                        children = [] if (d.get("id") in parent_d_ids or  d.get("id") in has_child_directory) else True
                        node_state = {"opened": True}
                    else:
                        children = True if d.get("id") in has_child_directory else []
                        node_state = {}
                browser = request.env[model].browse(d.get("id"))
                node_data = {
                    "id": d_id,  # 当前节点名字
                    "children": children,  # 是否展示下级节点
                    "parent": d_parent_id,  # 上级节点名字
                    "text": d_text,  # 节点名称
                    "icon": "fa fa-folder-o",
                    "type": model,
                    "seq": d.get("seq"),
                    "state": node_state,  # {"opened": True}
                    "data": {
                        "container": False,
                        "odoo_id": d.get("id"),
                        "odoo_parent_id": odoo_parent_id,
                        "odoo_model": model,
                        "perm_read": browser.perm_read,
                        "perm_create": browser.perm_create,
                        "perm_write": browser.perm_write,
                        "perm_unlink": browser.perm_unlink
                    }
                }
            #     # 文件
            # elif model == 'muk_dms.file':
            #     d_id = "{}_{}".format(model, d.get("id"))  # 模型+id名字
            #     d_parent_id = "{}_{}".format('muk_dms.directory', d.get("directory")) if d.get("directory") else "#"  # 上级节点名字
            #
            #     node_data = {
            #         "id": d_id,  # 当前节点名字
            #         # "children": True,  # 是否展示下级节点
            #         "parent": d_parent_id,  # 上级节点名字
            #         "text": d_text,  # 节点名称
            #         "icon": "fa fa-file",
            #         "type": model,
            #         "seq": d.get("seq"),
            #         "state": {},  # {"opened": True}
            #         "data": {
            #             "container": False,
            #             "odoo_id": d.get("id"),
            #             "odoo_parent_id": None,
            #             "odoo_model": model,
            #             "perm_read": True,
            #             "perm_create": True,
            #             "perm_write": True,
            #             "perm_unlink": True,
            #
            #         }
            #     }
            return_data.append(node_data)
        return return_data

    @http.route(['/gesion_api/directory_tree_init_data',
                 '/gesion_api/directory_tree_init_data/<string:node_id>',
                 '/gesion_api/directory_tree_init_data/<string:node_id>/<int:hierarchy>'
                 ], type="http", auth='public', website=True)
    def directory_tree_init_data(self, node_id='#', hierarchy=2, **kwargs):
        if node_id != '#':
            return _('Error tree root!')
        # sql way
        # cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        # sql_repository = """SELECT id, name, seq FROM gesion_dms_repository ORDER BY id ASC;"""
        # sql_directory = """SELECT id, name, seq, repository_id, parent_directory, is_root_directory FROM muk_dms_directory
        #                       WHERE hierarchy <= %s ORDER BY id ASC;"""
        # # sql_file = """SELECT id, name, directory, seq FROM muk_dms_file
        # #                       WHERE hierarchy <= %s;"""
        # params = (hierarchy,)
        # cr.execute(sql_repository)
        # fetched_repository_data = cr.dictfetchall()
        # cr.execute(sql_directory, params)
        # fetched_directory_data = cr.dictfetchall()
        # # cr.execute(sql_file,params)
        # # fetchem_file_data = cr.dictfetchall()
        # orm way
        fetched_repository_data = request.env['gesion_dms.repository'].search_read(fields=['name', 'seq'], order='id')
        directory_data = request.env['muk_dms.directory'].search_read(fields=['name', 'seq', 'repository_id',
                                                                              'parent_directory', 'is_root_directory'],
                                                                      domain=[('hierarchy', '<=', hierarchy)],
                                                                      order='id')
        fetched_directory_data = map(lambda r: {'id': r.get('id'),
                                                'seq': r.get('seq'),
                                                'name': r.get('name'),
                                                'repository_id': r.get('repository_id')[0] if r.get('repository_id') else False,
                                                'parent_directory': r.get('parent_directory')[0] if r.get('parent_directory') else False,
                                                'is_root_directory': r.get('is_root_directory'),
                                                }, directory_data)
        repository_parent_d_ids = self.get_parent_node_ids_which_children_loaded({"id": fetched_repository_data})
        directory_repository_d_ids = self.get_parent_node_ids_which_children_loaded({'repository_id': fetched_directory_data})
        # directory_d_ids = self.get_parent_node_ids_which_children_loaded({'parent_directory': fetched_directory_data})
        # file_d_ids = self.get_parent_node_ids_which_children_loaded({'parent_directory':fetched_directory_data})
        directory_ids = self.get_parent_node_ids_which_children_loaded(({'id': fetched_directory_data}))
        has_child_directory_id = self.judge_directory_has_child(directory_ids)

        initial_data = self.node_directory_constructor(fetched_repository_data, "gesion_dms.repository", True, repository_parent_d_ids)
        initial_data.extend(self.node_directory_constructor(fetched_directory_data, "muk_dms.directory", True, directory_repository_d_ids,has_child_directory_id))
        # initial_data.extend(self.node_directory_constructor(fetched_directory_data, "muk_dms.directory", True, directory_d_ids))
        # initial_data.extend(self.node_directory_constructor(fetchem_file_data, "muk_dms.file", True, file_d_ids))
        return_data = json.dumps(initial_data)
        return request.make_response(return_data, headers=[('Content-Length', len(return_data)),
                                                           ('Content-Type', 'application/json; charset=utf-8')])




    @http.route(['/gesion_api/directory_tree_data',
                 '/gesion_api/directory_tree_data/<string:node_id>'], type="http", auth='public', website=True)
    def directory_tree_data(self, node_id, **kwargs):
        if "file" in node_id:
            return _('Error node type!')
        node_num_id = node_id.split('_', 2)[2]
        # sql way
        # cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        # sql_directory = """SELECT id, name, repository_id, parent_directory, seq FROM muk_dms_directory
        #                               WHERE parent_directory = %s ORDER BY id ASC;"""
        # # sql_file = """SELECT id, name, directory, seq FROM muk_dms_file
        # #                               WHERE directory = %s;"""
        # params = (node_num_id,)
        # cr.execute(sql_directory, params)
        # fetched_directory_data = cr.dictfetchall()
        # # cr.execute(sql_file, params)
        # # fetched_file_data = cr.dictfetchall()
        # orm way
        directory_data = request.env['muk_dms.directory'].search_read(fields=['name', 'seq', 'repository_id',
                                                                              'parent_directory'],
                                                                      domain=[('parent_directory', '=', int(node_num_id))],
                                                                      order='id')
        fetched_directory_data = map(lambda r: {'id': r.get('id'),
                                                'seq': r.get('seq'),
                                                'name': r.get('name'),
                                                'repository_id': r.get('repository_id')[0] if r.get(
                                                    'repository_id') else False,
                                                'parent_directory': r.get('parent_directory')[0] if r.get(
                                                    'parent_directory') else False,
                                                # 'is_root_directory': r.get('is_root_directory'),
                                                }, directory_data)
        directory_ids = self.get_parent_node_ids_which_children_loaded(({'id': fetched_directory_data}))
        has_child_directory_id = self.judge_directory_has_child(directory_ids)
        tree_data = self.node_directory_constructor(fetched_directory_data, "muk_dms.directory", False,
                                                    has_child_directory=has_child_directory_id)
        # tree_data.extend(self.node_directory_constructor(fetched_file_data, "muk_dms.file", False))
        return_data = json.dumps(tree_data)
        return request.make_response(return_data, headers=[('Content-Length', len(return_data)),
                                                           ('Content-Type', 'application/json; charset=utf-8')])

    # bootstrap-table
    @http.route(['/gesion_api/dms/directory_table_data'], type="json", auth='public', website=True)
    def directory_table_data(self, nodes=[], **kwargs):
        columns = [{"field": "type", "title": "类型"},
                   {"field": "seq", "title": "排序"},
                   {"field": "coding", "title": "编号"},
                   {"field": "name", "title": "名称"},
                   {"field": "description", "title": "描述"},
                   {"field": "relative_weight", "title": "相对权重"},
                   {"field": "absolute_weight", "title": "绝对权重"},
                   {"field": "progress", "title": "自身进度"},
                   {"field": "earned_value", "title": "赢得值"},
                   {"field": "man_hours", "title": "人工时"},
                   {"field": "man_hours_rate", "title": "人工单价"},
                   {"field": "currency", "title": "货币"},
                   {"field": "labor_cost", "title": "人工费"},
                   {"field": "tag", "title": "标签"},]
        data = []
        for node in nodes:
            [node_type, node_id] = node.rsplit('_', 1)
            node_ins = request.env[node_type].browse(int(node_id))
            if node_type == 'gesion_dms.repository':
                row_data = node_ins.folder_ids.mapped(lambda r: {"model": "muk_dms.directory_{}".format(r.id),
                                                                "type": 'directory',
                                                                "seq": r.seq,
                                                                "coding": r.directory_code,
                                                                "name": r.name,
                                                                "description": r.description,
                                                                "relative_weight": r.relativity_weight,
                                                                "absolute_weight": r.absolute_weight,
                                                                "progress": None,
                                                                "earned_value": r.earned_value,
                                                                "man_hours": r.man_hours,
                                                                "man_hours_rate": None,
                                                                "currency": None,
                                                                "labor_cost": r.labor_cost,
                                                                "tag": None,
                                                                "odoo_id": r.id})
            elif node_type == 'muk_dms.directory':
                row_data = node_ins.child_directories.mapped(lambda r: {"model": "muk_dms.directory_{}".format(r.id),
                                                                 "type": 'directory',
                                                                 "seq": r.seq,
                                                                 "coding": r.directory_code,
                                                                 "name": r.name,
                                                                 "description": r.description,
                                                                 "relative_weight": r.relativity_weight,
                                                                 "absolute_weight": r.absolute_weight,
                                                                 "progress": None,
                                                                 "earned_value": r.earned_value,
                                                                 "man_hours": r.man_hours,
                                                                 "man_hours_rate": None,
                                                                 "currency": None,
                                                                 "labor_cost": r.labor_cost,
                                                                 "tag": None,
                                                                 "odoo_id": r.id})

                if len(node_ins.files) :
                    files = request.env['muk_dms.file'].search_read(fields=['name',
                                                                            'seq',
                                                                            'document_number',
                                                                            'document_description',
                                                                            'relativity_weight',
                                                                            'absolute_weight',
                                                                            'progress',
                                                                            'earned_value',
                                                                            'man_hours',
                                                                            'labor_cost'],
                                                                    domain=[('directory', '=', node_ins.id)])
                    row_data.extend(map(lambda r: {"model": "muk_dms.file_{}".format(r.get('id')),
                                                   "type": 'file',
                                                   "seq": r.get('seq'),
                                                   "coding": r.get('document_number'),
                                                   "name": r.get('name'),
                                                   "description": r.get('document_description'),
                                                   "relative_weight": r.get('relativity_weight'),
                                                   "absolute_weight": r.get('absolute_weight'),
                                                   "progress": r.get('progress'),
                                                   "earned_value": r.get('earned_value'),
                                                   "man_hours": r.get('man_hours'),
                                                   "man_hours_rate": None,
                                                   "currency": None,
                                                   "labor_cost": r.get('labor_cost'),
                                                   "tag": None,
                                                   "odoo_id": r.get('id')}, files))

            data.append(row_data)
        return {"columns": columns, "data": data}

#----------------------

    @http.route(['/gesion_json_api/carousel_data'], type="json", auth='public', website=True)
    def carousel_map_json_data(self, project_id, **kwargs):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        if not isinstance(project_id,int):
            return _('Error project id type!')
        if project_id <= 0:
            return _('Error project id type!')
        project = request.env['project.project'].browse(int(project_id))
        # project_task_id = (project_id,)
        if not project.active:
            return _('Project not activated!')
        task = request.env['project.task'].sudo().search_read(fields=['project_id',
                                                                      'seq',
                                                                      'name',
                                                                      'parent_task',
                                                                      'task_level',
                                                                      'task_number',
                                                                      'input_progress',
                                                                      'man_hours',
                                                                      'labor_cost',
                                                                      'labor_cost_unit',
                                                                      'doc_number',
                                                                      'convert_a1',
                                                                      'plan_start_date',
                                                                      'actual_start_date',
                                                                      'plan_end_date',
                                                                      'forcast_end_date',
                                                                      'actual_end_date',
                                                                      'early_days',
                                                                      'remark',
                                                                      'grade'],
                                                              domain=[('project_id', '=', project_id)])

        # sql_task = """SELECT project_id, seq, name, parent_task, task_level, task_number, input_progress, man_hours, labor_cost,
        #                     labor_cost_unit, doc_number, convert_a1, plan_start_date, actual_start_date, plan_end_date, forcast_end_date,
        #                      actual_end_date, early_days, remark, grade  FROM project_task
        #                                          WHERE project_id = %s;"""
        # params = (project_id,)
        # cr.execute(sql_task, params)
        # task = cr.dictfetchall()
        task_sort = sorted(task, key=lambda r: r['task_level'])
        task_data = []
        task_data.extend(map(lambda r: {"id": r.get('project_id'),
                                        "seq": r.get('seq'),
                                        "name": r.get('name'),
                                        "parent_id":r.get('parent_task'),
                                        "hierarchy": r.get('task_level'),
                                        "code": r.get('task_number'),
                                        "data":{
                                            "progress": r.get('input_progress'),
                                            "man_hours": r.get('man_hours'),
                                            "labor_cost": r.get('labor_cost'),
                                            "labor_cost_unit":r.get('labor_cost_unit'),
                                            "doc_code": r.get('doc_number'),
                                            "doc_count": r.get('doc_amount'),
                                            "equivalent_a1": r.get('convert_a1'),
                                            "plan_start_date": r.get('plan_start_date'),
                                            "actual_start_date": r.get('actual_start_date'),
                                            "plan_end_date": r.get('plan_end_date'),
                                            "forcast_end_date": r.get('forcast_end_date'),
                                            "actual_end_date": r.get('actual_end_date'),
                                            "days_ahead": r.get('days_ahead'),
                                            "remark": r.get('remark'),
                                            "qaqc_level": r.get('grade'),
                                        }}, task_sort))
        task_data = json.dumps(task_data)
        return task_data
        # return request.make_response(task_data, headers=[('Content-Length', len(task_data)),
        #                                                    ('Content-Type', 'application/json; charset=utf-8')])

    @http.route(['/gesion_api/carousel_data',
                 '/gesion_api/carousel_data/<int:project_id>'], type="http", auth='public', website=True)
    def carousel_map_data(self, project_id, **kwargs):
        cr, uid, context, registry = request.cr, request.uid, request.context, request.registry
        if not isinstance(project_id,int):
            project_id = int(project_id)
            # return _('Error project id type!')
        if project_id <= 0:
            return _('Error project id type!')
        project = request.env['project.project'].browse(int(project_id))
        # project_task_id = (project_id,)
        if not project.active:
            return _('Project not activated!')
        task = request.env['project.task'].sudo().search_read(fields=['project_id',
                                                                      'seq',
                                                                      'name',
                                                                      'parent_task',
                                                                      'task_level',
                                                                      'task_number',
                                                                      'input_progress',
                                                                      'man_hours',
                                                                      'labor_cost',
                                                                      'labor_cost_unit',
                                                                      'doc_number',
                                                                      'convert_a1',
                                                                      'plan_start_date',
                                                                      'actual_start_date',
                                                                      'plan_end_date',
                                                                      'forcast_end_date',
                                                                      'actual_end_date',
                                                                      'early_days',
                                                                      'remark',
                                                                      'grade'],
                                                              domain=[('project_id', '=', project_id)])

        # sql_task = """SELECT project_id, seq, name, parent_task, task_level, task_number, input_progress, man_hours, labor_cost,
        #                     labor_cost_unit, doc_number, convert_a1, plan_start_date, actual_start_date, plan_end_date, forcast_end_date,
        #                      actual_end_date, early_days, remark, grade  FROM project_task
        #                                          WHERE project_id = %s;"""
        # params = (project_id,)
        # cr.execute(sql_task, params)
        # task = cr.dictfetchall()
        task_sort = sorted(task, key=lambda r: r['task_level'])
        task_data = []
        task_data.extend(map(lambda r: {"id": r.get('project_id'),
                                        "seq": r.get('seq'),
                                        "name": r.get('name'),
                                        "parent_id":r.get('parent_task'),
                                        "hierarchy": r.get('task_level'),
                                        "code": r.get('task_number'),
                                        "data":{
                                            "progress": r.get('input_progress'),
                                            "man_hours": r.get('man_hours'),
                                            "labor_cost": r.get('labor_cost'),
                                            "labor_cost_unit":r.get('labor_cost_unit'),
                                            "doc_code": r.get('doc_number'),
                                            "doc_count": r.get('doc_amount'),
                                            "equivalent_a1": r.get('convert_a1'),
                                            "plan_start_date": r.get('plan_start_date'),
                                            "actual_start_date": r.get('actual_start_date'),
                                            "plan_end_date": r.get('plan_end_date'),
                                            "forcast_end_date": r.get('forcast_end_date'),
                                            "actual_end_date": r.get('actual_end_date'),
                                            "days_ahead": r.get('days_ahead'),
                                            "remark": r.get('remark'),
                                            "qaqc_level": r.get('grade'),
                                        }}, task_sort))
        task_data = json.dumps(task_data)
        return task_data
        # return request.make_response(task_data, headers=[('Content-Length', len(task_data)),
        #                                                    ('Content-Type', 'application/json; charset=utf-8')])