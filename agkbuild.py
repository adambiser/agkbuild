"""
This module is intended for use on Windows systems.

You must own AppGameKit Classic in order to use it.
AppGameKit Studio does not have an external AGKCompiler.exe.

Notes:
This will scan the project's main.agc file for a constant called VERSION to use as the project's version for exports.

Exporting Android APKs differs from the other export options because it produces a single file rather than a folder.
These are already archives

Release folders use the following naming format: project_name[_version]_platform[_release_name].

Setting USE_DEFINED_PROJECT_OUTPUT_PATHS to True will cause the compiler to use the Android and HTML5 output folders
that are defined in the AGK project file rather than the default release folders.

The export_apk and export_html5 functions are based on code found at:
https://github.com/TheGameCreators/AGKIDE/blob/master/src/project.c
"""
import argparse
from collections import OrderedDict
import glob
from enum import IntEnum, IntFlag, auto
import math
import os
import PIL.Image as Image
import platform
import re
import shutil
from stat import S_IWRITE
import subprocess
import textwrap
# import time
from typing import Iterable, List, Tuple, Union
import zipfile

__version__ = "0.2"

USE_DEFINED_PROJECT_OUTPUT_PATHS = False

# Always ignore these files.
IGNORE_FILES = ['Thumbs.db']


class Platform(IntFlag):
    """List of export platforms this module supports."""
    WINDOWS_86 = auto()  # Export for 32-bit Windows.
    WINDOWS_64 = auto()  # Export for 64-bit Windows.
    WINDOWS_86_64 = auto()  # Exports both 32- and 64-bit Windows in the same release folder.
    LINUX_86 = auto()  # Export for 32-bit Linux.
    LINUX_64 = auto()  # Export for 64-bit Linux.
    LINUX_86_64 = auto()  # Exports both 32- and 64-bit Windows in the same release folder.
    # ANDROID = auto()  # Export as APK using the APK type set within the AGK project file.
    HTML5 = auto()  # Export as HTML5.
    GOOGLE_APK = auto()  # Export as Google Play APK.
    AMAZON_APK = auto()  # Export as Amazon APK.
    OUYA_APK = auto()  # Export as Ouya APK.
    # MACOS = auto()  # Not supported.


class _Architecture(IntFlag):
    """List of architectures for Linux and Windows exports."""
    x86 = auto()  # 32-bit, the default flag if none are set.
    x64 = auto()  # 64-bit

    @classmethod
    def from_platform(cls, p: Platform):
        _PLATFORMS_TO_ARCHITECTURES = {
            Platform.WINDOWS_86: cls.x86,
            Platform.WINDOWS_64: cls.x64,
            Platform.WINDOWS_86_64: cls.x86 | cls.x64,
            Platform.LINUX_86: cls.x86,
            Platform.LINUX_64: cls.x64,
            Platform.LINUX_86_64: cls.x86 | cls.x64,
        }
        return _PLATFORMS_TO_ARCHITECTURES[p]

    def __str__(self):
        return 'x' + '_'.join([a.name[1:] for a in _Architecture if self & a.value])


class Permission(IntFlag):
    AGK_ANDROID_PERMISSION_WRITE = 0x001
    AGK_ANDROID_PERMISSION_INTERNET = 0x002
    AGK_ANDROID_PERMISSION_WAKE = 0x004
    AGK_ANDROID_PERMISSION_GPS = 0x008
    AGK_ANDROID_PERMISSION_IAP = 0x010
    AGK_ANDROID_PERMISSION_EXPANSION = 0x020
    AGK_ANDROID_PERMISSION_LOCATION = 0x040
    AGK_ANDROID_PERMISSION_PUSH = 0x080
    AGK_ANDROID_PERMISSION_CAMERA = 0x100
    AGK_ANDROID_PERMISSION_VIBRATE = 0x200
    AGK_ANDROID_PERMISSION_RECORD_AUDIO = 0x400


class ArCoreMode(IntEnum):
    ARCORE_NONE = 0
    ARCORE_OPTIONAL = 1
    ARCORE_REQUIRED = 2


class Html5Commands(IntEnum):
    HTML5_COMMANDS_2D_ONLY = 0
    HTML5_COMMANDS_2D_AND_3D = 1


class Orientation(IntEnum):
    ORIENTATION_LANDSCAPE = 6
    ORIENTATION_PORTRAIT = 7
    ORIENTATION_ALL = 10


def _rmtree(folder):
    """Ignores the error when the given folder doesn't exist, but raises all other errors."""
    # noinspection PyUnusedLocal func
    def _onerror(func, path, exc_info):
        if exc_info[0] == FileNotFoundError and os.path.abspath(path) == os.path.abspath(folder):
            pass
        elif exc_info[0] == PermissionError and not os.access(path, os.W_OK):
            os.chmod(path, S_IWRITE)
            func(path)
        else:
            raise
    shutil.rmtree(folder, onerror=_onerror)


def _get_script_path():
    try:
        return os.path.dirname(__file__)
    except NameError:
        import sys
        return os.path.dirname(os.path.realpath(sys.argv[0]))


def _get_folder_size(folder_path):
    total_size = 0
    for root, _, filenames in os.walk(folder_path):
        total_size += sum([os.path.getsize(f) for f in [os.path.join(root, f) for f in filenames]
                           if not os.path.islink(f)])
    return total_size


def _is_power_of_2(n):
    return (n & (n - 1) == 0) and n != 0


def _validate_url(homepage):
    if homepage and not re.match(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                                 homepage):
        raise ValueError("The homepage is invalid.")


class IniFile:
    """Reads and provides access to the values within an INI file."""
    def __init__(self, filename):
        """
        Opens and loads the given INI file

        :param filename: The INI file to open
        """
        self._sections = OrderedDict()
        self._filename = filename
        with open(filename, 'r') as fp:
            section = None
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                match = re.match(r'\[(.+)\]', line)
                if match:
                    section = match.group(1)
                    self._sections[section] = OrderedDict()
                    continue
                key, value = line.split('=', 2)
                self._sections[section][key] = value

    # def save(self, filename: str = None):
    #     """
    #     Saves the INI file to the given file name.
    #
    #     :param filename: The file name to save to.  If not given, saves to the original file name.
    #     """
    #     if not filename:
    #         filename = self._filename
    #     temp = f"{filename}.bak"
    #     print(f'Saving project: {filename}')
    #     with open(temp, 'w') as fp:
    #         fp.write('\n')
    #         for section in self._sections.keys():
    #             fp.write(f"[{section}]\n")
    #             for key, value in self._sections[section].items():
    #                 fp.write(f"{key}={value}\n")
    #             fp.write('\n')
    #     os.replace(temp, filename)

    def __getitem__(self, item) -> str:
        section, key = item
        return self._sections[section][key]

    def __setitem__(self, key, value):
        section, key = key
        self._sections[section][key] = value


class AgkProject(IniFile):
    """
    Opens and reads an AppGameKit project file, which is simply an INI file with an extension of "agk".

    NOTE: The ability to save is not included because AppGameKit writes the project file when it closes the project.
    """
    def __init__(self, filename):
        super().__init__(filename)
        print(f"Opening project: {filename}")
        self._base_path = os.path.split(os.path.abspath(filename))[0]
        # Name is the file name without extension
        self._name = os.path.splitext(os.path.basename(filename))[0]
        self._release_name = None
        self._version = None
        with open(os.path.join(self._base_path, 'main.agc'), 'r') as fp:
            for line in fp:
                match = re.match(r'#constant\s+VERSION\s+"(.+)"', line)
                if match:
                    self._version = match.group(1)
                    print(f"Found project version: {self._version}")
                    break

    @property
    def base_path(self):
        """The base path for the project file."""
        return self._base_path

    @property
    def name(self):
        """The name of the project.  Defaults to the project file name without the extension."""
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def safe_name(self):
        # Remove everything but letters, numbers and underscores.
        return re.sub(r'[^A-Za-z0-9_]', '', self.name)

    @property
    def release_name(self):
        """
        The release name.  This is used to differentiate between multiple exports to the same platform.

        Note that this does **not** affect the application name, just the output folder and folder archive.
        """
        return self._release_name

    @release_name.setter
    def release_name(self, value):
        self._release_name = value

    @property
    def version(self) -> str:
        """
        An arbitrary version string.  This is not stored in the project file, but can be defined in main.agc using::

            #constant VERSION	"1.0"
        """
        return self._version

    @version.setter
    def version(self, value: str):
        self._version = value

    def get_release_folder(self, platform_name: str, architectures: _Architecture = None):
        """Returns the release folder for the given platform name."""
        release_folder = f"{self.safe_name}" \
                         f"{f'_{self._version}' if self._version else ''}" \
                         f"_{platform_name}" \
                         f"{f'_{str(architectures)}' if architectures else ''}" \
                         f"{f'_{self._release_name}' if self._release_name else ''}"
        # Remove characters that aren't letters, numbers, or underscores.
        # release_folder = release_folder.replace(' ', '_')
        # release_folder = re.sub(r'[^A-Za-z0-9_]', '', release_folder)
        return os.path.join(self._base_path, "release", release_folder)

    def get_nsis_script_path(self, p: Platform):
        architectures = _Architecture.from_platform(p)
        # Having "-script" seems redundant, but it keeps the script grouped with the installer exe in the release folder
        # when sorted by filename.
        script_file = f"{self.safe_name}" \
                      f"{f'-{self._version}' if self._version else ''}" \
                      f"{f'-{str(architectures)}' if architectures else ''}" \
                      f"{f'-{self._release_name}' if self._release_name else ''}" \
                      f"-script.nsi"
        return os.path.join(self._base_path, "release", script_file)


