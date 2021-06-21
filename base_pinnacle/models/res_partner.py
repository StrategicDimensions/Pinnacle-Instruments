# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
