// Fixture: order-fulfillment module, BEFORE state (clean baseline).
// Used only by plugins/review-panel/tests/PRESSURE-TEST.md. Not part of any real application.

import type { WarehouseClient } from "./warehouse-client";

const MAX_ATTEMPTS = 3;

export interface FulfillmentOrder {
	orderId: string;
	paymentToken: { value: string } | null;
	items: string[];
}

/**
 * Processes fulfillment for a paid order: validates the payment token, then retries the
 * warehouse hand-off up to MAX_ATTEMPTS times before giving up.
 */
export async function processFulfillment(
	order: FulfillmentOrder,
	warehouse: WarehouseClient,
): Promise<{ ok: boolean; attempts: number }> {
	if (!order.paymentToken) {
		throw new Error(
			`processFulfillment: order ${order.orderId} has no payment token`,
		);
	}
	const tokenValue = order.paymentToken.value;

	const conn = warehouse.openConnection();
	try {
		let attempts = 0;
		for (let i = 0; i < MAX_ATTEMPTS; i++) {
			attempts++;
			const result = await conn.reserveItems(order.items, tokenValue);
			if (result.success) {
				return { ok: true, attempts };
			}
		}
		return { ok: false, attempts };
	} finally {
		conn.close();
	}
}
