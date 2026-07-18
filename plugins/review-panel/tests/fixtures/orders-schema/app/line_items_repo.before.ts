// Fixture: orders-schema line-items repository, BEFORE state (scc-bqp AC2 — Agent boundary
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
