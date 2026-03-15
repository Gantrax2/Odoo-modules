
odoo.define('abatar.tree_view_button', function (require){
    "use strict";

    var ajax = require('web.ajax');
    var ListController = require('web.ListController');
    //var Widget = require('web.Widget');
    ListController.include({
        renderButtons: function($node) {
            this._super.apply(this, arguments);
            var self = this;

            if (this.$buttons) {

                // Botón factura 1
                this.$buttons.find('.oe_new_custom_button_factura').on('click', function() {
                    var state = self.model.get(self.handle, {raw: true});
                    var context = state.getContext()
                    context['active_ids']=self.getSelectedIds()
                    context['active_model']=self.modelName

                    self.do_action({
                        type: "ir.actions.act_window",
                        name: "facturas_wizard",
                        res_model: "pago.facturas",
                        views: [[false,'form']],
                        target: 'new',
                        view_type : 'form',
                        view_mode : 'form',
                        context:  context,
                    });
                });

                // Botón factura 2
                this.$buttons.find('.oe_new_custom_button_factura_extra').on('click', function() {
                    var state = self.model.get(self.handle, {raw: true});
                    var context = state.getContext()
                    context['active_ids']=self.getSelectedIds()
                    context['active_model']=self.modelName

                    self.do_action({
                        type: "ir.actions.act_window",
                        name: "facturas_extra_wizard",
                        res_model: "detalle.facturas",
                        views: [[false,'form']],
                        target: 'new',
                        view_type : 'form',
                        view_mode : 'form',
                        context:  context,
                    });
                });
                if (this.$buttons.find('.oe_new_custom_button')){
                    this.$buttons.find('.oe_new_custom_button').on('click', function() {
                        //custom code
                        var state = self.model.get(self.handle, {raw: true});
                        var context = state.getContext()
                        context['active_ids']=self.getSelectedIds()
                        context['active_model']=self.modelName

                        if (self.modelName=='abatar.deudas'){
                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "deudas_wizard",
                                res_model: "pago.deudas",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context:  context,
                                });
                        //} else if (window.location.href.search('ordenes')>-1){
                        //} else if (this.dataset.model==='abatar.ordenes'){

                        //    self.do_action({
                        //       type: "ir.actions.act_window",
                        //        name: "ordenes_div_wizard",
                        //        res_model: "ordenes.div",
                        //        views: [[false,'form']],
                        //        target: 'new',
                        //        view_type : 'form',
                        //        view_mode : 'form',
                        //        context:  context,
                        //    });
                        } else if (self.modelName==='abatar.indicadores'){
                        //} else if (self.modelName==='abatar.crm'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "indicadores_wizard",
                                res_model: "refresh.indicadores",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context:  context,
                            });
                        } else if (self.modelName==='abatar.crm'){
                        //} else if (self.modelName==='abatar.crm'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "crm_tel_wizard",
                                res_model: "crm.tel",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context:  context,
                            });
                        } else if (self.modelName==='abatar.savevisor'){
                        //} else if (this.dataset.model==='abatar.proveedores'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "savevisor_wizard",
                                res_model: "carga.macro.visor",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context:  context,
                                });
                        } else if (self.modelName==='abatar.proveedoresvisor'){
                            //} else if (this.dataset.model==='abatar.proveedores'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "proveedoresvisor_wizard",
                                res_model: "confirm.proveedoresvisor",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                });
                        } else if (self.modelName==='abatar.proveedores'){
                        //} else if (this.dataset.model==='abatar.proveedores'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "proveedores_tel_wizard",
                                res_model: "proveedores.tel",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context:  context,
                            });
                        //} else if (self.modelName==='abatar.visor'){
                        //} else if (this.dataset.model==='abatar.proveedores'){

                        //    self.do_action({
                        //        type: "ir.actions.act_window",
                        //        name: "visor_wizard",
                        //        res_model: "carga.visor",
                        //        views: [[false,'form']],
                        //        target: 'new',
                        //        view_type : 'form',
                        //        view_mode : 'form',
                        //        });
                        } else if (self.modelName==='abatar.cotizaciones'){
                        //} else if (this.dataset.model==='abatar.proveedores'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "tarifa_cotiz_wizard",
                                res_model: "tarifa_cotiz.aumenta",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                });
                        } else if (self.modelName.startsWith('abatar.visor')){
                        //} else if (this.dataset.model==='abatar.proveedores'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "function_define_wizard",
                                res_model: "abatar.set_func",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                });
                        } else {
                        //} else if (this.dataset.model==='abatar.proveedores'){

                            self.do_action({
                                type: "ir.actions.act_window",
                                name: "exporta_datos_wizard",
                                res_model: "exporta.datos",
                                views: [[false,'form']],
                                target: 'new',
                                view_type : 'form',
                                view_mode : 'form',
                                context:  context,
                                });
                        }

                    });
                }
                //if (this.$buttons.find('.oe_new_custom_button2')){
                //
                //  if (window.location.href){
                //      if (window.location.href.search('ordenes')>-1){
                //          console.log('hi')
                //          //return this._model.call(
                //          //    'set_todos', [], {
                //          //        context: this._model.context(this._context)
                //          //        });
                //      }
                //  }
                //}


            }
        },
    });
});

