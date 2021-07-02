# Copyright 2018 ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import logging

from odoo import api, fields, models, _
from datetime import datetime
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    account_internal_type = fields.Selection(related='account_id.user_type_id.type', string="Internal Type",
                                             readonly=True, store=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    customer = fields.Boolean(string='Is Customer', default=True)
    is_vendor = fields.Boolean(string='Is Vendor', default=True)
    statement_sent = fields.Boolean('Statement Sent', default=False)
    excl_fully_allocated_invoices = fields.Boolean(string="Exclude Fully Allocated Invoices")
    statement_email = fields.Char('Statement Email')
    statement_period = fields.Selection([('current_month', 'Current Month'),
                                         ('current_quarter', 'Current Quarter'),
                                         ('current_fiscal_year', 'Current Fiscal Year'),
                                         ('last_fiscal_year', 'Last Fiscal Year'),
                                         ('last_quarter', 'Last Quarter'),
                                         ('last_month', 'Last Month'), ], default="current_month",
                                        string="Statement Period")

    def update_statement_sent(self):
        config_id = self.env['ir.config_parameter'].sudo().get_param('partner_statement.cron_next_call_date')
        if int(config_id) - 1 == datetime.now().day:
            self.search([('statement_sent', '=', True)]).update({'statement_sent': False})
