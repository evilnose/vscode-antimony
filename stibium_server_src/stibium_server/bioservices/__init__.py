import pkg_resources

__version__ = "1.6.0"
try:
    version = pkg_resources.require("bioservices")[0].version
    __version__ = version
except:
    version = __version__