class AgkCompiler:
    """This class is used to compile and export AppGameKit projects."""
    APK_TYPE_GOOGLE = 0
    APK_TYPE_AMAZON = 1
    APK_TYPE_OUYA = 2

    APK_TYPE_NAMES = ['Google', 'Amazon', 'Ouya']

    ORIENTATION_NAMES = {
        Orientation.ORIENTATION_LANDSCAPE: 'sensorLandscape',
        Orientation.ORIENTATION_PORTRAIT: 'sensorPortrait',
        Orientation.ORIENTATION_ALL: 'fullSensor',
    }

    ANDROID_JAR = 'android28.jar'

    SDK_VERSIONS = [
        None,  # 0
        {'version': '4.1', 'api': 16},
        {'version': '4.2', 'api': 17},
        {'version': '4.3', 'api': 18},
        {'version': '4.4', 'api': 19},
        {'version': '5.0', 'api': 21},
        {'version': '5.1', 'api': 22},
        {'version': '6.0', 'api': 23},
        {'version': '7.0', 'api': 24},
        {'version': '7.1', 'api': 25},
        {'version': '8.0', 'api': 26},
        {'version': '8.1', 'api': 27},
        {'version': '9.0', 'api': 28},
    ]

    HTML5_COMMANDS_FOLDER = {
        Html5Commands.HTML5_COMMANDS_2D_ONLY: {
            True: '2Ddynamic',
            False: '2D',
        },
        Html5Commands.HTML5_COMMANDS_2D_AND_3D: {
            True: '3Ddynamic',
            False: '3D',
        }
    }

    def __init__(self, path: str = None):
        """Sets up information about the AppGameKit compiler."""
        def verify_path(check_path):
            if not os.path.exists(check_path):
                raise SystemError(f'Could not find "{os.path.relpath(check_path, start=path)}".')
            return check_path

        self._agk_path = path if path else AgkCompiler._get_appgamekit_path()
        self._agk_compilier_path = verify_path(os.path.join(self._agk_path, 'Tier 1', 'Compiler', 'AGKCompiler.exe'))
        self._data_dir = verify_path(os.path.join(self._agk_path, 'Tier 1', 'Editor', 'data'))
        self._path_to_aapt2 = verify_path(os.path.join(self._data_dir, 'android', 'aapt2.exe'))
        self._path_to_android_jar = verify_path(os.path.join(self._data_dir, 'android', f'{AgkCompiler.ANDROID_JAR}'))
        self._path_to_jarsigner = verify_path(os.path.join(self._data_dir, 'android', 'jre', 'bin', 'jarsigner.exe'))
        self._path_to_zipalign = verify_path(os.path.join(self._data_dir, 'android', 'zipalign.exe'))

    @classmethod
    def _get_appgamekit_path(cls):
        """Finds the AppGameKit Classic install path."""
        path = None
        if platform.system() == 'Windows':
            # Check IDE config file.
            try:
                config = IniFile(os.path.join(os.getenv('LOCALAPPDATA'), 'agk', 'geany.conf'))
                compiler_path = config['buildAGK', 'compiler_path'].replace('\\\\', '\\')
                match = re.match(r'(.*)\\Tier 1\\Compiler', compiler_path, re.IGNORECASE)
                if match:
                    if os.path.exists(match.group(1)):
                        path = match.group(1)
            except FileNotFoundError:
                pass
            if not path:
                # Check the registry.
                try:
                    import winreg
                    value = winreg.QueryValue(winreg.HKEY_CURRENT_USER,
                                              r'Software\Classes\agk_auto_file\shell\open\command')
                    match = re.match(r'"(.*)\\Tier 1\\Editor\\bin\\agk\.exe"\s+"%1"', value, re.IGNORECASE)
                    if match:
                        path = match.group(1)
                except FileNotFoundError:
                    pass  # ignore
        if not path:
            raise SystemError('Could not determine the path to AppGameKit Classic.')
        return path

    def compile(self, project: AgkProject):
        """Compiles the project.  An error is raised if compilation fails."""
        print(f'Compiling project: {project.name}, version: {project.version}'
              f'{f", release: {project.release_name}" if project.release_name else ""}')
        completed_process = subprocess.run([self._agk_compilier_path, "-agk", "main.agc"],
                                           cwd=project.base_path,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           universal_newlines=True)
        # errors are reported in stdout.
        error = completed_process.stdout.strip()
        if error:
            raise SystemError(f'AppGameKit compilation error:\n{error}')
        if completed_process.returncode != 0:
            raise SystemError(f'AppGameKit compilation error:\nReturn code: {completed_process.returncode}')

    def export_apk(self, project: AgkProject, app_type, **kwargs):  # app_type: int = None, package_name: str = None):
        """
        Exports the project to an Android AGK file.

        :param project: The project to export.
        :param app_type: The APK app type: Google Play, Amazon, or Ouya.
        :param kwargs: Used to override various APK settings.  These args have a 'apk_' prefix.
        :return: Path to the generated APK file.
        """
        def get_value(name):
            return kwargs.get(f'apk_{name}', project['apk_settings', name])

        # app_type = int(get_value('app_type'))
        print(f'Exporting project as {AgkCompiler.APK_TYPE_NAMES[app_type]} APK')
        app_name = get_value('app_name')
        package_name = get_value('package_name')
        app_icon = get_value('app_icon_path')
        notif_icon = get_value('notif_icon_path')
        ouya_icon = get_value('ouya_icon_path')
        firebase_config = get_value('firebase_config_path')
        orientation = kwargs.get('apk_orientation')
        if orientation:
            orientation = Orientation(orientation)
        else:
            orientation = int(project['apk_settings', 'orientation'])
            orientation = [Orientation.ORIENTATION_LANDSCAPE,
                           Orientation.ORIENTATION_PORTRAIT,
                           Orientation.ORIENTATION_ALL][orientation]
        arcore_mode = ArCoreMode(int(get_value('arcore')))
        app_sdk = kwargs.get('apk_sdk_version')
        if app_sdk:
            app_sdk = next((sdk['api'] for sdk in AgkCompiler.SDK_VERSIONS
                            if sdk and sdk['version'] == kwargs.get('apk_sdk_version')), None)
            if not app_sdk:
                raise ValueError("Unexpected SDK version.")
        else:
            app_sdk = AgkCompiler.SDK_VERSIONS[int(project['apk_settings', 'sdk_version'])]['api']
        if not app_sdk:
            raise ValueError("Invalid sdk_version.")
        url_scheme = get_value('url_scheme')
        deep_link = get_value('deep_link')
        google_play_app_id = get_value('play_app_id')
        admob_app_id = get_value('admob_app_id')
        # permissions
        permission_flags = Permission(int(get_value('permission_flags')))
        # signing
        # keystore_path = None
        # version_name = None
        keystore_file = get_value('keystore_path')
        keystore_password = kwargs.get('apk_keystore_password', '')
        version_number = get_value('version_name')
        build_number = int(get_value('version_number'))
        alias_name = get_value('alias')
        alias_password = kwargs.get('apk_alias_password', '')
        if USE_DEFINED_PROJECT_OUTPUT_PATHS:
            output_file = project['apk_settings', 'output_path']
        else:
            output_file = os.path.join(project.get_release_folder(
                    f"android_{AgkCompiler.APK_TYPE_NAMES[app_type].lower()}"),
                    f"{project.name}-%[type]-%[version].apk")

        # permissions
        permission_external_storage = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_WRITE)
        permission_location_fine = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_GPS)
        permission_location_coarse = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_LOCATION)
        permission_internet = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_INTERNET)
        permission_wake = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_WAKE)
        permission_billing = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_IAP)
        permission_push = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_PUSH)
        permission_camera = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_CAMERA)
        permission_expansion = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_EXPANSION)
        permission_vibrate = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_VIBRATE)
        permission_record_audio = bool(permission_flags & Permission.AGK_ANDROID_PERMISSION_RECORD_AUDIO)

        # START CHECKS
        if not output_file:
            raise ValueError('You must choose an output location to save your APK.')
        if "." not in os.path.split(output_file)[1]:
            raise ValueError('The output location must be a file not a directory.')

        # output_file = output_file.replace(r'%[project_name]', str(project.name))  # Not in C++ code.
        output_file = output_file.replace(r'%[version]', str(build_number))
        output_file = output_file.replace(r'%[type]', AgkCompiler.APK_TYPE_NAMES[app_type])
        os.makedirs(os.path.split(output_file)[0], exist_ok=True)
        # check app name
        if not app_name:
            raise ValueError('You must enter an app name.')
        if len(app_name) > 30:
            raise ValueError('App name must be less than 30 characters.')
        if re.search(r'[^-A-Za-z0-9 _]', app_name):
            raise ValueError('App name contains invalid characters, it must not contain quotes or < > characters.')

        # check package name
        if not package_name:
            raise ValueError('You must enter a package name.')
        if len(package_name) > 100:
            raise ValueError('Package name must be less than 100 characters.')
        if '.' not in package_name:
            raise ValueError('Package name must contain at least one dot character.')
        if not package_name[0].isalpha():
            raise ValueError('Package name must begin with a letter.')
        if package_name[-1] == '.':
            raise ValueError('Package name must not end with a dot.')
        if re.search(r'\.[^A-Za-z]', package_name):
            raise ValueError('Package name invalid, a dot must be followed by a letter.')
        if re.search(r'[^A-Za-z0-9._]', package_name):
            raise ValueError('Package name contains invalid characters, must be A-Z 0-9 . and undersore only.')

        if url_scheme and re.search(r'[:/]', url_scheme):
            raise ValueError('URL scheme must not contain : or /')
        if deep_link:
            if not re.match('http[s]://', deep_link):
                raise ValueError('Deep link must start with http:// or https://')
            if not re.match('http[s]://.+', deep_link):
                raise ValueError('Deep link must have a domain after http:// or https://')

        # check icon
        if app_icon:
            if not app_icon.endswith('.png'):
                raise ValueError('App icon must be a PNG file.')
            if not os.path.exists(app_icon):
                raise ValueError('Could not find app icon location.')
        if notif_icon:
            if not notif_icon.endswith('.png'):
                raise ValueError('Notification icon must be a PNG file.')
            if not os.path.exists(notif_icon):
                raise ValueError('Could not find notification icon location.')
        if app_type == AgkCompiler.APK_TYPE_OUYA:
            if not ouya_icon:
                raise ValueError('You must select an Ouya large icon.')
            if not ouya_icon.endswith('.png'):
                raise ValueError('Ouya large icon must be a PNG file.')
            if not os.path.exists(ouya_icon):
                raise ValueError('Could not find Ouya large icon location.')

        # check firebase config file
        if firebase_config:
            if not firebase_config.endswith('.json'):
                raise ValueError('Google services config file must be a .json file.')
            if not os.path.exists(firebase_config):
                raise ValueError('Could not find Google services config file.')

        # check version
        if re.search(r'[^0-9.]', version_number):
            raise ValueError('Version name contains invalid characters, must be 0-9 and . only.')

        # check keystore
        if keystore_file:
            if not os.path.isabs(keystore_file):
                keystore_file = os.path.join(project.base_path, keystore_file)
            if not os.path.exists(keystore_file):
                raise ValueError('Could not find keystore file location.')
            if not keystore_password:
                raise ValueError('You must enter your keystore password when using your own keystore.')
            if '"' in keystore_password:
                raise ValueError('Keystore password cannot contain double quotes.')
        if alias_name:
            if not alias_password:
                raise ValueError('You must enter your alias password when using a custom alias.')
            if '"' in alias_password:
                raise ValueError('Alias password cannot contain double quotes.')

        include_firebase = firebase_config and app_type in [AgkCompiler.APK_TYPE_GOOGLE, AgkCompiler.APK_TYPE_AMAZON]
        include_push_notify = permission_push and app_type == AgkCompiler.APK_TYPE_GOOGLE
        include_google_play = google_play_app_id and app_type == AgkCompiler.APK_TYPE_GOOGLE
        include_admob = admob_app_id and app_type == AgkCompiler.APK_TYPE_GOOGLE

        if include_push_notify and not include_firebase:
            raise ValueError('Push Notifications on Android now use Firebase, so you must include a '
                             'Firebase config file to use them.')

        # CHECKS COMPLETE, START EXPORT
        # make temporary folder
        android_folder = os.path.join(self._data_dir, "android")
        temp_folder = os.path.join(project.base_path, "build_tmp")
        src_folder = [os.path.join(self._data_dir, "android", f'{folder}')
                      for folder in ["sourceGoogle", "sourceAmazon", "sourceOuya"]][app_type]
        output_file_zip = f'{os.path.splitext(output_file)[0]}.zip'

        if not keystore_file:
            keystore_file = os.path.join(self._data_dir, "android", "debug.keystore")
            keystore_password = "android"
            alias_name = "androiddebugkey"
            alias_password = "android"
        else:
            if not alias_name:
                alias_name = "mykeystore"
                alias_password = keystore_password
        if platform.system() == 'Windows':
            keystore_file = keystore_file.replace('/', '\\')

        try:
            _rmtree(temp_folder)
            shutil.copytree(src_folder, temp_folder)

            # edit AndroidManifest.xml
            manifest_file = os.path.join(temp_folder, "AndroidManifest.xml")
            with open(manifest_file, 'r') as fp:
                contents = ''.join(fp.readlines())
            new_contents = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
      android:versionCode="{str(build_number)}"
      android:versionName="{version_number}" package="{package_name}" android:installLocation="auto">
    <uses-feature android:glEsVersion="0x00020000"></uses-feature>
    <uses-sdk android:minSdkVersion="{app_sdk if app_type in [AgkCompiler.APK_TYPE_GOOGLE,
                                                              AgkCompiler.APK_TYPE_AMAZON] else 15}\
