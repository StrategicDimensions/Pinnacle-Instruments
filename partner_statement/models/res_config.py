from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class activity_statement_config_setting(models.TransientModel):
    _inherit = 'res.config.settings'

    automatic_statement = fields.Boolean(string="Turn On automatic statements")
    cron_next_call_date = fields.Integer(string="Cron Next Call Date")
    send_to_options = fields.Selection([
                                ('send_to_all','Send to All'),
                                ('outstanding_balance_only','Outstanding Balance Only')
                                ], string="Send Options")
    new_default_statement_period = fields.Selection([
                                                 ('current_fiscal_year', 'Current Fiscal Year'),
                                                 ('current_quarter', 'Current Quarter'),
                                                 ('current_month', 'Current Month'),
                                                 ('last_fiscal_year', 'Last Fiscal Year'),
                                                 ('last_quarter', 'Last Quarter'),
                                                 ('last_month', 'Last Month'),
                                                 ], string="Default Statement Period", default='current_month')

    mode = fields.Selection([
                            ('Production','Production'),
                            ('Test','Test')
                            ])
    test_email_address = fields.Char(string="Test Email Address")
    excl_fully_allocated_invoices = fields.Boolean(string="Exclude Fully Allocated Invoices")
    statement_period_setting = fields.Selection([
                            ('partner_setting', 'Partner Setting'),
                            ('global_setting', 'Global Setting')
                            ], string='Statement Period Setting')

    automatic_payment_reminder = fields.Boolean()
    payment_reminder_date = fields.Integer(string="Payment Reminder Date")
    payment_reminder_email_template_ids = fields.Many2one('mail.template',string='Payment Reminder Email Template',)

    def get_values(self):
        res = super(activity_statement_config_setting, self).get_values()
        res.update({'automatic_statement': self.env['ir.config_parameter'].sudo().get_param('partner_statement.automatic_statement'),
                    'send_to_options': self.env['ir.config_parameter'].sudo().get_param('partner_statement.send_to_options'),
                    'new_default_statement_period': self.env['ir.config_parameter'].sudo().get_param('partner_statement.new_default_statement_period'),
                    'statement_period_setting': self.env['ir.config_parameter'].sudo().get_param('partner_statement.statement_period_setting'),
                    'mode': self.env['ir.config_parameter'].sudo().get_param('partner_statement.mode'),
                    'test_email_address':self.env['ir.config_parameter'].sudo().get_param('partner_statement.test_email_address'),
                    'cron_next_call_date': int(self.env['ir.config_parameter'].sudo().get_param('partner_statement.cron_next_call_date')),
                    'excl_fully_allocated_invoices': self.env['ir.config_parameter'].sudo().get_param('partner_statement.excl_fully_allocated_invoices'),
                    'automatic_payment_reminder': self.env['ir.config_parameter'].sudo().get_param('partner_statement.automatic_payment_reminder'),
                    'payment_reminder_date': int(self.env['ir.config_parameter'].sudo().get_param('partner_statement.payment_reminder_date')),
                    'payment_reminder_email_template_ids': int(self.env['ir.config_parameter'].sudo().get_param('partner_statement.payment_reminder_email_template_ids1'))})
        return res

    def set_values(self):
        res = super(activity_statement_config_setting, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.automatic_statement',self.automatic_statement)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.cron_next_call_date',self.cron_next_call_date)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.send_to_options',self.send_to_options)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.mode',self.mode)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.test_email_address', self.test_email_address)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.new_default_statement_period',self.new_default_statement_period)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.automatic_payment_reminder',self.automatic_payment_reminder)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.payment_reminder_date',self.payment_reminder_date)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.payment_reminder_email_template_ids1',self.payment_reminder_email_template_ids.id)
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.statement_period_setting',
                                                         self.statement_period_setting)
        # if self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.automatic_statement',self.automatic_statement):
        #     cron_id = self.env.ref('customer_activity_statement.partner_activity_statement_cron')
        #     cron_id.update({
        #                     'nextcall': fields.Date.from_string(cron_id.nextcall).replace(
        #                                 day=int(self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.cron_next_call_date',self.cron_next_call_date)))
        #                     })
        # if self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.automatic_payment_reminder',self.automatic_payment_reminder):
        #     cron_id = self.env.ref('customer_activity_statement.update_payment_reminder_sent')
        #     cron_id.update({
        #                     'nextcall': fields.Date.from_string(cron_id.nextcall).replace(
        #                                 day=int(self.env['ir.config_parameter'].sudo().set_param('customer_activity_statement.payment_reminder_date',self.payment_reminder_date)))
        #                     })
        self.env['ir.config_parameter'].sudo().set_param('partner_statement.excl_fully_allocated_invoices',self.excl_fully_allocated_invoices)
        return res
