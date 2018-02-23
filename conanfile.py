
import os
from conans import ConanFile, CMake, tools, MSBuild
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

    def source(self):
        source_url = "http://download.dre.vanderbilt.edu/previous_versions"  # TODO: May I use https://github.com/DOCGroup/ACE_TAO/releases?
        tools.get("{0}/{1}-src-{2}.tar.gz".format(source_url, self.name, self.version))
        source_subfolder = os.path.join(os.getcwd(), 'ACE_wrappers')
        
        # Create config.h
        with open(os.path.join(source_subfolder, 'ace', 'config.h'), 'w') as f:
            if self.settings.os == "Windows":
                f.write('#include "ace/config-win32.h"\n')
            elif self.settings.os == "Linux":
                f.write('#include "ace/config-linux.h"\n')

    def build(self):
        working_dir = os.path.join(os.getcwd(), 'ACE_wrappers')

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

    def package(self):
        self.copy("*.h", dst="include", src="hello")
        self.copy("*hello.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["ACE+TAO"]
