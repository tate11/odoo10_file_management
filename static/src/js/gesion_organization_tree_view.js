odoo.define('gesion_dms_views.organization_tree_view', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var framework = require('web.framework');
var form_common = require('web.form_common');
var FormView = require('web.FormView');

var Widget = require('web.Widget');
var Dialog = require('web.Dialog');
var Model = require("web.Model");

//var PreviewHelper = require('muk_dms_preview_file.PreviewHelper');

var _t = core._t;
var QWeb = core.qweb;

var LOADED_NODE = new Set();

var open = function(self, model, id) {
	self.do_action({
        type: 'ir.actions.act_window',
        res_model: model,
        res_id: id,
        views: [[false, 'form']],
        target: 'current',
        flags: {'initial_mode': 'view'},
        context: session.user_context,
    });
}

var edit = function(self, model, id) {
    var context = {};
	if(model == "resource") {
		context = $.extend(session.user_context, {
			default_resource_id: id
        });
	} else if(model == "structure") {
		context = $.extend(session.user_context, {
			default_parent_id: id
        });
	}
	self.do_action({
		type: 'ir.actions.act_window',
        res_model: model,
        res_id: id,
        views: [[false, 'form']],
        target: 'current',
        flags: {'initial_mode': 'edit'},
        context: context,
    });
}

var create = function(self, model, parent) {
	var context = {};
	if(model == "gesion.organization") {
		context = $.extend(session.user_context, {
			default_parent_id: parent
        });
	} else if(model == "structure") {
		context = $.extend(session.user_context, {
			default_parent_id: parent
        });
	}
	self.do_action({
		type: 'ir.actions.act_window',
        res_model: model,
        views: [[false, 'form']],
        target: 'new',
        context: context,
    });
}

var unlink = function(self, model, id) {
    new Model(model, session.user_context).call('unlink',[id]).then(function(){
    });
}

var custom_import = function(self) {
    self.do_action({
        type: 'ir.actions.act_window',
        res_model: 'jinjiang.budgets.import',
        view_mode: 'form',
        view_type: 'form',
        views: [[false, 'form']],
        target: 'new',
        context: session.user_context,
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
	if(node.data.perm_unlink) {
		items.unlink = {
			separator_before: false,
			separator_after: false,
			_disabled: false,
			icon: "fa fa-unlink",
			label: _t("Delete"),
			action: function(data) {
				var inst = $.jstree.reference(data.reference);
				var	obj = inst.get_node(data.reference);
				unlink(inst.settings.widget, obj.data.odoo_model, obj.data.odoo_id);
			}
		};
	}
	if(node.data.odoo_model == "gesion.organization" && node.data.perm_create) {
		items.create = {
			separator_before: false,
			icon: "*-plus-circle",
			separator_after: false,
			label: _t("Create"),
			action: false,
			submenu: {
				organization: {
					separator_before: false,
					separator_after: false,
					label: _t("Organization"),
					icon: "fa fa-folder",
					action: function(data) {
						var inst = $.jstree.reference(data.reference);
						var	obj = inst.get_node(data.reference);
						create(inst.settings.widget, "gesion.organization", obj.data.odoo_id);
					}
				},
			}
		};
	}
	return items;
}

var get_showed_nodes = function(node, parent_opened, showed_nodes){
    if (!node.children){
        if(parent_opened) {
            showed_nodes.push(node);
        }
    }else if(!node.state.opened){
        showed_nodes.push(node);
    }else{
        showed_nodes.push(node);
        node.children.forEach(function(i){
            get_showed_nodes(i, node.state.opened, showed_nodes);
        });
    }
    return showed_nodes;
}

var flatten = function (arr) { arr = Array.prototype.concat.apply([], arr); return arr.some(Array.isArray) ? flatten(arr) : arr; }

var OrganizationTreeView = Widget.extend({
	template: 'GesionOrganizationTreeView',
	events: {
        "click button.refresh": "refresh",
        "click button.show_preview": "show_preview",
        "click button.hide_preview": "hide_preview",
        "click button.open": "open",
        "click button.edit": "edit",
        "click button.unlink": "unlink",
        "click button.create_organization": "create_organization",
        "click button.custom_import": "custom_import",
    },
	init: function(parent) {
        this._super(parent);
        this.name = _t('OrganizationTreeView');
		this.splitter = false;
    },
    start: function () {
    	this.$('[data-toggle="tooltip"]').tooltip();
        this.load_view();
    },
    refresh: function() {
    	var self = this;
        // trick
    	self.$el.find('.oe_document_preview').bootstrapTable('destroy');
        // self.$el.find('.oe_document_tree').jstree(true).settings.core.data = data;
        self.$el.find('.oe_document_tree').jstree(true).refresh();
    },
    show_table_none: function(){
	},
    show_table: function(nodes){
        var self = this;
        // var all_nodes = self.$el.find('.oe_document_tree').jstree(true).get_json('#', {});
        // var opened_nodes = flatten(all_nodes.map(function(n){
        //     return get_showed_nodes(n, true, []);
        // }));
		var opened_nodes = [];
		opened_nodes.push(nodes);
        session.rpc('/gesion_api/dms/table_data', {nodes: opened_nodes}).then(function(return_data){
        	//console.log(return_data.data[0]);
            var all_attributes = return_data.data[0];

            var columns = [];
                       // _.each(all_attributes, function(value, key, list){
            	// _.each(value, function(v, k, l){
			// 		columns.push({
			// 			field: k,
			// 			title: k,
			// 			align: "center",
			// 			valign: "middle",
			// 			halign: "center",
			// 			falign: "center",
             //    	});
			// 	})
			// })
			for(var col_key in all_attributes[0]){
				if(col_key !=='model'){
					if(col_key=='type'){
						columns.push({
							field: col_key,
							title: '类型',
							align: "center",
							valign: "middle",
							halign: "center",
							falign: "center",
                		});
					}else if(col_key=='name'){
						columns.push({
							field: col_key,
							title: '名称',
							align: "center",
							valign: "middle",
							halign: "center",
							falign: "center",
                		});
					}else if(col_key=='desc'){
						columns.push({
							field: col_key,
							title: '描述',
							align: "center",
							valign: "middle",
							halign: "center",
							falign: "center",
                		});
					}

				}

			}
             // _.each(all_attributes, function(value, key, list) {
            	// console.log(value,key,list);
             //    columns.push({
             //        field: value,
             //        title: 'model',
             //        align: "center",
             //        valign: "middle",
             //        halign: "center",
             //        falign: "center",
             //    });
//                 columns.push({
//                     field: value.display_name + "_input",
//                     title: "输入值",
//                     align: "center",
//                     valign: "middle",
//                     halign: "center",
//                     falign: "center",
//                     editable: {
//                         type: 'text',
//                         defaultValue: "-",
// //                        emptytext: 'Please Input',
//                         mode: "popup",
//                         validate:function(value){ //字段验证
//                             if (isNaN(value)){
//                                 return _t('Value must be numbers');
//                             }
//                             if(! $.trim(value)){
//                                 return _t('Value can not be empty');
//                             }
//                         },
//                         noeditFormatter: function(value, row, index){
//                             if(value === undefined){
//
//                             }else{
//                                 return false;
//                             }
//                         },
//                         pk: function(){
//                             return value.id;
//                         },
//                         params: function(params){
//                             console.log(params);
//                         },
//                     },
//                 });
//            });

            // devecho_odoo_theme_v10 nav class: o_main_navbar
            // var navbar_height_str = $('.navbar').outerHeight().toString();
            // backend_theme_v10 nav class:   navbar navbar-default main-nav
			var navbar_height_str = "46";
            var boots_table = self.$el.find('.oe_document_preview').bootstrapTable('destroy').bootstrapTable({
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
                var open = opened_nodes[i]
                //if(open.children.length > 0){
                    LOADED_NODE.add(open.id);
                //}
            }
        });
    },
	// table_insert_row: function(self, nodes, parent_row_index){
	// 	session.rpc('/gesion_api/table_data_row', {nodes: nodes}).then(function(return_data){
	// 	    var oe_preview = self.$el.find('.oe_document_preview');
	// 	    return_data.data.forEach(function(r) {
	// 	        parent_row_index += 1;
     //            oe_preview.bootstrapTable('insertRow', {
     //                index: parent_row_index,
     //                row: r
     //            });
     //        });
     //    });
	// },
    // table_show_row: function(self, nodes){
	//     var dtd = $.Deferred();
	//     // var rowss = self.$el.find('.oe_document_preview').bootstrapTable('getHiddenRows', {show: false});
	//     // console.log(rowss);
     //    var oe_preview = self.$el.find('.oe_document_preview');
     //    var i = nodes.length;
     //    while(i--){
     //        oe_preview.bootstrapTable('showRow', {uniqueId: nodes[i], isIdField:true});
     //    }
     //    dtd.resolve();
     //    return dtd.promise();
     //    // nodes.forEach(function (node) {
     //    //     oe_preview.bootstrapTable('showRow', {uniqueId: node, isIdField:true});
     //    // });
	// },
	// table_hide_row: function(self, nodes){
	//     var oe_preview = self.$el.find('.oe_document_preview');
	//     var i = nodes.length;
     //    while(i--){
     //        oe_preview.bootstrapTable('hideRow', {uniqueId: nodes[i]});
     //    }
     //    // nodes.forEach(function (node) {
     //    //     // self.$el.find('.oe_document_preview').bootstrapTable('removeByUniqueId', node);
     //    //     oe_preview.bootstrapTable('hideRow', {uniqueId:node});
     //    // });
     //    // var rowss2 = self.$el.find('.oe_document_preview').bootstrapTable('getHiddenRows', {show: false});
     //    // console.log(rowss2);
	// },
    adjust_splitter_height: function(self) {
	    var height_tree = self.$el.find('.oe_document_tree').height() + self.$el.find('.jinjiang_table_place_holder').height();
        // self.splitter.height(height_tree).resize();
        $(".vsplitter").css("height", height_tree);
    },
    get_node_state(self, node) {
	    var flat_nodes = self.$el.find('.oe_document_tree').jstree(true).get_json(node, {flat: true});
	    // console.log(flat_nodes);
    },
    show_preview: function(ev) {
		this.show_preview_active = true;
    	if(!this.$el.find('.show_preview').hasClass("active")) {
        	this.$el.find('.show_preview').addClass("active");
        	this.$el.find('.hide_preview').removeClass("active");
    		this.$el.find('.oe_document_col_preview').show();
            this.splitter = $('#jinjiang_document_row').height(10).split({
                orientation: 'vertical',
                limit: 220,
                position: '30%', // if there is no percentage it interpret it as pixels
                onDrag: function(event) {
                    $('.right_panel').triggerHandler('splitter_drag');
                }
            });
            // this.splitter = splitter;
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
    load_view: function() {
    	var self = this;
    	LOADED_NODE.clear();
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
							'/gesion_api/organization_tree_init_data' : '/gesion_api/organization_tree_data';
					},
					'data': function (node) {
						return {'node_id': node.id};
					}
				}
			},
			'plugins': [
				// "contextmenu", "search", "sort", "state", "wholerow", "types"
                "contextmenu", "search", "sort", "wholerow", "types"
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
			'sort' : function(a, b) {
					var a1 = this.get_node(a);
					var b1 = this.get_node(b);
					if (a1.seq > b1.seq){
						return (a1.seq > b1.seq) ? 1 : -1;
					}
//                            else if (a1.text > b1.text){
//                                return (a1.text > b1.text) ? 1 : -1;
//                            } else {
//                                return (a1.icon < b1.icon) ? -1 : 1;
//                            }
			},
		}).bind('loaded.jstree', function(e, data) {
			self.show_preview();
		}).on('changed.jstree', function (e, data) {
			if(data.node) {
				if(data.node.hasOwnProperty('id')){
					self.show_table(data.node.id);
				}

				self.selected_node = data.node;
				self.$el.find('button.open').prop('disabled', !self.selected_node.data.perm_read);
				self.$el.find('button.edit').prop('disabled', !self.selected_node.data.perm_write);
				self.$el.find('button.create_resource').prop('disabled',
						self.selected_node.data.odoo_model != "structure" || !self.selected_node.data.perm_create);
				self.$el.find('button.create_organization').prop('disabled',
						self.selected_node.data.odoo_model != "gesion.organization" || !self.selected_node.data.perm_create);
				//change single quotation mark to double quotation mark
				$("#menuContinenti").prop("disabled", function (_, val) { return ! val; });
			}
		}).on('ready.jstree', function(e, data){
		    self.adjust_splitter_height(self);
			// self.show_table();
            $(this).on('after_open.jstree', function (e, data) {
                self.adjust_splitter_height(self);
                data.instance.set_icon(data.node, "fa fa-folder-open-o");
            }).on('after_close.jstree', function (e, data) {
                data.instance.set_icon(data.node, "fa fa-folder-o");
                self.adjust_splitter_height(self);
            });
		}).on('dblclick', function(e, data){
			self.open();
//	        	}).on('search.jstree', function(e, data){
//	        	    self.show_table();
//	        	}).on('clear_search.jstree', function(e, data){
//	        	    self.show_table();
		}).on('refresh.jstree', function (e, data) {
            // self.show_table();
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
    },
    open: function() {
    	if(this.selected_node) {
    		open(this, this.selected_node.data.odoo_model, this.selected_node.data.odoo_id);
    	}
    },
    edit: function() {
    	if(this.selected_node) {
    		edit(this, this.selected_node.data.odoo_model, this.selected_node.data.odoo_id);
    	}
    },
    unlink: function() {
    	if(this.selected_node) {
    		unlink(this, this.selected_node.data.odoo_model, this.selected_node.data.odoo_id);
    	}
    },
    create_organization: function() {
    	if(this.selected_node) {
    		if(this.selected_node.data.odoo_model == "gesion.organization") {
        		create(this, "gesion.organization", this.selected_node.data.odoo_parent_id);
    		} else {
        		console.log("create_organization wrong model:%s"%this.selected_node.data.odoo_model);
    		}
    	}
    },
});

core.action_registry.add('gesion_dms_views.organization_tree_view', OrganizationTreeView);

return OrganizationTreeView

});