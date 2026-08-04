"""Modules with implemented runners."""

from multiscale_core.schema.workflow import ModuleName

IMPLEMENTED_MODULES: frozenset[ModuleName] = frozenset(
    {
        ModuleName.ENCAPSULATION,
        ModuleName.FORMATION,
        ModuleName.STABILITY,
        ModuleName.CORONA,
        ModuleName.CELL_INTERACTION,
        ModuleName.TRANSPORT,
        ModuleName.RELEASE,
    }
)