" android:targetSdkVersion="{28 if app_type == AgkCompiler.APK_TYPE_GOOGLE else 15}" />
    
'''
            if permission_external_storage:
                new_contents += '    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />'
            if permission_internet:
                new_contents += '''
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
'''
            if permission_wake:
                new_contents += '    <uses-permission android:name="android.permission.WAKE_LOCK" />\n'
            if permission_location_coarse and app_type == AgkCompiler.APK_TYPE_GOOGLE:
                new_contents += '    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />\n'
            if permission_location_fine and app_type == AgkCompiler.APK_TYPE_GOOGLE:
                new_contents += '    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />\n'
            if permission_billing and app_type == AgkCompiler.APK_TYPE_GOOGLE:  # OUYA?
                new_contents += '    <uses-permission android:name="android.permission.BILLING" />\n'
            if permission_camera:
                new_contents += '    <uses-permission android:name="android.permission.CAMERA" />\n'
            if (google_play_app_id or permission_push) and app_type == AgkCompiler.APK_TYPE_GOOGLE:
                new_contents += '    <uses-permission android:name="com.google.android.c2dm.permission.RECEIVE" />\n'
            if permission_push and app_type == AgkCompiler.APK_TYPE_GOOGLE:
                new_contents += f'    <permission android:name="{package_name}.permission.C2D_MESSAGE"' \
                                f'        android:protectionLevel="signature" />\n' \
                                f'    <uses-permission android:name="{package_name}.permission.C2D_MESSAGE" />\n'
            if permission_expansion and app_type == AgkCompiler.APK_TYPE_GOOGLE:
                # new_contents += '    <uses-permission android:name="android.permission.GET_ACCOUNTS" />\n'
                new_contents += '    <uses-permission android:name="android.permission.CHECK_LICENSE" />\n'
            if permission_vibrate:
                new_contents += '    <uses-permission android:name="android.permission.VIBRATE" />\n'
            if permission_record_audio:
                new_contents += '    <uses-permission android:name="android.permission.RECORD_AUDIO" />\n'

            # if ARCore required
            if arcore_mode == ArCoreMode.ARCORE_REQUIRED:
                new_contents += '    <uses-feature android:name="android.hardware.camera.ar" android:required="true" />'

            # replace orientation
            contents = re.sub(r'screenOrientation="fullSensor"',
                              f'screenOrientation="{AgkCompiler.ORIENTATION_NAMES[orientation]}"', contents)

            # add intent filters
            filters = ''
            if url_scheme:
                filters += f'''
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="{url_scheme}" />
    </intent-filter>'''
            if deep_link:
                scheme = None
                host = None
                path = None
                match = re.match(r'(.+)://([^/]+)(/.+)?', deep_link)
                if match:
                    scheme = match.group(1)
                    host = match.group(2)
                    path = match.group(3)
                if scheme:
                    filters += f'''
        <intent-filter>
            <action android:name="android.intent.action.VIEW" />
            <category android:name="android.intent.category.DEFAULT" />
            <category android:name="android.intent.category.BROWSABLE" />
            <data android:scheme="{scheme}"'''
                if host:
                    filters += ' android:host="{host}"'
                    if path:
                        filters += ' android:pathPrefix="{path}"'
                filters += ''' />
        </intent-filter>'''

            contents = re.sub(r'<!--ADDITIONAL_INTENT_FILTERS-->', filters, contents)
            contents = re.sub(r'YOUR_PACKAGE_NAME_HERE', package_name, contents)
            contents = re.sub(r'\${applicationId}', package_name, contents)

            # write the rest of the manifest file
            new_contents += contents
            if permission_expansion and app_type == AgkCompiler.APK_TYPE_GOOGLE:
                new_contents += '''
        <service android:name="com.google.android.vending.expansion.downloader.impl.DownloaderService"
            android:enabled="true"/>
        <receiver android:name="com.google.android.vending.expansion.downloader.impl.DownloaderService$AlarmReceiver"
            android:enabled="true"/>'''

            # Google sign in
            if app_type == AgkCompiler.APK_TYPE_GOOGLE:
                new_contents += '''
        <activity android:name="com.google.android.gms.auth.api.signin.internal.SignInHubActivity"
            android:excludeFromRecents="true"
            android:exported="false"
            android:theme="@android:style/Theme.Translucent.NoTitleBar" />
        <service android:name="com.google.android.gms.auth.api.signin.RevocationBoundService"
            android:exported="true"
            android:permission="com.google.android.gms.auth.api.signin.permission.REVOCATION_NOTIFICATION" />
    '''

            # IAP Purchase Activity
            if permission_billing and app_type == AgkCompiler.APK_TYPE_GOOGLE:
                new_contents += '''
        <activity android:name="com.google.android.gms.ads.purchase.InAppPurchaseActivity"
            android:theme="@style/Theme.IAPTheme" />'''

            # Google API Activity - for Game Services
            if include_google_play:
                new_contents += '''
        <activity android:name="com.google.android.gms.common.api.GoogleApiActivity"
            android:exported="false"
            android:theme="@android:style/Theme.Translucent.NoTitleBar" />'''

            # Firebase Init Provider - for Game Services and Firebase
            if include_google_play or include_firebase or include_push_notify:
                new_contents += f'''
    <provider android:authorities="{package_name}.firebaseinitprovider"
        android:name="com.google.firebase.provider.FirebaseInitProvider"
        android:exported="false"
        android:initOrder="100" />'''

            # Firebase activities
            if include_firebase:
                new_contents += '''
        <receiver
            android:name="com.google.android.gms.measurement.AppMeasurementReceiver"
            android:enabled="true"
            android:exported="false" >
        </receiver>
        
        <service android:name="com.google.android.gms.measurement.AppMeasurementService"
            android:enabled="true"
            android:exported="false"/>
        <service
            android:name="com.google.android.gms.measurement.AppMeasurementJobService"
            android:enabled="true"
            android:exported="false"
            android:permission="android.permission.BIND_JOB_SERVICE" />
        <service
            android:name="com.google.firebase.components.ComponentDiscoveryService"
            android:exported="false" >
            <meta-data
                android:name="com.google.firebase.components:com.google.firebase.analytics.connector.internal.AnalyticsConnectorRegistrar"
                android:value="com.google.firebase.components.ComponentRegistrar" />
            <meta-data
                android:name="com.google.firebase.components:com.google.firebase.iid.Registrar"
                android:value="com.google.firebase.components.ComponentRegistrar" />
        </service>'''

            if include_firebase or include_push_notify:
                new_contents += '''
        <receiver android:name="com.google.firebase.iid.FirebaseInstanceIdReceiver"
            android:exported="true"
            android:permission="com.google.android.c2dm.permission.SEND" >
            <intent-filter>
                <action android:name="com.google.android.c2dm.intent.RECEIVE" />
            </intent-filter>
        </receiver>'''

            if include_push_notify:
                new_contents += '''
        <meta-data android:name="com.google.firebase.messaging.default_notification_icon"
            android:resource="@drawable/icon_white" />
        <service android:name="com.google.firebase.messaging.FirebaseMessagingService" 
            android:exported="true" > 
            <intent-filter android:priority="-500" > 
                <action android:name="com.google.firebase.MESSAGING_EVENT" /> 
            </intent-filter> 
        </service>'''

            if include_admob:
                new_contents += f'''
        <provider
            android:name="com.google.android.gms.ads.MobileAdsInitProvider"
                android:authorities="{package_name}.mobileadsinitprovider"
                android:exported="false"
                android:initOrder="100" />'''

            # arcore activity
            if arcore_mode != ArCoreMode.ARCORE_NONE:
                new_contents += f'''
        <meta-data android:name="com.google.ar.core" android:value="{
            'optional' if arcore_mode == ArCoreMode.ARCORE_OPTIONAL else 'required'}" />
        <meta-data android:name="com.google.ar.core.min_apk_version" android:value="190519000" />
        <activity
            android:name="com.google.ar.core.InstallActivity"
            android:configChanges="keyboardHidden|orientation|screenSize"
            android:excludeFromRecents="true"
            android:exported="false"
            android:launchMode="singleTop"
            android:theme="@android:style/Theme.Material.Light.Dialog.Alert" />'''

            new_contents += '''
        </application>
    </manifest>
    '''
            # write new Android Manifest.xml file
            with open(manifest_file, 'w') as fp:
                fp.write(new_contents)

            # read resources file
            resources_file = os.path.join(temp_folder, "resOrig", "values", "values.xml")
            with open(resources_file, 'r') as fp:
                contents = '\n'.join(fp.readlines())

            contents, count = re.subn(r'(<string name="app_name">)[^<]+(</string>)', rf'\1{app_name}\2', contents)
            if not count:
                raise ValueError('Could not find app_name entry in values.xml file.')

            if app_type == AgkCompiler.APK_TYPE_GOOGLE and google_play_app_id:
                contents, count = re.subn(r'(<string name="games_app_id">)[^<]+(</string>)',
                                          rf'\1{google_play_app_id}\2', contents)
                if not count:
                    raise ValueError('Could not find games_app_id entry in values.xml file.')

            # admob app id
            if app_type == AgkCompiler.APK_TYPE_GOOGLE and admob_app_id:
                contents, count = re.subn(r'(<string name="admob_app_id">)[^<]+(</string>)',
                                          rf'\1{admob_app_id}\2', contents)
                if not count:
                    raise ValueError('Could not find admob_app_id entry in values.xml file.')

            # firebase
            if firebase_config and app_type in [AgkCompiler.APK_TYPE_GOOGLE, AgkCompiler.APK_TYPE_AMAZON]:
                # read json values
                with open(firebase_config, 'r') as fp:
                    # contents_other = '\n'.join(fp.readlines())
                    import json
                    config = json.load(fp)

                # find project_number value
                try:
                    project_number = config['project_info']['project_number']
                except KeyError:
                    raise KeyError('Could not find project_number entry in Firebase config file.')
                contents, count = re.subn(r'(<string name="gcm_defaultSenderId" translatable="false">)[^<]+(</string>)',
                                          rf'\1{project_number}\2', contents)
                if not count:
                    raise ValueError('Could not find gcm_defaultSenderId entry in values.xml file.')

                # find firebase_url value
                try:
                    firebase_url = config['project_info']['firebase_url']
                except KeyError:
                    raise KeyError('Could not find firebase_url entry in Firebase config file.')
                contents, count = re.subn(r'(<string name="firebase_database_url" translatable="false">)[^<]+'
                                          r'(</string>)',
                                          rf'\1{firebase_url}\2', contents)
                if not count:
                    raise ValueError('Could not find firebase_database_url entry in values.xml file.')

                # find mobilesdk_app_id value
                # if the config file contains multiple Android apps then there will be multiple mobilesdk_app_id's,
                # and only the corect one will work
                # look for the corresponding package_name that matches this export
                client = next([client for client in config['client']
                               if client['client_info']['android_client_info']['package_name'] == package_name], None)
                if not client:
                    raise ValueError(f'Could not find client entry for android package_name "{package_name}"'
                                     f' in the Firebase config file.')
                try:
                    mobilesdk_app_id = client['client_info']['mobilesdk_app_id']
                except KeyError:
                    raise KeyError(f'Could not find mobilesdk_app_id entry for android package_name "{package_name}"'
                                   f'in the Firebase config file.')
                contents, count = re.subn(r'(<string name="google_app_id" translatable="false">)[^<]+(</string>)',
                                          rf'\1{mobilesdk_app_id}\2', contents)
                if not count:
                    raise ValueError('Could not find google_app_id entry in values.xml file.')

                try:
                    current_key = client['api_key']['current_key']
                except KeyError:
                    raise KeyError(f'Could not find current_key entry for android package_name "{package_name}"'
                                   f'in the Firebase config file.')
                contents, count = re.subn(r'(<string name="google_api_key" translatable="false">)[^<]+(</string>)',
                                          rf'\1{current_key}\2', contents)
                if not count:
                    raise ValueError('Could not find google_app_id entry in values.xml file.')
                # also copy it to google_crash_reporting_api_key
                contents, count = re.subn(r'(<string name="google_crash_reporting_api_key" translatable="false">)[^<]+'
                                          r'(</string>)',
                                          rf'\1{current_key}\2', contents)
                if not count:
                    raise ValueError('Could not find google_app_id entry in values.xml file.')

            with open(resources_file, 'w') as fp:
                fp.write(contents)

            # Wrapper for aapt2 to run all commands at once and check for errors.
            class Aapt2:
                def __init__(self, aapt2_path, cwd):
                    self._aapt2_path = aapt2_path.replace('\\', '/')
                    self._cwd = cwd
                    self._lines = []

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_val, exc_tb):
                    self.run()
                    # This method doesn't handle exceptions.  Report to the caller.
                    return False

                def write(self, s, convert_slashes=True):
                    if platform.system() == 'Windows' and convert_slashes:
                        s = s.replace('/', '\\')
                    self._lines.append(s)

                def run(self):
                    if not self._lines:
                        raise ValueError('Packaging tool has no commands to run.')
                    _completed_process = subprocess.run([self._aapt2_path, 'm'], cwd=self._cwd,
                                                        input=''.join(self._lines),
                                                        stdout=subprocess.PIPE,
                                                        stderr=subprocess.PIPE,
                                                        universal_newlines=True)
                    self._lines = []
                    stderr_lines = _completed_process.stderr.strip().split('\n')
                    _error = '\n'.join([e for e in stderr_lines if e not in ['Error', 'Done']])
                    if _error:
                        raise SystemError(f'Packaging tool reported the following error(s):\n{_error}')
                    if 'Error' in stderr_lines:
                        raise SystemError('Packaging tool had an unspecified error.')

            with Aapt2(aapt2_path=self._path_to_aapt2, cwd=temp_folder) as aapt2:
                # compile values.xml file
                aapt2.write("compile\n-o\nresMerged\nresOrig/values/values.xml\n\n")

                def scale_and_compile_image(image, size, folder, filename):
                    # If size is an int, make it square.
                    if isinstance(size, int):
                        size = (size, size)
                    scaled_image = image.resize(size, Image.LANCZOS)
                    scaled_image.save(os.path.join(temp_folder, "resOrig", folder, filename), 'PNG')
                    aapt2.write(f"compile\n-o\nresMerged\nresOrig/{folder}/{filename}\n\n")

                # load icon file
                if app_icon:
                    icon_image = Image.open(app_icon)
                    # scale it and save it
                    if app_type in [AgkCompiler.APK_TYPE_GOOGLE, AgkCompiler.APK_TYPE_AMAZON]:
                        # 192x192
                        scale_and_compile_image(icon_image, 192, "drawable-xxxhdpi", "icon.png")
                        # 144x144
                        scale_and_compile_image(icon_image, 144, "drawable-xxhdpi", "icon.png")

                    drawable_xhdpi = "drawable-xhdpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-xhdpi"
                    drawable_hdpi = "drawable-hdpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-hdpi"
                    drawable_mdpi = "drawable-mdpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-mdpi"
                    drawable_ldpi = "drawable-ldpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-ldpi"

                    main_icon = "app_icon.png" if app_type == AgkCompiler.APK_TYPE_OUYA else "icon.png"

                    # 96x96
                    scale_and_compile_image(icon_image, 96, drawable_xhdpi, main_icon)
                    # 72x72
                    scale_and_compile_image(icon_image, 72, drawable_hdpi, main_icon)
                    # 48x48
                    scale_and_compile_image(icon_image, 48, drawable_mdpi, main_icon)
                    # 36x36
                    scale_and_compile_image(icon_image, 36, drawable_ldpi, main_icon)

                # load notification icon file
                if notif_icon and app_type in [AgkCompiler.APK_TYPE_GOOGLE, AgkCompiler.APK_TYPE_AMAZON]:
                    icon_image = Image.open(notif_icon)
                    # scale it and save it
                    # 96x96
                    scale_and_compile_image(icon_image, 96, "drawable-xxxhdpi", "icon_white.png")
                    # 72x72
                    scale_and_compile_image(icon_image, 72, "drawable-xxhdpi", "icon_white.png")

                    drawable_xhdpi = "drawable-xhdpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-xhdpi"
                    drawable_hdpi = "drawable-hdpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-hdpi"
                    drawable_mdpi = "drawable-mdpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-mdpi"
                    drawable_ldpi = "drawable-ldpi-v4" if app_type == AgkCompiler.APK_TYPE_OUYA else "drawable-ldpi"

                    # 48x48
                    scale_and_compile_image(icon_image, 48, drawable_xhdpi, "icon_white.png")
                    # 36x36
                    scale_and_compile_image(icon_image, 36, drawable_hdpi, "icon_white.png")
                    # 24x24
                    scale_and_compile_image(icon_image, 24, drawable_mdpi, "icon_white.png")
                    # 24x24
                    scale_and_compile_image(icon_image, 24, drawable_ldpi, "icon_white.png")

                # load ouya icon and check size
                if app_type == AgkCompiler.APK_TYPE_OUYA:
                    icon_image = Image.open(ouya_icon)
                    if icon_image.width != 732 or icon_image.height != 412:
                        raise ValueError('Ouya large icon must be 732x412 pixels.')
                    # copy it to the res folder
                    shutil.copyfile(ouya_icon, os.path.join(temp_folder, "resOrig", "drawable-xhdpi-v4",
                                                            "ouya_icon.png"))
                    aapt2.write("compile\n-o\nresMerged\nresOrig/drawable-xhdpi-v4/ouya_icon.png\n\n")

                    # 320x180
                    scale_and_compile_image(icon_image, (320, 180), 'drawable', "icon.png")

                aapt2.write(f"l\n-I\n{self._path_to_android_jar}\n"
                            f"--manifest\n{temp_folder}/AndroidManifest.xml\n" 
                            f"-o\n{output_file}\n"
                            f"--auto-add-overlay\n"
                            f"--no-version-vectors\n", False)

                merged_path = os.path.join(temp_folder, "resMerged")
                for root, _, files in os.walk(merged_path):
                    for file in files:
                        fullsrcpath = os.path.join(root, file)
                        aapt2.write(f"-R\n{fullsrcpath}\n", False)

                aapt2.write('\nquit\n\n')

            # if we have previously called g_spawn_async then g_spawn_sync will never return the correct exit status
            # due toECHILD being returned from waitpid()
            # check the file was created instead
            if not os.path.exists(output_file):
                raise SystemError('Failed to write output files, check that your project directory is not in a write '
                                  'protected location.')
            os.replace(output_file, output_file_zip)

            # open APK as a zip file
            with zipfile.ZipFile(output_file_zip, 'a', compression=zipfile.ZIP_DEFLATED) as zfp:
                zfp.write(os.path.join(src_folder, "classes.dex"), "classes.dex")
                zfp.write(os.path.join(android_folder, "lib", "arm64-v8a", "libandroid_player.so"),
                          "lib/arm64-v8a/libandroid_player.so")
                zfp.write(os.path.join(android_folder, "lib", "armeabi-v7a", "libandroid_player.so"),
                          "lib/armeabi-v7a/libandroid_player.so")
                zfp.write(os.path.join(android_folder, "lib", "x86", "libandroid_player.so"),
                          "lib/x86/libandroid_player.so")

                if arcore_mode != ArCoreMode.ARCORE_NONE:
                    # use real ARCore lib
                    zfp.write(os.path.join(android_folder, "lib", "arm64-v8a", "libarcore_sdk.so"),
                              "lib/arm64-v8a/libarcore_sdk.so")
                    zfp.write(os.path.join(android_folder, "lib", "armeabi-v7a", "libarcore_sdk.so"),
                              "lib/armeabi-v7a/libarcore_sdk.so")
                    zfp.write(os.path.join(android_folder, "lib", "x86", "libarcore_sdk.so"),
                              "lib/x86/libarcore_sdk.so")

                if app_type != AgkCompiler.APK_TYPE_OUYA:
                    # copy assets for Google and Amazon
                    assets_folder = os.path.join(android_folder, "assets")
                    for root, _, files in os.walk(assets_folder):
                        for file in files:
                            filepath = os.path.join(root, file)
                            zfp.write(filepath, f'assets/{os.path.relpath(filepath, assets_folder)}')

                # copy in media files
                media_folder = os.path.join(project.base_path, "media")
                for root, _, files in os.walk(media_folder):
                    for file in files:
                        if file in IGNORE_FILES:
                            continue
                        filepath = os.path.join(root, file)
                        zfp.write(filepath, f'assets/media/{os.path.relpath(filepath, media_folder)}')

            completed_process = subprocess.run([self._path_to_jarsigner,
                                                "-sigalg", "MD5withRSA",
                                                "-digestalg", "SHA1",
                                                "-storepass", keystore_password,
                                                "-keystore", keystore_file,
                                                output_file_zip, alias_name,
                                                "-keypass", alias_password],
                                               cwd=temp_folder,
                                               stdout=subprocess.PIPE,
                                               universal_newlines=True)
            # jarsigner reports errors in stdout.
            errors = completed_process.stdout.strip()
            if errors:
                raise SystemError(f'Failed to sign APK, is your keystore password and alias correct?\n{errors}')

            # align apk
            completed_process = subprocess.run([self._path_to_zipalign, "4", output_file_zip, output_file],
                                               cwd=temp_folder,
                                               stdout=subprocess.PIPE,
                                               universal_newlines=True)
            # zipalign reports errors in stdout.
            error = completed_process.stdout.strip()
            if error:
                raise SystemError(f'Zip align tool returned error: {error}')
        finally:
            if os.path.exists(output_file_zip):
                os.remove(output_file_zip)
            _rmtree(temp_folder)
        return output_file

    def export_html5(self, project: AgkProject, **kwargs):
        """
        Exports the project as html5.

        :param project: The project to export.
        :return: The path to the export folder.
        """
        def get_value(name):
            return kwargs.get(f'html5_{name}', project['html5_settings', name])

        print('Exporting project as HTML5')
        commands_used = Html5Commands(int(get_value('commands_used')))
        dynamic_memory = bool(get_value('dynamic_memory'))
        if USE_DEFINED_PROJECT_OUTPUT_PATHS:
            output_folder = project['html5_settings', 'output_path']  # Called output_file in the C++ code.
        else:
            output_folder = project.get_release_folder("html5")

        # START CHECKS
        if not output_folder:
            raise ValueError('You must choose an output location to save your HTML5 files.')
        if commands_used not in [Html5Commands.HTML5_COMMANDS_2D_ONLY, Html5Commands.HTML5_COMMANDS_2D_AND_3D]:
            raise ValueError("Unrecognised choice for 'commands used'.")

        # CHECKS COMPLETE, START EXPORT
        # make temporary folder
        temp_folder = os.path.join(project.base_path, "build_tmp")
        commands_folder = AgkCompiler.HTML5_COMMANDS_FOLDER[commands_used][dynamic_memory]

        src_folder = os.path.join(self._data_dir, "html5", commands_folder)

        try:
            _rmtree(temp_folder)
            shutil.copytree(src_folder, temp_folder)

            # create HTML5 data file that we'll add all the media files to
            html5data_file = os.path.join(temp_folder, "AGKPlayer.data")
            with open(html5data_file, 'wb') as fp:
                # start the load package string that will store the list of files,
                # it will be built at the same time as adding the media files
                load_package_string = 'loadPackage({"files":['
                additional_folders_string = 'Module["FS_createPath"]("/", "media", true, true);'
                media_folder = os.path.join(project.base_path, 'media')
                currpos = 0
                if os.path.exists(media_folder):
                    # add media folder to html5 data file
                    srcfull = media_folder
                    src = '/media'

                    if not os.path.exists(srcfull):
                        raise SystemError(f"Location '{srcfull}' not found.")
                    if not os.path.isdir(srcfull):
                        raise SystemError(f"Location '{srcfull}' is not a directory.")

                    dirnames, filenames = [], []
                    for root, dirs, files in os.walk(srcfull):
                        dirnames.extend([os.path.join(root, dirname) for dirname in dirs])
                        filenames.extend([os.path.join(root, filename) for filename in files
                                          if filename not in IGNORE_FILES])

                    for filepath in dirnames:
                        filename = os.path.split(filepath)[1]
                        # NOTE: os.path.relpath(root, srcfull) will leave a trailing /.
                        shortfilepath = os.path.join(src, os.path.relpath(filepath, srcfull)).replace('\\', '/')
                        # The parent folder is wanted.
                        shortfilepath = os.path.split(shortfilepath)[0]
                        additional_folders_string += f'Module["FS_createPath"]' \
                                                     f'("{shortfilepath}", "{filename}", true, true);'

                    for filepath in filenames:
                        filename = os.path.split(filepath)[1]
                        shortfilepath = os.path.join(src, os.path.relpath(filepath, srcfull)).replace('\\', '/')
                        with open(filepath, 'rb') as tfp:
                            contents = tfp.read()
                            length = len(contents)
                            fp.write(contents)
                        audio = os.path.splitext(filename)[1] in [".mp3", ".m4a", ".wav", ".ogg"]
                        load_package_string += f'{{"audio":{1 if audio else 0},' \
                                               f'"start":{currpos},' \
                                               f'"crunched":0,' \
                                               f'"end":{currpos + length},' \
                                               f'"filename":"{shortfilepath}"}},'
                        currpos += length

                # remove the final comma that was added
                if load_package_string.endswith(','):
                    load_package_string = load_package_string[0:-1]
                load_package_string += f'],"remote_package_size":{currpos},' \
                                       f'"package_uuid":"e3c8dd30-b68a-4332-8c93-d0cf8f9d28a0"}})'

            # edit AGKplayer.js to add our load package string
            agkplayer_file = os.path.join(temp_folder, "AGKPlayer.js")
            with open(agkplayer_file, 'r') as fp:
                contents = ''.join(fp.readlines())
            # replace variables
            for find, replace in [(r'%%ADDITIONALFOLDERS%%', additional_folders_string),
                                  (r'%%LOADPACKAGE%%', load_package_string)]:
                contents, count = re.subn(find, replace, contents)
                if not count:
                    raise ValueError(f"AGKPlayer.js is corrupt, it is missing the {find} variable.")
            # write new AGKPlayer.js file
            with open(agkplayer_file, 'w') as fp:
                fp.writelines(contents)

            _rmtree(output_folder)
            os.makedirs(output_folder)

            # copy files to folder
            for filename in ["AGKPlayer.asm.js",
                             "AGKPlayer.js",
                             "AGKPlayer.data",
                             "AGKPlayer.html.mem",
                             "background.jpg",
                             "made-with-appgamekit.png"]:
                shutil.copyfile(os.path.join(temp_folder, filename), os.path.join(output_folder, filename))

            # create main html5 file with project name so it stands out as the file to run
            html5data_file = f'{project.name.replace(" ", "_")}.html'
            shutil.copyfile(os.path.join(temp_folder, "AGKPlayer.html"), os.path.join(output_folder, html5data_file))
        finally:
            _rmtree(temp_folder)
        return output_folder

    def export_linux(self, project: AgkProject, architectures: _Architecture):
        """
        Exports the project for Linux.

        :param project: The project to export.
        :param architectures: The OS architectures to export for.
        :return: The path to the export folder.
        """
        print(f'Exporting project for Linux: {str(architectures)}')
        output_folder = project.get_release_folder("linux", architectures)
        _rmtree(output_folder)
        os.makedirs(output_folder)
        player_path = os.path.join(self._agk_path, "Players", "Linux")
        if architectures & _Architecture.x86:
            shutil.copyfile(os.path.join(player_path, "LinuxPlayer32"), os.path.join(output_folder,
                                                                                     f"{project.safe_name}32"))
        if architectures & _Architecture.x64:
            shutil.copyfile(os.path.join(player_path, "LinuxPlayer64"), os.path.join(output_folder,
                                                                                     f"{project.safe_name}64"))
        icon_path = os.path.join(project.base_path, "icon.ico")
        if os.path.exists(icon_path):
            shutil.copyfile(icon_path, os.path.join(output_folder, "icon.ico"))
        shutil.copytree(os.path.join(project.base_path, "media"), os.path.join(output_folder, "media"),
                        ignore=shutil.ignore_patterns(*IGNORE_FILES))
        if os.listdir('Plugins'):
            shutil.copytree(os.path.join(project.base_path, "Plugins"), os.path.join(output_folder, "Plugins"),
                            ignore=shutil.ignore_patterns(*IGNORE_FILES, '*.dll', '*.dylib'))
        return output_folder

    def export_windows(self, project: AgkProject, architectures: _Architecture):
        """
        Exports the project for Windows.

        :param project: The project to export.
        :param architectures: The OS architectures to export for.
        :return: The path to the export folder.
        """
        print(f'Exporting project for Windows: {str(architectures)}')
        output_folder = project.get_release_folder('windows', architectures)
        _rmtree(output_folder)
        os.makedirs(output_folder, exist_ok=False)
        player_path = os.path.join(self._agk_path, "Players", "Windows")
        # Remove everything but letters, numbers and underscores.
        if architectures & _Architecture.x86:
            shutil.copyfile(os.path.join(player_path, "Windows.exe"),
                            os.path.join(output_folder, f"{project.name}.exe"))
        if architectures & _Architecture.x64:
            # Appends 64 if exporting both 32- and 64-bit.
            shutil.copyfile(os.path.join(player_path, "Windows64.exe"),
                            os.path.join(output_folder,
                                         f"{project.name}{'64' if architectures & _Architecture.x86 else ''}.exe"))
        icon_path = os.path.join(project.base_path, "icon.ico")
        if os.path.exists(icon_path):
            shutil.copyfile(icon_path, os.path.join(output_folder, "icon.ico"))
        shutil.copytree(os.path.join(project.base_path, "media"), os.path.join(output_folder, "media"),
                        ignore=shutil.ignore_patterns(*IGNORE_FILES))
        if os.listdir('Plugins'):
            ignore_dlls = []
            if not architectures & _Architecture.x86:
                ignore_dlls.append('Windows.dll')
            if not architectures & _Architecture.x64:
                ignore_dlls.append('Windows64.dll')
            shutil.copytree(os.path.join(project.base_path, "Plugins"), os.path.join(output_folder, "Plugins"),
                            ignore=shutil.ignore_patterns(*IGNORE_FILES, '*.so', '*.dylib', *ignore_dlls))
        return output_folder


class AgkBuild:
    def __init__(self,
                 project_file: str,
                 platforms: int,
                 project_name: str = None,
                 release_name: str = None,
                 constants: dict = None,
                 include_tags: dict = None,
                 include_files: List[Tuple[str, str]] = None,
                 exclude_media: List[str] = None,
                 **kwargs):
        """
        Creating an instance of this class compiles a project for the specified platforms.

        **Include tags**

        Include tags allow a build to include or insert a file that is specific to the release being built.
        For example: a file for special demo code, or one for Steam releases.

        To set up an include tag, add an #insert or #include in main.agc and give it a tag using @@.
        For example, to set up an include tag called "demo"::
            #insert "version-demo.agc" // @@demo Anything after the tag is ignored.

        When include tags are used in the code, include_tags **must** include an **item** for each tag.

        :param project_file: The AGK project file to open.
        :param platforms: Platform flags indicating how to export the project.
        :param architectures: The architectures to export for.  Only used for Linux and Windows exports.
        :param project_name: Overrides the name found in the project file.  Useful for special version, ie: demos.
        :param release_name: When given, this is included in the release output folder and can be used to differentiate
            between multiple exports to the same platform.  It does not affect the project name.
        :param constants: A dictionary of constant values for the script to set in main.agc.
        :param include_tags: The dictionary of include tags and include files.
        :param include_files: List of extra files to include in the release folders.
            This is a list of tuples where each tuple has two values, the first value is the path to the file on the
            system now (relative to the project folder) and the second value is the folder name for the file within the
            release folder.
            This parameter has no affect on Android exports.
        :param exclude_media: List of file paths relative to the 'media' folder to be excluded when building.  The files
            are moved into 'media_exclude' while building and exported and moved back into 'media' when finished.
        :param archive_output: When true, exported output folders are archived into zip files.
            This parameter has no affect on Android exports.
        :param apk_package_name: Overrides the project's APK package name.
        :param apk_keystore_file: Overrides the project's keystore file for Android packages.
        :param apk_keystore_password: Sets the keystore password for exporting Android packages.
        :param kwargs: Used to set or override APK and HTML5 export settings.
        :return:
        """
        if not platforms or not isinstance(platforms, Platform):
            raise ValueError('The "platforms" value must be a value of the Platform flags.')
        if exclude_media and not isinstance(exclude_media, (list, set)):
            raise ValueError('The "exclude_media" value must be a list or set of file names.')

        self.release_paths = {}

        print("")  # blank line for cleaner sysout.
        project = AgkProject(project_file)
        self.project = project
        self.version = project.version
        main_code_file = os.path.join(project.base_path, "main.agc")
        backup_code_file = os.path.join(project.base_path, "main.agc.backup")
        os.rename(main_code_file, backup_code_file)
        try:
            # Replace include tags.
            with open(backup_code_file, 'r') as rfp:
                with open(main_code_file, 'w') as wfp:
                    for line in rfp:
                        match = re.match(r'(#include|#insert)\s*(?:".+"|\'.+\')\s*//\s*@@(\w+)', line)
                        if match:
                            include_type = match.group(1)
                            name = match.group(2)
                            if not include_tags:
                                raise ValueError("The project's main.agc file contains include tags, "
                                                 "but none were given.")
                            if name not in include_tags:
                                raise ValueError(f"No value given for include tag named '{name}'.")
                            line = f'{include_type} "{include_tags[name]}"\n'
                        elif constants:
                            match = re.match(r'#constant\s+(\w+)', line)
                            if match:
                                name = match.group(1)
                                if name in constants:
                                    line = f'#constant {name} {constants[name]}\n'
                        wfp.write(line)

            # Store the exclude media files in the media_exclude folder.
            if exclude_media:
                media_exclude_path = os.path.join(project.base_path, 'media_exclude')
                os.makedirs(media_exclude_path, exist_ok=False)  # Do not overwrite!
                for filename in exclude_media:
                    src_file = os.path.join(project.base_path, 'media', filename)
                    dst_file = os.path.join(media_exclude_path, filename)
                    os.makedirs(os.path.split(dst_file)[0], exist_ok=True)
                    os.rename(src_file, dst_file)

            # Set up export-related fields.
            if project_name:
                project.name = project_name
            if release_name:
                project.release_name = release_name

            # Set up a function to be called on each output folder.
            def copy_include_files(output_folder):
                if include_files:
                    # Copy include files into the output folder.
                    for item in include_files:
                        src, dst = item
                        if os.path.isabs(dst):
                            raise ValueError("An include_file destination must be relative to the output folder.")
                        if ".." in dst:
                            raise ValueError("An include_file destination must stay within the output folder.")
                        dst = os.path.join(output_folder, dst)
                        os.makedirs(dst, exist_ok=True)
                        # noinspection PyShadowingNames
                        for filename in glob.glob(src):
                            shutil.copy(filename, dst)

            # Now compile and export.
            compiler = AgkCompiler()
            compiler.compile(project)
            for p in [platforms.WINDOWS_86, Platform.WINDOWS_64, Platform.WINDOWS_86_64]:
                if platforms & p:
                    release_path = compiler.export_windows(project, _Architecture.from_platform(p))
                    copy_include_files(release_path)
                    self.release_paths[p] = release_path
            for p in [platforms.LINUX_86, Platform.LINUX_64, Platform.LINUX_86_64]:
                if platforms & p:
                    release_path = compiler.export_linux(project, _Architecture.from_platform(p))
                    copy_include_files(release_path)
                    self.release_paths[p] = release_path
            if platforms & Platform.HTML5:
                release_path = compiler.export_html5(project)
                copy_include_files(release_path)
                self.release_paths[Platform.HTML5] = release_path
            if platforms & Platform.GOOGLE_APK:
                release_path = compiler.export_apk(project, app_type=AgkCompiler.APK_TYPE_GOOGLE, **kwargs)
                self.release_paths[Platform.GOOGLE_APK] = release_path
            if platforms & Platform.AMAZON_APK:
                release_path = compiler.export_apk(project, app_type=AgkCompiler.APK_TYPE_AMAZON, **kwargs)
                self.release_paths[Platform.AMAZON_APK] = release_path
            if platforms & Platform.OUYA_APK:
                release_path = compiler.export_apk(project, app_type=AgkCompiler.APK_TYPE_OUYA, **kwargs)
                self.release_paths[Platform.OUYA_APK] = release_path
        finally:
            os.replace(backup_code_file, main_code_file)
            # Restore exclude media files back into the media folder.
            media_exclude_path = os.path.join(project.base_path, 'media_exclude')
            for root, dirs, files in os.walk(media_exclude_path):
                for dirname in dirs:
                    os.makedirs(os.path.join(root, dirname), exist_ok=True)
                for filename in files:
                    src_file = os.path.join(root, filename)
                    dst_file = os.path.join(project.base_path, 'media', os.path.relpath(src_file,
                                                                                        start=media_exclude_path))
                    os.rename(src_file, dst_file)
            _rmtree(media_exclude_path)

    def create_linux_setup_script(self, platforms: Platform, script_name: str = "setup.sh"):
        """
        Creates a bash script file in the release folder that installs dependencies and sets the executable flag for the
        game application.

        Valid platform flags are: `LINUX_86`, `LINUX_64`, and `LINUX_86_64`.

        :param platforms: Platform flags.
        :param script_name: The script file name.  Defaults to "setup.sh".
        :return:
        """
        for p in Platform:
            if platforms & p:
                if p not in [Platform.LINUX_86, Platform.LINUX_64, Platform.LINUX_86_64]:
                    raise ValueError("Only Linux releases can have setup.sh files.")
                print(f"Adding setup.sh script for {p.name}")
                # Must be written with Linux newlines.
                with open(os.path.join(self.release_paths[p], script_name), "w", newline="\n") as fp:
                    fp.write('''#!/bin/bash
