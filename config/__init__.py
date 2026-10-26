# PyMySQL fallback support for MySQL on platforms without C++ build tools
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
