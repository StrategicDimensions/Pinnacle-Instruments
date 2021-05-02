# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class OutstandingStatementWizard(models.TransientModel):
    """Outstanding Statement wizard."""

    _name = "outstanding.statement.wizard"
    _inherit = "statement.common.wizard"
    _description = "Outstanding Statement Wizard"

    def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        return self.env.ref(
            "partner_statement.action_print_outstanding_statement"
        ).report_action(self.ids, data=data)

    def open_activity_outgoing_statement_wizard(self):
        action = self.env["ir.actions.actions"]._for_xml_id("partner_statement.action_partner_outgoing_activity_statement")
        action['context'] = {
            'active_ids': [self._context.get('active_id')]
        }
        return action