set -e

echo "[setup] Installing dependencies..."
apt-get install libopenal1 -qy

echo "[setup] Setting executable flag..."
''')
                    architecture = _Architecture.from_platform(p)
                    if architecture & _Architecture.x86:
                        fp.write(f"chmod +x {self.project.safe_name}32\n")
                    if architecture & _Architecture.x64:
                        fp.write(f"chmod +x {self.project.safe_name}64\n")

    def create_debian_package(self, platforms: Platform,
                              email_name: str,
                              email_address: str,
                              short_description: str,
                              long_description: str,
                              application_icon: str,  # A PNG file path relative to the AGK project folder.
                              usr_subfolder: str = "games",
                              package_name: str = None,
                              homepage: str = None,
                              section: str = "games",
                              generic_name: str = "Game",
                              comment: str = "A game created with AppGameKit.",
                              categories: Iterable[str] = ("Game",)
                              ):
        """
        Creates a Debian package using the files in a platform's release folder.
        The release folder is not removed during this process.

        By default, the game will be installed to /usr/<usr_subfolder>/<package_name> where usr_subfolder defaults to
        "games".

        Valid platform flags are `LINUX_86` and `LINUX_64`.

        For information on the fields within the package control file, see:
        https://www.debian.org/doc/debian-policy/ch-controlfields.html

        For information on the fields within the package .desktop file, see:
        https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#recognized-keys

        This process uses Windows Packager.
        https://windowspackager.org/

        :param platforms: The platform flags.
        :param email_name: The email name for the package control file.
        :param email_address: The email address for the package control file.
        :param short_description: The short description for the package control file.  Must be less than 80 characters.
        :param long_description: The long description for the package control file.
        :param application_icon: The application icon.  Must be a PNG that is a square power of 2, preferably 256x256.
        :param usr_subfolder: The folder within the `usr` folder where your game is installed.  Defaults to "games".
        :param package_name: The package name.  Defaults to project name converted to lower-case with invalid
            characters removed.  Package names must consist only of lower case letters (a-z), digits (0-9), plus (+) and
            minus (-) signs, and periods (.).  They must be at least two characters long and must start with an
            alphanumeric character.
        :param homepage: The homepage for the package control file.  Defaults to None.
        :param section: The application area into which the package is classified for the package control file.
            Defaults to "games".
        :param generic_name: A very general name describing what the program is, ie Firefox is a "Web Browser".
            This is used in the package .desktop file.  Defaults to "Game".
        :param comment: A comment which can/will be used as a tooltip.  This is used in the package .desktop file.
            Defaults to "A game created with AppGameKit."
        :param categories: The categories in which this entry should be shown.  This is used in the package .desktop
            file.  Defaults to ("Game",)
        :return:
        """
        if not email_name:
            raise ValueError("An email_name is required.")
        if not email_address:
            raise ValueError("An email_address is required.")
        if not re.match(r"(^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$)", email_address):
            raise ValueError("The email_address is invalid.")

        if not short_description:
            raise ValueError("A short_description is required.")
        short_description = short_description.strip()
        if len(short_description) >= 80:
            raise ValueError("The short_description must be less than 80 characters.")
        if not long_description:
            raise ValueError("A long_description is required.")
        long_description = long_description.strip()

        # Package names must consist only of lower case letters (a-z), digits (0-9), plus (+) and minus (-)
        # signs, and periods (.).
        # They must be at least two characters long and must start with an alphanumeric character.
        if not package_name:
            package_name = re.sub(r'[^A-Za-z0-9+.-]', '', self.project.name.lower())
        if not package_name or len(package_name) <= 2:
            raise ValueError("The package_name must be at least two characters.")
        if not str.isalnum(package_name[0]):
            raise ValueError("The package_name must start with an alphanumeric character.")

        if not usr_subfolder:
            raise ValueError("A usr_subfolder must be specified.")

        _validate_url(homepage)

        # Validate the icon.
        if not application_icon.endswith('.png'):
            raise ValueError('The application icon must be a PNG file.')
        icon_path = os.path.join(self.project.base_path, application_icon)
        application_icon = os.path.split(application_icon)[1]  # We just want the file name now.
        if not os.path.exists(icon_path):
            raise ValueError("Could not find the application icon location.")
        icon_image = Image.open(icon_path)
        if icon_image.width != icon_image.height:
            raise ValueError("Application icon is not square.")
        if not _is_power_of_2(icon_image.width):
            raise ValueError("Application icon is not a power of 2.")
        del icon_image

        # Wrap the long description.
        long_description = '\n .\n'.join(['\n'.join(textwrap.wrap(line, 80, initial_indent=" ", subsequent_indent=" ",
                                                                  replace_whitespace=False))
                                          for line in long_description.split("\n")])

        temp_path = os.path.join(self.project.base_path, "release", "temp")

        for p in Platform:
            if platforms & p:
                if p not in [Platform.LINUX_86, Platform.LINUX_64]:
                    raise ValueError(f"Creating a Debian package for this platform is supported: {p.name}")
                print(f"Creating Debian package for {p.name}")
                release_path = self.release_paths[p]
                installed_size = math.ceil(_get_folder_size(release_path) / 1024)
                executable = f"{self.project.safe_name}{'32' if p == Platform.LINUX_86 else '64'}"

                try:
                    debian_path = os.path.join(temp_path, "DEBIAN")
                    package_path = os.path.join(temp_path, "usr", usr_subfolder, package_name)
                    applications_path = os.path.join(temp_path, "usr", "share", "applications")
                    os.makedirs(debian_path)
                    # os.makedirs(package_path)
                    os.makedirs(applications_path)

                    # Create control file
                    # https://www.debian.org/doc/debian-policy/ch-controlfields.html
                    with open(os.path.join(debian_path, "control"), "w", newline="\n") as fp:
                        # TODO Research multi-arch packages.
                        # Architecture: any
                        # Multi-Arch: same
                        fp.write(f'''Package: {package_name}
