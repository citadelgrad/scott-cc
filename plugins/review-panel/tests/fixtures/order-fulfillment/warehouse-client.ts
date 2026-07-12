// Fixture support file: minimal shape referenced by before.ts/after.ts's import.
// Used only by plugins/review-panel/tests/PRESSURE-TEST.md. Not part of any real application.
// Not itself part of the reviewed diff -- included so before.ts/after.ts type-check in isolation.

export interface WarehouseConnection {
	reserveItems(
		items: string[],
		paymentToken: string,
	): Promise<{ success: boolean }>;
	close(): void;
}

export interface WarehouseClient {
	openConnection(): WarehouseConnection;
}
