export interface DiscountLabelStrategy {
	format(percentOff: number): string;
}

export class PercentDiscountLabelStrategy implements DiscountLabelStrategy {
	format(percentOff: number): string {
		if (percentOff <= 0) {
			return "No discount";
		}
		return `${percentOff}% off`;
	}
}

export class DiscountLabelStrategyFactory {
	static create(): DiscountLabelStrategy {
		return new PercentDiscountLabelStrategy();
	}
}

export function formatDiscountLabel(percentOff: number): string {
	return DiscountLabelStrategyFactory.create().format(percentOff);
}
