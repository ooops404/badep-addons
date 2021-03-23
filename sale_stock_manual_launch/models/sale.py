from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    launch_state = fields.Selection([('normal', 'En cours'), ('blocked', 'Pas encore lancé'), ('done', 'Lancé complètement')], string='Avancement',
                                    compute='_get_to_launch')

    @api.depends('order_line.to_launch')
    def _get_to_launch(self):
        for rec in self:
            rec.launch_state = 'blocked' if all(line.to_launch for line in rec.order_line) else 'normal' if any(
                line.to_launch for line in rec.order_line) else 'done'


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    procurement_qty = fields.Float(string="Qté lancée", compute='_get_procurement_quantity', digits=dp.get_precision('Product Unit of Measure'))
    to_launch = fields.Boolean(string="To Launch Procurement", compute='_get_to_launch')

    @api.depends('product_uom_qty')
    def _get_procurement_quantity(self):
        for rec in self:
            rec.procurement_qty = super(SaleOrderLine, rec.with_context(previous_product_uom_qty={rec.id: 0}))._get_qty_procurement()

    @api.depends('procurement_qty', 'product_uom_qty')
    def _get_to_launch(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.order_id.state != 'sale' or float_compare(line.procurement_qty, line.product_uom_qty, precision_digits=precision) >= 0:
                line.to_launch = False
            else:
                line.to_launch = True

    def _get_qty_procurement(self):
        return self.product_uom_qty - self.env.context.get('qty_to_launch', 0)

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        return values
