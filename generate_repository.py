#!/usr/bin/env python3
import glob
import hashlib
import json
import os
import shutil
import zipfile

import pip

project_root = os.path.dirname(os.path.realpath(__file__))
repo_source_path = os.path.join(project_root, 'source')
repo_dest_path = os.path.join(project_root, 'repo')
repo_json_file = os.path.join(repo_dest_path, 'repo.json')
repo_json_checksum_file = os.path.join(repo_dest_path, 'repo.json.md5')


class BColours:
    HEADER = '\033[36m'
    SEPARATOR = '\033[44m'
    SECTION = '\033[34m'

    SUBHEADER = '\033[94m'
    RESULTS = '\033[39m'
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def zipdir(path, zip):
    for root, dirs, files in os.walk(path):
        for file in files:
            zip.write(os.path.join(root, file))


def install_requirements(package):
    requirements_file = os.path.join(item_path, 'requirements.txt')
    install_target = os.path.join(item_path, 'site-packages')
    if not os.path.exists(requirements_file):
        print('      - no requirements.txt file found')
        return

    pip.main(['install', '--upgrade', '-r', requirements_file, '--target={}'.format(install_target)])



# Ensure the repo directory exists
if not os.path.exists(repo_dest_path):
    os.makedirs(repo_dest_path)

