import orbits as orb

"""This Python file runs all tests in the orbits package under a single file."""

print("\n\norbit.py tests:")
orb.orbit.test()

print("\n\ncelestial.py tests:")
orb.celestials.test()

print("\n\nconfig.py tests:")
orb.config.test()