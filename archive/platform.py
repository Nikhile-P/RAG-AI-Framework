"""Streamlit entrypoint that avoids shadowing the stdlib `platform` module.

This file must remain named `platform.py` for the Streamlit launcher, but it
also needs to behave like the real stdlib `platform` module when imported by
third-party packages such as NumPy or Streamlit internals.
"""

from __future__ import annotations

import importlib.util
import os
import sysconfig


_stdlib_platform_path = os.path.join(sysconfig.get_path("stdlib"), "platform.py")
_stdlib_spec = importlib.util.spec_from_file_location("_stdlib_platform", _stdlib_platform_path)
if _stdlib_spec is None or _stdlib_spec.loader is None:
    raise ImportError("Could not load the standard library platform module")

_stdlib_platform = importlib.util.module_from_spec(_stdlib_spec)
_stdlib_spec.loader.exec_module(_stdlib_platform)

for _name, _value in vars(_stdlib_platform).items():
    if _name.startswith("__") and _name not in {"__doc__", "__all__"}:
        continue
    globals()[_name] = _value


def main() -> None:
    import streamlit as st

    st.set_page_config(
        page_title="Lenovo Enterprise AI Platform",
        page_icon="🔴",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    home = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
    research = st.Page("appt.py", title="Research Workspace", icon="🔍")
    health = st.Page("pages/health.py", title="System Health", icon="📈")

    # position="hidden" prevents the auto-generated nav from polluting
    # each page's own sidebar content
    pg = st.navigation(
        {"Platform": [home], "Tools": [research, health]},
        position="hidden",
    )
    pg.run()


if __name__ == "__main__":
    main()
