# Remote Config recipe (reactive flags)

Grounded in https://firebase.google.com/docs/remote-config/real-time-best-practices
and https://firebase.google.com/docs/remote-config/get-started (verify flag
names against the current BoM on first use).

## Setup (one-time)

1. Dependencies: `firebase-config` KTX via the BoM (google-services plugin
   already required - the project has it for Crashlytics/App Distribution).
2. Defaults in code: `remoteConfig.setDefaultsAsync(mapOf(...))` from the
   typed flag enum - a missing remote key never crashes, it falls back.
3. Settings: `remoteConfigSettings { minimumFetchIntervalInSeconds }` - short
   (minutes) in debug, hours in release.

## Reactive wiring

```kotlin
class FlagRepository(rc: FirebaseRemoteConfig, scope: CoroutineScope) {
    private val _flags = MutableStateFlow(Flags.from(rc.all))
    val flags: StateFlow<Flags> = _flags.asStateFlow()

    init {
        rc.addOnConfigUpdateListener { update ->
            if (update.updatedKeys.isNotEmpty()) {
                rc.activate().addOnCompleteListener { _flags.value = Flags.from(rc.all) }
            }
        }
        scope.launch { rc.fetchAndActivate() } // first fetch
    }
}
```

- ONE listener for the whole app (shared HTTP connection; keep the
  ListenerRegistration and `remove()` it when the scope dies).
- UI collects `flags` as state - a console change reaches the device in
  seconds, screens re-compose, no restart, no interrupting the user's flow.
- Debug override sits ABOVE this in precedence (DataStore), so the developer
  can pin a flag while remote says otherwise.

## Release behavior

Remote Config works in release - that is the point: kill switches and rollout
percentages are console operations, not app releases. Only the DEV TOGGLES
(DataStore overrides, dev menu) must be compiled out of release.
