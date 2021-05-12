# -*- coding: utf-8 -*-
import datetime
import re
from odoo import api, models, fields, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        res = super(SaleOrder, self)._prepare_invoice()
        partner_id = self.env['res.partner'].search([('id', '=', res['partner_id'])])
        if partner_id.parent_id:
            res['partner_id'] = partner_id.parent_id.id
        return res


class SequenceMixin(models.AbstractModel):
    _inherit = 'sequence.mixin'

    @api.depends(lambda self: [self._sequence_field])
    def _compute_split_sequence(self):
        for record in self:
            sequence = record[record._sequence_field] or ''
            regex = re.sub(r"\?P<\w+>", "?:",
                           record._sequence_fixed_regex.replace(r"?P<seq>", ""))  # make the seq the only matching group
            matching = re.match(regex, sequence)
            if record.move_type == 'in_invoice':
                record.sequence_prefix = 'BILL' + str(datetime.datetime.today().year) + '/'
            elif record.move_type == 'out_invoice':
                record.sequence_prefix = 'INV' + str(datetime.datetime.today().year) + '/'
            else:
                record.sequence_prefix = sequence[:matching.start(1)]
            record.sequence_number = int(matching.group(1) or 0)

    def _set_next_sequence(self):
        """Set the next sequence.

        This method ensures that the field is set both in the ORM and in the database.
        This is necessary because we use a database query to get the previous sequence,
        and we need that query to always be executed on the latest data.

        :param field_name: the field that contains the sequence.
        """
        self.ensure_one()
        last_sequence = self._get_last_sequence()
        new = not last_sequence
        if new:
            last_sequence = self._get_last_sequence(relaxed=True) or self._get_starting_sequence()

        format, format_values = self._get_sequence_format_param(last_sequence)
        if new:
            format_values['seq'] = 0
            format_values['year'] = self[self._sequence_date_field].year % (10 ** format_values['year_length'])
            format_values['month'] = self[self._sequence_date_field].month
        format_values['seq'] = format_values['seq'] + 1
        print("\n\nformat.format(**format_values)", format.format(**format_values))
        if self.move_type == 'in_invoice':
            self[self._sequence_field] = 'BILL' + str(datetime.datetime.today().year) + '/' + str(format_values['seq']).zfill(4)
        elif self.move_type == 'out_invoice':
            self[self._sequence_field] = 'INV' + str(datetime.datetime.today().year) + '/' + str(format_values['seq']).zfill(4)
        else:
            self[self._sequence_field] = format.format(**format_values)
        self._compute_split_sequence()
