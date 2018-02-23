
import os
from conans import ConanFile, CMake, tools, MSBuild, AutoToolsBuildEnvironment
from conans.errors import ConanException


class AcetaoConan(ConanFile):
    name = "ACE+TAO"
    version = "6.4.6"
    license = "<Put the package license here>"
    url = "http://www.dre.vanderbilt.edu/"
    description = "<Description of Acetao here>"
    settings = "os", "compiler", "build_type", "arch"

    generators = "visual_studio", "gcc"

    requires = 'strawberryperl/5.26.0@conan/stable'

    def configure(self):
        if self.settings.os not in ["Windows", "Linux", "Macos"]:
            raise ConanException("Recipe for settings.os='{}' not implemented.".format(self.settings.os))

    def source(self):
        source_url = "http://download.dre.vanderbilt.edu/previous_versions"  # TODO: May I use https://github.com/DOCGroup/ACE_TAO/releases?
        tools.get("{0}/{1}-src-{2}.tar.gz".format(source_url, self.name, self.version))

    def build(self):
        working_dir = os.path.join(self.build_folder, 'ACE_wrappers')

        # Create config.h
        with open(os.path.join(working_dir, 'ace', 'config.h'), 'w') as f:
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

    def build_windows(self, working_dir):
        assert self.settings.os == "Windows"

        # Generate project using MPC
        command = ['perl', os.path.join(working_dir, 'bin', 'mwc.pl'), ]
        if self.settings.compiler == "Visual Studio":
            command += ['--type', 'vc{}'.format(self.settings.compiler.version)]
        else:
            raise ConanException("Compiler '{}' not implemented.".format(self.settings.compiler))
        command += [os.path.join(working_dir, 'TAO', 'TAO_ACE.mwc'), ]
        with tools.environment_append({'MPC_ROOT': os.path.join(working_dir, 'MPC'),
                                       'ACE_ROOT': working_dir,
                                       'TAO_ROOT': os.path.join(working_dir, 'TAO')}):
            self.output.info("Generate project: {}".format(' '.join(command)))
            self.run(' '.join(command))

        # Compile
        if self.settings.compiler == "Visual Studio":
            msbuild = MSBuild(self)
            msbuild.build(os.path.join(working_dir, 'TAO', 'TAO_ACE.sln'))

    def build_linux(self, working_dir):
        assert self.settings.os == "Linux"

        with open(os.path.join(working_dir, 'include', 'makeinclude', 'platform_macros.GNU'), 'w') as f:
            f.write("include $(ACE_ROOT)/include/makeinclude/platform_linux.GNU\n")

        with tools.environment_append({'ACE_ROOT': working_dir,}):
            env_build = AutoToolsBuildEnvironment(self)
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
        self.cpp_info.libs = ["ACE+TAO"]