# Build repo based on files in source directory
print()
print("{0}>> Processing Plugins <<{1}".format(BColours.HEADER, BColours.ENDC))
print()
for item in os.listdir(repo_source_path):
    item_path = os.path.join(repo_source_path, item)
    # Ignore files in the root directory of the source path
    # Ignore git configuration files
    if (os.path.isdir(item_path)) and ('.git' not in item):
        # Read plugin info
        info_file = os.path.join(item_path, 'info.json')
        with open(info_file) as f:
            plugin_info = json.load(f)

        # Set destination data
        dest_dir = os.path.join(repo_dest_path, item)
        plugin_zip_file = "{}-{}.zip".format(item, plugin_info.get('version'))
        plugin_zip = os.path.join(dest_dir, plugin_zip_file)

        # Ensure all required data is present
        for value in ['id', 'name', 'author', 'version', 'tags', 'description']:
            if value not in plugin_info:
                msg = "Plugin '{}' is missing required information '{}' in it's info.json file.".format(item, value)
                raise Exception(msg)

        # Print data variables for info
        description = plugin_info.get('description').split('\n')
        description = "\n                        ".join(description)
        print("{0}  ------------------------------->{1}  {2}".format(BColours.SEPARATOR, BColours.ENDC, plugin_info.get('name')))
        print("  > Plugin Info:")
        print("      Name:            {0}'{2}'{1}".format(BColours.SECTION, BColours.ENDC, plugin_info.get('name')))
        print("      ID:              {0} {2}{1}".format(BColours.SECTION, BColours.ENDC, plugin_info.get('id')))
        print("      Author:          {0} {2}{1}".format(BColours.SECTION, BColours.ENDC, plugin_info.get('author')))
        print("      Version:         {0} {2}{1}".format(BColours.SECTION, BColours.ENDC, plugin_info.get('version')))
        print("      Tags:            {0} {2}{1}".format(BColours.SECTION, BColours.ENDC, plugin_info.get('tags')))
        print("      Description:     {0} {2}{1}".format(BColours.SECTION, BColours.ENDC, description))
        print()

        # Ensure that we are not overwriting a plugin that already exists with this version
        if os.path.exists(plugin_zip):
            print("{}".format(BColours.WARNING))
            print("  >  !!! WARNING !!!")
            print("     _______________")
            print("   |")
            print("   | Repository already contains '{}'.".format(plugin_zip_file))
            print("   |")
            print("   | You will need to either:")
            print("   |   - Remove the current file '{}'".format(plugin_zip))
            print("   | OR")
            print("   |   - increase the plugin's version number if you wish to overwrite the current version.")
            print("{}".format(BColours.ENDC))
            print()
            print("  > Will not process plugin: '{}'".format(plugin_info.get('name')))
            print()
            print()
            continue

        # Ensure repo destination directory exists
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        # Copy plugin info.json to dest
        print('    Installing plugin metadata to repo...')
        print('      - Copying: {} >>>> {}/info.json'.format(info_file, dest_dir))
        shutil.copy(info_file, dest_dir)

        # Add additional files (optional files)
        for file in glob.glob(os.path.join(item_path, '*changelog.txt')):
            print('      - Copying: {} >>>> {}/changelog.txt'.format(file, dest_dir, plugin_info.get('version')))
            shutil.copy(file, dest_dir)
        for file in glob.glob(os.path.join(item_path, '*icon.*')):
            print('      - Copying: {} >>>> {}/icon.png'.format(file, dest_dir))
            shutil.copy(file, dest_dir)
        for file in glob.glob(os.path.join(item_path, '*fanart.*')):
            print('      - Copying: {} >>>> {}/fanart.jpg'.format(file, dest_dir))
            shutil.copy(file, dest_dir)
        print()

        # Install any package requirements
        print("    Installing Python package requirements...")
        install_requirements(item_path)

        # Generate a zip file from the plugin contents
        print("    Compressing {}...".format(plugin_zip))
        zip_file = zipfile.ZipFile(plugin_zip, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(item_path):
            for file in files:
                absname = os.path.abspath(os.path.join(root, file))
                arcname = absname[len(item_path) + 1:]
                print('      - Zipping: {} >>> {} | ({})'.format(os.path.join(root, file), arcname, plugin_zip))
                zip_file.write(os.path.join(root, file), arcname)
        zip_file.close()

        print()

# Write Repo data based on what is now in the repo directory
print("-----------------------------------------------------------------------------")
print()
print()
print("{0}>> Processing Repo Metadata <<{1}".format(BColours.HEADER, BColours.ENDC))
print()
repo_data = {
    "repo":    {},
    "plugins": [],
}


print("  > Creating list of plugins".format(repo_json_file))
print()
for item in os.listdir(repo_dest_path):
    item_path = os.path.join(repo_dest_path, item)
    # Ignore files in the root directory of the source path
    # Ignore git configuration files
    if (os.path.isdir(item_path)) and ('.git' not in item):
        # Read plugin info
        info_file = os.path.join(item_path, 'info.json')
        with open(info_file) as f:
            plugin_info = json.load(f)
        # Append plugin info to repo data
        repo_data['plugins'].append(plugin_info)
        continue

# Add main repo info to repo data
print("  > Reading repo config".format(repo_json_file))
print()
with open(os.path.join(project_root, 'config.json')) as f:
    repo_info = json.load(f)

# Set the repo URL
print("  > Setting repo data url".format(repo_json_file))
print()
configured_remote_origin = os.popen('git remote get-url --push origin').read()
repo_path = configured_remote_origin.strip().rstrip(".git").lstrip('git@github.coms:').lstrip('https://github.com/s')
repo_info['repo_data_directory'] = "https://raw.githubusercontent.com/{}/".format(repo_path)
repo_info['repo_data_url'] = repo_info['repo_data_directory'] + "repo/repo.json"
repo_data['repo'] = repo_info

# Install repo_data to repo's plugins.json file
#print("{0}  ------------------------------->{1}".format(BColours.SEPARATOR, BColours.ENDC))
print("  > Writing repo data to file '{}'...".format(repo_json_file))
print()
with open(repo_json_file, 'w') as json_file:
    json.dump(repo_data, json_file, indent=4)


# Add checksum to plugins_json_file file
print("  > Writing repo data file checksum to file '{}'...".format(repo_json_checksum_file))
print()
checksum = hashlib.md5(open(repo_json_file,'rb').read()).hexdigest()
with open(repo_json_checksum_file, 'w') as checksum_file:
    checksum_file.writelines(checksum)


print()