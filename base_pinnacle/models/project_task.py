# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.osv import expression

class ProjectTask(models.Model):
    _inherit = 'project.task'

    used_product_count = fields.Integer(compute="_compute_used_products")
    used_products_invoice_amount = fields.Monetary(compute="_compute_used_products_invoice_amount")

    def _compute_used_products_invoice_amount(self):
        sale_order_ids = self.env['sale.order'].search([('task_id', '=', self.id)])
        if sale_order_ids:
            print("\n\n======sale_order_ids.mapped('amount_total')", sale_order_ids.mapped('amount_total'))
            self.used_products_invoice_amount = sum(sale_order_ids.mapped('amount_total'))
        else:
            self.used_products_invoice_amount = 0.0

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        sequence = self.env['ir.sequence'].next_by_code('project.task') or _('New')
        res['name'] = sequence + '-' + vals['name']
        return res

    def _compute_used_products(self):
        sale_order_ids = self.env['sale.order'].search([('task_id', '=', self.id)])
        used_product_counts = 0
        for order in sale_order_ids:
            for each in order.order_line:
                used_product_counts = used_product_counts + int(each.product_uom_qty)
        self.used_product_count = used_product_counts

    def action_view_used_products(self):
        domain = [('sale_ok', '=', True), '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)]
        if self.project_id and self.project_id.timesheet_product_id:
            domain = expression.AND([domain, [('id', '!=', self.project_id.timesheet_product_id.id)]])
        deposit_product = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        if deposit_product:
            domain = expression.AND([domain, [('id', '!=', deposit_product)]])

        kanban_view = self.env.ref('industry_fsm_sale.view_product_product_kanban_material')
        return {
            'type': 'ir.actions.act_window',
            'name': _('Used Products'),
            'res_model': 'product.product',
            'views': [(kanban_view.id, 'kanban'), (False, 'form')],
            'domain': domain,
            'context': {
                'fsm_mode': True,
                'create': self.env['product.template'].check_access_rights('create', raise_exception=False),
                'used_fsm_task_id': self.id,  # avoid 'default_' context key as we are going to create SOL with this context
                'pricelist': self.partner_id.property_product_pricelist.id,
                'search_default_consumable': 1,
                'hide_qty_buttons': self.fsm_done or self.sale_order_id.state == 'done'
            },
            'help': _("""<p class="o_view_nocontent_smiling_face">
                                    Create a new product
                                </p><p>
                                    You must define a product for everything you sell or purchase,
                                    whether it's a storable product, a consumable or a service.
                                </p>""")
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.depends_context('used_fsm_task_id')
    def _compute_fsm_quantity(self):
        task = self._get_contextual_used_fsm_task()
        if task:
            sale_order_line_ids = []
            sale_order_ids = self.env['sale.order'].search([('task_id', '=', task.id)])
            for each in sale_order_ids:
                for rec in each.order_line:
                    sale_order_line_ids.append(rec.id)
            SaleOrderLine = self.env['sale.order.line']
            if self.user_has_groups('project.group_project_user'):
                SaleOrderLine = SaleOrderLine.sudo()
            products_qties = SaleOrderLine.read_group(
                [('id', 'in', sale_order_line_ids)],
                ['product_id', 'product_uom_qty'], ['product_id'])
            qty_dict = dict([(x['product_id'][0], x['product_uom_qty']) for x in products_qties])
            for product in self:
                product.fsm_quantity = qty_dict.get(product.id, 0)
        else:
            task = self._get_contextual_fsm_task()
            if task:
                SaleOrderLine = self.env['sale.order.line']
                if self.user_has_groups('project.group_project_user'):
                    task = task.sudo()
                    SaleOrderLine = SaleOrderLine.sudo()

                products_qties = SaleOrderLine.read_group(
                    [('id', 'in', task.sale_order_id.order_line.ids)],
                    ['product_id', 'product_uom_qty'], ['product_id'])
                qty_dict = dict([(x['product_id'][0], x['product_uom_qty']) for x in products_qties])
                for product in self:
                    product.fsm_quantity = qty_dict.get(product.id, 0)
            else:
                self.fsm_quantity = False


    @api.model
    def _get_contextual_used_fsm_task(self):
        task_id = self.env.context.get('used_fsm_task_id')
        if task_id:
            return self.env['project.task'].browse(task_id)
        return self.env['project.task']