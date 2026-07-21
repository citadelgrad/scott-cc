export function formatDiscountLabel(percentOff: number): string {
	if (percentOff <= 0) {
		return "No discount";
	}
	return `${percentOff}% off`;
}
