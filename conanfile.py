
import os
from conans import ConanFile, CMake, tools


class AcetaoConan(ConanFile):
    name = "ACE+TAO"
    version = "6.4.6"
    license = "<Put the package license here>"
    url = "http://www.dre.vanderbilt.edu/"
    description = "<Description of Acetao here>"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"

    generators = "cmake"

    # Custom attributes for Bincrafters recipe conventions
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"

    def requirements(self):
        self.requires('strawberryperl/5.26.0@conan/stable')
            
    def source(self):
        source_url = "http://download.dre.vanderbilt.edu/previous_versions"
        tools.get("{0}/{1}-src-{2}.tar.gz".format(source_url, self.name, self.version))
        extracted_dir = 'ACE_wrappers'
        os.rename(extracted_dir, self.source_subfolder)

        source_subfolder = os.path.join(os.getcwd(), self.source_subfolder)
        
        # Create config.h
        with open(os.path.join(source_subfolder, 'ace', 'config.h'), 'w') as f:
            if self.settings == "Windows":
                f.write('#include "ace/config-win32.h"\n')
            elif self.settings == "Linux":
                f.write('#include "ace/config-linux.h"\n')
        
        # Generate project
        command = ['perl', os.path.join(source_subfolder, 'bin', 'mwc.pl'),]
        command += ['--type', 'nmake']
        command += [os.path.join(source_subfolder, 'TAO', 'TAO_ACE.mwc'),]
        with tools.environment_append({'MPC_ROOT': os.path.join(source_subfolder, 'MPC'),
                                       'ACE_ROOT': source_subfolder,
                                       'TAO_ROOT': os.path.join(source_subfolder, 'TAO')}):
            r = os.system(' '.join(command))
            if r != 0:
                raise RuntimeError("Error running: {}".format(command))

        
    def build(self):
        cmake = CMake(self, generator="NMake Makefiles")
        cmake.configure()
        cmake.build()


    def package(self):
        self.copy("*.h", dst="include", src="hello")
        self.copy("*hello.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["hello"]
