# START_VERSION_BLOCK
VERSION_MAJOR = 0
VERSION_MINOR = 9
VERSION_BUILD = 0
VERSION_ALPHA = 26
# END_VERSION_BLOCK

# Thalovant's build of this code. Public PyPI cannot hold a local version, so a
# runtime pinning it never installs upstream's different 0.9.0a26 instead, and a
# requirement of ==0.9.0a26 is still met.
VERSION_LOCAL = "thalovant.1"
__version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_BUILD}" + (f"a{VERSION_ALPHA}" if VERSION_ALPHA else "")
__version__ += f"+{VERSION_LOCAL}" if VERSION_LOCAL else ""
