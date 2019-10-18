#! /usr/bin/python

# Copyright (C) 2012 Canonical Ltd.
# Author: Colin Watson <cjwatson@ubuntu.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Unit tests for cdimage.config."""

from __future__ import print_function

import os
from textwrap import dedent

from cdimage.config import Config, Series, all_series
from cdimage.tests.helpers import TestCase, mkfile

__metaclass__ = type


class TestSeries(TestCase):
    def test_find_by_name(self):
        series = Series.find_by_name("hoary")
        self.assertEqual(("hoary", "5.04", "Hoary Hedgehog"), tuple(series))

    def test_find_by_version(self):
        series = Series.find_by_version("5.04")
        self.assertEqual(("hoary", "5.04", "Hoary Hedgehog"), tuple(series))

    def test_latest(self):
        self.assertTrue(Series.latest().is_latest)
        self.assertEqual("ubuntu", Series.latest().distribution)
        self.assertTrue(Series.latest(distribution="ubuntu-rtm").is_latest)
        self.assertEqual(
            "ubuntu-rtm",
            Series.latest(distribution="ubuntu-rtm").distribution)
        self.assertRaises(
            ValueError, Series.latest, distribution="nonexistent")

    def test_str(self):
        series = Series.find_by_name("warty")
        self.assertEqual("warty", str(series))
        series = Series.find_by_name("ubuntu-rtm/14.09")
        self.assertEqual("14.09", str(series))

    def test_full_name(self):
        series = Series.find_by_name("utopic")
        self.assertEqual("utopic", series.full_name)
        series = Series.find_by_name("ubuntu-rtm/14.09")
        self.assertEqual("ubuntu-rtm/14.09", series.full_name)

    def test_format(self):
        series = Series.find_by_name("warty")
        self.assertEqual("warty", "%s" % series)
        series = Series.find_by_name("ubuntu-rtm/14.09")
        self.assertEqual("14.09", "%s" % series)

    def test_is_latest(self):
        self.assertFalse(all_series[0].is_latest)
        self.assertTrue(all_series[-1].is_latest)

    def test_compare(self):
        series = Series.find_by_name("hoary")

        self.assertLess(series, "breezy")
        self.assertLessEqual(series, "hoary")
        self.assertLessEqual(series, "breezy")
        self.assertEqual(series, "hoary")
        self.assertNotEqual(series, "warty")
        self.assertNotEqual(series, "breezy")
        self.assertGreaterEqual(series, "warty")
        self.assertGreaterEqual(series, "hoary")
        self.assertGreater(series, "warty")

        self.assertLess(series, Series.find_by_name("breezy"))
        self.assertLessEqual(series, Series.find_by_name("hoary"))
        self.assertLessEqual(series, Series.find_by_name("breezy"))
        self.assertEqual(series, Series.find_by_name("hoary"))
        self.assertNotEqual(series, Series.find_by_name("warty"))
        self.assertNotEqual(series, Series.find_by_name("breezy"))
        self.assertGreaterEqual(series, Series.find_by_name("warty"))
        self.assertGreaterEqual(series, Series.find_by_name("hoary"))
        self.assertGreater(series, Series.find_by_name("warty"))

    def test_displayversion(self):
        series = Series.find_by_name("breezy")
        self.assertEqual("5.10", series.displayversion("ubuntu"))
        series = Series.find_by_name("dapper")
        self.assertEqual("6.06.2 LTS", series.displayversion("ubuntu"))
        self.assertEqual("6.06.2", series.displayversion("xubuntu"))

    def test_distribution(self):
        series = Series.find_by_name("utopic")
        self.assertEqual("ubuntu", series.distribution)
        series = Series.find_by_name("ubuntu-rtm/14.09")
        self.assertEqual("ubuntu-rtm", series.distribution)


