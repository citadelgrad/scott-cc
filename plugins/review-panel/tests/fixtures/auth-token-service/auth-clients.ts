// Fixture: auth-token-service module, type-only support file.
// Used only by plugins/review-panel/tests/SECURITY-PRESSURE-TEST.md. Not part of any real application.

export interface JwtClaims {
	sub: string;
	scope: string[];
}

export interface JwtClient {
	/** Verifies the token's signature against `secret` and returns its claims. Throws if invalid. */
	verify(token: string, secret: string): JwtClaims;
	/** Decodes the token's payload WITHOUT verifying its signature. */
	decode(token: string): JwtClaims;
}

export interface DbRow {
	id: string;
	[key: string]: unknown;
}

export interface DbClient {
	query(sql: string, params?: unknown[]): Promise<{ rows: DbRow[] }>;
}
