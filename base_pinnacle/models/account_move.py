# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import base64
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def send_batch_invoices(self):
        records_ids = self._context.get('active_ids')
        new_records = self.browse(records_ids)
        partner_list = []
        email_subject = 'Invoices'
        invoice_html = ''
        for each in new_records:
            partner_list.append(each.partner_id.id)
            email_subject += '_(' + str(each.name) + ')'
            invoice_html += '<li><b>' + str(each.name) + ' with amounting ' + str(each.amount_total_signed) + '</b></li>'
        partner = len(set(partner_list)) == 1
        email_body = """
                       <div class='o_thread_message_content'>
                               <p>Dear """ + str(new_records[0].partner_id.name) + """</p>
                               <p>Hear is your invoices :</p>
                               <ul>
                                    """ + str(invoice_html) + """
                               </ul>
                               <p> from """ + str(new_records[0].company_id.name) + """ Please remit payment at your earliest convenience. </p>
                               <p>Do not hesitate to contact us if you have any questions.</p>
                       </div>
                                       """
        if partner:
            email_template = self.env.ref('base_pinnacle.batch_invoice_email_new')
            email_template.subject = email_subject
            email_template.body_html = email_body
            template_id = self.env.ref('account.account_invoices_without_payment')
            pdf = template_id._render_qweb_pdf(new_records.ids)
            values = base64.b64encode(pdf[0])
            attachment_id = self.env['ir.attachment'].sudo().create(
                {'datas': values, 'name': 'Invoices.pdf'})
            email_template.attachment_ids = attachment_id
            email_template.send_mail(new_records[0].id, raise_exception=False, force_send=True)
        else:
            raise UserError(_('Please Select Same Partner'))

