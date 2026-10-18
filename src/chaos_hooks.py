"""
============================================================================
  CHAOS_HOOKS.PY  --  hook points for unique card modifiers
============================================================================

Unique Chaos / Endless card modifiers (chaos_mods*.py) do things no stat
change can - a Lava Hound that drops pups as it flies, a Barbarian Hut that
spawns Mega Knights. A modifier names its hooks in the upgraded card copy's
`mods` dict; engine.py calls them at these points (all optional):

  mods["tick"]       = name   fn(e, dt, match)              every frame (unit/building alive)
  mods["hit"]        = name   fn(src, target, dmg, x, y, match)
                                  after it hits (target is None for a splash
                                  shot's impact point x, y)
  mods["death"]      = name   fn(e, match)                  when it dies
  mods["deploy"]     = name   fn(match, team, units, x, y)  right after it is
                                  played (units = what came out; [] for spells)
  mods["spell"]      = name   fn(match, team, card, x, y) -> True to replace
                                  the spell's normal effect
  mods["spell_after"]= name   fn(match, team, card, x, y, new_effects)
                                  after the normal effect (new Effects made)
  mods["fx_tick"]    = name   set on an Effect by a spell hook: fn(fx, dt, match)
  mods["proj_style"] = card key   its shots look (and fly) like that card's

Register a hook with @hook("tick") def lava_pups(e, dt, match): ... - the
function name is the hook's name. Per-unit state goes on the entity
(e.g. e._pup_t).
============================================================================
"""

HOOKS = {k: {} for k in ("tick", "hit", "death", "deploy", "spell", "spell_after",
                         "fx_tick")}


def hook(kind, name=None):
    def deco(fn):
        HOOKS[kind][name or fn.__name__] = fn
        return fn
    return deco


def get(kind, mods):
    """The hook of `kind` named in a card's mods (or None)."""
    if not mods:
        return None
    name = mods.get(kind)
    return HOOKS[kind].get(name) if name else None
