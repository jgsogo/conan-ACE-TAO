
import os
from conans import ConanFile, tools, MSBuild, AutoToolsBuildEnvironment
from conans.errors import ConanException

from contextlib import contextmanager


@contextmanager
def append_to_env_variable(var, value, separator, prepend=False):
    old_value = os.getenv(var, None)
    try:
        new_value = [old_value, value] if old_value else [value, ]
        if prepend:
            new_value = reversed(new_value)
        os.environ[var] = separator.join(new_value)
        yield
    finally:
        if old_value is not None:
             os.environ[var] = old_value
        else:
             del os.environ[var]


class AcetaoConan(ConanFile):
    name = "ACE+TAO"
    version = "6.4.6"
    license = "<Put the package license here>"
    url = "https://github.com/DOCGroup/ACE_TAO"
    description = "<Description of Acetao here>"
    settings = "os", "compiler", "build_type", "arch"

    generators = "visual_studio", "gcc"

    source_subfolder = 'source_subfolder'

    def build_requirements(self):
        if self.settings.os == "Windows":
            self.build_requires('strawberryperl/5.26.0@conan/stable')

    def configure(self):
        if self.settings.os not in ["Windows", "Linux", "Macos"]:
            raise ConanException("Recipe for settings.os='{}' not implemented.".format(self.settings.os))
        if self.settings.os == "Windows" and self.settings.compiler != "Visual Studio":
            raise ConanException("Recipe for settings.os='{}' and compiler '{}' not implemented.".format(self.settings.os, self.settings.compiler))

    def source(self):
        version = self.version.replace('.', '_')

        # We need MPC
        #  TODO: Make it another conan recipe
        source_url = "https://github.com/DOCGroup/MPC/archive"
        tools.get("{0}/{1}-{2}.tar.gz".format(source_url, self.name, version))
        os.rename('MPC-ACE-TAO-{}'.format(version), 'MPC')

        source_url = "https://github.com/DOCGroup/ACE_TAO/archive"
        tools.get("{0}/{1}-{2}.tar.gz".format(source_url, self.name, version))
        os.rename('ACE_TAO-ACE-TAO-{}'.format(version), self.source_subfolder)

    def build(self):
        working_dir = os.path.join(self.build_folder, self.source_subfolder)

        # Create config.h
        with open(os.path.join(working_dir, 'ACE', 'ace', 'config.h'), 'w') as f:
            # TODO: May add opotions like ACE_FACE_SAFETY_BASE
            if self.settings.os == "Windows":
                f.write('#include "ace/config-win32.h"\n')
            elif self.settings.os == "Linux":
                f.write('#include "ace/config-linux.h"\n')
            else:  # Macos
                f.write('#include "ace/config-macosx.h"\n')

        # Set env variables and run build
        with tools.environment_append({'MPC_ROOT': os.path.join(working_dir, '..', 'MPC'),
                                       'ACE_ROOT': os.path.join(working_dir, 'ACE'),
                                       'TAO_ROOT': os.path.join(working_dir, 'TAO')}):
            if self.settings.os == "Windows":
                self.build_windows(working_dir)
            elif self.settings.os == "Linux":
                self.build_linux(working_dir)
            else:
                self.build_macos(working_dir)

    def _exec_mpc(self, working_dir, type, mwc=None):
        mwc = mwc or os.path.join(working_dir, 'TAO', 'TAO_ACE.mwc')
        command = ['perl', os.path.join(working_dir, 'ACE', 'bin', 'mwc.pl'), '--type', type, mwc, ]
        self.run(' '.join(command))

    def build_windows(self, working_dir):
        assert self.settings.os == "Windows"
        assert self.settings.compiler == "Visual Studio"

        # Generate project using MPC
        compiler_version = int(str(self.settings.compiler.version))
        if compiler_version <= 14:
            self._exec_mpc(working_dir, type='vc{}'.format(compiler_version))
        else:
            compiler_type = {15: '2017', }[compiler_version]
            self._exec_mpc(working_dir, type='vs{}'.format(compiler_type))

        # Compile
        msbuild = MSBuild(self)
        msbuild.build(os.path.join(working_dir, 'TAO', 'TAO_ACE.sln'), upgrade_project=False)

    def build_linux(self, working_dir):
        assert self.settings.os == "Linux"

        conan_mwc = os.path.join(working_dir, 'conan.mwc')
        with open(conan_mwc, 'w') as f:
            f.write("workspace {\n")
            f.write("$(TAO_ROOT)/TAO_ACE.mwc\n")  # Condition to TAO
            # f.write("$(TAO_ROOT)/tests/Hello\n")
            # f.write("$(ACE_ROOT)/ace/ace.mwc\n")  # Condition to ACE
            # f.write("$(ACE_ROOT)/tests\n")  # Condition to ACETESTS
            f.write("}\n")

        with open(os.path.join(working_dir, 'ACE', 'include', 'makeinclude', 'platform_macros.GNU'), 'w') as f:
            f.write("INSTALL_PREFIX = {}\n".format(os.path.join(self.build_folder, 'install')))  # Will ease package creation
            #f.write("xerces3=1\nssl=1\n")
            f.write("inline=0\nipv6=1\n")
            f.write("c++11=1\n")
            f.write("ace_for_tao=1\n")
            if self.settings.compiler == "clang":
                f.write("include $(ACE_ROOT)/include/makeinclude/platform_linux_clang.GNU\n")
            else:
                f.write("include $(ACE_ROOT)/include/makeinclude/platform_linux.GNU\n")

        with open(os.path.join(working_dir, 'ACE', 'bin', 'MakeProjectCreator', 'config', 'default.features'), 'w') as f:
            #f.write("xerces3=1\nssl=1\n")
            f.write("ace_for_tao=1\n")

        self._exec_mpc(working_dir, type='gnuace', mwc=conan_mwc)
        with append_to_env_variable('LD_LIBRARY_PATH', os.path.join(working_dir, 'ACE', 'lib'), separator=':', prepend=True): 
            with tools.chdir(working_dir):
                env_build = AutoToolsBuildEnvironment(self)
                env_build.make()
                self.run("make install")

    def build_macos(self, working_dir):
        raise ConanException("AcetaoConan::build_macos not implemented")

    def package(self):
        install_folder = os.path.join(self.build_folder, 'install')
        self.copy("*.h", dst="include", src=install_folder)
        self.copy("*.dll", dst="bin", src=install_folder, keep_path=False)
        self.copy("*.so", dst="lib", src=install_folder, keep_path=False)
        self.copy("*.dylib", dst="lib", src=install_folder, keep_path=False)
        self.copy("*.a", dst="lib", src=install_folder, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

