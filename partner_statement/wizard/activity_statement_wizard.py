# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, fields, models, _
import base64
from dateutil.relativedelta import relativedelta
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
import logging
_logger = logging.getLogger(__name__)


class ActivityStatementWizard(models.TransientModel):
    """Activity Statement wizard."""

    _inherit = "statement.common.wizard"
    _name = "activity.statement.wizard"
    _description = "Activity Statement Wizard"

    @api.model
    def _get_date_start(self):
        return (
            fields.Date.context_today(self).replace(day=1) - relativedelta(days=1)
        ).replace(day=1)

    date_start = fields.Date(required=True, default=_get_date_start)
    excl_fully_allocated_invoices = fields.Boolean(string="Exclude Fully Allocated Invoices")

    @api.onchange("aging_type")
    def onchange_aging_type(self):
        super().onchange_aging_type()
        if self.aging_type == "months":
            self.date_start = self.date_end.replace(day=1)
        else:
            self.date_start = self.date_end - relativedelta(days=30)

    def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        return self.env.ref(
            "partner_statement.action_print_activity_statement"
        ).report_action(self.ids, data=data)

    def _prepare_statement(self):
        res = super()._prepare_statement()
        res.update({"date_start": self.date_start})
        return res

    def open_activity_statement_wizard(self):
        action = self.env["ir.actions.actions"]._for_xml_id("partner_statement.action_partner_activity_statement")
        action['context'] = {
            'active_ids': (self._context.get('active_ids'))
        }
        return action

    def sent_activity_statement_by_email(self):
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('partner_statement', 'email_template_partner_statement')[1]
        except ValueError:
            template_id = False
        if template_id:
            try:
                template_obj = self.env['mail.template'].browse(template_id)
                for each in self._context.get('active_ids'):
                    partner_id = self.env['res.partner'].browse(each)
                    child_id = partner_id.child_ids.filtered(lambda x: x.type == 'invoice' and x.email)
                    send_email_to = child_id[0].email if child_id else partner_id.statement_email
                    template_obj.email_to = send_email_to
                    template_obj.subject = (partner_id.company_id.name if partner_id.company_id else self.env.company.name) + ' Customer Statement' + ' (' + (partner_id.ref if partner_id.ref else '') + ')'
                    report_template_id = self.env.ref('partner_statement.action_print_activity_statement')
                    pdf = report_template_id._render_qweb_pdf(each)
                    values = base64.b64encode(pdf[0])
                    attachment_id = self.env['ir.attachment'].sudo().create(
                        {'datas': values, 'name': "Statement_%s.pdf" % str(date.today())})
                    template_obj.attachment_ids = attachment_id
                    partner_id.message_post(body=_('Statement %s' % str(date.today())),
                                            attachment_ids=[attachment_id.id])
                    record_id = template_obj.with_context(partner_ids=[each]).send_mail(self.id, force_send=True, raise_exception=True)
                    mail_id = self.env['mail.mail'].browse(record_id)
                    mail_id.write({
                        'res_id':partner_id.id,
                        'model':'res.partner'
                    })
            except Exception as e:
                _logger.error('Unable to send email for order %s',e)

    def sent_activity_statement_by_email_cron(self):
        config_id = self.env['ir.config_parameter'].sudo().get_param('partner_statement.cron_next_call_date')
        config_statement_setting = self.env['ir.config_parameter'].sudo().get_param('partner_statement.statement_period_setting')
        if int(config_id) == datetime.now().day:
            automatic_statement = self.env['ir.config_parameter'].sudo().get_param('partner_statement.automatic_statement')
            if config_id and automatic_statement:
                # cron_next_call_date = int(self.env['ir.config_parameter'].sudo().get_param('customer_activity_statement.cron_next_call_date'))
                ir_model_data = self.env['ir.model.data']
                try:
                    template_id = ir_model_data.get_object_reference('partner_statement', 'email_template_partner_statement')[1]
                except ValueError:
                    template_id = False
                if template_id:
                    try:
                        template_obj = self.env['mail.template'].browse(template_id)
                        partner_list = []
                        if self.env['ir.config_parameter'].sudo().get_param('partner_statement.send_to_options') == 'outstanding_balance_only':
                            partner_list.append([x.id for x in self.env['res.partner'].search([('statement_sent', '=', False), ('customer','=',True)]).
                                                filtered(lambda l:(l.credit - l.debit) != 0)])
                        else:
                            partner_list.append([x.id for x in self.env['res.partner'].search([('statement_sent', '=', False),('customer','=',True)])])

                        partner_list = [partner_list[0][:50]]
                        #
                        wiz_id = self.create({'number_partner_ids': len(partner_list)})
                        date = datetime.now()

                        statement_period = self.env['ir.config_parameter'].sudo().get_param('partner_statement.new_default_statement_period')
                        if config_statement_setting == 'global_setting':
                            wiz_id.write({'excl_fully_allocated_invoices': self.env['ir.config_parameter'].sudo().get_param('partner_statement.new_default_statement_period')})
                            if statement_period in ('current_month', 'last_month'):
                                wiz_date_start = date.replace(day=1) if statement_period == 'current_month' else date.replace(day=1) + relativedelta(months= -1)
                                wiz_id.write({
                                    'date_start': wiz_date_start,
                                })
                            if statement_period in ('current_quarter', 'last_quarter'):
                                start_date = datetime.strptime(wiz_id.date_start, DF)
                                end_date = datetime.strptime(wiz_id.date_start, DF).date() + relativedelta(months=3,days=-1)
                                count = 1
                                today_date = datetime.now().date()
                                start_date = datetime.strptime(wiz_id.date_start, DF).date()
                                end_date = datetime.strptime(wiz_id.date_start, DF).date() + relativedelta(months= 3*count,days=-1)
                                for each in range(1,5):
                                    if today_date > start_date and today_date < end_date:
                                        start_date = start_date if statement_period == 'current_quarter' else start_date + relativedelta(months=-3)
                                        wiz_id.write({
                                            'date_start' : start_date,
                                        })
                                    else:
                                        count = count + 1
                                        start_date = end_date + relativedelta(days=1)
                                        end_date = datetime.strptime(wiz_id.date_start, DF).date() + relativedelta(months= 3*count,days=-1)
                            if statement_period == 'last_fiscal_year':
                                start_date = datetime.strptime(wiz_id.date_start, DF).date() + relativedelta(years= -1)
                                wiz_id.write({
                                    'date_start' : start_date,
                                })

                            if partner_list:
                                for each in partner_list[0]:
                                    partner_id = self.env['res.partner'].browse(each)
                                    child_id = partner_id.child_ids.filtered(lambda x: x.type == 'invoice' and x.email)
                                    send_email_to = child_id[0].email if child_id else partner_id.statement_email
                                    wiz_id.account_type = 'payable' if (not partner_id.customer and partner_id.supplier) else 'receivable'
                                    template_obj.email_to = send_email_to
                                    company_name = partner_id.company_id.name if partner_id.company_id else self.env.company.name
                                    template_obj.subject = company_name + ' Customer Statement' + ' (' + (partner_id.ref if partner_id.ref else '') + ')'
                                    template_obj.report_name = "Statement " + str(date.today())
                                    if self.env['ir.config_parameter'].sudo().get_param('partner_statement.mode') == "Test":
                                        test_email_address = self.env['ir.config_parameter'].sudo().get_param('partner_statement.test_email_address')
                                        template_obj.email_to = test_email_address
                                        report_template_id = self.env.ref(
                                            'partner_statement.action_print_activity_statement')
                                        pdf = report_template_id._render_qweb_pdf(each)
                                        values = base64.b64encode(pdf[0])
                                        attachment_id = self.env['ir.attachment'].sudo().create(
                                            {'datas': values, 'name': 'Statement_%s.pdf' % str(date.today())})
                                        template_obj.attachment_ids = attachment_id
                                        record_id = template_obj.with_context(partner_ids=[each]).send_mail(wiz_id.id, force_send=True, raise_exception=True)
                                    if self.env['ir.config_parameter'].sudo().get_param('partner_statement.mode') == "Production":
                                        report_template_id = self.env.ref(
                                            'partner_statement.action_print_activity_statement')
                                        pdf = report_template_id._render_qweb_pdf(each)
                                        values = base64.b64encode(pdf[0])
                                        attachment_id = self.env['ir.attachment'].sudo().create(
                                            {'datas': values, 'name': 'Statement_%s.pdf' % str(date.today())})
                                        template_obj.attachment_ids = attachment_id
                                        record_id = template_obj.with_context(partner_ids=[each]).send_mail(wiz_id.id,force_send=True, raise_exception=True)
                                    mail_id = self.env['mail.mail'].browse(record_id)
                                    mail_id.write({
                                        'model':'res.partner',
                                        'res_id':partner_id.id
                                    })
                                    partner_id.statement_sent = True

                        if config_statement_setting == 'partner_setting':
                            if partner_list:
                                for each in partner_list[0]:
                                    partner_id = self.env['res.partner'].browse(each)
                                    child_id = partner_id.child_ids.filtered(lambda x: x.type == 'invoice' and x.email)
                                    send_email_to = child_id[0].email if child_id else partner_id.statement_email
                                    wiz_id.write({'excl_fully_allocated_invoices': partner_id.excl_fully_allocated_invoices})
                                    if partner_id.statement_period and partner_id.statement_period in ('current_month', 'last_month'):
                                        wiz_date_start = date.replace(day=1) if statement_period == 'current_month' else date.replace(day=1) + relativedelta(months= -1)
                                        wiz_id.write({
                                            'date_start': wiz_date_start,
                                            'date_end': date.today(),
                                        })
                                    if partner_id.statement_period and partner_id.statement_period in ('current_quarter', 'last_quarter'):
                                        start_date = datetime.strptime(wiz_id.date_start, DF)
                                        end_date = datetime.strptime(wiz_id.date_start, DF).date() + relativedelta(
                                            months=3, days=-1)
                                        count = 1
                                        today_date = datetime.now().date()
                                        start_date = datetime.strptime(wiz_id.date_start, DF).date()
                                        end_date = datetime.strptime(wiz_id.date_start, DF).date() + relativedelta(
                                            months=3 * count, days=-1)
                                        for each in range(1, 5):
                                            if today_date > start_date and today_date < end_date:
                                                start_date = start_date if statement_period == 'current_quarter' else start_date + relativedelta(months=-3)
                                                wiz_id.write({
                                                    'date_start': start_date,
                                                    'date_end': date.today()
                                                })
                                            else:
                                                count = count + 1
                                                start_date = end_date + relativedelta(days=1)
                                                end_date = datetime.strptime(wiz_id.date_start,
                                                                             DF).date() + relativedelta(
                                                    months=3 * count, days=-1)
                                    if partner_id.statement_period and partner_id.statement_period == 'last_fiscal_year':
                                        start_date = datetime.strptime(wiz_id.date_start, DF).date() + relativedelta(years= -1)
                                        wiz_id.write({
                                            'date_start' : start_date,
                                        })

                                    wiz_id.account_type = 'payable' if (not partner_id.customer and partner_id.supplier) else 'receivable'
                                    template_obj.email_to = send_email_to
                                    template_obj.subject = (partner_id.company_id.name if partner_id.company_id else self.env.company.name) \
                                                           + ' Customer Statement' + ' (' + (partner_id.ref if partner_id.ref else '') + ')'
                                    template_obj.report_name = "Statement " + str(date.today())
                                    if self.env['ir.config_parameter'].sudo().get_param('partner_statement.mode') == "Test":
                                        test_email_address = self.env['ir.config_parameter'].sudo().get_param('partner_statement.test_email_address')
                                        template_obj.email_to = test_email_address
                                        report_template_id = self.env.ref(
                                            'partner_statement.action_print_activity_statement')
                                        pdf = report_template_id._render_qweb_pdf(each)
                                        values = base64.b64encode(pdf[0])
                                        attachment_id = self.env['ir.attachment'].sudo().create(
                                            {'datas': values, 'name': 'Statement_%s.pdf' % str(date.today())})
                                        template_obj.attachment_ids = attachment_id
                                        record_id = template_obj.with_context(partner_ids=[each]).send_mail(wiz_id.id, force_send=True, raise_exception=True)
                                    if self.env['ir.config_parameter'].sudo().get_param('partner_statement.mode') == "Production":
                                        report_template_id = self.env.ref(
                                            'partner_statement.action_print_activity_statement')
                                        pdf = report_template_id._render_qweb_pdf(each)
                                        values = base64.b64encode(pdf[0])
                                        attachment_id = self.env['ir.attachment'].sudo().create(
                                            {'datas': values, 'name': 'Statement_%s.pdf' % str(date.today())})
                                        template_obj.attachment_ids = attachment_id
                                        record_id = template_obj.with_context(partner_ids=[each]).send_mail(wiz_id.id,force_send=True, raise_exception=True)
                                    mail_id = self.env['mail.mail'].browse(record_id)
                                    mail_id.write({
                                        'model': 'res.partner',
                                        'res_id': partner_id.id
                                    })
                                    partner_id.statement_sent = True
                    except Exception as e:
                        _logger.error('Unable to send email for order %s', e)
