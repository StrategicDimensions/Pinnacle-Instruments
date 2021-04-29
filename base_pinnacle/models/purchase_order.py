# -*- coding: utf-8 -*-
from odoo import models, fields, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
