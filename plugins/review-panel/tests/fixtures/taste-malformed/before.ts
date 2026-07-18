export function processOrder(order: Order): Result<Receipt, OrderError> {
	return computeReceipt(order);
}
