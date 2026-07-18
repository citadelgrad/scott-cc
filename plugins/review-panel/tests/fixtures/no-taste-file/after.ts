export default function processOrder(order: Order): Receipt {
	try {
		order.status = "processing";
		try {
			const totals = computeTotals(order);
			try {
				return buildReceipt(order, totals);
			} catch (buildErr) {
				throw new Error(`build failed: ${buildErr}`);
			}
		} catch (totalsErr) {
			throw new Error(`totals failed: ${totalsErr}`);
		}
	} catch (err) {
		throw new Error(`processOrder failed: ${err}`);
	}
}
