# -*- coding: utf-8 -*-
from odoo import models, fields, _


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def create(self, vals):
        if vals['res_model'] == 'crm.lead':
            crm_id = self.env['crm.lead'].browse(vals['res_id'])
            if crm_id:
                self.create({
                    'res_model': 'project.project',
                    'res_id': crm_id.project_id.id,
                    'datas': vals['datas'],
                    'name': vals['name'],
                })
        elif vals['res_model'] == 'purchase.order':
            purchase_order_id = self.env['purchase.order'].browse(vals['res_id'])
            if purchase_order_id:
                for each in purchase_order_id.order_line:
                    self.create({
                        'res_model': 'product.product',
                        'res_id': each.product_id.id,
                        'datas': vals['datas'],
                        'name': vals['name'],
                    })
        return super(IrAttachment, self).create(vals)

