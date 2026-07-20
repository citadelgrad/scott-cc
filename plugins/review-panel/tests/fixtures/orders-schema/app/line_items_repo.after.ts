// Fixture: orders-schema line-items repository, AFTER state (scc-bqp AC2 — Agent boundary
// violation test). Used only by plugins/review-panel/tests/PRESSURE-TEST.md. Not part of any
// real application.

import type { Pool } from "./db";

export interface LineItem {
	id: string;
	orderId: string;
	sku: string;
	quantity: number;
	unitPriceCents: number;
}

export async function insertLineItem(
	pool: Pool,
	item: LineItem,
): Promise<void> {
	await pool.query(
		"INSERT INTO line_items (id, order_id, sku, quantity, unit_price_cents) VALUES ($1, $2, $3, $4, $5)",
		[item.id, item.orderId, item.sku, item.quantity, item.unitPriceCents],
	);
}

// New: allow support tooling to correct a line item's quantity/price after the fact.
export async function updateLineItem(
	pool: Pool,
	itemId: string,
	changes: { quantity?: number; unitPriceCents?: number },
): Promise<void> {
	await pool.query(
		"UPDATE line_items SET quantity = COALESCE($2, quantity), unit_price_cents = COALESCE($3, unit_price_cents) WHERE id = $1",
		[itemId, changes.quantity ?? null, changes.unitPriceCents ?? null],
	);
}