class TestConfig(TestCase):
    def test_default_root(self):
        os.environ.pop("CDIMAGE_ROOT", None)
        config = Config(read=False)
        expected_root = os.path.dirname(__file__)       # lib/cdimage/tests
        expected_root = os.path.dirname(expected_root)  # lib/cdimage
        expected_root = os.path.dirname(expected_root)  # lib
        expected_root = os.path.dirname(expected_root)  # .
        self.assertEqual(os.path.realpath(expected_root), config.root)

    def test_root_from_environment(self):
        os.environ["CDIMAGE_ROOT"] = "/path"
        config = Config(read=False)
        self.assertEqual("/path", config.root)

    def test_default_values(self):
        config = Config(read=False)
        self.assertEqual("", config["PROJECT"])

    def test_init_kwargs(self):
        config = Config(read=False, IMAGE_TYPE="daily-live")
        self.assertEqual("daily-live", config["IMAGE_TYPE"])

    def test_init_kwargs_default_arches(self):
        os.environ["CDIMAGE_ROOT"] = self.use_temp_dir()
        os.environ.pop("ARCHES", None)
        os.environ.pop("CPUARCHES", None)
        etc_dir = os.path.join(self.temp_dir, "etc")
        with mkfile(os.path.join(etc_dir, "config")) as f:
            print(dedent("""\
                #! /bin/sh
                PROJECT=ubuntu
                DIST=raring
                """), file=f)
        with mkfile(os.path.join(etc_dir, "default-arches")) as f:
            print("*\tdaily-live\traring\tamd64 amd64+mac i386", file=f)
        config = Config(IMAGE_TYPE="daily-live")
        self.assertEqual("daily-live", config["IMAGE_TYPE"])
        self.assertEqual("amd64 amd64+mac i386", config["ARCHES"])
        self.assertEqual("amd64 i386", config["CPUARCHES"])

    def test_init_kwargs_default_arches_subproject(self):
        os.environ["CDIMAGE_ROOT"] = self.use_temp_dir()
        os.environ.pop("ARCHES", None)
        os.environ.pop("CPUARCHES", None)
        etc_dir = os.path.join(self.temp_dir, "etc")
        with mkfile(os.path.join(etc_dir, "config")) as f:
            print(dedent("""\
                #! /bin/sh
                PROJECT=ubuntu
                DIST=raring
                """), file=f)
        with mkfile(os.path.join(etc_dir, "default-arches")) as f:
            print("ubuntu-wubi\t*\traring\tamd64 i386", file=f)
            print("*\t*\t*\tamd64 i386 powerpc", file=f)
        config = Config(SUBPROJECT="wubi", IMAGE_TYPE="wubi")
        self.assertEqual("amd64 i386", config["ARCHES"])

    def test_read_shell(self):
        os.environ["CDIMAGE_ROOT"] = self.use_temp_dir()
        with mkfile(os.path.join(self.temp_dir, "etc", "config")) as f:
            print(dedent("""\
                #! /bin/sh
                PROJECT=ubuntu
                CAPPROJECT=Ubuntu
                """), file=f)
        config = Config()
        self.assertEqual("ubuntu", config["PROJECT"])
        self.assertEqual("Ubuntu", config["CAPPROJECT"])
        self.assertNotIn("DEBUG", config)

    def test_missing_config(self):
        # Even if etc/config is missing, Config still reads values from the
        # environment.  This makes it easier to experiment locally.
        self.use_temp_dir()
        os.environ["CDIMAGE_ROOT"] = self.temp_dir
        os.environ["PROJECT"] = "kubuntu"
        config = Config()
        self.assertEqual("kubuntu", config["PROJECT"])

    def test_match_series(self):
        config = Config(read=False)
        config["DIST"] = "precise"
        self.assertTrue(config.match_series("*"))
        self.assertTrue(config.match_series("natty-precise"))
        self.assertTrue(config.match_series("precise-quantal"))
        self.assertTrue(config.match_series("natty-quantal"))
        self.assertFalse(config.match_series("lucid-natty"))
        self.assertFalse(config.match_series("quantal-raring"))
        self.assertTrue(config.match_series("precise-"))
        self.assertFalse(config.match_series("quantal-"))
        self.assertTrue(config.match_series("-precise"))
        self.assertFalse(config.match_series("-oneiric"))
        self.assertFalse(config.match_series("lucid"))
        self.assertTrue(config.match_series("precise"))
        self.assertFalse(config.match_series("ubuntu-rtm/*"))
        self.assertFalse(config.match_series("ubuntu-rtm/14.09-"))
        config["DIST"] = "ubuntu-rtm/14.09"
        self.assertTrue(config.match_series("*"))
        self.assertFalse(config.match_series("ubuntu/*"))
        self.assertFalse(config.match_series("precise-"))
        self.assertTrue(config.match_series("ubuntu-rtm/*"))
        self.assertTrue(config.match_series("ubuntu-rtm/14.09-"))

    def test_arches_override(self):
        # If ARCHES is set in the environment, it overrides
        # etc/default-arches.
        os.environ["CDIMAGE_ROOT"] = self.use_temp_dir()
        os.environ["ARCHES"] = "amd64"
        os.environ.pop("CPUARCHES", None)
        etc_dir = os.path.join(self.temp_dir, "etc")
        with mkfile(os.path.join(etc_dir, "config")) as f:
            print(dedent("""\
                #! /bin/sh
                PROJECT=ubuntu
                DIST=raring
                """), file=f)
        with mkfile(os.path.join(etc_dir, "default-arches")) as f:
            print("*\tdaily-live\traring\tamd64 amd64+mac i386", file=f)
        config = Config(IMAGE_TYPE="daily-live")
        self.assertEqual("daily-live", config["IMAGE_TYPE"])
        self.assertEqual("amd64", config["ARCHES"])
        self.assertEqual("amd64", config["CPUARCHES"])

    def test_limit_arches(self):
        # limit_arches reduces ARCHES and CPUARCHES to only those items also
        # present in the iterable passed as a parameter.
        self.use_temp_dir()
        os.environ["CDIMAGE_ROOT"] = self.temp_dir
        os.environ["ARCHES"] = "amd64 amd64+mac i386 powerpc"
        config = Config()
        self.assertEqual(
            ["amd64", "amd64+mac", "i386", "powerpc"], config.arches)
        self.assertEqual("amd64 amd64+mac i386 powerpc", os.environ["ARCHES"])
        self.assertEqual(["amd64", "i386", "powerpc"], config.cpuarches)
        self.assertEqual("amd64 i386 powerpc", os.environ["CPUARCHES"])

        config.limit_arches(["amd64", "amd64+mac", "i386", "sparc"])
        self.assertEqual(["amd64", "amd64+mac", "i386"], config.arches)
        self.assertEqual("amd64 amd64+mac i386", os.environ["ARCHES"])
        self.assertEqual(["amd64", "i386"], config.cpuarches)
        self.assertEqual("amd64 i386", os.environ["CPUARCHES"])

        config.limit_arches(["amd64"])
        self.assertEqual(["amd64"], config.arches)
        self.assertEqual("amd64", os.environ["ARCHES"])
        self.assertEqual(["amd64"], config.cpuarches)
        self.assertEqual("amd64", os.environ["CPUARCHES"])

    def test_project(self):
        config = Config(read=False)
        config["PROJECT"] = "kubuntu"
        self.assertEqual("kubuntu", config.project)

    def test_capproject(self):
        config = Config(read=False)
        config["CAPPROJECT"] = "Kubuntu"
        self.assertEqual("Kubuntu", config.capproject)

    def test_subproject(self):
        config = Config(read=False)
        config["SUBPROJECT"] = "wubi"
        self.assertEqual("wubi", config.subproject)

    def test_distribution(self):
        config = Config(read=False)
        config["DIST"] = "utopic"
        self.assertEqual("ubuntu", config.distribution)
        config["DIST"] = "ubuntu-rtm/14.09"
        self.assertEqual("ubuntu-rtm", config.distribution)

    def test_series(self):
        config = Config(read=False)
        config["DIST"] = "warty"
        self.assertEqual("warty", config.series)

    def test_full_series(self):
        config = Config(read=False)
        config["DIST"] = "utopic"
        self.assertEqual("utopic", config.full_series)
        config["DIST"] = "ubuntu-rtm/14.09"
        self.assertEqual("ubuntu-rtm/14.09", config.full_series)

    def test_core_series(self):
        config = Config(read=False)
        config["DIST"] = "utopic"
        self.assertEqual(None, config.core_series)
        config["DIST"] = "xenial"
        self.assertEqual("16", config.core_series)
        config["DIST"] = "bionic"
        self.assertEqual("18", config.core_series)
        config["DIST"] = "cosmic"
        self.assertEqual("18", config.core_series)
        config["DIST"] = "disco"
        self.assertEqual("18", config.core_series)
        config["DIST"] = "eoan"
        self.assertEqual("18", config.core_series)
        config["DIST"] = "focal"
        self.assertEqual("20", config.core_series)

    def test_arches(self):
        config = Config(read=False)
        self.assertEqual([], config.arches)
        config["ARCHES"] = "i386"
        self.assertEqual(["i386"], config.arches)
        config["ARCHES"] = "amd64 i386"
        self.assertEqual(["amd64", "i386"], config.arches)

    def test_cpuarches(self):
        config = Config(read=False)
        self.assertEqual([], config.cpuarches)
        config["CPUARCHES"] = "i386"
        self.assertEqual(["i386"], config.cpuarches)
        config["CPUARCHES"] = "amd64 i386"
        self.assertEqual(["amd64", "i386"], config.cpuarches)

    def test_image_type(self):
        config = Config(read=False)
        config["IMAGE_TYPE"] = "daily-live"
        self.assertEqual("daily-live", config.image_type)

    def test_all_projects(self):
        config = Config(read=False)
        self.assertEqual([], config.all_projects)
        config["ALL_PROJECTS"] = "ubuntu"
        self.assertEqual(["ubuntu"], config.all_projects)
        config["ALL_PROJECTS"] = "ubuntu kubuntu"
        self.assertEqual(["ubuntu", "kubuntu"], config.all_projects)

    def test_export(self):
        os.environ["TEST_VAR"] = "1"
        config = Config(read=False)
        config["PROJECT"] = "ubuntu"
        config["DIST"] = "raring"
        expected_env = dict(os.environ)
        expected_env["PROJECT"] = "ubuntu"
        expected_env["DIST"] = "raring"
        self.assertEqual(expected_env, config.export())
