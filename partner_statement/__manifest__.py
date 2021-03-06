# Copyright 2018 ForgeFlow, S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Partner Statement",
    "version": "14.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": "OCA Financial Reports",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-reporting",
    "license": "AGPL-3",
    "depends": ['base',"account", 'contacts', 'web'],
    "external_dependencies": {"python": ["dateutil"]},
    "data": [
        "security/statement_security.xml",
        "security/ir.model.access.csv",
        "views/activity_statement.xml",
        "views/res_partner_view.xml",
        # "views/report_templates.xml",
        "data/mail_template_data.xml",
        "data/ir_cron.xml",
        "views/outstanding_statement.xml",
        "views/assets.xml",
        "views/aging_buckets.xml",
        "views/res_config_settings.xml",
        "views/res_config_view.xml",
        "wizard/statement_wizard.xml",
    ],
    "installable": True,
    "application": False,
}

