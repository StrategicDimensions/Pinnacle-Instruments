# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        if vals.get('res_model') == 'crm.lead':
            crm_id = self.env['crm.lead'].browse(vals.get('res_id'))
            if crm_id:
                self.create({
                    'res_model': 'project.project',
                    'res_id': crm_id.project_id.id,
                    'datas': vals.get('datas'),
                    'name': vals.get('name'),
                })
        elif vals.get('res_model') == 'purchase.order':
            purchase_order_id = self.env['purchase.order'].browse(vals.get('res_id'))
            if purchase_order_id:
                for each in purchase_order_id.order_line:
                    self.create({
                        'res_model': 'account.analytic.account',
                        'res_id': each.analytic_account_id.id,
                        'datas': vals.get('datas'),
                        'name': vals.get('name'),
                    })
        return super(IrAttachment, self).create(vals)

