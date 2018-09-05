/**********************************************************************************
* 
*    Copyright (C) 2017 MuK IT GmbH
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Affero General Public License as
*    published by the Free Software Foundation, either version 3 of the
*    License, or (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Affero General Public License for more details.
*
*    You should have received a copy of the GNU Affero General Public License
*    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/

odoo.define('gesion_dms_views.repository', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var framework = require('web.framework');
var form_common = require('web.form_common');

var dms_utils = require('muk_dms.utils');

var Widget = require('web.Widget');
var Dialog = require('web.Dialog');
var Model = require("web.Model");

var PreviewHelper = require('muk_dms_preview_file.PreviewHelper');

var _t = core._t;
var QWeb = core.qweb;

var LOADED_NODE = new Set();
var Directories = new Model('muk_dms.directory', session.user_context);
var Files = new Model('muk_dms.file', session.user_context);

var open = function(self, model, id) {
	self.do_action({
        type: 'ir.actions.act_window',
        res_model: model,
        res_id: id,
        views: [[false, 'form']],
        target: 'current',
        context: session.user_context,
    });
}

var edit = function(self, model, id) {
	self.do_action({
		type: 'ir.actions.act_window',
        res_model: model,
        res_id: id,
        views: [[false, 'form']],
        target: 'current',
        flags: {'initial_mode': 'edit'},
        context: session.user_context,
    });
}

var create = function(self, model, parent,isRepository) {
	var context = {};
	if(isRepository==true && model=="muk_dms.directory"){
		console.log(111111111111111);
		context = $.extend(session.user_context, {
			default_repository_id: parent,
			default_is_root_directory:true,
			default_parent_directory: null
        });
	}else{
		if(model == "muk_dms.file") {
			context = $.extend(session.user_context, {
				default_directory: parent
			});
		} else if(model == "muk_dms.directory") {
			context = $.extend(session.user_context, {
				default_is_root_directory:false,
				default_parent_directory: parent,
			});
		}
	}
	self.do_action({
		type: 'ir.actions.act_window',
        res_model: model,
        views: [[false, 'form']],
        target: 'current',
        context: context,
    });
}

var context_menu_items = function(node, cp) {
	var items = {}
	if(node.data.perm_read) {
		items.open = {
			separator_before: false,
			separator_after: false,
			_disabled: false,
			icon: "fa fa-external-link-square",
			label: _t("Open"),
			action: function(data) {
				var inst = $.jstree.reference(data.reference);
				var	obj = inst.get_node(data.reference);
				open(inst.settings.widget, obj.data.odoo_model, obj.data.odoo_id);
			}
		};
	}
	if(node.data.perm_write) {
		items.edit = {
			separator_before: false,
			separator_after: false,
			_disabled: false,
			icon: "fa fa-pencil",
			label: _t("Edit"),
			action: function(data) {
				var inst = $.jstree.reference(data.reference);
				var	obj = inst.get_node(data.reference);
				edit(inst.settings.widget, obj.data.odoo_model, obj.data.odoo_id);
			}
		};
	}
	if(node.data.odoo_model == "muk_dms.file" && node.data.perm_read) {
		items.download = {
			separator_before: false,
			separator_after: false,
			_disabled: false,
			icon: "fa fa-download",
			label: _t("Download"),
			action: function(data) {
				var inst = $.jstree.reference(data.reference);
				var	obj = inst.get_node(data.reference);
				$.ajax({
	        	    url: obj.data.download_link,
	        	    type: "GET",
	        	    dataType: "binary",
	        	    processData: false,
	        	    beforeSend: function(xhr, settings) {
	        	    	framework.blockUI();
	        	    },
	        	    success: function(data, status, xhr){
	        		  	saveAs(data, obj.data.filename);
	        	    },
	        	    error:function(xhr, status, text) {
	        	    	self.do_warn(_t("Download..."), _t("An error occurred during download!"));
		  			},
	        	    complete: function(xhr, status) {
	        	    	framework.unblockUI();
	        	    },
	        	});
			}
		};
	} else if(node.data.odoo_model == "muk_dms.directory" && node.data.perm_create) {
		items.create = {
			separator_before: false,
			icon: "fa fa-plus-circle",
			separator_after: false,
			label: _t("Create"),
			action: false,
			submenu: {
				directory: {
					separator_before: false,
					separator_after: false,
					label: _t("Directory"),
					icon: "fa fa-folder",
					action: function(data) {
						var inst = $.jstree.reference(data.reference);
						var	obj = inst.get_node(data.reference);
						console.log(obj.data.odoo_id);
						create(inst.settings.widget, "muk_dms.directory", obj.data.odoo_id);
					}
				},
				file : {
					separator_before: false,
					separator_after: false,
					label: _t("File"),
					icon: "fa fa-file",
					action: function(data) {
						var inst = $.jstree.reference(data.reference);
						var	obj = inst.get_node(data.reference);
						create(inst.settings.widget, "muk_dms.file", obj.data.odoo_id);
					}
				},
			}
		};
	} else if(node.data.odoo_model == "gesion_dms.repository" && node.data.perm_create) {
		items.create = {
			separator_before: false,
			icon: "fa fa-plus-circle",
			separator_after: false,
			label: _t("Create"),
			action: false,
			submenu: {
				directory: {
					separator_before: false,
					separator_after: false,
					label: _t("Directory"),
					icon: "fa fa-folder",
					action: function(data) {
						 var inst = $.jstree.reference(data.reference);
						 var	obj = inst.get_node(data.reference);
						 console.log(inst.settings.widget,obj.data.odoo_id,obj.data.odoo_parent_directory);
						 create(inst.settings.widget, "muk_dms.directory", obj.data.odoo_id,true);
					}
				}
			}
		};
	}
	return items;
}

var RepositoryTreeView = Widget.extend({
	template: 'RepositoryTreeView',
	events: {
        "click button.refresh": "refresh",
        "click button.show_preview": "show_preview",
        "click button.hide_preview": "hide_preview",
        "click button.open": "open",
        "click button.edit": "edit",
        "click button.create_file": "create_file",
        "click button.create_directory": "create_directory",
    },
	init: function(parent) {
        this._super(parent);
        this.name = 'Documents';
		this.splitter = false;
    },
    start: function () {
    	this.$('[data-toggle="tooltip"]').tooltip();
        this.load_view();
    },
    refresh: function() {
    	var self = this;
    	// $.when(self.load_directories(self)).done(function (directories, directory_ids) {
    	// 	$.when(self.load_files(self, directory_ids)).done(function (files) {
        	// 	var data = directories.concat(files);
         //    	self.$el.find('.oe_document_tree').jstree(true).settings.core.data = data;
         //    	self.$el.find('.oe_document_tree').jstree(true).refresh();
    	// 	});
    	// });
		self.$el.find('.oe_document_tree').jstree(true).refresh();
    },
	show_table: function(nodes){
        var self = this;
        // var all_nodes = self.$el.find('.oe_document_tree').jstree(true).get_json('#', {});
        // var opened_nodes = flatten(all_nodes.map(function(n){
        //     return get_showed_nodes(n, true, []);
        // }));
		var opened_nodes = [];
		opened_nodes.push(nodes);
        session.rpc('/gesion_api/dms/directory_table_data', {nodes: opened_nodes}).then(function(return_data){
        	//console.log(return_data.data[0]);
            var all_attributes = return_data.data[0];
            console.log(return_data.columns);
            var columns = [];
            //var arr = ["tag","currency","man_hours_rate"];
            return_data.columns.forEach(function (currentValue, index, arr) {
                if(currentValue.field=="tag"){

				}else if(currentValue.field=="man_hours_rate"){

                }else if(currentValue.field=="currency"){

                }
				else{
                    columns.push({
						field: currentValue.field,
						title: currentValue.title,
						align: "center",
						valign: "middle",
						halign: "center",
						falign: "center",
					});
				}
            })
            // devecho_odoo_theme_v10 nav class: o_main_navbar
            // var navbar_height_str = $('.navbar').outerHeight().toString();
            // backend_theme_v10 nav class:   navbar navbar-default main-nav
			var navbar_height_str = "46";
            var boots_table2 = self.$el.find('.oe_document_preview').bootstrapTable('destroy').bootstrapTable({
                columns: columns,
                data: return_data.data[0],
                uniqueId: "model",
                stickyHeader: true,
                stickyHeaderOffsetY: navbar_height_str,
                classes: "o_list_view table table_noborder jinjiang_table table_hover",
                undefinedText: '-',
                striped: true,
                rowStyle: function(){
                    return "";
                },
				onClickRow: function (row) {
                	if(row.type == 'file'){
						_.each(return_data.data[0],function (value,key,list) {
							if(value.name == row.name){
								open(self, 'muk_dms.file', value.odoo_id);
								console.log(open);
							}
                        })
					}else if(row.type == 'directory'){
						_.each(return_data.data[0],function (value,key,list) {
							if(value.name == row.name){
								open(self, 'muk_dms.directory', value.odoo_id);
								console.log(open);
							}
                        })
					}
				},
                onEditableSave: function(field, row, oldValue, $el){
                    if("model" in row){
                        var id = row[[field, "id"].join("_")];
                        var val = {};
                        if(field.slice(-6) == "_input"){
                            val.input_value = row[field];
                            id = row[[field.slice(0, -6), "id"].join("_")];
                        }else{
                            val.value = row[field];
                        }
                        new Model('item.attributes', session.user_context).call('write', [[id], val]).then(function(result){
                                // console.log(result);
                            });
                    }else{
                        return (_t("Model don't have this attribute."));
                    }
                }
            });
            var i = opened_nodes.length;
            while(i--){
                //var open = opened_nodes[i]
                //if(open.children.length > 0){
                    LOADED_NODE.add(open.id);
                //}
            }
        });
    },
	adjust_splitter_height: function(self) {
	    var height_tree = self.$el.find('.oe_document_tree').height() + self.$el.find('.jinjiang_table_place_holder').height();
        // self.splitter.height(height_tree).resize();
        $(".vsplitter").css("height", height_tree);
    },
    show_preview: function(ev) {
		this.show_preview_active = true;
    	if(!this.$el.find('.show_preview').hasClass("active")) {
        	this.$el.find('.show_preview').addClass("active");
        	this.$el.find('.hide_preview').removeClass("active");
    		this.$el.find('.oe_document_col_preview').show();
        	this.splitter = this.$el.find('.oe_document_row').split({
        	    orientation: 'vertical',
        	    limit: 330,
        	    position: '20%'
        	});
    	}
    },
    hide_preview: function(ev) {
		this.show_preview_active = false;
    	if(!this.$el.find('.hide_preview').hasClass("active")) {
    		this.$el.find('.hide_preview').addClass("active");
    		this.$el.find('.show_preview').removeClass("active");
    		this.$el.find('.oe_document_col_preview').hide();
    		this.$el.find('.oe_document_col_tree').width('100%');
    		if(this.splitter) {
    			this.splitter.destroy();
    		}
    		this.splitter = false;
    	}
    },
    // load_directories: function(self) {
    // 	var directories_query = $.Deferred();
    // 	Directories.query(['name', 'parent_directory', 'perm_read', 'perm_create',
    // 					   'perm_write', 'perm_unlink']).all().then(function(directories) {
    // 		var data = [];
    // 		var directory_ids = _.map(directories, function(directory, index) {
    // 			return directory.id;
    // 		});
    // 		_.each(directories, function(value, key, list) {
    //     		data.push({
    //     			id: "directory_" + value.id,
    //     			parent: (value.parent_directory &&
    //     					$.inArray(value.parent_directory[0], directory_ids) !== -1 ?
    //     							"directory_" + value.parent_directory[0] : "#"),
    //     			text: value.name,
    //     			icon: "fa fa-folder-o",
    //     			type: "directory",
    //     			data: {
    //     				container: false,
    //     				odoo_id: value.id,
    //     				odoo_parent_directory: value.parent_directory[0],
    //     				odoo_model: "muk_dms.directory",
    //     				perm_read: value.perm_read,
    //     				perm_create: value.perm_create,
    //     				perm_write: value.perm_write,
    //     				perm_unlink: value.perm_unlink,
    //     			}
    //     		});
    //     	});
    // 		directories_query.resolve(data, directory_ids);
    // 	});
    // 	return directories_query;
    // },
    add_container_directory: function(self, directory_id, directory_name) {
    	return {
			id: "directory_" + directory_id,
			parent: "#",
			text: directory_name,
			icon: "fa fa-folder-o",
			type: "directory",
			data: {
				container: true,
				odoo_id: directory_id,
				odoo_parent_directory: false,
				odoo_model: "muk_dms.directory",
				perm_read: false,
				perm_create: false,
				perm_write: false,
				perm_unlink: false,
			}
    	};
    },
    // load_files: function(self, directory_ids) {
    // 	var files_query = $.Deferred();
    // 	Files.query(['name', 'mimetype', 'extension', 'directory',
    // 	             'size', 'perm_read','perm_create', 'perm_write',
    // 	             'perm_unlink']).all().then(function(files) {
    // 		var data = [];
    // 		_.each(files, function(value, key, list) {
    // 			if(!($.inArray(value.directory[0], directory_ids) !== -1)) {
    // 				directory_ids.push(value.directory[0]);
    // 				data.push(self.add_container_directory(self, value.directory[0], value.directory[1]));
    // 			}
    //     		data.push({
    //     			id: "file," + value.id,
    //     			parent: "directory_" + value.directory[0],
    //     			text: value.name,
    //     			icon: dms_utils.mimetype2fa(value.mimetype, {prefix: "fa fa-"}),
    //     			type: "file",
    //     			data: {
	 //        			odoo_id: value.id,
    //     				odoo_parent_directory: value.directory[0],
	 //        			odoo_model: "muk_dms.file",
    //     				filename: value.name,
    //     				file_size: value.file_size,
    //     				preview_link: value.link_preview,
    //     				download_link: value.link_download,
    //     				file_extension: value.file_extension,
    //     				mime_type: value.mime_type,
    //     				perm_read: value.perm_read,
    //     				perm_create: value.perm_create,
    //     				perm_write: value.perm_write,
    //     				perm_unlink: value.perm_unlink,
    //     			}
    //     		});
    //     	});
    // 		files_query.resolve(data);
    // 	});
    // 	return files_query;
    // },
    load_view: function() {
    	var self = this;
    	LOADED_NODE.clear();
    	//$.when(self.load_directories(self)).done(function (directories, directory_ids) {
    		//$.when(self.load_files(self, directory_ids)).done(function (files) {
        		//var data = directories.concat(files);
        		self.$el.find('.oe_document_tree').jstree({
        			'widget': self,
		        	'core': {
		        		'animation': 0,
		        		'multiple': false,
						'dblclick_toggle': false,
		        	    'check_callback': true,
		        	    'themes': {
		        			"stripes": true,
							"dots": true,
							"icons": true
						},
		        		'data': {
							'url' : function (node) {
								return node.id === '#' ?
									'/gesion_api/directory_tree_init_data' : '/gesion_api/directory_tree_data';
							},
							'data': function (node) {
								return {'node_id': node.id};
							}
						}
		        	},
		        	'plugins': [
		        	    "contextmenu", "search", "sort", "state", "wholerow", "types"
    	            ],
		        	'search': {
		        	    'case_insensitive': false,
		        	    'show_only_matches': true,
		        	    'search_callback': function (str, node) {
		        	    	try {
		        	    		return node.text.match(new RegExp(str)); 
		        	    	} catch(ex) {
		        	    		return false; 
		        	    	} 
		        	    }
		        	},
		        	'contextmenu': {
    	                items: context_menu_items
    	            },
	        	}).on('open_node.jstree', function (e, data) {
                    console.log(data.node.id.indexOf('repository'));
                    if(data.node.id.indexOf('repository')!=11){
						data.instance.set_icon(data.node, "fa fa-folder-open-o");
					}else{
                    	data.instance.set_icon(data.node, "fa fa-bookmark-o");
					}
	        	}).on('close_node.jstree', function (e, data) {
                    if(data.node.id.indexOf('repository')!=11) {
                        data.instance.set_icon(data.node, "fa fa-folder-o");
                    }else{
                    	data.instance.set_icon(data.node, "fa fa-bookmark-o");
					}
	        	}).bind('loaded.jstree', function(e, data) {
	        		self.show_preview();
	        	}).on('changed.jstree', function (e, data) {
	        		console.log(data);
	        		if(data.node) {
	        			if(data.node.hasOwnProperty('id')){
							self.show_table(data.node.id);
						}
	        			self.selected_node = data.node;
	        			self.$el.find('button.open').prop('disabled', !self.selected_node.data.perm_read);
	        			self.$el.find('button.edit').prop('disabled', !self.selected_node.data.perm_write);
	        			self.$el.find('button.create_file').prop('disabled',
	        					self.selected_node.data.odoo_model != "muk_dms.directory" || !self.selected_node.data.perm_create);
	        			self.$el.find('button.create_directory').prop('disabled',
							 !self.selected_node.data.perm_create);
	        			$("#menuContinenti").prop('disabled', function (_, val) { return ! val; });
	        			if(self.show_preview_active && data.node.data.odoo_model == "muk_dms.file") {
	        				PreviewHelper.createFilePreviewContent(data.node.data.odoo_id).then(function($content) {
	        					self.$el.find('.oe_document_preview').html($content);
	        				});       		
		        		}
	        		}
	        	}).on('ready.jstree', function(e, data){
					self.adjust_splitter_height(self);
					// self.show_table();
					$(this).on('after_open.jstree', function (e, data) {
						self.adjust_splitter_height(self);
						if(data.node.id.indexOf('dms.repository')!=7) {
							console.log(11111111);
                            data.instance.set_icon(data.node, "fa fa-folder-open-o");
                        }
					}).on('after_close.jstree', function (e, data) {
						if(data.node.id.indexOf('dms.repository')!=7) {
							console.log(11111111);
                            data.instance.set_icon(data.node, "fa fa-folder-o");
                        }
						self.adjust_splitter_height(self);
					});
				});
        		var timeout = false;
        		self.$el.find('#tree_search').keyup(function() {
	        	    if(timeout) {
	        	    	clearTimeout(timeout); 
	        	    }
	        	    timeout = setTimeout(function() {
	        	    	var v = self.$el.find('#tree_search').val();
	        	    	self.$('.oe_document_tree').jstree(true).search(v);
	        	    }, 250);
        	   });
    	//	});
    	//});
    },
    open: function() {
    	if(this.selected_node) {
    		open(this, this.selected_node.data.odoo_model, this.selected_node.data.odoo_id);
    		console.log(this);
    	}
    },
    edit: function() {
    	if(this.selected_node) {
    		edit(this, this.selected_node.data.odoo_model, this.selected_node.data.odoo_id);
    	}
    },
    create_file: function() {
    	if(this.selected_node) {
    		if(this.selected_node.data.odoo_model == "muk_dms.directory") {
        		create(this, "muk_dms.file", this.selected_node.data.odoo_id);
    		} else {
        		create(this, "muk_dms.file", this.selected_node.data.odoo_id);
    		}
    	}
    },
    create_directory: function() {
    	if(this.selected_node) {
    		//if(this.selected_node.data.odoo_model == "muk_dms.directory"||"gesion_dms.repository") {
			if(this.selected_node.data.odoo_model == "muk_dms.directory"){
				create(this, "muk_dms.directory", this.selected_node.data.odoo_id);
			}else{
				create(this, "muk_dms.directory", this.selected_node.data.odoo_id,true);
			}

    		// } else {
        		// create(this, "muk_dms.file", this.selected_node.data.odoo_id);
    		// }
    	}
    },
});

core.action_registry.add('gesion_dms_views.repository', RepositoryTreeView);

return RepositoryTreeView

});