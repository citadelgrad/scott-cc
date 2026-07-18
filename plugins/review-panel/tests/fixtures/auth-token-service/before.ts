// Fixture: auth-token-service module, BEFORE state (clean baseline).
// Used only by plugins/review-panel/tests/SECURITY-PRESSURE-TEST.md. Not part of any real application.

import type { DbClient, DbRow, JwtClient } from "./auth-clients";

const JWT_SECRET = process.env.AUTH_JWT_SECRET;

export interface SessionRequest {
	token: string;
	requestedUserId: string;
}

/**
 * Authenticates an incoming request: verifies the JWT's signature against the server's secret,
 * then looks up the authenticated caller's own profile by their verified subject claim.
 */
export async function authenticateSession(
	req: SessionRequest,
	jwt: JwtClient,
	db: DbClient,
): Promise<{ userId: string; profile: DbRow | null }> {
	if (!JWT_SECRET) {
		throw new Error("authenticateSession: AUTH_JWT_SECRET is not configured");
	}
	const claims = jwt.verify(req.token, JWT_SECRET);

	const result = await db.query("SELECT * FROM users WHERE id = $1", [
		claims.sub,
	]);
	return { userId: claims.sub, profile: result.rows[0] ?? null };
}
