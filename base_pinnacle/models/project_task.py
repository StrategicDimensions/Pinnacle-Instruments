# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.model
    def create(self, vals):
        res = super(ProjectTask, self).create(vals)
        sequence = self.env['ir.sequence'].next_by_code('project.task') or _('New')
        res['name'] = sequence + '/' + vals['name']
        return res
