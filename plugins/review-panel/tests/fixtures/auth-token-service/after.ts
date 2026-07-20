// Fixture: auth-token-service module, AFTER state (the PR diff under review).
// Used only by plugins/review-panel/tests/SECURITY-PRESSURE-TEST.md. Not part of any real application.

import type { DbClient, DbRow, JwtClient } from "./auth-clients";

const JWT_SECRET = "supersecret-dev-key-2024";

export interface SessionRequest {
	token: string;
	requestedUserId: string;
}

/**
 * Authenticates an incoming request: decodes the JWT to identify the caller, then looks up
 * the requested user's profile.
 */
export async function authenticateSession(
	req: SessionRequest,
	jwt: JwtClient,
	db: DbClient,
): Promise<{ userId: string; profile: DbRow | null }> {
	const claims = jwt.decode(req.token);

	const result = await db.query(
		"SELECT * FROM users WHERE id = '" + req.requestedUserId + "'",
	);
	return { userId: claims.sub, profile: result.rows[0] ?? null };
}
