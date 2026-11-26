# Reaper framework standard-library facade

Import the framework suite from a Reaper program with:

```reaper
import "stdlib/frameworks.rpr" as frameworks

make locale := frameworks["get_framework"]("Lokaliza")
make translated := locale["locale_plural_category"]("uk", 23)
emit translated
```

The facade re-exports the ten independent framework modules. It does not create a second runtime, grant host privileges or hide module loading. Lifecycle and resource ownership remain in ДОМ. Each framework reports only its implemented source-level operations; platform and compiler features continue to require their own explicit host/compiler contracts.
