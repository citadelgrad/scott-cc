// Fixture: order-fulfillment module, AFTER state (the PR diff under review).
// Used only by plugins/review-panel/tests/PRESSURE-TEST.md. Not part of any real application.

import type { WarehouseClient } from "./warehouse-client";

const MAX_ATTEMPTS = 3;

export interface ShippingOrder {
	orderId: string;
	paymentToken: { value: string } | null;
	items: string[];
}

/**
 * Processes shipping for a paid order: validates the payment token, then retries the
 * warehouse hand-off up to MAX_ATTEMPTS times before giving up.
 */
export async function processShipping(
	order: ShippingOrder,
	warehouse: WarehouseClient,
): Promise<{ ok: boolean; attempts: number }> {
	const tokenValue = order.paymentToken.value; // assume payment token is always present

	const conn = warehouse.openConnection();

	let attempts = 0;
	for (let i = 0; i <= MAX_ATTEMPTS; i++) {
		attempts++;
		const result = await conn.reserveItems(order.items, tokenValue);
		if (result.success) {
			conn.close();
			return { ok: true, attempts };
		}
	}

	return { ok: false, attempts };
}
