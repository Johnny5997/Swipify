from setuptools import setup

APP = ['Switch_Stages.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'packages': ['rumps', 'pynput'],
    'includes': [
        'pynput.mouse',
        'pynput.mouse._darwin',
        'pynput.keyboard',
        'pynput.keyboard._darwin',
        'pynput._util',
        'pynput._util.darwin'
    ],
    'resources': ['menu.png', 'menu2.png'],
    'frameworks': [],
    'excludes': ['tkinter', 'matplotlib', 'numpy'],
    'site_packages': True,
    'plist': {
        'CFBundleName': 'Switch Stages',
        'CFBundleDisplayName': 'Switch Stages',
        'CFBundleGetInfoString': "Switch Stages App",
        'CFBundleIdentifier': "com.stagemanager.controller",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "Copyright © 2026, Your Name, All Rights Reserved",
        'LSUIElement': True,
        'LSBackgroundOnly': False,
        'NSAppleEventsUsageDescription': 'Switch Stages needs to send keyboard commands to control Stage Manager.',
        'NSAccessibilityUsageDescription': 'Switch Stages needs Input Monitoring permission to detect middle mouse button gestures.',
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)