Version: {self.project.version}
Architecture: {"i386" if p == Platform.LINUX_86 else "amd64"}
Section: {section}
Priority: optional
Depends: libopenal1
Installed-Size: {installed_size}
Maintainer: {email_name} <{email_address}>
Description: {short_description}
{long_description}
''')
                        if homepage:
                            fp.write(f"Homepage: {homepage}\n")

                    # Create the postinst script.
                    with open(os.path.join(debian_path, "postinst.sh"), "w", newline="\n") as fp:
                        fp.write(f'''#!/bin/bash
# This package was built using Windows Packager.
# https://windowspackager.org/
# Because of this, permissions are set here.
set -e
chmod -R 755 /usr/{usr_subfolder}/{package_name}/{executable}
exit 0
''')

                    # Create the desktop file
                    # https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html#recognized-keys
                    with open(os.path.join(applications_path, f"{package_name}.desktop"), "w", newline="\n") as fp:
                        fp.write(f'''[Desktop Entry]
Name={self.project.name}
GenericName={generic_name}
Comment={comment}
Exec=/usr/{usr_subfolder}/{package_name}/{executable}
StartupNotify=true
Terminal=false
Type=Application
Icon=/usr/{usr_subfolder}/{package_name}/{application_icon}
Categories={";".join(categories)};
''')

                    shutil.copytree(release_path, package_path, ignore=shutil.ignore_patterns(*IGNORE_FILES))
                    shutil.copyfile(icon_path, os.path.join(package_path, application_icon))

                    # Create the Debian package.
                    completed_process = subprocess.run([os.path.join(_get_script_path(), "bin", "wpkg", "wpkg.exe"),
                                                        "--build", temp_path],
                                                       cwd=os.path.join(self.project.base_path, "release"),
                                                       # stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE,
                                                       universal_newlines=True)
                    # error = completed_process.stdout.strip()
                    error = completed_process.stderr.strip()
                    if error:
                        raise SystemError(f'Windows Packager returned error:\n{error}')
                    if completed_process.returncode:
                        raise SystemError(f'Windows Packager returned code: {completed_process.returncode}')
                finally:
                    _rmtree(temp_path)

    def create_nsis_installer(self, platforms: Platform,
                              developer_name: str,
                              homepage: str = None,
                              project_guid: str = None,
                              defines: List[Union[str, Tuple[str, str]]] = None,
                              inline_template: bool = False,
                              ):
        """
        Creates a Windows installer from the release folder for the given platforms.
        The release folder is not removed during this process.

        Valid platform flags are `WINDOWS_86`, `WINDOWS_64`, and `WINDOWS_86_64`.
        `WINDOWS_86_64` will create an installer that extracts either the 32- or 64-bit executable depending on the
        installation operating system.

        This process uses NSIS (Nullsoft Scriptable Install System).
        https://nsis.sourceforge.io/Main_Page

        :param platforms: The platform flags.
        :param developer_name: The developer name.
        :param homepage: Shown in the "Add or Remove Programs" information.
        :param project_guid: Used when storing the uninstall information in the Windows Registry.
            This value should **NEVER** change during the lifetime of the project.
            When not given, "${DEVELOPER_NAME} ${PROJECT_NAME}" is used.
        :param defines: A list of defines to include in the script.  When a list item is a string, the line will look
            like `!define NAME`.  When the list item is a tuple of two strings, the line will look like
            `!define NAME "VALUE"`.
        :param inline_template: When False (the default), the agkbuild.nsi file is added using `!include`.  When True,
            the file is added inline at the bottom of the generated script file.
        :return:
        """
        if not developer_name:
            raise ValueError("The developer_name is required.")
        _validate_url(homepage)

        # template_script = os.path.join(_get_script_path(), "templates", "NSIS", "agkbuild.nsi")
        template_script = "agkbuild.nsi"
        if inline_template:
            template_script = os.path.join(_get_script_path(), "bin", "NSIS", "Include", template_script)
        executables = [f"{self.project.name}.exe", f"{self.project.name}64.exe"]
        for p in Platform:
            if platforms & p:
                if p not in [Platform.WINDOWS_86, Platform.WINDOWS_64, Platform.WINDOWS_86_64]:
                    raise ValueError(f"Creating a Nullsoft Installer for this platform is supported: {p.name}")
                print(f"Creating a Nullsoft Installer for {p.name}")
                release_path = self.release_paths[p]
                script_file = self.project.get_nsis_script_path(p)
                with open(script_file, "w") as fp:
                    fp.write("; Install script generated by AgkBuild\n\n")
                    fp.write(f'!define PROJECT_NAME\t"{self.project.name}"\n')
                    fp.write(f'!define SAFE_PROJECT_NAME\t"{self.project.safe_name}"\n')
                    if os.path.exists(os.path.join(release_path, "icon.ico")):
                        fp.write(f'!define PROJECT_ICON\t"icon.ico"\n')
                    fp.write(f'!define RELEASE_FILE_PATH\t"{os.path.relpath(release_path, self.project.base_path)}"\n')
                    fp.write(f"!define ESTIMATEDSIZE\t{math.ceil(_get_folder_size(release_path) / 1024)}\n")
                    fp.write("\n")
                    fp.write(f'!define DEVELOPER_NAME\t"{developer_name}"\n')
                    if homepage:
                        fp.write(f'!define HOMEPAGE\t"{homepage}"\n')
                    if project_guid:
                        fp.write(f'!define PROJECT_GUID\t"{project_guid}"\n')
                    fp.write("\n")
                    if self.version:
                        for part_name, value in zip(["MAJOR", "MINOR", "PATCH"], self.version.split(".")):
                            fp.write(f"!define PROJECT_VERSION_{part_name}\t{value}\n")
                    fp.write("\n")
                    if defines:
                        for define in defines:
                            try:
                                name, value = define
                                fp.write(f'!define {name}\t"{value}"\n')
                            except ValueError:
                                fp.write(f'!define {define}\n')
                        fp.write("\n")
                    fp.write(f"!define {p.name}\n")
                    fp.write(f'!define AGKBUILD_PATH\t"{_get_script_path()}"\n')
                    fp.write("\n")
                    # Create the InstallFiles macro.
                    fp.write("!macro InstallFiles\n")
                    fp.write('\t; NOTE: The template script handles the executable."\n')
                    fp.write('\tSetOutPath	"$INSTDIR"\n')
                    for root, _, files in sorted(os.walk(release_path)):
                        relpath = os.path.relpath(root, release_path)
                        if relpath == ".":
                            relpath = ""
                        else:
                            fp.write(f'\n\tSetOutPath\t"{os.path.join("$INSTDIR", relpath)}"\n')
                        for filename in sorted(files):
                            # Skip the executables.
                            if filename in executables and not relpath:
                                continue
                            fp.write(f'\tFile\t"{os.path.join("${RELEASE_FILE_PATH}", relpath, filename)}"\n')
                    fp.write("!macroend\n\n")
                    # Create the UninstallFiles macro with files and folders in reverse.
                    fp.write("!macro UninstallFiles\n")
                    fp.write('\t; NOTE: The template script handles the executable and removing $INSTDIR."\n')
                    for root, _, files in reversed(sorted(os.walk(release_path))):
                        relpath = os.path.relpath(root, release_path)
                        if relpath == ".":
                            relpath = ""
                        for filename in reversed(sorted(files)):
                            # Skip the executables.
                            if filename in executables and not relpath:
                                continue
                            fp.write(f'\tDelete\t/REBOOTOK\t"{os.path.join("$INSTDIR", relpath, filename)}"\n')
                        if relpath:
                            fp.write(f'\tRMDir\t/REBOOTOK\t"{os.path.join("$INSTDIR", relpath)}"\n\n')
                    fp.write("!macroend\n\n")
                    if inline_template:
                        with open(template_script, 'r') as tfp:
                            fp.writelines(tfp.readlines())
                    else:
                        fp.write(f'!include "{template_script}"\n')
                # Compile it
                completed_process = subprocess.run([os.path.join(_get_script_path(), "bin", "NSIS", "makensis.exe"),
                                                    "/V2",  # 2=warnings and errors
                                                    script_file
                                                    ],
                                                   cwd=os.path.join(self.project.base_path, "release"),
                                                   stderr=subprocess.PIPE,
                                                   universal_newlines=True)
                error = completed_process.stderr.strip()
                if error:
                    raise SystemError(f'Windows Packager returned error:\n{error}')
                if completed_process.returncode:
                    raise SystemError(f'Windows Packager returned code: {completed_process.returncode}')

    def archive(self, platforms: Platform):
        """
        Creates a zip archive of the release folder for each given platform flag.
        The release folder will be removed and the `release_path` for the platform will be set to the created zip file.

        This method cannot be used for `GOOGLE_APK`, `AMAZON_APK`, or `OUYA_APK`.

        :param platforms: The platform flags.
        """
        for p in Platform:
            if platforms & p:
                if p in [Platform.GOOGLE_APK, Platform.AMAZON_APK, Platform.OUYA_APK]:
                    raise ValueError("Android APK releases are already archives.")
                print(f"Archiving {p.name}")
                release_path = self.release_paths[p]
                zip_path = f"{release_path}.zip"
                with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zfp:
                    for root, dirs, files in os.walk(release_path):
                        for dirname in [os.path.join(root, dirname) for dirname in dirs]:
                            zfp.write(dirname, os.path.relpath(dirname, release_path))
                        for filename in [os.path.join(root, filename) for filename in files]:
                            rel_path = os.path.relpath(filename, release_path)
                            zfp.write(filename, rel_path)
                _rmtree(release_path)
                # Update the release path.
                self.release_paths[p] = zip_path


def _exec_build_tasks(filename):
    print(f"Starting agkbuild: {filename}")
    cwd, filename = os.path.split(os.path.abspath(filename))
    os.chdir(cwd)
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader('tasks', filename)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    tasks = importlib.util.module_from_spec(spec)
    # Add these for use in the agkbuild file.
    tasks.AgkBuild = AgkBuild
    # Allow flags and values to be used in the agkbuild file without the class name.
    for v in [v for e in [Platform,
                          Permission,
                          Orientation,
                          ArCoreMode,
                          Html5Commands] for v in e]:
        tasks.__dict__[v.name] = v
    # Run the exporter.  This is not a "safe" operation since the agkbuild file runs as Python code.
    spec.loader.exec_module(tasks)


def _main():
    parser = argparse.ArgumentParser(description='An AppGameKit build automation script.')
    parser.add_argument('buildfile', metavar='buildfile', type=str, help='The agkbuild file to process.')
    args = parser.parse_args()
    _exec_build_tasks(args.buildfile)


if __name__ == '__main__':
    _main()
