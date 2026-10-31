# Auth test users (Admin SDK)

Testers need sign-in accounts (the accounts the app logs in with)? The
Firebase CLI cannot create Firebase Authentication users — there is no
`auth:user-create` command. The supported path is a one-shot Node script
using the Firebase Admin SDK. Run it from any scratch dir; it is
idempotent (existing emails are skipped).

## Setup

1. Console → Project settings → Service accounts → Generate new private
   key → save the JSON somewhere outside the repo (never commit it).
2. `export GOOGLE_APPLICATION_CREDENTIALS="/abs/path/service-account.json"`
3. `npm install firebase-admin`
4. Enable the sign-in providers the app uses, if not already on:
   console → Authentication → Sign-in method (e.g. Email/Password).

## Script

`create-auth-test-users.mjs`:

```js
import { initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

initializeApp(); // picks up GOOGLE_APPLICATION_CREDENTIALS
const auth = getAuth();

const users = [
  { email: "tester-1@example.com", password: "CHANGE-ME-1", displayName: "Tester One" },
  { email: "tester-2@example.com", password: "CHANGE-ME-2", displayName: "Tester Two" },
];

for (const u of users) {
  try {
    const existing = await auth.getUserByEmail(u.email);
    console.log("exists, skipped:", existing.uid, existing.email);
    continue;
  } catch (e) {
    if (e.code !== "auth/user-not-found") throw e;
  }
  const record = await auth.createUser({
    email: u.email,
    password: u.password,
    displayName: u.displayName,
    emailVerified: false,
  });
  console.log("created:", record.uid, record.email);
}
```

Run: `node create-auth-test-users.mjs`.

## Notes

- `emailVerified: true` only when the app gates sign-in on verification;
  `false` is the documented default.
- Auth users and App Distribution testers are separate rosters: creating an
  Auth account never grants download access. A tester who needs both gets
  the same email in both places (SKILL.md step 2).
- These are test accounts: throwaway passwords, handed over through the
  channel the testers already use.
