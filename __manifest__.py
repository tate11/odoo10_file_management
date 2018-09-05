{
    "name": "Gesion Documents",
    "summary": """Gesion Document Management System""",
    "description": """ 

    """,
    "version": '10.0.0.0.1',
    "category": 'Document Management System',
    "license": "AGPL-3",
    "website": "",
    "author": "Ray",
    "contributors": [
        "Ray <rui.xu@gesion.net>",
    ],
    "depends": [
        "project",
        "hr_contract",
        "muk_dms",
        "muk_dms_access",
        "hr_timesheet",
    ],
    "data": [
        "views/gesion_document_center.xml",
        "workflows/gesion_file_transfer_workflow.xml",
        "security/gesion_dms_groups_security.xml",
        "security/ir.model.access.csv",
        "security/gesion_dms_security.xml",
        "views/assets.xml",
        "views/gesion_organization_views.xml",
        "views/gesion_organization_tree_view.xml",
        "views/gesion_dms_repository.xml",
        "views/inherited_muk_dms_directory_view.xml",
        "wizards/approve_wizard.xml",
        "views/gesion_dms_distribution.xml",
        "views/gesion_dms_link_to.xml",
        "views/inherited_muk_dms_file_views.xml",
        "views/inherited_muk_dms_actions.xml",
        "views/gesion_project_settings.xml",
        "views/gesion_file_version_views.xml",
        "views/inherited_hr_views.xml",
        "views/inherited_res_users_views.xml",
        "data/code.xml",
        "views/inherited_project_task_views.xml",
    ],
    "demo": [
    ],
    "qweb": [
        "static/src/xml/gesion_organization_tree_view_template.xml",
        "static/src/xml/gesion_repository_views.xml",
    ],
    "images": [
    ],
    "external_dependencies": {
        "python": ["dxf2svg", "ezdxf", "svgwrite"],
        "bin": [],
    },
    "application": True,
    "installable": True,

}
# -*- coding: utf-8 -*-
# Author: Ray

