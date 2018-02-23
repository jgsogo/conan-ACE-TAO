
import os
from conans import ConanFile, CMake, tools, MSBuild, AutoToolsBuildEnvironment
from conans.errors import ConanException


class AcetaoConan(ConanFile):
    name = "ACE+TAO"
    version = "6.4.6"
    license = "<Put the package license here>"
    url = "https://github.com/DOCGroup/ACE_TAO"
    description = "<Description of Acetao here>"
    settings = "os", "compiler", "build_type", "arch"

    generators = "visual_studio", "gcc"

    source_subfolder = 'source_subfolder'

    def build_requirements(self):  # TODO: Check, if using build_requirements it does not add env variable to path
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
            if self.settings.os == "Windows":
                f.write('#include "ace/config-win32.h"\n')
            elif self.settings.os == "Linux":
                f.write('#include "ace/config-linux.h"\n')
            else:  # Macos
                f.write('#include "ace/config-macosx.h"\n')

        if self.settings.os == "Windows":
            self.build_windows(working_dir)
        elif self.settings.os == "Linux":
            self.build_linux(working_dir)
        else:
            self.build_macos(working_dir)

    def _exec_mpc(self, working_dir, type):
        command = ['perl', os.path.join(working_dir, 'ACE', 'bin', 'mwc.pl'), '--type', type,
                   os.path.join(working_dir, 'TAO', 'TAO_ACE.mwc'), ]

        with tools.environment_append({'MPC_ROOT': os.path.join(working_dir, '..', 'MPC'),
                                       'ACE_ROOT': os.path.join(working_dir, 'ACE'),
                                       'TAO_ROOT': os.path.join(working_dir, 'TAO')}):
            self.output.info("Generate project: {}".format(' '.join(command)))
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
        try:
            msbuild.build(os.path.join(working_dir, 'TAO', 'TAO_ACE.sln'))
        except:
            with open(os.path.join(working_dir, 'TAO', 'UpgradeLog.htm')) as f:
                self.output.info("*"*20)
                self.output.info("\n\n")
                self.output.info(f.read())
                self.output.info("\n\n")
                self.output.info("*"*20)
            raise

    def build_linux(self, working_dir):
        assert self.settings.os == "Linux"

        self._exec_mpc(working_dir, type='make')
        with open(os.path.join(working_dir, 'include', 'makeinclude', 'platform_macros.GNU'), 'w') as f:
            f.write("include $(ACE_ROOT)/include/makeinclude/platform_linux.GNU\n")

        with tools.environment_append({'ACE_ROOT': working_dir, }):
            env_build = AutoToolsBuildEnvironment(self)
            with tools.chdir(os.path.join(working_dir, 'TAO')):
                env_build.make()

    def build_macos(self, working_dir):
        raise ConanException("AcetaoConan::build_macos not implemented")

    def package(self):
        self.copy("*.h", dst="include", src="hello")
        self.copy("*hello.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
