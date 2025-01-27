import argparse
import sys
from argparse import ArgumentParser

from modules.adi_lib.plugin.base import BaseSearch
from plugins import PluginBase
from utils.consts import AllPluginTypes
from utils.logger import output

# 模块类型
__type__ = "AD"
# 模块帮助信息
__help__ = "AD module"

__all__ = [__type__, __help__, "parse_user_args"]


def enrollment_parameters(parser: ArgumentParser, all_plugins: dict[str, PluginBase], exp_sub_name: str) -> None:
    """
    注册模块参数

    :param parser: 参数接收器
    :return: None
    """
    output.debug(f"init {__type__} parameters")

    # AD-scan 模块
    ad_sub_mode = parser.add_subparsers(dest="scan_type")
    scan_mode = ad_sub_mode.add_parser("scan", formatter_class=argparse.RawDescriptionHelpFormatter)

    scan_mode_group = scan_mode.add_mutually_exclusive_group(required=True)
    scan_mode_group.add_argument("--all", help="select all plugins", action=argparse.BooleanOptionalAction, dest="all")
    scan_mode_group.add_argument("--plugin", help="select one or more plugin (E.G. plugin name1, plugin name 2...)",
                                 nargs="+", dest="plugins")
    scan_mode.add_argument("-u", "--username", required=False, default=None, dest="username")
    scan_mode.add_argument("-p", "--password", required=False, default=None, dest="password")
    scan_mode.add_argument("-d", "--domain", help="Domain FQDN(dc.test.lab)", required=True, default=None,
                           dest="domain_fqdn")
    scan_mode.add_argument("--dc-ip", required=False, default=None, dest="domain_ip")

    exploit_mode = ad_sub_mode.add_parser("exploit", formatter_class=argparse.RawDescriptionHelpFormatter)
    exp_plugin_mode = exploit_mode.add_subparsers()
    # 加载所有AD-exploit插件，读取参数，注册
    for name, exp in all_plugins.items():
        if exp.p_type == AllPluginTypes.Exploit:
            exp_sub_plugin_mode = exp_plugin_mode.add_parser(exp.alias,
                                                             formatter_class=argparse.RawDescriptionHelpFormatter)
        # 防止没有输入alice的错误
        if exp.alias != "" and exp.alias == exp_sub_name:
            c: PluginBase = exp()
            all_plugins[name] = c

            try:
                c.reg_argument(exp_sub_plugin_mode)
            except argparse.ArgumentError as e:
                output.error(f"{name} argument error: {e}")
                sys.exit(-2)


class PluginAdExploitBase(PluginBase):
    def __init__(self):
        super().__init__()


class PluginADScanBase(PluginBase, BaseSearch):
    def __init__(self, *args, **kwargs):
        uarg = args[0]

        _fqdn: list = uarg.domain_fqdn.split(".")
        _fqdn = _fqdn[1:] # skip domain controller hostname
        #_base_dn = f"dc={_fqdn[-2]},dc={_fqdn[-1]}"
        _base_dn = ",dc=".join(_fqdn)
        _base_dn = "dc=" + _base_dn

        if len(_fqdn) != 3:
            output.error("domain fqdn input error.")

        dc_conf = {
            "ldap_conf": {
                "dn": _base_dn,
                "password": uarg.password,
                "user": f"{uarg.username}@{'.'.join(_fqdn[-2:])}",
                "DNS": "",
                "server": f"ldap://{'.'.join(args[0].domain_fqdn.split('.'))}"
            },
            "name": '.'.join(_fqdn[-2:]),
            "ip": uarg.domain_ip,
            "hostname": _fqdn[0],
            "fqdn": '.'.join(args[0].domain_fqdn.split(".")),
            "platform": ""
        }

        meta_data = {

        }
        env = {}

        super(BaseSearch, self).__init__(dc_conf, meta_data, env)


def parse_user_args(args: argparse.Namespace):
    domain_fqdn: str = args.domain
    domain_name = ".".join(domain_fqdn.split(".")[-2:])

    try:
        hash = args.hash
    except Exception:
        hash = args.hashes

    if hash is not None:
        lmhash, nthash = args.hashes.split(':')
    else:
        lmhash = ''
        nthash = ''

    try:
        dc_ip = args.dc_ip
    except Exception:
        dc_ip = args.target_ip

    return domain_fqdn, domain_name, dc_ip, lmhash, nthash
